"""The beat and event contract: events.json, written by a project's build. CONTRACT.md section 7.

From plan.json and the project's bind tables, never selection.json. An event the tables do not bind still gets a row, with no target,
so the source check counts it as UNVERIFIED rather than missing it.
"""
import json, os, re, sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "beat_render"))
from common import frame_of
import ownership

SCHEMA = 1
NAME = "events.json"
HOLD = 15  # default hold for a change or a mark: as long as the check reads after the word
HOLD_TEXT = 30  # default hold for words, a second to read them
STYLE_KEYS = ("italic",)  # beats.json says how a title is set here, not what it says
ASSET = re.compile(r"assets/\S+")  # a plan's asset line is a path, often followed by a note


def lines(copy):
    """Every string in a beat's copy, in order, without the style keys."""
    if isinstance(copy, str):
        return [copy]
    if isinstance(copy, dict):
        return [s for k, v in copy.items() if k not in STYLE_KEYS for s in lines(v)]
    if isinstance(copy, list):
        return [s for v in copy for s in lines(v)]
    return []


def beat_at(lock, frame):
    return next((b["beat_id"] for b in lock["beats"] if b["start_frame"] <= frame < b["end_frame"]), None)


def interval_end(owner, frame, total):
    """Where the owner's interval holding this frame ends. An event outside every interval gets the whole video."""
    if owner:
        for a, b in owner["frames"]:
            if a <= frame < b:
                return b
    return total


def word_fields(words, index):
    if index is None:
        return {"word_id": None, "word": None, "word_start": None}
    return {"word_id": index, "word": words[index]["text"], "word_start": words[index]["start"]}


def plan_events(plan, words, binds, owners, fps, total, assets_of):
    out = []
    for beat in plan["beats"]:
        rows = [("anchor", beat["anchor"])] + [("sub_anchor", e) for e in beat["sub_anchors"]] + [("action", e) for e in beat["actions"]]
        for kind, source in rows:
            id_ = source["event_id"]
            event = {"event_id": id_, "beat_id": beat["id"], "kind": kind, "t": source.get("t"), "what": source.get("what"), "owner": None, "target": None, "expect": None,
                     "copy": None, "hold_frames": None, "lead_frames": source.get("lead_frames", 0), "assets": assets_of(beat), "carried": None}
            event.update(word_fields(words, source.get("word_i")))
            if source.get("t") is not None:
                event["frame"] = frame_of(source["t"], fps)
            if id_ in binds:
                owner, target, expect, copy, hold = binds[id_][:5]
                event.update(owner=owner, target=target, expect=expect, copy=copy)
                if len(binds[id_]) > 5:
                    event["lead_frames"] = binds[id_][5]
                if hold is None:
                    hold = min(HOLD_TEXT if copy else HOLD, interval_end(owners.get(owner), event["frame"], total) - event["frame"])
                event["hold_frames"] = hold
            out.append(event)
    return out


def caption_events(caps, chunks, words, owners, fps, total):
    out = []
    for on, off, _, _, id_ in caps:
        chunk, owner = chunks[id_], owners[id_]
        frame = frame_of(on, fps)
        end = min(frame_of(off, fps), total)
        out.append({"event_id": id_, "beat_id": owner["beat"], "kind": "caption", "owner": id_, "t": on, "frame": frame, "end_frame": end, **word_fields(words, chunk["words"][0]),
                    "target": f"[data-own='{id_}']", "expect": "appear", "copy": chunk["text"], "hold_frames": end - frame, "lead_frames": 0, "assets": [], "carried": None})
    return out


def carried_events(hud, chains, hud_binds, lock, fps):
    chain_of = {link: c["id"] for c in chains for link in c["links"]}
    out = []
    for name, t in hud:
        id_ = "hud." + name
        frame = frame_of(t, fps)
        out.append({"event_id": id_, "beat_id": beat_at(lock, frame), "kind": "carried", "owner": id_, "t": t, "frame": frame, "word_id": None, "word": None, "word_start": None,
                    "target": hud_binds.get(name), "expect": "change" if name in hud_binds else None, "copy": None, "hold_frames": None, "lead_frames": 0, "assets": [],
                    "carried": {"chain": chain_of[id_], "identity": "same-node"}})
    return out


def copy_events(beats, rows, fps):
    """One event per line of beats.json copy. Each is a moment that line must be on screen."""
    table = {}
    for row in rows:
        table.setdefault((row[0], row[1]), []).append(row)
    out, used = [], set()
    for beat in beats:
        for n, line in enumerate(lines(beat.get("copy") or {}), 1):
            event = {"event_id": f"{beat['id']}.copy{n}", "beat_id": beat["id"], "kind": "copy", "t": None, "word_id": None, "word": None, "word_start": None, "owner": None, "target": None,
                     "expect": None, "copy": line, "hold_frames": None, "lead_frames": 0, "assets": [], "carried": None}
            found = table.get((beat["id"], line))
            if found:
                row = found.pop(0)
                used.add(id(row))
                event.update(owner=row[2], target=row[3], t=row[4], frame=frame_of(row[4], fps), expect="present")
                if len(row) > 5:
                    event.update(row[5])
            out.append(event)
    unused = [row[:2] for row in rows if id(row) not in used]
    if unused:
        raise ValueError(f"copy binds that match no line of beats.json: {unused}")
    return out


def emit(project, plan, lock, m, binds, copy_binds, hud_binds, chunks):
    """Writes events.json from the page just built. It binds to this exact page through composition_rev, and a bad table raises and leaves no file."""
    project = Path(project)
    (project / NAME).unlink(missing_ok=True)
    fixture = project.parents[1]
    words = json.loads((fixture / "words.json").read_text(encoding="utf8"))
    beats = json.loads((fixture / "beats.json").read_text(encoding="utf8"))["beats"]
    html = (project / "index.html").read_text(encoding="utf8")
    caps, _ = ownership.data_of(html, "CAPS")
    hud, _ = ownership.data_of(html, "HUD")
    fps, total = lock["fps"], lock["total_frames"]
    owners = {o["id"]: o for o in m["owners"]}
    for id_, row in binds.items():
        if row[0] not in owners:
            raise ValueError(f"{id_} binds unknown owner {row[0]}")
    unknown = sorted(set(binds) - {e["event_id"] for b in plan["beats"] for e in [b["anchor"], *b["sub_anchors"], *b["actions"]]})
    if unknown:
        raise ValueError(f"binds for events the plan does not have: {unknown}")
    assets_of = lambda beat: sorted({m[0] for a in beat.get("assets", []) if isinstance(a, str) for m in [ASSET.match(a)] if m})
    events = plan_events(plan, words, binds, owners, fps, total, assets_of)
    events += caption_events(caps, chunks, words, owners, fps, total)
    events += carried_events(hud, m["chains"], hud_binds, lock, fps)
    events += copy_events(beats, copy_binds, fps)
    doc = {"schema": SCHEMA, "composition_rev": m["composition_rev"], "html_sha256": m["html_sha256"], "lock_revision": lock["revision"], "fps": fps, "total_frames": total, "events": events}
    path = project / NAME
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf8", newline="\n")
    os.replace(tmp, path)
    return doc


def load(project):
    """The contract, or None if missing or damaged."""
    try:
        return json.loads((Path(project) / NAME).read_text(encoding="utf8"))
    except (OSError, ValueError):
        return None
