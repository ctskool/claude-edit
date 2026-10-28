"""Prepare a recording for a motion-graphics recut: a split-screen short (screen on top, face cam below) or a plain
camera take (16:9 or 9:16 talking head).

Usage: python prep_source.py <video> <work_dir> [--layout auto|split|camera] [--face-top 0.575] [--no-transcribe] [--no-retime]

--layout camera (auto for any landscape video): the whole frame is the camera; face_half / face_full / face_wide are centre
crops of it. --layout split (auto for portrait video): the face cam is the region below --face-top.

Writes into <work_dir>/assets:
  face_half.mp4  face cam (bottom region of the source), 1280 wide, 30fps, no audio
  face_full.mp4  face cam center-cropped to 1080x1920 for full-frame moments, 30fps, no audio
  voice.m4a      source audio
and <work_dir>/metadata.json, <work_dir>/transcript.json (word timestamps), <work_dir>/face_map.json (retime map).

The face clips go through face_retime.py by default: 60 fps exports from OBS-style recorders can carry an irregular ~30 fps camera cadence, and a
plain fps=30 filter sometimes shows one camera frame twice and skips the next, so the face judders. face_retime picks a
unique camera frame for every 30 fps tick (same crops, sizes and frame count as before). --no-retime = the old fps=30 path.

--face-top is where the clean face cam starts, as a fraction of source height. The default
skips the seam + burned-in captions of a finished split-screen export with burned-in captions (seam ~51.7%,
two-line caption tails to ~56.8%). Use 0.52 for a raw OBS split recording without captions (rawcut.py output; seam 51.9%).

Clean camera (--camera, or automatic when <dir>/cam_cut.mp4 sits next to a rawcut <dir>/cut.mp4): the 4K camera file cut on
the same frames. The face clips then come from it instead of the split's bottom half: OBS's face crop is located inside the
camera image by template matching one frame, and face_half / face_full keep that crop's centre and aspect but extend to the
camera's top edge (all the headroom OBS cut off) at native 4K sharpness. Also writes face_wide.mp4 (the whole 16:9 camera,
1920x1080) for cut-out and wide layouts. --no-camera forces the old split-crop path.
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import profile  # noqa: E402

# Words Whisper reliably mishears in an AI / dev niche, plus the user's own (profile.json "glossary"); fed as the prompt.
GLOSSARY = ", ".join(dict.fromkeys(
    ["Claude", "Claude Code", "Anthropic", "Opus", "Sonnet", "Codex", "HyperFrames", "Remotion", "GitHub", "MCP", "GSAP",
     "JavaScript"] + [g.strip() for g in str(profile().get("glossary", "")).split(",") if g.strip()])) + "."


def run(cmd):
    print(" ".join(cmd), file=sys.stderr)
    subprocess.run(cmd, check=True)


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate:format=duration", "-of", "json", path],
                         check=True, capture_output=True, text=True).stdout
    d = json.loads(out)
    s = d["streams"][0]
    num, den = s["r_frame_rate"].split("/")
    return {"width": s["width"], "height": s["height"], "fps": float(num) / float(den),
            "duration": float(d["format"]["duration"])}


def grab(path, t, w, h):
    """One RGB frame at t seconds as a numpy array (h, w, 3)."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3)


