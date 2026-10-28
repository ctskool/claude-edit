"""Rebuild a social post as a crisp plate (DPR 2) from its real content - for posts behind a login wall (X, Threads, ...),
where a headless capture renders blank and a signed-in browser screenshot is capped at ~800 px.

Usage: python post_card.py <spec.json> <out.png>
spec.json (read the values off the real post - in the in-app browser, signed in, with get_page_text / javascript_tool):
  {"platform": "x", "theme": "dark"|"light", "width": 600,               # CSS px; the PNG is 2x
   "author": {"name": "Kimi.ai", "handle": "@Kimi_Moonshot", "avatar": "<url or path>", "badge": "gold"|"blue"|"none"},
   "text": "Introducing Kimi K3.1 Pro ...\n\n- 1M-token context",          # exact text; \n kept; @x #y and links coloured
   "date": "11:02 AM · Oct 23, 2026",
   "media": ["<url or path>", ...],                                       # 0-4 images, as on the post; leave out an
                                                                          # image that shows numbers facts.json rules out
   "stats": {"replies": "1.2K", "reposts": "9.5K", "likes": "46K", "views": "14M"},   # optional
   "highlight": ["Open weights by Nov 4, 2026."],                         # optional: phrases to mark for zooms
   "source_url": "https://x.com/Kimi_Moonshot/status/..."}                # recorded, never drawn
Writes <out>.png and <out>.json (source_url, captured date, boxes of the header, each text line, each highlight and each
image in PNG px / 2, the same shape capture_shots.py writes) so scenes can pan / zoom to a phrase.
Remote images are downloaded once into tools/.cache/post_media/ and embedded; nothing of the viewer's own account is drawn.
"""
import base64
import datetime
import hashlib
import html
import json
import mimetypes
import os
import re
import sys
import urllib.request

from playwright.sync_api import sync_playwright

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache", "post_media")
THEMES = {"dark": dict(bg="#000000", fg="#E7E9EA", dim="#71767B", line="#2F3336", link="#1D9BF0"),
          "light": dict(bg="#FFFFFF", fg="#0F1419", dim="#536471", line="#EFF3F4", link="#1D9BF0")}
BADGE = {"gold": ("#E2B719", "#000"), "blue": ("#1D9BF0", "#fff")}
X_LOGO = ('<svg viewBox="0 0 24 24" width="22" height="22"><path fill="currentColor" d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 '
          '21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>')


def data_uri(src):
    """A local path or URL -> data: URI (URLs are cached on disk)."""
    if not src:
        return ""
    if re.match(r"https?://", src):
        os.makedirs(CACHE, exist_ok=True)
        ext = os.path.splitext(src.split("?")[0])[1] or ".jpg"
        path = os.path.join(CACHE, hashlib.sha1(src.encode()).hexdigest()[:16] + ext)
        if not os.path.exists(path):
            req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
            open(path, "wb").write(urllib.request.urlopen(req, timeout=30).read())
        src = path
    mime = mimetypes.guess_type(src)[0] or "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(open(src, "rb").read()).decode()


def rich(text, theme, highlight):
    """Escape, colour @mentions / #tags / links, mark highlight phrases, keep line breaks."""
    t = html.escape(text)
    for k, h in enumerate(highlight or []):
        t = t.replace(html.escape(h), f'<span class="hl" data-box="highlight{k}">{html.escape(h)}</span>', 1)
    t = re.sub(r"(?<![\w/])([@#][A-Za-z0-9_]+)", rf'<span style="color:{theme["link"]}">\1</span>', t)
    t = re.sub(r"(https?://[^\s<]+|\b(?:[\w-]+\.)+(?:ai|com|io|dev|org|net|co)(?:/[^\s<]*)?)", rf'<span style="color:{theme["link"]}">\1</span>', t)
    return t.replace("\n", "<br>")


