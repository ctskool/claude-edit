"""Pull critic evidence from an ENCODED render (frames selected by index, never by timestamp).

Usage: python evidence.py <video.mp4> <out_dir> [--band 0,0,1080,900] [--max-strips 24]
Writes into out_dir:
  overview.jpg            1 fps, 8 columns, timestamped
  dense_<t0>.jpg          5 fps sheets, one per 6 s window (10x3 cells)
  strip_<frame>.jpg       10-frame strips (n-4 .. n+5) around the biggest graphics-band changes
  INDEX.md                what each file is, with times
"""
import argparse
import os
import subprocess

import cv2
import numpy as np


def run(args):
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + args, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out_dir")
    ap.add_argument("--band", default="0,0,1080,900")
    ap.add_argument("--max-strips", type=int, default=24)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    x, y, w, h = map(int, a.band.split(","))
    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    dur = n / fps
    lines = [f"# Evidence for {a.video}", f"{n} frames @ {fps:.2f} fps = {dur:.2f} s. Frame index i <-> time i/{fps:.0f}.", ""]

    label = "drawtext=text='%{pts\\:hms}':x=4:y=4:fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.6"
    rows = int(np.ceil(dur / 8))
    run(["-i", a.video, "-vf", f"fps=1,scale=216:-2,{label},tile=8x{rows}", "-frames:v", "1", os.path.join(a.out_dir, "overview.jpg")])
    lines.append("- overview.jpg: 1 frame per second, 8 per row, timestamp top-left")
    for t0 in np.arange(0, dur - 0.5, 6.0):  # skip a sliver window at the end (no frames at 5 fps)
        name = f"dense_{t0:05.1f}.jpg"
        run(["-ss", f"{t0:.2f}", "-t", "6", "-i", a.video, "-vf", f"fps=5,scale=180:-2,{label},tile=10x3", "-frames:v", "1",
             os.path.join(a.out_dir, name)])
        lines.append(f"- {name}: {t0:.1f}-{min(t0 + 6, dur):.1f} s at 5 fps (timestamps are relative to the window start + {t0:.1f}s)")

    prev, diffs = None, []
    for i in range(n):
        ok, f = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(cv2.resize(f[y:y + h, x:x + w], (96, int(96 * h / w))), cv2.COLOR_BGR2GRAY).astype(np.int16)
        diffs.append(0.0 if prev is None else float(np.abs(g - prev).mean()))
        prev = g
    order = np.argsort(diffs)[::-1]
    picked = []
    for i in order:
        if diffs[i] < 2.0 or len(picked) >= a.max_strips:
            break
        if all(abs(i - p) > 8 for p in picked):
            picked.append(int(i))
    lines.append("")
    lines.append("Strips around the largest graphics-band changes (frame n-4 .. n+5, 5 per row):")
    for i in sorted(picked):
        s0 = max(0, i - 4)
        name = f"strip_{i:05d}.jpg"
        run(["-i", a.video, "-vf", f"select='between(n\\,{s0}\\,{s0 + 9})',scale=270:-2,tile=5x2", "-fps_mode", "vfr", "-frames:v", "1",
             os.path.join(a.out_dir, name)])
        lines.append(f"- {name}: frames {s0}-{s0 + 9} ({s0 / fps:.2f}-{(s0 + 9) / fps:.2f} s), change magnitude {diffs[i]:.1f}")
    open(os.path.join(a.out_dir, "INDEX.md"), "w").write("\n".join(lines) + "\n")
    print(os.path.join(a.out_dir, "INDEX.md"))


if __name__ == "__main__":
    main()
