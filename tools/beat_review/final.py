"""The final path. PLAN-V2-BEAT-REVIEW.md Workstream E, phase 5.

  python tools/beat_review/final.py build <project> --spec 1080p30 --workers 4
  python tools/beat_review/final.py build <project> --spec 4k60 --workers 6 [--swaps swaps.json]
  python tools/beat_review/final.py probe <project> --spec 4k60 --workers 4 --beats b19,b20 [--swaps swaps.json]
  python tools/deliver.py <project> <base> --mode final --stitched <file that build printed>

Three things stay separate. The composition revision is what the picture should be (ownership.json). A render artifact is one encoded file of it (stitch.json). Sound is bound to picture_rev, which
hashes content, so a new render profile leaves it alone. Approval is bound to the composition, and a final is a new render of that composition, never a copy of the review picture.

build refuses without a passing approval record. It freezes everything that made the picture into work/<id>-final-<rev16>/, including tools_local, and proves the copy complete by rebuilding it byte
for byte. It renders there in a store of its own, so nothing is reused from review, and the output check runs on the delivered file, not this one, because only that file is mastered.

Sound is not part of a composition, so a new sheet or cue bytes after a final is a sound revision: work/<id>-final-<rev16>-sound-<identity8>/, the same bundle by hard link with new sheet and cue copies. Nothing renders again, and
a bundle is still never changed. The revision also includes home waiver hashes. deliver.py refuses a bundle whose sound identity is not the project's. At 4K60 the derivative is rebuilt from the sound revision,
which is a whole render, because rebinding makes its sheet its own.

A 4K60 or swapped final is a derivative revision: its own bundle and composition revision, and derivative.json says exactly what changed from the approved one: the fps edits to the sources, each
swap, the frame map, and sound's rebinding. Anything else that differs refuses it. A swap needs authorized_by. Naming a file in --source-swap only states what is expected, and authorizes nothing.
"""
import argparse, contextlib, json, math, os, re, shutil, subprocess, sys, time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import project_root
ROOT = project_root()
sys.path[:0] = [str(HERE), str(ROOT / "tools" / "beat_check"), str(ROOT / "tools" / "beat_render"), str(ROOT / "tools")]
import lock as beat_lock
import confine
import output as checks
import ownership
import run as renderer
import sentinel
import sound_mix
import stitch as stitcher
import store
from common import frame_of, source_frame_time, sha

OK = ("PASS", "RECONCILED", "APPROVED")
BUNDLE = "bundle.json"
DERIVATIVE = "derivative.json"
BUILD = "final.json"
PROFILES = "final-profiles.json"
WAIVER_FILES = ("fixture.json", "waivers.json")
GENERATED = ("index.html", "ownership.json", "beats.lock.json", "events.json")  # build.py writes these
NOT_FROZEN = (".hyperframes/", "renders/", "snaps", "verification/", "tools_local/_bak/", "tools_local/__pycache__/")  # what no picture reads, as review.py's SKIP
SPECS = {"1080p30": {"profile": "final", "fps": 30}, "4k30": {"profile": "final-4k30", "fps": 30}, "4k60": {"profile": "final-4k60", "fps": 60}}
FINAL_4K60 = {"name": "final-4k60", "width": 2160, "height": 3840, "dpr": 2, "fps": 60,
              "capture": {"method": "screenshot", "format": "jpeg", "quality": 100, "gpu": "hardware"}, "extraction": "auto",
              "encoder": {"lib": "libx264", "preset": "medium", "crf": 16, "pix_fmt": "yuv420p", "gop": "closed-per-segment", "bframes": 0},
              "threads": {"decoder": 1, "filter": 1, "encoder": 4}, "page_rotate_frames": 240}
# 4K on the review's own 30 fps grid: no fps edits, so a derivative is only its swaps. Half the frames of 4k60.
FINAL_4K30 = dict(FINAL_4K60, name="final-4k30", fps=30)
FINALS_4K = {p["name"]: p for p in (FINAL_4K60, FINAL_4K30)}
# Every place ivory's sources fix the frame grid. Each must match exactly once, or the derivative is refused: a new builder has to be read, not guessed at.
FPS_EDITS = [("tools_local/build.py", r"^FPS = 30\r?$", "FPS = {fps}"), ("tools_local/build.py", r'data-fps="30"', 'data-fps="{fps}"'),
             ("tools_local/timeline.js", r"FPS = 30;", "FPS = {fps};")]
HTML_MAY_DIFFER = re.compile(r'<video\b|data-fps=|FPS = \d+;')
ALIGN_SAMPLES = 48
ALIGN_PSNR = 26.0  # the same camera frames at a different size score far above this. Measured in stage1/phase5-final.md
CHECK_SECONDS_4K = 5400


class Refused(ValueError):
    """Fail closed: nothing is delivered."""


def home_of(project):
    return Path(project).resolve().parents[1]


def editorial(home):
    return Path(home) / "v2" / "editorial"


def complete_profile(name):
    """The complete profile of a spec. The base profile is read from profiles.json, so a final's hash is the store's."""
    data = json.loads(renderer.PROFILES.read_text(encoding="utf8"))
    return FINALS_4K.get(name) or data["profiles"][name]


