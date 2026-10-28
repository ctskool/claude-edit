"""Finish a rendered style: loudness-normalise for social and make a review contact sheet.

Usage: python finish.py <render.mp4> <out.mp4> [--sheet sheet.jpg]
Two-pass EBU R128 to -14 LUFS / -2.0 dBTP limiter (lands <= -1.5 dBTP after AAC) (Instagram/TikTok/Shorts target); video stream is copied untouched.
"""
import argparse
import json
import subprocess


def loudnorm(src, dst):
    probe = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", "loudnorm=I=-14:TP=-2.0:LRA=11:print_format=json",
                            "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(probe[probe.rindex("{"):probe.rindex("}") + 1])
    af = (f"loudnorm=I=-14:TP=-2.0:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-c:v", "copy", "-af", af, "-ar", "48000", "-c:a", "aac",
                    "-b:a", "256k", "-movflags", "+faststart", dst], check=True)
    return m


def sheet(src, dst, fps=2, cols=8):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf",
                    f"fps={fps},scale=216:-2,drawtext=text='%{{pts\\:hms}}':x=4:y=4:fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.6,"
                    f"tile={cols}x12", "-frames:v", "1", dst], check=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--sheet")
    a = ap.parse_args()
    m = loudnorm(a.src, a.dst)
    print(f"input {m['input_i']} LUFS / {m['input_tp']} dBTP -> -14 LUFS")
    if a.sheet:
        sheet(a.dst, a.sheet)
