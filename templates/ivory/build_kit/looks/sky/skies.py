"""Sky recolours: one finished sky short, many skies.

A sky short's page writes its colours by role: four sky bands, the cloud pixels and their shading, the title-cloud fill,
the cream card frame, the navy outline and text, the soft text, the card shadow, grass and brick. This swaps those roles
on the built page (`<OUT>/index.html`) and writes each sky as its own HyperFrames project, so a recolour costs a render,
not a rebuild. The guide, Claude's orange, logos, captions, motion and sound are untouched. Some skies add a texture or
props over the bands (rain, snow, stars, palms, an outrun sun, a perspective grid), drawn in CSS and pixel SVG.

Why: posting one video several times as trial reels. A whole-look colour change is what got a variant past Instagram's
duplicate filter in our tests; the further a sky sits from the original, the better (`distance` measures it).

  python templates/ivory/build_kit/looks/sky/skies.py list
  python templates/ivory/build_kit/looks/sky/skies.py <OUT> set stills 2.2,6.5,25        (or: noir,storm  |  all)
  python templates/ivory/build_kit/looks/sky/skies.py <OUT> set check
  python templates/ivory/build_kit/looks/sky/skies.py <OUT> set render [4k]
  python templates/ivory/build_kit/looks/sky/skies.py <OUT> distance                     (after stills: how far each is from the original)

<OUT> is the built sky project (the folder with index.html, e.g. work/<id>/v2/sky). Each sky lands in <OUT>/skies/<name>/;
a render is delivered as <OUT>/skies/<id>_sky-<name>_1080p30.mp4 (or _4k30) at -14 LUFS with a contact sheet.

Rules learned making them:
- An orange sky swallows the orange guide and Claude's mark (a golden-hour sky was dropped; sunset keeps purple on top).
- On a dark sky, labels written straight on the sky in the navy must go light. HyperFrames refuses `[style*=...]` selectors
  and GSAP re-serialises inline styles anyway, so the colour is rewritten in the page (`light=True`).
- Light clouds on a dark sky read as daytime; dark skies tint the cloud pixels and the title-cloud fill too.
"""
import os, pathlib, re, shutil, subprocess, sys
from urllib.parse import quote

KIT = pathlib.Path(__file__).resolve().parent
REPO = KIT.parents[4]
HF = "npx --yes hyperframes@0.9.13"

# each role as the day build writes it
DAY = dict(s1="#5d9bf7", s2="#6fa8ff", s3="#82b6ff", s4="#97c3ff", cloud='fill="#ffffff"', shade="#cfe3ff", frame="#fffaf0",
           navy="#1d2b53", soft="#5b6890", shadow="rgba(29,43,83,.4)", g1="#63c74d", g2="#3e8948", b1="#c97c43", b2="#a35b2c",
           titlebg="background:#fff;")

# the default set: the five picked for trial-reel variants, all well away from the original blue
SET = ["noir", "storm", "snow", "sunset", "vicepastel"]


# ---------------------------------------------------------------- drawing helpers (layers over the sky bands)

def px(rows, pal, s):
    """Pixel art -> data-URI SVG. rows: one char per pixel, '.' empty; pal: char -> colour; s: pixel size."""
    w, h = len(rows[0]), len(rows)
    rects = "".join(f'<rect x="{x * s}" y="{y * s}" width="{s}" height="{s}" fill="{pal[c]}"/>'
                    for y, r in enumerate(rows) for x, c in enumerate(r) if c != ".")
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w * s}" height="{h * s}" shape-rendering="crispEdges">{rects}</svg>'
    return f'url("data:image/svg+xml,{quote(svg)}")', w * s, h * s


def layers(p, extra):
    """extra: (image, size, position, repeat), first drawn on top; the four sky bands go underneath."""
    bands = f"linear-gradient(180deg,{p['s1']} 0 30%,{p['s2']} 30% 62%,{p['s3']} 62% 82%,{p['s4']} 82%)"
    L = extra + [(bands, "100% 100%", "0 0", "no-repeat")]
    return ("\n.top,.scn{background-image:" + ",".join(l[0] for l in L) + " !important;background-size:" + ",".join(l[1] for l in L) +
            " !important;background-position:" + ",".join(l[2] for l in L) + " !important;background-repeat:" + ",".join(l[3] for l in L) + " !important}\n")


