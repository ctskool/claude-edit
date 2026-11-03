"""Rounds, notes, waivers and approval state for the picture Chase reviews. PLAN-V2-BEAT-REVIEW.md Workstream D.

project is always a path to v2/editorial. Everything is about the review profile's newest stitched picture, failed or not: a picture that failed is still shown, and only cannot be approved
until each FAIL is fixed or waived. UNVERIFIED items are counted and shown and block nothing, because a review picture's best status is UNVERIFIED. A check that never ran is not an item: it blocks.

notes.jsonl, waivers.json and dropped_notes.json sit beside fixture.json, never in v2/editorial, where a new file stales the build. Rounds sit in the store: beat/rounds/NNNN.json, one snapshot each, with file bytes
in beat/rounds/blobs/<sha256>, so a round costs only what it changed. A round is what go_back restores: sources, plan, lock, ownership map, and which picture is the newest.
A note closes only when a round says it did it, and only while that round is on the head's line. What a round did not do stays open and holds approval until a later round does it or Chase drops it.
Importable, for server.py. Nothing here renders except native_beat and the check approve starts in its own process.
"""
import json, math, os, shutil, subprocess, sys, tempfile, threading, time, uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import project_root
ROOT = project_root()
sys.path[:0] = [str(HERE), str(ROOT / "tools" / "beat_check"), str(ROOT / "tools" / "beat_render"), str(ROOT / "tools")]
import output as checks
import ownership
import sound_mix
import store
from common import sha

PROFILE = "review"
RUN = ROOT / "tools" / "beat_render" / "run.py"
SKIP = (".hyperframes/", "renders/", "snaps", "verification/", "tools_local/_bak/", "tools_local/__pycache__/")  # what no picture reads
HOME = ("beats.json", "facts.json", "metadata.json", "words.json")  # the build and the copy check read these, two levels up
NATIVE_WORKERS = 1
NATIVE_SECONDS = 600
UNWAIVABLE = "this finding names no frames, so it can only be fixed"
NOT_SAID = "the round did not say what happened to this note"
NO_NOTES = {"done": set(), "held": {}, "undone": set(), "dropped": set()}
writing = threading.Lock()
words_cache = {}


def home_of(project):
    return Path(project).resolve().parents[1]


def root_of(project):
    return store.open_store(store.root_of(project))


def rounds_dir(root):
    path = Path(root) / "rounds"
    path.mkdir(exist_ok=True)
    return path


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


# ---- the picture


def picture(project):
    """The newest stitched picture, as the store names it. A copied store keeps old absolute paths in its entries, so the file comes from the folder name."""
    root = root_of(project)
    attempt = store.read_json(root / "last_attempt.json", {}).get(PROFILE)
    entry = attempt or store.read_json(root / "current.json", {}).get(PROFILE)
    if not entry:
        return None
    folder = root / "stitched" / entry["stitched"]
    return {"file": str(folder / f"{PROFILE}.mp4"), "file_sha256": entry["file_sha256"], "composition_rev": entry["composition_rev"], "lock_revision": entry["lock_revision"],
            "status": entry.get("status", "UNVERIFIED"), "source": "last_attempt" if attempt else "current", "stitched": entry["stitched"]}


def picture_named(root, picture_sha):
    """Any picture this store holds, by its file hash: what a note binds to. None if it never existed."""
    for folder in (Path(root) / "stitched").glob(f"{PROFILE}-{picture_sha[:16]}*"):
        record = store.read_json(folder / "stitch.json")
        if record and record["file_sha256"] == picture_sha:
            return {"file": str(folder / record["file"]), "file_sha256": picture_sha, "composition_rev": record["composition_rev"], "lock_revision": record["lock_revision"], "stitched": folder.name}
    return None


def stitched_beats(root, name):
    return store.read_json(Path(root) / "stitched" / name / "stitch.json", {}).get("beats", [])


# ---- findings


def source_reports(root, pic):
    """Every source report of this exact file, oldest first. Each covers its own beats, so the newest word on an event or a check stands."""
    folder = Path(root) / "checks" / pic["composition_rev"][:16]
    paths = sorted(folder.glob(f"source-*{pic['file_sha256'][:16]}.json"), key=lambda p: p.stat().st_mtime_ns)
    return [r for r in (store.read_json(p) for p in paths) if r]


