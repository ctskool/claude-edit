"""Measures what each kind of note touches, with real edits to a copy of the fixture's real sources. CONTRACT.md section 9.

  python tools/beat_render/touch_table.py [--out report.md]

For each case: edit the copy, run its real build.py, compare the two maps with ownership.invalidate, then restore the copy.
Nothing is rendered and the fixture is never written. The copy sits two levels under work/, as the fixture does, because build.py finds tools/ from there.
"""
import argparse, json, os, shutil, statistics, subprocess, sys, tempfile
from pathlib import Path

import lock
import ownership
import sound_mix
from common import overlaps

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import project_root
ROOT = project_root()
FIXTURE = ROOT / "work" / "beat-fixture"
ED = FIXTURE / "v2" / "editorial"
OUT = ROOT / "reports" / "2026-10-31-moves-plan-page" / "stage1" / "phase2-note-touch-table.md"
SKIP = shutil.ignore_patterns("__pycache__", "renders", "snaps*", ".hyperframes", "*.tmp")
MOST = 0.5  # "most of the video"
SCENES = "tools_local/scenes.py"
TIMELINE = "tools_local/timeline.js"
OWNERS = "tools_local/owners.py"
STYLE = "tools_local/style.css"
PLAN = "plan.json"


# ---- edits, each real and each on one project copy


def sub(project, rel, old, new):
    path = project / rel
    text = path.read_bytes().decode("utf8")
    if text.count(old) != 1:
        raise ValueError(f"{rel}: expected one {old!r}, found {text.count(old)}")
    path.write_bytes(text.replace(old, new).encode("utf8"))


def edit_plan(project, change):
    path = project / PLAN
    plan = json.loads(path.read_text(encoding="utf8"))
    change(plan)
    path.write_text(json.dumps(plan, indent=1, ensure_ascii=False), encoding="utf8", newline="\n")


def chunk(plan, first_word):
    return next(c for c in plan["captions"]["chunks"] if c["words"][0] == first_word)


def caption_word(first_word):
    def change(plan):
        c = chunk(plan, first_word)
        words = c["text"].split(" ")
        words[-1] = "NOTED"
        c["text"] = " ".join(words)
    return change


def caption_time(first_word, delta):
    def change(plan):
        c = chunk(plan, first_word)
        c["on"] = round(c["on"] + delta, 3)
    return change


def beat_time(beat_id, delta):
    def change(plan):
        rows = plan["beats"]
        i = next(n for n, b in enumerate(rows) if b["id"] == beat_id)
        rows[i]["start"] = rows[i - 1]["end"] = round(rows[i]["start"] + delta, 3)
    return change


def swap_bytes(project, rel, other):
    path = project / rel
    if os.stat(path).st_nlink != 1:
        raise ValueError(f"{rel} is hard-linked; a write here could reach another project")
    shutil.copyfile(project / other, path)


def text_edit(*rows):
    return lambda p: [sub(p, *row) for row in rows]


def plan_edit(change):
    return lambda p: edit_plan(p, change)


