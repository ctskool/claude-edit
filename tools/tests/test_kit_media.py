#!/usr/bin/env python3
"""Pixel proof for the six-second mechanical kit copy: real face punch-in and a held clip.

python tools/tests/test_kit_media.py work/beat-first-real-punch-20261101
The copy uses a 1.08 punch from 0.8 to 2.3 s and a 3.5 s clip held through 6 s.
Nothing renders or changes the project. The inputs are decoded from its draft and real assets.
"""
import argparse, json, math, subprocess
from pathlib import Path

import numpy as np
from PIL import Image


def frame(path, t, size, vf=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(path), "-frames:v", "1"]
    if vf:
        cmd += ["-vf", vf]
    r = subprocess.run(cmd + ["-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"], capture_output=True, check=True)
    return Image.frombytes("RGB", size, r.stdout)


def psnr(a, b):
    mse = np.mean((np.asarray(a).astype(float) - np.asarray(b).astype(float)) ** 2)
    return 10 * math.log10(255 ** 2 / max(mse, 1e-12))


def verify(root):
    project = root / "v2" / "editorial"
    record = json.loads((root / "beat" / "changes" / "0001.json").read_text(encoding="utf8"))
    video = Path(record["stitched"])
    assert record["checks"]["source"] == "PASS", record["checks"]
    actual = frame(video, 1.2, (540, 960)).crop((20, 500, 520, 940))
    scores = {1.0: [], 1.08: []}
    for offset in range(-2, 3):
        base = frame(project / "assets" / "face_half.mp4", 1.2 + offset / 30, (540, 480),
                     "scale=540:480:force_original_aspect_ratio=increase,crop=540:480")
        for scale in scores:
            w, h = round(540 * scale), round(480 * scale)
            expected = base.resize((w, h), Image.Resampling.BICUBIC)
            x, y = (w - 540) // 2, (h - 480) // 2
            expected = expected.crop((x + 20, y + 20, x + 520, y + 460))
            scores[scale].append(psnr(actual, expected))
    plain, punch = max(scores[1.0]), max(scores[1.08])
    print(f"real face: expected 1.08x {punch:.2f} dB, unzoomed {plain:.2f} dB")
    assert punch > plain + 3, "the rendered face does not match the punch-in"

    held = Image.open(project / "assets" / "held" / "s01.png").convert("RGB").resize((199, 165), Image.Resampling.BICUBIC)
    after = frame(video, 4.5, (540, 960))  # after the source clip's 3.5 s end
    # The 1080px composition's plate is at (341, 130, 398, 330); allow its half-pixel edge.
    hold = max(psnr(after.crop((x + 5, 70, x + 194, 225)), held.crop((5, 5, 194, 160))) for x in (170, 171))
    print(f"real held frame at 4.5 s: {hold:.2f} dB")
    assert hold > 25, "the plate does not hold its real still after the clip ends"
    print("PASS real-media kit proof")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("work", type=Path)
    verify(p.parse_args().work.resolve())
