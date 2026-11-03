"""Scene markup. All coordinates are frame px (1080x1920). Geometry is from plan.json.

The helpers come from templates/ivory/build_kit. Scenes go at the end, in build(). Each is one element wrapped by own(), and its root is <div id="sc-x" class="scene">.
"""
import json
import math
import struct
import subprocess
from pathlib import Path

from common import frame_of

ED = Path(__file__).resolve().parent.parent
A = ED / "assets"
SIZES = {}  # id -> (natW, natH, rect) for the JS mapper
_sizes = {}


def nat(src):
    """Natural size of an asset: a PNG from its header, anything else from ffprobe."""
    if src not in _sizes:
        path = A / src
        if path.suffix.lower() == ".png":
            _sizes[src] = struct.unpack(">II", path.read_bytes()[16:24])
        else:
            r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", str(path)], capture_output=True, text=True, check=True)
            s = json.loads(r.stdout)["streams"][0]
            _sizes[src] = (s["width"], s["height"])
    return _sizes[src]


def imgstyle(src, rect, box):
    W, H = nat(src)
    rx, ry, rw, rh = rect
    sx, sy = box[2] / rw, box[3] / rh
    return f"left:{-rx * sx:.2f}px;top:{-ry * sy:.2f}px;width:{W * sx:.2f}px;height:{H * sy:.2f}px"


def boxstyle(b):
    return f"left:{b[0]}px;top:{b[1]}px;width:{b[2]}px;height:{b[3]}px"


def img(id_, src, rect, box, style=""):
    return f'<img id="{id_}" src="assets/{src}" alt="" style="{imgstyle(src, rect, box)};{style}">'


_track = [2]


def vid(id_, src, rect, box, start, dur, media):
    """start snaps to its frame, floored, so the clip is up on the switch frame and never one frame late"""
    _track[0] += 1
    f0 = frame_of(start, 30)
    start = math.floor(f0 / 30 * 1e5) / 1e5
    return (f'<video id="{id_}" class="clip" src="assets/{src}" muted playsinline data-start="{start}" data-duration="{dur}" data-media-start="{media}" '
            f'data-track-index="{_track[0]}" style="{imgstyle(src, rect, box)}"></video>')


def plate(id_, src, rect, box, cls="", style="", extra=""):
    """A capture window: .plate (window) > .pin (push / zoom) > img"""
    SIZES[id_] = (*nat(src), list(rect))
    return (f'<div id="{id_}" class="plate {cls}" style="{boxstyle(box)};{style}"><div id="{id_}-p" class="pin">'
            f'{img(id_ + "-i", src, rect, box)}{extra}</div></div>')


def vplate(id_, stills, src, rect, box, start, dur, media, extra=""):
    """A clip window. stills: [(id, png, style)], held frames sized like the clip, under the video"""
    inner = "".join(f'<img id="{i}" src="assets/{p}" alt="" style="{imgstyle(src, rect, box)};{s}">' for i, p, s in stills)
    return (f'<div id="{id_}" class="plate" style="{boxstyle(box)}"><div id="{id_}-p" class="pin">{inner}'
            f'{vid(id_ + "-v", src, rect, box, start, dur, media)}{extra}</div></div>')


def card(id_, b, style=""):
    return f'<div id="{id_}" class="pc" style="{boxstyle(b)};{style}"></div>'


def ol(id_, b, cls=""):
    return f'<div id="{id_}" class="ol {cls}" style="{boxstyle(b)}"></div>'


def map_box(rect, box, sub):
    """sub = (x,y,w,h) in rect's px -> frame box"""
    sx, sy = box[2] / rect[2], box[3] / rect[3]
    return [round(box[0] + (sub[0] - rect[0]) * sx, 1), round(box[1] + (sub[1] - rect[1]) * sy, 1), round(sub[2] * sx, 1), round(sub[3] * sy, 1)]


def drawn(id_, b, r=22):
    """a 3 px clay outline that draws round a box"""
    return (f'<svg id="{id_}" class="abs" style="{boxstyle(b)};overflow:visible;opacity:0"><rect id="{id_}-r" x="0" y="0" width="{b[2]}" height="{b[3]}" rx="{r}" ry="{r}" '
            f'fill="none" stroke="#d97757" stroke-width="3" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1"/></svg>')


