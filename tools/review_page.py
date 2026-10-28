"""Build a local review page: per style, the donor reference vs every iteration (v1, v2, ...).

Usage: python review_page.py <id>
Reads out/<id>_<style>_<tag>.mp4 / -sheet.jpg / -gates.json and any reference sheets you added in
reference/<style>/sheets/*.jpg, writes out/<id>-review.html.
Open it in a browser (videos are linked relatively, so keep it in out/).
"""
import glob
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    vid = sys.argv[1]
    out = os.path.join(ROOT, "out")
    runs = {}
    for mp4 in glob.glob(os.path.join(out, f"{vid}_*_*.mp4")):
        m = re.match(rf"{re.escape(vid)}_(\w+)_(v\d+\w*)\.mp4$", os.path.basename(mp4))
        if m:
            runs.setdefault(m.group(1), []).append(m.group(2))
    parts = [f"<h1>{html.escape(vid)} - claude-edit review</h1>",
             "<p>Each row: donor reference sheets first, then every iteration. Gates: static seconds of the graphics band per 30 s "
             "(lower = livelier), longest static hold, loudness. Targets are in styles/CALIBRATION.md.</p>"]
    sp = os.path.join(out, f"{vid}-scores.json")
    scores = json.load(open(sp, encoding="utf-8")) if os.path.exists(sp) else {}
    for style in sorted(runs):
        sc = scores.get(style, {})
        trail = " &rarr; ".join(f"{t} <b>{v['overall']}</b>" for t, v in sc.items())
        parts.append(f"<h2>{style}</h2>" + (f"<p>Critic overall (10 = indistinguishable from the donor's editor): {trail}</p>" if trail else "") + "<div class=row>")
        for ref in sorted(glob.glob(os.path.join(ROOT, "reference", style, "sheets", "*.jpg"))):
            sheet = os.path.relpath(ref, out).replace(os.sep, "/")
            parts.append(f"<figure><figcaption>reference {html.escape(os.path.basename(ref))}</figcaption><img src='{sheet}'></figure>")
        for tag in sorted(runs[style], key=lambda t: int(re.sub(r"\D", "", t) or 0)):
            base = f"{vid}_{style}_{tag}"
            g = {}
            gp = os.path.join(out, base + "-gates.json")
            if os.path.exists(gp):
                g = json.load(open(gp))
            b = g.get("band", {})
            loud = g.get("loudness") or {}
            meta = (f"{g.get('verdict', '?')} | static/30s {b.get('static_per_30s', '?')} | longest hold {b.get('longest_hold_s', '?')}s"
                    f" | {loud.get('lufs', '?')} LUFS")
            parts.append(f"<figure><figcaption><b>{tag}</b> {html.escape(meta)}</figcaption>"
                         f"<video controls preload=metadata src='{base}.mp4'></video>"
                         f"<img src='{base}-sheet.jpg'></figure>")
        parts.append("</div>")
    page = ("<!doctype html><meta charset=utf-8><title>claude-edit review</title><style>"
            "body{font:14px system-ui;margin:24px;background:#111;color:#eee}h2{margin-top:40px}"
            ".row{display:flex;gap:16px;overflow-x:auto;align-items:flex-start}figure{margin:0;flex:0 0 auto;width:420px}"
            "figure img{width:420px;display:block;margin-top:6px}video{width:270px;display:block}"
            "figcaption{font-size:12px;color:#bbb}</style>" + "".join(parts))
    path = os.path.join(out, f"{vid}-review.html")
    open(path, "w", encoding="utf-8").write(page)
    print(path)


if __name__ == "__main__":
    main()
