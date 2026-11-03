"""The approval check, the backstop for a wrong cache. PLAN-V2-BEAT-REVIEW.md Workstream D.

  python tools/beat_review/approval.py check <project> --picture <sha256>       the whole check. review.approve starts this in its own process
  python tools/beat_review/approval.py compare <a.mp4> <b.mp4> --out rows.json  two files, every frame

Comparing a final to a review render is not sound, so every beat is rendered fresh at the same complete review profile, into a separate store that shares nothing with the picture's and never
replaces a segment, then compared to the approved file, every frame, paired by decoded frame number, with no exemption for touched beats. Fresh captures are not bit-identical, so the method has
three zones, set by qualification on clean reruns against planted defects (stage1/phase3-approval-qualification.json): under pass_under passes, over fail_over is a real difference and stops, and
between them no machine can call it, so the differing regions go to Chase. With no qualification, or if clean noise and defects overlapped, nothing passes by itself.

A record is written once, beat/approvals/<file_sha16>.json, and never overwritten. approvals/active.json says which picture is approved now, and any picture change clears it.
"""
import argparse, json, os, shutil, subprocess, sys, time, uuid
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import project_root
ROOT = project_root()
sys.path[:0] = [str(HERE), str(ROOT / "tools" / "beat_render"), str(ROOT / "tools")]
import ownership
import review
import sentinel
import sound_mix
import stitch as stitcher
import store

EVIDENCE = ROOT / "reports" / "2026-10-31-moves-plan-page" / "stage1" / "phase3-approval-qualification.json"
RUN = ROOT / "tools" / "beat_render" / "run.py"
PROFILES = ROOT / "tools" / "beat_render" / "profiles.json"
BLOCK_PX, FINE_PX = 48, 24  # at 1080 wide. Scaled with the frame, so a block covers the same part of the picture at every size. A small object is lost in a 48 px block, so a finer one runs too
METRICS = ("block", "fine", "chroma")  # higher is worse. psnr is reported and never decides: a whole-frame number averages a small change away
OK = ("PASS", "RECONCILED")
GROUP_GAP = 3  # flagged frames this close are one region
MAX_REGIONS = 24
BOX_DIFF = 16  # a pixel this far off counts toward a crop's box
BOX_PAD = 20
SCALE = 2
METHOD = "every decoded frame paired by frame number. Luma PSNR, worst sliding 48 and 24 px luma window and worst 48 px chroma window by mean absolute difference, half-window step"


def approvals(root):
    path = Path(root) / "approvals"
    path.mkdir(exist_ok=True)
    return path


# ---- comparing two files


