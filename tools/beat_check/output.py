"""Output check: runs on decoded frames of the actual file. CONTRACT.md section 7.

  python tools/beat_check/output.py <stitched.mp4> [--project <project>] [--store <root>]

Writes beat/checks/<rev16>/output-<file_sha16>.json, bound to the file's sha256. Exit 0 PASS, 1 FAIL, 3 UNVERIFIED, 4 there was nothing to check.
It reads stitch.json and never source.json, because a pass on the source says nothing about these pixels. Frames pair by decoded frame number, never by timestamp.
O5 compares samples, and every frame is screened for the fault's one signature. Nothing here clears every frame, and each report says how many were not compared.
A waiver names a check, its exact frames and why. A waived finding no longer fails its check, and is listed under "waived" in every report. They come from an append-only waivers.json beside
the project's notes.jsonl, never inside v2/editorial, where any new file stales the build, and from the "waivers" rows of a fixture's fixture.json that name frames.
"""
import argparse, json, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import project_root
ROOT = project_root()
sys.path[:0] = [str(HERE), str(ROOT / "tools" / "beat_render"), str(ROOT / "tools")]
import events as contract
import sentinel
import sound_mix
import stitch as stitcher
import store
from common import frame_of, sha

GATES = ROOT / "tools" / "gates.py"
FLASH = ROOT / "tools" / "flash_scan.py"
PASS, FAIL, UNVERIFIED = "PASS", "FAIL", "UNVERIFIED"
CODES = {PASS: 0, FAIL: 1, UNVERIFIED: 3}
NOT_CHECKED = 4  # no file or no stitch.json, so nothing below ran. run.py must not read that as a check that looked
SUSPECTS_KEPT = 64  # decoded suspects held for comparison. One past this is a FAIL all the same
FLASH_WIDTHS = (540, 1080)  # flash_scan.py is trusted at a width only once it has gone red on a planted flash there (HOUSE.md). tools/tests/test_beat_check.py plants one at 540
LISTED = 12  # rows kept in a report for each kind of problem


def worst(statuses):
    statuses = list(statuses)
    return FAIL if FAIL in statuses else UNVERIFIED if UNVERIFIED in statuses or not statuses else PASS


def result(status, **fields):
    return {"status": status, **fields}


def o1_frames(rows, total, stream, want):
    problems = []
    if len(rows) != total:
        problems.append(f"decoded {len(rows)} frames, expected {total}")
    if stream["packets"] != total:
        problems.append(f"{stream['packets']} packets, expected {total}")
    differs = {k: (stream[k], want[k]) for k in stitcher.STREAM_KEYS if k != "time_base" and want and stream[k] != want[k]}
    if differs:
        problems.append(f"stream differs from its segments: {differs}")
    return result(FAIL if problems else PASS, decoded=len(rows), expected=total, problems=problems)


def o2_content(root, record, rows):
    """Each decoded row equals its segment's row at its global frame. A segment whose bytes moved since it was published is a FAIL even if this file still looks right."""
    problems, missing = [], []
    segments = {}
    ph = record["profile_hash"]
    for beat in record["beats"]:
        id_, key = beat["beat_id"], beat["key"]
        seg = store.find(root, ph, key)
        if seg is None:
            missing.append(id_)
            continue
        folder = store.segment_dir(root, ph, key)
        if sound_mix.file_hash(folder / seg["file"]) != seg["file_sha256"]:
            problems.append(f"{id_}: segment file changed since it was published")
        seg_rows = store.rows_of(root, ph, key)
        segments[id_] = seg_rows
        if sha("\n".join(seg_rows)) != beat["content_hash"] or seg["decoded"]["content_hash"] != beat["content_hash"]:
            problems.append(f"{id_}: segment rows do not hash to the stitched record")
        a, b = beat["start_frame"], beat["end_frame"]
        got = rows[a:b]
        if got != seg_rows:
            at = next((a + i for i, (x, y) in enumerate(zip(got, seg_rows)) if x != y), a + min(len(got), len(seg_rows)))
            problems.append(f"{id_}: frame {at} differs from its segment")
    status = FAIL if problems else UNVERIFIED if missing else PASS
    return result(status, frames_matched=len(rows) if status == PASS else None, problems=problems[:LISTED], problem_count=len(problems), segments_missing=missing), segments


def o3_timestamps(path, fps, total):
    problems = stitcher.timestamp_problems(path, fps, total)
    return result(FAIL if problems else PASS, problems=problems)


