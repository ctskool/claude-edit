"""Blueprint engine (Python side): drafting primitives, the HyperFrames project it writes, the sound mix, render via HyperFrames.
A short is a spec module (see examples/rea.py) that defines its regions and keyed moves and calls bp.main(spec).
Not a build.py look: the whole short is hand-built on this engine (LOOK.md beside this file)."""
import asyncio, json, math, pathlib, shutil, subprocess, sys, wave
import numpy as np
KIT = pathlib.Path(__file__).parent
REPO = KIT.parents[4]
SFX = REPO / "templates/ivory/sfx"
FPS, SR = 30, 48000
W, H, GX, GY = 1080, 998, 140, 140            # one region = the top half of the frame; gaps between regions
RED = '<b class="red">{}</b>'
TEXT_TOP = 150   # titles and the HUD start here, clear of the phone's status bar / Dynamic Island [Chase, 2026-11-20]


# ── drafting primitives (region-local coords). t = the second it draws; without t it drafts in with its region ──
def A(t): return f' data-t="{t}"' if t is not None else ""
def ln(x1, y1, x2, y2, c="l", ex="", t=None): return f'<line pathLength="1" class="{c}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" {ex}{A(t)}/>'
def pl(pts, c="l", ex="", t=None): return f'<polyline pathLength="1" class="{c}" fill="none" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" {ex}{A(t)}/>'
def rc(x, y, w, h, c="l", ex="", t=None): return f'<rect pathLength="1" class="{c}" x="{x}" y="{y}" width="{w}" height="{h}" {ex}{A(t)}/>'
def g(inner, t=None, ex=""): return f'<g{A(t)} {ex}>{inner}</g>'


def tx(x, y, s, size=20, anchor="start", c="tl", rot=None, t=None):
    """SVG label. c: tl white, tr red, ts soft."""
    r = f' transform="rotate({rot} {x} {y})"' if rot is not None else ""
    return f'<text class="{c}" x="{x}" y="{y}" font-size="{size}" font-weight="700" text-anchor="{anchor}"{r}{A(t)}>{s}</text>'


def dim_h(x1, x2, y, label, ext=None, red=False, t=None):
    """Horizontal dimension line with arrowheads; ext = y the extension lines start from."""
    c, m = ("r", "ahr") if red else ("t", "ah")
    s = (ln(x1, ext, x1, y + 10, "t") + ln(x2, ext, x2, y + 10, "t")) if ext is not None else ""
    s += ln(x1, y, x2, y, c, f'marker-start="url(#{m})" marker-end="url(#{m})"') + tx((x1 + x2) / 2, y - 10, label, 20, "middle", "tr" if red else "tl")
    return g(s, t)


def dim_v(x, y1, y2, label, ext=None, red=False, t=None):
    c, m = ("r", "ahr") if red else ("t", "ah")
    s = (ln(ext, y1, x - 10, y1, "t") + ln(ext, y2, x - 10, y2, "t")) if ext is not None else ""
    s += ln(x, y1, x, y2, c, f'marker-start="url(#{m})" marker-end="url(#{m})"') + tx(x - 12, (y1 + y2) / 2, label, 20, "middle", "tr" if red else "tl", -90)
    return g(s, t)


def leader(pts, red=False, t=None):
    return g(f'<circle class="{"dotr" if red else "dot"}" cx="{pts[0][0]}" cy="{pts[0][1]}" r="6"/>' + pl(pts, "r" if red else "l"), t)


def balloon(x, y, n, red=False, t=None):
    return g(f'<circle pathLength="1" class="{"r" if red else "l"} bfill" cx="{x}" cy="{y}" r="21"/>' + tx(x, y + 8, n, 22, "middle", "tr" if red else "tl"), t)


def ticks(x, y, w, h, gp=12, L=22, t=None):
    """Corner crop ticks just outside a plate."""
    s = ""
    for cx, cy, dx, dy in [(x, y, -1, -1), (x + w, y, 1, -1), (x, y + h, -1, 1), (x + w, y + h, 1, 1)]:
        s += ln(cx + dx * gp, cy, cx + dx * (gp + L), cy, "t") + ln(cx, cy + dy * gp, cx, cy + dy * (gp + L), "t")
    return g(s, t)


def cons(lines):
    """Faint dash-dot construction lines (x1, y1, x2, y2), shown first as a region drafts in."""
    return "".join(f'<line class="cn" x1="{a}" y1="{b}" x2="{c}" y2="{d}"/>' for a, b, c, d in lines)


