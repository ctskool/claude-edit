"""The sky look engine: the pixel Claude guide acting out the short on a bright pixel sky, rendered through HyperFrames.
A short is one spec module (see examples/rea.py) that calls main(spec, argv):
  check | stills 3.9 8.2 ... | render [4k]
The spec gives NAME, OUT, WORDS, FACE (FACE4K), VOICE, IMG, END, SOUNDS, SCENES (markup of its .scn scenes), JS (its
choreography, pasted into engine.js), and optionally CSS, STAGE (extra markup over the scenes), POSES / POSES2 (the
guide's poses and his copy's), CHUNKS (hand-set caption chunks) and H1_TOP."""
import json, pathlib, re, shutil, subprocess, sys

KIT = pathlib.Path(__file__).parent
REPO = KIT.parents[4]
sys.path.insert(0, str(KIT)); sys.path.insert(0, str(KIT.parent / "blueprint"))
import bp  # noqa: E402  mix() and hf(): the same sound rule and HyperFrames 0.9.13 runner as blueprint
from sprites import PAL, POSES, PROPS, PX  # noqa: E402

TEXT_TOP = 150   # titles start here, clear of the phone's status bar / Dynamic Island [Chase, 2026-11-20]
LOW = {"chop": 45}   # poses drawn below his feet line (the blade), px
STEP = ("polygon(0 12px,6px 12px,6px 6px,12px 6px,12px 0,calc(100% - 12px) 0,calc(100% - 12px) 6px,calc(100% - 6px) 6px,"
        "calc(100% - 6px) 12px,100% 12px,100% calc(100% - 12px),calc(100% - 6px) calc(100% - 12px),calc(100% - 6px) calc(100% - 6px),"
        "calc(100% - 12px) calc(100% - 6px),calc(100% - 12px) 100%,12px 100%,12px calc(100% - 6px),6px calc(100% - 6px),"
        "6px calc(100% - 12px),0 calc(100% - 12px))")          # the stepped pixel corners of a title cloud
CLOUD = ["....wwww......", "..wwwwwwww....", ".wwwwwwwwwwww.", "wwwwwwwwwwwwww", "wwwwwwwwwwwwww", ".ssssssssssss."]
CLOUD_SVG = ('<svg width="168" height="72" shape-rendering="crispEdges">' + "".join(
    f'<rect x="{c*12}" y="{r*12}" width="12" height="12" fill="{ {"w": "#ffffff", "s": "#cfe3ff"}[ch]}"/>'
    for r, row in enumerate(CLOUD) for c, ch in enumerate(row) if ch != ".") + '</svg>')
EDGE = [(-70, 300, 1), (-90, 640, .8), (960, 190, .9), (985, 520, 1.1), (950, 800, .7), (-60, 830, .6)]   # clouds at the frame edges
FONTS = [("Jersey 15", 400, "normal", "jersey-15-latin-400-normal"), ("Hanken Grotesk", 600, "normal", "hanken-grotesk-latin-600-normal"),
         ("Hanken Grotesk", 700, "normal", "hanken-grotesk-latin-700-normal"), ("Hanken Grotesk", 800, "normal", "hanken-grotesk-latin-800-normal"),
         ("JetBrains Mono", 500, "normal", "jetbrains-mono-latin-500-normal"), ("JetBrains Mono", 700, "normal", "jetbrains-mono-latin-700-normal"),
         ("JetBrains Mono", 800, "normal", "jetbrains-mono-latin-800-normal")]


# ── drawing the guide and his props ──
def svg(rows, px=PX, cls="", ident=""):
    """A pixel grid as an SVG at its natural size (the guide's poses: 15 px a pixel)."""
    w, h = max(len(r) for r in rows) * px, len(rows) * px
    rects = "".join(f'<rect x="{c*px}" y="{r*px}" width="{px}" height="{px}" fill="{PAL[ch]}"/>'
                    for r, line in enumerate(rows) for c, ch in enumerate(line) if ch in PAL)
    return f'<svg {ident} class="{cls}" width="{w}" height="{h}" shape-rendering="crispEdges">{rects}</svg>'


def blk(rows, px=12):
    """A pixel prop that fills its box (a video block he carries, a book, a keyboard)."""
    w, h = len(rows[0]) * px, len(rows) * px
    rects = "".join(f'<rect x="{c*px}" y="{r*px}" width="{px}" height="{px}" fill="{PAL[ch]}"/>'
                    for r, line in enumerate(rows) for c, ch in enumerate(line) if ch in PAL)
    return f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" style="width:100%;height:100%;display:block" shape-rendering="crispEdges">{rects}</svg>'


def guide(poses=None):
    return '<div id="g">' + "".join(svg(POSES[p], PX, "pose", f'id="p-{p}"' + (f' style="bottom:-{LOW[p]}px"' if p in LOW else ''))
                                    for p in (poses or POSES)) + '</div>'


def guide2(poses):
    """His copy (he mimics himself, a beat late): #g2, poses shown with pose2()."""
    return '<div id="g2">' + "".join(svg(POSES[p], PX, "pose2", f'id="q-{p}"') for p in poses) + '</div>'


def peek(poses=("idle", "blink", "lookl")):
    """His head and hands for a peek over a card's top edge (#pk .pp, idle shown)."""
    return "".join(svg(POSES[q], PX, "pp", f'id="pk-{q}"' + ('' if q == poses[0] else ' style="display:none"')) for q in poses)


def frames(cls, ident, n, src):
    """An image sequence the timeline flips through (a real clip playing in a card): <img> per frame, the first shown."""
    return "".join(f'<img class="{cls}" id="{ident}{i}" src="{src}/{i+1:03d}.jpg" style="position:absolute;inset:0;width:100%;height:100%;'
                   f'object-fit:cover;display:{"block" if i == 0 else "none"}">' for i in range(n))


