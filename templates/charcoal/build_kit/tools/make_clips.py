#!/usr/bin/env python3
"""Cuts the clips in tools/clips.json (written by build.mjs) from this cut's own footage. Run from work/<id>/full.

  python tools/make_clips.py            the clips designed scenes show, when missing or changed
  python tools/make_clips.py --all      also the clips of scenes that are only footage (fullFace, screenFull)

screen = ../raw/cut.mp4 (his screen), cam = ../raw/cam_cut.mp4 (his camera). Crop and scale only, nothing generated.
Each clip covers its scene's seconds on the cut timeline exactly, at 30 fps. CLIP_SCALE=2 makes them at twice their
stage size for a 4K render; render_slices.py sets it and runs this itself before it renders.

A scene that is only footage is built by ffmpeg straight from the cut (slices.json `ff`), so its clip file is not
needed for a render and is skipped. --all makes those too: for `npx hyperframes preview`, a snapshot of such a scene,
or `hyperframes check` on the whole page.
"""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

K = int(os.environ.get("CLIP_SCALE", "1"))   # 1 for the 1080p review render, 2 for the 4K final
SRC = {"screen": Path("../raw/cut.mp4"), "cam": Path("../raw/cam_cut.mp4")}
clips = json.loads(Path("tools/clips.json").read_text())
sl = Path("tools/slices.json")
FF = {s["id"] for s in json.loads(sl.read_text()) if s.get("ff")} if sl.exists() else set()
# tools/holds.json: pauses added to the project's media that raw/cut.mp4 does not have.
HOLDS = json.loads(Path("tools/holds.json").read_text()) if Path("tools/holds.json").exists() else []


def raw_t(t):
    """A time of the project (with its added and removed stretches) -> the time of raw/cut.mp4. HOLDS = [[at, d], ...]:
    at a time `at` of raw/cut.mp4, d seconds were added (d > 0) or the d seconds before it removed (d < 0)."""
    c = 0
    for at, d in sorted(HOLDS):
        if t >= at + c + d - 1e-6: c += d            # after this change
        elif t > at + c + min(d, 0): return at       # inside an added stretch: no such moment in raw/cut.mp4
        else: break
    return t - c


def make(c):
    out = Path(c["file"]); side = out.with_suffix(".json")
    if c.get("footage") in FF and "--all" not in sys.argv:
        return None
    # start and end in the times of raw/cut.mp4, so a pause added to the project (tools/holds.json) does not re-cut clips
    spec = json.dumps({k: c[k] for k in ("src", "crop", "w", "h")} | {"start": round(raw_t(c["start"]), 3), "end": round(raw_t(c["end"]), 3), "k": K}, sort_keys=True)
    if out.exists() and side.exists() and side.read_text() == spec:
        return f"ok    {c['id']}"
    x, y, w, h = c["crop"]
    frames = round((c["end"] - c["start"]) * 30 + 1e-6)
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{raw_t(c['start']):.3f}", "-i", str(SRC[c["src"]]), "-frames:v", str(frames), "-an",
           "-vf", f"fps=30,crop={w}:{h}:{x}:{y},scale={c['w'] * K}:{c['h'] * K}:flags=lanczos",
           "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-g", "30", "-pix_fmt", "yuv420p", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        return f"FAIL  {c['id']}: {r.stderr[-300:]}"
    side.write_text(spec)
    return f"made  {c['id']} ({frames} frames)"


def main():
    Path("assets/clips").mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(3) as ex:
        lines = [x for x in ex.map(make, clips) if x]
    for line in lines:
        print(line)
    print(f"{len(lines)} of {len(clips)} clips needed ({len(clips) - len(lines)} are footage slices, built by ffmpeg)")
    return 1 if any(x.startswith("FAIL") for x in lines) else 0


if __name__ == "__main__":
    sys.exit(main())