def cloud(x, y, w, h, r=8, t=None):
    """A revision cloud (scalloped red outline) around a box."""
    pts, per = [], 2 * (w + h)
    n = int(per / (2 * r))
    for k in range(n + 1):
        q = k / n * per
        if q <= w: pts.append((x + q, y))
        elif q <= w + h: pts.append((x + w, y + q - w))
        elif q <= 2 * w + h: pts.append((x + w - (q - w - h), y + h))
        else: pts.append((x, y + h - (q - 2 * w - h)))
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f} " + " ".join(f"A{r},{r} 0 0 1 {px:.1f},{py:.1f}" for px, py in pts[1:])
    return g(f'<path pathLength="1" class="r" d="{d}"/>', t)


def revtri(x, y, s="A", t=None):
    """Revision triangle."""
    return g(f'<polygon pathLength="1" class="r bfill" points="{x},{y - 22} {x + 22},{y + 16} {x - 22},{y + 16}"/>' + tx(x, y + 10, s, 20, "middle", "tr"), t)


def plate(x, y, w, h, src, pos="center", duo=False, dev=None, t=None, ident="", cls=""):
    """A screenshot/footage plate. duo: blueprint duotone. dev=(t0, t1): duotone that develops into colour over t0..t1."""
    if dev:
        inner = (f'<img class="duoimg" src="{src}" style="object-position:{pos}">'
                 f'<img class="dev" data-t0="{dev[0]}" data-t1="{dev[1]}" src="{src}" style="position:absolute;inset:0;object-position:{pos};clip-path:inset(0 100% 0 0)">'
                 f'<i class="scan" style="left:0;opacity:0"></i>')
    else:
        inner = f'<img class="{"duoimg" if duo else ""}" src="{src}" style="object-position:{pos}">'
    return f'<div class="plate {cls}"{ident}{A(t)} style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">{inner}</div>'


def title(lines, x=60, y=TEXT_TOP, size=104, t=None):
    """Big Barlow Condensed headline; RED.format(word) for the accent. Wipes in outlined, then fills."""
    return f'<div class="h1"{A(t)} style="left:{x}px;top:{y}px;font-size:{size}px">{"<br>".join(lines)}</div>'


def note(x, y, s, size=22, color="var(--soft)", ex="", t=None, cls="note"):
    return f'<div class="{cls}"{A(t)} style="left:{x}px;top:{y}px;font-size:{size}px;color:{color};{ex}">{s}</div>'


def hand(x, y, s, size=38, t=None, rot=-4):
    """A handwritten red margin note (Caveat), for redlines."""
    return note(x, y, s, size, "var(--red)", f"font-family:Caveat;font-weight:500;letter-spacing:0;line-height:1;transform:rotate({rot}deg)", t)


def typed(text, t0, t1): return f'<span class="ty" data-text="{text}" data-t0="{t0}" data-t1="{t1}"></span>'


# ── page ──
def snake(cols, rows):
    """Region order: left-to-right, then right-to-left, so every camera move goes to a neighbour."""
    out = []
    for r in range(rows):
        cs = range(cols) if r % 2 == 0 else range(cols - 1, -1, -1)
        out += [(c, r) for c in cs]
    return out


def layout(spec):
    cells = snake(spec.COLS, spec.ROWS)[:len(spec.REGIONS)]
    orig = [(c * (W + GX) + 120, r * (H + GY) + 120) for c, r in cells]
    return orig, spec.COLS * W + (spec.COLS - 1) * GX + 240, spec.ROWS * H + (spec.ROWS - 1) * GY + 240


def chunks(spec):
    words = json.load(open(spec.WORDS, encoding="utf-8"))
    out, cur = [], []
    for k, w in enumerate(words):
        cur.append(w)
        nxt = words[k + 1] if k + 1 < len(words) else None
        txt = " ".join(x["text"] for x in cur)
        if (w["text"][-1] in ".,?!" or nxt is None or nxt["start"] - w["end"] > 0.3 or len(cur) >= 3
                or (nxt and len(txt) + 1 + len(nxt["text"]) > 18)):
            t = txt.rstrip(".,?!")
            for a, b in getattr(spec, "CAPTION_FIX", {}).items():
                t = t.replace(a, b)
            out.append((cur[0]["start"], cur[-1]["end"], t))
            cur = []
    return out