def source_rows(reports):
    events, findings = {}, {}
    for report in reports:
        events.update({e["event_id"]: e for e in report.get("events", [])})
        findings.update({f["check"]: f for f in report.get("findings", [])})
    return events, findings


def finding(check, message, frames=()):
    frames = sorted(frames)
    tail = "-".join(map(str, frames)) if frames else sha(message)[:8]
    return {"id": f"{check}:{tail}", "check": check, "message": message[:400], "frames": frames}


def output_findings(report):
    """Every FAIL in an output report. Rows with frames can be waived. Damage to the file or its store cannot."""
    rows = []
    cs = report.get("checks", {})
    for name, c in cs.items():
        if c.get("status") == "FAIL" and name not in ("O4", "O5", "O6"):
            rows += [finding(name, str(p)) for p in c.get("problems", []) or [f"{name} failed"]]
    if "O4" in cs:
        rows += [finding("O4", str(p)) for p in cs["O4"].get("problems", [])]
        scan = cs["O4"].get("flash", {})
        rows += [finding("O4.flash", f"flash at frames {r.get('frames') or [r['frame']]}", r.get("frames") or [r["frame"]]) for r in scan.get("flashes", [])]
        rows += [finding("O4.double_cut", f"double cut at frames {r['frames']}, changes {r['diffs']}", r["frames"]) for r in scan.get("double_cuts", [])]
    if "O5" in cs:
        rows += [finding("O5.sample", f"frame {r['frame']} differs from its reference: {json.dumps({k: v for k, v in r.items() if k != 'frame'})}", [r["frame"]]) for r in cs["O5"].get("failed", [])]
        rows += [finding("O5.clip", f"frame {f} looks clipped and no reference clears it", [f]) for f in cs["O5"].get("clip_suspects_uncleared", [])]
    if cs.get("O6", {}).get("status") == "FAIL":
        rows += [finding(f"O6.{r.get('check')}", json.dumps(r, ensure_ascii=False)) for r in cs["O6"].get("blocking", [])]
    return rows


def findings_of(project, root, pic):
    """(findings, unverified counts) for a picture, read from its check reports. Waivers apply as they stand now, so a click takes effect without a new check."""
    keys = {b["beat_id"]: b["key"] for b in stitched_beats(root, pic["stitched"])}
    waivers = checks.waivers_of(project, root)
    output = store.read_json(Path(root) / "checks" / pic["composition_rev"][:16] / f"output-{pic['file_sha256'][:16]}.json")
    sources = source_reports(root, pic)
    events, source = source_rows(sources)
    rows, counts = [], {}
    if output is None:
        rows.append(finding("output", "the output check has not run on this picture"))
    else:
        rows += output_findings(output)
        rows += [{**finding(w["check"], f"waived: {w['why']}", w["frames"]), "already": True} for w in output.get("waived", [])]
        counts.update({name: 1 for name, c in output.get("checks", {}).items() if c["status"] == "UNVERIFIED"})
    if not sources:
        rows.append(finding("source", "the source check has not run on this picture"))
    for e in events.values():
        if e["status"] == "FAIL":
            rows.append(finding(f"source.{e['event_id']}", f"{e['event_id']}: {'; '.join(e.get('problems', []))}", [e["frame"]] if "frame" in e else []))
        elif e["status"] == "UNVERIFIED":
            counts[e["kind"]] = counts.get(e["kind"], 0) + 1
    for f in source.values():
        if f["status"] == "FAIL":
            rows.append(finding(f"source.{f['check']}", f["message"]))
        elif f["status"] == "UNVERIFIED":
            counts[f["check"]] = counts.get(f["check"], 0) + 1
    seen = {}
    for row in rows:
        already = row.pop("already", False)
        waived = already or seen.get(row["id"], {}).get("waived", False) or checks.waiver_for(row["check"], row["frames"], waivers, keys, {**pic, "profile": PROFILE}) is not None
        seen[row["id"]] = {**row, "waived": waived, "waivable": bool(row["frames"])}
    return list(seen.values()), counts


def blocking(project, root, pic):
    """What stops this picture being approved. A run can fail a picture on grounds no report holds, such as a touched beat invalidate missed, and that fails closed."""
    rows, _ = findings_of(project, root, pic)
    left = [f for f in rows if not f["waived"]]
    if pic.get("status") == "FAIL" and not rows:
        left.append(finding("run", "the run failed this picture and no check report says why: see beat/changes"))
    return left