def use(sym, cls="ic", style=""):
    return f'<svg class="{cls}" style="{style}"><use href="#{sym}"/></svg>'


def title(id_, top, size, pre, word, post):
    spans = []
    if pre:
        spans.append(f'<span id="{id_}-1">{pre}</span>')
    spans.append(f'<span id="{id_}-2" class="it">{word}</span>')
    if post:
        spans.append(f'<span id="{id_}-3">{post}</span>')
    return f'<div id="{id_}" class="serif" style="top:{top}px;height:{size}px;font-size:{size}px">{"".join(spans)}</div>'


def lbl(id_, x, y, txt, size, style=""):
    return f'<div id="{id_}" class="lbl" style="left:{x}px;top:{y}px;font-size:{size}px;{style}">{txt}</div>'


def own(id_, html):
    """One scene group, marked for tools/beat_render/ownership.py"""
    return f"<!--@own scene.{id_}-->\n{html}\n<!--@/own-->"


def inpin(box, tx, ty, s, f):
    """A frame-px box at rest, as a box inside a pin pushed by (tx, ty, s) with origin 0 0"""
    return [round((f[0] - box[0] - tx) / s, 2), round((f[1] - box[1] - ty) / s, 2), round(f[2] / s, 2), round(f[3] / s, 2)]


def mark(id_, b, cls="mkr", extra=""):
    """A marker tint or a strike line. Starts hidden, wipes on from the left"""
    return f'<div id="{id_}" class="{cls}" style="{boxstyle(b)};{extra}"></div>'


def serif_lines(id_, size, rows, mid=450):
    """Quiet panel: one serif line in centred rows, in a wrapper so the copy bind reads the whole line. rows: [[(words, italic), ...], ...]"""
    step = round(size * 1.16)
    height = size + step * (len(rows) - 1)
    out, n = [], 0
    for r, row in enumerate(rows):
        spans = []
        for text, it in row:
            n += 1
            cls = ' class="it"' if it else ""
            spans.append(f'<span id="{id_}-{n}"{cls}>{text}</span>')
        out.append(f'<div class="serif" style="top:{step * r}px;height:{size}px;font-size:{size}px">{"".join(spans)}</div>')
    return f'<div id="{id_}" class="abs" style="left:0;top:{round(mid - height / 2)}px;width:1080px;height:{height}px">{"".join(out)}</div>'


def quiet(name, size, rows):
    return own(f"sc-{name}", f"""<div id="sc-{name}" class="scene">{serif_lines(name + "-t", size, rows)}</div>""")


