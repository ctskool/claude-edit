"""One command for a first draft, one for a change. CONTRACT.md sections 4 to 6.

  python tools/beat_render/run.py draft  <project> --profile review [--workers N] [--force]
  python tools/beat_render/run.py change <project> --profile review [--workers N] [--kind caption]
  python tools/beat_render/run.py stitch <project> --profile review
  python tools/beat_render/run.py refs   <project> --profile review
  python tools/beat_render/run.py draft  <project> --profile final --workers 1 --store <another store> --only b05

draft renders every beat with no intact segment. change compares the project to the last stitched picture and renders every beat whose key has none in the store.
A touched beat whose key is in the store reuses that segment, so going back returns the exact pixels. --force renders them anyway and replaces the segment.
A segment is reused only if its input key and complete profile match and its bytes still hash to what was published. Any doubt renders more, never less. Run from anywhere; only one run per store.
The owner audit runs in the page before anything renders, and a picture becomes current only after both checks ran to the end and neither failed. Any other is in last_attempt.json.
--inject-fault is for tests: nothing a faulted attempt renders is ever published.
"""
import argparse, json, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import project_root
ROOT = project_root()
sys.path.append(str(HERE.parent))
import lock as beat_lock
import ownership
import sentinel
import sound_mix
import stitch as stitcher
import store
import tied
from common import sha

PIN = "0.9.13"  # also fixed in hf.mjs. An upgrade is a re-qualification.
RENDER = HERE / "render.mjs"
REFS = HERE / "refs.mjs"
WORKER = HERE / "worker.mjs"
PROFILES = HERE / "profiles.json"
RETRIES = 2
REF_PAGE_FRAMES = 40  # far below the 481 where the whole-render fault first showed
SUSPECTS_MAX = 8
CHECK_STATUS = {0: "PASS", 1: "FAIL", 3: "UNVERIFIED"}  # beat_check's exit codes for a check that ran to the end. Any other exit, or a hang, says nothing
AUDIT_SECONDS = 300
CHECK_SECONDS = 1200  # far above the 47 s and 20 s measured on a busy machine. Past this a check reads UNVERIFIED


class Refused(Exception):
    """Fail closed: nothing rendered, nothing published."""


def installed_version():
    package = ROOT / "node_modules" / "hyperframes" / "package.json"
    try:
        return json.loads(package.read_text(encoding="utf8"))["version"]
    except (OSError, ValueError, KeyError):
        return None


def check_version(version=None):
    version = version or installed_version()
    if version != PIN:
        raise Refused(f"HyperFrames is {version}, this renderer is qualified on {PIN} only")


def load_profile(name, workers):
    data = json.loads(PROFILES.read_text(encoding="utf8"))
    if name not in data["profiles"]:
        raise Refused(f"unknown profile {name}")
    profile = data["profiles"][name]
    workers = workers or data["workers"].get(name)
    if not workers:
        raise Refused(f"no measured worker count for {name}: pass --workers")
    return profile, sha(profile), workers


def engine_hash(chrome):
    version = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    return sha({"hyperframes": PIN, "ffmpeg": version, "chrome": chrome, "files": {p.name: sound_mix.file_hash(p) for p in (RENDER, HERE / "hf.mjs", HERE / "virtual-time.mjs")}})


def plan_key(m, profile):
    return sha({"timing_hash": m["shared"]["timing_hash"], "media_hash": m["shared"]["media_hash"], "fps": profile["fps"], "extraction": profile["extraction"], "hyperframes": PIN})


def stale_files(project, m):
    """Files that differ from the map, or that the map has never seen. A stale map gives wrong keys, so the build must run first."""
    project = Path(project)
    known = {**m["shared"]["files"], **m["authoring"]}
    known.update(ownership.asset_hashes(m))
    known.update({r["src"]: r["sha256"] for r in m["shared"]["media"]})
    problems = [rel for rel, h in sorted(known.items()) if not (project / rel).is_file() or sound_mix.file_hash(project / rel) != h]
    unused = set(m["shared"].get("unused", []))
    return problems + [rel for rel in ownership.project_files(project) if rel != "index.html" and rel not in known and rel not in unused and not ownership.is_ignored(rel)]