CASES = [
    ("Caption word", "One word in a chip labelled b02 that opens inside b01", [PLAN], plan_edit(caption_word(6))),
    ("Caption word", "One word in a chip inside the long b14", [PLAN], lambda p: edit_plan(p, caption_word(first_word_in(p, "b14")))),
    ("Caption word", "One chip opens 0.1 s later, same word (chip time)", [PLAN], lambda p: edit_plan(p, caption_time(first_word_in(p, "b14", 1), 0.1))),
    ("Word in a graphic", "'my schedule' to 'my calendar', b16's one-beat scene", [SCENES], text_edit((SCENES, ">my schedule<", ">my calendar<"))),
    ("Word in a graphic", "'sort receipts' to 'sort invoices', the b38-b39 scene", [SCENES], text_edit((SCENES, '"sort receipts"', '"sort invoices"'))),
    ("Word in a graphic", "'personal life' to 'home life', the grid scene (b07, b09-b12)", [SCENES], text_edit((SCENES, ">personal life<", ">home life<"))),
    ("Word in a graphic", "'Tap to talk' to 'Tap to speak', b19, the scene that also writes #cab3", [SCENES], text_edit((SCENES, ">Tap to talk<", ">Tap to speak<"))),
    ("Card swap in one scene", "The radar card points at a different still, one scene", [SCENES],
     text_edit((SCENES, 'plate("rd-pl", "stills/research-outlier-radar.png", RD, RDB)', 'plate("rd-pl", "stills/research-github-trending.png", RD, RDB)'))),
    ("Card swap in one scene", "The radar card points at a still no scene used before", [SCENES, "assets/stills/architecture-clean.png"],
     text_edit((SCENES, 'plate("rd-pl", "stills/research-outlier-radar.png", RD, RDB)', 'plate("rd-pl", "stills/architecture-clean.png", RD, RDB)'))),
    ("Card swap in one scene", "Same still path, new bytes, used by one scene", ["assets/stills/research-outlier-radar.png"],
     lambda p: swap_bytes(p, "assets/stills/research-outlier-radar.png", "assets/stills/research-github-trending.png")),
    ("Card swap in one scene", "Same still path, new bytes, the orb used by four scenes", ["assets/stills/jarvis-orb-claude.png"],
     lambda p: swap_bytes(p, "assets/stills/jarvis-orb-claude.png", "assets/stills/research-github-trending.png")),
    ("Card swap in one scene", "A playing clip card points at a different clip", [SCENES],
     text_edit((SCENES, 'vplate("dr-pl", [], "clips/directives-panel.mp4", DR, DB, 27.7, 2.4, 0)', 'vplate("dr-pl", [], "clips/obsidian-overview.mp4", DR, DB, 27.7, 2.4, 0)'))),
    ("Card swap in one scene", "Same clip path, new bytes", ["assets/clips/directives-panel.mp4"],
     lambda p: swap_bytes(p, "assets/clips/directives-panel.mp4", "assets/clips/skills-panel.mp4")),
    ("Scene-group change", "Grid scene: card resized and a tile move retimed, windows unchanged", [SCENES, TIMELINE],
     text_edit((SCENES, 'card("gr-card", (117, 130, 846, 630))', 'card("gr-card", (117, 130, 846, 640))'),
               (TIMELINE, 'tl.to("#gr-orb-m", { x: OX, duration: 0.5,', 'tl.to("#gr-orb-m", { x: OX, duration: 0.6,'))),
    ("Timing change", "A tween inside b16's block moves 0.11 s", [TIMELINE], text_edit((TIMELINE, 'pop("#dr-tile", 28.69);', 'pop("#dr-tile", 28.8);'))),
    ("Timing change", "One scene window ends 0.1 s later (b16 to b17)", [OWNERS],
     text_edit((OWNERS, '["#sc-dr", 27.7, 30.1], ["#sc-sk", 30.1, 32.9]', '["#sc-dr", 27.7, 30.2], ["#sc-sk", 30.2, 32.9]'))),
    ("Timing change", "One clip's data-start moves 0.1 s", [SCENES],
     text_edit((SCENES, 'vplate("dr-pl", [], "clips/directives-panel.mp4", DR, DB, 27.7, 2.4, 0)', 'vplate("dr-pl", [], "clips/directives-panel.mp4", DR, DB, 27.8, 2.4, 0)'))),
    ("Timing change", "One beat boundary moves 0.1 s (b12 to b13)", [PLAN], plan_edit(beat_time("b13", 0.1))),
    ("Shared style change", "Caption chip radius, 10 to 12 px", [STYLE], text_edit((STYLE, ".chip .in { height: 96px; padding: 0 26px; border-radius: 10px;", ".chip .in { height: 96px; padding: 0 26px; border-radius: 12px;"))),
    ("Shared helper", "timeline.js pop() lasts 0.02 s longer", [TIMELINE], text_edit((TIMELINE, "duration: dur || 0.26,", "duration: dur || 0.28,"))),
    ("Shared helper", "scenes.py card() gains one style", [SCENES],
     text_edit((SCENES, '''return f'<div id="{id_}" class="pc" style="{boxstyle(b)};{style}"></div>\'''', '''return f'<div id="{id_}" class="pc" style="{boxstyle(b)};outline:0;{style}"></div>\''''))),
    ("HUD seat", "First HUD state, strip arrives 0.1 s later", [OWNERS], text_edit((OWNERS, '["strip", 6.8]', '["strip", 6.9]'))),
    ("HUD seat", "Second plug seats 0.2 s later (seat1, b17)", [OWNERS], text_edit((OWNERS, '["seat1", 32.21]', '["seat1", 32.41]'))),
    ("HUD seat", "Last ring flashes 0.1 s later (ring3)", [OWNERS], text_edit((OWNERS, '["ring3", 95.88]', '["ring3", 95.98]'))),
]


def first_word_in(project, beat_id, nth=0):
    """The first chip of a beat can sit on a layout switch, and build.py snaps a chip there, so a time edit uses a later one."""
    plan = json.loads((project / PLAN).read_text(encoding="utf8"))
    return [c["words"][0] for c in plan["captions"]["chunks"] if c["beat"] == beat_id][nth]


# ---- running