def expected_cuts(lock, m):
    """Every planned switch and card swap, as frame times, so a planned cut never reads as a flash."""
    fps = lock["fps"]
    frames = {b["start_frame"] for a, b in zip(lock["beats"], lock["beats"][1:]) if a["layout"] != b["layout"]}
    frames |= {frame_of(t, fps) for _, a, b in m["shared"]["timing"]["windows"] for t in (a, b)}
    return sorted(frames)


def flash(path, lock, m, width):
    if width not in FLASH_WIDTHS:
        return result(UNVERIFIED, why=f"flash_scan.py has not gone red on a planted flash at {width} wide")
    fps = lock["fps"]
    times = ",".join(f"{f / fps:.4f}" for f in expected_cuts(lock, m))
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "flash.json"
        r = subprocess.run([sys.executable, str(FLASH), str(path), "--expect-times", times, "--json", str(out)], capture_output=True, text=True, encoding="utf8", errors="replace")
        if r.returncode not in (0, 1) or not out.is_file():
            return result(UNVERIFIED, why=f"flash_scan.py exited {r.returncode}: {r.stderr[-300:]}")
        report = json.loads(out.read_text(encoding="utf8"))
    return result(FAIL if report["verdict"] == "FAIL" else PASS, flashes=report["flashes"], double_cuts=report["double_cuts"], unexpected_cuts=len(report["unexpected"]), expected=len(times.split(",")))


def o4_joins(record, rows, segments, path, lock, m, width):
    bad = []
    joins = 0
    beats = record["beats"]
    for left, right in zip(beats, beats[1:]):
        joins += 1
        at = right["start_frame"]
        a, b = segments.get(left["beat_id"]), segments.get(right["beat_id"])
        if a is None or b is None or len(rows) <= at:
            bad.append(f"{left['beat_id']}|{right['beat_id']}: no rows to compare")
        elif rows[at - 1] != a[-1] or rows[at] != b[0]:
            bad.append(f"{left['beat_id']}|{right['beat_id']}: frame {at - 1} or {at} differs from its segment")
    scan = flash(path, lock, m, width)
    return result(worst([FAIL if bad else PASS, scan["status"]]), joins=joins, problems=bad[:LISTED], flash=scan)


def o5_samples(root, record, lock, picked, suspects, width, height, events):
    """Samples against references, on the stitched file, plus every frame that looks clipped. A suspect no reference clears is a FAIL."""
    ph = record["profile_hash"]
    keys = {b["beat_id"]: b["key"] for b in record["beats"]}
    region_top = height // 2
    failed, unverified, whole, region, blocks, compared = [], [], [], [], [], 0
    uncleared, failed_beats = [], []
    for beat in lock["beats"]:
        a, b = beat["start_frame"], beat["end_frame"]
        inside = [s for s in suspects if a <= s < b]
        frames = sorted(set(sentinel.samples(beat, events)) | {s for s in inside if s in picked})
        frames = [f for f in frames if f in picked]
        stills = sentinel.load_stills(store.refs_dir(root, ph, keys[beat["beat_id"]]), frames, width, height)
        seen = sentinel.compare(picked, stills, frames, width, height, region_top)
        compared += len(frames) - len(seen["unverified"])
        failed += seen["failed"]
        unverified += seen["unverified"]
        whole += [seen["min_psnr"]] if seen["min_psnr"] is not None else []
        region += [seen["min_psnr_region"]] if seen["min_psnr_region"] is not None else []
        blocks += [seen["max_block"]] if seen["max_block"] is not None else []
        bad = {row["frame"] for row in seen["failed"]}
        missed = [s for s in inside if s in bad or s in seen["unverified"] or s not in picked]
        uncleared += missed
        failed_beats += [beat["beat_id"]] if bad or missed else []
    switches = [y["start_frame"] for x, y in zip(lock["beats"], lock["beats"][1:]) if x["layout"] != y["layout"]]
    status = FAIL if failed or uncleared else UNVERIFIED if unverified or not compared else PASS
    return result(status, frames_compared=compared, frames_no_reference=len(unverified), no_reference=unverified[:LISTED], failed=failed[:LISTED], failed_count=len(failed), failed_beats=failed_beats,
                  clip_suspects=len(suspects), clip_suspects_uncleared=uncleared, layout_switches=len(switches),
                  min_psnr=min(whole) if whole else None, min_psnr_region=min(region) if region else None, psnr_min=sentinel.PSNR_MIN,
                  max_block=max(blocks) if blocks else None, block_max=sentinel.BLOCK_MAX)