def project_stamp(project, m):
    """Changes if anything a render read moved under it."""
    project = Path(project)
    read = m.get("shared", {}).get("files", {})  # an ignored path the page names is in the shared files
    files = [(rel, (project / rel).stat().st_size, (project / rel).stat().st_mtime_ns) for rel in ownership.project_files(project) if not ownership.is_ignored(rel) or rel in read]
    return sha({"composition_rev": m["composition_rev"], "files": files})


def assign(beats, workers):
    """Beats in time order, each to the least loaded worker, so a worker seeks forward."""
    slots = [[] for _ in range(workers)]
    loads = [0] * workers
    for b in sorted(beats, key=lambda x: x["start_frame"]):
        i = loads.index(min(loads))
        slots[i].append(b)
        loads[i] += b["end_frame"] - b["start_frame"]
    return [s for s in slots if s]


def render_set(lock, keys, invalidated, in_store, old_keys, engine_changed=False, force=False):
    """Returns (beats to render, beats invalidate missed). A beat renders if its key is not in the store. A touched beat whose key is there reuses that segment, so a go-back returns the
    exact bytes a picture was stitched from. force renders the touched beats anyway. CONTRACT.md section 4: a changed key invalidate did not name is a bug, so it is named."""
    touched = set(invalidated)
    missed = []
    if not engine_changed:
        missed = [b["beat_id"] for b in lock["beats"] if b["beat_id"] not in touched and keys[b["beat_id"]] != old_keys.get(b["beat_id"])]
    chosen = {b["beat_id"] for b in lock["beats"] if not in_store(b["beat_id"])}
    if force:
        chosen |= touched | set(missed)
    return [b["beat_id"] for b in lock["beats"] if b["beat_id"] in chosen], missed


def worst(statuses):
    return "FAIL" if "FAIL" in statuses else "UNVERIFIED" if "UNVERIFIED" in statuses or not statuses else "PASS"


def node(script, verb, job_path, log):
    args = ["node", str(script)] + ([verb] if verb else []) + [str(job_path)]
    return tied.spawn(args, cwd=ROOT, stdout=open(log, "w", encoding="utf8"), stderr=subprocess.STDOUT)


def finish_all(procs, seconds):
    """Waits for processes this run started, and stops any that hang."""
    deadline = time.perf_counter() + seconds
    codes = []
    for p in procs:
        try:
            codes.append(p.wait(max(1, deadline - time.perf_counter())))
        except subprocess.TimeoutExpired:
            tied.kill_tree(p)
            codes.append(p.wait())
    return codes