def built(project):
    """(map, lock) of a project whose generated files are its sources' current output."""
    project = Path(project).resolve()
    m = ownership.load(project)
    if m is None:
        raise Refused(f"no valid ownership.json for this index.html in {project}: run the build")
    try:
        lock = beat_lock.load(project)
    except (OSError, ValueError) as e:
        raise Refused(f"no valid beats.lock.json: {e}")
    if m["lock_revision"] != lock["revision"]:
        raise Refused("ownership.json is not of this beats.lock.json: run the build")
    stale = renderer.stale_files(project, m)
    if stale:
        raise Refused(f"the build is stale for: {', '.join(stale[:8])}")
    return m, lock


# ---- approval


def approval_of(project, composition_rev, lock_revision):
    """The passing record of this exact composition, still the approved one. Anything else refuses."""
    import review
    pic = review.picture(project)
    if pic and review.open_notes(project, store.root_of(project), pic):
        raise Refused("notes still open: close the round or let Chase drop them before building a final")
    folder = store.root_of(project) / "approvals"
    records = [r for r in (store.read_json(p) for p in sorted(folder.glob("*.json"))) if r and "approved_file_sha256" in r]
    same = [r for r in records if r.get("composition_rev") == composition_rev and r.get("lock_revision") == lock_revision]
    if not same:
        raise Refused(f"no approval record for composition {composition_rev[:16]}: {len(records)} record(s) of other compositions")
    good = [r for r in same if r.get("result") in OK]
    if not good:
        raise Refused(f"the approval record for {composition_rev[:16]} did not pass: {[r.get('result') for r in same]}")
    active = store.read_json(folder / "active.json", {})
    if active.get("composition_rev") != composition_rev:
        raise Refused(f"composition {composition_rev[:16]} is not the approved picture any more: a later picture cleared it, approve it again")
    record = next((r for r in good if r["approved_file_sha256"] == active.get("file_sha256")), good[-1])
    picture = next(iter(store.root_of(project).glob(f"stitched/*-{record['approved_file_sha256'][:16]}-{composition_rev[:16]}/stitch.json")), None)
    stitched = store.read_json(picture, {}) if picture else {}
    if stitched.get("file_sha256") != record["approved_file_sha256"] or sha(record.get("profile")) != stitched.get("profile_hash"):
        raise Refused("the approval record names no stitched picture of this composition at its complete profile")
    return record


# ---- the frozen bundle


def file_rows(folder):
    return {rel: sound_mix.file_hash(folder / rel) for rel in ownership.project_files(folder) if not rel.startswith(NOT_FROZEN)}


def rebuild(ed):
    r = subprocess.run([sys.executable, "tools_local/build.py"], cwd=ed, capture_output=True, text=True, encoding="utf8", errors="replace")
    shutil.rmtree(Path(ed) / "tools_local" / "__pycache__", ignore_errors=True)
    if r.returncode:
        raise Refused(f"the bundle does not build: {r.stdout[-400:]}{r.stderr[-800:]}")


def sheet_hash(project):
    path = Path(project) / "sound.json"
    return sound_mix.file_hash(path) if path.is_file() else None


def sound_identity(project):
    try:
        return sound_mix.sound_identity(project)
    except (OSError, ValueError) as e:
        raise Refused(str(e)) from e


def home_rows(home):
    """The waiver lists a final's output check reads. They sit outside v2/editorial, and they decide its status."""
    return {name: sound_mix.file_hash(Path(home) / name) for name in WAIVER_FILES if (Path(home) / name).is_file()}


@contextlib.contextmanager
def building(target):
    """Where a bundle is made. A refusal leaves nothing behind."""
    folder = Path(target).with_name(Path(target).name + ".building")
    shutil.rmtree(folder, ignore_errors=True)
    try:
        yield folder
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def link_or_copy(a, b):
    try:
        os.link(a, b)
    except OSError:
        shutil.copy2(a, b)


def copy_home(home, target):
    """What the build and the checks read two levels up: the small JSON beside the project, and raw's word files. Never the raw video."""
    for path in [*home.glob("*.json"), *(home / "raw").glob("*.json")]:
        rel = path.relative_to(home)
        if path.name in (BUNDLE, BUILD, DERIVATIVE, PROFILES):
            continue
        (target / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target / rel)


