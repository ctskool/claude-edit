"""Validated stitch and the voice-only audio bed. CONTRACT.md section 6.

Refuses unless actual decoded counts, stream parameters, hashes and timestamps all hold. Concatenates by stream copy, muxes one continuous bed, decodes the result and requires
its frame rows to equal the segments' rows. Only then renames into stitched/. Re-encoding the whole picture would forfeit the unchanged-pixel guarantee.
"""
import json, os, shutil, subprocess, sys
from fractions import Fraction
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
import sound_mix
import sentinel
import store
from common import sha

BED_ARGS = ["-c:a", "aac", "-b:a", "256k", "-ar", "48000"]
STREAM_KEYS = ("codec", "pix_fmt", "width", "height", "r_frame_rate", "time_base", "has_b_frames")


def check_segments(lock, keys, profile_hash, records, hashes):
    """Every reason not to stitch. records: beat_id to segment.json or None. hashes: beat_id to the file's sha256 now."""
    problems = []
    next_frame = 0
    first = None
    for beat in lock["beats"]:
        id_ = beat["beat_id"]
        r = records.get(id_)
        if r is None:
            problems.append(f"{id_}: no segment")
            next_frame = beat["end_frame"]
            continue
        if r["beat_id"] != id_ or r["start_frame"] != beat["start_frame"] or r["end_frame"] != beat["end_frame"]:
            problems.append(f"{id_}: segment is for {r['beat_id']} [{r['start_frame']},{r['end_frame']})")
        if r["start_frame"] != next_frame:
            problems.append(f"{id_}: starts at {r['start_frame']}, expected {next_frame}")
        next_frame = r["end_frame"]
        if r["input_key"] != keys[id_]:
            problems.append(f"{id_}: key is stale")
        if r["profile_hash"] != profile_hash:
            problems.append(f"{id_}: profile differs")
        if r["file_sha256"] != hashes.get(id_):
            problems.append(f"{id_}: file hash differs")
        frames = beat["end_frame"] - beat["start_frame"]
        if r["decoded"]["frames"] != frames:
            problems.append(f"{id_}: decoded {r['decoded']['frames']} frames, expected {frames}")
        if r["stream"]["packets"] != frames:
            problems.append(f"{id_}: {r['stream']['packets']} packets, expected {frames}")
        if r["stream"]["has_b_frames"] != 0:
            problems.append(f"{id_}: has B-frames")
        params = {k: r["stream"][k] for k in STREAM_KEYS}
        first = first or params
        if params != first:
            problems.append(f"{id_}: stream parameters differ: {params} against {first}")
    if next_frame != lock["total_frames"]:
        problems.append(f"segments end at {next_frame}, expected {lock['total_frames']}")
    return problems


def probe_video(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                        "stream=codec_name,pix_fmt,width,height,r_frame_rate,time_base,has_b_frames,nb_read_packets", "-of", "json", str(path)],
                       capture_output=True, text=True, check=True)
    s = json.loads(r.stdout)["streams"][0]
    return {"codec": s["codec_name"], "pix_fmt": s["pix_fmt"], "width": s["width"], "height": s["height"], "r_frame_rate": s["r_frame_rate"],
            "time_base": s["time_base"], "has_b_frames": s.get("has_b_frames", 0), "packets": int(s["nb_read_packets"])}


def timestamp_problems(path, fps, total):
    """No B-frames, one packet per frame slot, uniform spacing, audio_verify.py's method."""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time,dts_time", "-of", "json", str(path)],
                       capture_output=True, text=True, check=True)
    packets = json.loads(r.stdout)["packets"]
    pts = [float(p["pts_time"]) for p in packets]
    problems = []
    if len(pts) != total:
        problems.append(f"{len(pts)} packets, expected {total}")
    if any(p["pts_time"] != p["dts_time"] for p in packets):
        problems.append("pts and dts differ, so a frame was reordered")
    tolerance = 0.25 / fps
    for i, t in enumerate(pts):
        if abs(t - pts[0] - i / fps) > tolerance:
            problems.append(f"packet {i} at {t}, expected {pts[0] + i / fps:.6f}")
            break
    streams = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "json", str(path)], capture_output=True, text=True, check=True).stdout)["streams"]
    if not any(s["codec_type"] == "audio" for s in streams):
        problems.append("no audio stream")
    return problems