FONTS = [("Barlow Condensed", 600, "normal", "barlow-condensed-latin-600-normal"), ("Barlow Condensed", 700, "normal", "barlow-condensed-latin-700-normal"),
         ("Barlow Condensed", 800, "normal", "barlow-condensed-latin-800-normal"), ("Caveat", 500, "normal", "caveat-latin-500-normal"),
         ("JetBrains Mono", 600, "normal", "jetbrains-mono-latin-600-normal"), ("JetBrains Mono", 600, "italic", "jetbrains-mono-latin-600-italic"),
         ("JetBrains Mono", 700, "normal", "jetbrains-mono-latin-700-normal"), ("JetBrains Mono", 800, "normal", "jetbrains-mono-latin-800-normal")]


def page(spec):
    """The HyperFrames composition: one standalone root, the drawing on top, his face and voice framework-owned below."""
    orig, SW, SH = layout(spec)
    n = len(spec.REGIONS)
    regs = ""
    for i, fn in enumerate(spec.REGIONS):
        h, s = fn()
        x, y = orig[i]
        regs += f'<div class="reg" id="reg{i}" data-arr="{spec.ARR[i]}" style="left:{x}px;top:{y}px">{h}<svg class="ink" width="1080" height="998">{s}</svg></div>'
    mls, pens = "", ""
    for i in range(n - 1):
        (ax, ay), (bx, by) = orig[i], orig[i + 1]
        if ay == by:
            x = (ax + bx + W) / 2
            mls += f'<div class="match" style="left:{x - 10}px;top:{ay + 40}px;writing-mode:vertical-rl">MATCH LINE · SHEET {spec.SHEETNO[i]} → {spec.SHEETNO[i + 1]}</div>'
            mls += f'<div style="position:absolute;left:{x}px;top:{ay}px;width:0;height:{H}px;border-left:3px dashed rgba(234,243,255,.45)"></div>'
            sx = ax + (1040 if bx > ax else 40); ex = bx + (40 if bx > ax else 1040)
            path = f"M{sx},{ay + 930} L{x},{ay + 930} L{x},{by + 70} L{ex},{by + 70}"
        else:
            y = ay + H + GY / 2
            mls += f'<div class="match" style="left:{ax + 40}px;top:{y - 30}px">MATCH LINE · SHEET {spec.SHEETNO[i]} → {spec.SHEETNO[i + 1]}</div>'
            mls += f'<div style="position:absolute;left:{min(ax, bx)}px;top:{y}px;width:{W}px;height:0;border-top:3px dashed rgba(234,243,255,.45)"></div>'
            path = f"M{ax + 1000},{ay + 975} L{ax + 1000},{y} L{bx + 1000},{y} L{bx + 1000},{by + 30}"
        pens += f'<path id="pen{i}" pathLength="1" class="r" d="{path}" stroke-width="5" style="stroke-dasharray:1 1;stroke-dashoffset:1;opacity:0"/>'
    nib = ('<g id="nib" style="opacity:0"><g transform="rotate(-30)"><path d="M0,0 L-7,-26 L7,-26 Z" fill="#eaf3ff"/>'
           '<rect x="-11" y="-120" width="22" height="94" rx="4" fill="#eaf3ff"/><rect x="-11" y="-60" width="22" height="10" fill="#ff7a45"/></g></g>')
    creases = "".join(f'<div class="crease v" style="left:{SW * k // spec.COLS}px"></div>' for k in range(1, spec.COLS))
    creases += "".join(f'<div class="crease h" style="top:{SH * k // spec.ROWS}px"></div>' for k in range(1, spec.ROWS))
    border = f'<div style="position:absolute;left:40px;top:40px;width:{SW - 80}px;height:{SH - 80}px;border:4px solid rgba(234,243,255,.6);outline:2px solid rgba(234,243,255,.35);outline-offset:10px"></div>'
    marks = "".join(f'<div class="reg-mark" style="{p}"></div>' for p in ["left:12px;top:12px", "right:12px;top:12px", "left:12px;top:946px", "right:12px;top:946px"])
    nb = len(spec.BEATS)
    hud = f"<div id='hud'><div>{spec.HUD}</div>" + "".join(f"<div class='hudn' id='hn{k}'>SHEET {k + 1:02d} / {nb}</div>" for k in range(nb)) + "</div>"
    caps = chunks(spec)
    capdivs = "".join(f'<div class="capc" id="c{k}">{t}</div>' for k, (_, _, t) in enumerate(caps))
    faces = "".join(f'@font-face {{ font-family: "{fam}"; font-weight: {w}; font-style: {st}; src: url("assets/fonts/{f}.woff2") format("woff2"); }}\n' for fam, w, st, f in FONTS)
    css = faces + (KIT / "blueprint.css").read_text(encoding="utf-8").replace("__SW__", str(SW)).replace("__SH__", str(SH))
    css += "\n#root{position:relative;width:100%;height:100%;overflow:hidden;background:#000}\n#face{position:absolute;left:0;top:998px;width:1080px;height:922px;object-fit:cover;z-index:0}\n"
    css += f"#hud{{top:{getattr(spec, 'HUD_TOP', TEXT_TOP)}px}}\n"   # clear of the phone's status bar
    cid = "blueprint"
    data = json.dumps({"ID": cid, "ARR": spec.ARR, "ORIG": orig, "W": W, "H": H, "SW": SW, "SH": SH, "BEATS": spec.BEATS, "CAPS": caps,
                       "END": spec.END, "PULL_AT": getattr(spec, "PULL_AT", None)})
    media = (f'<video id="face" src="assets/face.mp4" data-start="0" data-duration="{spec.END}" muted playsinline></video>'
             f'<audio id="voice" src="assets/voice.m4a" data-start="0" data-duration="{spec.END}" data-volume="1"></audio>'
             f'<audio id="cues" src="assets/cues.wav" data-start="0" data-duration="{spec.END}" data-volume="1"></audio>')
    return ("<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=1080, height=1920'>"
            f"<script src='assets/vendor/gsap.min.js'></script><style>{css}</style></head><body>"
            f"<div id='root' data-composition-id='{cid}' data-start='0' data-width='1080' data-height='1920' data-duration='{spec.END}'>"
            f"{(KIT / 'defs.html').read_text(encoding='utf-8')}{media}"
            f"<div class='top'><div id='sheet' data-layout-allow-overlap>{border}{creases}{mls}{regs}<svg id='pens' width='{SW}' height='{SH}'>{pens}{nib}</svg></div>"
            f"{hud}{marks}{getattr(spec, 'ENDBLOCK', '')}<div id='grain'></div></div>{capdivs}</div>"
            f"<script>const D = {data};\n{getattr(spec, 'JS', '')}</script>"
            f"<script>{(KIT / 'engine.js').read_text(encoding='utf-8')}</script></body></html>")


