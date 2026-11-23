"""Worked example: the rea short (work/1118-rea) in the blueprint look, the version Chase approved on 2026-11-19
("that's really good"). 9 regions on a 3 x 3 snake, every keyed move on his words (words.json).
  python templates/ivory/build_kit/looks/blueprint/examples/rea.py check
  python templates/ivory/build_kit/looks/blueprint/examples/rea.py stills 8.4 31.3
  python templates/ivory/build_kit/looks/blueprint/examples/rea.py render 4k
Copy this file for a new short: change the paths, the regions, ARR/BEATS, SOUNDS and the JS hooks."""
import math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))
import bp  # noqa: E402
from bp import RED, ln, pl, rc, g, tx, dim_h, dim_v, leader, balloon, ticks, cons, cloud, revtri, plate, title, note, hand, typed  # noqa: E402

WORK = bp.REPO / "work/1119-pixel-guide-test"
REA = bp.REPO / "work/1118-rea"
NAME = "blueprint-rea"
OUT = WORK / "bp-hf"                    # the HyperFrames project; images are copied into its assets/img
IMG = WORK / "img"
WORDS, FACE, VOICE = REA / "words.json", REA / "assets/face_half.mp4", REA / "assets/voice.m4a"
FACE4K = REA / "assets/face_half_4k.mp4"
END = 49.2
COLS, ROWS = 3, 3
ARR = [0, 4.633, 10.5, 17.5, 23.9, 30.367, 36.4, 38.967, 45.6]    # camera arrives at each region (the last is seen in the pull-back)
BEATS = [0, 4.633, 7.6, 10.5, 12.867, 17.5, 19.6, 23.9, 30.367, 32.867, 36.4, 38.967, 41.1, 45.467]   # his cut's beat starts
PULL_AT = 45.4
SHEETNO = ["01", "02", "04", "06", "08", "09", "11", "12", "14"]
HUD = "REA-VIDEO"
HUD_TOP = 22   # as posted 2026-11-20; a new short leaves this out (default 150, clear of the status bar)
CAPTION_FIX = {"rea-video": "REA-VIDEO"}
SHOTS = [("CODE", "0.0–1.4", 77), ("AI", "1.4–2.8", 85), ("AI", "2.8–3.9", 68), ("CODE", "3.9–5.8", 79), ("AI", "5.8–7.5", 88),
         ("CODE", "7.5–10.5", 79), ("AI", "10.5–11.5", 85), ("CODE", "11.5–13.5", 77), ("AI", "13.5–16.1", 88), ("CODE", "16.1–19.0", 73)]
STEPS = ["PLAN THE CONTENT", "COLLECT MATERIAL", "GENERATE · 4 SEEDANCE CALLS", "SCREEN + MOTION GRAPHICS", "EDIT",
         "PACKAGING · subtitles.srt", "SOUND", "COMPARE WITH THE ORIGINAL"]
PROMPT2 = ("Medium shot, slightly high angle, the young woman sits left of center. Having just looked at her phone, she looks up "
           "toward frame right, eyebrows raised and mouth open, and asks in surprise; the phone in her hand moves slightly; "
           "ends on her surprised face. Locked-off camera.")
SOUNDS = [(3.52, "pencil-b", "detail", "the first section cut through the shot strip"),
          (8.05, "es-pop-1", "detail", "the detail circle pops open on the star button"),
          (20.32, "es-whoosh-fast-tight", "detail", "the four layers pull apart"),
          (30.82, "es-swish-flick", "detail", "the shot stack explodes"),
          (41.54, "pencil-a", "main", "the red strike through step 3"),
          (45.4, "sheet-slide", "detail", "the pull-back to the whole drawing")]