def o6_gates(path, width, is_final):
    band = "0,0,1080,900" if is_final else "0,0,540,450"
    counted = ("black", "audio", "loudness", "true-peak") if is_final else ("black", "audio")
    skipped = () if is_final else ("frozen-band", "hold", "freeze", "layout-run")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "gates.json"
        command = [sys.executable, str(GATES), str(path), "--band", band, "--json", str(out)] + (["--pack", "editorial"] if is_final else [])
        r = subprocess.run(command, capture_output=True, text=True, encoding="utf8", errors="replace")
        if r.returncode not in (0, 1, 2) or not out.is_file():
            return result(UNVERIFIED, why=f"gates.py exited {r.returncode}: {r.stderr[-300:]}")
        report = json.loads(out.read_text(encoding="utf8"))
    blocking = [f for f in report["findings"] if f["check"] in counted]
    warnings = [f for f in report["findings"] if f["check"] not in counted and f["check"] not in skipped and f["check"] not in ("loudness", "true-peak")]
    return result(FAIL if blocking else PASS, blocking=blocking, warnings=warnings, counted=list(counted), skipped=list(skipped), band=band,
                  loudness=report.get("loudness"), black=report.get("black"), audio=report.get("audio"))


def waivers_of(project, root):
    home = (Path(project).resolve() if project else Path(root).resolve().parent / "v2" / "editorial").parents[1]
    fixture = store.read_json(home / "fixture.json", {}).get("waivers", [])  # its rows with no frames are conform.py's
    return [{**w, "source": name} for name, rows in (("waivers.json", store.read_json(home / "waivers.json", [])), ("fixture.json", fixture)) for w in rows if w.get("frames")]


def waiver_for(check, frames, waivers, keys, record=None):
    """The waiver of exactly this finding, or None. One that names segments holds only while those beats are those segments, so an edit there brings the finding back.
    A key is bound to its profile, so a final of the same composition can never match one from review. There the waiver's own composition stands in for its keys, and any edit is a new composition.
    Frames must still match exactly, so a 60 fps derivative, a new composition and frame grid, needs its own."""
    def holds(w):
        if check == "O5.sample":
            if not w.get("picture_sha") or not record or w["picture_sha"] != record.get("file_sha256"):
                return False
        if all(keys.get(b) == k for b, k in w.get("keys", {}).items()):
            return True
        return check.startswith("O4.") and bool(record) and w.get("composition_rev") == record.get("composition_rev") and "profile" in w and w["profile"] != record.get("profile")
    return next((w for w in waivers if w["check"] == check and sorted(w["frames"]) == sorted(frames) and holds(w)), None)


def apply_waivers(report, waivers, record):
    """Takes waived rows out of what fails O4 and O5, and lists each under report["waived"]. Runs after the checks, so a finding is found every time and only then excused."""
    keys = {b["beat_id"]: b["key"] for b in record["beats"]}
    waived = []

    def keep(rows, check, frames_of):
        left = []
        for row in rows:
            w = waiver_for(check, frames_of(row), waivers, keys, record)
            if w:
                waived.append({"check": check, "frames": frames_of(row), "why": w["why"], "from": w["source"]})
            else:
                left.append(row)
        return left

    o4, o5 = report["checks"]["O4"], report["checks"]["O5"]
    scan = o4["flash"]
    if scan["status"] == FAIL:
        scan["flashes"] = keep(scan["flashes"], "O4.flash", lambda r: r.get("frames") or [r["frame"]])
        scan["double_cuts"] = keep(scan["double_cuts"], "O4.double_cut", lambda r: r["frames"])
        if waived and not scan["flashes"] and not scan["double_cuts"]:
            scan["status"] = PASS
    o4["status"] = worst([FAIL if o4["problems"] else PASS, scan["status"]])
    before = len(o5["failed"])
    o5["failed"] = keep(o5["failed"], "O5.sample", lambda r: [r["frame"]])
    o5["failed_count"] -= before - len(o5["failed"])
    o5["clip_suspects_uncleared"] = keep(o5["clip_suspects_uncleared"], "O5.clip", lambda f: [f])
    if o5["status"] == FAIL and not o5["failed_count"] and not o5["clip_suspects_uncleared"]:
        o5["status"] = UNVERIFIED if o5["frames_no_reference"] or not o5["frames_compared"] else PASS
    report["waived"] = waived


def o7_coverage(total, samples):
    compared = samples.get("frames_compared", 0)
    return {"status": "REPORT", "frames": total, "frames_compared": compared, "frames_not_compared": total - compared,
            "note": "Sampling cannot clear every frame. Every frame was decoded, matched to its segment and screened for the clip signature. Only the compared frames were checked against a reference."}