# ---- notes


def notes_path(project):
    return home_of(project) / "notes.jsonl"


def read_notes(project):
    path = notes_path(project)
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf8").splitlines() if line.strip()]


def words_of(project):
    path = home_of(project) / "raw" / "cut_words.json"
    if path not in words_cache:
        words_cache[path] = store.read_json(path, [])
    return words_cache[path]


def nearest_word(words, t):
    """Rows are [text, start, end, id]. The word being said at t, or the nearest one."""
    if not words:
        return None
    return min(words, key=lambda w: 0 if w[1] <= t <= w[2] else min(abs(t - w[1]), abs(t - w[2])))


def still_of(root, picture_sha, frame):
    return Path(root) / "stills" / picture_sha[:16] / f"{frame}.jpg"


def start_still(video, frame, out):
    """Decodes this frame of the render by frame number, in its own process, so the note returns at once. A timestamp could land on a neighbour."""
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-map", "0:v:0", "-vf", f"select=eq(n\\,{frame})", "-fps_mode", "passthrough", "-frames:v", "1", "-q:v", "3", str(out)],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def add_note(project, note):
    """Binds a note to the picture it was made on and appends it. The still is made in the background. A note on an older picture is kept and flagged, and no round picks it up."""
    root = root_of(project)
    text, scope, frame, picture_sha = (note.get("text") or "").strip(), note.get("scope", "frame"), note.get("frame"), note.get("picture_sha")
    if not text:
        raise ValueError("a note needs text")
    if scope not in ("frame", "video", "sound"):
        raise ValueError(f"unknown scope {scope}")
    pic = picture_named(root, picture_sha or "")
    if pic is None:
        raise ValueError(f"no picture {str(picture_sha)[:16]} in this store")
    lock = store.read_json(root / "stitched" / pic["stitched"] / "beats.lock.json", {})
    row = {"id": uuid.uuid4().hex[:12], "text": text, "scope": scope, "frame": None, "time": None, "word_id": None, "word": None, "beat_id": None, "still": None,
           "picture_sha": picture_sha, "composition_rev": pic["composition_rev"], "lock_revision": pic["lock_revision"], "older_picture": picture(project)["file_sha256"] != picture_sha, "created": now()}
    if scope == "sound":
        sound = sound_view(project)
        index = note.get("cue_index")
        if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(sound["cues"]):
            raise ValueError("sound note needs a cue_index from this sheet")
        if not sound.get("identity") or note.get("sheet_identity") != sound["identity"]:
            raise ValueError("the sound sheet changed; reload it before leaving a note")
        cue = sound["cues"][index]
        row.update(cue_index=index, cue_time=cue["t"], cue_name=cue["name"], sheet_identity=sound["identity"])
    if scope in ("frame", "sound"):
        if not isinstance(frame, int) or isinstance(frame, bool) or not 0 <= frame < lock["total_frames"]:
            raise ValueError(f"frame {frame} is not in this picture")
        t = frame / lock["fps"]
        word = nearest_word(words_of(project), t)
        still = still_of(root, picture_sha, frame)
        row.update(frame=frame, time=round(t, 3), word_id=word[3] if word else None, word=word[0] if word else None, still=str(still.relative_to(root)),
                   beat_id=next(b["beat_id"] for b in lock["beats"] if b["start_frame"] <= frame < b["end_frame"]))
        if not still.is_file():
            start_still(pic["file"], frame, still)
    with writing, open(notes_path(project), "a", encoding="utf8", newline="\n") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    if scope != "sound" and store.read_json(approval.approvals(root) / "active.json", {}).get("file_sha256") == picture_sha:
        approval.clear(root)  # he is still changing it. The record stands, so approving again needs no second render
    return shown_note(root, row, NO_NOTES, None)


def dropped_path(project):
    return home_of(project) / "dropped_notes.json"