PALM = ["....kkkk...kkkk....", "..kkkkkkk.kkkkkkk..", ".kkk...kkkkk...kkk.", "kk....kk.k.kk....kk", "k....kk..k..kk....k",
        "....kk...k...kk....", "...k.....k.....k...", ".........kk........", ".........kk........", "........kk.........",
        "........kk.........", "........kk.........", "........kkk........", ".........kk........", ".........kk........",
        ".........kk........", "........kkk........", "........kk.........", "........kk.........", "........kk.........",
        ".......kkk.........", ".......kkkk........", "......kkkkkk.......", ".....kkkkkkkk......"]
PLANET = ["..........cccccc..........", "........cccccccccc........", ".......cccdddddcccc.......", "......ccddddddddddcc......",
          "rrrr..ccdddddddddddcc..rrr", "..rrrrrrccddddddddcc.rrr..", ".....rrrrrrrrrrrrrrrrr....", "......ccddrrrrrrrrrdcc....",
          "......ccdddddddddddcc.....", ".......cccdddddddccc......", "........cccccccccc........", "..........cccccc.........."]
MOON = ["...gggg...", ".gggggggg.", "ggghgggggg", "gggggghggg", "gghggggggg", "ggggggghgg", ".gggghggg.", "...gggg..."]
STARS = ("radial-gradient(#fff 1.6px,transparent 2.2px)", "151px 127px", "23px 11px", "repeat")
STARS2 = ("radial-gradient(rgba(255,255,255,.7) 1.2px,transparent 1.8px)", "97px 113px", "7px 59px", "repeat")


def palms(colour, s=12):
    img, w, h = px(PALM, {"k": colour}, s)
    return [(img, f"{w}px {h}px", f"-40px {950 - h}px", "no-repeat"), (img, f"{w}px {h}px", f"{1080 - w + 50}px {950 - h + 24}px", "no-repeat")]


def sun(top, mid, bottom, stripe, cx=540, r=230, base=950):
    """An outrun sun on the horizon, its lower part cut into stripes of the band colour behind it."""
    x, y = cx - r - 10, base - r - 40
    disc = (f"radial-gradient(circle {r}px at 50% {r + 40}px,{top} 0,{mid} 45%,{bottom} 92%,transparent 93%)", f"{2 * r + 20}px {r + 40}px", f"{x}px {y}px", "no-repeat")
    cut = (f"repeating-linear-gradient(180deg,transparent 0 14px,{stripe} 14px 22px)", f"{2 * r + 20}px 132px", f"{x}px 818px", "no-repeat")
    return [cut, disc]


def grid(line, vy=818, y1=950):
    """A perspective floor grid in the bottom band, running to a vanishing point on the horizon."""
    ls = "".join(f'<line x1="540" y1="0" x2="{x}" y2="{y1 - vy}" stroke="{line}" stroke-width="3"/>' for x in range(-1600, 2700, 150))
    ls += "".join(f'<line x1="0" y1="{(y1 - vy) * (k / 7) ** 2:.1f}" x2="1080" y2="{(y1 - vy) * (k / 7) ** 2:.1f}" stroke="{line}" stroke-width="3"/>' for k in range(1, 8))
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="{y1 - vy}">{ls}</svg>'
    return (f'url("data:image/svg+xml,{quote(svg)}")', f"1080px {y1 - vy}px", f"0 {vy}px", "no-repeat")


# ---------------------------------------------------------------- the skies