def locate_face_crop(video, cam, meta, cmeta, top):
    """Where the split's face region (rows top..h of `video`) sits inside the camera frame: (x, y, w, h) in camera px, score.
    Multi-scale normalised cross-correlation on a quarter-size camera frame, median over three moments."""
    import cv2
    import numpy as np
    W, H, Wc, Hc = meta["width"], meta["height"], cmeta["width"], cmeta["height"]
    fw, fh = W, H - top; f = 960 / Wc; hits = []
    for t in (meta["duration"] * x for x in (0.25, 0.5, 0.75)):
        face = cv2.cvtColor(grab(video, t, W, H)[top:], cv2.COLOR_RGB2GRAY)
        small = cv2.cvtColor(cv2.resize(grab(cam, t, Wc, Hc), None, fx=f, fy=f, interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2GRAY)
        best = (-2, 0, (0, 0))
        for s in np.linspace(fh / Hc, 1.8, 90):                 # s = split px per camera px
            tw, th = round(fw * f / s), round(fh * f / s)
            if tw > small.shape[1] or th > small.shape[0]:
                continue
            res = cv2.matchTemplate(small, cv2.resize(face, (tw, th), interpolation=cv2.INTER_AREA), cv2.TM_CCOEFF_NORMED)
            _, v, _, loc = cv2.minMaxLoc(res)
            best = max(best, (v, s, loc))
        v, s, (lx, ly) = best
        hits.append((lx / f, ly / f, fw / s, fh / s, v))
    x, y, w, h, v = (float(np.median([hh[i] for hh in hits])) for i in range(5))
    return (x, y, w, h), v


def camera_crops(rect, aspect, Wc, Hc):
    """half / full / wide crop strings for the clean camera: OBS's crop centre, extended up to the camera's top edge."""
    x, y, w, h = rect
    cx, bottom = x + w / 2, min(Hc, y + h)
    ev = lambda v: int(v) // 2 * 2

    def box(ratio):
        ch = bottom; cw = ch * ratio
        if cw > Wc:
            cw = Wc; ch = cw / ratio
        cw, ch = ev(cw), ev(ch)
        return f"{cw}:{ch}:{ev(min(max(cx - cw / 2, 0), Wc - cw))}:{ev(bottom - ch)}"
    return box(aspect), box(9 / 16), f"{Wc}:{Hc}:0:0"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("work_dir")
    ap.add_argument("--layout", default="auto", choices=["auto", "split", "camera"])
    ap.add_argument("--face-top", type=float, default=0.575)
    ap.add_argument("--no-transcribe", action="store_true")
    ap.add_argument("--no-retime", action="store_true",
                    help="encode the face clips with a plain fps=30 filter (old path; can judder on 60 fps exports)")
    ap.add_argument("--camera", help="clean camera file cut on the same frames as <video> (default: cam_cut.mp4 beside a cut.mp4)")
    ap.add_argument("--no-camera", action="store_true", help="always crop the face from the split, even if cam_cut.mp4 exists")
    a = ap.parse_args()
    if not a.camera and not a.no_camera and os.path.basename(a.video) == "cut.mp4":
        guess = os.path.join(os.path.dirname(a.video), "cam_cut.mp4")
        a.camera = guess if os.path.exists(guess) else None

    assets = os.path.join(a.work_dir, "assets")
    os.makedirs(assets, exist_ok=True)
    meta = probe(a.video)
    w, h = meta["width"], meta["height"]
    top = int(h * a.face_top) // 2 * 2
    face_h = h - top
    meta.update({"source": os.path.abspath(a.video), "face_top_px": top, "face_region": [w, face_h]})

    # Half-panel face cam: full width of the face region, 1280 wide.
    half_crop = f"{w}:{face_h}:0:{top}"
    # Full-frame face cam: 9:16 center crop of the face region, 1080x1920.
    full_w = int(face_h * 9 / 16) // 2 * 2
    full_crop = f"{full_w}:{face_h}:{(w - full_w) // 2}:{top}"
    face_half, face_full = os.path.join(assets, "face_half.mp4"), os.path.join(assets, "face_full.mp4")
    layout = a.layout if a.layout != "auto" else ("camera" if w > h else "split")
    meta["layout"] = layout
    if layout == "camera":
        # the source IS the camera: same three crops as the clean-camera path, centred on the frame
        half_c, full_c, wide_c = camera_crops((0, 0, w, h), 1280 / 1092, w, h)
        if w <= h:
            wide_c = f"{w}:{w * 9 // 16 // 2 * 2}:0:{(h - w * 9 // 16) // 4 * 2}"
        meta.update({"face_top_px": 0, "face_region": [w, h], "camera_crops": {"half": half_c, "full": full_c, "wide": wide_c}})
        args = [sys.executable, os.path.join(HERE, "face_retime.py"), a.video, "--map", os.path.join(a.work_dir, "face_map.json"),
                "--crop", half_c, "--scale", "1280x-2", "--out", face_half,
                "--crop", full_c, "--scale", "1080x1920", "--out", face_full,
                "--crop", wide_c, "--scale", "1920x1080", "--out", os.path.join(assets, "face_wide.mp4")]
        run(args)
        meta["face_retime"] = "face_map.json"
    elif a.camera and not a.no_camera:
        cmeta = probe(a.camera)
        rect, score = locate_face_crop(a.video, a.camera, meta, cmeta, top)
        half_c, full_c, wide_c = camera_crops(rect, w / face_h, cmeta["width"], cmeta["height"])
        print(f"camera: split face crop found at x {rect[0]:.0f} y {rect[1]:.0f} {rect[2]:.0f}x{rect[3]:.0f} camera px "
              f"(match {score:.2f}{'  <-- WEAK, check face_half.mp4 by eye' if score < 0.6 else ''}); "
              f"half {half_c}, full {full_c}", file=sys.stderr)
        meta.update({"camera": os.path.abspath(a.camera), "camera_size": [cmeta["width"], cmeta["height"]],
                     "split_crop_in_camera": [round(v) for v in rect], "camera_match": round(score, 3),
                     "camera_crops": {"half": half_c, "full": full_c, "wide": wide_c}})
        # unique-frame detection on the face area only: over the whole room the face's motion is diluted and real camera
        # frames read as duplicates (the clip then holds frames and drifts off the cut by a tick here and there)
        args = [sys.executable, os.path.join(HERE, "face_retime.py"), a.camera, "--map", os.path.join(a.work_dir, "face_map.json"),
                "--proxy-crop", half_c,
                "--crop", half_c, "--scale", "1280x-2", "--out", face_half,
                "--crop", full_c, "--scale", "1080x1920", "--out", face_full,
                "--crop", wide_c, "--scale", "1920x1080", "--out", os.path.join(assets, "face_wide.mp4")]
        if a.no_retime:
            sys.exit("--no-retime is not supported with --camera")
        run(args)
        meta["face_retime"] = "face_map.json"
    elif a.no_retime:
        run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-an", "-vf",
             f"crop={half_crop},scale=1280:-2,fps=30", "-c:v", "libx264", "-crf", "16", "-g", "15",
             "-preset", "medium", "-pix_fmt", "yuv420p", face_half])
        run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-an", "-vf",
             f"crop={full_crop},scale=1080:1920,fps=30", "-c:v", "libx264",
             "-crf", "16", "-g", "15", "-preset", "medium", "-pix_fmt", "yuv420p", face_full])
        meta["face_retime"] = None
    else:
        # one unique-frame map for the face region, both crops encoded through it (face_retime.py)
        run([sys.executable, os.path.join(HERE, "face_retime.py"), a.video,
             "--map", os.path.join(a.work_dir, "face_map.json"),
             "--crop", half_crop, "--scale", "1280x-2", "--out", face_half,
             "--crop", full_crop, "--scale", "1080x1920", "--out", face_full])
        meta["face_retime"] = "face_map.json"
    run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-vn", "-c:a", "aac", "-b:a", "192k",
         os.path.join(assets, "voice.m4a")])

    with open(os.path.join(a.work_dir, "metadata.json"), "w") as f:
        json.dump(meta, f, indent=1)

    if not a.no_transcribe:
        wav = os.path.join(a.work_dir, "audio16k.wav")
        run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-vn", "-ac", "1", "-ar", "16000", wav])
        run([sys.executable, os.path.join(HERE, "transcribe.py"), wav,
             os.path.join(a.work_dir, "transcript.json"), "large-v3", GLOSSARY])


if __name__ == "__main__":
    main()