def build():
    S = []
    POST = "posts/claude-post-tight-light.png"
    OVER = "posts/overell-post-tight-light.png"
    HERO = "posts/post-hero-cards.png"
    PLANS = "shots/pricing-plans-light.png"
    FOOT = "shots/pricing-footnote-light.png"

    # ---- b01-b02 hook: rebuilt post card. Window fixed, the pin pushes. Overlays sit in the pin so they travel with it
    HB = (90, 286, 900, 337)
    HP = (-36, -468.67, 2.3)
    hk = (mark("hk-s", inpin(HB, *HP, (121.5, 505.5, 297.0, 6.0)), "sk") + mark("hk-a", inpin(HB, *HP, (427.5, 470.2, 69.8, 76.4)), extra="border-radius:2.6px")
          + mark("hk-u", inpin(HB, *HP, (513.0, 465.7, 168.8, 85.4)), extra="border-radius:2.6px"))
    S.append(own("sc-hook", f"""<div id="sc-hook" class="scene">
  {card("hk-card", (72, 268, 936, 372))}
  {plate("hk-pl", POST, (0, 0, 920, 344), HB, "o0 w", extra=hk)}
</div>"""))

    # ---- b03 his own recording: first frame held, then 1x
    S.append(own("sc-title", f"""<div id="sc-title" class="scene"><div id="ti-g" class="fill">
  {card("ti-card", (72, 212, 936, 467))}
  {vplate("ti-pl", [("ti-h", "held/title-highlight-first.png", "")], "clips/title-highlight.mp4", (0, 0, 960, 460), (90, 230, 900, 431), 5.30, 2.2, 0)}
</div></div>"""))

    # ---- b04-b05 before-after: two pills struck, then the post's own art
    def pill(id_, y, text, strike):
        return (f'<div id="{id_}" class="pillw" style="left:190px;top:{y}px;width:700px;height:160px;border-radius:22px;font-size:84px">'
                f'<span id="{id_}t" class="stw">{text}<i id="{strike}" class="sk" style="left:-12px;right:-12px;top:42px;height:6px"></i></span></div>')
    S.append(own("sc-names", f"""<div id="sc-names" class="scene full">
  {pill("nm-a", 530, "Max 5x", "nm-sa")}
  {pill("nm-b", 750, "Max 20x", "nm-sb")}
  <div id="nm-art" class="fill" style="opacity:0">
    {card("nm-card", (72, 505, 936, 590))}
    {plate("nm-m", HERO, (1198, 47, 692, 1128), (90, 523, 340, 554), "w", "border-radius:12px 0 0 12px")}
    {plate("nm-u", HERO, (1888, 47, 1142, 1128), (429, 523, 561, 554), "w", "border-radius:0 12px 12px 0;opacity:0")}
  </div>
</div>"""))

    # ---- b06-b07 the same post card on its lower strip
    WB = (90, 377, 900, 137)
    WP = (-28.02, -28.02, 1.7899)
    S.append(own("sc-week", f"""<div id="sc-week" class="scene"><div id="wk-g" class="fill">
  {card("wk-card", (72, 359, 936, 173))}
  {plate("wk-pl", POST, (0, 760, 920, 140), WB, "o0 w", extra=mark("wk-m", inpin(WB, *WP, (112.8, 429.6, 873.7, 73.6)), extra="border-radius:3.35px"))}
</div></div>"""))

    # ---- b08-b09 real plan card, real row, real footnote
    UB = (90, 1222, 900, 83)
    S.append(own("sc-ultra", f"""<div id="sc-ultra" class="scene full">
  <div id="ul-c1" class="fill">
    {card("ul-card", (72, 327, 936, 806))}
    {plate("ul-pl", PLANS, (1396, 160, 1216, 1040), (90, 345, 900, 770), "w")}
    {drawn("ul-o", (167.0, 638.2, 251.6, 97.7), 12)}
  </div>
  <div id="ul-c2" class="fill" style="opacity:0">
    {card("ul-card2", (72, 956, 936, 234))}
    {plate("ul-p2", PLANS, (1396, 1720, 1216, 268), (90, 974, 900, 198), "w")}
  </div>
  <div id="ul-c3" class="fill" style="opacity:0">
    {card("ul-card3", (72, 1204, 936, 119))}
    {plate("ul-p3", FOOT, (0, 0, 1176, 108), UB, "w", extra=mark("ul-m", inpin(UB, 0, 0, 1, (552.2, 1243.5, 381.1, 52.3)), extra="border-radius:6px"))}
  </div>
</div>"""))

    # ---- b10 quiet panel
    CB = (90, 218, 900, 399)
    # ---- b10 Chase's note: OpenAI's doc arrives early, same card and box as b11, so the join holds still. An outline draws on better
    S.append(own("sc-q10", f"""<div id="sc-q10" class="scene"><div id="q10-g" class="fill">
  {card("q10-card", (72, 200, 936, 435))}
  {plate("q10-pl", "shots/codex-pricing-light.png", (0, 0, 812, 360), CB, "w")}
  {drawn("q10-o", (72, 200, 936, 435), 22)}
</div></div>"""))

    # ---- b11-b12 OpenAI's paragraph. The whole card takes the slow push: this plate has no side padding, so a push on the pin would clip its first letters
    S.append(own("sc-codex", f"""<div id="sc-codex" class="scene"><div id="cx-g" class="fill">
  {card("cx-card", (72, 200, 936, 435))}
  {plate("cx-pl", "shots/codex-pricing-light.png", (0, 0, 812, 360), CB, "w", extra=mark("cx-m0", inpin(CB, 0, 0, 1, (706.3, 284.5, 151.8, 42.1)), extra="border-radius:6px") + mark("cx-m1", inpin(CB, 0, 0, 1, (90.0, 342.1, 512.1, 42.1)), extra="border-radius:6px"))}
  <div id="cx-s" class="src" style="left:72px;top:655px;width:936px;text-align:center;font-size:26px;opacity:0">Codex pricing doc, learn.chatgpt.com/docs/pricing</div>
</div></div>"""))

    # ---- b13 Chase's note: the Codex line stays up and Claude's own help page lands under it
    AR, AB = (0, 46, 812, 120), (90, 200, 900, 133)
    BR, BB = (20, 160, 1330, 205), (90, 442, 900, 139)
    S.append(own("sc-q13", f"""<div id="sc-q13" class="scene"><div id="q13-g" class="fill">
  {card("q13-card-a", (72, 140, 936, 218))}
  <div id="q13-la" class="src" style="left:90px;top:158px;font-size:26px">Codex pricing doc</div>
  {plate("q13-pa", "shots/codex-pricing-light.png", AR, AB, "w", extra=mark("q13-m0", inpin(AB, 0, 0, 1, map_box(AR, AB, (556, 60, 137, 38))), extra="border-radius:6px") + mark("q13-m1", inpin(AB, 0, 0, 1, map_box(AR, AB, (0, 112, 462, 38))), extra="border-radius:6px"))}
  <div id="q13-b" class="fill" style="opacity:0">
    {card("q13-card-b", (72, 382, 936, 230))}
    <div id="q13-lb" class="src" style="left:90px;top:400px;font-size:26px">Claude Code help page</div>
    {plate("q13-pb", "shots/claude-code-support.png", BR, BB, "w", extra=mark("q13-m2", inpin(BB, 0, 0, 1, map_box(BR, BB, (875, 236, 285, 50))), extra="border-radius:6px") + mark("q13-m3", inpin(BB, 0, 0, 1, map_box(BR, BB, (22, 305, 945, 50))), extra="border-radius:6px"))}
  </div>
</div></div>"""))

    # ---- b14-b16 list card: three empty sockets, a verbatim post crop and a check land on each item
    def row(i, y, rect, box):
        return (f'<div class="lsock" style="left:102px;top:{y - 42}px"></div>'
                f'<svg id="ls-c{i}" class="abs" viewBox="0 0 84 84" style="left:102px;top:{y - 42}px;width:84px;height:84px;opacity:0"><path d="M23 44 L37 58 L62 28" fill="none" stroke="#2e9e5b" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
                f'<div id="ls-b{i}" class="skel" style="left:206px;top:{y - 14}px;width:560px;height:28px"></div>'
                + plate(f"ls-r{i}", POST, rect, box, "w", "border-radius:0;opacity:0"))
    S.append(own("sc-list", f"""<div id="sc-list" class="scene full">
  {card("ls-card", (72, 400, 936, 660))}
  <div class="abs" style="left:102px;top:620px;width:876px;height:1px;background:#e4e2da"></div>
  <div class="abs" style="left:102px;top:840px;width:876px;height:1px;background:#e4e2da"></div>
  {row(0, 510, (28, 524, 832, 92), (206, 466.7, 784.0, 86.7))}
  {row(1, 730, (28, 804, 500, 46), (206, 708.3, 471.2, 43.3))}
  {row(2, 950, (28, 284, 252, 44), (206, 929.3, 237.5, 41.5))}
</div>"""))

    # ---- b17 his own selection, first frame held
    S.append(own("sc-max20", f"""<div id="sc-max20" class="scene"><div id="mx-g" class="fill">
  {card("mx-card", (72, 212, 936, 467))}
  {vplate("mx-pl", [("mx-h", "held/max20x-highlight-first.png", "")], "clips/max20x-highlight.mp4", (0, 0, 960, 460), (90, 230, 900, 431), 31.40, 1.567, 0)}
</div></div>"""))

    # ---- b18-b19 the assumed math, struck, then his drag. 4x is never up without the label, and from 34.30 never without the strike
    def eqpill(id_, x, text):
        return f'<div id="{id_}" class="pillw" style="left:{x}px;top:470px;width:340px;height:120px;border-radius:18px;font-size:60px">{text}</div>'
    S.append(own("sc-four", f"""<div id="sc-four" class="scene full">
  <div id="fr-c" class="fill">
    {card("fr-card", (72, 360, 936, 740))}
    <div id="fr-l" class="t" style="left:72px;top:405px;width:936px;text-align:center;font-family:var(--mono);font-weight:500;font-size:30px;letter-spacing:.14em;color:var(--mut)">THE ASSUMED MATH</div>
    {eqpill("fr-pa", 130, "Max 20x")}
    <div id="fr-dv" class="t" style="left:470px;top:482px;width:140px;text-align:center;font-family:var(--serif);font-weight:500;font-size:96px">÷</div>
    {eqpill("fr-pb", 610, "Max 5x")}
    <div id="fr-row" class="abs" style="left:72px;top:640px;width:936px;height:260px;display:flex;justify-content:center;align-items:baseline;gap:40px;font-family:var(--serif);font-weight:500;line-height:1;color:var(--ink);opacity:0">
      <span id="fr-eq" style="position:relative;top:-34px;font-size:200px">=</span>
      <span id="fr-fig" class="stw" style="font-size:260px;letter-spacing:-.02em">4x<i id="fr-st" class="sk" style="left:-24px;right:-24px;top:107px;height:8px"></i></span>
    </div>
    <div id="fr-s" class="src" style="left:72px;top:990px;width:936px;text-align:center;font-size:28px">From the plan names, not a usage figure</div>
  </div>
  <div id="fr-cg" class="fill" style="opacity:0">
    {card("fr-clc", (72, 690, 936, 467))}
    {vplate("fr-pl", [("fr-h", "held/drag-select-max5x-first.png", "")], "clips/drag-select-max5x.mp4", (0, 0, 960, 460), (90, 708, 900, 431), 34.633, 1.984, 0)}
  </div>
</div>"""))

    # ---- b20-b21 rebuilt Overell post
    OB = (90, 168, 900, 513)
    def okm(id_, f):
        return mark(id_, inpin(OB, 0, 0, 1, f), extra="border-radius:6px")
    S.append(own("sc-over", f"""<div id="sc-over" class="scene"><div id="ov-g" class="fill">
  {card("ov-card", (72, 150, 936, 549))}
  {plate("ov-pl", OVER, (0, 0, 920, 524), OB, "w", extra=okm("ov-m0", (422.6, 498.9, 376.6, 41.1)) + okm("ov-m1", (893.2, 451.9, 21.5, 41.1)) + okm("ov-m2", (119.3, 498.9, 296.4, 41.1)))}
</div></div>"""))

    # ---- b22 real compare table
    S.append(own("sc-table", f"""<div id="sc-table" class="scene full">
  {card("tb-card", (72, 292, 936, 793))}
  {plate("tb-pl", "shots/pricing-compare-light.png", (0, 0, 1224, 796), (90, 310, 900, 585), "w")}
  <div id="tb-row" class="abs" style="left:90px;top:685.3px;width:900px;height:209.7px;background:rgba(217,119,87,.14);border-radius:0 0 12px 12px;transform-origin:0 50%;opacity:0"></div>
  {ol("tb-o0", (612.8, 811.1, 79.4, 57.4), "bare")}
  {ol("tb-o1", (831.2, 811.1, 90.4, 57.4), "bare")}
  <svg class="abs" style="left:0;top:0;width:1080px;height:1920px;overflow:visible"><path id="tb-br" d="M652 874 V914 H876 V874" fill="none" stroke="#d97757" stroke-width="3" stroke-linejoin="round" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1"/></svg>
  <div id="tb-dbl" class="t" style="left:564px;top:924px;width:400px;text-align:center;font-family:var(--serif);font-style:italic;font-weight:500;font-size:56px;color:var(--clay);opacity:0">double</div>
  {plate("tb-fn", FOOT, (0, 0, 1176, 108), (140, 994, 800, 73), "w")}
  <div id="tb-s" class="src" style="left:72px;top:1104px;width:936px;text-align:center;font-size:28px">Weekly limit, claude.com/pricing</div>
</div>"""))

    # ---- b23-b28 Chase's note: real artifacts and the assumed-math callback in ivory cards
    QB = (90, 318, 900, 144)
    QR = (16, 548, 880, 140.8)
    S.append(own("sc-q23", f"""<div id="sc-q23" class="scene">
  {card("q23-card", (72, 300, 936, 180))}
  {plate("q23-pl", OVER, QR, QB, "w", extra=mark("q23-m0", inpin(QB, 0, 0, 1, map_box(QR, QB, (32, 566, 830, 45)))) + mark("q23-m1", inpin(QB, 0, 0, 1, map_box(QR, QB, (32, 613, 88, 45)))))}
</div>"""))

    S.append(own("sc-q24", f"""<div id="sc-q24" class="scene">
  {card("q24-card", (72, 212, 936, 467))}
  {vplate("q24-pl", [], "clips/rename-line-highlight.mp4", (0, 0, 960, 460), (90, 230, 900, 431), 44.183, 2.517, 0)}
</div>"""))

    SB = (90, 240, 900, 194)
    SR = (0, 0, 1392, 300)
    S.append(own("sc-q25", f"""<div id="sc-q25" class="scene">
  {card("q25-card", (72, 222, 936, 373))}
  {plate("q25-pl", "shots/ultra-support.png", SR, SB, "w", extra=mark("q25-m", inpin(SB, 0, 0, 1, map_box(SR, SB, (24, 158, 956, 58)))))}
  {lbl("q25-tag", 116, 512, "I'm pretty sure", 34, "padding:14px 18px;background:#f6e3da;border-radius:10px;opacity:0")}
</div>"""))

    S.append(own("sc-q26", f"""<div id="sc-q26" class="scene">
  {card("q26-card", (72, 200, 936, 510))}
  <div id="q26-l" class="t" style="left:72px;top:245px;width:936px;text-align:center;font-family:var(--mono);font-weight:500;font-size:30px;letter-spacing:.14em;color:var(--mut)">THE ASSUMED MATH</div>
  <div id="q26-row" class="abs" style="left:72px;top:345px;width:936px;height:260px;display:flex;justify-content:center;align-items:baseline;font-family:var(--serif);font-weight:500;line-height:1;color:var(--ink)">
    <span id="q26-fig" class="stw" style="font-size:260px;letter-spacing:-.02em">4x<i id="q26-st" class="sk" style="left:-24px;right:-24px;top:107px;height:8px"></i></span>
  </div>
</div>"""))

    S.append(own("sc-q27", f"""<div id="sc-q27" class="scene">
  {card("q27-card", (72, 162, 936, 530))}
  {plate("q27-pl", HERO, (0, 0, 3080, 1250), (90, 180, 900, 365.26), "o0 w")}
  {lbl("q27-verified", 116, 615, "No 5-hour limit, verified", 34)}
</div>"""))

    S.append(own("sc-q28", f"""<div id="sc-q28" class="scene">
  {card("q28-card", (72, 254, 936, 396))}
  {plate("q28-p0", PLANS, (64, 500, 1216, 200), (90, 272, 900, 148), "w")}
  <div class="abs" style="left:90px;top:452px;width:900px;height:1px;background:#e4e2da"></div>
  {plate("q28-p1", PLANS, (1396, 500, 1216, 200), (90, 484, 900, 148), "w")}
</div>"""))

    # ---- b29 two real name rows, through the final frame
    S.append(own("sc-close", f"""<div id="sc-close" class="scene"><div id="cl-g" class="fill">
  {card("cl-card", (72, 254, 936, 396))}
  {plate("cl-p0", PLANS, (64, 500, 1216, 200), (90, 272, 900, 148), "w")}
  <div class="abs" style="left:90px;top:452px;width:900px;height:1px;background:#e4e2da"></div>
  {plate("cl-p1", PLANS, (1396, 500, 1216, 200), (90, 484, 900, 148), "w")}
  {drawn("cl-o0", (409.7, 328.2, 426.3, 77.0), 12)}
  {drawn("cl-o1", (436.4, 540.2, 426.3, 77.0), 12)}
</div></div>"""))
    # @SCENES
    return "\n".join(S)