def build(project):
    r = subprocess.run([sys.executable, "tools_local/build.py"], cwd=project, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"build failed in {project}:\n{r.stdout}\n{r.stderr}")
    m = ownership.load(project)
    if m is None:
        raise RuntimeError(f"build left no valid map in {project}")
    return m


def restore(project, files):
    for rel in files:
        shutil.copyfile(ED / rel, project / rel)


def measure(project, base):
    rows = []
    for kind, note, files, change in CASES:
        change(project)
        new = build(project)
        beat_lock = lock.load(project)
        r = ownership.invalidate(base, new, beat_lock, files)
        if new["composition_rev"] == base["composition_rev"]:
            raise RuntimeError(f"edit changed nothing: {note}")
        rows.append({"kind": kind, "note": note, "files": files, "result": r})
        restore(project, files)
        print(f"{r['share']:6.1%} {len(r['beats']):3d} beats  {kind}: {note}", flush=True)
    if build(project)["composition_rev"] != base["composition_rev"]:
        raise RuntimeError("the copy did not return to its starting picture after the cases")
    return rows


def reach(m, beat_lock, kind):
    """Share of the video one changed owner of this kind would touch, for every owner. Computed from the map, not an edit."""
    out = []
    for o in m["owners"]:
        if o["kind"] == kind:
            out.append(sum(b["end_frame"] - b["start_frame"] for b in beat_lock["beats"] if overlaps(o["frames"], b)) / beat_lock["total_frames"])
    return sorted(out)


# ---- writing


def beat_runs(beats, order):
    """b07, b09-b12. Beats are ordered by the lock, so a run is unbroken in it."""
    index = {b: i for i, b in enumerate(order)}
    runs = []
    for b in beats:
        if runs and index[b] == index[runs[-1][-1]] + 1:
            runs[-1].append(b)
        else:
            runs.append([b])
    return ", ".join(r[0] if len(r) == 1 else f"{r[0]}-{r[-1]}" for r in runs)


def pct(x):
    return f"{x:.1%}"