def r0():   # 0 - 4.63  "This free tool reverse engineers any viral video for you, shot by shot."
    h = title(["Reverse-engineer", "any " + RED.format("viral video.")], y=44, t=0.05)
    h += note(62, 18, "FIG. 01 &nbsp;·&nbsp; INPUT", t=0.0)
    h += plate(100, 300, 270, 480, "assets/img/dr_s02.png", t=0.3)
    s = dim_h(100, 370, 270, "1080", ext=292, t=0.55) + dim_v(66, 300, 780, "1920", ext=92, t=0.65) + ticks(100, 300, 270, 480, t=0.45)
    for k in range(4):
        h += plate(450 + k * 145, 330, 135, 200, f"assets/img/dr_s{k + 1:02d}.png", "center 30%", t=0.85 + k * 0.1)
        s += tx(452 + k * 145, 318, ["0.0", "1.4", "2.8", "3.9"][k] + "s", 18, "start", "ts", t=0.9 + k * 0.1)
    s += dim_h(450, 1020, 568, "19.0 s · 10 SHOTS", ext=540, t=1.4)
    s += leader([(370, 420), (410, 420), (410, 380), (446, 380)], t=0.8)
    for k, tt in enumerate([3.52, 4.08, 4.16]):            # "shot by shot": a red section cut per word
        x = 450 + (k + 1) * 145 - 5
        s += g(ln(x, 300, x, 556, "r", 'stroke-dasharray="14 6 3 6" stroke-width="5"') + tx(x, 292, "ABC"[k], 24, "middle", "tr"), tt)
    for k, (lab, red, tt) in enumerate([("SPLIT", False, 2.08), ("CLASSIFY", False, 2.4), ("REBUILD", True, 2.72)]):
        x = 450 + k * 200
        s += g(rc(x, 660, 170, 76, ("r" if red else "l") + " bfill", 'rx="6"') + tx(x + 85, 708, lab, 26, "middle", "tr" if red else "tl")
               + (ln(x + 172, 698, x + 198, 698, "l", 'marker-end="url(#ah)"') if k < 2 else ""), tt)
    s += tx(450, 640, "PROCESS", 18, "start", "ts", t=2.0)
    s += cons([(0, 300, 1080, 300), (0, 780, 1080, 780), (100, 0, 100, 998), (370, 0, 370, 998), (0, 698, 1080, 698)])
    return h, s


def r1():   # 4.63 "It's called rea-video. It's open source," 7.6 "over 10,000 GitHub stars in under three weeks,"
    h = '<div class="h1 outline" data-t="4.5" style="left:56px;top:40px;font-size:180px">rea-video</div>'
    h += note(64, 236, typed("OPEN SOURCE · APACHE-2.0 · FREE", 6.96, 7.5), 24, "var(--line)", t=6.9)
    h += ('<div class="plate" data-t="7.62" style="left:60px;top:300px;width:640px;height:135px">'
          '<img class="duoimg" src="assets/img/gh.jpg" style="width:1280px;height:auto;transform:scale(.5) translateY(-120px);transform-origin:0 0;object-fit:none"></div>')
    bx, by = 60 + 1191 * .5, 300 + (201 - 60) * .5          # the star button on the page, in region coords
    cx, cy, cr, z = 872, 418, 138, 2.6
    h += (f'<div class="detail bp-keyed" id="detail" style="left:{cx - cr}px;top:{cy - cr}px;width:{2 * cr}px;height:{2 * cr}px;'
          f'background:#fff url(assets/img/gh.jpg) {-(1191 * z - cr):.0f}px {-(201 * z - cr):.0f}px/{1280 * z:.0f}px auto no-repeat"></div>')
    s = ticks(60, 300, 640, 135, t=7.7)
    a = math.atan2(cy - by, cx - bx)
    s += g(f'<circle pathLength="1" class="r" cx="{bx:.0f}" cy="{by:.0f}" r="34"/>', 7.92)
    s += g(ln(bx + 34 * math.cos(a), by + 34 * math.sin(a), cx - cr * math.cos(a), cy - cr * math.sin(a), "r"), 8.02)
    s += g(f'<circle pathLength="1" class="r" cx="{cx}" cy="{cy}" r="{cr + 6}" stroke-width="6"/>', 8.1)
    s += tx(cx, cy + cr + 40, "DETAIL B · SCALE 2.6 : 1", 20, "middle", "tr", t=8.3)
    h += '<div class="big red bp-keyed" id="count" style="left:596px;top:618px;font-size:150px">0</div>'
    h += note(608, 772, "GITHUB STARS &nbsp;★", 28, "var(--line)", t=8.24)
    x0, y0, x1, y1 = 110, 830, 500, 600
    ax = ln(x0, y0, x1 + 20, y0, "l", 'marker-end="url(#ah)"') + ln(x0, y0, x0, y1 - 20, "l", 'marker-end="url(#ah)"')
    for d in range(0, 22, 7):
        x = x0 + (x1 - x0) * d / 21
        ax += ln(x, y0, x, y0 + 10, "t") + tx(x, y0 + 34, f"{d}", 18, "middle", "ts")
    for v in (5, 10):
        y = y0 - (y0 - y1) * v / 10
        ax += ln(x0 - 10, y, x0, y, "t") + tx(x0 - 16, y + 6, f"{v}K", 18, "end", "ts") + ln(x0, y, x1, y, "cn")
    ax += tx(x0 + 4, y1 - 30, "STARS", 18, "start", "ts") + tx(x1 + 26, y0 + 6, "DAYS", 18, "start", "ts")
    s += g(ax, 8.5)
    pts = [(x0 + (x1 - x0) * d / 21, y0 - (y0 - y1) * (v / 10)) for d, v in
           [(0, 0), (2, .2), (4, .9), (6, 2.4), (8, 4.1), (10, 5.6), (12, 6.9), (14, 7.9), (16, 8.7), (18, 9.4), (20, 10)]]
    s += pl(pts, "r", 'stroke-width="5" data-d="1.0"', t=8.64)
    s += dim_h(x0, x1, y0 + 74, "&lt; 3 WEEKS", red=True, t=9.6)
    return h, s