def note_ledger(project, root):
    """What the rounds on the head's line did to their notes. A round go_back left behind did nothing to this picture, so what it did reads as undone, and what it left undone says nothing."""
    rounds = {r["n"]: r for r in all_rounds(root)}
    n = store.read_json(rounds_dir(root) / "head.json", {}).get("n")
    line = []
    while n in rounds:
        line.append(n)
        n = rounds[n]["parent"]
    done, held = set(), {}
    for r in (rounds[i] for i in reversed(line)):
        done |= set(r.get("note_ids", []))
        held.update(r.get("not_done", {}))
    dropped = {row["id"] for row in store.read_json(dropped_path(project), [])}
    undone_at = {}
    for r in rounds.values():
        if r["n"] not in line:
            for i in r.get("note_ids", []):
                undone_at[i] = max(undone_at.get(i, -1), r["n"])
    # Explicit adoption after a go-back may carry a note as not_done. Earlier adoption must not undo a later go-back's flag.
    adopted = {i for n in line for i in rounds[n].get("adopted_note_ids", []) if n > undone_at.get(i, -1)}
    frozen = set(store.read_json(rounds_dir(root) / "frozen.json", {}).get("note_ids", []))
    # Sound outcomes are independent of the picture head and never take a snapshot.
    for outcome in store.read_json(home_of(project) / "sound_rounds.json", []):
        done.update(outcome["done"])
        held.update(outcome["not_done"])
    return {"done": done - dropped, "held": {i: why for i, why in held.items() if i not in done | dropped}, "undone": set(undone_at) - done - dropped - adopted, "dropped": dropped, "frozen": frozen - done - dropped}


def shown_note(root, row, ledger, newest):
    """A stored row plus what is true of it now. older_picture means no round picks it up without asking him: left on an older picture, or undone by going back. A note left undone is carried, whatever picture it was left on."""
    still = Path(root) / row["still"] if row.get("still") else None
    i = row["id"]
    closed = i in ledger["done"] or i in ledger["dropped"]
    held = ledger["held"].get(i)
    undone = i in ledger["undone"]
    return {**row, "still": str(still) if still else None, "still_ready": bool(still and still.is_file()), "closed": closed, "dropped": i in ledger["dropped"], "not_done": held, "undone": undone,
            "older_picture": row["older_picture"] if newest is None else (not closed and i not in ledger.get("frozen", set()) and (undone or (row["picture_sha"] != newest and held is None)))}


def open_notes(project, root, pic):
    """Notes a round still owes on this picture, which hold approval. One on an older picture is flagged and no round picks it up, so it cannot hold approval forever."""
    ledger = note_ledger(project, root)
    rows = [shown_note(root, n, ledger, pic["file_sha256"]) for n in read_notes(project)]
    return [n for n in rows if n.get("scope") != "sound" and not n["closed"] and not n["older_picture"]]


def sound_notes(project):
    """Open sound notes, including ones left on an older picture or sheet."""
    return [n for n in state(project)["notes"] if n.get("scope") == "sound" and not n["closed"]]


def close_sound(project, done=(), not_done=None):
    """Record only the listed sound outcomes. No picture round, freeze or snapshot."""
    done, not_done = list(done), dict(not_done or {})
    with writing:
        ids = {n["id"] for n in sound_notes(project)}
        if set(done) & set(not_done):
            raise ValueError("a note cannot be both done and not done")
        if (set(done) | set(not_done)) - ids:
            raise ValueError("only open sound notes can close in a sound round")
        if any(not str(why).strip() for why in not_done.values()):
            raise ValueError("a note left undone needs a reason")
        record = {"done": done, "not_done": not_done, "created": now()}
        path = home_of(project) / "sound_rounds.json"
        store.write_json(path, store.read_json(path, []) + [record])
    return record


def drop_note(project, note_id):
    """Chase takes a note back. By his click only. It stays in notes.jsonl as evidence, and no round owes it any more."""
    if not any(n["id"] == note_id for n in read_notes(project)):
        raise ValueError(f"no note {note_id}")
    path = dropped_path(project)
    with writing:
        store.write_json(path, store.read_json(path, []) + [{"id": note_id, "by": "chase", "created": now()}])
    return {"id": note_id, "dropped": True}