def check_status(command, seconds):
    """A check's exit code as (status, ran to the end). One that hangs is stopped and reads UNVERIFIED: no output from it is no evidence.
    A review picture's best status is UNVERIFIED too, so the status alone cannot say whether a check finished."""
    p = tied.spawn(command, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        code = p.wait(seconds)
    except subprocess.TimeoutExpired:
        tied.kill_tree(p)
        p.wait()
        return "UNVERIFIED", False
    return CHECK_STATUS.get(code, "UNVERIFIED"), code in CHECK_STATUS


class Run:
    def __init__(self, args):
        check_version()
        self.project = Path(args.project).resolve()
        try:
            self.lock = beat_lock.load(self.project)
        except (OSError, ValueError) as e:
            raise Refused(f"no valid beats.lock.json: {e}")
        self.map = ownership.load(self.project)
        if self.map is None:
            raise Refused("no valid ownership.json for this index.html: run the build")
        if self.map["lock_revision"] != self.lock["revision"]:
            raise Refused("ownership.json is not of this beats.lock.json: run the build")
        stale = stale_files(self.project, self.map)
        if stale:
            raise Refused(f"the build is stale for: {', '.join(stale[:8])}")
        self.profile, self.profile_hash, self.workers = load_profile(args.profile, args.workers)
        if self.profile["fps"] != self.lock["fps"]:
            raise Refused(f"profile fps {self.profile['fps']} is not the lock's {self.lock['fps']}")
        self.root = store.open_store(Path(args.store).resolve() if args.store else store.root_of(self.project))
        self.force = bool(getattr(args, "force", False) or args.inject_fault)
        self.inject = {"kind": args.inject_fault, "beats": (args.inject_beats or "").split(","), "rounds": args.inject_rounds} if args.inject_fault else None
        self.timings = {}
        self.beats = {b["beat_id"]: b for b in self.lock["beats"]}
        events = store.read_json(self.project / "events.json", {})
        self.events = events.get("events", []) if events.get("composition_rev") == self.map["composition_rev"] else []
        self.frame_size = (self.profile["width"], self.profile["height"])
        self.region_top = self.profile["height"] // 2
        self.stamp = project_stamp(self.project, self.map)

    def stored(self, beat_id):
        """A segment this run may reuse. One whose bytes moved counts as missing, so the beat renders again."""
        return store.intact(self.root, self.profile_hash, self.keys[beat_id]) is not None

    def timed(self, name, started):
        self.timings[name] = round(self.timings.get(name, 0) + time.perf_counter() - started, 2)

    def job(self, tmp, name, **fields):
        path = tmp / f"{name}.json"
        store.write_json(path, {"plan": str(self.plan), "project": str(self.project), "compiled": str(tmp / "compiled"), "scratch": str(tmp / "scratch"), "profile": self.profile, **fields})
        return path

    def ensure_plan(self):
        started = time.perf_counter()
        self.plan = store.plan_dir(self.root, plan_key(self.map, self.profile))
        if not (self.plan / "plan.json").is_file():
            building = self.root / "plans" / (self.plan.name + "-building")
            shutil.rmtree(building, ignore_errors=True)
            command = ["node", str(WORKER), "plan", str(self.project), str(building), str(self.profile["fps"]), "standard", "0", self.profile["extraction"]]
            if tied.spawn(command, cwd=ROOT, stdout=subprocess.DEVNULL).wait():
                raise Refused("the media plan did not build")
            building.replace(self.plan)
            store.prune_plans(self.root)
        self.timed("plan", started)

    def prepare(self, tmp):
        """Compiles the page once for every worker, checks it against the plan, and asks the browser its version."""
        started = time.perf_counter()
        result = tmp / "prepare-result.json"
        job = self.job(tmp, "prepare", result=str(result))
        log = tmp / "prepare.log"
        if finish_all([node(RENDER, "prepare", job, log)], 300) != [0]:
            raise Refused(f"prepare failed: {log.read_text(encoding='utf8', errors='replace')[-1500:]}")
        info = json.loads(result.read_text(encoding="utf8"))
        if info["hyperframes"] != PIN:
            raise Refused(f"worker reports HyperFrames {info['hyperframes']}")
        self.engine = engine_hash(info["chrome"])
        self.keys = {b["beat_id"]: ownership.input_key(b, self.lock, self.map, self.profile_hash, self.engine) for b in self.lock["beats"]}
        self.timed("prepare", started)

    def samples(self, beat):
        return sentinel.samples(beat, [e for e in self.events if "frame" in e])

    def ref_path(self, beat, frame):
        return store.refs_dir(self.root, self.profile_hash, self.keys[beat["beat_id"]]) / f"{frame}.jpg"

    def ref_jobs(self, beats, extra=None):
        """The references these beats still need. A page can keep what a frame it landed on did, so a beat's references are always a whole set, stepped in order from its first frame,
        as its render is. Filling in one frame from elsewhere would make a reference depend on how the store was filled. One missing or invalid sample recaptures the set."""
        jobs = []
        for beat in beats:
            frames = sorted(set(self.samples(beat)) | set((extra or {}).get(beat["beat_id"], [])))
            valid = [self.ref_path(beat, f).is_file() and sentinel.receipt_valid(store.read_json(str(self.ref_path(beat, f)) + ".json"), beat["start_frame"]) for f in frames]
            if not all(valid):
                jobs += [{"frame": f, "beat": beat["beat_id"], "from": beat["start_frame"], "out": str(self.ref_path(beat, f)), "want": sentinel.expected(f, beat, self.map)} for f in frames]
        return sorted(jobs, key=lambda j: j["frame"])

    def start_refs(self, tmp, jobs, name):
        if not jobs:
            return None
        job = self.job(tmp, name, frames=jobs, page_frames=REF_PAGE_FRAMES)
        return node(REFS, None, job, tmp / f"{name}.log")

    def forget_refs(self, beat):
        """A file with no receipt counts as absent, so the next round recaptures this beat's set."""
        for receipt in self.ref_path(beat, 0).parent.glob("*.json"):
            receipt.unlink()

    def recapture(self, tmp, beats, extra, name):
        """Captures whatever these beats still lack, and waits. A references process that died leaves beats short, and a beat is never judged on what happened to get written."""
        jobs = self.ref_jobs(beats, extra)
        if jobs:
            finish_all([self.start_refs(tmp, jobs, name)], 300 + 6 * len(jobs))

    def stills(self, beat, frames):
        """Decoded references for these frames. None for any frame without a valid one."""
        return sentinel.load_stills(self.ref_path(beat, 0).parent, frames, *self.frame_size)

    def inspect(self, beat, folder):
        """Decodes a rendered beat. Returns what it holds, or why it cannot be a segment."""
        video = folder / "segment.mp4"
        frames = beat["end_frame"] - beat["start_frame"]
        result = store.read_json(str(video) + ".json")
        if result is None:
            error = store.read_json(str(video) + ".error.json", {})
            return {"problem": error.get("error", "no result from the worker"), "started": bool(error)}
        wanted = [f - beat["start_frame"] for f in self.samples(beat)]
        try:
            rows, picked, suspects = sentinel.scan(video, *self.frame_size, wanted, keep_suspects=SUSPECTS_MAX)
        except RuntimeError as e:
            return {"problem": f"does not decode: {str(e)[:300]}", "started": True}
        stream = stitcher.probe_video(video)
        problem = None
        if len(rows) != frames or stream["packets"] != frames:
            problem = f"{len(rows)} frames and {stream['packets']} packets, expected {frames}"
        elif stream["has_b_frames"] != 0:
            problem = "has B-frames"
        return {"problem": problem, "started": True, "rows": rows, "picked": picked, "suspects": suspects, "stream": stream, "result": result}

    def judge(self, beat, seen):
        a = beat["start_frame"]
        frames = sorted(set(self.samples(beat)) | {a + n for n in seen["suspects"][:SUSPECTS_MAX]})
        stills = self.stills(beat, frames)
        record = sentinel.compare({a + n: data for n, data in seen["picked"].items()}, stills, frames, *self.frame_size, self.region_top)
        record["unsampled"] = beat["end_frame"] - a - len(frames)
        record["clip_suspects"] = len(seen["suspects"])
        return record

    def build_record(self, beat, folder, seen, record, retries):
        video = folder / "segment.mp4"
        content = sha("\n".join(seen["rows"]))
        (folder / "segment.framemd5").write_text("\n".join(seen["rows"]) + "\n", encoding="utf8", newline="\n")
        store.write_json(folder / "segment.json", {
            "schema": store.SCHEMA, "beat_id": beat["beat_id"], "start_frame": beat["start_frame"], "end_frame": beat["end_frame"],
            "input_key": self.keys[beat["beat_id"]], "profile": self.profile["name"], "profile_hash": self.profile_hash, "profile_full": self.profile,
            "file": "segment.mp4", "file_sha256": sound_mix.file_hash(video), "bytes": video.stat().st_size,
            "decoded": {"frames": len(seen["rows"]), "content_hash": content}, "stream": seen["stream"],
            "render": {"workers": self.workers, "page_frames_before": seen["result"]["page_frames_before"], "retries": retries, "capture_ms": seen["result"]["capture_ms"], "engine_hash": self.engine},
            "sentinel": {k: record.get(k) for k in ("status", "sampled", "unsampled", "min_psnr", "min_psnr_region", "psnr_min", "max_block", "block_max", "clip_suspects")}})
        Path(str(video) + ".json").unlink(missing_ok=True)

    def render_round(self, tmp, todo, number):
        """One attempt at these beats. Returns (published beat ids, failures). A failed sample is discarded here and retried in a fresh session."""
        started = time.perf_counter()
        folders, procs = {}, []
        for slot, group in enumerate(assign([self.beats[i] for i in todo], min(self.workers, len(todo)))):
            ranges = []
            for beat in group:
                folder = tmp / f"round{number}-{beat['beat_id']}"
                folder.mkdir()
                folders[beat["beat_id"]] = folder
                entry = {"id": beat["beat_id"], "start": beat["start_frame"], "end": beat["end_frame"], "path": str(folder / "segment.mp4")}
                if self.inject and beat["beat_id"] in self.inject["beats"] and number < self.inject["rounds"]:
                    entry["inject"] = {"kind": self.inject["kind"]}
                ranges.append(entry)
            job = self.job(tmp, f"round{number}-worker{slot}", ranges=ranges, result=str(tmp / f"round{number}-worker{slot}-result.json"),
                           fresh=number > 0, page_rotate_frames=self.profile["page_rotate_frames"])
            procs.append(node(RENDER, "capture", job, tmp / f"round{number}-worker{slot}.log"))
        refs = self.start_refs(tmp, self.ref_jobs([self.beats[i] for i in todo]), f"round{number}-refs")
        watched = procs + ([refs] if refs else [])
        codes = finish_all(watched, 300 + 3 * sum(self.beats[i]["end_frame"] - self.beats[i]["start_frame"] for i in todo))
        self.timed("render", started)
        self.worker_results = getattr(self, "worker_results", []) + [store.read_json(tmp / f"round{number}-worker{i}-result.json") for i in range(len(procs))]

        started = time.perf_counter()
        with ThreadPoolExecutor(4) as pool:
            seen = dict(zip(todo, pool.map(lambda i: self.inspect(self.beats[i], folders[i]), todo)))
        extra = {i: [self.beats[i]["start_frame"] + n for n in s["suspects"][:SUSPECTS_MAX]] for i, s in seen.items() if s.get("suspects")}
        self.recapture(tmp, [self.beats[i] for i in todo if not seen[i]["problem"]], extra, f"round{number}-refs-again")
        with ThreadPoolExecutor(4) as pool:
            verdicts = dict(zip(todo, pool.map(lambda i: self.judge(self.beats[i], seen[i]) if not seen[i]["problem"] else None, todo)))
        self.timed("verify", started)

        passed, failures = [], {}
        for i in todo:
            if seen[i]["problem"]:
                failures[i] = {"why": seen[i]["problem"], "started": seen[i]["started"]}
            elif verdicts[i]["status"] == "FAIL":
                failures[i] = {"why": f"sentinel failed: {verdicts[i]['failed'][:4]}", "started": True, "sentinel": verdicts[i]}
                self.forget_refs(self.beats[i])  # the reference may be the bad one, and a retry against it could never pass
            elif seen[i]["result"]["injected"]:
                failures[i] = {"why": "injected fault was not detected", "started": True, "undetected": True, "sentinel": verdicts[i]}
            elif verdicts[i]["status"] != "PASS":
                failures[i] = {"why": f"no valid reference for frames {verdicts[i]['unverified'][:6]}", "started": True, "references_missing": verdicts[i]["unverified"]}
            else:
                passed.append(i)
        if passed and project_stamp(self.project, ownership.load(self.project) or {"composition_rev": None}) != self.stamp:
            raise Refused("the project changed during this render: nothing from it was published")
        started = time.perf_counter()
        for i in passed:
            self.build_record(self.beats[i], folders[i], seen[i], verdicts[i], number)
            store.publish(self.root, folders[i], self.profile_hash, self.keys[i], force=self.force)
        self.timed("publish", started)
        print(f"round {number}: {len(passed)} published, {len(failures)} failed, worker exits {codes}", flush=True)
        return passed, failures

    def render(self, tmp, todo):
        """Renders beats, retrying what fails in fresh sessions. Stops the run if a beat is still bad after RETRIES, with no partial segment."""
        log = []
        for number in range(1 + RETRIES):
            if not todo:
                break
            passed, failures = self.render_round(tmp, todo, number)
            log.append({"round": number, "beats": todo, "published": passed, "failures": failures})
            todo = list(failures)
        return log, todo

    def owner_audit(self):
        """Runs in the page before anything renders. A tween that reaches past its owner makes every key wrong, and no later check can see that on a beat it left alone."""
        conform = ROOT / "tools" / "beat_check" / "conform.py"
        if not conform.is_file():
            return "UNVERIFIED"
        started = time.perf_counter()
        command = [sys.executable, str(conform), str(self.project), "--audit", "--store", str(self.root)]
        status = check_status(command, AUDIT_SECONDS)[0]
        if status == "UNVERIFIED":  # a page that would not open on a busy machine is not a finding. Once more, then it stops the run
            status = check_status(command, AUDIT_SECONDS)[0]
        self.timed("audit", started)
        return status

    def finish(self, change, tmp, failed=False):
        """Stitches, captures any reference the picture lacks, checks, and only then moves current.json. Returns the run's status."""
        started = time.perf_counter()
        bed = stitcher.audio_bed(self.project, self.root)
        self.timed("audio_bed", started)
        if ownership.load(self.project) is None or project_stamp(self.project, self.map) != self.stamp:
            raise Refused("the project changed during this render: nothing was stitched")
        started = time.perf_counter()
        record, folder = stitcher.stitch(self.root, self.project, self.lock, self.map, self.profile, self.profile_hash, self.engine, self.keys, bed)
        self.timed("stitch", started)
        records = [store.find(self.root, self.profile_hash, self.keys[b]) for b in self.beats]
        change["stitched"] = str(folder / record["file"])
        change["file_sha256"] = record["file_sha256"]
        # As each segment was judged when it rendered, on the samples of that moment. O5 in the checks is the result for this picture.
        change["sentinel_at_render"] = {"status": worst([r["sentinel"]["status"] for r in records]), "beats_unverified": [r["beat_id"] for r in records if r["sentinel"]["status"] == "UNVERIFIED"],
                                        "frames_sampled": sum(len(r["sentinel"]["sampled"]) for r in records), "frames_unsampled": sum(r["sentinel"]["unsampled"] for r in records),
                                        "min_psnr": min(r["sentinel"]["min_psnr"] or 99 for r in records), "min_psnr_region": min(r["sentinel"]["min_psnr_region"] or 99 for r in records)}
        started = time.perf_counter()
        beats = list(self.beats.values())
        self.recapture(tmp, beats, None, "finish-refs")
        self.timed("refs_after", started)
        change["references_missing"] = sorted({j["frame"] for j in self.ref_jobs(beats)})
        started = time.perf_counter()
        change["checks"], change["checks_unfinished"] = self.run_checks(folder / record["file"], self.touched(change))
        self.recheck_references(change, record, folder / record["file"], tmp)
        self.timed("checks", started)
        status = "FAIL" if failed else worst([change["sentinel_at_render"]["status"], *change["checks"].values()])
        change["current_moved"] = store.set_current(self.root, self.profile["name"], stitcher.current_entry(record, folder), status, not change["checks_unfinished"])
        clear_approval(self.root, record["file_sha256"])
        change["store"] = store.evict(self.root)
        return status

    def touched(self, change):
        """What the source check covers, in beat order: what the change reached, whether or not it had to render, and whatever did render. A draft has no invalidate."""
        beats = set(change.get("invalidate", {}).get("beats", [])) | set(change.get("rendered") or [])
        return [b for b in self.beats if b in beats]

    def source_check(self, picture, beats):
        tool = ROOT / "tools" / "beat_check" / "conform.py"
        if not tool.is_file():
            return "UNVERIFIED", False
        scope = ["--beats", ",".join(beats)] if beats and len(beats) < len(self.beats) else ["--all"]
        return check_status([sys.executable, str(tool), str(self.project), *scope, "--render", str(picture), "--store", str(self.root)], CHECK_SECONDS)

    def output_check(self, picture):
        tool = ROOT / "tools" / "beat_check" / "output.py"
        if not tool.is_file():
            return "UNVERIFIED", False
        return check_status([sys.executable, str(tool), str(picture), "--project", str(self.project), "--store", str(self.root)], CHECK_SECONDS)

    def run_checks(self, picture, beats):
        """Workstream C's two checks: each one's status, and the names of any that did not run to the end. A tool that is not there, or that hangs, is UNVERIFIED and unfinished, never a pass."""
        results = {"source": self.source_check(picture, beats), "output": self.output_check(picture)}
        return {name: r[0] for name, r in results.items()}, [name for name, r in results.items() if not r[1]]

    def recheck_references(self, change, record, picture, tmp):
        """A bad reference clears itself when its beat renders. Under a reused segment nothing renders, so O5 would fail on every run until someone deleted it.
        So once, for the beats O5 failed on that did not render here, recapture their references and compare again. A fresh capture cannot hide a bad segment: it fails the same way."""
        report = store.read_json(self.root / "checks" / record["composition_rev"][:16] / f"output-{record['file_sha256'][:16]}.json", {})
        rendered = set(change.get("rendered") or [])
        suspects = [b for b in report.get("checks", {}).get("O5", {}).get("failed_beats", []) if b not in rendered and b in self.beats]
        if change["checks"]["output"] != "FAIL" or not suspects:
            return
        beats = [self.beats[b] for b in suspects]
        for beat in beats:
            self.forget_refs(beat)
        self.recapture(tmp, beats, None, "recheck-refs")
        change["references_recaptured"] = suspects
        change["references_missing"] = sorted({j["frame"] for j in self.ref_jobs(list(self.beats.values()))})
        status, finished = self.output_check(picture)
        change["checks"]["output"] = status
        change["checks_unfinished"] = [name for name in change["checks_unfinished"] if name != "output"] + ([] if finished else ["output"])

    def close(self, change, status, wall):
        change.update({"status": status, "composition_rev": self.map["composition_rev"], "lock_revision": self.lock["revision"], "profile": self.profile["name"], "workers": self.workers,
                       "wall_s": round(wall, 2), "timings": self.timings, "worker_results": getattr(self, "worker_results", [])})
        path = store.next_change(self.root)
        store.write_json(path, change)
        summary = {k: v for k, v in change.items() if k not in ("rounds", "reasons", "worker_results", "invalidate")}
        print(json.dumps(summary, indent=1, ensure_ascii=False))
        print("change record:", path)
        # A review picture's best status is UNVERIFIED, because of loudness. Missing references and a check that did not finish are different things, so they do not read the same
        return 1 if status == "FAIL" else 3 if change.get("references_missing") or change.get("checks_unfinished") else 0


def clear_approval(root, file_sha):
    """Any picture change clears approval. beat_review reads this file, and a store with none has nothing to clear."""
    approved = Path(root) / "approvals" / "active.json"
    if store.read_json(approved, {}).get("file_sha256", file_sha) != file_sha:
        approved.unlink()


def damaged(run, todo):
    """Beats about to render because the segment under their key no longer matches its record."""
    return [b for b in todo if store.find(run.root, run.profile_hash, run.keys[b]) is not None and not run.stored(b)]


def draft(run, args, tmp, started):
    run.ensure_plan()
    run.prepare(tmp)
    todo = list(run.beats) if args.force else [b for b in run.beats if not run.stored(b)]
    if run.inject and args.inject_beats:
        todo = [b for b in run.beats if b in run.inject["beats"]]
    only = args.only.split(",") if isinstance(getattr(args, "only", None), str) else None  # one beat for a look at native size. It stops before stitching, so it never makes a picture
    if only:
        if set(only) - set(run.beats):
            raise Refused(f"no such beats: {sorted(set(only) - set(run.beats))}")
        todo = [b for b in todo if b in only]
    change = {"kind": "draft", "rendered": todo, "reused": [b for b in run.beats if b not in todo], "damaged": damaged(run, todo), "injected": run.inject}
    if only:
        change["segments"] = {b: str(store.segment_dir(run.root, run.profile_hash, run.keys[b]) / "segment.mp4") for b in only}
    return render_and_finish(run, change, tmp, todo, started, stitch_after=not (run.inject or only))


def change_cmd(run, args, tmp, started):
    base = store.latest(run.root, run.profile["name"])
    if not base:
        raise Refused(f"no stitched {run.profile['name']} picture yet: run draft first")
    old_dir = run.root / "stitched" / base["stitched"]
    old_map = store.read_json(old_dir / "ownership.json")
    old_stitch = store.read_json(old_dir / "stitch.json")
    if not old_map or not old_stitch:
        raise Refused(f"stitched record is damaged: {old_dir}")
    invalidated = ownership.invalidate(old_map, run.map, run.lock)
    run.ensure_plan()
    run.prepare(tmp)
    old_keys = {b["beat_id"]: b["key"] for b in old_stitch["beats"]}
    engine_changed = old_stitch["engine_hash"] != run.engine or old_stitch["profile_hash"] != run.profile_hash
    todo, missed = render_set(run.lock, run.keys, invalidated["beats"], run.stored, old_keys, engine_changed, args.force)
    if run.inject and args.inject_beats:
        todo = [b for b in todo if b in run.inject["beats"]]
    change = {"kind": args.kind or "change", "invalidate": invalidated, "share": invalidated["share"], "new_media_plan": invalidated["new_media_plan"], "all_reasons": invalidated["all_reasons"],
              "owners_changed": invalidated["owners_changed"], "engine_changed": engine_changed, "rendered": todo, "reused": [b for b in run.beats if b not in todo], "damaged": damaged(run, todo), "under_invalidated": missed, "injected": run.inject}
    return render_and_finish(run, change, tmp, todo, started, stitch_after=not run.inject, failed=bool(missed))


def render_and_finish(run, change, tmp, todo, started, stitch_after=True, failed=False):
    change["owner_audit"] = run.owner_audit()
    if change["owner_audit"] != "PASS":
        change.update(would_render=todo, rendered=[], reused=[], rounds=[])
        print(f"stopped before rendering: the owner audit is {change['owner_audit']}", flush=True)
        return run.close(change, "FAIL", time.perf_counter() - started)
    rounds, unresolved = run.render(tmp, todo) if todo else ([], [])
    change["rounds"] = rounds
    change["retried"] = sorted({b for r in rounds[1:] for b in r["beats"]})
    if unresolved:
        change["unresolved"] = unresolved
        print(f"stopped: {len(unresolved)} beats still bad after {RETRIES} retries, no partial segment published: {unresolved}", flush=True)
        return run.close(change, "FAIL", time.perf_counter() - started)
    if not stitch_after:
        status = worst([store.find(run.root, run.profile_hash, run.keys[b])["sentinel"]["status"] for b in todo])
        return run.close(change, "FAIL" if failed else status, time.perf_counter() - started)
    try:
        status = run.finish(change, tmp, failed)
    except (ValueError, RuntimeError, subprocess.CalledProcessError) as e:
        change["refused"] = str(e)[:2000]
        print("REFUSED:", change["refused"], flush=True)
        return run.close(change, "FAIL", time.perf_counter() - started)
    return run.close(change, status, time.perf_counter() - started)


def stitch_cmd(run, args, tmp, started):
    run.ensure_plan()
    run.prepare(tmp)
    return render_and_finish(run, {"kind": "stitch", "rendered": [], "reused": list(run.beats)}, tmp, [], started)


def refs_cmd(run, args, tmp, started):
    """Captures every reference the samples need and the store lacks, with no render. A new events.json adds sample frames, and output.py reads these."""
    run.ensure_plan()
    run.prepare(tmp)
    beats = list(run.beats.values())
    jobs = run.ref_jobs(beats)
    wall = time.perf_counter()
    if (finish_all([run.start_refs(tmp, jobs, "refs")], 300 + 6 * len(jobs)) if jobs else [0]) != [0]:
        print((tmp / "refs.log").read_text(encoding="utf8", errors="replace")[-1500:])
        return run.close({"kind": "refs", "captured": len(jobs)}, "FAIL", time.perf_counter() - started)
    run.timed("refs", wall)
    left = sorted({j["frame"] for j in run.ref_jobs(beats)})
    print(f"{len(jobs)} references captured, {len(left)} still without a valid one", flush=True)
    return run.close({"kind": "refs", "captured": len(jobs), "references_missing": left}, "UNVERIFIED" if left else "PASS", time.perf_counter() - started)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Beat renderer")
    parser.add_argument("command", choices=["draft", "change", "stitch", "refs"])
    parser.add_argument("project")
    parser.add_argument("--profile", default="review")
    parser.add_argument("--workers", type=int)
    parser.add_argument("--force", action="store_true", help="draft: render every beat. change: render every touched beat. Replaces their segments, so an older picture that used them stops validating")
    parser.add_argument("--kind", help="change: the note kind for the change record")
    parser.add_argument("--only", help="draft: render only these comma-separated beats and stop before stitching")
    parser.add_argument("--store", help="tests: a store other than the project's")
    parser.add_argument("--inject-fault", choices=["viewport", "dom", "clear", "gpu", "crash"], help="tests: show a fault in these beats. The run stops before stitching.")
    parser.add_argument("--inject-beats", help="tests: comma-separated beats")
    parser.add_argument("--inject-rounds", type=int, default=1, help="tests: how many attempts the fault lasts")
    args = parser.parse_args(argv)
    started = time.perf_counter()
    try:
        run = Run(args)
    except Refused as e:
        print("REFUSED:", e)
        return 2
    try:
        store.lock(run.root)
    except RuntimeError as e:
        print("REFUSED:", e)
        return 2
    tmp = store.new_tmp(run.root)
    try:
        return {"draft": draft, "change": change_cmd, "stitch": stitch_cmd, "refs": refs_cmd}[args.command](run, args, tmp, started)
    except (Refused, ValueError, subprocess.CalledProcessError) as e:
        print("REFUSED:", e)
        return 2
    finally:
        store.clear_tmp(run.root)
        store.unlock(run.root)


if __name__ == "__main__":
    sys.exit(main())