def r2():   # 10.5 "hand Claude a video" 12.867 "and get a breakdown of exactly how it was created so you can make your own version."
    h = title(["Hand Claude", "a " + RED.format("video.")], y=44, t=10.6)
    h += note(62, 18, "FIG. 04 &nbsp;·&nbsp; INPUT → REPORT", t=10.55)
    h += ('<div class="term" data-t="10.9" style="left:60px;top:282px;width:740px;height:150px">'
          '<div style="color:var(--red)">✻ Claude Code</div>'
          f'<div><span style="color:var(--soft)">&gt;</span> {typed("break down this video  dual_role.mp4", 11.5, 12.5)}</div></div>')
    h += plate(840, 250, 140, 249, "assets/img/dr_s02.png", ident=' id="handed"', t=11.52)
    s = g(ln(836, 380, 806, 380, "r", 'marker-end="url(#ahr)"'), 11.7)
    rows = [("HOW THIS VIDEO WAS MADE", "var(--soft)", 13.0), ("dual_role.mp4", "var(--line)", 13.15),
            ('CODE <b class="red">59%</b> · AI <b class="red">41%</b>', "var(--line)", 13.4), ("10 SHOTS · 0:19 · 9:16", "var(--line)", 13.6),
            ("CONFIDENCE 80%", "var(--soft)", 13.8)]
    h += '<div class="doc" data-t="12.9" style="left:60px;top:480px;width:430px;height:342px"></div>'
    for k, (txt, col, tt) in enumerate(rows):
        h += note(84, 500 + k * 62, txt, 24 if k else 20, col, t=tt)
    h += plate(520, 480, 500, 342, "assets/img/storyboard.jpg", dev=(14.0, 14.9), t=13.12)
    s += ticks(520, 480, 500, 342, t=13.2)
    s += g(revtri(560, 880) + pl([(600, 870), (640, 870)], "r"), 16.56)
    h += hand(650, 846, "make your own version", 40, t=16.6, rot=-3)
    s += cons([(0, 480, 1080, 480), (0, 822, 1080, 822), (520, 0, 520, 998)])
    return h, s