def freeze(project, adopt=()):
    """The one acknowledged set for a round: every open note on the newest picture, plus any an earlier round left undone. A note added after this waits for the next round, and by then it is on an older picture, so it is flagged.
    adopt includes flagged ids only after Chase asks for them. A resumed freeze after rendering keeps the existing set. Takes the first round's snapshot if there is none, because this is the last moment the sources are still that picture."""
    root = root_of(project)
    pic = picture(project)
    if pic is None:
        raise ValueError("no picture yet")
    if not all_rounds(root):
        close_round(project)
    frozen = store.read_json(rounds_dir(root) / "frozen.json")
    ledger = note_ledger(project, root)
    rows = [n for n in (shown_note(root, n, ledger, pic["file_sha256"]) for n in read_notes(project)) if n.get("scope") != "sound" and not n["closed"]]
    adopt = set(adopt)
    unknown = adopt - {n["id"] for n in rows}
    if unknown:
        raise ValueError(f"cannot adopt unknown or closed notes: {sorted(unknown)[:4]}")
    if frozen and frozen["picture_sha"] != pic["file_sha256"]:
        if adopt - set(frozen["note_ids"]):
            raise ValueError("this round already rendered: close it before adopting more notes")
        ids = set(frozen["note_ids"])
        return {"notes_rev": frozen["notes_rev"], "notes": [n for n in rows if n["id"] in ids], "flagged": [n for n in rows if n["id"] not in ids]}
    notes = [n for n in rows if not n["older_picture"] or n["id"] in adopt]
    flagged = [n for n in rows if n["older_picture"] and n["id"] not in adopt]
    rev = sha({"picture": pic["file_sha256"], "notes": [n["id"] for n in notes]})[:16]
    adopted = sorted(adopt | set((frozen or {}).get("adopted_note_ids", [])))
    store.write_json(rounds_dir(root) / "frozen.json", {"notes_rev": rev, "note_ids": [n["id"] for n in notes], "adopted_note_ids": adopted, "picture_sha": pic["file_sha256"], "created": now()})
    if notes:
        approval.clear(root)
    return {"notes_rev": rev, "notes": notes, "flagged": flagged}


# ---- rounds


def files_of(project):
    """Everything a build or a picture reads: name in a round to file. Files two levels up go under home/."""
    project = Path(project).resolve()
    rows = {rel: project / rel for rel in ownership.project_files(project) if not rel.startswith(SKIP)}
    rows.update({f"home/{name}": home_of(project) / name for name in HOME if (home_of(project) / name).is_file()})
    return rows


def snapshot(project, root):
    """Hashes every file and keeps the bytes of any not held yet. Real copies, so a later write to the project cannot reach a round."""
    blobs = rounds_dir(root) / "blobs"
    blobs.mkdir(exist_ok=True)
    manifest = {}
    for rel, path in files_of(project).items():
        h = manifest[rel] = sound_mix.file_hash(path)
        if not (blobs / h).is_file():
            tmp = blobs / f"{h}.{uuid.uuid4().hex}"
            shutil.copyfile(path, tmp)
            if sound_mix.file_hash(tmp) != h:
                tmp.unlink()
                raise ValueError(f"{rel} moved while it was being kept")
            os.replace(tmp, blobs / h)
    return manifest


def restore(project, root, manifest):
    """Makes the project these exact files. Returns what it wrote and what it removed. Refuses before touching anything if a byte is missing."""
    blobs = rounds_dir(root) / "blobs"
    missing = [rel for rel, h in manifest.items() if not (blobs / h).is_file()]
    if missing:
        raise ValueError(f"this round has lost {missing[:4]}")
    project = Path(project).resolve()
    held = files_of(project)
    wrote, removed = [], []
    for rel, h in manifest.items():
        path = held.get(rel) or (home_of(project) / rel[5:] if rel.startswith("home/") else project / rel)
        if rel in held and sound_mix.file_hash(path) == h:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}")
        shutil.copyfile(blobs / h, tmp)
        os.replace(tmp, path)
        wrote.append(rel)
    for rel, path in held.items():
        if rel not in manifest:
            path.unlink()
            removed.append(rel)
    return wrote, removed


def all_rounds(root):
    return [r for r in (store.read_json(p) for p in sorted(rounds_dir(root).glob("[0-9][0-9][0-9][0-9].json"))) if r]


def head_of(root):
    n = store.read_json(rounds_dir(root) / "head.json", {}).get("n")
    return store.read_json(rounds_dir(root) / f"{n:04d}.json") if n is not None else None


def set_head(root, n):
    store.write_json(rounds_dir(root) / "head.json", {"n": n})


def changed_since(root, stitched, base):
    """Beats whose segment differs from the base picture's, in beat order. No base means nothing to compare."""
    if not base:
        return []
    old = {b["beat_id"]: b["key"] for b in stitched_beats(root, base)}
    return [b["beat_id"] for b in stitched_beats(root, stitched) if old.get(b["beat_id"]) != b["key"]]


