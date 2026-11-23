#!/usr/bin/env python3
"""Sets up work/<id>/full, a charcoal (16:9 long-form) project, from this kit. README.md beside this file says what comes next.

  python templates/charcoal/build_kit/new_project.py <id> --check-face --crop W:H:X:Y     # one still, before anything else
  python templates/charcoal/build_kit/new_project.py <id> --crop W:H:X:Y [--radius 0] [--series rule:10] [--docs-site host/path]
  python templates/charcoal/build_kit/new_project.py <id> --quick --crop W:H:X:Y ...       # seconds: as soon as `rawcut.py cut` has run
  python templates/charcoal/build_kit/new_project.py <id> --refresh-media [--keep note1]  # the media, or after the cut changed

It needs the spine's output in work/<id>/raw: cut.mp4, cut_words.json and edl.json, plus cam_cut.mp4 when the take has a
clean CAMERA file. The face window is a 4:5 crop of his real camera pixels (cam_cut.mp4, else cut.mp4): crop and scale
only, nothing generated. --check-face writes work/<id>/face-check.jpg, the crop as the window will show it, and stops:
look at it first. Black in the corners means the camera file has a mask baked in (1109-fable's had OBS's circle), and
the crop cannot go wider than that mask.

A first run copies the kit's tools and fonts and makes the media. It never overwrites an existing project's tools or
sections. --refresh-media re-makes face.mp4, voice.m4a and words.json from today's cut and keeps the old ones as
<name>.before-<keep>.<ext>.

--quick ([Chase] 2026-11-13: the scenes should be done while he listens to the cut) needs only cut_words.json and
edl.json, which exist the moment `rawcut.py cut` has run, before any picture is rendered. It copies the tools, writes
words.json, video.json and cut0.json, and makes a stand-in voice from raw/edit.wav (about half a minute). The sections can be written and built
(`node tools/build.mjs` checks every cue and the tiling; joins_check.py the joins) straight away. The face track and
the stills need the rendered cut: run --refresh-media when raw/cut.mp4 exists (the draft, about 11 min into his
listen), and again with --keep draft after he approves.

The face track is made on the GPU (face_track.build_base, about 2 min for a 12-minute cut) when NVENC is there, and
with x264 in software otherwise (about 7 min).

The project may be started on the DRAFT cut that the cut review page renders while Chase listens (raw/rendered.json
says `reviewed: false`). A first run writes tools/cut0.json, the keeps the sections are written against. After his
approval, --refresh-media compares those keeps with today's and writes tools/retime.json itself (what moved, in whole
frames), and raises media_rev: section files keep the times they were written with. A project without cut0.json
(made before 2026-11-12) still needs its retime.json row added by hand, as README.md describes.
"""
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path

KIT = Path(__file__).resolve().parent
SHORTS = KIT.parents[2]
FPS = 30
FACE_W, FACE_H = 960, 1200          # the large window is 480 x 600, so this is its exact size on the 4K canvas


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"{' '.join(map(str, cmd[:6]))} ... failed:\n{r.stderr[-600:]}")
    return r.stdout


def frames(p):
    out = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", str(p)]).strip()
    return int(out) if out.isdigit() else -1


def crop_of(text):
    try:
        w, h, x, y = (int(v) for v in text.split(":"))
    except ValueError:
        sys.exit("--crop is W:H:X:Y in the camera file's pixels, e.g. 1440:1800:1200:173")
    if abs(w / h - 0.8) > 0.005:
        sys.exit(f"--crop {w}x{h} is not 4:5: the window is 480 x 600 and his footage is never stretched")
    return w, h, x, y


def has_nvenc():
    r = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True)
    return "h264_nvenc" in r.stdout


def voice(raw, out):
    """The cut's audio: copied from raw/cut.mp4 when the cut is rendered, else a stand-in encoded from raw/edit.wav."""
    if (raw / "cut.mp4").is_file():
        run(["ffmpeg", "-v", "error", "-y", "-i", str(raw / "cut.mp4"), "-vn", "-c:a", "copy", str(out)])
    elif (raw / "edit.wav").is_file():
        # a stand-in until the cut is rendered (--refresh-media then copies the real track): the fast coder, because the
        # default one takes 2.5 min for 12 min of audio at 320k and this one 26 s (measured on 1113-nod)
        run(["ffmpeg", "-v", "error", "-y", "-i", str(raw / "edit.wav"), "-c:a", "aac", "-aac_coder", "fast", "-b:a", "192k", str(out)])
    else:
        sys.exit(f"{raw} has neither cut.mp4 nor edit.wav: run `rawcut.py cut` first")


