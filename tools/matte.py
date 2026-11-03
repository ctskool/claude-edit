"""GPU person cut-out (transparent WebM) with Robust Video Matting - the fast replacement for tools/cutout.sh.

Usage (needs the matting venv, not the system Python):
  python tools/matte.py <in.mp4> <out.webm> [--model resnet50|mobilenetv3] [--ratio auto]
                                            [--rgb fgr|src] [--alpha <alpha.mp4>] [--batch 8]

Output is VP9 + alpha (yuva420p), same size / frame rate / frame count as the input, so it lines up frame for frame
with the clip it was made from (e.g. work/<id>/assets/face_half.mp4 -> face_cut.webm).

Why RVM and not `hyperframes remove-background`: on this Windows box HyperFrames only has a CPU provider (u2net,
~1.8 s/frame, ~50 min per 48 s) and u2net mattes every frame on its own, so edges shimmer. RVM is a video model with
recurrent state (temporally steady edges, hair) and runs on the RTX 5090 in fp16.

--ratio   downsample ratio for the backbone pass; auto keeps the long side near 512 px (RVM's recommended range).
--rgb fgr uses RVM's colour-decontaminated foreground (best over a different background); src keeps the source RGB.
--alpha   also write the alpha matte as a grayscale mp4 for QA.

Setup (once, activated environment): python -m pip install torch torchvision numpy. For optional NVIDIA acceleration,
choose the CUDA wheel command at https://pytorch.org/get-started/locally/. Code: vendor/RobustVideoMatting (GPL-3.0, PeterL1n),
weights: vendor/rvm-weights/rvm_<model>.pth from its v1.0.0 release.
"""
import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import time

import numpy as np
import torch

from paths import project_root
ROOT = str(project_root())
sys.path.insert(0, os.path.join(ROOT, "vendor", "RobustVideoMatting"))
from model import MattingNetwork  # noqa: E402


def probe(path):
    s = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=width,height,r_frame_rate", "-of", "json", path],
                                  check=True, capture_output=True, text=True).stdout)["streams"][0]
    return s["width"], s["height"], s["r_frame_rate"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--model", default="resnet50", choices=["resnet50", "mobilenetv3"])
    ap.add_argument("--ratio", default="auto")
    ap.add_argument("--rgb", default="fgr", choices=["fgr", "src"])
    ap.add_argument("--alpha")
    ap.add_argument("--batch", type=int, default=8)
    a = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    if device == "cpu":
        print("WARN popout matting on CPU is slow; use split if unsuitable", file=sys.stderr)

    w, h, fps = probe(a.input)
    ratio = min(1.0, 512 / max(w, h)) if a.ratio == "auto" else float(a.ratio)
    net = MattingNetwork(a.model).eval().to(device)
    net.load_state_dict(torch.load(os.path.join(ROOT, "vendor", "rvm-weights", f"rvm_{a.model}.pth"),
                                   map_location=device, weights_only=True))
    net = net.to(dtype=dtype)

    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", a.input, "-fps_mode", "passthrough", "-f", "rawvideo",
                            "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{w}x{h}",
                            # realtime/cpu-used 8: 2.4x faster than good/4 at the same PSNR (benchmarked on 1280x1092 alpha)
                            "-r", fps, "-i", "-", "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-crf", "16", "-b:v", "0",
                            "-deadline", "realtime", "-cpu-used", "8", "-row-mt", "1", "-tile-columns", "2", "-threads", "16",
                            "-auto-alt-ref", "0", a.output],
                           stdin=subprocess.PIPE)
    aenc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{w}x{h}",
                             "-r", fps, "-i", "-", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", a.alpha],
                            stdin=subprocess.PIPE) if a.alpha else None

    q = queue.Queue(maxsize=4)                                        # encoder runs on its own thread (it is the bottleneck)

    def writer():
        while (out := q.get()) is not None:
            enc.stdin.write(out.tobytes())
            if aenc:
                aenc.stdin.write(out[..., 3].tobytes())

    wt = threading.Thread(target=writer); wt.start()
    fsz = w * h * 3; rec = [None] * 4; n = 0; t0 = time.time(); infer = 0.0
    with torch.inference_mode():
        while True:
            buf = bytearray(dec.stdout.read(fsz * a.batch))
            k = len(buf) // fsz
            if k == 0:
                break
            src = np.frombuffer(buf, np.uint8, k * fsz).reshape(k, h, w, 3)
            x = torch.from_numpy(src).to(device=device, dtype=dtype).permute(0, 3, 1, 2).div(255).unsqueeze(0)   # [1, T, 3, H, W]
            ti = time.time()
            fgr, pha, *rec = net(x, *rec, downsample_ratio=ratio)
            rgb = (fgr if a.rgb == "fgr" else x)[0]
            out = torch.cat([rgb, pha[0]], 1).mul(255).round().byte().permute(0, 2, 3, 1).contiguous().cpu().numpy()
            infer += time.time() - ti
            q.put(out)
            n += k
    q.put(None); wt.join()
    for p in (enc, aenc):
        if p:
            p.stdin.close(); p.wait()
    dec.wait()
    total = time.time() - t0
    print(f"matte: {n} frames {w}x{h} ({a.model}, ratio {ratio:.3f}, fp16) in {total:.1f}s = {n / total:.1f} fps overall, "
          f"{n / max(infer, 1e-6):.0f} fps on the GPU -> {a.output}")


if __name__ == "__main__":
    main()