def frames_of(path, width, height):
    size = sentinel.frame_bytes(width, height)
    with subprocess.Popen(["ffmpeg", "-v", "error", "-threads", "2", "-i", str(path), "-map", "0:v:0", "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as p:
        while True:
            data = p.stdout.read(size)
            if len(data) < size:
                return
            yield data


def planes(data, width, height):
    n, c = width * height, (width // 2) * (height // 2)
    y = np.frombuffer(data, np.uint8, n, 0).reshape(height, width).astype(np.int16)
    u = np.frombuffer(data, np.uint8, c, n).reshape(height // 2, width // 2).astype(np.int16)
    v = np.frombuffer(data, np.uint8, c, n + c).reshape(height // 2, width // 2).astype(np.int16)
    return y, u, v


def worst_window(d, side):
    """The worst mean over any side by side window, stepping half a side, with the last row and column of windows on the frame's edge. Returns value, y, x."""
    h, w = d.shape
    total = np.pad(d.astype(np.int64).cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    ys = np.unique(np.r_[np.arange(0, h - side, side // 2), h - side])
    xs = np.unique(np.r_[np.arange(0, w - side, side // 2), w - side])
    sums = total[np.ix_(ys + side, xs + side)] - total[np.ix_(ys, xs + side)] - total[np.ix_(ys + side, xs)] + total[np.ix_(ys, xs)]
    at = np.unravel_index(int(sums.argmax()), sums.shape)
    return float(sums[at]) / (side * side), int(ys[at[0]]), int(xs[at[1]])


def frame_row(a, b, width, height):
    """[psnr, block, fine, chroma, y, x], where y and x are the worst block's corner."""
    ya, ua, va = planes(a, width, height)
    yb, ub, vb = planes(b, width, height)
    d = np.abs(ya - yb)
    mse = float((d.astype(np.float32) ** 2).mean())
    block, y, x = worst_window(d, max(4, BLOCK_PX * width // 1080))
    fine = worst_window(d, max(4, FINE_PX * width // 1080))[0]
    side = max(4, BLOCK_PX * width // 2160)
    chroma = max(worst_window(np.abs(ua - ub), side)[0], worst_window(np.abs(va - vb), side)[0])
    return [99.0 if mse == 0 else round(float(10 * np.log10(255 * 255 / mse)), 2), round(block, 2), round(fine, 2), round(chroma, 2), y, x]


def compare(approved, fresh, on_frame=None):
    """Every frame of two files. Frames pair by decoded frame number. A frame count that differs is reported, never paired around."""
    stream = stitcher.probe_video(approved)
    other = stitcher.probe_video(fresh)
    width, height = stream["width"], stream["height"]
    if (other["width"], other["height"]) != (width, height):
        raise ValueError(f"{other['width']}x{other['height']} against {width}x{height}: not the same profile")
    rows = {}
    n = identical = 0
    for a, b in zip(frames_of(approved, width, height), frames_of(fresh, width, height)):
        if a == b:
            identical += 1
        else:
            rows[n] = frame_row(a, b, width, height)
        n += 1
        if on_frame and n % 300 == 0:
            on_frame(n)
    worst = {name: max((r[i + 1] for r in rows.values()), default=0.0) for i, name in enumerate(METRICS)}
    return {"frames_approved": stream["packets"], "frames_fresh": other["packets"], "frames_compared": n, "identical": identical, "width": width, "height": height,
            "worst_psnr": min((r[0] for r in rows.values()), default=99.0), "worst_block": worst["block"], "worst_fine": worst["fine"], "worst_chroma": worst["chroma"],
            "worst_frame": {name: max(rows, key=lambda f: rows[f][i + 1]) if rows else None for i, name in enumerate(METRICS)}, "rows": rows}


def over(row, limits):
    return any(row[i + 1] > limits[name] for i, name in enumerate(METRICS))


def regions(numbers, limits, lock=None):
    """Frames over these limits, grouped into runs, worst frame of each. Worst run first."""
    flagged = sorted(f for f, r in numbers["rows"].items() if over(r, limits))
    runs = []
    for f in flagged:
        if runs and f - runs[-1][-1] <= GROUP_GAP:
            runs[-1].append(f)
        else:
            runs.append([f])
    rows = numbers["rows"]
    score = lambda f: max(rows[f][i + 1] / max(limits[name], 0.01) for i, name in enumerate(METRICS))
    out = []
    for run in runs:
        worst = max(run, key=score)
        beats = [b["beat_id"] for b in (lock or {}).get("beats", []) if b["start_frame"] <= run[-1] and run[0] < b["end_frame"]]
        beat = next((b["beat_id"] for b in (lock or {}).get("beats", []) if b["start_frame"] <= worst < b["end_frame"]), None)
        out.append({"first": run[0], "last": run[-1], "frames": len(run), "worst_frame": worst, "beat": beat, "beats": beats, "block": rows[worst][1], "fine": rows[worst][2], "chroma": rows[worst][3], "y": rows[worst][4], "x": rows[worst][5], "score": round(score(worst), 2)})
    return sorted(out, key=lambda r: -r["score"])


def rgb(data, width, height):
    """yuv420p to an RGB array, BT.709 limited range, as the render is encoded."""
    y, u, v = (p.astype(np.float32) for p in planes(data, width, height))
    u, v = (np.repeat(np.repeat(p, 2, axis=0), 2, axis=1)[:height, :width] - 128 for p in (u, v))
    y = (y - 16) * 1.164
    out = np.stack([y + 1.793 * v, y - 0.213 * u - 0.533 * v, y + 2.112 * u], axis=-1)
    return np.clip(out, 0, 255).astype(np.uint8)


def crop_box(a, b, width, height, region):
    """The box of what differs around the worst block."""
    d = np.abs(planes(a, width, height)[0] - planes(b, width, height)[0])
    side = max(4, BLOCK_PX * width // 1080)
    near = d[max(0, region["y"] - side):region["y"] + 2 * side, max(0, region["x"] - side):region["x"] + 2 * side]
    ys, xs = np.nonzero(near > BOX_DIFF)
    top, left = max(0, region["y"] - side), max(0, region["x"] - side)
    if len(ys):
        return max(0, top + int(ys.min()) - BOX_PAD), max(0, left + int(xs.min()) - BOX_PAD), min(height, top + int(ys.max()) + BOX_PAD), min(width, left + int(xs.max()) + BOX_PAD)
    return top, left, min(height, region["y"] + 2 * side), min(width, region["x"] + 2 * side)


def write_crops(approved, fresh, found, width, height, out):
    """One image per region: the approved picture, the fresh one, and their difference at four times. Frames are found by decoded frame number."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    found = found[:MAX_REGIONS]
    wanted = [r["worst_frame"] for r in found]
    a = sentinel.scan(approved, width, height, wanted)[1]
    b = sentinel.scan(fresh, width, height, wanted)[1]
    for r in found:
        f = r["worst_frame"]
        top, left, bottom, right = crop_box(a[f], b[f], width, height, r)
        left_img, right_img = rgb(a[f], width, height)[top:bottom, left:right], rgb(b[f], width, height)[top:bottom, left:right]
        diff = np.clip(np.abs(left_img.astype(np.int16) - right_img.astype(np.int16)) * 4, 0, 255).astype(np.uint8)
        strip = np.concatenate([left_img, np.full((bottom - top, 8, 3), 128, np.uint8), right_img, np.full((bottom - top, 8, 3), 128, np.uint8), diff], axis=1)
        image = Image.fromarray(strip)
        name = f"frame{f:05d}-{r['beat'] or 'beat'}-approved-fresh-diff.png"
        image.resize((image.width * SCALE, image.height * SCALE), Image.NEAREST).save(out / name)
        r["image"] = str(out / name)
    return found


def qualification():
    """The limits the qualification run set, or None."""
    doc = store.read_json(EVIDENCE)
    return doc.get("limits") if doc else None


def decide(numbers, limits):
    """PASS, FAIL or RECONCILE, with why. Frames that do not line up are a FAIL whatever the pixels say."""
    if numbers["frames_approved"] != numbers["frames_fresh"] or numbers["frames_compared"] != numbers["frames_approved"]:
        return "FAIL", f"{numbers['frames_approved']} frames against {numbers['frames_fresh']}, {numbers['frames_compared']} compared"
    if limits is None:
        return "RECONCILE", "the method has no qualification, so nothing passes by itself"
    if any(over(r, limits["fail_over"]) for r in numbers["rows"].values()):
        return "FAIL", "a region is over the line real defects reached"
    if any(over(r, limits["pass_under"]) for r in numbers["rows"].values()):
        return "RECONCILE", "a region is over clean noise and under the line real defects reached"
    if limits.get("overlap"):
        return "RECONCILE", "clean noise and real defects overlapped in qualification, so nothing passes by itself"
    return "PASS", "every frame is inside clean noise"


# ---- the record


def write_once(path, record):
    """Refuses to replace a record, whatever is there. The rename is a hard link, which fails if the name exists."""
    tmp = Path(str(path) + f".{uuid.uuid4().hex}")
    tmp.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf8", newline="\n")
    try:
        os.link(tmp, path)
    finally:
        tmp.unlink()


def record_of(pic, fresh_sha, numbers, result, **extra):
    profile = json.loads(PROFILES.read_text(encoding="utf8"))["profiles"][review.PROFILE]
    limits = qualification()
    return {"approved_file_sha256": pic["file_sha256"], "composition_rev": pic["composition_rev"], "lock_revision": pic["lock_revision"], "profile": profile, "fresh_file_sha256": fresh_sha,
            "method": {"how": METHOD, "limits": limits, "qualification": str(EVIDENCE.relative_to(ROOT)) if limits else None}, "frames_compared": numbers["frames_compared"],
            "worst_psnr": numbers["worst_psnr"], "worst_block": numbers["worst_block"], "worst_fine": numbers["worst_fine"], "worst_chroma": numbers["worst_chroma"], "identical_frames": numbers["identical"],
            "result": result, "created": review.now(), **extra}


def activate(root, pic):
    store.write_json(approvals(root) / "active.json", {"file_sha256": pic["file_sha256"], "composition_rev": pic["composition_rev"], "lock_revision": pic["lock_revision"], "approved": review.now()})


def clear(root):
    (approvals(root) / "active.json").unlink(missing_ok=True)


def clear_unless(root, picture_sha):
    if store.read_json(approvals(root) / "active.json", {}).get("file_sha256", picture_sha) != picture_sha:
        clear(root)


def hold_for_notes(project, root, pic):
    """A note a round still owes stops every way a picture becomes approved, because he is still changing it."""
    left = review.open_notes(project, root, pic)
    if left:
        raise ValueError(f"{len(left)} note(s) still open: do them in a round, or drop them")


def bound(record, pic):
    return (record["approved_file_sha256"], record["composition_rev"], record["lock_revision"]) == (pic["file_sha256"], pic["composition_rev"], pic["lock_revision"])


# ---- state


def status(project):
    """none, running, reconcile, blocked, error, failed or approved, for the newest picture."""
    root = review.root_of(project)
    pic = review.picture(project)
    empty = {"state": "none", "record": None}
    if pic is None:
        return empty
    folder = approvals(root)
    tag = pic["file_sha256"][:16]
    running = store.read_json(folder / f"running-{tag}.json")
    if running:
        if store.alive(running["pid"]):
            return {"state": "running", "stage": running["stage"], "started": running["started"], "record": None}
        return {"state": "error", "why": "the check stopped with no result", "record": None}
    record = store.read_json(folder / f"{tag}.json")
    if record and record["result"] == "FAIL":
        return {"state": "failed", "record": record, "regions": record.get("regions", []), "regions_dir": record.get("regions_dir")}
    if record and bound(record, pic) and store.read_json(folder / "active.json", {}).get("file_sha256") == pic["file_sha256"]:
        return {"state": "approved", "record": record}
    for state in ("reconcile", "blocked", "error"):
        held = store.read_json(folder / f"{state}-{tag}.json")
        if held:
            return {**held, "state": state, "record": None}
    return {**empty, "record": record}


def start(project, picture_sha):
    """Checks everything a quick look can, then starts the check in its own process. A picture already approved by a record of this exact composition needs no second render."""
    project = Path(project).resolve()
    root = review.root_of(project)
    pic = review.picture(project)
    if pic is None or pic["file_sha256"] != picture_sha:
        raise ValueError("that is not the newest picture")
    if sound_mix.file_hash(pic["file"]) != picture_sha:
        raise ValueError("the file on disk is not this picture")
    m = ownership.load(project)
    if m is None or m["composition_rev"] != pic["composition_rev"]:
        raise ValueError("the project has moved on from this picture: run run.py change, or go back")
    left = review.blocking(project, root, pic)
    if left:
        raise ValueError("fix or waive first: " + ", ".join(f["id"] for f in left[:8]))
    hold_for_notes(project, root, pic)
    folder = approvals(root)
    tag = picture_sha[:16]
    record = store.read_json(folder / f"{tag}.json")
    if record:
        if record["result"] == "FAIL":
            beats = ",".join(sorted({b for r in record.get("regions", []) for b in r.get("beats") or [r.get("beat") or "?"]}))
            raise ValueError(f"the check failed on this picture and a record is written once. Repair it: run.py draft --force --only {beats}, then run.py stitch. Regions: {record.get('regions_dir')}")
        if not bound(record, pic):
            raise ValueError("a record for this file names another composition, and a record is written once")
        activate(root, pic)
        return status(project)
    now_state = status(project)
    if now_state["state"] == "running":
        return now_state
    for name in ("running", "reconcile", "blocked", "error"):
        (folder / f"{name}-{tag}.json").unlink(missing_ok=True)
    log = open(folder / f"{tag}.log", "a", encoding="utf8")
    p = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "check", str(project), "--picture", picture_sha], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                         creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0))
    log.close()
    store.write_json(folder / f"running-{tag}.json", {"pid": p.pid, "stage": "starting", "started": review.now()})
    return status(project)


def reconcile(project, picture_sha, why):
    """Chase looked at the regions and says the picture stands. Only a check that found neither a clean pass nor a real difference can end this way."""
    root = review.root_of(project)
    pic = review.picture(project)
    if pic is None or pic["file_sha256"] != picture_sha:
        raise ValueError("that is not the newest picture")
    if not (why or "").strip():
        raise ValueError("a reconcile needs a reason")
    hold_for_notes(project, root, pic)
    folder = approvals(root)
    held = store.read_json(folder / f"reconcile-{picture_sha[:16]}.json")
    if not held:
        raise ValueError("this picture has no regions waiting for you")
    write_once(folder / f"{picture_sha[:16]}.json", {**held["record"], "result": "RECONCILED", "why": why.strip(), "reconciled": review.now()})
    (folder / f"reconcile-{picture_sha[:16]}.json").unlink()
    activate(root, pic)
    return status(project)


# ---- the check


def run_check(project, picture_sha, reuse=None):
    """reuse is qualification only: an existing fresh store of this same composition, so a planted picture is judged without a third whole render. review.approve never passes it."""
    project = Path(project).resolve()
    root = review.root_of(project)
    folder = approvals(root)
    tag = picture_sha[:16]
    pic = review.picture(project)
    running = folder / f"running-{tag}.json"
    held = store.read_json(running, {"pid": os.getpid(), "started": review.now()})

    def stage(name, **fields):
        store.write_json(running, {**held, "pid": os.getpid(), "stage": name, **fields})
        print(review.now(), name, fields, flush=True)

    def stop(state, **fields):
        store.write_json(folder / f"{state}-{tag}.json", {"created": review.now(), **fields})
        print(review.now(), state, fields.get("why", ""), flush=True)

    try:
        fresh = Path(reuse) if reuse else review.home_of(project) / "beat-fresh" / tag
        stage("rendering")
        started = time.perf_counter()
        code = None
        if not reuse:
            shutil.rmtree(fresh, ignore_errors=True)
            code = subprocess.run([sys.executable, str(RUN), "draft", str(project), "--profile", review.PROFILE, "--store", str(fresh)], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
        changes = sorted((fresh / "changes").glob("*.json"))
        done = store.read_json(changes[-1]) if changes else None
        if code == 2 or not done or not done.get("file_sha256"):
            return stop("error", why=f"the fresh render did not finish: run.py exited {code}")
        render_s = round(time.perf_counter() - started, 1)
        fresh_file = Path(done["stitched"].replace("\\", "/"))
        m = ownership.load(project)
        if m is None or m["composition_rev"] != pic["composition_rev"]:
            return stop("error", why="the project moved during the check")
        stage("comparing", render_s=render_s)
        started = time.perf_counter()
        numbers = compare(pic["file"], fresh_file)
        compare_s = round(time.perf_counter() - started, 1)
        limits = qualification()
        result, why = decide(numbers, limits)
        line = limits["pass_under"] if limits else dict.fromkeys(METRICS, 0)
        lock = store.read_json(root / "stitched" / pic["stitched"] / "beats.lock.json", {})
        found = regions(numbers, line, lock)
        regions_dir = folder / f"regions-{tag}"
        if found:
            write_crops(pic["file"], fresh_file, found, numbers["width"], numbers["height"], regions_dir)
        provenance = {"reused_fresh": bool(reuse), "fresh_store": str(fresh.resolve()), "fresh_file_sha256": done["file_sha256"], "approved_file_sha256": pic["file_sha256"]}
        store.write_json(folder / f"compare-{tag}.json", {**{k: (v if k != "rows" else {str(f): r for f, r in v.items()}) for k, v in numbers.items()}, "render": provenance})
        fresh_pic = {"file_sha256": done["file_sha256"], "composition_rev": done["composition_rev"], "stitched": fresh_file.parent.name, "status": done["status"]}
        # This is the first source check of every beat on this composition, so the player's findings read it too
        for path in (fresh / "checks" / pic["composition_rev"][:16]).glob(f"source-*{done['file_sha256'][:16]}.json"):
            shutil.copy(path, root / "checks" / pic["composition_rev"][:16] / f"source-approval-{tag}.json")
        left = review.blocking(project, fresh, fresh_pic)
        extra = {"regions": found[:MAX_REGIONS], "regions_dir": str(regions_dir) if found else None, "why": why, "render_s": render_s, "compare_s": compare_s, "render": provenance}
        record = record_of(pic, done["file_sha256"], numbers, result, **extra)
        if result == "FAIL":
            write_once(folder / f"{tag}.json", record)
        elif left:
            stop("blocked", why="the fresh render's checks found what the picture's did not", findings=left[:24], regions=found[:MAX_REGIONS], regions_dir=extra["regions_dir"])
        elif result == "RECONCILE":
            stop("reconcile", why=why, regions=found[:MAX_REGIONS], regions_dir=extra["regions_dir"], record=record)
        else:
            write_once(folder / f"{tag}.json", record)
            if not review.open_notes(project, root, pic):  # a note left during the check: the record stands, and approving again activates it with no second render
                activate(root, pic)
        for name in ("segments", "refs", "plans", "tmp") if not reuse else ():  # the file and its checks are the evidence, and they stay
            shutil.rmtree(fresh / name, ignore_errors=True)
        print(review.now(), result, why, {k: v for k, v in numbers.items() if k != "rows"}, flush=True)
    finally:
        running.unlink(missing_ok=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    c = sub.add_parser("check")
    c.add_argument("project")
    c.add_argument("--picture", required=True)
    c.add_argument("--reuse-fresh", help="qualification only: a fresh store of this same composition")
    d = sub.add_parser("compare")
    d.add_argument("a")
    d.add_argument("b")
    d.add_argument("--out")
    a = ap.parse_args(argv)
    if a.command == "check":
        run_check(a.project, a.picture, a.reuse_fresh)
        return 0
    numbers = compare(a.a, a.b)
    if a.out:
        store.write_json(a.out, {k: (v if k != "rows" else {str(f): r for f, r in v.items()}) for k, v in numbers.items()})
    print(json.dumps({k: v for k, v in numbers.items() if k != "rows"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
