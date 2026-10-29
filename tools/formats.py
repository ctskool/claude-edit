"""Format library glue: one prepped video (claude-edit contract) -> HyperFrames projects for the ported pack formats.

Usage (run from the repo root):
  python tools/formats.py media  <id>                      shared media for every format  -> work/<id>/formats/_media/
  python tools/formats.py new    <id> <format> [--title T] scaffold work/<id>/formats/<format>/ (never overwrites build.py)
  python tools/formats.py render <id> <format> [--draft]   build.py -> hyperframes check -> render -> sound -> out/<id>_fmt-<format>.mp4
  python tools/formats.py gallery <id>                     out/<id>-formats.html: the cut, every style and every format side by side
  python tools/formats.py list                             the formats and what each one needs

Formats live in formats/<name>/: the Creator Skill Pack skills bundled in pack/ (rotation, frost, popout), imported and
patched for Windows + macOS by `python tools/import_formats.py`, filled with your brand (config/profile.json ->
formats/profile/profile.json) by their setup/apply_profile.py; see formats/README.md.

THE CONTRACT - what every format may read from work/<id>/ (written by tools/rawcut.py + tools/prep_source.py, and by the
recut-plan workflow for the content):
  raw/cut.mp4        tight cut, split composite, carries the voice          raw/cam_cut.mp4  clean 4K camera, same frames
  raw/cut_words.json [[text, start, end, i]] on the cut clock              raw/cuts.json    joins {t, removed, kind, big}
  raw/edl.json, raw/edit.wav                                               words.json       [{i, text, start, end}]
  assets/face_full.mp4 (1080x1920), face_half.mp4 (1280x1092), face_wide.mp4 (1920x1080): 30 fps, re-timed, from the camera
  assets/voice.m4a   metadata.json (split_crop_in_camera, camera_crops)    face_map.json (60 -> 30 fps frame map)
  facts.json, ASSETS.md, shared/ (shots, clips, logos), beats.json         (content plan; formats read, never write)
"""
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FMT = os.path.join(ROOT, "formats")
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)
from common import chrome_path, matte_python, profile  # noqa: E402

MATTE_PY = matte_python()
GSAP = os.path.join(ROOT, "node_modules", "gsap", "dist", "gsap.min.js")
PROFILE = os.path.join(FMT, "profile")
FIX = profile().get("caption_fixes", {})   # misheard names on screen, e.g. {"Kimmy": "Kimi"} (config/profile.json)
# the imported pack scripts find the cut-out tool and Chrome through these (tools/import_formats.py rules)
ENV = dict(os.environ, PYTHONUTF8="1", CREATOR_PROFILE_DIR=PROFILE, CLAUDE_EDIT_ROOT=ROOT, CLAUDE_EDIT_PY=MATTE_PY,
           CLAUDE_EDIT_CHROME=chrome_path() or "")
if not os.path.isdir(os.path.join(FMT, "business-short-form-reels")) and sys.argv[1:2] != ["list"]:
    sys.exit("No layout formats installed yet (rotation, frost, popout). Install them with:\n"
             "  python tools/import_formats.py")

FORMATS = {
    "business": dict(skill="business-short-form-reels",
                     what="rotation: face full screen / split (graphics top, face bottom) / full-screen animation; glass pills, real UIs"),
    "panel": dict(skill="explainer-panel-reel",
                  what="you in a rounded panel at the bottom (head pops above it), headings + diagrams building above; close-ups"),
    "glass": dict(skill="glass-explainer-reel",
                  what="the panel layout with business graphics on rectangular glass cards (notifications, docs, channel cards, graphs)"),
}
# panel-style formats (the skill's own crop / caption scripts, a project built by build.py with the skill's engine)
PANEL_LIKE = {
    "panel": dict(crop="06_crops.py", media=("cam_full.mp4", "cam_panel.mp4", "cam_panel_fg.webm"), crops="crops.json",
                  engine=("panel_engine.py",)),
    "glass": dict(crop="06_crops.py", media=("cam_full.mp4", "cam_panel.mp4", "cam_panel_fg.webm"), crops="crops.json",
                  engine=("glass_engine.py", "glass_kit.py"), avatar=True),
}


