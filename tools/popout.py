"""Popout bottom, shared by every template: Chase in a rounded card that runs off the frame's bottom edge, his real cut-out rising
above the card's top. Split beats only. Rule: templates/HOUSE.md "Popout bottom". Proof: work/1030-2-popout/POPOUT.md.

  python tools/popout.py make <project> [--final]

<project> is work/<id>/v2/<template>. Needs the clean camera (metadata.json "camera", "camera_crops") and the face frame map that
prep_source.py wrote. Reads the template's "popout" block from templates/<name>/template.json. Writes into the project:
  assets/popout_cam.mp4    the camera crop at review size, on the same frame map as face_half.mp4
  assets/popout_fg.webm    its cut-out (tools/matte.py, VP9 with alpha)
  assets/popout.json       the geometry the template's build reads
--final also writes the same two clips at twice the size to work/<id>/popout_final/, and swaps-popout.json listing them for
tools/beat_review/final.py --swaps. Fill in authorized_by when Chase approves the picture.

How the size is chosen: the card runs to the frame bottom, so the clip's height fixes its top, and the largest scale whose highest
measured head still clears the template's clear_y wins. The crop centres on his measured head and stays inside the camera.
The card edge then sits EDGE_GAP px under the median top of his head in the clip, so the head breaks it.
"""
import argparse, json, subprocess, sys
from pathlib import Path
import numpy as np

from paths import project_root
ROOT = project_root()
MATTE_PY = sys.executable
FRAME_W, FRAME_H, HALF = 1080, 1920, 960
EDGE_GAP = 65  # px the head rises above the card edge, at 1080x1920. Chase picked this look on 1030-2, 2026-11-02
FACE_LINE = 1440  # a face centre lower than this risks the platforms' caption block (the bottom quarter)
MEASURE_W = 960  # the whole camera, scaled to this width, for measuring
SAMPLE_FPS = 4


def run(cmd):
    subprocess.run([str(c) for c in cmd], check=True)


def even(v):
    return int(round(v / 2)) * 2


def template_of(project):
    """The template whose project folder this is. Folders use the tools' name, so ivory's is editorial."""
    for f in sorted((ROOT / "templates").glob("*/template.json")):
        t = json.loads(f.read_text(encoding="utf8"))
        if project.name in (t.get("name"), t.get("tool_name")):
            return t
    sys.exit(f"no template in templates/ owns a project folder named {project.name}")


def camera_of(home):
    meta = json.loads((home / "metadata.json").read_text(encoding="utf8"))
    if not meta.get("camera") or not meta.get("camera_crops"):
        sys.exit("popout needs the clean camera: metadata.json has no camera. Run prep_source.py with --camera first")
    w, h = meta["camera_size"]
    return Path(meta["camera"]), w, h, meta["camera_crops"]["half"]


def clip(home, camera, proxy, crop, size, out):
    """One crop of the camera on the face frame map, so it lines up frame for frame with face_half.mp4."""
    run([sys.executable, ROOT / "tools" / "face_retime.py", camera, "--map", home / "face_map.json", "--reuse", "--proxy-crop", proxy,
         "--crop", crop, "--scale", f"{size[0]}x{size[1]}", "--out", out])


def matte(src, out):
    run([MATTE_PY, ROOT / "tools" / "matte.py", src, out])


def alphas(webm, w, h):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", str(webm), "-vf", f"fps={SAMPLE_FPS},alphaextract,format=gray",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w) > 128