def count(img, folder): return len(list((pathlib.Path(img) / folder).glob("*.jpg")))


# ── captions ──
def chunks(words, end, fixed=()):
    """Caption chips: the hand-set chunks first, then 1-3 words a chip, broken at punctuation and pauses, 18 characters at most."""
    ch = list(fixed); i = ch[-1][1] + 1 if ch else 0
    while i < len(words):
        j = i
        while j + 1 < len(words) and j - i < 2 and not words[j]["text"].endswith((",", ".", "?")) \
                and words[j + 1]["start"] - words[j]["end"] < 0.3 and len(" ".join(w["text"] for w in words[i:j + 2])) <= 18:
            j += 1
        ch.append((i, j)); i = j + 1
    caps = []
    for k, (a, b) in enumerate(ch):
        t0 = words[a]["start"]; t1 = words[ch[k + 1][0]]["start"] if k + 1 < len(ch) else end
        caps.append(dict(t0=round(t0, 3), t1=round(t1, 3), txt=" ".join(words[i]["text"] for i in range(a, b + 1)).strip(".,?").upper()))
    return caps


# ── the page ──
def clouds(k):
    """The edge clouds of scene k (skipped in a rotation so no two scenes have the same sky)."""
    out = []
    for i, (x, y, s) in enumerate(EDGE):
        if (i + k) % 5 == 4: continue
        out.append(f'<div class="cloud" data-layout-allow-overflow data-i="{i}" data-s="{s}" style="left:{x}px;top:{y + (k * 23) % 60}px">'
                   f'<div style="transform:scale({s})">{CLOUD_SVG}</div></div>')
    return "".join(reversed(out))


def page(spec):
    words = json.load(open(spec.WORDS, encoding="utf-8"))
    caps = chunks(words, spec.END, getattr(spec, "CHUNKS", ()))
    k = iter(range(10 ** 6))
    scenes = re.sub(r'(<div class="scn"[^>]*>)', lambda m: m.group(1) + clouds(next(k)), spec.SCENES)
    scenes = scenes.replace('src="img/', 'src="assets/img/').replace('url(img/', 'url(assets/img/')
    faces = "".join(f'@font-face {{ font-family: "{fam}"; font-weight: {w}; font-style: {st}; src: url("assets/fonts/{f}.woff2") format("woff2"); }}\n'
                    for fam, w, st, f in FONTS)
    css = faces + (KIT / "sky.css").read_text(encoding="utf-8").replace("__STEP__", STEP)
    css += f"h1{{top:{getattr(spec, 'H1_TOP', TEXT_TOP)}px}}\n" + getattr(spec, "CSS", "")
    dust = svg(PROPS["dust"], 8)
    stage = (guide(getattr(spec, "POSES", None)) + (guide2(spec.POSES2) if getattr(spec, "POSES2", None) else "")
             + getattr(spec, "STAGE", "") + "".join(f'<div class="fx" id="d{i}">{dust}</div>' for i in range(4)))
    capdivs = "".join(f'<div class="cap" id="c{i}">{c["txt"]}</div>' for i, c in enumerate(caps))
    cid = "sky"
    media = (f'<video id="face" src="assets/face.mp4" data-start="0" data-duration="{spec.END}" muted playsinline></video>'
             f'<audio id="voice" src="assets/voice.m4a" data-start="0" data-duration="{spec.END}" data-volume="1"></audio>'
             f'<audio id="cues" src="assets/cues.wav" data-start="0" data-duration="{spec.END}" data-volume="1"></audio>')
    data = json.dumps({"ID": cid, "END": spec.END, "CAPS": caps})
    js = (KIT / "engine.js").read_text(encoding="utf-8").replace("/*__SHORT__*/", spec.JS)
    return ("<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=1080, height=1920'>"
            f"<script src='assets/vendor/gsap.min.js'></script><style>{css}</style></head><body>"
            f"<div id='root' data-composition-id='{cid}' data-start='0' data-width='1080' data-height='1920' data-duration='{spec.END}'>"
            f"{media}<div class='top'>{scenes}{stage}</div>{capdivs}</div>"
            f"<script>const D = {data};\n{js}</script></body></html>")


def build(spec):
    """Write the HyperFrames project: <OUT>/index.html + assets (fonts, gsap, images, face, voice, cues)."""
    out = pathlib.Path(spec.OUT); a = out / "assets"
    for d in ("fonts", "vendor"): (a / d).mkdir(parents=True, exist_ok=True)
    for _, _, _, f in FONTS: shutil.copy(KIT / "fonts" / f"{f}.woff2", a / "fonts")
    kit = REPO / "templates/ivory/build_kit"
    shutil.copy(kit / "assets/vendor/gsap.min.js", a / "vendor")
    for f in ("package.json", "hyperframes.json"): shutil.copy(kit / "project" / f, out / f)
    shutil.copytree(spec.IMG, a / "img", dirs_exist_ok=True)
    face = getattr(spec, "FACE4K", None) or spec.FACE                 # the 4K face when there is one: a 4K render supersamples it
    if not (a / "face.mp4").is_file() or (a / "face.mp4").stat().st_size != pathlib.Path(face).stat().st_size: shutil.copy(face, a / "face.mp4")
    shutil.copy(spec.VOICE, a / "voice.m4a")
    rep = bp.mix(spec, a / "cues.wav"); (out / "sound.txt").write_text("\n".join(rep), encoding="utf-8")
    (out / "index.html").write_text(page(spec), encoding="utf-8")
    return out


def main(spec, argv):
    """check | stills 3.9 8.2 ... | render [4k] | player | final <rev>: the commands blueprint has (bp.run), on this engine's build."""
    bp.run(spec, argv, build, "sky")
