"""Test-only renderer qualification. Writes no store segment. stage1/phase2-renderer.md holds the results.

  python tools/beat_render/qualify.py range <project> --profile review --start 0 --end 3214 --workers 1 --rotate 0 --out DIR [--inject KIND@OFFSET]
  python tools/beat_render/qualify.py sweep <project> --profile review --counts 2,4,6 --out FILE

range renders one or more long pages, past anything a real beat reaches, and compares every frame to a reference picture by decoded frame number. --rotate 0 keeps one page for its whole chunk.
sweep times whole forced drafts through run.py at each worker count, with the other work on the machine listed before and after each.

  python tools/beat_render/qualify.py exit <project> --profile review --out FILE

  python tools/beat_render/qualify.py faults <project> --profiles review,final --out FILE
  python tools/beat_render/qualify.py compare <file> --profile final --out FILE

faults injects each fault through run.py at each profile, with the beat's segment removed first, so a segment afterwards can only come from a clean retry.
compare checks any whole render against the reference picture, every frame, for the fault's signature.
exit makes a real one-beat edit in plan.json, rebuilds, runs change, compares every decoded frame to the picture before it, then restores the source and runs change again.
"""
import argparse, json, shutil, subprocess, sys, time
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run as runner
import sentinel
import store

ROOT = runner.ROOT
REFERENCES = {"review": ROOT / "work/beat-fixture/compare/reference-540.mp4", "final": ROOT / "out/1030-1_editorial_v3.mp4"}
FAULT_DB = 30.0