def project_events(project, root, m):
    """The event frames for O5, from the project this picture came from. Only a contract of this exact composition counts."""
    project = Path(project) if project else Path(root).parent / "v2" / "editorial"
    doc = contract.load(project)
    if doc is None or doc.get("composition_rev") != m.get("composition_rev"):
        return None
    return [e for e in doc["events"] if "frame" in e]


def check(path, project=None, root=None):
    path = Path(path).resolve()
    root = Path(root or path.parents[2])
    report = {"schema": 1, "check": "output", "file": str(path), "checks": {}}
    record = store.read_json(path.parent / "stitch.json")
    if not path.is_file() or record is None:
        report.update(status=UNVERIFIED, why=f"no file, or no stitch.json beside {path}")
        return report
    folder = path.parent
    file_sha = sound_mix.file_hash(path)
    m = store.read_json(folder / "ownership.json", {})
    lock = store.read_json(folder / "beats.lock.json", {})
    report.update(file_sha256=file_sha, stitched_sha256=record["file_sha256"], composition_rev=record["composition_rev"], lock_revision=record["lock_revision"],
                  profile=record["profile"], profile_hash=record["profile_hash"], engine_hash=record["engine_hash"])
    problems = []
    if file_sha != record["file_sha256"]:
        problems.append("this file is not the one stitch.json describes")
    if m.get("composition_rev") != record["composition_rev"]:
        problems.append("ownership.json beside it is of another composition")
    if lock.get("revision") != record["lock_revision"]:
        problems.append("beats.lock.json beside it is of another lock")
    report["checks"]["binding"] = result(FAIL if problems else PASS, problems=problems)
    if not lock.get("beats") or not m.get("shared"):
        report["status"] = FAIL
        return finish(report, root, file_sha, record)

    events = project_events(project, root, m)
    report["event_frames"] = "used" if events is not None else "no contract of this composition, so samples are first, middle and last only"
    stream = stitcher.probe_video(path)
    width, height = stream["width"], stream["height"]
    total, fps = lock["total_frames"], lock["fps"]
    wanted = sorted({f for b in lock["beats"] for f in sentinel.samples(b, events or [])})
    try:
        rows, picked, suspects = sentinel.scan(path, width, height, wanted, keep_suspects=SUSPECTS_KEPT)
    except RuntimeError as e:
        report["checks"]["O1"] = result(FAIL, problems=[str(e)[:400]])
        report["status"] = FAIL
        return finish(report, root, file_sha, record)

    first = store.find(root, record["profile_hash"], record["beats"][0]["key"]) if record["beats"] else None
    report["checks"]["O1"] = o1_frames(rows, total, stream, first["stream"] if first else None)
    report["checks"]["O2"], segments = o2_content(root, record, rows)
    report["checks"]["O3"] = o3_timestamps(path, fps, total)
    report["checks"]["O4"] = o4_joins(record, rows, segments, path, lock, m, width)
    report["checks"]["O5"] = o5_samples(root, record, lock, picked, suspects, width, height, events or [])
    is_final = record["profile"] != "review"
    report["checks"]["O6"] = o6_gates(path, width, is_final)
    if not is_final:
        report["checks"]["loudness"] = result(UNVERIFIED, why="the review bed is unmastered, because finish.py runs only in delivery")
    if events is None:
        report["checks"]["events"] = result(UNVERIFIED, why=report["event_frames"])
    report["checks"]["O7"] = o7_coverage(total, report["checks"]["O5"])
    apply_waivers(report, waivers_of(project, root), record)
    report["status"] = worst(c["status"] for name, c in report["checks"].items() if name != "O7")
    return finish(report, root, file_sha, record)


def finish(report, root, file_sha, record):
    folder = Path(root) / "checks" / record["composition_rev"][:16]
    folder.mkdir(parents=True, exist_ok=True)
    name = f"output-{file_sha[:16]}.json"
    report["path"] = str(folder / name)
    store.write_json(folder / name, report)
    return report


def summary(report):
    for name, c in report["checks"].items():
        detail = {k: v for k, v in c.items() if k != "status" and v not in (None, [], {}, 0)}
        print(name, c["status"], json.dumps(detail, ensure_ascii=False)[:400])
    for w in report.get("waived", []):
        print("WAIVED", json.dumps(w, ensure_ascii=False)[:300])
    print(report["status"], report.get("path", report.get("why", "")))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file")
    ap.add_argument("--project", help="default: the project beside the store")
    ap.add_argument("--store", help="default: the store the file sits in")
    a = ap.parse_args(argv)
    report = check(a.file, a.project, a.store)
    summary(report)
    return NOT_CHECKED if "why" in report else CODES[report["status"]]


if __name__ == "__main__":
    sys.exit(main())