def run(cmd, **kw):
    print(">", " ".join(str(c) for c in cmd)[:220], file=sys.stderr)
    return subprocess.run([str(c) for c in cmd], check=True, env=ENV, **kw)


def probe(path, entries="format=duration"):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", entries, "-of", "json", path],
                         check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def dur(path):
    return float(probe(path)["format"]["duration"])


def link(src, dst):
    """Hard link (same NTFS volume, no admin needed, no copy); falls back to a copy."""
    if os.path.lexists(dst):
        os.remove(dst)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def W(vid, *p):
    return os.path.join(ROOT, "work", vid, *p)


def words_seconds(vid):
    """[[start, end, word], ...] on the cut clock from words.json (the cut's own transcript), names fixed."""
    ws = json.load(open(W(vid, "words.json"), encoding="utf-8")); out = []
    for w in ws:
        t = w["text"]
        if out and re.match(r"^\.\d", t) and re.search(r"\d$", out[-1][2]):     # Whisper splits decimals: "5" ".5," -> "5.5,"
            out[-1][2] += t; out[-1][1] = w["end"]
            continue
        out.append([w["start"], w["end"], FIX.get(t, t)])
    return out


# ------------------------------------------------------------------------------------------------------------- media
def face_geometry(video, n=9):
    """Median face box over n frames of the 4K camera cut (OpenCV Haar): cx, top of hair (estimated), chin, in source px."""
    import cv2
    import numpy as np
    det = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
    d = dur(video); boxes = []
    for k in range(n):
        t = d * (k + 0.5) / n
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1", "-vf", "scale=960:-2",
                              "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
        h = len(raw) // 960
        g = np.frombuffer(raw, np.uint8).reshape(h, 960)
        f = det.detectMultiScale(g, 1.1, 6, minSize=(120, 120))
        if len(f):
            x, y, w, hh = max(f, key=lambda b: b[2] * b[3]); boxes.append((x, y, w, hh))
    if not boxes:
        sys.exit("no face found in the camera cut")
    s = probe(video, "stream=width,height")["streams"][0]["width"] / 960
    x, y, w, h = (float(np.median([b[i] for b in boxes])) for i in range(4))
    # Haar box: mid-forehead to the mouth. Measured on the author's 4K framing (2026-10-24): hair top ~0.35 box heights above it,
    # chin ~0.22 box heights below it.
    return {"cx": round((x + w / 2) * s), "top": round(max(0, y - 0.35 * h) * s), "chin": round((y + h * 1.22) * s),
            "box": [round(v * s) for v in (x, y, w, h)], "frames": len(boxes)}


def media(vid):
    M = W(vid, "formats", "_media"); os.makedirs(M, exist_ok=True)
    A = W(vid, "assets"); R = W(vid, "raw")
    for f in ("face_full.mp4", "face_half.mp4", "face_wide.mp4", "voice.m4a"):
        if not os.path.exists(os.path.join(A, f)):
            sys.exit(f"missing assets/{f}: run tools/prep_source.py on raw/cut.mp4 first")
    D = dur(os.path.join(R, "cut.mp4"))
    # full-screen face (business FACE windows) = prep's face_full; its cut-out on the GPU
    link(os.path.join(A, "face_full.mp4"), os.path.join(M, "cam_full.mp4"))
    if not os.path.exists(os.path.join(M, "cam_fg.webm")):
        run([MATTE_PY, os.path.join(TOOLS, "matte.py"), os.path.join(M, "cam_full.mp4"), os.path.join(M, "cam_fg.webm")])
    # split face (business): 9:8 1080x960 from face_half (1280x1092), carries the voice
    run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(A, "face_half.mp4"), "-i", os.path.join(A, "voice.m4a"),
         "-map", "0:v", "-map", "1:a", "-vf", "scale=1125:960:flags=lanczos,crop=1080:960", "-c:v", "libx264", "-crf", "15",
         "-g", "30", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart",
         os.path.join(M, "cam_top.mp4")])
    # 16:9 camera cut at 30 fps (panel format source): 4K camera re-timed through the same unique-frame map, + the voice
    c16 = os.path.join(M, "cut16x9.mp4")
    if not os.path.exists(c16):
        meta = json.load(open(W(vid, "metadata.json"), encoding="utf-8"))
        tmp = os.path.join(M, "_cam30.mp4")
        run([sys.executable, os.path.join(TOOLS, "face_retime.py"), meta.get("camera") or meta["source"], "--map", W(vid, "face_map.json"), "--reuse",
             "--proxy-crop", meta["camera_crops"]["half"], "--crop", meta["camera_crops"]["wide"], "--out", tmp])
        run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-i", os.path.join(A, "voice.m4a"), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
             "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", c16])
        os.remove(tmp)
    geo = face_geometry(c16)
    words = words_seconds(vid)
    json.dump(words, open(os.path.join(M, "words_sew.json"), "w", encoding="utf-8"))
    info = {"id": vid, "dur": round(D, 3), "fps": 30, "face_16x9": geo, "words": len(words),
            "big_cuts": [c["t"] for c in json.load(open(os.path.join(R, "cuts.json"))) if c["big"]]}
    json.dump(info, open(os.path.join(M, "media.json"), "w"), indent=1)
    print(json.dumps(info, indent=1))