def rd(path):
    with wave.open(str(path)) as w:
        n, ch, sr = w.getnframes(), w.getnchannels(), w.getframerate()
        a = np.frombuffer(w.readframes(n), np.int16).astype(float) / 32768
    a = a.reshape(-1, ch).mean(1)
    return np.interp(np.arange(int(len(a) * SR / sr)) * sr / SR, np.arange(len(a)), a) if sr != SR else a


def rms_db(x): return 20 * np.log10(max(1e-9, float(np.sqrt(np.mean(x ** 2)))))


def mix(spec, dst):
    """Few sounds, on his actions: vetted slices set by job against the voice (templates/ivory/sound.md levels) -> one cue track."""
    END = spec.END; voice = dst.parent / "_voice_probe.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(spec.VOICE), "-t", str(END), "-ac", "1", "-ar", str(SR), str(voice)], check=True)
    v = rd(voice); voice.unlink(); cues = np.zeros(int(SR * END) + SR * 4); rep = []
    for t, name, job, why in spec.SOUNDS:
        x = rd(SFX / f"{name}.wav"); att = int(np.argmax(np.abs(x) > 0.1 * np.abs(x).max())); win = int(0.25 * SR)
        i = max(0, int(t * SR) - att)
        vdb = max(rms_db(v[int(t * SR):int(t * SR) + win]), -26.0)
        y = x * 10 ** (((vdb - {"main": 11, "detail": 14}[job]) - rms_db(x[att:att + win])) / 20)
        if np.abs(y).max() > 10 ** (-8 / 20): y *= 10 ** (-8 / 20) / np.abs(y).max()
        cues[i:i + len(y)] += y
        rep.append(f"{t:6.2f} {name:22s} {job:6s} voice {vdb:6.1f} dB  ({why})")
    with wave.open(str(dst), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(cues[:int(SR * END)], -1, 1) * 32767).astype(np.int16).tobytes())
    return rep