def public_round(r):
    return {k: r.get(k) for k in ("n", "parent", "picture_sha", "changed_beats", "notes_rev", "composition_rev", "lock_revision", "status", "created")}


def close_round(project, done=(), not_done=None):
    """Snapshots this round after a change. Refuses unless the project is the newest picture, because a round that does not rebuild its picture is no restore point.
    done is the frozen note ids this round did, and not_done maps the ones it did not to why. A frozen note it names in neither stays open too: only a round's word closes a note.
    Returns the round. Closing again with nothing new returns the same one."""
    project = Path(project).resolve()
    root = root_of(project)
    pic = picture(project)
    if pic is None:
        raise ValueError("no picture yet")
    m = ownership.load(project)
    if m is None or m["composition_rev"] != pic["composition_rev"]:
        raise ValueError("the project is not the newest picture: run run.py change first")
    head = head_of(root)
    frozen = store.read_json(rounds_dir(root) / "frozen.json")
    done, not_done, ids = list(done), dict(not_done or {}), frozen["note_ids"] if frozen else []
    strays = [i for i in [*done, *not_done] if i not in ids]
    if strays:
        raise ValueError(f"not in this round's frozen notes: {strays[:4]}")
    if head and head["picture_sha"] == pic["file_sha256"] and head["composition_rev"] == pic["composition_rev"] and not frozen:
        return public_round(head)
    if set(done) & set(not_done):
        raise ValueError(f"a note cannot be both done and not done: {sorted(set(done) & set(not_done))[:4]}")
    if any(not str(why).strip() for why in not_done.values()):
        raise ValueError("a note left undone needs a reason")
    not_done = {**{i: NOT_SAID for i in ids if i not in done}, **not_done}
    entry = store.read_json(root / ("last_attempt.json" if pic["source"] == "last_attempt" else "current.json"))[PROFILE]
    n = max((r["n"] for r in all_rounds(root)), default=-1) + 1
    record = {"n": n, "parent": head["n"] if head else None, "picture_sha": pic["file_sha256"], "composition_rev": pic["composition_rev"], "lock_revision": pic["lock_revision"],
              "stitched": pic["stitched"], "source": pic["source"], "entry": {**entry, "file": pic["file"]}, "status": pic["status"],
              "changed_beats": changed_since(root, pic["stitched"], head["stitched"] if head else None),
              "notes_rev": frozen["notes_rev"] if frozen else None, "note_ids": done, "not_done": not_done, "adopted_note_ids": (frozen or {}).get("adopted_note_ids", []), "manifest": snapshot(project, root), "created": now()}
    store.write_json(rounds_dir(root) / f"{n:04d}.json", record)
    set_head(root, n)
    (rounds_dir(root) / "frozen.json").unlink(missing_ok=True)
    if open_notes(project, root, pic):
        approval.clear(root)
    else:
        approval.clear_unless(root, pic["file_sha256"])
    return public_round(record)


def go_back(project, n):
    """A real restore: sources, plan, beat map, ownership map and the picture, so the next change builds from that round. Rounds after it stay, and what was here is kept in rounds/left-*.json.
    Takes the store's run lock, so it cannot land under a render. After it, run.py change renders 0 and stitches the same file. Clears approval."""
    project = Path(project).resolve()
    root = root_of(project)
    round_ = store.read_json(rounds_dir(root) / f"{n:04d}.json")
    if round_ is None:
        raise ValueError(f"no round {n}")
    video = root / "stitched" / round_["stitched"] / f"{PROFILE}.mp4"
    if not video.is_file() or sound_mix.file_hash(video) != round_["picture_sha"]:
        raise ValueError(f"round {n}'s picture is gone or changed: {video}")
    store.lock(root)
    try:
        store.write_json(rounds_dir(root) / f"left-{uuid.uuid4().hex[:12]}.json", {"created": now(), "head": (head_of(root) or {}).get("n"), "manifest": snapshot(project, root)})
        wrote, removed = restore(project, root, round_["manifest"])
        attempts = store.read_json(root / "last_attempt.json", {})
        attempts.pop(PROFILE, None)
        entry = {**round_["entry"], "file": str(video)}
        if round_["source"] == "last_attempt":
            attempts[PROFILE] = entry
        else:
            store.write_json(root / "current.json", {**store.read_json(root / "current.json", {}), PROFILE: entry})
        store.write_json(root / "last_attempt.json", attempts)
        set_head(root, n)
        (rounds_dir(root) / "frozen.json").unlink(missing_ok=True)
        approval.clear(root)
    finally:
        store.unlock(root)
    return {"n": n, "picture_sha": round_["picture_sha"], "composition_rev": round_["composition_rev"], "wrote": wrote, "removed": removed}