def _skies():
    P = {}

    def add(name, extra=None, **p):
        if extra is not None:
            p["css"] = layers(p, extra(p))
        P[name] = p

    # -- the default set
    add("noir", s1="#141414", s2="#1f1f1f", s3="#2b2b2b", s4="#383838", cloud='fill="#e6e6e6"', shade="#9a9a9a", frame="#f2f2f2",
        navy="#111111", soft="#5a5a5a", shadow="rgba(0,0,0,.55)", g1="#8a8a8a", g2="#5a5a5a", b1="#6a6a6a", b2="#4a4a4a",
        titlebg="background:#e6e6e6;", light=True)   # black and white; Claude's orange and DeepSeek's blue the only colour
    add("storm", lambda p: [("repeating-linear-gradient(105deg,transparent 0 22px,rgba(220,230,245,.16) 22px 24px,transparent 24px 61px)", "100% 100%", "0 0", "no-repeat")],
        s1="#353a46", s2="#454b59", s3="#58606f", s4="#6f7887", cloud='fill="#a3abb9"', shade="#6d7686", frame="#eef0f4",
        navy="#151a24", soft="#545d6e", shadow="rgba(0,0,0,.45)", g1="#5f8a4e", g2="#3d5e36", b1="#7a6656", b2="#57473b",
        titlebg="background:#a3abb9;", light=True)   # slate grey, dark clouds, rain
    add("snow", lambda p: [("radial-gradient(#fff 3px,transparent 3.6px)", "131px 157px", "13px 29px", "repeat"),
                           ("radial-gradient(rgba(255,255,255,.85) 2px,transparent 2.6px)", "83px 97px", "13px 29px", "repeat")],
        s1="#c9d3df", s2="#d7dfe8", s3="#e3e9f0", s4="#eef2f6", cloud='fill="#ffffff"', shade="#b9c5d4", frame="#ffffff",
        navy="#1e2a3d", soft="#5c6b80", shadow="rgba(30,42,61,.3)", g1="#fbfdff", g2="#c9d6e8", b1="#8fa3bf", b2="#6f85a3")   # winter: snow ground, icy stone, flakes
    add("sunset", s1="#5b3a8c", s2="#a3478f", s3="#e0627a", s4="#ff9a6e", shade="#f3cfe0", frame="#fff6ef", navy="#2e1840",
        soft="#7a5a8c", shadow="rgba(46,24,64,.4)", g1="#8cbf4b", g2="#5a8a3a", b1="#b8693a", b2="#8f4a25", light=True)   # purple on top so the orange guide still reads
    add("vicepastel", lambda p: palms("#0b6f7a") + sun("#fff6c8", "#ffc7a0", "#ff7fb6", p["s4"]),
        s1="#ff6fae", s2="#ff9cc6", s3="#5fd8d2", s4="#a6eee8", cloud='fill="#ffffff"', shade="#ffc2dc", frame="#ffffff",
        navy="#0b3540", soft="#4f7f88", shadow="rgba(214,30,120,.3)", g1="#2cd8cf", g2="#0d8a95", b1="#ffffff", b2="#ff4fa3")   # daytime Miami: pink over turquoise, sun, palms, deco tiles

    # -- more skies
    add("night", lambda p: [STARS, STARS2], s1="#0a1230", s2="#101d4a", s3="#172a60", s4="#203877", cloud='fill="#c9d4f0"', shade="#8394c4",
        frame="#eef1fb", navy="#0b1026", soft="#4c5a86", shadow="rgba(0,0,0,.5)", g1="#2f7d4c", g2="#1d4d33", b1="#6e4a3a", b2="#4a3026",
        titlebg="background:#c9d4f0;", light=True)
    add("dusk", s1="#2c2a6a", s2="#47398c", s3="#7a52a5", s4="#b56faf", cloud='fill="#f4ecff"', shade="#cdb8ea", frame="#fbf4ff",
        navy="#1b1240", soft="#6a5c8e", shadow="rgba(10,6,30,.45)", g1="#56a05c", g2="#2f6a44", b1="#9a5a3e", b2="#6e3d29",
        titlebg="background:#f4ecff;", light=True)
    add("dawn", s1="#8fa6e6", s2="#b3b2ee", s3="#dcbbe2", s4="#ffd6cc", shade="#e8d6f2", frame="#fffaf5", navy="#2f2b5c",
        soft="#6e6a98", shadow="rgba(47,43,92,.35)", g1="#7cc95a", g2="#4d9050", b1="#c98a5a", b2="#a2643a")
    add("aqua", s1="#138a9e", s2="#22a3b2", s3="#46bcc4", s4="#7fd4d2", shade="#c4ecea", frame="#fbfffd", navy="#0d3440",
        soft="#4f7a84", shadow="rgba(13,52,64,.4)", g1="#e6c873", g2="#c2a04f")
    add("crimson", s1="#2a0710", s2="#430c1b", s3="#621326", s4="#821d33", cloud='fill="#f4d8de"', shade="#c98b9a", frame="#fff5f6",
        navy="#1f0610", soft="#7a4a56", shadow="rgba(0,0,0,.45)", g1="#4f7d45", g2="#30522c", b1="#8a5040", b2="#5e3329",
        titlebg="background:#f4d8de;", light=True)
    add("lemon", s1="#f2c230", s2="#f6d156", s3="#f9df80", s4="#fcecb0", shade="#f3dfa0", frame="#fffdf4", navy="#33240b",
        soft="#7a6438", shadow="rgba(51,36,11,.32)", g1="#7cc95a", g2="#4d9050")
    add("candy", s1="#f0609e", s2="#f47fb2", s3="#f89ec6", s4="#fbbdd9", shade="#f6cfe2", frame="#fff8fb", navy="#3d1640",
        soft="#8a5a88", shadow="rgba(61,22,64,.35)", g1="#7fd06a", g2="#4f9a48")

    def space(p):
        planet, plw, plh = px(PLANET, {"c": "#5fd0c8", "d": "#3a9ea8", "r": "#e9b8ff"}, 9)
        moon, mw, mh = px(MOON, {"g": "#bfc0cc", "h": "#8d8f9e"}, 10)
        return [(planet, f"{plw}px {plh}px", "800px 60px", "no-repeat"), (moon, f"{mw}px {mh}px", "60px 430px", "no-repeat"),
                ("radial-gradient(#fff 1.8px,transparent 2.4px)", "137px 121px", "17px 23px", "repeat"),
                ("radial-gradient(rgba(200,210,255,.75) 1.2px,transparent 1.8px)", "71px 59px", "5px 41px", "repeat")]
    add("space", space, s1="#05040a", s2="#09071a", s3="#0e0b25", s4="#141032", cloud='fill="#2a2150"', shade="#3d2f74", frame="#f1eeff",
        navy="#0e0a1f", soft="#5a5280", shadow="rgba(0,0,0,.6)", g1="#c3c3cf", g2="#8d8d9a", b1="#6c6c78", b2="#4c4c56",
        titlebg="background:#e9e4ff;", light=True)
    add("pop", lambda p: [("radial-gradient(rgba(255,59,48,.55) 3.2px,transparent 3.8px)", "16px 16px", "0 0", "repeat"),
                          ("radial-gradient(rgba(255,59,48,.55) 3.2px,transparent 3.8px)", "16px 16px", "8px 8px", "repeat")],
        s1="#ffd60a", s2="#ffd60a", s3="#ffd000", s4="#ffcb00", cloud='fill="#ffffff"', shade="#111111", frame="#ffffff",
        navy="#111111", soft="#444444", shadow="rgba(17,17,17,1)", g1="#1f6feb", g2="#111111", b1="#ff3b30", b2="#111111")
    add("deepsea", lambda p: [("radial-gradient(circle,transparent 5px,rgba(200,245,255,.55) 5.5px 7.5px,transparent 8px)", "173px 211px", "40px 90px", "repeat"),
                              ("radial-gradient(circle,transparent 3px,rgba(200,245,255,.45) 3.5px 5px,transparent 5.5px)", "97px 143px", "71px 13px", "repeat"),
                              ("repeating-linear-gradient(100deg,transparent 0 90px,rgba(180,240,255,.07) 90px 150px,transparent 150px 260px)", "100% 100%", "0 0", "no-repeat")],
        s1="#03252f", s2="#063848", s3="#0a4d60", s4="#0f6478", cloud='fill="#9fe6ee"', shade="#4cb6c6", frame="#f2fdff",
        navy="#04222b", soft="#3f6f7a", shadow="rgba(0,0,0,.45)", g1="#ecd79c", g2="#c9b273", b1="#b89a5e", b2="#8f7745",
        titlebg="background:#bff0f5;", light=True)
    add("miami", lambda p: palms("#a3195f"), s1="#0d8a95", s2="#2cc3c2", s3="#ff8cc3", s4="#ffb6d8", cloud='fill="#ffffff"', shade="#ff9ccb",
        frame="#ffffff", navy="#0b3540", soft="#4f7f88", shadow="rgba(214,30,120,.35)", g1="#2cd8cf", g2="#0d8a95", b1="#ffffff", b2="#ff4fa3")
    add("arcade", lambda p: [("repeating-linear-gradient(180deg,transparent 0 16px,#a01f86 16px 24px)", "520px 132px", "280px 818px", "no-repeat"),
                             ("radial-gradient(circle 250px at 50% 100%,#ffe45a 0,#ffb13d 40%,#ff3d8b 92%,transparent 93%)", "520px 300px", "280px 650px", "no-repeat"),
                             STARS],
        s1="#14062e", s2="#2c0a4c", s3="#5c1272", s4="#a01f86", cloud='fill="#3b1866"', shade="#ff4fa8", frame="#fff4fd",
        navy="#1a0833", soft="#7a4a8c", shadow="rgba(255,61,139,.35)", g1="#ff3dd0", g2="#7a1fa2", b1="#1a0833", b2="#ff3dd0",
        titlebg="background:#ffe3f3;", light=True)
    add("vice", lambda p: palms("#0d0420") + sun("#ffe45a", "#ff9a3d", "#ff3d8b", p["s4"]) + [grid("rgba(34,229,212,.75)"), STARS],
        s1="#1b0b3a", s2="#3a0f5c", s3="#8c1f7a", s4="#e0367f", cloud='fill="#2a0f4a"', shade="#22e5d4", frame="#fff4fd",
        navy="#170830", soft="#6a4a8c", shadow="rgba(34,229,212,.35)", g1="#22e5d4", g2="#0b6f7a", b1="#170830", b2="#22e5d4",
        titlebg="background:#d8fbf7;", light=True)
    add("vicetide", lambda p: palms("#ff3d9a") + sun("#ffd1e6", "#ff6fb3", "#ff2d8a", p["s4"]) + [grid("rgba(255,61,154,.7)")],
        s1="#052a3a", s2="#0a4a5e", s3="#13808f", s4="#26b3b5", cloud='fill="#e9fbff"', shade="#ff3d9a", frame="#ffffff",
        navy="#062330", soft="#3f6f7a", shadow="rgba(255,61,154,.35)", g1="#ff3d9a", g2="#a0105a", b1="#062330", b2="#ff3d9a",
        titlebg="background:#ffe1f0;", light=True)
    add("vicenight", lambda p: palms("#000000") + sun("#22e5d4", "#8a7cff", "#ff3d9a", p["s4"]) + [grid("rgba(255,61,154,.8)"), STARS],
        s1="#050414", s2="#0b0a26", s3="#140f3a", s4="#2a1655", cloud='fill="#1c1640"', shade="#ff3d9a", frame="#f6f2ff",
        navy="#0b0a1f", soft="#5a5280", shadow="rgba(255,61,154,.4)", g1="#ff3d9a", g2="#7a1052", b1="#0b0a1f", b2="#ff3d9a",
        titlebg="background:#f6e3ff;", light=True)
    return P