# ------------------------------------------------------------------------------------------------------------- scaffold
def base_project(P, skill, name):
    os.makedirs(os.path.join(P, "assets", "fonts"), exist_ok=True)
    os.makedirs(os.path.join(P, "renders"), exist_ok=True)
    for f in os.listdir(os.path.join(FMT, skill, "assets", "fonts")):
        shutil.copy2(os.path.join(FMT, skill, "assets", "fonts", f), os.path.join(P, "assets", "fonts", f))
    shutil.copy2(GSAP, os.path.join(P, "assets", "gsap.min.js"))
    json.dump({"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
               "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
               "media": {"autoProxy": True}}, open(os.path.join(P, "hyperframes.json"), "w"), indent=2)
    json.dump({"id": name, "name": name}, open(os.path.join(P, "meta.json"), "w"))
    json.dump({"name": name, "private": True, "type": "module"}, open(os.path.join(P, "package.json"), "w"))


def new(vid, fmt, title):
    spec = FORMATS[fmt]; skill = spec["skill"]; S = os.path.join(FMT, skill)
    M = W(vid, "formats", "_media"); P = W(vid, "formats", fmt)
    info = json.load(open(os.path.join(M, "media.json")))
    D = info["dur"]
    json.dump(words_seconds(vid), open(os.path.join(M, "words_sew.json"), "w", encoding="utf-8"))   # always the current fixes (decimals, names)
    base_project(P, skill, f"{vid}-{fmt}")
    if fmt == "business":
        shutil.copy2(os.path.join(S, "assets", "brand.css"), os.path.join(P, "assets", "brand.css"))
        for f in ("reel_engine.py", "kit.py", "mix.py"):
            shutil.copy2(os.path.join(S, "engine", f), os.path.join(P, f))
        shutil.copy2(os.path.join(PROFILE, "assets", "sfx_map.json"), os.path.join(P, "sfx_map.json"))
        for f in ("cam_top.mp4", "cam_full.mp4", "cam_fg.webm"):
            link(os.path.join(M, f), os.path.join(P, "assets", f))
        shutil.copy2(os.path.join(M, "words_sew.json"), os.path.join(P, "words.json"))
        if not os.path.exists(os.path.join(P, "build.py")):
            t = open(os.path.join(S, "templates", "build.py"), encoding="utf-8").read()
            open(os.path.join(P, "build.py"), "w", encoding="utf-8").write(t.replace("__TITLE__", title).replace("__DUR__", str(D)))
    elif fmt in PANEL_LIKE:
        new_panellike(vid, fmt, P, S, M, info, title)
    print(f"project {P} ({D:.2f}s). Next: write build.py (formats/{skill}/SKILL.md + its examples), then: "
          f"python tools/formats.py render {vid} {fmt} --draft")