def freeze(project):
    """Copies everything that made this composition to work/<id>-final-<rev16>/, and proves it complete: tools_local rebuilds it byte for byte. Returns the home of the bundle. A bundle is never changed."""
    project = Path(project).resolve()
    m, lock = built(project)
    sound = sound_identity(project)
    home = home_of(project)
    target = home.parent / f"{home.name}-final-{m['composition_rev'][:16]}"
    if (target / BUNDLE).is_file():
        return sound_revision(target, project)
    with building(target) as work:
        ed = editorial(work)
        for rel in ownership.project_files(project):
            if not rel.startswith(NOT_FROZEN):
                (ed / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(project / rel, ed / rel)
        copy_home(home, work)
        files = file_rows(ed)
        rebuild(ed)
        moved = [rel for rel, digest in file_rows(ed).items() if files.get(rel) != digest]
        if moved:
            raise Refused(f"the bundle's sources do not rebuild this composition, these files changed: {moved[:8]}")
        if sound_identity(ed) != sound or sound_identity(project) != sound:
            raise Refused("sound inputs changed while freezing")
        store.write_json(work / BUNDLE, {"schema": 1, "source": str(project), "composition_rev": m["composition_rev"], "approved_composition_rev": m["composition_rev"], "lock_revision": lock["revision"],
                                         "picture_rev": sound_mix.picture_rev(ed), "sheet_sha256": sound["sheet_sha256"], "sound_identity": sound, "home_files": home_rows(work), "files": files, "created": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
        os.replace(work, target)
    return target


def bundle_sheet(record):
    """The project sheet a bundle was frozen with. A derivative's own sheet differs, because rebinding writes to it."""
    return record.get("sheet_sha256", record["files"].get("sound.json"))


def sound_revision(target, project):
    """This composition with the project's sound and waiver inputs. Hard links share the picture; every replaced input is unlinked first."""
    sound, record = sound_identity(project), store.read_json(target / BUNDLE)
    problems = bundle_problems(target)
    if problems:
        raise Refused("; ".join(problems[:6]))
    held = record.get("sound_identity") or sound_identity(editorial(target))
    homes = home_rows(home_of(project))
    if sound == held and homes == record.get("home_files", {}):
        return target
    revision = target.with_name(f"{target.name}-sound-{sha([sound, homes])[:8]}")
    if (revision / BUNDLE).is_file():
        problems = bundle_problems(revision)
        if problems:
            raise Refused("; ".join(problems[:6]))
        return revision
    with building(revision) as work:
        shutil.copytree(target, work, copy_function=link_or_copy, ignore=shutil.ignore_patterns("renders", "tmp", "run.lock", BUILD, PROFILES, "*-delivered-*"))
        ed = editorial(work)
        changed = {"sound.json", *sound["cue_files"]}
        for rel in changed:
            (ed / rel).parent.mkdir(parents=True, exist_ok=True)
            (ed / rel).unlink(missing_ok=True)  # never write through a link to the old bundle
            shutil.copy2(Path(project) / rel, ed / rel)
        for name in WAIVER_FILES:
            (work / name).unlink(missing_ok=True)
            if name in homes:
                shutil.copy2(home_of(project) / name, work / name)
        files = file_rows(ed)
        moved = [rel for rel in sorted(set(files) | set(record["files"])) if rel not in changed and files.get(rel) != record["files"].get(rel)]
        if moved:
            raise Refused(f"a sound revision moved more than the sheet: {moved[:8]}")
        if sound_mix.picture_rev(ed) != record["picture_rev"]:
            raise Refused("a cue replacement changed the picture too: rebuild and approve that composition")
        if sound_identity(ed) != sound or home_rows(work) != homes:
            raise Refused("sound or waiver inputs changed while freezing")
        store.write_json(work / BUNDLE, {**record, "sheet_sha256": sound["sheet_sha256"], "sound_identity": sound, "home_files": homes, "sound_of": target.name, "files": files, "created": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
        os.replace(work, revision)
    return revision


def bundle_problems(home):
    """Every way a bundle differs from what it recorded. A file added, changed or gone is a swap nobody listed."""
    record = store.read_json(Path(home) / BUNDLE)
    if record is None:
        return [f"no {BUNDLE} in {home}: a final is built from a frozen bundle"]
    now = file_rows(editorial(home))
    held = home_rows(home)
    frozen = record.get("home_files", held)  # a bundle from before waiver files were frozen has no row
    return [f"{rel}: differs from the frozen bundle" for rel in sorted(set(now) | set(record["files"])) if now.get(rel) != record["files"].get(rel)] + \
           [f"{name}: differs from the frozen bundle" for name in sorted(set(held) | set(frozen)) if held.get(name) != frozen.get(name)]


# ---- a derivative revision


def edit_sources(ed, fps):
    """The fps edits, each matched exactly once. Returns what changed, for the record."""
    rows = []
    for rel, pattern, replacement in FPS_EDITS:
        path = Path(ed) / rel
        with open(path, encoding="utf8", newline="") as f:
            text = f.read()
        new, count = re.subn(pattern, replacement.format(fps=fps), text, flags=re.M)
        if count != 1:
            raise Refused(f"{rel}: {pattern} matched {count} times, expected 1. This builder's frame grid has not been read")
        with open(path, "w", encoding="utf8", newline="") as f:
            f.write(new)
        rows.append({"file": rel, "from": pattern, "to": replacement.format(fps=fps)})
    # Older ivory builders predate source_frame_time. Only the derivative changes: rebuilding review must keep every generated byte and key.
    path = Path(ed) / "tools_local/build.py"
    text = path.read_text(encoding="utf8")
    old = text
    for runs in ('plan["computed_stats"]["layout_runs"]', 'layout_runs(plan["beats"])'):
        line = f"runs = {runs}"
        if line in text:
            text = text.replace(line, f"runs = [[source_frame_time(a), source_frame_time(b) if b != END else b, k] for a, b, k in {runs}]", 1)
    text = text.replace('frame_of(b["start"], FPS), frame_of(b["end"], FPS)', 'frame_of(source_frame_time(b["start"]), FPS), frame_of(source_frame_time(b["end"]), FPS)')
    text = text.replace('"WINDOWS": owners.WINDOWS', '"WINDOWS": [[s, source_frame_time(a), source_frame_time(b)] for s, a, b in owners.WINDOWS]')
    # A chip on a layout switch must land with it. Off the source grid it opens one 60 fps frame ahead.
    text = text.replace('caps.append([c["on"], off,', 'caps.append([source_frame_time(c["on"]), source_frame_time(off) if off <= END else off,')
    text = text.replace('switches = [y["start"] for', 'switches = [source_frame_time(y["start"]) for')
    if text != old:
        if not re.search(r"^from common import .*\bsource_frame_time\b", text, re.M):
            text, count = re.subn(r"^from common import frame_of\r?$", "from common import frame_of, source_frame_time", text, flags=re.M)
            if count != 1:
                raise Refused("this builder's beat grid import has not been read")
        path.write_text(text, encoding="utf8", newline="\n")
        rows.append({"file": "tools_local/build.py", "from": "beat layout and face times", "to": "source_frame_time on the 30 fps source grid"})
    return rows


def stream_of(path):
    s = stitcher.probe_video(path)
    return {**s, "seconds": s["packets"] / eval_rate(s["r_frame_rate"])}


def eval_rate(rate):
    a, b = rate.split("/")
    return int(a) / int(b)


def grey(path, width=160):
    """Every frame of a video, small and grey, for an alignment check."""
    height = int(round(width * 9 / 16))
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"scale={width}:{height}:flags=area,format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype=np.uint8).reshape(-1, height, width)


def alignment(old, new):
    """A swap must be the same footage on the same frames. Returns (PSNR on the same frame numbers, the offset that scores best)."""
    a, b = grey(old), grey(new)
    if len(a) != len(b):
        return None, None
    picks = np.linspace(4, len(a) - 5, ALIGN_SAMPLES).astype(int)
    def score(offset):
        mse = np.mean((a[picks].astype(np.float32) - b[picks + offset].astype(np.float32)) ** 2)
        return 99.0 if mse == 0 else float(10 * np.log10(255 ** 2 / mse))
    scores = {offset: score(offset) for offset in range(-3, 4)}
    return round(scores[0], 2), max(scores, key=scores.get)


def check_swap(ed, row):
    """Same frames, same rate, same shape, at least as sharp, and the same footage on the same frames. Returns the record row. Any doubt refuses."""
    rel = row.get("path")
    new = Path(row.get("file", ""))
    if not str(row.get("authorized_by") or "").strip():
        raise Refused(f"{rel}: listing a swap does not authorize it, it needs authorized_by")
    if not str(row.get("why") or "").strip() or not str(row.get("source") or "").strip():
        raise Refused(f"{rel}: a swap names its source and why")
    if ownership.clean_path(rel) != rel or Path(rel).suffix.lower() not in (".mp4", ".mov", ".webm") or not (Path(ed) / rel).is_file() or not new.is_file():
        raise Refused(f"{rel}: a swap replaces one existing video in the project with one existing file")
    a, b = stream_of(Path(ed) / rel), stream_of(new)
    if a["packets"] != b["packets"] or a["r_frame_rate"] != b["r_frame_rate"]:
        raise Refused(f"{rel}: {b['packets']} frames at {b['r_frame_rate']}, the approved source has {a['packets']} at {a['r_frame_rate']}")
    if abs(a["width"] / a["height"] - b["width"] / b["height"]) > 0.002 or b["width"] < a["width"]:
        raise Refused(f"{rel}: {b['width']}x{b['height']} is not the shape of {a['width']}x{a['height']}, or is smaller")
    psnr, best = alignment(Path(ed) / rel, new)
    if psnr is None or best != 0 or psnr < ALIGN_PSNR:
        raise Refused(f"{rel}: not aligned with the approved source: {psnr} dB on the same frames, best offset {best}")
    return {"path": rel, "from_sha256": sound_mix.file_hash(Path(ed) / rel), "to_sha256": sound_mix.file_hash(new), "source": row["source"], "why": row["why"], "authorized_by": row["authorized_by"],
            "from": f"{a['width']}x{a['height']}", "to": f"{b['width']}x{b['height']}", "frames": a["packets"], "aligned_psnr": psnr, "best_offset": best}


def frame_map(base, lock):
    """The global map from the reviewed grid to the final one. Review frame n and final frame n x factor are the same instant. Whatever is timed between two review frames lands on the first
    final frame at its time. Beat cuts stay on the reviewed grid exactly. Any other shape refuses."""
    factor = lock["fps"] / base["fps"]
    if factor != int(factor) or factor < 1:
        raise Refused(f"{base['fps']} to {lock['fps']} fps is not a whole multiple")
    factor = int(factor)
    if [b["beat_id"] for b in base["beats"]] != [b["beat_id"] for b in lock["beats"]] or [b["layout"] for b in base["beats"]] != [b["layout"] for b in lock["beats"]]:
        raise Refused("the derivative's beats are not the approved beats")
    if lock["total_frames"] != math.ceil(lock["fps"] * base["duration"]):
        raise Refused(f"{lock['total_frames']} final frames, expected {math.ceil(lock['fps'] * base['duration'])}")
    rows = []
    for a, b in zip(base["beats"], lock["beats"]):
        if b["start_frame"] != factor * a["start_frame"]:
            raise Refused(f"{a['beat_id']}: starts on {b['start_frame']}, not {factor * a['start_frame']}")
        rows.append([a["beat_id"], a["start_frame"], a["end_frame"], b["start_frame"], b["end_frame"]])
    return {"rule": "Review frame n is final frame n x factor, the same instant. Beat starts use exactly that frame. Other animation changes may land between review frames; final frames are rendered at their own time, never interpolated.",
            "review_fps": base["fps"], "final_fps": lock["fps"], "factor": factor, "review_frames": base["total_frames"], "final_frames": lock["total_frames"], "beats": rows}


def check_events(base, new, factor):
    """Every event of the approved composition is in the derivative at the same time. Its frame is the same instant, or one frame earlier on the finer grid. A chip sits on the source grid, so its time may read as that grid's and its frame must be the same instant."""
    a, b = {e["event_id"]: e for e in base["events"]}, {e["event_id"]: e for e in new["events"]}
    if set(a) != set(b):
        raise Refused(f"events differ from the approved ones: {sorted(set(a) ^ set(b))[:8]}")

    def held(e, n):
        if e["event_id"].startswith("cap.") and "frame" in e and n.get("t") == source_frame_time(e.get("t")):
            return n["frame"] == factor * e["frame"]
        return e.get("t") == n.get("t") and ("frame" not in e or factor * e["frame"] - factor < n["frame"] <= factor * e["frame"])
    moved = [i for i, e in a.items() if not held(e, b[i])]
    if moved:
        raise Refused(f"events moved: {moved[:8]}")
    return {"events": len(a), "with_frames": sum("frame" in e for e in a.values())}


def check_timing(base, new, base_fps, fps):
    """The page's layout and scene windows must follow the same source grid as its lock, even with a builder we did not rewrite."""
    factor = fps / base_fps
    for name in ("runs", "windows"):
        old, rows = base[name], new[name]
        if len(old) != len(rows):
            raise Refused(f"the derivative's {name} differ from the approved ones")
        for a, b in zip(old, rows):
            identity, times = (2, (0, 1)) if name == "runs" else (0, (1, 2))
            if a[identity] != b[identity] or any(frame_of(b[i], fps) != factor * frame_of(a[i], base_fps) for i in times if a[i] != base["duration"]):
                raise Refused(f"the derivative's {name} leave the source grid: {a} -> {b}")
    return {name: len(new[name]) for name in ("runs", "windows")}


def check_html(old, new):
    """The derivative's page may differ from the approved page only in the frame grid and in video timing tags, which snap to it."""
    a, b = Path(old).read_text(encoding="utf8").splitlines(), Path(new).read_text(encoding="utf8").splitlines()
    if len(a) != len(b):
        raise Refused(f"the derivative's page has {len(b)} lines, the approved page {len(a)}")
    changed = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    def grid_table(x, y):
        pattern = r"\s*const (RUNS|WINDOWS|CAPS) = /\*@\1\*/(.*);\s*"
        left, right = re.fullmatch(pattern, x), re.fullmatch(pattern, y)
        if not left or not right or left[1] != right[1]:
            return False
        before, after = json.loads(left[2]), json.loads(right[2])
        if left[1] == "WINDOWS":
            return after == [[sel, source_frame_time(start), source_frame_time(stop)] for sel, start, stop in before]
        end = before[-1][1] if before else None
        return after == [[source_frame_time(start), source_frame_time(stop) if stop != end else stop, *rest] for start, stop, *rest in before]
    extra = [i + 1 for i in changed if not ((HTML_MAY_DIFFER.search(a[i]) and HTML_MAY_DIFFER.search(b[i])) or grid_table(a[i], b[i]))]
    if extra:
        raise Refused(f"the derivative's page changed outside its frame grid, lines {extra[:8]}")
    return {"lines_changed": len(changed)}


def derive(bundle, spec_name, swaps=None):
    """A frozen bundle, changed only as listed: the fps edits, then each authorized swap. Rebuilt from its sources, checked against the approved revision, and sound rebound. Returns the new bundle's home."""
    bundle = Path(bundle).resolve()
    spec, base = SPECS[spec_name], store.read_json(bundle / BUNDLE)
    problems = bundle_problems(bundle)
    if problems:
        raise Refused("; ".join(problems[:6]))
    old = editorial(bundle)
    lock0 = beat_lock.load(old)
    rows = (swaps or {}).get("swaps", [])
    gaps = confine.frame_gaps((old / "tools_local/timeline.js").read_text(encoding="utf8"), spec["fps"])
    for sel, t in gaps:
        print(f"FRAME GAP: show({sel}, {t}) lands before its tween at {spec['fps']} fps")
    tag = sha(["source-grid-v2", spec_name, [[r.get("path"), sound_mix.file_hash(r["file"]) if Path(r.get("file", "")).is_file() else None] for r in rows]])[:8]
    target = bundle.with_name(f"{bundle.name}-{spec_name}-{tag}")
    if (target / BUNDLE).is_file():
        return target
    sheet = sound_mix.sheet_of(old)
    if sheet.get("picture_rev") != sound_mix.picture_rev(old):
        raise Refused("sound.json is stale against the approved picture, and rebinding must not hide that: review it first")
    swapped = [check_swap(old, r) for r in rows]
    if len({r["path"] for r in swapped}) != len(swapped):
        raise Refused("a path is swapped twice")
    with building(target) as work:
        ed = editorial(work)
        shutil.copytree(old, ed, ignore=shutil.ignore_patterns("renders", ".hyperframes", "__pycache__"))
        copy_home(bundle, work)
        edits = edit_sources(ed, spec["fps"]) if spec["fps"] != lock0["fps"] else []
        for r, row in zip(rows, swapped):
            shutil.copyfile(r["file"], ed / row["path"])
        rebuild(ed)
        m, lock = built(ed)

        listed = {r["file"] for r in edits} | {r["path"] for r in swapped}
        before, after = base["files"], file_rows(ed)
        unlisted = [rel for rel in sorted(set(before) | set(after)) if before.get(rel) != after.get(rel) and rel not in listed and rel not in GENERATED]
        if unlisted:
            raise Refused(f"changed and not listed: {unlisted[:8]}")
        if sound_mix.file_hash(ed / "plan.json") != before["plan.json"]:
            raise Refused("plan.json changed")
        mapping = frame_map(lock0, lock)
        timing = check_timing(store.read_json(old / "ownership.json")["shared"]["timing"], m["shared"]["timing"], lock0["fps"], lock["fps"])
        events = check_events(store.read_json(old / "events.json"), store.read_json(ed / "events.json"), mapping["factor"])
        page = check_html(old / "index.html", ed / "index.html")
        media = {r["id"]: r for r in m["shared"]["media"]}
        if set(media) != {r["id"] for r in store.read_json(old / "ownership.json")["shared"]["media"]}:
            raise Refused("the derivative's videos are not the approved videos")
        why = f"derivative {spec_name} of {base['composition_rev'][:16]}: {len(edits)} fps edits, {len(swapped)} swaps. plan.json and every cue are unchanged."
        try:
            rev = sound_mix.rebind(ed, why, sound_mix.events_of(sound_mix.plan_of(old)))
        except ValueError as e:
            raise Refused(str(e)) from e
        cues_same = sound_mix.sheet_of(ed)["cues"] == sheet["cues"]
        record = {"schema": 1, "spec": spec_name, "base_composition_rev": base["composition_rev"], "base_lock_revision": base["lock_revision"], "composition_rev": m["composition_rev"], "lock_revision": lock["revision"],
                  "source_edits": edits, "swaps": swapped, "frame_map": mapping, "timing": timing, "frame_gaps": [{"selector": sel, "show_time": t, "fps": spec["fps"]} for sel, t in gaps], "events": events, "page": page, "cues_unchanged": cues_same,
                  "sound": {"from": base["picture_rev"], "to": rev, "cues": len(sheet["cues"]), "audition": "UNVERIFIED until Chase listens"}}
        if not cues_same:
            raise Refused("rebinding changed a cue")
        store.write_json(work / DERIVATIVE, record)
        store.write_json(work / BUNDLE, {**base, "composition_rev": m["composition_rev"], "lock_revision": lock["revision"], "picture_rev": rev, "sheet_sha256": bundle_sheet(base), "sound_identity": base.get("sound_identity") or sound_identity(old), "derivative": sha(record), "files": file_rows(ed), "created": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
        os.replace(work, target)
    return target


# ---- render


def renderer_for(spec_name, home):
    """run.py with the spec's profile added, and its output check left for the delivered file. A stitched final is unmastered, so O6 could only fail it on loudness."""
    data = json.loads(renderer.PROFILES.read_text(encoding="utf8"))
    data["profiles"].update(FINALS_4K)
    path = Path(home) / PROFILES
    store.write_json(path, data)
    renderer.PROFILES = path
    renderer.CHECK_SECONDS = CHECK_SECONDS_4K
    renderer.Run.output_check = lambda self, picture: ("UNVERIFIED", True)
    if spec_name != "1080p30":
        # conform.py's frame budgets (0.5 s to read, 2 frames from a word) are written for 30 fps. The derivative's events are held to the approved ones above, and the approved composition passed it.
        renderer.Run.source_check = lambda self, picture, beats: ("UNVERIFIED", True)
    return SPECS[spec_name]["profile"]


def build(project, spec_name, workers, swaps=None):
    """Refuses first, because a whole final is a long wait. Returns the record in the bundle."""
    project = Path(project).resolve()
    m, lock = built(project)
    approval_of(project, m["composition_rev"], lock["revision"])
    started = time.perf_counter()
    home = freeze(project)
    if SPECS[spec_name]["fps"] != lock["fps"] or (swaps or {}).get("swaps"):
        home = derive(home, spec_name, swaps)
    ed = editorial(home)
    prepared = round(time.perf_counter() - started, 1)
    name = renderer_for(spec_name, home)
    code = renderer.main(["draft", str(ed), "--profile", name, "--workers", str(workers)])
    root = store.root_of(ed)
    entry = store.latest(root, name) or {}
    if not entry or code not in (0, 3):
        raise Refused(f"the render stopped with exit {code}: see {root / 'changes'}")
    record = {"schema": 1, "spec": spec_name, "profile": name, "picture": entry["file"], "file_sha256": entry["file_sha256"], "composition_rev": entry["composition_rev"], "render_exit": code, "status": entry["status"],
              "prepare_s": prepared, "wall_s": round(time.perf_counter() - started, 1), "workers": workers}
    store.write_json(home / BUILD, record)
    print(f"built {spec_name}: {entry['file']}")
    return record


def probe(project, spec_name, workers, beats, swaps=None):
    """What a spec costs, from a short range. Its segments are published, so the whole render reuses them."""
    m, lock = built(project)
    home = freeze(project)
    if SPECS[spec_name]["fps"] != lock["fps"] or (swaps or {}).get("swaps"):
        home = derive(home, spec_name, swaps)
    name = renderer_for(spec_name, home)
    args = argparse.Namespace(project=str(editorial(home)), store=None, profile=name, workers=workers, force=False, inject_fault=None, inject_beats=None, inject_rounds=1)
    run = renderer.Run(args)
    store.lock(run.root)
    tmp = store.new_tmp(run.root)
    try:
        started = time.perf_counter()
        run.ensure_plan()
        run.prepare(tmp)
        log, left = run.render(tmp, beats)
        frames = sum(run.beats[b]["end_frame"] - run.beats[b]["start_frame"] for b in beats)
        wall = time.perf_counter() - started
        render_s = run.timings.get("render", 0) + run.timings.get("verify", 0) + run.timings.get("publish", 0)
        report = {"spec": spec_name, "beats": beats, "frames": frames, "workers": workers, "wall_s": round(wall, 1), "timings": run.timings, "seconds_per_frame": round(render_s / frames, 3), "whole_minutes": round(render_s / frames * run.lock["total_frames"] / 60, 1), "unresolved": left}
        print(json.dumps(report, indent=1))
        return report
    finally:
        store.clear_tmp(run.root)
        store.unlock(run.root)


# ---- accepting a stitched picture


def validate_stitched(picture):
    """The first half of deliver.py's gate: segment hashes, input keys and complete profile, all read again from the files. Returns what it read. Raises with every problem."""
    picture = Path(picture).resolve()
    folder, root = picture.parent, picture.parents[2]
    record, m, lock = (store.read_json(folder / n) for n in ("stitch.json", "ownership.json", "beats.lock.json"))
    if not (record and m and lock):
        raise Refused(f"no stitched record beside {picture}: only a validated stitch is accepted")
    problems = []
    if not picture.is_file() or sound_mix.file_hash(picture) != record["file_sha256"]:
        problems.append("this file is not the one stitch.json describes")
    if m.get("composition_rev") != record["composition_rev"] or sha({k: v for k, v in m.items() if k not in ("composition_rev", "authoring")}) != record["composition_rev"]:
        problems.append("ownership.json beside it is not of this composition")
    if lock.get("revision") != record["lock_revision"] or beat_lock.revision_of(lock) != record["lock_revision"]:
        problems.append("beats.lock.json beside it is not of this lock")
    if problems:
        raise Refused("; ".join(problems))
    keys = {b["beat_id"]: ownership.input_key(b, lock, m, record["profile_hash"], record["engine_hash"]) for b in lock["beats"]}
    if keys != {b["beat_id"]: b["key"] for b in record["beats"]}:
        problems.append("input keys differ from the keys of this composition and profile")
    records = {b["beat_id"]: store.find(root, record["profile_hash"], b["key"]) for b in record["beats"]}
    hashes = {b["beat_id"]: sound_mix.file_hash(store.segment_dir(root, record["profile_hash"], b["key"]) / records[b["beat_id"]]["file"]) for b in record["beats"] if records[b["beat_id"]]}
    problems += stitcher.check_segments(lock, keys, record["profile_hash"], records, hashes)
    for b in record["beats"]:
        r = records[b["beat_id"]]
        if r and (r["decoded"]["content_hash"] != b["content_hash"] or sha(r["profile_full"]) != record["profile_hash"]):
            problems.append(f"{b['beat_id']}: segment does not match the stitched record")
    if problems:
        raise Refused("; ".join(problems[:8]))
    return {"picture": picture, "root": root, "record": record, "map": m, "lock": lock, "profile": records[record["beats"][0]["beat_id"]]["profile_full"]}


def validate_decoded(seen):
    """Every decoded frame against the segments' rows, and the timestamps. Last, because at 4K this is minutes. Raises with every problem."""
    picture, root, record, lock = seen["picture"], seen["root"], seen["record"], seen["lock"]
    stream = stitcher.probe_video(picture)
    rows, _, _ = sentinel.scan(picture, stream["width"], stream["height"])
    expected = [row for b in record["beats"] for row in store.rows_of(root, record["profile_hash"], b["key"])]
    problems = []
    if rows != expected:
        at = next((i for i, (a, b) in enumerate(zip(rows, expected)) if a != b), min(len(rows), len(expected)))
        problems.append(f"decoded {len(rows)} rows, expected {len(expected)}, first difference at frame {at}")
    problems += stitcher.timestamp_problems(picture, lock["fps"], lock["total_frames"])
    if problems:
        raise Refused("; ".join(problems[:8]))
    return len(rows)


def accept(project, picture, reviewed_final=True, listed=()):
    """Everything that must hold before deliver.py binds this picture. For a reviewed final: a frozen bundle intact, its derivative record if it is one, the complete profile of its spec, and the approval record."""
    project = Path(project).resolve()
    seen = validate_stitched(picture)
    record = seen["record"]
    home = seen["root"].parent
    ed = editorial(home)
    swaps = []
    if reviewed_final:
        problems = bundle_problems(home)
        if problems:
            raise Refused("; ".join(problems[:6]))
        bundle = store.read_json(home / BUNDLE)
        if record["composition_rev"] != bundle["composition_rev"] or record["lock_revision"] != bundle["lock_revision"]:
            raise Refused("this picture is not of its bundle's composition")
        frozen_sound = bundle.get("sound_identity") or sound_identity(ed)
        if sound_identity(project) != frozen_sound:
            raise Refused("the project's sound sheet or cue bytes differ from this bundle, so this would deliver the old sound: run final.py build again")
        seen["source_sound_identity"] = frozen_sound
        if home_rows(home_of(project)) != bundle.get("home_files", {}):
            raise Refused("the project's waiver lists differ from this bundle: run final.py build again")
        if sha(complete_profile(record["profile"])) != record["profile_hash"]:
            raise Refused(f"profile {record['profile']} is not the complete publish profile")
        derivative = store.read_json(home / DERIVATIVE)
        base_rev, base_lock = bundle["approved_composition_rev"], bundle["lock_revision"]
        if derivative:
            if sha(derivative) != bundle.get("derivative") or derivative["composition_rev"] != record["composition_rev"]:
                raise Refused(f"{DERIVATIVE} is not the record this bundle was built with")
            if any(not str(row.get("authorized_by") or "").strip() for row in derivative["swaps"]):
                raise Refused("a swap in the derivative has no authorization")
            base_rev, base_lock = derivative["base_composition_rev"], derivative["base_lock_revision"]
            swaps = [row["path"] for row in derivative["swaps"]]
        elif bundle.get("derivative"):
            raise Refused(f"this bundle is a derivative and its {DERIVATIVE} is gone")
        if sorted(listed) != sorted(swaps):
            raise Refused(f"--source-swap lists {sorted(listed)}, this revision swapped {sorted(swaps)}. Listing a swap does not authorize it: a swap is a derivative revision")
        now = ownership.load(project)
        if now is None or now["composition_rev"] != base_rev:
            raise Refused(f"the project is not at the approved composition {base_rev[:16]}: go back to it or approve this one")
        seen["approval"] = approval_of(project, base_rev, base_lock)
    elif listed:
        raise Refused("listing a swap does not authorize it: a swap is a derivative revision of a reviewed final")
    return {**seen, "frames": validate_decoded(seen), "project": ed if reviewed_final else project, "home": home, "swaps": swaps, "derivative": store.read_json(home / DERIVATIVE) if reviewed_final else None}


# ---- the output check, on the delivered file


def proxy_of(video, out):
    """gates.py and flash_scan.py are qualified at 1080 wide. Every final frame is kept, so a one-frame flash is still one frame."""
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(video), "-vf", "scale=1080:1920:flags=area", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", "-c:a", "copy", str(out)], check=True)
    return out


def check_delivered(accepted, video):
    """Workstream C's output check on the delivered file. It has the stitched picture's frames with the mastered sound, so it gets a stitched record of its own, and O1 to O7 read it as they read any other.
    Above 1080 wide, O4's flash scan and O6's gates run on a 1080 wide copy of the same file."""
    video, root, record = Path(video).resolve(), accepted["root"], accepted["record"]
    digest = sound_mix.file_hash(video)
    folder = root / "stitched" / f"{record['profile']}-delivered-{digest[:16]}"
    folder.mkdir(exist_ok=True)
    target = folder / f"{record['profile']}.mp4"
    if not target.is_file():
        os.link(video, target)
    for name in ("ownership.json", "beats.lock.json"):
        shutil.copy(accepted["picture"].parent / name, folder / name)
    store.write_json(folder / "stitch.json", {**record, "file": target.name, "file_sha256": digest, "stitched_from": record["file_sha256"]})
    report = checks.check(target, accepted["project"], root)
    width = accepted["profile"]["width"]
    if width > max(checks.FLASH_WIDTHS) and "O4" in report["checks"]:
        small = accepted.get("proxy") or proxy_of(video, folder / "proxy-1080.mp4")
        o4, flash = report["checks"]["O4"], checks.flash(small, accepted["lock"], accepted["map"], 1080)
        o4.update(flash=flash, status=checks.worst([checks.FAIL if o4["problems"] else checks.PASS, flash["status"]]))
        report["checks"]["O6"] = checks.o6_gates(small, 1080, True)
        checks.apply_waivers(report, checks.waivers_of(accepted["project"], root), {**record, "file_sha256": digest})
        report["status"] = checks.worst(c["status"] for name, c in report["checks"].items() if name != "O7")
        report["proxy"] = str(small)
        checks.finish(report, root, digest, record)
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["build", "probe"])
    ap.add_argument("project")
    ap.add_argument("--spec", required=True, choices=list(SPECS))
    ap.add_argument("--workers", type=int, required=True)
    ap.add_argument("--swaps", help="JSON: {\"swaps\": [{path, file, source, why, authorized_by}]}")
    ap.add_argument("--beats", help="probe: comma-separated beats")
    a = ap.parse_args(argv)
    swaps = store.read_json(a.swaps) if a.swaps else None
    if a.swaps and swaps is None:
        print(f"REFUSED: cannot read {a.swaps}")
        return 2
    try:
        if a.command == "build":
            build(a.project, a.spec, a.workers, swaps)
        else:
            probe(a.project, a.spec, a.workers, a.beats.split(","), swaps)
    except (ValueError, OSError, subprocess.SubprocessError) as e:
        print("REFUSED:", e)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