SKIES = _skies()


# ---------------------------------------------------------------- recolour, check, stills, render

def recolor(src, name):
    p = SKIES[name]
    out = src / "skies" / name
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").unlink(missing_ok=True)
    shutil.copytree(src, out, dirs_exist_ok=True, ignore=shutil.ignore_patterns(
        "skies", "checks", "renders", "sheets", ".hyperframes", "review", "rounds", "*.mp4", "*.wav", "*.m4a", "*.py"))
    for f in src.glob("assets/*"):
        if f.suffix in (".mp4", ".wav", ".m4a") and not (out / "assets" / f.name).exists():
            try: os.link(f, out / "assets" / f.name)
            except OSError: shutil.copy(f, out / "assets" / f.name)
    t = (src / "index.html").read_text(encoding="utf-8")
    for role, new in p.items():
        if role in DAY:
            t = re.sub(re.escape(DAY[role]), new, t, flags=re.I)
    if p.get("light"):   # labels written straight on the sky (class ctr) in the navy go light on a dark sky
        t = re.sub(r'(<div class="ctr[^"]*"[^>]*?color:)' + re.escape(p["navy"]), lambda m: m.group(1) + "#f3f0ff", t, flags=re.I)
    if "css" in p:
        t = t.replace("</style>", p["css"] + "</style>", 1)
    (out / "index.html").write_text(t, encoding="utf-8")
    return out