# ---- waivers


def waive(project, finding_id, why):
    """Writes one waiver. By Chase's click only: nothing else may call this. The waiver names the segments its frames sit in, so an edit to those beats brings the finding back.
    It names its composition and profile too: O4 may hold for a final of this composition, whose keys differ by profile. An O5.sample waiver names only this rendered file. tools/beat_check/output.py waiver_for."""
    root = root_of(project)
    pic = picture(project)
    if pic is None:
        raise ValueError("no picture yet")
    if not (why or "").strip():
        raise ValueError("a waiver needs a reason")
    row = next((f for f in findings_of(project, root, pic)[0] if f["id"] == finding_id), None)
    if row is None:
        raise ValueError(f"no finding {finding_id} on this picture")
    if not row["frames"]:
        raise ValueError(UNWAIVABLE)
    if row["waived"]:
        raise ValueError(f"{finding_id} is already waived")
    beats = stitched_beats(root, pic["stitched"])
    keys = {b["beat_id"]: b["key"] for b in beats if any(b["start_frame"] <= f < b["end_frame"] for f in row["frames"])}
    waiver = {"check": row["check"], "frames": row["frames"], "why": why.strip(), "by": "chase", "picture_sha": pic["file_sha256"], "composition_rev": pic["composition_rev"], "profile": PROFILE, "keys": keys, "created": now()}
    path = home_of(project) / "waivers.json"
    with writing:
        store.write_json(path, store.read_json(path, []) + [waiver])
    return waiver


# ---- state


def sound_view(project):
    """Sheet cues at t (not the attack offset at), with stale's revision/event rules."""
    if not (Path(project) / "sound.json").is_file():
        return {"present": False, "identity": None, "cues": []}
    try:
        sheet = sound_mix.sheet_of(project)
        identity, error = None, None
        try:
            identity = sha(sound_mix.sound_identity(project))
        except (ValueError, KeyError, TypeError, OSError) as e:
            error = str(e)  # keep the cues visible even when one of their files is missing
        changed = sheet.get("picture_rev") != sound_mix.picture_rev(project)
        events = sound_mix.events_of(sound_mix.plan_of(project))
        cues = []
        for i, cue in enumerate(sheet["cues"]):
            eid = cue.get("event_id", "missing")
            unconfirmed = events.get(eid) is None
            moved = not unconfirmed and abs(float(events[eid]) - cue["t"]) > .001
            gain = float(cue["gain"])
            cues.append({**cue, "index": i, "name": Path(cue["file"]).stem,
                         "gain_db": round(20 * math.log10(gain), 1) if gain > 0 else None,
                         "stale": changed or moved or unconfirmed})
        result = {"present": True, "identity": identity, "cues": cues, "stale": changed}
        if error:
            result["error"] = error
        return result
    except (ValueError, KeyError, TypeError, OSError) as e:
        return {"present": True, "identity": None, "cues": [], "error": str(e)}


def sound_preview(project, picture_sha, sheet_identity):
    """Listening derivative only. Stream copy picture; never publish to any picture store entry."""
    project = Path(project).resolve()
    pic = picture(project)
    def unchanged():
        return (pic and pic["file_sha256"] == picture_sha
                and sound_mix.file_hash(pic["file"]) == picture_sha
                and sha(sound_mix.sound_identity(project)) == sheet_identity)
    if not unchanged():
        raise ValueError("picture or sound sheet changed; request a new listening preview")
    folder = root_of(project) / "sound-preview"
    folder.mkdir(exist_ok=True)
    target = folder / f"{picture_sha[:16]}-{sheet_identity[:16]}.mp4"
    if target.is_file():
        return str(target)
    with tempfile.TemporaryDirectory(dir=folder) as tmp:
        audio, movie = Path(tmp) / "mix.wav", Path(tmp) / "preview.mp4"
        sound_mix.mix(str(project), str(audio))
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pic["file"], "-i", str(audio),
                            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(movie)],
                           capture_output=True, text=True, timeout=180)
        if r.returncode:
            raise ValueError(f"listening preview failed: {r.stderr[-800:]}")
        if not unchanged():
            raise ValueError("picture or sound sheet changed during the preview build; try again")
        os.replace(movie, target)
    return str(target)


