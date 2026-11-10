#!/usr/bin/env python3
"""Find one-frame jumps in a project's newest review picture. Advisory: it prints what to look at and exits 0.

python tools/beat_check/jumps.py work/<id>/v2/editorial [--picture <review.mp4>]

A contact sheet at one frame a second cannot show a card that snaps in a single frame, and both light-path tests had one that
every other check passed. Two findings:

  JOIN   a beat join that falls inside a scene's window with no layout switch, where the picture changes far more on that one
         frame than on the frames either side. Each beat renders as its own segment, so a scene that spans a join can come out
         in two slightly different states. This is a defect: make the two beats one, or give the scene one window per beat.
  SPIKE  any other frame whose change stands alone (quiet before, quiet after) and that no time written in the page explains.
         Look at it; a planned hard cut inside a clip reads the same way.

Only the graphics are measured: the panel above the seam on a split beat, the frame above the chip on a takeover. Full-face beats
are skipped, and so is his footage.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

W, H = 270, 480
SEAM, TAKEOVER_CHIP = 904 / 1920, 1470 / 1920  # just above the chip in each layout
QUIET, RATIO, FLOOR = 4, 4.0, 0.35


def frames(path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "gray", "-"], stdout=subprocess.PIPE)
    size = W * H
    while True:
        buf = p.stdout.read(size)
        if len(buf) < size:
            break
        yield buf
    p.wait()


def change(a, b, rows):
    n = rows * W
    return sum(abs(x - y) for x, y in zip(a[:n], b[:n])) / n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--picture")
    args = ap.parse_args()
    project = Path(args.project).resolve()
    work = project.parent.parent
    if args.picture:
        picture, lock_dir = Path(args.picture), Path(args.picture).parent
    else:
        cur = json.loads((work / "beat" / "current.json").read_text(encoding="utf8"))["review"]
        picture, lock_dir = Path(cur["file"]), Path(cur["file"]).parent
    lock_file = lock_dir / "beats.lock.json" if (lock_dir / "beats.lock.json").is_file() else project / "beats.lock.json"
    beats = json.loads(lock_file.read_text(encoding="utf8"))["beats"]
    html = (project / "index.html").read_text(encoding="utf8")
    windows = json.loads(re.search(r"/\*@WINDOWS\*/(\[.*?\]);", html, re.S).group(1))
    fps = 30
    # every time the page itself names: a frame beside one of these has a reason to change
    script = html[html.rindex("<script>"):]
    named = set()
    for m in re.finditer(r"(?<![\w.#-])(\d+(?:\.\d+)?)(?=\s*[,)\]])", script):
        t = float(m.group(1))
        if 0 < t < beats[-1]["end_frame"] / fps + 1:
            f = round(t * fps)
            named.update((f - 1, f, f + 1))
    layout_at = {}
    for b in beats:
        for f in range(b["start_frame"], b["end_frame"]):
            layout_at[f] = b["layout"]
    joins = [b["start_frame"] for a, b in zip(beats, beats[1:]) if a["layout"] == b["layout"] and b["layout"] != "full-face"
             and any(round(w[1] * fps) < b["start_frame"] < round(w[2] * fps) for w in windows)]
    rows = {"split": int(H * SEAM), "full-graphic": int(H * TAKEOVER_CHIP)}
    d, prev = {}, None
    for n, cur in enumerate(frames(picture)):
        lay = layout_at.get(n)
        if prev is not None and lay in rows and layout_at.get(n - 1) == lay:
            d[n] = change(prev, cur, rows[lay])
        prev = cur
    found = 0
    for f in joins:
        around = sorted(d[k] for k in list(range(f - QUIET, f)) + list(range(f + 1, f + 1 + QUIET)) if k in d)
        if f in d and around and d[f] > max(RATIO * around[len(around) // 2], FLOOR):
            beat = next(b.get("beat_id") or b.get("id") or "a beat" for b in beats if b["start_frame"] == f)
            print(f"JOIN  frame {f} ({f / fps:.2f} s, start of {beat}): change {d[f]:.2f} against {around[len(around) // 2]:.2f} around it. A scene spans this beat join and its picture jumps here")
            found += 1
    spikes = []
    for f, v in d.items():
        if f in named or f in joins or v < 1.0:
            continue
        near = [d[k] for k in (f - 2, f - 1, f + 1, f + 2) if k in d]
        if len(near) == 4 and v > 6 * max(max(near), 0.12):
            spikes.append((v, f))
    for v, f in sorted(spikes, reverse=True)[:12]:
        print(f"SPIKE frame {f} ({f / fps:.2f} s): change {v:.2f} stands alone and no time in the page is within a frame of it. Look at frames {f - 1} and {f}")
        found += 1
    print(f"jumps: {len(d)} frames measured, {len(joins)} beat joins inside a scene, {found} to look at" + ("" if found else ": nothing stands out"))


if __name__ == "__main__":
    main()