def audio_bed(project, root):
    """One continuous voice-only bed from our own mix, never HyperFrames' planned audio. The bed is not mastered, because finish.py runs only in delivery."""
    plan = sound_mix.plan_of(project)
    key = sha({"voice": sound_mix.file_hash(sound_mix.voice_of(project)), "duration": plan["duration"], "encoder": BED_ARGS})
    bed = Path(root) / "audio" / f"{key[:16]}.m4a"
    if bed.is_file():
        return bed
    tmp = store.new_tmp(root)
    wav = tmp / "bed.wav"
    sound_mix.mix(project, str(wav), voice_only=True)
    out = tmp / "bed.m4a"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), *BED_ARGS, str(out)], check=True)
    os.replace(out, bed)
    shutil.rmtree(tmp, ignore_errors=True)
    return bed


def stitch(root, project, lock, m, profile, profile_hash, engine_hash, keys, bed):
    """Writes stitched/<profile>-<file_sha16>-<rev16>/ and returns its stitch.json. Raises ValueError with every problem, and leaves nothing behind. It does not move current.json: the run does that, after the checks."""
    root = Path(root)
    records = {b["beat_id"]: store.find(root, profile_hash, keys[b["beat_id"]]) for b in lock["beats"]}
    hashes = {id_: sound_mix.file_hash(store.segment_dir(root, profile_hash, keys[id_]) / r["file"]) for id_, r in records.items() if r}
    problems = check_segments(lock, keys, profile_hash, records, hashes)
    if problems:
        raise ValueError("; ".join(problems))
    work = store.new_tmp(root)
    listing = work / "concat.txt"
    lines = [f"file '{(store.segment_dir(root, profile_hash, keys[b['beat_id']]) / 'segment.mp4').as_posix()}'" for b in lock["beats"]]
    listing.write_text("\n".join(lines) + "\n", encoding="utf8", newline="\n")
    out = work / f"{profile['name']}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-i", str(bed), "-map", "0:v:0", "-map", "1:a:0", "-c", "copy", "-movflags", "+faststart", str(out)], check=True)

    expected = [row for b in lock["beats"] for row in store.rows_of(root, profile_hash, keys[b["beat_id"]])]
    rows, _, _ = sentinel.scan(out, profile["width"], profile["height"])
    problems = timestamp_problems(out, lock["fps"], lock["total_frames"])
    if rows != expected:
        at = next((i for i, (a, b) in enumerate(zip(rows, expected)) if a != b), min(len(rows), len(expected)))
        problems.append(f"decoded {len(rows)} rows, expected {len(expected)}, first difference at frame {at}")
    if problems:
        shutil.rmtree(work, ignore_errors=True)
        raise ValueError("; ".join(problems))

    file_sha = sound_mix.file_hash(out)
    record = {"schema": 1, "file": out.name, "file_sha256": file_sha, "composition_rev": m["composition_rev"], "lock_revision": lock["revision"],
              "profile": profile["name"], "profile_hash": profile_hash, "engine_hash": engine_hash, "bed_sha256": sound_mix.file_hash(bed),
              "beats": [{"beat_id": b["beat_id"], "key": keys[b["beat_id"]], "content_hash": records[b["beat_id"]]["decoded"]["content_hash"], "start_frame": b["start_frame"], "end_frame": b["end_frame"]} for b in lock["beats"]]}
    store.write_json(work / "stitch.json", record)
    shutil.copy(Path(project) / "ownership.json", work / "ownership.json")
    shutil.copy(Path(project) / "beats.lock.json", work / "beats.lock.json")
    listing.unlink()
    # Two compositions can stitch to the same bytes: a change no pixel shows, or a revert. Each keeps its own records, so the name carries both.
    target = root / "stitched" / f"{profile['name']}-{file_sha[:16]}-{m['composition_rev'][:16]}"
    if target.exists():
        for name in ("stitch.json", "ownership.json", "beats.lock.json"):
            os.replace(work / name, target / name)
        shutil.rmtree(work, ignore_errors=True)
    else:
        os.replace(work, target)
    return record, target


def current_entry(record, folder):
    """What current.json or last_attempt.json says about this stitched picture."""
    return {"stitched": Path(folder).name, "file": str(Path(folder) / record["file"]), "file_sha256": record["file_sha256"], "composition_rev": record["composition_rev"], "lock_revision": record["lock_revision"]}
