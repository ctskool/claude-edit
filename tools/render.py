"""Render HyperFrames projects one after another (never in parallel), then finish, gate and package each.

Usage:
  python tools/render.py one <project_dir> <out_basename> [--quality draft|standard|high|looks] [--pack <style>]
      -> out/<out_basename>.mp4, out/<out_basename>-sheet.jpg, out/<out_basename>-gates.json; prints one JSON line
  python tools/render.py styles <id> <projects_dir> <tag> <style> [<style> ...]
      per style: `one` (quality looks) -> critic evidence pack out/evidence/<id>_<style>_<tag>/ -> phone copy
      out/preview/<id>_<style>_<tag>_preview.mp4 (< 30 MB for a ~50 s short) -> rebuilds out/<id>-review.html

Replaces the old render_one.sh / render_styles.sh so the same command works on Windows and macOS.
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import ROOT, utf8_env  # noqa: E402

OUT = os.path.join(ROOT, "out")


def one(proj, base, quality="draft", pack=None):
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(proj, "renders"), exist_ok=True)
    raw = os.path.join(proj, "renders", base + ".mp4")
    log = os.path.join(proj, "renders", base + ".log")
    t0 = time.time()
    with open(log, "w", encoding="utf-8", errors="replace") as lf:
        rc = subprocess.run(f'npx hyperframes render --quality {quality} -o "renders/{base}.mp4"', cwd=proj, shell=True,
                            stdout=lf, stderr=subprocess.STDOUT, env=utf8_env()).returncode
    secs = round(time.time() - t0)
    if rc or not os.path.exists(raw):
        tail = open(log, encoding="utf-8", errors="replace").read().splitlines()[-15:]
        print("\n".join(tail), file=sys.stderr)
        print(json.dumps({"ok": False, "render_seconds": secs, "log": log}))
        return None
    mp4, sheet, gates = (os.path.join(OUT, base + x) for x in (".mp4", "-sheet.jpg", "-gates.json"))
    subprocess.run([sys.executable, os.path.join(HERE, "finish.py"), raw, mp4, "--sheet", sheet], check=True,
                   stdout=sys.stderr)
    g = subprocess.run([sys.executable, os.path.join(HERE, "gates.py"), mp4, "--band", "0,0,1080,900", "--json", gates]
                       + (["--pack", pack] if pack else []), stdout=subprocess.DEVNULL)
    if g.returncode not in (0, 1, 2) or not os.path.exists(gates):      # 0/1/2 = PASS / PASS_WITH_WARNINGS / FAIL verdict
        print(json.dumps({"ok": False, "render_seconds": secs, "error": "gates.py crashed", "video": mp4}))
        return None
    d = json.load(open(gates, encoding="utf-8"))
    b = d["band"]
    res = {"ok": True, "render_seconds": secs, "video": mp4, "sheet": sheet, "verdict": d["verdict"],
           "static_per_30s": b["static_per_30s"], "longest_hold_s": b["longest_hold_s"], "loudness": d.get("loudness"),
           "findings": [f["msg"] for f in d["findings"]]}
    print(json.dumps(res))
    return res


def styles(vid, projects, tag, names):
    for s in names:
        print(f"=== {s} ({tag}) start {time.strftime('%H:%M:%S')}", file=sys.stderr)
        base = f"{vid}_{s}_{tag}"
        if not one(os.path.join(projects, s), base, "looks", s):
            print(f"!!! render failed for {s}", file=sys.stderr)
            continue
        mp4 = os.path.join(OUT, base + ".mp4")
        subprocess.run([sys.executable, os.path.join(HERE, "evidence.py"), mp4, os.path.join(OUT, "evidence", base)],
                       stdout=subprocess.DEVNULL)
        os.makedirs(os.path.join(OUT, "preview"), exist_ok=True)
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", mp4, "-c:v", "libx264", "-preset", "slow",
                        "-b:v", "3800k", "-maxrate", "4500k", "-bufsize", "8000k", "-pix_fmt", "yuv420p", "-c:a", "aac",
                        "-b:a", "128k", "-movflags", "+faststart", os.path.join(OUT, "preview", base + "_preview.mp4")])
        print(f"=== {s} done {time.strftime('%H:%M:%S')}", file=sys.stderr)
    subprocess.run([sys.executable, os.path.join(HERE, "review_page.py"), vid])


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("one")
    o.add_argument("project"); o.add_argument("base")
    o.add_argument("--quality", default="draft"); o.add_argument("--pack")
    st = sub.add_parser("styles")
    st.add_argument("id"); st.add_argument("projects"); st.add_argument("tag"); st.add_argument("styles", nargs="+")
    a = ap.parse_args()
    if a.cmd == "one":
        sys.exit(0 if one(os.path.abspath(a.project), a.base, a.quality, a.pack) else 1)
    styles(a.id, os.path.abspath(a.projects), a.tag, a.styles)


if __name__ == "__main__":
    main()