def make_avatar(vid):
    """your profile picture for channel/post cards: config/avatar.jpg if present, else a square face crop from your own camera (profile/assets/avatar.jpg)."""
    av = os.path.join(PROFILE, "assets", "avatar.jpg")
    if os.path.exists(av):
        return av
    M = W(vid, "formats", "_media"); g = json.load(open(os.path.join(M, "media.json")))["face_16x9"]
    x, y, w, h = g["box"]; side = int(w * 1.7) // 2 * 2; cy = y + h // 2
    run(["ffmpeg", "-v", "error", "-y", "-ss", "20", "-i", os.path.join(M, "cut16x9.mp4"), "-frames:v", "1", "-vf",
         f"crop={side}:{side}:{g['cx'] - side // 2}:{max(0, cy - side // 2)},scale=400:400", "-q:v", "2", av])
    return av


def new_panellike(vid, fmt, P, S, M, info, title):
    """A panel-style skill's own steps 6-8 (framing + cut-out, captions, project) on our contract. Its work dir = <P>/_work."""
    spec = PANEL_LIKE[fmt]
    PW = os.path.join(P, "_work"); os.makedirs(PW, exist_ok=True)
    R = W(vid, "raw")
    for f in ("edl.json", "cuts.json", "edit.wav", "words.txt"):
        if os.path.exists(os.path.join(R, f)):
            shutil.copy2(os.path.join(R, f), os.path.join(PW, f))
    cw = [[FIX.get(w[2], w[2]), w[0], w[1], i] for i, w in enumerate(words_seconds(vid))]   # [text, start, end, i] (panel shape)
    json.dump(cw, open(os.path.join(PW, "cut_words.json"), "w", encoding="utf-8"))
    c16 = os.path.join(M, "cut16x9.mp4"); s = probe(c16, "stream=width,height")["streams"][0]
    json.dump({"w": s["width"], "h": s["height"], "fps": "30/1", "src": c16, "cut": c16, "out": os.path.join(M, fmt),
               "stem": vid, "cut_dur": info["dur"]}, open(os.path.join(PW, "meta.json"), "w"), indent=1)
    g = info["face_16x9"]
    if not os.path.exists(os.path.join(PW, "layout.json")):
        json.dump({"face": {"cx": g["cx"], "top": g["top"], "chin": g["chin"]}, "popout": True}, open(os.path.join(PW, "layout.json"), "w"), indent=1)
    sc = os.path.join(S, "scripts")
    H = os.path.join(M, fmt, "hf-media")
    if not os.path.exists(os.path.join(H, spec["media"][-1])):
        run([sys.executable, os.path.join(sc, spec["crop"]), PW])
    if not os.path.exists(os.path.join(PW, "captions.json")):
        subprocess.run([sys.executable, os.path.join(sc, "07_captions.py"), PW], env=ENV)   # first run drafts phrases.txt and stops
    for f in spec["media"]:
        if os.path.exists(os.path.join(H, f)):
            link(os.path.join(H, f), os.path.join(P, "assets", f))
    for f in spec["engine"]:
        shutil.copy2(os.path.join(S, "engine", f), os.path.join(P, f))
    for f in os.listdir(os.path.join(S, "assets")):                           # image assets the engine expects
        if f.endswith(".png"):
            shutil.copy2(os.path.join(S, "assets", f), os.path.join(P, "assets", f))
    if os.path.exists(os.path.join(PROFILE, "assets", "sfx_map.json")):
        shutil.copy2(os.path.join(PROFILE, "assets", "sfx_map.json"), os.path.join(P, "sfx_map.json"))
    extra = {}
    if spec.get("avatar"):                                                    # glass: channel / notification cards
        os.makedirs(os.path.join(P, "assets", "proof"), exist_ok=True)
        shutil.copy2(make_avatar(vid), os.path.join(P, "assets", "proof", "avatar.jpg")); extra["avatar"] = "profile"
    sys.path.insert(0, sc)
    for m in [k for k in sys.modules if k in ("common", "stt")]:                # each skill has its own common.py
        del sys.modules[m]
    from common import brand                                                   # the skill's brand.json from the profile
    json.dump(brand(PW), open(os.path.join(P, "assets", "brand.json"), "w"), indent=1)
    sys.path.remove(sc)
    for f in ("captions.json", "cut_words.json", "cuts.json"):
        if os.path.exists(os.path.join(PW, f)):
            shutil.copy2(os.path.join(PW, f), os.path.join(P, f))
    C = json.load(open(os.path.join(PW, spec["crops"])))
    pj = os.path.join(P, "project.json")
    if title == vid and os.path.exists(pj):                  # a refresh without --title keeps the title given at scaffold time
        title = json.load(open(pj, encoding="utf-8")).get("title", title)
    geo = {"panel": C["pn"], "cap": C["cap"], "popout": C["popout"]} if "pn" in C else {"me": C["me"], "cap": C["cap"]}
    json.dump({"title": title, "slug": vid, "work": PW, "out": os.path.join(P, "renders"), "stem": vid, "dur": info["dur"], "fps": 30.0,
               "fps_str": "30/1", **geo, **extra}, open(os.path.join(P, "project.json"), "w"), indent=1)
    if not os.path.exists(os.path.join(P, "build.py")):
        open(os.path.join(P, "build.py"), "w", encoding="utf-8").write(
            open(os.path.join(S, "templates", "build.py"), encoding="utf-8").read().replace("__TITLE__", title))


