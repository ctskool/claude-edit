"""Capture crisp web screenshots (DPR 2) for motion-graphics plates.

Usage: python capture_shots.py <out_dir> <spec.json>
spec.json: [{"name", "url", "theme": "light"|"dark", "width": 1280, "height": 800,
             "full_page": bool, "element": css selector (optional), "hide": [css selectors]}]
For every shot it also writes <name>.json with the page-space boxes of headings, images and
badges, so scenes can pan/zoom to "the section being talked about" without guessing.
"""
import json
import os
import sys

from playwright.sync_api import sync_playwright

BOXES_JS = """(root) => {
  const scope = root || document;
  const out = [];
  for (const el of scope.querySelectorAll('h1,h2,h3,img,pre,table,a.Link--muted,[data-testid],strong')) {
    const r = el.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) continue;
    const ox = root ? root.getBoundingClientRect().left : -window.scrollX;
    const oy = root ? root.getBoundingClientRect().top : -window.scrollY;
    out.push({tag: el.tagName.toLowerCase(), text: (el.innerText || el.alt || '').trim().slice(0, 80),
              x: Math.round(r.left - ox), y: Math.round(r.top - oy), w: Math.round(r.width), h: Math.round(r.height)});
  }
  return out;
}"""

# Sites whose content sits behind a sign-in for a fresh headless browser. A shot of one that comes back as a wall is
# flagged (not silently kept): get it through the signed-in in-app browser instead - posts via tools/post_card.py.
WALLED = ("x.com", "twitter.com", "linkedin.com", "instagram.com", "threads.net", "facebook.com", "tiktok.com", "reddit.com")
WALL_JS = """() => { const t = (document.body ? document.body.innerText : '').trim();
  const prompt = /(sign in|log in|sign up|join now|create (an )?account|don.t miss what.s happening)/i.test(t.slice(0, 3000));
  return {chars: t.length, prompt}; }"""


def login_wall(url, page):
    host = url.split("/")[2].lower() if "://" in url else ""
    walled = any(host == h or host.endswith("." + h) for h in WALLED)
    w = page.evaluate(WALL_JS)
    return (walled and (w["chars"] < 600 or w["prompt"])) or (w["chars"] < 80)


def main():
    out_dir, spec_path = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    spec = json.load(open(spec_path, encoding="utf-8"))
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for s in spec:
            ctx = browser.new_context(viewport={"width": s.get("width", 1280), "height": s.get("height", 800)},
                                      device_scale_factor=2, color_scheme=s.get("theme", "light"))
            page = ctx.new_page()
            page.goto(s["url"], wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(1500)
            if s.get("hide"):
                page.add_style_tag(content=",".join(s["hide"]) + "{display:none !important}")
            png = os.path.join(out_dir, s["name"] + ".png")
            if s.get("element"):
                el = page.locator(s["element"]).first
                el.screenshot(path=png)
                boxes = el.evaluate(BOXES_JS)
            else:
                page.screenshot(path=png, full_page=s.get("full_page", False))
                boxes = page.evaluate(BOXES_JS, None)
            wall = login_wall(s["url"], page)
            json.dump({"url": s["url"], "dpr": 2, "boxes": boxes, "login_wall": wall}, open(png[:-4] + ".json", "w", encoding="utf-8"), indent=1)
            print(("WALL " if wall else "ok ") + s["name"] + (" - a sign-in wall, not the page: capture it through the signed-in in-app "
                                                            "browser (posts: tools/post_card.py), or use a frame of your own recording" if wall else ""))
            ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