def build(spec):
    """Write the HyperFrames project: <OUT>/index.html + assets (fonts, gsap, images, face, voice, cues)."""
    out = pathlib.Path(spec.OUT); a = out / "assets"
    for d in ("fonts", "vendor", "img"): (a / d).mkdir(parents=True, exist_ok=True)
    for _, _, _, f in FONTS: shutil.copy(KIT / "fonts" / f"{f}.woff2", a / "fonts")
    kit = REPO / "templates/ivory/build_kit"
    shutil.copy(kit / "assets/vendor/gsap.min.js", a / "vendor")
    for f in ("package.json", "hyperframes.json"): shutil.copy(kit / "project" / f, out / f)
    for f in pathlib.Path(spec.IMG).iterdir():
        if f.is_file() and not (a / "img" / f.name).is_file(): shutil.copy(f, a / "img")
    face = getattr(spec, "FACE4K", None) or spec.FACE                 # the 4K face when there is one: a 4K render supersamples it
    if not (a / "face.mp4").is_file() or (a / "face.mp4").stat().st_size != pathlib.Path(face).stat().st_size: shutil.copy(face, a / "face.mp4")
    shutil.copy(spec.VOICE, a / "voice.m4a")
    rep = mix(spec, a / "cues.wav"); (out / "sound.txt").write_text("\n".join(rep), encoding="utf-8")
    (out / "index.html").write_text(page(spec), encoding="utf-8")
    return out


def hf(cmd, cwd):
    print(">", cmd); return subprocess.run(f"npx --yes hyperframes@0.9.13 {cmd}", cwd=cwd, shell=True).returncode


def render(spec, out, k4=False):
    """HyperFrames render, then -14 LUFS. One heavy job at a time (tools/gpu_lock.py). Returns the finished file.
    In a player project (OUT = work/<id>/v2/<look>) it lands in renders/, which no round snapshots or restores."""
    sys.path.insert(0, str(REPO / "tools"))
    import gpu_lock
    raw = out / "renders" / f"{spec.NAME}{'_4k' if k4 else ''}_raw.mp4"; raw.parent.mkdir(exist_ok=True)
    with gpu_lock.held(f"{'4K' if k4 else 'review'} render {spec.NAME}"):
        rc = hf(f'render {"--resolution portrait-4k " if k4 else ""}-o "renders/{raw.name}"', out)
    if rc: sys.exit(rc)
    final = (raw.parent if out.parent.name == "v2" else out) / f"{spec.NAME}{'_4k30' if k4 else ''}.mp4"
    finish(raw, final)
    return final


def finish(raw, final):
    subprocess.run([sys.executable, str(REPO / "tools/finish.py"), str(raw), str(final), "--sheet", str(final.with_suffix(".sheet.jpg"))], check=True)


def run(spec, argv, build, engine):
    """The commands every hand-built look shares (sky calls this with its own build):
      check | stills 3.9 8.2 ... | render [4k]     as before: <OUT>/<NAME>[_4k30].mp4
      player                                       review render at 1080, loaded into the beat review player (tools/look_player.py)
      player --partial b04 b05                     experimental, slower than `player` today: only those beats filmed again (look_player.picture)
      final <composition_rev>                      the 4K final of the approved composition; his Approve click runs this (autofinal.py)"""
    out = build(spec)
    cmd = argv[0]
    if cmd == "check":
        sys.exit(hf("check", out))
    elif cmd == "stills":
        rc = hf(f'snapshot --at {",".join(argv[1:])} --no-end --keep -o "checks"', out)
        print("stills in", out / "checks"); sys.exit(rc)
    elif cmd == "render":
        print(render(spec, out, len(argv) > 1 and argv[1] == "4k"))
    elif cmd in ("player", "final"):
        sys.path.insert(0, str(REPO / "tools"))
        import look_player
        if cmd == "player":
            import gpu_lock
            with gpu_lock.held(f"review render {spec.NAME}"):
                if argv[1:] and argv[1] != "--partial":
                    sys.exit("`player` takes no beats: it renders the whole short. `player --partial b04 ...` exists but is slower today (tools/look_player.py)")
                mp4 = look_player.picture(spec, out, hf, finish, argv[2:])
            look_player.load(spec, mp4, engine)
        else:
            if look_player.file_hash(out / "index.html") != argv[1]:
                sys.exit("the spec no longer builds the approved composition: load it again with `player` and have him approve that")
            print("built 4k30:", render(spec, out, True))
    else:
        sys.exit(f"unknown command {cmd}: check | stills | render [4k] | player | final <rev>")


def main(spec, argv):
    run(spec, argv, build, "blueprint")