def page_html(s):
    th = THEMES[s.get("theme", "dark")]; a = s["author"]; w = s.get("width", 600)
    badge = ""
    if a.get("badge", "none") in BADGE:
        c, k = BADGE[a["badge"]]
        badge = (f'<svg viewBox="0 0 22 22" width="19" height="19" style="margin-left:3px;flex:none"><path fill="{c}" d="M20.4 11c0-1.3-.8-2.4-1.9-2.9'
                 f'.4-1.2.2-2.6-.7-3.5s-2.3-1.1-3.5-.7C13.8 2.8 12.6 2 11.3 2S8.8 2.8 8.3 3.9c-1.2-.4-2.6-.2-3.5.7s-1.1 2.3-.7 3.5C2.9 8.6 2 9.7 2 11s.9 2.4 '
                 f'2.1 2.9c-.4 1.2-.2 2.6.7 3.5s2.3 1.1 3.5.7c.5 1.1 1.6 1.9 2.9 1.9s2.4-.8 2.9-1.9c1.2.4 2.6.2 3.5-.7s1.1-2.3.7-3.5c1.2-.5 2-1.6 2-2.9z"/>'
                 f'<path fill="none" stroke="{k}" stroke-width="2" d="m7.5 11.2 2.4 2.4 4.8-5"/></svg>')
    media = s.get("media") or []
    grid = ""
    if media:
        cols = 1 if len(media) == 1 else 2
        cells = "".join(f'<div class="m" data-box="media{i}"><img src="{data_uri(m)}"></div>' for i, m in enumerate(media))
        grid = f'<div class="media" style="grid-template-columns:repeat({cols},1fr)">{cells}</div>'
    st = s.get("stats") or {}
    stats = ""
    if st:
        icons = {"replies": "M1.8 10c0-4.4 3.6-8 8-8h4.4c4.5 0 8.1 3.7 8.1 8.1 0 2.9-1.6 5.6-4.1 7.1L10 21.8v-3.6H9.8c-4.4.1-8-3.5-8-8.2z",
                 "reposts": "M4.5 3.9 8.9 8 7.5 9.5 5.5 7.6V16c0 1.1.9 2 2 2H13v2H7.5c-2.2 0-4-1.8-4-4V7.6L1.5 9.5.1 8 4.5 3.9zM16.5 6H11V4h5.5c2.2 0 4 1.8 4 4v8.4l2-1.9 1.4 1.5-4.4 4.1-4.4-4.1 1.4-1.5 2 1.9V8c0-1.1-.9-2-2-2z",
                 "likes": "M16.7 3.5c-1.8-.1-3.6.8-4.7 2.4-1.1-1.6-2.9-2.5-4.7-2.4-3 .1-5.3 2.9-5.3 6 0 6.1 9.7 11.1 10 11.3.3-.2 10-5.2 10-11.3 0-3.1-2.3-5.9-5.3-6z",
                 "views": "M8.8 21H6.8V3h2v18zm-5 0h-2v-7h2v7zm10 0h-2V8h2v13zm5 0h-2v-9h2v9z"}
        stats = '<div class="stats">' + "".join(
            f'<span><svg viewBox="0 0 24 24" width="19" height="19"><path fill="none" stroke="currentColor" stroke-width="1.7" d="{icons[k]}"/></svg>{html.escape(str(st[k]))}</span>'
            for k in ("replies", "reposts", "likes", "views") if k in st) + "</div>"
    av = data_uri(a.get("avatar"))
    return f"""<!doctype html><meta charset="utf-8"><style>
html,body{{margin:0;background:{th['bg']}}}
#post{{width:{w}px;box-sizing:border-box;padding:16px 16px 6px;background:{th['bg']};color:{th['fg']};
  font-family:"Segoe UI",-apple-system,BlinkMacSystemFont,"Helvetica Neue",Arial,sans-serif;font-size:17px;line-height:1.38}}
.head{{display:flex;align-items:center;gap:10px}} .av{{width:44px;height:44px;border-radius:50%;object-fit:cover;flex:none}}
.who{{flex:1;min-width:0}} .name{{display:flex;align-items:center;font-weight:700;font-size:16px}} .handle{{color:{th['dim']};font-size:15px}}
.logo{{color:{th['fg']};opacity:.9}} .text{{margin:12px 0 0;white-space:normal;word-wrap:break-word}}
.hl{{border-radius:3px}} .media{{display:grid;gap:2px;margin-top:12px;border-radius:16px;overflow:hidden;border:1px solid {th['line']}}}
.m img{{display:block;width:100%;height:100%;object-fit:cover;max-height:520px}}
.date{{color:{th['dim']};font-size:15px;margin:14px 0 0;padding-bottom:12px;border-bottom:1px solid {th['line']}}}
.stats{{display:flex;justify-content:space-between;color:{th['dim']};font-size:13px;padding:10px 4px}}
.stats span{{display:flex;align-items:center;gap:5px}}
</style><div id="post"><div class="head" data-box="header">{f'<img class="av" src="{av}">' if av else ''}
<div class="who"><div class="name">{html.escape(a['name'])}{badge}</div><div class="handle">{html.escape(a['handle'])}</div></div>
<div class="logo">{X_LOGO if s.get('platform', 'x') == 'x' else ''}</div></div>
<div class="text" data-box="text">{rich(s['text'], th, s.get('highlight'))}</div>{grid}
<div class="date">{html.escape(s.get('date', ''))}</div>{stats}</div>"""


BOXES = """() => {
  const P = document.getElementById('post').getBoundingClientRect(), out = [];
  const add = (kind, r, text) => out.push({kind, text: (text || '').slice(0, 120), x: Math.round(r.left - P.left), y: Math.round(r.top - P.top),
                                          w: Math.round(r.width), h: Math.round(r.height)});
  document.querySelectorAll('[data-box]').forEach(el => add(el.dataset.box, el.getBoundingClientRect(), el.innerText));
  // one box per rendered line of the post text
  const t = document.querySelector('.text'), rg = document.createRange(); rg.selectNodeContents(t);
  const lines = {}; for (const r of rg.getClientRects()) { const k = Math.round(r.top); lines[k] = lines[k] ? [Math.min(lines[k][0], r.left), Math.max(lines[k][1], r.right), r.top, r.height] : [r.left, r.right, r.top, r.height]; }
  Object.values(lines).forEach((l, i) => add('line' + i, {left: l[0], top: l[2], width: l[1] - l[0], height: l[3]}, ''));
  return out;
}"""


def main():
    spec_path, out = sys.argv[1], sys.argv[2]
    s = json.load(open(spec_path, encoding="utf-8"))
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": s.get("width", 600) + 40, "height": 400}, device_scale_factor=2,
                            color_scheme=s.get("theme", "dark"))
        page = ctx.new_page()
        page.set_content(page_html(s), wait_until="load")
        page.wait_for_timeout(300)
        page.locator("#post").screenshot(path=out)
        boxes = page.evaluate(BOXES)
        b.close()
    json.dump({"source_url": s.get("source_url"), "rebuilt": True, "captured": datetime.date.today().isoformat(), "dpr": 2,
               "platform": s.get("platform", "x"), "boxes": boxes}, open(out[:-4] + ".json", "w", encoding="utf-8"), indent=1)
    print("ok", out)


if __name__ == "__main__":
    main()