# ------------------------------------------------------------------------------------------------------------- render
def render(vid, fmt, draft):
    P = W(vid, "formats", fmt); M = W(vid, "formats", "_media"); out = os.path.join(ROOT, "out")
    tag = f"{vid}_fmt-{fmt}" + ("_draft" if draft else "")
    run([sys.executable, "build.py"], cwd=P)
    chk = subprocess.run("npx hyperframes check", cwd=P, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    bad = [l for l in re.sub(r"\x1b\[[0-9;]*m", "", chk.stdout + chk.stderr).splitlines() if "✗" in l and "text_occluded" not in l]
    print("\n".join(bad[:25]) or "check: no errors (text_occluded behind the head is intended)")
    raw = os.path.join(P, "renders", tag + ".mp4")
    r = subprocess.run(f'npx hyperframes render --fps 30 --quality {"draft" if draft else "looks"} -o "{raw}"', cwd=P, shell=True,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    if r.returncode or not os.path.exists(raw):
        sys.exit("render failed:\n" + re.sub(r"\x1b\[[0-9;]*m", "", r.stdout + r.stderr)[-1500:])
    voiced = os.path.join(P, "renders", tag + "_voice.mp4")
    has_audio = any(s.get("codec_type") == "audio" for s in probe(raw, "stream=codec_type")["streams"])
    if has_audio:
        shutil.copy2(raw, voiced)
    else:                                                   # a silent render: put the cut's voice under it
        run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-i", W(vid, "assets", "voice.m4a"), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
             "-c:a", "aac", "-b:a", "256k", "-shortest", voiced])
    final = voiced
    if fmt == "business" and os.path.exists(os.path.join(P, "sfx.json")):        # the kit's sound plan (K.flush) -> mix.py
        mixed = mix_business(P, voiced, tag)
        final = mixed or voiced
    os.makedirs(out, exist_ok=True)
    run([sys.executable, os.path.join(TOOLS, "finish.py"), final, os.path.join(out, tag + ".mp4"), "--sheet", os.path.join(out, tag + "-sheet.jpg")])
    print("wrote", os.path.join(out, tag + ".mp4"))