def media(root, project, crop, keep=None, face=True):
    """face.mp4, voice.m4a and words.json from today's cut. face=False (--quick) leaves the face track for later."""
    raw = root / "raw"; assets = project / "assets"; assets.mkdir(parents=True, exist_ok=True)
    src = raw / "cam_cut.mp4" if (raw / "cam_cut.mp4").is_file() else raw / "cut.mp4"
    for name in ("face.mp4", "voice.m4a", "words.json"):
        f = assets / name
        if f.exists() and (face or name != "face.mp4"):
            if keep:
                f.rename(f.with_name(f"{f.stem}.before-{keep}{f.suffix}"))
            elif name == "face.mp4":
                sys.exit(f"{f} exists. Pass --refresh-media --keep <label> to replace it and keep the old one")
            else:
                f.unlink()                                            # voice and words are copies of raw/: nothing to keep
    w, h, x, y = crop
    dur = json.loads((raw / "edl.json").read_text())["dur"]
    voice(raw, assets / "voice.m4a")
    shutil.copy2(raw / "cut_words.json", assets / "words.json")
    if not face:
        return None, dur
    if not src.is_file():
        sys.exit(f"{src} is missing: the face track needs the rendered cut (the cut review page's draft, or his approved render)")
    made = False
    if has_nvenc():
        sys.path.insert(0, str(KIT))
        import face_track
        try:
            face_track.build_base(src, f"{w}:{h}:{x}:{y}", assets / "face.mp4"); made = True
        except SystemExit as e:
            print(f"GPU face track failed ({e}); x264 in software instead")
    if not made:
        run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-an", "-vf", f"crop={w}:{h}:{x}:{y},scale={FACE_W}:{FACE_H}:flags=lanczos,fps={FPS}",
             "-c:v", "libx264", "-crf", "21", "-preset", "fast", "-g", str(FPS), "-pix_fmt", "yuv420p", str(assets / "face.mp4")])
    got, want = frames(assets / "face.mp4"), int(dur * FPS + 0.5)
    print(f"face.mp4 from {src.name}: {got} frames at {FPS} fps (cut is {dur} s = {want}){'' if abs(got - want) <= 1 else '  <-- FRAME COUNT MISMATCH'}")
    return src.name, dur


def retime_rows(old, new, cut_fps):
    """[[atSecond, addedSeconds], ...] for tools/retime.json: what moved between two cuts of the same session.

    old, new: keeps as [start, end) session frames, in order. Footage kept in both cuts sits at a new place in the
    cut; each row says "everything from here on moved by this much", on the OLD cut's clock (the one the sections were
    written against). The total moved so far is rounded to whole project frames, so no error builds up. A row's time
    is half a project frame before the first footage it moves, so a shot that starts exactly on a join moves with it."""
    def both():
        i = j = 0
        while i < len(old) and j < len(new):
            s, e = max(old[i][0], new[j][0]), min(old[i][1], new[j][1])
            if s < e:
                yield s
            if old[i][1] <= new[j][1]:
                i += 1
            else:
                j += 1

    def place(keeps, f):                                             # where session frame f sits in a cut, in cut frames
        return sum(min(e, f) - s for s, e in keeps if s < f)
    rows, moved = [], 0
    for s in both():
        now = round((place(new, s) - place(old, s)) / cut_fps * FPS)             # in whole project frames
        if now != moved:
            rows.append([round(place(old, s) / cut_fps - 0.5 / FPS, 4), round((now - moved) / FPS, 6)])
            moved = now
    return rows


