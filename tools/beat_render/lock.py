"""Writes beats.lock.json, the frame map every beat tool reads. CONTRACT.md section 2.

Beats come from plan.json and the duration from metadata.json. fps comes from the builder, because metadata.json's fps is the raw source's.
"""
import json, math, os
from pathlib import Path

from common import frame_of, source_frame_time, sha

SCHEMA = 1


def derive(plan, duration, fps):
    """The lock for this plan. Any broken beat raises, which stops the build."""
    rows = plan["beats"]
    if not rows:
        raise ValueError("plan has no beats")
    ids = [b["id"] for b in rows]
    if len(set(ids)) != len(ids):
        raise ValueError(f"duplicate beat ids: {sorted({i for i in ids if ids.count(i) > 1})}")
    if rows[0]["start"] != 0:
        raise ValueError(f"first beat starts at {rows[0]['start']}, not 0")
    for a, b in zip(rows, rows[1:]):
        if a["end"] != b["start"]:
            raise ValueError(f"{a['id']} ends at {a['end']} but {b['id']} starts at {b['start']}")
    if rows[-1]["end"] != duration:
        raise ValueError(f"last beat ends at {rows[-1]['end']}, duration is {duration}")
    total = math.ceil(fps * duration)
    starts = [frame_of(source_frame_time(b["start"]), fps) for b in rows] + [total]
    beats = []
    for b, start, end in zip(rows, starts, starts[1:]):
        if end <= start:
            raise ValueError(f"{b['id']} is empty on the {fps} fps frame grid: [{start},{end})")
        beats.append({"beat_id": b["id"], "start_frame": start, "end_frame": end, "plan_start": b["start"], "plan_end": b["end"], "layout": b["layout"]})
    lock = {"schema": SCHEMA, "fps": fps, "total_frames": total, "duration": duration, "beats": beats,
            "source_plan_hash": sha({"duration": duration, "beats": [[b["id"], b["start"], b["end"], b["layout"]] for b in rows]})}
    lock["revision"] = revision_of(lock)
    return lock


def revision_of(lock):
    return sha({k: lock[k] for k in ("schema", "fps", "total_frames", "beats")})


def write(project, plan, duration, fps):
    lock = derive(plan, duration, fps)
    path = Path(project) / "beats.lock.json"
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(lock, indent=1, ensure_ascii=False) + "\n", encoding="utf8", newline="\n")
    os.replace(tmp, path)
    return lock


def load(project):
    """The lock, or ValueError if its contents are not the ones its revision was made from. It is in ownership.IGNORED, so nothing else would notice a hand edit."""
    lock = json.loads((Path(project) / "beats.lock.json").read_text(encoding="utf8"))
    try:
        revision = revision_of(lock)
    except (KeyError, TypeError) as e:
        raise ValueError(f"beats.lock.json is missing {e}")
    if lock.get("revision") != revision:
        raise ValueError("beats.lock.json does not match its own revision: run the build")
    return lock
