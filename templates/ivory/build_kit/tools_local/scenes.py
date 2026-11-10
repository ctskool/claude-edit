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


def _ground_text(cols=119, rows=9, seed=3):
    """A strip of ASCII terrain, the charcoal look's texture. Deterministic."""
    def h(i, j, s):
        x = (i * 374761393 + j * 668265263 + s * 1442695041) & 0xFFFFFFFF
        x = ((x ^ (x >> 13)) * 1274126177) & 0xFFFFFFFF
        return (x ^ (x >> 16)) / 4294967295
    out = []
    for j in range(rows):
        line = ""
        for i in range(cols):
            u, v = i / 146, j / rows
            y0 = 0.36 + math.sin(u * 5 + seed) * 0.24 + math.sin(u * 13 + seed * 2) * 0.11 + math.sin(u * 31 + seed) * 0.05
            n, dd = h(i, j, seed), v - y0
            line += " " if dd <= 0 or n <= 0.1 else ("." if n > 0.55 else ":") if dd < 0.07 else "-" if dd < 0.2 else "=" if dd < 0.36 else "+" if dd < 0.56 else "#"
        out.append(line)
    return "\n".join(out)


def ground(p, full=False):
    """A look's ground band, as the scene root's first child: the densest rows on a split panel's base, all nine on a takeover's.
    Its drift is one line in the scene's block, on the video's clock so it never jumps between scenes (looks/charcoal/LOOK.md)."""
    top, hgt, off = (1704, 216, 0) if full else (884, 76, -140)
    return f'<div class="gclip" style="top:{top}px;height:{hgt}px"><div id="{p}-gr" class="gr" style="top:{off}px">{_ground_text()}</div></div>'


def own(id_, html):
    """One scene group, marked for tools/beat_render/ownership.py"""
    return f"<!--@own scene.{id_}-->\n{html}\n<!--@/own-->"


def build():
    S = []
    # @SCENES
    return "\n".join(S)
