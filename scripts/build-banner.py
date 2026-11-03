"""Make the README banner: the title beside two phones, the raw take and the edit, playing the same seconds.

  python scripts/build-banner.py --from "C:/path/to/your/project"

Reads the before/after pair from docs/catalog.json (paths under --from, which never ship). Writes media/banner.webp.
Needs ffmpeg and Playwright's Chromium. The fonts come from the ivory kit, so the banner uses the template's own type.
"""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
W, H, SECONDS, FPS = 1400, 560, 6.0, 20
PHONE = (270, 480)
SLOTS = {"before": (700, 30), "after": (1060, 30)}  # top-left of each phone
FONTS = ROOT / "templates/ivory/build_kit/assets/fonts"

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
@font-face { font-family: Inter; font-weight: 500; src: url("FONTS/inter-latin-500-normal.woff2"); }
@font-face { font-family: Inter; font-weight: 700; src: url("FONTS/inter-latin-700-normal.woff2"); }
@font-face { font-family: Mono; font-weight: 500; src: url("FONTS/jetbrains-mono-latin-500-normal.woff2"); }
@font-face { font-family: Serif; font-style: italic; font-weight: 500; src: url("FONTS/newsreader-latin-500-italic.woff2"); }
html, body { margin: 0; width: Wpx; height: Hpx; background: #e6e7e6; color: #141516; font-family: Inter; overflow: hidden; }
.text { position: absolute; left: 64px; top: 92px; width: 600px; }
.eyebrow { font: 500 14px Mono; letter-spacing: .08em; text-transform: uppercase; color: #5a5e62; }
h1 { margin: 14px 0 0; font-weight: 700; font-size: 96px; line-height: .95; letter-spacing: -.035em; }
.line { margin: 18px 0 0; font: italic 500 34px/1.15 Serif; color: #141516; }
.flow { margin: 34px 0 0; font: 500 15px/1.6 Mono; color: #5a5e62; }
.flow b { color: #141516; font-weight: 500; border-bottom: 2px solid #ff6a3d; }
.slot { position: absolute; width: PWpx; height: PHpx; outline: 1px solid #b9bcbb; outline-offset: 0; background: #101114; }
.label { position: absolute; font: 500 12px Mono; letter-spacing: .08em; text-transform: uppercase; color: #5a5e62; }
.arrow { position: absolute; left: 994px; top: 250px; font: 500 30px Mono; color: #ff6a3d; }
</style></head><body>
<div class="text">
  <div class="eyebrow">A Claude Code skill</div>
  <h1>Claude Edit</h1>
  <p class="line">Raw take in. Your notes, at the exact second.</p>
  <p class="flow">cut listen &rarr; first edit &rarr; <b>notes</b> &rarr; note round<br>&rarr; approval &rarr; sound &rarr; final</p>
</div>
SLOTS
<div class="arrow">&rarr;</div>
</body></html>"""


def backdrop(path):
    slots = []
    for name, (x, y) in SLOTS.items():
        label = "Raw take" if name == "before" else "Claude's edit"
        slots.append(f'<div class="slot" style="left:{x}px;top:{y}px"></div><div class="label" style="left:{x}px;top:{y + PHONE[1] + 12}px">{label}</div>')
    html = (PAGE.replace("FONTS", FONTS.as_uri()).replace("SLOTS", "\n".join(slots)).replace("PWpx", f"{PHONE[0]}px")
            .replace("PHpx", f"{PHONE[1]}px").replace("Wpx", f"{W}px").replace("Hpx", f"{H}px"))
    page_file = path.with_suffix(".html")
    page_file.write_text(html, encoding="utf8")
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        page.goto(page_file.as_uri())
        page.evaluate("document.fonts.ready")
        page.screenshot(path=str(path))
        browser.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="src", required=True, type=Path)
    a = ap.parse_args()
    item = next(i for g in json.loads((ROOT / "docs/catalog.json").read_text(encoding="utf8"))["groups"] for i in g["items"] if i.get("kind") == "before-after")
    start = item.get("cardFrom", 0)
    with tempfile.TemporaryDirectory() as tmp:
        back = Path(tmp) / "back.png"
        backdrop(back)
        inputs, graph, last = ["-loop", "1", "-framerate", str(FPS), "-t", str(SECONDS), "-i", str(back)], [], "0:v"
        for n, name in enumerate(("before", "after"), start=1):
            inputs += ["-ss", str(start), "-t", str(SECONDS), "-i", str(a.src / item[name])]
            x, y = SLOTS[name]
            graph.append(f"[{n}:v]fps={FPS},scale={PHONE[0]}:{PHONE[1]}:flags=lanczos,setsar=1[v{n}]")
            graph.append(f"[{last}][v{n}]overlay={x}:{y}:shortest=1[o{n}]")
            last = f"o{n}"
        out = ROOT / "media" / "banner.webp"
        out.parent.mkdir(exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(graph), "-map", f"[{last}]",
                        "-c:v", "libwebp_anim", "-quality", "74", "-compression_level", "6", "-loop", "0", "-an", str(out)], check=True)
    print(out, f"{out.stat().st_size / 1048576:.1f} MB")


if __name__ == "__main__":
    main()
