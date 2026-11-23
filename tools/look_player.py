"""A hand-built look's short (blueprint, sky) in the beat review player, with notes by beat, rounds and Approve.

Those looks are not kit builds: one spec file, one HyperFrames composition, one whole render. So there is no ownership
map, no per-beat segments and no check reports. This writes what the player and review.py need instead:

  <project>/engine.json                         which engine and spec built this index.html (review.py reads it where a kit
                                                project has ownership.json: composition() below)
  <project>/plan.json                           the spoken line of each beat
  work/<id>/beat/stitched/review-<sha16>/       review.mp4, beats.lock.json, stitch.json
  work/<id>/beat/current.json                   which picture is the newest
  work/<id>/beat/checks/<rev16>/look-<sha16>.json   the only automatic check there is: the file's length and its sound

<project> is the spec's OUT and must be work/<id>/v2/<look>, the layout the player expects. Keep the spec file inside it
(short.py), so a round snapshots it and Go back restores it.

A beat reads "changed" in the player when its frames differ from the picture before (the whole short is re-rendered each
round, so the frames are compared; a kit short compares segment keys).

The spec's own `player` command renders and calls load(); nothing here is run by hand:
  python work/<id>/v2/<look>/short.py player              the whole short (always the first picture)
  python work/<id>/v2/<look>/short.py player --partial b04 b05      only these beats filmed again (picture() below). EXPERIMENTAL and slower than a
                                                                    whole render as measured 2026-11-22 (each stretch pays about 1 min 50 s of HyperFrames start-up, in
                                                                    software capture, and the stills check a few minutes more): do not use it in a run yet
  python -B tools/beat_review_v2/server.py work/<id>/v2/<look>
Notes are a normal round: review.freeze(project), edit the spec, `player` again, review.close_round(project, done=[...]).
His Approve click starts the 4K final (autofinal.py runs the spec's `final`).
"""
import json, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tools" / "beat_render")]
from sound_mix import file_hash  # noqa: E402
import store  # noqa: E402

MARK = "engine.json"
PROFILE = "review"
CMP = (90, 160)        # frames are compared at this size
CHANGED = 30           # a block this far from the old picture (of 255) is a change. Measured on the sky rea short 2026-11-22: the same frames through
                       # two encodes stay under 6, through HyperFrames' two capture paths (GPU whole render, software ranged render) under 20, and a changed word is over 200


def marker(project):
    return store.read_json(Path(project) / MARK)


def composition(project):
    """The marker, if it is the marker of this index.html; None once the project has moved on. What ownership.load is to a kit project."""
    m = marker(project)
    try:
        return m if m and file_hash(Path(project) / "index.html") == m["html_sha256"] else None
    except OSError:
        return None


def project_of(spec):
    out = Path(spec.OUT).resolve()
    if out.parent.name != "v2" or out.parents[2] != ROOT / "work":
        sys.exit(f"the player needs OUT = work/<id>/v2/<look>, not {out}")
    if not getattr(spec, "BEATS", None) or spec.BEATS[0] != 0:
        sys.exit("the player needs BEATS in the spec: the second each beat of his cut starts, the first one 0")
    return out


def probe(mp4):
    r = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-show_entries", "stream=codec_type,nb_read_packets,r_frame_rate", "-of", "json", str(mp4)],
                       capture_output=True, text=True, check=True)
    streams = json.loads(r.stdout)["streams"]
    v = next(s for s in streams if s["codec_type"] == "video")
    num, den = map(int, v["r_frame_rate"].split("/"))
    return num / den, int(v["nb_read_packets"]), any(s["codec_type"] == "audio" for s in streams)


def small_frames(mp4):
    import numpy as np
    w, h = CMP
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-map", "0:v:0", "-vf", f"scale={w}:{h}:flags=area,format=gray", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.int16)


def changed_beats(new_mp4, beats, old_folder):
    """Beat ids whose frames differ from the picture before. Every beat when there is no picture before to compare, or its beats sit elsewhere."""
    old = store.read_json(old_folder / "stitch.json") if old_folder else None
    if not old or not (old_folder / "review.mp4").is_file():
        return {b["beat_id"] for b in beats}, {}
    old_rows = {b["beat_id"]: b for b in old["beats"]}
    a, b_ = small_frames(old_folder / "review.mp4"), small_frames(new_mp4)
    changed = set()
    for b in beats:
        o = old_rows.get(b["beat_id"])
        s, e = b["start_frame"], b["end_frame"]
        if not o or (o["start_frame"], o["end_frame"]) != (s, e) or e > len(a) or e > len(b_):
            changed.add(b["beat_id"])
        elif int(abs(a[s:e] - b_[s:e]).max()) > CHANGED:
            changed.add(b["beat_id"])
    return changed, {i: r["key"] for i, r in old_rows.items()}