def state(project):
    """Everything the player shows. Reads only."""
    project = Path(project).resolve()
    root = root_of(project)
    pic = picture(project)
    head = head_of(root)
    rounds = all_rounds(root)
    lock = store.read_json(root / "stitched" / pic["stitched"] / "beats.lock.json", {}) if pic else store.read_json(project / "beats.lock.json", {})
    if pic:
        rows, unverified = findings_of(project, root, pic)
        base = head["stitched"] if head and head["picture_sha"] != pic["file_sha256"] else next((r["stitched"] for r in rounds if head and r["n"] == head["parent"]), None)
        changed = set(changed_since(root, pic["stitched"], base))
    else:
        rows, unverified, changed = [], {}, set()
    say = {b["id"]: b for b in store.read_json(project / "plan.json", {}).get("beats", [])}
    fps = lock.get("fps")
    beats = [{"id": b["beat_id"], "start_frame": b["start_frame"], "end_frame": b["end_frame"], "start": round(b["start_frame"] / fps, 3), "end": round(b["end_frame"] / fps, 3),
              "script": say.get(b["beat_id"], {}).get("say", ""), "layout": b["layout"], "changed": b["beat_id"] in changed} for b in lock.get("beats", [])]
    ledger = note_ledger(project, root)
    sound = sound_view(project)
    notes = [shown_note(root, n, ledger, pic["file_sha256"] if pic else None) for n in read_notes(project)]
    for note in notes:
        if note.get("scope") == "sound":
            note.update(older_picture=bool(pic and note["picture_sha"] != pic["file_sha256"]),
                        older_sheet=note.get("sheet_identity") != sound.get("identity"))
    return {"picture": {k: pic[k] for k in ("file", "file_sha256", "composition_rev", "lock_revision", "status", "source")} if pic else None,
            "approvable": bool(pic) and not blocking(project, root, pic), "findings": rows, "unverified": unverified, "fps": fps, "frames": lock.get("total_frames"), "beats": beats,
            "rounds": [public_round(r) for r in rounds], "head": head["n"] if head else None,
            "notes": notes, "sound": sound, "approval": approval.status(project)}


# ---- approval


def approve(project, picture_sha):
    """Starts the approval check in its own process and returns its state. Refuses a picture that is not the newest, that does not match the project, or that has a FAIL not fixed or waived."""
    return approval.start(project, picture_sha)


def approval_status(project):
    return approval.status(project)


def reconcile(project, picture_sha, why):
    """Chase's call on differing regions the method could not call. By his click only. Added to the agreed list, because the record's RECONCILED result needs a way to be written."""
    return approval.reconcile(project, picture_sha, why)


# ---- one beat at native size


def native_beat(project, beat_id):
    """That beat at native size, with no sound. Renders in its own store, work/<id>/beat-native, at the final profile, so the review picture and its store are never read or written.
    Waits for the render, and asking again for the same composition returns the same file at once. One run per store, so server.py should call this off its request thread and one beat at a time."""
    project = Path(project).resolve()
    native = home_of(project) / "beat-native"
    m = ownership.load(project)
    held = store.read_json(native / "held.json", {})
    known = held.get(f"{m['composition_rev'] if m else None}:{beat_id}")
    if known and Path(known).is_file():
        return known
    command = [sys.executable, str(RUN), "draft", str(project), "--profile", "final", "--workers", str(NATIVE_WORKERS), "--store", str(native), "--only", beat_id]
    r = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf8", errors="replace", timeout=NATIVE_SECONDS)
    if r.returncode not in (0, 3):
        raise ValueError(f"the native render of {beat_id} exited {r.returncode}: {r.stdout[-400:]}")
    done = store.read_json(sorted((native / "changes").glob("*.json"))[-1])
    if m:
        store.write_json(native / "held.json", {**held, f"{m['composition_rev']}:{beat_id}": done["segments"][beat_id]})
    return done["segments"][beat_id]


import approval  # needs what is above: approval.py imports this module for its findings