def frames_of(path, width, height, skip=0):
    size = sentinel.frame_bytes(width, height)
    n = 0
    with subprocess.Popen(["ffmpeg", "-v", "error", "-threads", "2", "-i", str(path), "-map", "0:v:0", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as p:
        while True:
            data = p.stdout.read(size)
            if len(data) < size:
                break
            if n >= skip:
                yield n, data
            n += 1


def compare_chunks(chunks, reference, width, height, region_top):
    """Every frame of every chunk against the reference. Pairs by decoded frame number."""
    refs = frames_of(reference, width, height, chunks[0]["start"])
    rows, suspects = [], []
    for chunk in chunks:
        for local, data in frames_of(chunk["path"], width, height):
            global_frame, ref = next(refs)
            if global_frame != chunk["start"] + local:
                raise RuntimeError(f"frame pairing slipped at {global_frame}")
            rows.append((global_frame, sentinel.psnr(data, ref, width, height), sentinel.psnr(data, ref, width, height, region_top)))
            if sentinel.clipped(data, width, height):
                suspects.append(global_frame)
    refs.close()
    bad = [f for f, whole, region in rows if whole < FAULT_DB or region < FAULT_DB]
    runs = []
    for f in bad:
        if runs and runs[-1][1] == f:
            runs[-1][1] = f + 1
        else:
            runs.append([f, f + 1])
    return {"frames": len(rows), "min_psnr": round(min(r[1] for r in rows), 2), "min_psnr_region": round(min(r[2] for r in rows), 2),
            "frames_under_30": len(bad), "runs_under_30": runs, "clip_suspects": len(suspects), "first_suspects": suspects[:8]}


def cmd_range(args):
    run = runner.Run(SimpleNamespace(project=args.project, profile=args.profile, workers=args.workers, store=None, inject_fault=None, inject_beats=None, inject_rounds=0))
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    tmp = out / "tmp"
    tmp.mkdir(exist_ok=True)
    run.ensure_plan()
    run.prepare(tmp)
    size = args.end - args.start
    chunk = -(-size // args.workers)
    chunks, procs = [], []
    started = time.perf_counter()
    for slot in range(args.workers):
        a, b = args.start + slot * chunk, min(args.end, args.start + (slot + 1) * chunk)
        path = out / f"chunk{slot}.mp4"
        entry = {"id": f"q{slot}", "start": a, "end": b, "path": str(path)}
        if args.inject:
            kind, offset = args.inject.split("@")
            entry["inject"] = {"kind": kind, "offset": int(offset)}
        chunks.append(entry)
        job = run.job(tmp, f"worker{slot}", ranges=[entry], result=str(tmp / f"worker{slot}-result.json"), fresh=False, page_rotate_frames=args.rotate)
        procs.append(runner.node(runner.RENDER, "capture", job, tmp / f"worker{slot}.log"))
    codes = runner.finish_all(procs, 600 + 4 * size)
    wall = time.perf_counter() - started
    results = [store.read_json(tmp / f"worker{i}-result.json") for i in range(args.workers)]
    report = {"profile": args.profile, "range": [args.start, args.end], "workers": args.workers, "rotate": args.rotate, "inject": args.inject, "exit_codes": codes, "capture_wall_s": round(wall, 1), "workers_detail": results}
    if all(c == 0 for c in codes):
        reference = Path(args.reference) if args.reference else REFERENCES[args.profile]
        report["compare"] = compare_chunks(chunks, reference, *run.frame_size, run.region_top)
        report["reference"] = str(reference)
    store.write_json(out / "result.json", report)
    print(json.dumps(report, indent=1))
    return 0 if all(c == 0 for c in codes) else 1


def others_rendering():
    """Other work on this machine, for the record. Reads process names and command lines, touches nothing."""
    if sys.platform == "win32":
        script = "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'hyperframes(\\\\|/|\\.mjs| render)|remotion render|animate\\.mjs render|ffmpeg.*(-c:v|libx264)' } | ForEach-Object { $_.Name + ' ' + $_.CommandLine.Substring(0,[Math]::Min(90,$_.CommandLine.Length)) }"
        r = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True)
        return [line for line in r.stdout.splitlines() if "beat_render" not in line and "beat-fixture" not in line]
    
    r = subprocess.run(["ps", "-axo", "pid=,comm=,args="], capture_output=True, text=True)
    return [line for line in r.stdout.splitlines() if any(s in line for s in ("hyperframes", "remotion render", "ffmpeg"))
            and "beat_render" not in line and "beat-fixture" not in line]


def cmd_sweep(args):
    results = []
    for workers in [int(x) for x in args.counts.split(",")]:
        before = others_rendering()
        changes = sorted(store.root_of(args.project).glob("changes/*.json"))
        started = time.perf_counter()
        code = runner.main(["draft", args.project, "--profile", args.profile, "--workers", str(workers), "--force"])
        wall = time.perf_counter() - started
        after = others_rendering()
        newest = sorted(store.root_of(args.project).glob("changes/*.json"))[-1]
        record = store.read_json(newest, {}) if len(sorted(store.root_of(args.project).glob("changes/*.json"))) > len(changes) else {}
        results.append({"workers": workers, "exit": code, "wall_s": round(wall, 1), "timings": record.get("timings"), "boots": sum(r["boots"] for r in record.get("worker_results", []) if r),
                        "sentinel": record.get("sentinel_at_render"), "retried": record.get("retried"), "others_before": len(before), "others_after": len(after), "others_sample": (before + after)[:6]})
        store.write_json(args.out, results)
    print(json.dumps(results, indent=1))
    return 0


FAULTS = [("viewport", 1, "b05"), ("dom", 1, "b05"), ("crash", 1, "b05"), ("viewport", 3, "b05"), ("dom", 1, "b03"), ("dom", 1, "b10")]


def segment_of(root, profile_hash, beat_id):
    for path in (root / "segments" / profile_hash[:16]).glob("*/segment.json"):
        if store.read_json(path, {}).get("beat_id") == beat_id:
            return path.parent
    return None


def cmd_faults(args):
    project = Path(args.project).resolve()
    root = store.root_of(project)
    results = []
    for name in args.profiles.split(","):
        profile_hash = runner.load_profile(name, 1)[1]
        for kind, rounds, beat in FAULTS:
            old = segment_of(root, profile_hash, beat)
            if old:
                shutil.rmtree(old)
            code = runner.main(["draft", str(project), "--profile", name, "--workers", "1", "--inject-fault", kind, "--inject-beats", beat, "--inject-rounds", str(rounds)])
            record = store.read_json(sorted(root.glob("changes/*.json"))[-1])
            after = segment_of(root, profile_hash, beat)
            row = {"profile": name, "kind": kind, "beat": beat, "fault_rounds": rounds, "exit": code, "status": record["status"], "wall_s": record["wall_s"],
                   "rounds": [{"published": r["published"], "why": {b: f["why"][:220] for b, f in r["failures"].items()}} for r in record["rounds"]],
                   "unresolved": record.get("unresolved", []), "segment_after": bool(after), "tmp_left": len(list((root / "tmp").iterdir()))}
            if after:
                seg = store.read_json(after / "segment.json")
                row["segment"] = {"retries": seg["render"]["retries"], "sentinel": seg["sentinel"]["status"], "min_psnr": seg["sentinel"]["min_psnr"], "frames": seg["decoded"]["frames"], "complete": bool(store.find(root, profile_hash, seg["input_key"]))}
            results.append(row)
            store.write_json(args.out, results)
    print(json.dumps(results, indent=1, ensure_ascii=False))
    return 0


def cmd_compare(args):
    size = runner.load_profile(args.profile, 1)[0]
    result = compare_chunks([{"start": 0, "path": args.file}], Path(args.reference) if args.reference else REFERENCES[args.profile], size["width"], size["height"], size["height"] // 2)
    result["file"] = args.file
    store.write_json(args.out, result)
    print(json.dumps(result, indent=1))
    return 0


def build(project):
    subprocess.run([sys.executable, "tools_local/build.py"], cwd=project, check=True, capture_output=True)


def reuse_check(before, after, lock, rendered, width, height):
    """Decoded rows of two stitched pictures, beat by beat. Reused beats must be bit-identical."""
    a, b = sentinel.scan(before, width, height)[0], sentinel.scan(after, width, height)[0]
    outside = [f for x in lock["beats"] if x["beat_id"] not in rendered for f in range(x["start_frame"], x["end_frame"])]
    different = [f for f in outside if a[f] != b[f]]
    inside = [f for x in lock["beats"] if x["beat_id"] in rendered for f in range(x["start_frame"], x["end_frame"]) if a[f] != b[f]]
    return {"frames_a": len(a), "frames_b": len(b), "reused_frames_checked": len(outside), "reused_frames_different": len(different), "rendered_frames": sum(x["end_frame"] - x["start_frame"] for x in lock["beats"] if x["beat_id"] in rendered), "rendered_frames_different": len(inside)}


def cmd_exit(args):
    project = Path(args.project).resolve()
    root = store.root_of(project)
    profile = args.profile
    plan_file = project / "plan.json"
    original = plan_file.read_bytes()
    first = store.latest(root, profile)
    report = {"profile": profile, "first": first["file"]}
    data = json.loads(original.decode("utf8"))
    chunk = next(c for c in data["captions"]["chunks"] if c["words"][0] == args.first_word)
    report["edit"] = {"beat": chunk["beat"], "before": chunk["text"], "after": args.text}
    chunk["text"] = args.text
    try:
        plan_file.write_text(json.dumps(data, indent=1, ensure_ascii=False) + chr(10), encoding="utf8", newline=chr(10))
        build(project)
        started = time.perf_counter()
        code = runner.main(["change", str(project), "--profile", profile, "--kind", "caption"])
        report["change"] = {"exit": code, "wall_s": round(time.perf_counter() - started, 1)}
        newest = sorted(root.glob("changes/*.json"))[-1]
        record = store.read_json(newest)
        report["change"].update({k: record.get(k) for k in ("rendered", "share", "timings", "status", "sentinel_at_render", "under_invalidated")})
        second = store.latest(root, profile)
        lock = store.read_json(project / "beats.lock.json")
        size = runner.load_profile(profile, 1)[0]
        report["change"]["reuse"] = reuse_check(first["file"], second["file"], lock, record["rendered"], size["width"], size["height"])
    finally:
        plan_file.write_bytes(original)
        build(project)
    started = time.perf_counter()
    code = runner.main(["change", str(project), "--profile", profile, "--kind", "go-back"])
    report["restore"] = {"exit": code, "wall_s": round(time.perf_counter() - started, 1)}
    record = store.read_json(sorted(root.glob("changes/*.json"))[-1])
    third = store.latest(root, profile)
    report["restore"].update({k: record.get(k) for k in ("rendered", "status")})
    report["restore"]["reuse"] = reuse_check(first["file"], third["file"], store.read_json(project / "beats.lock.json"), record["rendered"], size["width"], size["height"])
    store.write_json(args.out, report)
    print(json.dumps(report, indent=1, ensure_ascii=False))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    r = sub.add_parser("range")
    r.add_argument("project")
    r.add_argument("--profile", default="review")
    r.add_argument("--start", type=int, default=0)
    r.add_argument("--end", type=int, required=True)
    r.add_argument("--workers", type=int, default=1)
    r.add_argument("--rotate", type=int, default=0)
    r.add_argument("--inject")
    r.add_argument("--reference")
    r.add_argument("--out", required=True)
    s = sub.add_parser("sweep")
    s.add_argument("project")
    s.add_argument("--profile", default="review")
    s.add_argument("--counts", default="2,4,6")
    s.add_argument("--out", required=True)
    f = sub.add_parser("faults")
    f.add_argument("project")
    f.add_argument("--profiles", default="review,final")
    f.add_argument("--out", required=True)
    c = sub.add_parser("compare")
    c.add_argument("file")
    c.add_argument("--profile", default="final")
    c.add_argument("--reference")
    c.add_argument("--out", required=True)
    e = sub.add_parser("exit")
    e.add_argument("project")
    e.add_argument("--profile", default="review")
    e.add_argument("--first-word", type=int, default=79)
    e.add_argument("--text", default="SO WE SEE")
    e.add_argument("--out", required=True)
    args = parser.parse_args()
    return {"range": cmd_range, "sweep": cmd_sweep, "exit": cmd_exit, "faults": cmd_faults, "compare": cmd_compare}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