# ---- the review picture, whole or only the beats a note touched
#
# The picture is kept as one segment per beat (renders/parts/bNN.mp4, each a closed GOP with the same encoder settings) plus the
# sound as one wav. A whole render is cut into them once; a note round films only the named beats again (hyperframes render
# --start/--end), swaps their segments and their stretch of sound, and joins the set with no re-encode. So a beat nobody touched
# is the same bytes round after round.
# One spec builds the whole page and things carry across beats (a blueprint region stays on the sheet, the sky guide walks on),
# so naming the beats is not proof the others did not move: each other beat is checked with stills of the new page against the
# picture before, and any that moved is filmed too.

ENC = ["-c:v", "libx264", "-crf", "14", "-preset", "fast", "-pix_fmt", "yuv420p", "-bf", "2", "-video_track_timescale", "15360",
       "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
TOP = 92               # rows of the 160 compared in the stills check: the graphics and the caption seam, not his face


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)


def beat_rows(spec, fps, total):
    starts = [round(t * fps) for t in spec.BEATS]
    rows = [{"beat_id": f"b{i + 1:02d}", "start_frame": s, "end_frame": starts[i + 1] if i + 1 < len(starts) else total} for i, s in enumerate(starts)]
    bad = [r["beat_id"] for r in rows if r["end_frame"] <= r["start_frame"]]
    if bad:
        sys.exit(f"empty beat {bad[0]}: BEATS must rise and end before the short does ({total} frames)")
    return rows


def cut(src, rows, offset, parts, fps):
    """Each row's frames of src (which starts at frame `offset` of the short) into its own segment."""
    for r in rows:
        s, e = r["start_frame"] - offset, r["end_frame"] - offset
        ff("-i", src, "-an", "-vf", f"trim=start_frame={s}:end_frame={e},setpts=PTS-STARTPTS", "-r", fps, *ENC, parts / f"{r['beat_id']}.mp4")
        if probe(parts / f"{r['beat_id']}.mp4")[1] != e - s:
            sys.exit(f"{r['beat_id']} cut to the wrong length from {src}")


def read_wav(path):
    import wave
    import numpy as np
    with wave.open(str(path)) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, w.getnchannels()).copy(), w.getframerate()


def write_wav(path, data, rate):
    import wave
    with wave.open(str(path), "wb") as w:
        w.setnchannels(data.shape[1]); w.setsampwidth(2); w.setframerate(rate); w.writeframes(data.tobytes())