def mix_business(P, voiced, tag):
    """mix.py reads '<OUT>/<Title> - 9x16 Reel (<stem> - no SFX).mp4' plus 'renders/<Title> (<stem> - no SFX) (phone).mp4' and writes
    '... (<stem> - no music).mp4' next to each; feed it the voiced render under those names in a scratch folder."""
    mx = os.path.join(P, "renders", "_mix"); os.makedirs(mx, exist_ok=True)
    link(voiced, os.path.join(mx, "reel - 9x16 Reel (v - no SFX).mp4"))
    link(voiced, os.path.join(P, "renders", "reel (v - no SFX) (phone).mp4"))
    r = subprocess.run([sys.executable, "mix.py", mx, "reel", "v"], cwd=P, capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    print(r.stdout[-800:], r.stderr[-800:])
    out = os.path.join(mx, "reel - 9x16 Reel (v - no music).mp4")
    return out if os.path.exists(out) else None


def gallery(vid):
    """out/<id>-formats.html: every version of one video side by side - the tight cut, the latest render of each style, each format."""
    import glob
    import html
    out = os.path.join(ROOT, "out"); cards = []
    rel = lambda p: os.path.relpath(p, out).replace("\\", "/")
    cut = W(vid, "raw", "cut.mp4")
    if os.path.exists(cut):
        cards.append(("the tight cut", "raw take after tools/rawcut.py (no graphics)", rel(cut), None))
    styles = {}
    for mp4 in glob.glob(os.path.join(out, f"{vid}_*_v*.mp4")):
        m = re.match(rf"{re.escape(vid)}_([a-z]+)_v(\d+)\w*\.mp4$", os.path.basename(mp4))
        if m and int(m.group(2)) >= styles.get(m.group(1), (0, ""))[0]:
            styles[m.group(1)] = (int(m.group(2)), mp4)
    for st, (n, mp4) in sorted(styles.items()):
        sheet = mp4[:-4] + "-sheet.jpg"
        cards.append((f"style: {st} v{n}", "claude-edit style (split screen, graphics on top)", rel(mp4), rel(sheet) if os.path.exists(sheet) else None))
    for k, v in FORMATS.items():
        for tag in (f"{vid}_fmt-{k}", f"{vid}_fmt-{k}_draft"):
            mp4 = os.path.join(out, tag + ".mp4")
            if os.path.exists(mp4):
                sheet = os.path.join(out, tag + "-sheet.jpg")
                cards.append((f"format: {k}" + (" (draft)" if tag.endswith("_draft") else ""), v["what"], rel(mp4),
                              rel(sheet) if os.path.exists(sheet) else None))
                break
    figs = "".join(f"<figure><figcaption><b>{html.escape(t)}</b><br>{html.escape(d)}</figcaption><video controls preload=metadata src='{s}'></video>"
                   + (f"<img src='{sh}'>" if sh else "") + "</figure>" for t, d, s, sh in cards)
    page = ("<!doctype html><meta charset=utf-8><title>" + html.escape(vid) + " - every edit</title><style>"
            "body{font:14px system-ui;margin:24px;background:#111;color:#eee}.row{display:flex;gap:18px;overflow-x:auto;align-items:flex-start}"
            "figure{margin:0;flex:0 0 auto;width:300px}video{width:300px;display:block;margin-top:6px;border-radius:8px}"
            "img{width:300px;display:block;margin-top:6px}figcaption{font-size:12px;color:#bbb;min-height:48px}button{font:14px system-ui;padding:8px 14px}"
            "</style><h1>" + html.escape(vid) + " - the same recording, every edit</h1><p><button onclick=\"document.querySelectorAll('video')"
            ".forEach(v=>{v.currentTime=0;v.muted=true;v.play()});document.querySelector('video').muted=false\">play all together (sound on the first)</button></p>"
            "<div class=row>" + figs + "</div>")
    path = os.path.join(out, f"{vid}-formats.html")
    open(path, "w", encoding="utf-8").write(page)
    print(path, f"({len(cards)} versions)")


def main():
    for s in (sys.stdout, sys.stderr):              # piped output on Windows is cp1252; hyperframes check prints ✗ / ⚠
        s.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    if not a or a[0] == "list":
        for k, v in FORMATS.items():
            print(f"{k:9s} formats/{v['skill']:28s} {v['what']}")
        return
    cmd, vid = a[0], a[1]
    if cmd == "media":
        media(vid)
    elif cmd == "new":
        title = a[a.index("--title") + 1] if "--title" in a else vid
        new(vid, a[2], title)
    elif cmd == "render":
        render(vid, a[2], "--draft" in a)
    elif cmd == "gallery":
        gallery(vid)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