def r3():   # 17.5 "So here's how it works." 19.6 "It breaks a video into all of its component pieces, sound, voice, motion graphics,"
    h = '<div class="tag" data-t="17.6" style="left:60px;top:40px">HOW IT WORKS</div>'
    h += title(["Component " + RED.format("pieces.")], y=96, size=92, t=18.64)
    px, py, pw, ph = 74, 310, 300, 533
    h += plate(px, py, pw, ph, "assets/img/dr_s01.png", "center top", duo=True, t=18.8)
    s = dim_h(px, px + pw, 290, "FRONT", ext=py - 14, t=19.0) + ticks(px, py, pw, ph, t=19.0)
    for yy in (py, py + ph):
        s += ln(px + pw + 30, yy, 1050, yy, "cn")
    for k, (lab, tt, red) in enumerate([("PICTURE", 20.88, True), ("SOUND", 21.70, False), ("VOICE", 22.26, False), ("MOTION GRAPHICS", 22.74, False)]):
        fx = 500 + k * 140
        s += rc(500, py, 40, ph, "l", f'style="fill:url(#{"hatchr" if red else "hatch"})" data-fx="{fx}" id="bar{k}"', t=19.4 + k * 0.05)
        s += balloon(fx + 20, py - 30, str(k + 1), red, t=tt)
        s += tx(fx + 70, py + ph / 2, lab, 24, "middle", "tr" if red else "tl", -90, t=tt)
        if lab in ("SOUND", "VOICE"):
            wv = [(fx + 20 + (12 if i % 2 else -12) * (0.4 + 0.6 * abs(math.sin(i * 1.7))), py + 30 + i * 18) for i in range(int((ph - 60) / 18))]
            s += pl(wv, "l", 'stroke-width="2.5"', t=tt + 0.08)
    s += tx(500, py + ph + 44, "SIDE VIEW · EXPLODED", 18, "start", "ts", t=20.4)
    s += cons([(px + pw / 2, 250, px + pw / 2, 960)])
    return h, s


def r4():   # 23.9 "and then decides, is this real footage, is this AI footage, or is this simply code ..."
    h = title(["Then it " + RED.format("decides.")], y=44, t=24.0)
    h += note(62, 18, "FIG. 08 &nbsp;·&nbsp; CLASSIFY", t=23.95)
    h += plate(60, 300, 210, 374, "assets/img/dr_s05.png", duo=True, t=24.1)
    s = ticks(60, 300, 210, 374, t=24.15) + balloon(165, 720, "05", t=24.3)
    cx, cy, r = 420, 487, 96
    s += g(f'<polygon pathLength="1" class="l bfill" points="{cx},{cy - r} {cx + r},{cy} {cx},{cy + r} {cx - r},{cy}"/>' + ln(272, 487, cx - r - 2, 487, "l", 'marker-end="url(#ah)"'), 24.4)
    s += tx(cx, cy - 18, "REAL?", 21, "middle", "ts", t=25.1) + tx(cx, cy + 10, "AI?", 24, "middle", "tr", t=26.5) + tx(cx, cy + 38, "CODE?", 21, "middle", "ts", t=28.4)
    outs = [("assets/img/real.jpg", "center 40%", "A", "REAL FOOTAGE", 25.22, None), ("assets/img/dr_s02.png", "center 35%", "B", "AI FOOTAGE", 26.66, (26.75, 27.45)),
            ("assets/img/code7.jpg", "center", "C", "CODE", 28.58, None)]
    for k, (src, pos, letter, lab, tt, dev) in enumerate(outs):
        y = 232 + k * 236
        red = dev is not None
        s += pl([(cx + r, cy), (580, cy), (580, y + 100), (636, y + 100)], "r" if red else "t",
                f'marker-end="url(#{"ahr" if red else "ah"})"' + ("" if red else ' stroke-dasharray="8 6"'), t=tt - 0.15)
        h += plate(640, y, 380, 200, src, pos, duo=not red, dev=dev, t=tt)
        h += f'<div class="tag{" redtag" if red else " dimtag"}" data-t="{tt + 0.1}" style="left:656px;top:{y + 14}px">{letter} · {lab}</div>'
        if red: h += f'<div class="tag redtag" data-t="27.5" style="left:824px;top:{y + 152}px;font-size:20px">MATCH 85%</div>'
        s += ticks(640, y, 380, 200, 10, 16, t=tt + 0.05)
    s += cons([(0, 487, 1080, 487), (420, 0, 420, 998), (640, 0, 640, 998)])
    return h, s


