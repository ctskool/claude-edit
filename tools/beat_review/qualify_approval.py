"""Qualifies the approval check's comparison on real runs. Test only. Writes stage1/phase3-approval-qualification.json, and approval.py reads its limits.

  python tools/beat_review/qualify_approval.py plant <copy's v2/editorial>           makes the planted picture
  python tools/beat_review/qualify_approval.py measure --base <mp4> --clean <mp4> <mp4> [...] --planted <mp4> --beats <plants.json>
  python tools/beat_review/qualify_approval.py widen --compare <compare-*.json> [...]    adds clean whole-render comparisons to the evidence and sets the limits again

plant makes real edits in a copy, renders what they touch, goes back, then publishes the wrong segments under the right keys, with matching records and references, and stitches.
So the store is wrong, every record agrees with it, and every other check is blind: only a fresh render can show it. Never point this at the fixture.
measure compares clean pairs and the planted picture to clean renders, every frame, per plant, and sets the limits. If any plant stays inside clean noise on every measure, the two overlap, and it says so.
widen is for what approval checks turned up later. It takes only comparisons of a clean picture to its own fresh render, as approval.py wrote them, and judges the same plants by the same rule. Nothing else about the method moves.
"""
import argparse, json, shutil, subprocess, sys, time, uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import project_root
ROOT = project_root()
sys.path.insert(0, str(HERE))
import approval
import review
import store

MARGIN = 1.15  # pass_under, over the worst clean pair
PLANTS = {  # what each stands for, and the beat its wrong segment lands in
    "stale_cube": {"beat": "b16", "what": "an 84 px tile left 10 px from where the composition puts it, for one beat"},
    "wrong_word": {"beat": "b38", "what": "'sort invoices' where the composition says 'sort receipts', one small list row"},
    "small_object": {"beat": "b53", "what": "the 22 px moving dot in the wrong colour"},
    "one_letter": {"beat": "b48", "what": "one letter of a label: 'Whisper = eers'"},
}


def sub(project, rel, old, new):
    path = Path(project) / rel
    text = path.read_bytes().decode("utf8")
    if old not in text:
        raise ValueError(f"{old} not in {rel}")
    path.write_bytes(text.replace(old, new).encode("utf8"))


def word(project, old, new, in_scene):
    sub(project, "tools_local/scenes.py", in_scene, in_scene.replace(old, new))
    sub(project, "tools_local/owners.py", f'"{old}"', f'"{new}"')
    sub(project, "../../beats.json", f'"{old}"', f'"{new}"')
    sub(project, "plan.json", f'"{old}"', f'"{new}"')


def edit(project):
    """The wrong picture, in real sources."""
    sub(project, "tools_local/scenes.py", 'id="al-dot" class="abs" style="left:-11px;top:-11px;width:22px;height:22px;border-radius:50%;background:var(--clay)', 'id="al-dot" class="abs" style="left:-11px;top:-11px;width:22px;height:22px;border-radius:50%;background:#2f8fd0')
    word(project, "sort receipts", "sort invoices", '"sort receipts"')
    word(project, "Whisper = ears", "Whisper = eers", ">Whisper = ears<")
    text = (Path(project) / "tools_local/scenes.py").read_text(encoding="utf8")
    at = text.index('id="dr-tile"')
    line = text[at:text.index(">", at)]
    left = line[line.index("left:") + 5:line.index("px", line.index("left:"))]
    sub(project, "tools_local/scenes.py", line, line.replace(f"left:{left}px", f"left:{int(left) + 10}px"))


def plant(project):
    project = Path(project).resolve()
    if "beat-fixture" in str(project):
        raise ValueError("never in the fixture")
    root = review.root_of(project)
    review.close_round(project)
    base = review.picture(project)
    base_beats = {b["beat_id"]: b for b in review.stitched_beats(root, base["stitched"])}
    edit(project)
    subprocess.run([sys.executable, "tools_local/build.py"], cwd=project, check=True, stdout=subprocess.DEVNULL)
    started = time.perf_counter()
    r = subprocess.run([sys.executable, str(review.RUN), "change", str(project), "--profile", "review", "--kind", "planted"], cwd=ROOT, stdout=subprocess.DEVNULL)
    print("change exit", r.returncode, round(time.perf_counter() - started), "s", flush=True)
    wrong = review.picture(project)
    wrong_beats = {b["beat_id"]: b for b in review.stitched_beats(root, wrong["stitched"])}
    profile = store.read_json(root / "stitched" / wrong["stitched"] / "stitch.json")["profile_hash"]
    swapped = [b for b in wrong_beats if wrong_beats[b]["key"] != base_beats[b]["key"]]
    review.go_back(project, 0)
    # A wrong segment, published under the right key, with records and references that agree with it
    for beat in swapped:
        good, bad = base_beats[beat]["key"], wrong_beats[beat]["key"]
        built = root / "tmp" / f"plant-{uuid.uuid4().hex}"
        shutil.copytree(store.segment_dir(root, profile, bad), built)
        record = store.read_json(built / "segment.json")
        store.write_json(built / "segment.json", {**record, "input_key": good})
        store.publish(root, built, profile, good, force=True)
        refs = store.refs_dir(root, profile, good)
        shutil.rmtree(refs, ignore_errors=True)
        shutil.copytree(store.refs_dir(root, profile, bad), refs)
    r = subprocess.run([sys.executable, str(review.RUN), "stitch", str(project), "--profile", "review"], cwd=ROOT, capture_output=True, text=True, encoding="utf8", errors="replace")
    done = store.read_json(sorted((root / "changes").glob("*.json"))[-1])
    out = {"swapped": swapped, "stitch_exit": r.returncode, "status": done.get("status"), "checks": done.get("checks"), "file": done.get("stitched"), "file_sha256": done.get("file_sha256"), "current_moved": done.get("current_moved")}
    store.write_json(project.parents[1] / "plants.json", out)
    print(json.dumps(out, indent=1))
    return out