def short_id(src):
    """work/<id>/v2/sky or work/<id>-sky/v2/sky -> <id>"""
    parts = src.resolve().parts
    return parts[-3].removesuffix("-sky") if len(parts) >= 3 and parts[-2] == "v2" else src.name


def hf(cmd, cwd):
    print(">", cmd, flush=True)
    return subprocess.run(f"{HF} {cmd}", cwd=cwd, shell=True).returncode


def render(src, out, name, k4=False):
    sys.path.insert(0, str(REPO / "tools"))
    import gpu_lock
    raw = out / "renders" / f"{name}{'_4k' if k4 else ''}_raw.mp4"; raw.parent.mkdir(exist_ok=True)
    with gpu_lock.held(f"sky recolour {short_id(src)} {name}"):
        rc = hf(f'render {"--resolution portrait-4k " if k4 else ""}-o "renders/{raw.name}"', out)
    if rc: sys.exit(rc)
    final = src / "skies" / f"{short_id(src)}_sky-{name}_{'4k30' if k4 else '1080p30'}.mp4"
    subprocess.run([sys.executable, str(REPO / "tools/finish.py"), str(raw), str(final), "--sheet", str(final.with_suffix(".sheet.jpg"))], check=True)
    return final


def distance(src):
    """Mean per-pixel colour difference from the original (OKLab x100) over the drawing (y 0-990), across the stills
    every recolour shares with the original's own snapshot set. Higher = looks less like the original."""
    import numpy as np
    from PIL import Image

    def lab(path):
        c = np.asarray(Image.open(path).convert("RGB").crop((0, 0, 1080, 990)).resize((270, 248)), dtype=float) / 255
        c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
        l = np.cbrt(c @ np.array([[0.4122214708, 0.2119034982, 0.0883024619], [0.5363325363, 0.6806995451, 0.2817188376], [0.0514459929, 0.1073969566, 0.6299787005]]))
        return l @ np.array([[0.2104542553, 1.9779984951, 0.0259040371], [0.7936177850, -2.4285922050, 0.7827717662], [-0.0040720468, 0.4505937099, -0.8086757660]])
    base = {f.name: f for f in (src / "checks").glob("at-*.png")}
    rows = []
    for d in sorted((src / "skies").iterdir()):
        shots = [f for f in (d / "checks").glob("at-*.png") if f.name in base] if d.is_dir() else []
        if shots:
            rows.append((np.mean([np.linalg.norm(lab(f) - lab(base[f.name]), axis=2).mean() for f in shots]) * 100, d.name, len(shots)))
    if not rows:
        sys.exit(f"no shared stills: run `stills` on the original ({src}) and on the skies with the same times first")
    for v, n, k in sorted(rows, reverse=True):
        print(f"{n:11s} {v:5.1f}   ({k} stills)")


def main(argv):
    if "list" in argv[:2]:
        print("set:", ", ".join(SET)); print("all:", ", ".join(SKIES)); return
    if len(argv) < 2:
        sys.exit(__doc__)
    src = pathlib.Path(argv[0]).resolve()
    if not (src / "index.html").exists():
        sys.exit(f"{src} has no index.html: point at the built sky project (the folder short.py writes, e.g. work/<id>/v2/sky)")
    if argv[1] == "distance":
        return distance(src)
    names = SET if argv[1] == "set" else list(SKIES) if argv[1] == "all" else argv[1].split(",")
    bad = [n for n in names if n not in SKIES]
    if bad:
        sys.exit(f"unknown sky: {', '.join(bad)} (list: {', '.join(SKIES)})")
    cmd = argv[2] if len(argv) > 2 else ""
    for n in names:
        out = recolor(src, n)
        if cmd == "stills":
            hf(f'snapshot --at {argv[3]} --no-end --keep -o "checks"', out)
        elif cmd == "check":
            hf("check", out)
        elif cmd == "render":
            print("final", render(src, out, n, len(argv) > 3 and argv[3] == "4k"), flush=True)
        print("built", out, flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