def retime(root, project):
    """Writes tools/retime.json from tools/cut0.json and raw/edl.json. Returns the rows, or None when there is no cut0.json."""
    c0 = project / "tools" / "cut0.json"
    if not c0.is_file():
        return None
    old = json.loads(c0.read_text()); edl = json.loads((root / "raw" / "edl.json").read_text())
    rows = retime_rows(old["keeps"], edl["keeps"], old["fps"])
    (project / "tools" / "retime.json").write_text(json.dumps(rows) + "\n", encoding="utf8", newline="\n")
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("id")
    p.add_argument("--crop", help="W:H:X:Y, a 4:5 rectangle in the camera file")
    p.add_argument("--radius", type=int, default=113, help="window corner radius in px at 1080p. 113 is the rounded window Chase approved on 1109-fable; 0 is square")
    p.add_argument("--series", default="rule:10", help='label:count for chapter titles, e.g. "rule:10" prints "// rule 03 of 10"')
    p.add_argument("--docs-site", default="", help='label on docs excerpts, e.g. "platform.claude.com/docs"; default is the page host')
    p.add_argument("--check-face", action="store_true", help="write work/<id>/face-check.jpg and stop")
    p.add_argument("--quick", action="store_true", help="first run without the face track: needs only `rawcut.py cut`, takes seconds")
    p.add_argument("--refresh-media", action="store_true", help="make the face track of a --quick project, or re-make face, voice and words after the cut changed")
    p.add_argument("--keep", default="", help="label for the media --refresh-media replaces")
    p.add_argument("--work", default=str(SHORTS / "work"))
    a = p.parse_args()
    root = Path(a.work) / a.id; raw = root / "raw"; project = root / "full"
    missing = [n for n in (("cut_words.json", "edl.json") if a.quick else ("cut.mp4", "cut_words.json", "edl.json")) if not (raw / n).is_file()]
    if missing:
        sys.exit(f"{raw} is missing {', '.join(missing)}: run the spine (templates/story.md) first")

    if a.check_face:
        w, h, x, y = crop_of(a.crop or sys.exit("--check-face needs --crop"))
        src = raw / "cam_cut.mp4" if (raw / "cam_cut.mp4").is_file() else raw / "cut.mp4"
        mid = json.loads((raw / "edl.json").read_text())["dur"] / 2
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{mid:.2f}", "-i", str(src), "-frames:v", "1", "-vf", f"crop={w}:{h}:{x}:{y},scale=480:600:flags=lanczos", str(root / "face-check.jpg")])
        print(f"{root / 'face-check.jpg'}: the window at 1080p size, from {src.name} at {mid:.0f} s. Look at it before building.")
        return

    cfg_file = project / "tools" / "video.json"
    if a.refresh_media:
        if not cfg_file.is_file():
            sys.exit(f"{project} is not a charcoal project yet")
        first = not (project / "assets" / "face.mp4").exists()       # a --quick project getting its first face track
        if not a.keep and not first:
            sys.exit("--refresh-media needs --keep <label>, e.g. --keep note1")
        cfg = json.loads(cfg_file.read_text())
        source, dur = media(root, project, crop_of(a.crop or cfg["face"]["crop"]), a.keep or None)
        if a.crop:
            cfg["face"]["crop"] = a.crop
        cfg["face"]["source"] = f"raw/{source}"
        cfg["media_rev"] = cfg.get("media_rev", 0) + 1                # the footage under every scene changed: no old slice is re-used
        cfg_file.write_text(json.dumps(cfg, indent=1) + "\n", encoding="utf8", newline="\n")
        rows = retime(root, project)
        if rows is None:
            print(f"cut is now {dur} s; the sections were written against {cfg['end0']} s. Add the change to tools/retime.json "
                  f"as [atSecond, addedSeconds] in whole {FPS} fps frames (README.md, \"When the cut changes\").")
        else:
            end = cfg["end0"] + sum(r[1] for r in rows)
            print(f"cut is now {dur} s; the sections were written against {cfg['end0']} s. tools/retime.json: {len(rows)} row(s) "
                  f"{rows[:6]}{' ...' if len(rows) > 6 else ''}; the sections now end at {end:.3f} s"
                  f"{'' if abs(end - dur) <= 1 / FPS + 1e-6 else '  <-- DOES NOT MATCH THE CUT'}. media_rev is {cfg['media_rev']}. "
                  "Run node tools/build.mjs: a cue on words he cut stops the build and names the phrase.")
        return

    if cfg_file.exists():
        sys.exit(f"{project} already exists. Its tools and sections are never overwritten; use --refresh-media for a new cut")
    crop = crop_of(a.crop or sys.exit("--crop W:H:X:Y is required (try --check-face first)"))
    label, _, count = a.series.partition(":")
    (project / "compositions").mkdir(parents=True, exist_ok=True)
    shutil.copytree(KIT / "tools", project / "tools", dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    (project / "tools" / "sections").mkdir(exist_ok=True)
    for f in (KIT / "project").iterdir():
        shutil.copy2(f, project / f.name)
    shutil.copytree(KIT / "assets" / "fonts", project / "assets" / "fonts", dirs_exist_ok=True)
    (project / "assets" / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(exist_ok=True)
    (project / "meta.json").write_text(json.dumps({"id": f"{a.id}-full", "name": f"{a.id}-full"}, indent=2) + "\n", encoding="utf8", newline="\n")
    (project / "tools" / "retime.json").write_text("[]\n", encoding="utf8", newline="\n")
    edl = json.loads((raw / "edl.json").read_text())                  # the cut the sections will be written against
    (project / "tools" / "cut0.json").write_text(json.dumps({"keeps": edl["keeps"], "fps": edl.get("fps", 60), "reviewed": bool(edl.get("reviewed"))}) + "\n", encoding="utf8", newline="\n")
    source, dur = media(root, project, crop, face=not a.quick)
    cfg = {"id": a.id, "end0": dur, "fps": FPS, "media_rev": 0, "series": {"label": label, "count": int(count or 0)},
           "face": {"crop": a.crop, "radius": a.radius, "source": f"raw/{source}" if source else "pending"}}
    if a.docs_site:
        cfg["docs_site"] = a.docs_site
    cfg_file.write_text(json.dumps(cfg, indent=1) + "\n", encoding="utf8", newline="\n")
    if a.quick:
        print("No face track yet (--quick): write the sections and run node tools/build.mjs now. When raw/cut.mp4 exists: "
              f"python templates/charcoal/build_kit/new_project.py {a.id} --refresh-media   (then the stills and the storyboard)")
    print(f"{project}\nNext: templates/charcoal/CARD.md, from 'Plan the video'."
          + ("" if edl.get("reviewed") else "\nThis is the DRAFT cut (Chase has not approved it yet). After his approval: "
             f"python templates/charcoal/build_kit/new_project.py {a.id} --refresh-media --keep draft"))


if __name__ == "__main__":
    main()