def head(masks):
    """Per sampled frame: top row of the cut-out, and the centre of the head band (top to about the chin)."""
    tops, centres, areas = [], [], []
    for m in masks:
        rows = m.any(1)
        if not rows.any():
            continue
        t = int(np.argmax(rows))
        band = np.nonzero(m[t:t + m.shape[0] // 4])[1]
        tops.append(t); centres.append(float(band.mean())); areas.append(int(m.sum()))
    return np.array(tops), np.array(centres), np.array(areas)


def flicker(areas):
    """Sampled frames whose cut-out area jumps by more than 15% from the one before: a sign of a bad edge."""
    jumps = np.abs(np.diff(areas)) / np.maximum(areas[:-1], 1)
    return int((jumps > 0.15).sum())


def measure(home, camera, cw, ch, proxy, tmp):
    """Where his head sits in the camera, in camera px, from the whole camera at small size."""
    mh = even(MEASURE_W * ch / cw)
    src, fg = tmp / "measure.mp4", tmp / "measure_fg.webm"
    clip(home, camera, proxy, f"{cw}:{ch}:0:0", (MEASURE_W, mh), src)
    matte(src, fg)
    tops, centres, _ = head(alphas(fg, MEASURE_W, mh))
    k = cw / MEASURE_W
    return {"head_top_min": float(tops.min() * k), "head_top_median": float(np.median(tops) * k), "head_cx": float(np.median(centres) * k)}


def geometry(m, spec, cw, ch):
    """The crop and the clip's place on the frame. The clip ends on the frame's bottom edge."""
    w = spec["card_w"]
    # clip_y = FRAME_H - ch * s, and clip_y + head_top_min * s >= clear_y
    s = min((FRAME_H - spec["clear_y"]) / (ch - m["head_top_min"]), spec.get("max_scale", 1.0))
    wc = min(w / s, cw)
    s = w / wc
    x0 = min(max(m["head_cx"] - wc / 2, 0), cw - wc)
    return {"crop": [round(wc), ch, round(x0), 0], "scale": round(s, 4), "card_x": spec["card_x"], "card_w": w,
            "clip_h": even(ch * s), "clip_y": FRAME_H - even(ch * s)}


def make(project, final):
    project = Path(project).resolve()
    home = project.parents[1]
    tpl = template_of(project)
    spec = tpl.get("popout")
    if not spec:
        sys.exit(f"template {tpl['name']} has no popout block in template.json, so it does not offer popout")
    camera, cw, ch, proxy = camera_of(home)
    tmp = home / "popout_work"; tmp.mkdir(exist_ok=True)
    m = measure(home, camera, cw, ch, proxy, tmp)
    g = geometry(m, spec, cw, ch)
    crop = ":".join(map(str, g["crop"]))
    assets = project / "assets"
    cam, fg = assets / "popout_cam.mp4", assets / "popout_fg.webm"
    clip(home, camera, proxy, crop, (g["card_w"], g["clip_h"]), cam)
    matte(cam, fg)
    tops, centres, areas = head(alphas(fg, g["card_w"], g["clip_h"]))
    edge = int(np.median(tops)) + EDGE_GAP
    g.update({"edge": edge, "radius": spec.get("radius", 36), "clear_y": spec["clear_y"], "card_css": spec.get("card_css", ""),
              "measured": {k: round(v, 1) for k, v in m.items()}, "head_top_y": [int(g["clip_y"] + tops.min()), int(g["clip_y"] + np.median(tops))],
              "flicker_samples": flicker(areas), "samples": int(len(areas)), "cam": "assets/popout_cam.mp4", "fg": "assets/popout_fg.webm"})
    face_y = g["clip_y"] + np.median(tops) + 0.3 * ch * g["scale"]  # eyes sit about 0.3 of the camera height under the head top in his framing
    warn = []
    if g["head_top_y"][0] < spec["clear_y"]:
        warn.append(f"head reaches y {g['head_top_y'][0]}, above clear_y {spec['clear_y']}")
    if face_y > FACE_LINE:
        warn.append(f"face centre near y {face_y:.0f}, in the platforms' caption block")
    if g["flicker_samples"]:
        warn.append(f"{g['flicker_samples']} of {g['samples']} samples jump in cut-out area: check the edge by eye, and use split for this video if it halos or flickers")
    g["warnings"] = warn
    (assets / "popout.json").write_text(json.dumps(g, indent=1), encoding="utf8")
    print(f"popout: crop {crop} (scale {g['scale']}), clip {g['card_w']}x{g['clip_h']} at y {g['clip_y']}, card edge {edge} px into it, head top y {g['head_top_y']}")
    for w_ in warn:
        print("WARN", w_)
    if final:
        out = home / "popout_final"; out.mkdir(exist_ok=True)
        size = (2 * g["card_w"], 2 * g["clip_h"])
        clip(home, camera, proxy, crop, size, out / "popout_cam.mp4")
        matte(out / "popout_cam.mp4", out / "popout_fg.webm")
        rows = [{"path": g[k], "file": str(out / Path(g[k]).name), "source": f"{camera.name} crop {crop}, 2x the review size", "why": "the final's popout at full size",
                 "authorized_by": ""} for k in ("cam", "fg")]
        (home / "swaps-popout.json").write_text(json.dumps({"swaps": rows}, indent=1), encoding="utf8")
        print("final clips in", out, "and swaps-popout.json: fill in authorized_by before final.py")


# ---------- what a template's build puts on the page ----------

def css(g):
    """Overrides the split face rules. #face-wrap keeps filling the bottom half, because tools/beat_render/refs.mjs checks that box."""
    top = g["clip_y"] - HALF
    r = g["radius"]
    return f'''      /* popout bottom, tools/popout.py */
      #face-wrap {{ position: absolute; left: 0; top: {HALF}px; width: {FRAME_W}px; height: {HALF}px; z-index: 1; overflow: visible; background: none; }}
      #panel-bg {{ position: absolute; left: {g["card_x"]}px; top: {top + g["edge"]}px; width: {g["card_w"]}px; height: {HALF - top - g["edge"] + r}px; border-radius: {r}px {r}px 0 0; {g["card_css"]} }}
      #panel-clip {{ position: absolute; left: {g["card_x"]}px; top: {top}px; width: {g["card_w"]}px; height: {g["clip_h"]}px; clip-path: inset({g["edge"]}px 0 0 0 round {r}px {r}px 0 0); }}
      #face {{ position: absolute; left: 0; top: 0; width: {g["card_w"]}px; height: {g["clip_h"]}px; object-fit: fill; }}
      #face-fg {{ position: absolute; left: {g["card_x"]}px; top: {top}px; width: {g["card_w"]}px; height: {g["clip_h"]}px; }}
'''


def markup(g, end):
    return (f'<div id="face-wrap"><div id="panel-bg"></div><div id="panel-clip"><video id="face" class="clip" src="{g["cam"]}" muted playsinline data-start="0" '
            f'data-duration="{end}" data-track-index="0"></video></div><video id="face-fg" class="clip" src="{g["fg"]}" muted playsinline data-start="0" '
            f'data-duration="{end}" data-track-index="1"></video></div>')


def twin(js):
    """Every tween on #face gets the same tween on #face-fg on the next line, so a punch-in moves the cut-out with the picture."""
    out = []
    for line in js.split("\n"):
        out.append(line)
        if 'tl.' in line and '("#face",' in line:
            out.append(line.replace('("#face",', '("#face-fg",', 1))
    return "\n".join(out)


def roots(extra):
    """A scene that may move #face may also move #face-fg."""
    return {k: (v + ["#face-fg"] if "#face" in v and "#face-fg" not in v else v) for k, v in extra.items()}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=["make"])
    ap.add_argument("project")
    ap.add_argument("--final", action="store_true")
    a = ap.parse_args()
    make(a.project, a.final)