def r5():   # 30.367 "it reverse engineers every single part." 32.867 "So if it's an AI video, it gives you a prompt you can use to recreate it,"
    h = title(["Every " + RED.format("single"), "part."], y=44, size=96, t=30.45)
    h += note(62, 18, "FIG. 09 &nbsp;·&nbsp; EXPLODED VIEW", t=30.4)
    stack = "".join(
        f'<div class="lay{" ai" if SHOTS[i][0] == "AI" else ""}" id="lay{i}" style="transform:translateZ({(9 - i) * 46}px)"><img class="{"" if SHOTS[i][0] == "AI" else "duoimg"}" src="assets/img/dr_s{i + 1:02d}.png">'
        + "".join(f'<i class="mk" data-i="{i}" style="{p}"></i>' for p in ["left:0;top:0", "right:0;top:0", "left:0;bottom:0", "right:0;bottom:0"])
        + "</div>" for i in range(10))
    h += f'<div class="isowrap" data-t="30.45"><div class="iso">{stack}</div></div>'
    rows = "".join(f'<tr><td><span class="bal{" red" if t == "AI" else ""}">{i + 1}</span></td><td class="{"red" if t == "AI" else ""}">{"AI" if t == "AI" else "CODE"}</td>'
                   f'<td>{tm}s</td><td>{m}%</td></tr>' for i, (t, tm, m) in enumerate(SHOTS))
    h += f'<table class="bom" id="bom" style="left:640px;top:236px"><tr><th colspan="4">PARTS LIST · 10 SHOTS</th></tr>{rows}</table>'
    h += '<div class="note" id="mix" data-t="32.58" style="left:640px;top:800px;font-size:22px;color:var(--line)">CODE <b class="red">59%</b> &nbsp;·&nbsp; AI <b class="red">41%</b></div>'
    h += ('<div class="spec bp-keyed" id="prompt" style="left:620px;top:236px;width:420px;font-size:21px;line-height:1.5;opacity:0">'
          f'<b class="red">SHOT 02 · AI VIDEO · PROMPT</b><br>{typed(PROMPT2, 34.3, 36.2)}</div>')
    s = '<g id="leaders" class="bp-late"></g><g id="pleader" class="bp-late"></g>' + cons([(640, 0, 640, 998)])
    s += g(dim_h(640, 640 + 386 * .59, 860, "", ext=840) + dim_h(640 + 386 * .59, 1026, 860, "", ext=840, red=True), 32.6, 'id="mixdim"')
    return h, s


def r6():   # 36.4 "and if it's motion graphics, it gives you the actual code."
    h = title(["If it’s code:", "the " + RED.format("actual code.")], y=44, t=36.45)
    h += note(62, 18, "FIG. 11 &nbsp;·&nbsp; SECTION A–A", t=36.42)
    h += plate(110, 270, 860, 482, "assets/img/code7.jpg", dev=(38.02, 38.7), t=36.5)
    s = ticks(110, 270, 860, 482, t=36.6)
    for k, (x, y, w, hh, lab) in enumerate([(278, 370, 133, 237, "A · 9:16"), (440, 423, 229, 126, "B · 16:9"), (695, 370, 134, 237, "C · 9:16")]):
        s += g(rc(x, y, w, hh, "l", 'fill="none" stroke-dasharray="10 6"') + tx(x, y - 10, lab, 18, "start", "tl"), 36.9 + k * 0.15)
    s += dim_h(411, 440, 650, "29", ext=607, t=37.4) + dim_h(669, 695, 650, "26", ext=607, t=37.5)
    s += dim_h(278, 829, 712, "LAYOUT · 3-UP · CENTRED", ext=667, t=37.7)
    s += g(ln(40, 488, 1040, 488, "r", 'stroke-dasharray="26 8 4 8" stroke-width="5"')
           + "".join(ln(x, 488, x, 448, "r", 'marker-end="url(#ahr)"') + tx(x, 434, "A", 26, "middle", "tr") for x in (40, 1040)), 38.02)
    h += ('<div class="spec" data-t="37.5" style="left:110px;top:776px;width:860px;font-size:22px">'
          f'<b class="red">REMAKE · SHOT 7</b><br>{typed("Code render: rebuild in Remotion / HTML from the text tracks and layout. 100% controllable, no generative model needed.", 37.6, 38.9)}</div>')
    s += cons([(0, 270, 1080, 270), (0, 752, 1080, 752), (540, 0, 540, 998)])
    return h, s