def join(parts, rows, dst):
    lst = parts / "list.txt"
    lst.write_text("".join(f"file '{(parts / (r['beat_id'] + '.mp4')).as_posix()}'\n" for r in rows), encoding="utf8")
    ff("-f", "concat", "-safe", "0", "-i", lst, "-i", parts / "audio.wav", "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "pcm_s16le", dst)


def moved_beats(out, hf, rows, named, before, fps):
    """Beats outside `named` whose stills of the new page differ from the picture before: two moments each, the middle and just before the end."""
    import numpy as np
    spot = out / "renders" / "spot"
    shutil.rmtree(spot, ignore_errors=True)
    want = {}
    for r in rows:
        if r["beat_id"] not in named:
            for n in {(r["start_frame"] + r["end_frame"]) // 2, r["end_frame"] - 2}:
                want[n] = r["beat_id"]
    if not want:
        return set()
    times = {n: f"{n / fps:.3f}".rstrip("0").rstrip(".") for n in want}
    if hf(f'snapshot --at {",".join(times.values())} --no-end --keep -o "renders/spot"', out):
        sys.exit("the stills check did not run: use `player` with no beats for a whole render")
    old = small_frames(before)
    w, h = CMP
    moved = set()
    for n, beat in want.items():
        png = spot / f"at-{times[n]}s.png"
        if not png.is_file():
            sys.exit(f"the stills check wrote no {png.name}: use `player` with no beats for a whole render")
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(png), "-vf", f"scale={w}:{h}:flags=area,format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
        new = np.frombuffer(raw, np.uint8).reshape(h, w).astype(np.int16)
        if int(abs(new[:TOP] - old[n][:TOP]).max()) > CHANGED:
            moved.add(beat)
    return moved


def picture(spec, out, hf, finish, names=()):
    """Renders the review picture and returns the finished file. names: the beats a note touched; none means the whole short."""
    project = project_of(spec)
    root = store.open_store(store.root_of(project))
    fps, total = 30, round(spec.END * 30)
    rows = beat_rows(spec, fps, total)
    parts = out / "renders" / "parts"
    meta = store.read_json(parts / "parts.json")
    current = (store.read_json(root / "current.json", {}).get(PROFILE) or {})
    ranges = [[r["start_frame"], r["end_frame"]] for r in rows]
    names = set(names)
    unknown = names - {r["beat_id"] for r in rows}
    if unknown:
        sys.exit(f"no beat {sorted(unknown)[0]} in this short")
    why = None
    if not names:
        why = "asked for"
    elif not meta or meta.get("picture") != current.get("file_sha256") or not Path(current.get("file", "")).is_file():
        why = "the kept segments are not the newest picture's (first picture, or the player went back a round)"
    elif meta["ranges"] != ranges:
        why = "the beats moved"
    raw = out / "renders" / f"{spec.NAME}_raw.mkv"
    if why:
        print(f"whole render: {why}")
        whole = out / "renders" / f"{spec.NAME}_whole.mp4"
        if hf(f'render -o "renders/{whole.name}"', out):
            sys.exit("the render failed")
        if probe(whole)[1] != total:
            sys.exit(f"the render is {probe(whole)[1]} frames and END says {total}")
        shutil.rmtree(parts, ignore_errors=True); parts.mkdir(parents=True)
        cut(whole, rows, 0, parts, fps)
        ff("-i", whole, "-vn", "-ar", "48000", "-c:a", "pcm_s16le", parts / "audio.wav")
        filmed = [r["beat_id"] for r in rows]
    else:
        moved = moved_beats(out, hf, rows, names, current["file"], fps)
        if moved:
            print(f"also moved, by the stills check: {', '.join(sorted(moved))}")
        todo = [r for r in rows if r["beat_id"] in names | moved]
        runs = []
        for r in todo:  # neighbours are filmed as one stretch
            if runs and runs[-1][-1]["end_frame"] == r["start_frame"]: runs[-1].append(r)
            else: runs.append([r])
        audio, rate = read_wav(parts / "audio.wav")
        for run in runs:
            s, e = run[0]["start_frame"], run[-1]["end_frame"]
            clip = out / "renders" / "part.mp4"
            if hf(f'render --start {s / fps:.6f} --end {e / fps:.6f} -o "renders/{clip.name}"', out):
                sys.exit("the render failed")
            if probe(clip)[1] != e - s:
                sys.exit(f"{run[0]['beat_id']}..{run[-1]['beat_id']} rendered {probe(clip)[1]} frames, not {e - s}: use `player` with no beats for a whole render")
            cut(clip, run, s, parts, fps)
            ff("-i", clip, "-vn", "-ar", rate, "-ac", audio.shape[1], "-c:a", "pcm_s16le", parts / "part.wav")
            new, _ = read_wav(parts / "part.wav")
            a, b = round(s / fps * rate), round(e / fps * rate)
            new = new[:b - a]
            audio[a:a + len(new)] = new
        write_wav(parts / "audio.wav", audio, rate)
        filmed = [r["beat_id"] for r in todo]
    join(parts, rows, raw)
    final = out / "renders" / f"{spec.NAME}.mp4"
    finish(raw, final)
    if probe(final)[1] != total:
        sys.exit(f"the joined picture is {probe(final)[1]} frames, not {total}")
    store.write_json(parts / "parts.json", {"picture": file_hash(final), "ranges": ranges, "filmed": filmed})
    print(f"filmed {len(filmed)} of {len(rows)} beats: {', '.join(filmed)}")
    return final


def load(spec, mp4, engine):
    project = project_of(spec)
    home, root = project.parents[1], store.open_store(store.root_of(project))
    mp4 = Path(mp4).resolve()
    fps, total, audio = probe(mp4)
    if abs(fps - round(fps)) > 1e-6:
        sys.exit(f"the player needs a whole frame rate, got {fps}")
    fps = int(round(fps))

    words = json.loads(Path(spec.WORDS).read_text(encoding="utf8"))
    starts = [round(t * fps) for t in spec.BEATS]
    beats = []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else total
        if e <= s:
            sys.exit(f"beat {i + 1} is empty: BEATS must rise and end before the render does ({total} frames)")
        say = " ".join(w["text"] for w in words if s <= round(w["start"] * fps) < e)
        beats.append({"beat_id": f"b{i + 1:02d}", "start_frame": s, "end_frame": e, "say": say})

    html = file_hash(project / "index.html")
    rev, sha = html, file_hash(mp4)
    folder = root / "stitched" / f"{PROFILE}-{sha[:16]}"
    before = store.read_json(root / "current.json", {})
    old_name = (before.get(PROFILE) or {}).get("stitched")
    old_folder = root / "stitched" / old_name if old_name and old_name != folder.name else None
    changed, old_keys = changed_beats(mp4, beats, old_folder)
    for b in beats:
        b["key"] = f"{sha[:16]}-{b['beat_id']}" if b["beat_id"] in changed or b["beat_id"] not in old_keys else old_keys[b["beat_id"]]

    folder.mkdir(parents=True, exist_ok=True)
    dst = folder / f"{PROFILE}.mp4"
    if not dst.exists():
        shutil.copy2(mp4, dst)  # a real copy, never a hard link: the next render writes over the same file in renders/, and a link would take this picture with it
    store.write_json(folder / "beats.lock.json", {"schema": 1, "fps": fps, "total_frames": total, "duration": round(total / fps, 3),
        "beats": [{"beat_id": b["beat_id"], "start_frame": b["start_frame"], "end_frame": b["end_frame"], "plan_start": round(b["start_frame"] / fps, 3),
                   "plan_end": round(b["end_frame"] / fps, 3), "layout": "split"} for b in beats]})
    store.write_json(folder / "stitch.json", {"file": f"{PROFILE}.mp4", "file_sha256": sha, "composition_rev": rev, "lock_revision": rev,
        "beats": [{k: b[k] for k in ("beat_id", "key", "start_frame", "end_frame")} for b in beats]})

    # The one check a whole render can have without a kit build: it is the length the spec says, and it has his voice.
    problems = []
    if abs(total / fps - spec.END) > 2 / fps:
        problems.append(f"the render is {total / fps:.2f} s and the spec's END is {spec.END}")
    if not audio:
        problems.append("the render has no sound")
    checks = root / "checks" / rev[:16]
    checks.mkdir(parents=True, exist_ok=True)
    store.write_json(checks / f"look-{sha[:16]}.json", {"engine": engine, "problems": problems, "checked": ["length against END", "a sound stream"],
        "not_checked": "everything a kit build checks (motion lint, flashes, copy, geometry): his watch in the player is the check"})

    store.write_json(project / "plan.json", {"beats": [{"id": b["beat_id"], "say": b["say"]} for b in beats]})
    spec_file = Path(spec.__file__).resolve() if getattr(spec, "__file__", None) else None
    inside = bool(spec_file and project in spec_file.parents)
    store.write_json(project / MARK, {"schema": 1, "engine": engine, "name": spec.NAME, "spec": str(spec_file) if spec_file else None,
                                      "html_sha256": html, "composition_rev": rev})
    attempts = store.read_json(root / "last_attempt.json", {})
    if attempts.pop(PROFILE, None) is not None:
        store.write_json(root / "last_attempt.json", attempts)
    store.write_json(root / "current.json", {**before, PROFILE: {"stitched": folder.name, "file": str(dst), "file_sha256": sha, "composition_rev": rev,
                                                                 "lock_revision": rev, "status": "FAIL" if problems else "UNVERIFIED"}})
    print(f"{len(beats)} beats, {total} frames at {fps} fps, picture {sha[:16]}, changed: {', '.join(sorted(changed)) if old_folder else 'first picture'}")
    for p in problems:
        print("FAIL", p)
    if not inside:
        print(f"NOTE the spec ({spec_file}) is outside {project}: Go back in the player cannot restore it. Keep it there as short.py")
    if not (home / "raw" / "cut_words.json").is_file():
        print(f"NOTE no {home / 'raw' / 'cut_words.json'}: a note will not name the word under it")
    print(f"player: python -B tools/beat_review_v2/server.py {project.relative_to(ROOT).as_posix()}")
    return folder