def stats(numbers):
    return {k: numbers[k] for k in ("frames_compared", "identical", "worst_psnr", "worst_block", "worst_fine", "worst_chroma", "worst_frame")}


def within(numbers, start, end):
    rows = {f: r for f, r in numbers["rows"].items() if start <= f < end}
    return {"frames_differing": len(rows), "worst_psnr": min((r[0] for r in rows.values()), default=99.0), "worst_block": max((r[1] for r in rows.values()), default=0.0), "worst_fine": max((r[2] for r in rows.values()), default=0.0), "worst_chroma": max((r[3] for r in rows.values()), default=0.0)}


def measure(a):
    runs = {}
    clean = [Path(p) for p in a.clean]
    pairs = [("base", a.base, c) for c in clean] + [(f"clean{i}", clean[i], clean[j]) for i in range(len(clean)) for j in range(i + 1, len(clean))]
    worst = dict.fromkeys(approval.METRICS, 0.0)
    for name, x, y in pairs:
        started = time.perf_counter()
        numbers = approval.compare(x, y)
        runs[f"{name} vs {Path(y).parts[-4] if 'fresh' in str(y) else Path(y).name}"] = {**stats(numbers), "compare_s": round(time.perf_counter() - started, 1)}
        print(name, stats(numbers), flush=True)
        for m in approval.METRICS:
            worst[m] = max(worst[m], numbers[f"worst_{m}"])
    lock = store.read_json(a.lock)
    beats = {b["beat_id"]: b for b in lock["beats"]}
    plants = {}
    for c in clean:
        numbers = approval.compare(a.planted, c)
        print("planted", stats(numbers), flush=True)
        for name, plant_ in PLANTS.items():
            b = beats[plant_["beat"]]
            row = within(numbers, b["start_frame"], b["end_frame"])
            old = plants.setdefault(name, {**plant_, "against": []})
            old["against"].append(row)
    doc = {"created": review.now(), "clean_pairs": runs, "clean_worst": worst, "margin": MARGIN, "plants": plants, "planted_picture_checks": store.read_json(a.plants) if a.plants else None,
           "note": "Qualified on one fixture, a 107 s ivory edit at the review profile, on a shared machine. A new raw may need it checked."}
    write_limits(doc)


def judged(worst, plants):
    """The limits and which plants they catch, from the worst clean noise and what each plant reached. One rule for measure and widen."""
    limits = {"pass_under": {m: round(worst[m] * MARGIN + 0.05, 2) for m in approval.METRICS}}
    caught = {}
    for name, p in plants.items():
        low = {m: min(r[f"worst_{m}"] for r in p["against"]) for m in approval.METRICS}
        p["lowest"] = low
        caught[name] = [m for m in approval.METRICS if low[m] > limits["pass_under"][m]]
    overlap = [name for name, ms in caught.items() if not ms]
    # A real difference is anything at or past what the weakest plant reached on the measure that caught it, and never less than twice clean noise
    limits["fail_over"] = {m: round(max(min([plants[n]["lowest"][m] for n, ms in caught.items() if m in ms], default=float("inf")), limits["pass_under"][m] * 2) * 0.95, 2) if any(m in ms for ms in caught.values()) else 255.0 for m in approval.METRICS}
    limits["overlap"] = bool(overlap)
    stops = {name: [m for m in approval.METRICS if p["lowest"][m] > limits["fail_over"][m]] for name, p in plants.items()}
    return {"caught_by": caught, "stopped_by": stops, "inside_clean_noise": overlap, "limits": limits}


def write_limits(doc):
    doc.update(judged(doc["clean_worst"], doc["plants"]))
    store.write_json(approval.EVIDENCE, doc)
    print(json.dumps({k: doc[k] for k in ("clean_worst", "caught_by", "stopped_by", "inside_clean_noise", "limits")}, indent=1))


def widen(a):
    """Clean noise only ever grows here, so a limit can only move up, and a plant it no longer catches shows as overlap, which turns off every automatic pass."""
    doc = store.read_json(approval.EVIDENCE)
    for path in a.compare:
        numbers = store.read_json(path)
        provenance = numbers.get("render", {})
        reused = provenance.get("reused_fresh")
        label = "a reused fresh render in an approval check" if reused is True else "a whole fresh render in an approval check" if reused is False else "an approval comparison; fresh-render provenance unknown"
        doc["clean_pairs"][str(path)] = {**stats(numbers), "from": label, "render": provenance, "reused_fresh": reused}
        for m in approval.METRICS:
            doc["clean_worst"][m] = max(doc["clean_worst"][m], numbers[f"worst_{m}"])
    doc["widened"] = review.now()
    write_limits(doc)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub_ = ap.add_subparsers(dest="command", required=True)
    p = sub_.add_parser("plant")
    p.add_argument("project")
    m = sub_.add_parser("measure")
    m.add_argument("--base", required=True)
    m.add_argument("--clean", nargs="+", required=True)
    m.add_argument("--planted", required=True)
    m.add_argument("--lock", required=True)
    m.add_argument("--plants")
    w = sub_.add_parser("widen")
    w.add_argument("--compare", nargs="+", required=True)
    a = ap.parse_args(argv)
    if a.command == "plant":
        plant(a.project)
    elif a.command == "widen":
        widen(a)
    else:
        measure(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