def r7():   # 38.967 "And what you ultimately get is a recipe" 41.1 "that you can edit in any way you want to mimic the style of the original video."
    h = title(["A recipe", "you can " + RED.format("edit.")], y=44, t=40.18)
    h += note(62, 18, "FIG. 13 &nbsp;·&nbsp; PROCEDURE · REV A", t=39.0)
    rows = "".join(f'<div class="step" data-t="{39.4 + i * 0.12:.2f}"><span class="sn">{i + 1:02d}</span>{t}</div>' for i, t in enumerate(STEPS))
    h += (f'<div class="proc" data-t="39.05" style="left:60px;top:270px;width:640px"><div class="ph">REMAKE IT YOURSELF · DO IT IN THIS ORDER</div>'
          f'<div class="pq">“Copy the method and the rhythm, not the pictures.”</div>{rows}</div>')
    y0, rh = 270 + 52 + 64, 56
    s = g(cloud(54, y0 + 1, 652, rh - 4) + revtri(740, y0 + rh / 2 - 4) + pl([(712, y0 + rh / 2), (770, y0 + rh / 2)], "r"), 41.14)
    h += hand(790, y0 - 14, "your script,<br>your numbers", t=41.3)
    sy = y0 + 2 * rh + rh / 2
    s += g(ln(292, sy, 545, sy, "r", 'stroke-width="4"'), 41.54)
    s += g(pl([(560, sy), (728, sy)], "r", 'marker-end="url(#ahr)"'), 41.8)
    h += hand(740, sy - 30, "your own<br>footage", t=41.9)
    cy6 = y0 + 5 * rh
    s += g(cloud(54, cy6 + 1, 652, rh - 4) + revtri(740, cy6 + rh / 2 - 2, "B"), 43.14)
    h += hand(780, cy6 - 14, "your style", t=43.62)
    h += ('<table class="rev" data-t="44.3" style="left:716px;top:770px"><tr><th>REV</th><th>CHANGE</th><th>BY</th></tr>'
          '<tr><td class="red">A</td><td>YOUR CONTENT</td><td>YOU</td></tr><tr><td class="red">B</td><td>YOUR STYLE</td><td>YOU</td></tr></table>')
    return h, s


def r8():   # the drawing's own title block, bottom-right of the sheet; read in the pull-back
    h = ('<div class="tblock" style="left:60px;top:300px;width:960px">'
         '<div class="tbig" style="font-size:130px">REA-VIDEO</div>'
         '<div class="trow"><span>HOW IT WORKS</span><span>DRAWN: CLAUDE</span><span>14 SHEETS</span></div></div>')
    return h, cons([(0, 499, 1080, 499), (540, 0, 540, 998)])


REGIONS = [r0, r1, r2, r3, r4, r5, r6, r7, r8]
ENDBLOCK = ('<div id="endblock" data-layout-allow-overlap style="top:560px"><div class="tbig">SETUP <b class="red">GUIDE</b></div>'
            '<div class="trow"><span id="endcta" style="opacity:0;color:var(--red)">CHECK THE DESCRIPTION ↓</span><span>SHEET 14 / 14</span><span>FREE</span></div></div>'
            '<div id="endarrow"></div>')