def write_table(rows, m, beat_lock, out):
    order = [b["beat_id"] for b in beat_lock["beats"]]
    total = beat_lock["total_frames"]
    most = [r for r in rows if r["result"]["share"] > MOST]
    whole = [r for r in rows if r["result"]["all"]]
    local = [r for r in rows if r["result"]["share"] <= 0.1]
    kinds = list(dict.fromkeys(r["kind"] for r in rows))
    lines = ["# Phase 2: what each note touches", ""]
    find = lambda text: next(r["result"] for r in rows if text in r["note"])
    b19, seat1, first_seat = find("Tap to talk"), find("seat1"), find("First HUD state")
    still = find("points at a different still")
    lines += [f"**Result: {len(most)} of {len(rows)} real edits touched more than half the video, and {len(whole)} of those touched all of it. {len(local)} touched 10% or less.**", ""]
    lines += ["Most kinds do not touch most of the video, but two of the six kinds this test asked about do. A caption word, a word in a graphic, a still card swap and a scene-group change stay small. A timing change and a shared style change touch all of it.", ""]
    lines += [f"- **Small:** a caption word, a word in a graphic, a still swap in one scene, a scene-group change and a tween time inside a block. Each touched 1 to 5 beats, at most {pct(find('home life')['share'])} of the video, with one exception below. A still used by four scenes touches those four, {pct(find('orb')['share'])}.",
              f"- **Most or all of the video:** a scene window, a beat time, a clip's start, a shared style, a shared helper and a clip swap, at {pct(find('timeline.js pop')['share'])} or close to it. The window, beat time, clip start and clip swap also force a new media plan.",
              f"- **HUD notes depend on when the state lands.** An early one reaches {pct(first_seat['share'])}, because nothing resets the strip, so every later frame carries it. The last one reaches {pct(find('ring3')['share'])}.",
              f"- **The exception:** a word in b19's card touches {pct(b19['share'])}. That scene also writes the HUD's `#cab3`, see below.", ""]
    lines += ["This counts kinds of edit, not Chase's notes. How often he gives each kind is unmeasured, so this cannot say what share of his real notes will be slow. Phases 4 and 6 measure that.", ""]
    lines += ["Every row is a real edit to a real source in a copy of `work/beat-fixture/v2/editorial`, rebuilt with its real `build.py` and compared by `ownership.invalidate`. "
              "Nothing was rendered, so this says what would re-render, not how long it takes, and it does not prove the map right on pixels. Shares are whole beats, because a beat is the unit that renders.", ""]
    lines += ["## By kind", "", "| Kind | Edits | Smallest | Largest | Over half the video |", "|---|---:|---:|---:|---:|"]
    for k in kinds:
        shares = [r["result"]["share"] for r in rows if r["kind"] == k]
        lines.append(f"| {k} | {len(shares)} | {pct(min(shares))} | {pct(max(shares))} | {sum(s > MOST for s in shares)} |")
    lines += ["", "## Every edit", "", "| Kind | Real edit | Owners changed | Beats touched | Beats | Frames | Share | New media plan |", "|---|---|---:|---|---:|---:|---:|---|"]
    for r in rows:
        x = r["result"]
        named = f"all {len(order)}" if x["all"] else beat_runs(x["beats"], order)
        lines.append(f"| {r['kind']} | {r['note']} | {len(x['owners_changed'])} | {named} | {len(x['beats'])} | {x['frames_touched']} | {pct(x['share'])} | {'yes' if x['new_media_plan'] else 'no'} |")
    lines += ["", "## Why the whole-video rows are whole", "", "| Real edit | Reasons |", "|---|---|"]
    for r in whole:
        reasons = r["result"]["all_reasons"]
        lines.append(f"| {r['note']} | {', '.join(reasons[:4]) + (f', and {len(reasons) - 4} more' if len(reasons) > 4 else '')} |")
    lines += ["", "## Any one owner", "", "Computed from the map, not from edits: the share one changed owner would touch, across every owner of that kind.", "",
              "| Owner kind | Owners | Smallest | Median | Largest | Over half the video |", "|---|---:|---:|---:|---:|---:|"]
    for kind, label in (("caption", "Caption"), ("scene", "Scene"), ("hud", "HUD link")):
        shares = reach(m, beat_lock, kind)
        lines.append(f"| {label} | {len(shares)} | {pct(shares[0])} | {pct(statistics.median(shares))} | {pct(shares[-1])} | {sum(s > MOST for s in shares)} |")
    lines += ["", "## What sets these numbers", "",
              f"- **`#cab3`.** The cable sits in HUD DOM, and b19's block animates it. The contract declares it as an extra root, but a tween on it moved past the scene's window would still show, because the HUD stays up. "
              f"So an owner with an extra root now reaches the last frame. That is why b19 costs {pct(b19['share'])}. One declared reset would bring it back to one beat, once `tools/beat_check` can measure it.",
              f"- **HUD resets.** Ivory declares none, as the contract says, so `hud.seat1` touches every frame from 967 on, {pct(seat1['share'])}. Declared resets are the way to cut this, and they need the same measuring.",
              "- **Still library, added in this phase.** With the contract's rule as written, pointing a card at another still touched the whole video. The old still fell out of its owner, became a file nobody names, and landed in the shared files. "
              f"The first run of this table showed that at 100%. `owners.py` now declares `LIBRARY`, three folders of stills, and a file there that the page never names stays out of the shared files. The same edit now costs {pct(still['share'])}. A page that may build an asset path at runtime loses the exemption. This is a declaration the reviewer should check.",
              "- **Timing.** The contract counts the scene window table, beat times, and any video `data-start` as timing. Each one costs the whole video plus a new media plan, for time only. A tween time inside a block stays local.",
              "- **A scene-group change that alters a window** is a timing change, not a scene-group change. The row above leaves the windows alone.", ""]
    lines += ["For scale, on a shared machine, Phase 1 rendered all 56 beats at 540 wide in 228 s with 4 workers, and its media plan took 117 s. Those are not note turnarounds, which Phase 4 measures.", ""]
    tmp = Path(str(out) + ".tmp")
    tmp.write_text("\n".join(lines), encoding="utf8", newline="\n")
    os.replace(tmp, out)
    return len(most), len(whole), len(rows), total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    before = sound_mix.file_hash(ED / "index.html"), sound_mix.file_hash(ED / PLAN)
    base_dir = Path(tempfile.mkdtemp(prefix="beat-touch-", dir=ROOT / "work"))
    try:
        project = base_dir / "v2" / "editorial"
        for name in ("metadata.json", "words.json", "beats.json"):  # the build reads all three, two levels up
            shutil.copyfile(FIXTURE / name, base_dir / name)
        shutil.copytree(ED, project, ignore=SKIP)
        base = build(project)
        fixture_map = ownership.load(ED)
        if fixture_map is None or base["composition_rev"] != fixture_map["composition_rev"]:
            raise RuntimeError("the copy does not rebuild to the fixture's map")
        rows = measure(project, base)
        write_table(rows, base, lock.load(project), args.out)
    finally:
        shutil.rmtree(base_dir)
    if before != (sound_mix.file_hash(ED / "index.html"), sound_mix.file_hash(ED / PLAN)):
        raise RuntimeError("the fixture changed during the run")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