JS = r"""
// measured on the finished layout, before anything is hidden: leaders from the exploded stack to its parts list
window.BP_PRE = tl => { const reg = document.getElementById('reg5'); const R = reg.getBoundingClientRect();
  const gL = document.getElementById('leaders'); const rows = reg.querySelectorAll('.bom tr');
  for (let i = 0; i < 10; i++) {
    let best = null;
    reg.querySelectorAll('.mk[data-i="' + i + '"]').forEach(m => { const b = m.getBoundingClientRect(); if (!best || b.x > best.x) best = b; });
    const row = rows[i + 1].getBoundingClientRect();
    const x0 = best.x - R.x, y0 = best.y - R.y, x1 = row.x - R.x - 2, y1 = row.y + row.height / 2 - R.y;
    const ai = rows[i + 1].querySelector('td.red') ? 'r' : 't';
    gL.insertAdjacentHTML('beforeend', `<g data-t="${(32.0 + i * 0.05).toFixed(2)}"><circle class="${ai == 'r' ? 'dotr' : 'dot'}" cx="${x0}" cy="${y0}" r="5"/>` +
      `<polyline pathLength="1" class="${ai}" fill="none" points="${x0},${y0} ${x0 + 30},${y0} ${x1},${y1}"/></g>`);
    if (i == 1) { const p = document.getElementById('prompt').getBoundingClientRect();
      document.getElementById('pleader').insertAdjacentHTML('beforeend', `<g data-t="33.3"><circle class="dotr" cx="${x0}" cy="${y0}" r="6"/>` +
        `<polyline pathLength="1" class="r" fill="none" points="${x0},${y0} ${x0 + 30},${y0} ${p.x - R.x - 4},${p.y - R.y + 22}"/></g>`); }
  } };
window.BP_KEYED = tl => {
  // sheet 02: the star counter and the magnified detail
  const cnt = document.getElementById('count'), co = {v: 0};
  tl.fromTo(cnt, {opacity: 0}, {opacity: 1, duration: 0.1}, 7.92);
  tl.to(co, {v: 10000, duration: 0.75, ease: 'power2.out', onUpdate: () => { cnt.textContent = Math.round(co.v / 10) * 10 >= 10000 ? '10,000+' : Math.round(co.v).toLocaleString('en-US'); }}, 7.92);
  tl.fromTo('#detail', {scale: 0, opacity: 0}, {scale: 1, opacity: 1, duration: 0.4, ease: 'back.out(1.6)'}, 8.05);
  // sheet 04: the video is handed in
  tl.fromTo('#handed', {x: 160, rotation: 6}, {x: 0, rotation: 0, duration: 0.45, ease: 'power3.out'}, 11.52);
  // sheet 06: the four layers sit stacked, then pull apart on "component pieces"
  for (let k = 0; k < 4; k++) { const b = document.getElementById('bar' + k);
    tl.fromTo(b, {attr: {x: 500}}, {attr: {x: +b.dataset.fx}, duration: 0.55, ease: 'power3.out'}, 20.32 + k * 0.06); }
  // sheet 09: the stack explodes, then hands over to the shot-02 prompt
  for (let i = 0; i < 10; i++) tl.fromTo('#lay' + i, {z: 0}, {z: (9 - i) * 46, duration: 0.7, ease: 'power3.out'}, 30.82 + (9 - i) * 0.03);
  document.querySelectorAll('#bom tr').forEach((r, q) => tl.fromTo(r, {opacity: 0}, {opacity: 1, duration: 0.12}, 31.86 + q * 0.06));
  tl.to(['#bom', '#mix', '#mixdim', '#leaders'], {opacity: 0, duration: 0.25}, 32.95);
  for (let i = 0; i < 10; i++) if (i != 1) tl.to('#lay' + i, {opacity: 0.25, duration: 0.3}, 33.2);
  tl.to('#lay1', {x: 40, duration: 0.4, ease: 'power2.out'}, 33.2);
  tl.fromTo('#prompt', {opacity: 0, y: 14}, {opacity: 1, y: 0, duration: 0.35}, 33.3);
  // the end: the title block becomes the call to action
  tl.fromTo('#endblock', {opacity: 0, y: 60}, {opacity: 1, y: 0, duration: 0.45, ease: 'power3.out'}, 46.6);
  tl.to('#endcta', {opacity: 1, duration: 0.2}, 48.0);
  tl.fromTo('#endarrow', {height: 0}, {height: 60, duration: 0.3, ease: 'power2.out'}, 48.24);
};
"""

if __name__ == "__main__":
    bp.main(sys.modules[__name__], sys.argv[1:])
