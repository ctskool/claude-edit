"""Run state and read-only metrics; never renders or changes review records.

python tools/run_state.py init <id> --model "Opus 5.5" --template ivory --codex
python tools/run_state.py status <id>
python tools/run_state.py metrics <id>
python tools/run_state.py report

Use --root <folder> BEFORE the command for an isolated work/reports tree.
start player means the browser player has opened, not the server has started.
Repeated start while running is safe; start after a terminal status is a retry.
minutes counts running intervals only; waits are kept separately in intervals.
"""
import argparse
import json
import math
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from paths import project_root
ROOT = project_root()
STAGES = (
    "intake", "spine", "cut_listen", "research", "facts_assets_beats",
    "direction", "plan_check", "build", "review_render", "defects", "player",
    "approval", "sound", "final",
)
STATUSES = {"pending", "running", "done", "waiting_on_chase", "refused", "failed"}
LIVE = {"running", "waiting_on_chase"}
COMMANDS = {"start": "running", "done": "done", "wait": "waiting_on_chase",
            "refused": "refused", "fail": "failed"}


class StateError(ValueError):
    """An input or stored record needs attention."""


def now():
    return datetime.now().astimezone().isoformat(timespec="microseconds")


def instant(value):
    """Legacy review timestamps have no offset: interpret them as local time."""
    try:
        return datetime.fromisoformat(value).astimezone(timezone.utc)
    except (ValueError, TypeError, AttributeError) as e:
        raise StateError(f"invalid timestamp {value!r}") from e


def seconds(start, end):
    return max(0.0, (instant(end) - instant(start)).total_seconds())


def run_home(root, run_id):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", run_id):
        raise StateError(f"invalid run id {run_id!r}: use letters, numbers, - or _")
    work = (Path(root) / "work").resolve()
    home = work / run_id
    if home.resolve().parent != work:
        raise StateError(f"run id {run_id!r} points outside work")
    return home


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return default
    except (ValueError, UnicodeError) as e:
        raise StateError(f"{path}: {e}") from e


def atomic_write(path, text):
    """Publish a complete file with a same-directory rename."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         prefix=f".{path.name}.", suffix=".tmp",
                                         dir=path.parent, delete=False) as f:
            tmp = Path(f.name)
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)


def save(home, state):
    atomic_write(home / "run.json", json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def stage_key(name):
    if name in STAGES:
        return STAGES.index(name), 0
    match = re.fullmatch(r"note_round_([1-9][0-9]*)", name)
    if match:
        return STAGES.index("approval") - 0.5, int(match[1])
    raise StateError(f"unknown stage {name!r}; expected {', '.join(STAGES)}, or note_round_N (N >= 1)")


def new_stage(name):
    stage_key(name)
    row = {"name": name, "status": "pending", "started": None, "ended": None,
           "minutes": 0.0, "note": "", "intervals": []}
    if name == "plan_check":
        row["rounds"] = 0
    return row


def init_run(root, run_id, model=None, template=None, codex=False, reference=None):
    home = run_home(root, run_id)
    if (home / "run.json").exists():
        raise StateError(f"run {run_id!r} already has run.json; read status to resume")
    state = {"id": run_id, "created": now(), "model": model, "template": template,
             "codex": bool(codex), "reference": reference,
             "stages": [new_stage(name) for name in STAGES]}
    save(home, state)
    return state


def load_run(root, run_id):
    path = run_home(root, run_id) / "run.json"
    state = read_json(path)
    if state is None:
        raise StateError(f"unknown run id {run_id!r}: no {path}")
    if not isinstance(state, dict) or state.get("id") != run_id or not isinstance(state.get("stages"), list):
        raise StateError(f"{path}: expected matching id and a stages list")
    if not isinstance(state.get("created"), str) or type(state.get("codex")) is not bool:
        raise StateError(f"{path}: expected created timestamp and Boolean codex")
    instant(state["created"])
    names = []
    for row in state["stages"]:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            raise StateError(f"{path}: stage must be an object with a name")
        stage_key(row["name"])
        if not isinstance(row.get("status"), str) or row["status"] not in STATUSES:
            raise StateError(f"{path}: invalid status for {row['name']}")
        required = {"started", "ended", "minutes", "note"}
        if not required.issubset(row) or not isinstance(row["note"], str):
            raise StateError(f"{path}: missing stage fields or non-text note for {row['name']}")
        if type(row["minutes"]) not in (int, float) or not math.isfinite(row["minutes"]) or row["minutes"] < 0:
            raise StateError(f"{path}: invalid minutes for {row['name']}")
        for key in ("started", "ended"):
            if row[key] is not None:
                instant(row[key])
        if row["name"] == "plan_check" and (type(row.get("rounds")) is not int or row["rounds"] < 0):
            raise StateError(f"{path}: plan_check needs a nonnegative rounds count")
        intervals = row.get("intervals", [])
        if not isinstance(intervals, list):
            raise StateError(f"{path}: intervals must be a list for {row['name']}")
        for interval in intervals:
            if not isinstance(interval, dict) or interval.get("status") not in ("running", "waiting_on_chase"):
                raise StateError(f"{path}: invalid interval for {row['name']}")
            instant(interval.get("started"))
            if interval.get("ended") is not None:
                instant(interval["ended"])
        names.append(row["name"])
    if len(set(names)) != len(names) or not set(STAGES).issubset(names):
        raise StateError(f"{path}: duplicate or missing stages")
    state["stages"].sort(key=lambda s: stage_key(s["name"]))
    return state


def stage_minutes(row, at, status="running"):
    if "intervals" not in row:
        return float(row.get("minutes", 0)) if status == "running" else 0.0
    return sum(seconds(i["started"], i.get("ended") or at)
               for i in row["intervals"] if i["status"] == status) / 60


def change(root, run_id, name, status, note=None):
    stage_key(name)
    if status not in STATUSES - {"pending"}:
        raise StateError(f"unknown status {status!r}")
    state = load_run(root, run_id)
    row = next((s for s in state["stages"] if s["name"] == name), None)
    if row is None:
        row = new_stage(name)
        state["stages"].append(row)
        state["stages"].sort(key=lambda s: stage_key(s["name"]))
    stamp = now()
    old = row["status"]
    if old != status:
        intervals = row.setdefault("intervals", [])
        if intervals and intervals[-1].get("ended") is None:
            intervals[-1]["ended"] = stamp
        if row["started"] is None:
            row["started"] = stamp
        if name == "plan_check" and (old == "pending" or (status == "running" and old not in LIVE)):
            row["rounds"] = row.get("rounds", 0) + 1
        if status in LIVE:
            intervals.append({"status": status, "started": stamp, "ended": None})
        row.update(status=status, ended=None if status in LIVE else stamp, changed=stamp)
    if note is not None:
        row["note"] = note
    row["minutes"] = round(stage_minutes(row, stamp), 6)
    save(run_home(root, run_id), state)
    return row


def position(state):
    rows = state["stages"]
    live = [s for s in rows if s["status"] in LIVE]
    if live:
        current = ", ".join(f"{s['name']} ({s['status']})" for s in live)
        actions = [f"resume {s['name']}; verify its output before marking done"
                   if s["status"] == "running" else f"wait for Chase; then finish or resume {s['name']}" for s in live]
        return current, "; ".join(actions)
    blockers = [s for s in rows if s["status"] in {"refused", "failed"}]
    blocked = max(blockers, key=lambda s: s.get("changed") or s.get("ended") or "", default=None)
    current = blocked or next((s for s in rows if s["status"] == "pending"), None)
    if current is None:
        return "complete", "none; run complete"
    name, status = current["name"], current["status"]
    if status in {"refused", "failed"}:
        return f"{name} ({status})", f"resolve {name}: {current.get('note') or 'read the stage failure'}; then start {name}"
    return f"{name} (pending)", f"start {name}"


def status_text(state, at=None):
    at = at or now()
    current, step = position(state)
    end = next(s for s in state["stages"] if s["name"] == "final")
    elapsed = seconds(state["created"], end.get("ended") if end["status"] == "done" else at) / 60
    lines = [f"Run {state['id']} | model={state.get('model')} | template={state.get('template')} | codex={state.get('codex')}",
             "Stage                 Status               Active min  Note"]
    for s in state["stages"]:
        note = " ".join(s.get("note", "").split())
        lines.append(f"{s['name']:<21} {s['status']:<20} {stage_minutes(s, at):>10.2f}  {note}")
    lines += [f"Elapsed: {elapsed:.2f} min (including waits)", f"Now: {current}", f"Next: {step}"]
    return "\n".join(lines)


def interval_ranges(state, start, end, status):
    """Union a status's intervals, clipped to the first-player window."""
    lo, hi = instant(start), instant(end)
    ranges = []
    for row in state["stages"]:
        for i in row.get("intervals", []):
            if i["status"] == status:
                a, b = max(lo, instant(i["started"])), min(hi, instant(i.get("ended") or end))
                if a < b:
                    ranges.append((a, b))
    merged = []
    for a, b in sorted(ranges):
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else:
            merged.append((a, b))
    return merged


def waiting_seconds(state, start, end, blocked_only=True):
    """Deduct only waits without running work; research may run during a listen."""
    waits = interval_ranges(state, start, end, "waiting_on_chase")
    total = sum((b - a).total_seconds() for a, b in waits)
    if blocked_only:
        running = interval_ranges(state, start, end, "running")
        total -= sum(max(0.0, (min(b, d) - max(a, c)).total_seconds())
                     for a, b in waits for c, d in running)
    return total


def review_metrics(home):
    """Read review records without importing code that creates stores."""
    warnings = []
    metadata = read_json(home / "metadata.json", {})
    if not isinstance(metadata, dict):
        raise StateError(f"{home / 'metadata.json'}: expected an object")
    duration = metadata.get("duration")
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        duration = None
        warnings.append("metadata.json has no positive duration in seconds; note rates unavailable")
    notes = []
    path = home / "notes.jsonl"
    if path.is_file():
        for n, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                if not isinstance(row, dict) or not isinstance(row.get("id"), str):
                    raise ValueError("expected a note object with string id")
                notes.append(row)
            except ValueError as e:
                raise StateError(f"{path}:{n}: {e}") from e
    else:
        warnings.append("notes.jsonl missing; no notes recorded")
    # Notes remain evidence when dropped or adopted. A note id counts once.
    notes = list({n["id"]: n for n in notes}.values())
    sound = sum(n.get("scope") == "sound" for n in notes)
    rounds = []
    for path in sorted((home / "beat" / "rounds").glob("[0-9][0-9][0-9][0-9].json")):
        r = read_json(path)
        if not isinstance(r, dict) or type(r.get("n")) is not int:
            raise StateError(f"{path}: expected a picture round with n")
        rounds.append(r)
    # Round 0000 is normally a baseline snapshot, not a note round.
    note_rounds = [r for r in rounds if r.get("notes_rev") or r.get("note_ids") or r.get("not_done")]
    approvals = []
    folder = home / "beat" / "approvals"
    for path in sorted(folder.glob("*.json")):
        if not re.fullmatch(r"[0-9a-f]{16}\.json", path.name):
            continue  # active.json and compare-*.json are not approval records
        a = read_json(path)
        if isinstance(a, dict) and a.get("result") in {"PASS", "RECONCILED"} and a.get("approved_file_sha256") and a.get("created"):
            approvals.append(a)
    first = min(approvals, key=lambda a: instant(a["created"]), default=None)
    until, lineage_count = None, None
    if first:
        eligible = [r for r in note_rounds if r.get("created") and instant(r["created"]) <= instant(first["created"])]
        until = len(eligible)  # includes work later undone by go_back
        matched = [r for r in rounds if all(r.get(k) == first.get(v) for k, v in
                   (("picture_sha", "approved_file_sha256"), ("composition_rev", "composition_rev"), ("lock_revision", "lock_revision")))
                   and r.get("created") and instant(r["created"]) <= instant(first["created"])]
        if matched:
            by_n = {r["n"]: r for r in rounds}
            cursor = max(matched, key=lambda r: r["n"])
            seen = set()
            lineage_count = 0
            while cursor:
                if cursor["n"] in seen:
                    raise StateError(f"{home}/beat/rounds: cycle in parent chain")
                seen.add(cursor["n"])
                lineage_count += int(cursor in eligible)
                cursor = by_n.get(cursor.get("parent"))
        else:
            warnings.append("first approval has no matching round; approved-line round count unavailable")
    return {"duration_seconds": duration, "notes": len(notes), "picture_notes": len(notes) - sound,
            "sound_notes": sound, "notes_per_minute": len(notes) * 60 / duration if duration else None,
            "picture_notes_per_minute": (len(notes) - sound) * 60 / duration if duration else None,
            "note_rounds": len(note_rounds), "note_rounds_until_approval": until,
            "approved_line_rounds": lineage_count, "first_approval": first.get("created") if first else None,
            "warnings": warnings}


def metrics(root, run_id, at=None):
    home = run_home(root, run_id)
    if not home.is_dir() or not any((home / name).is_file() for name in ("run.json", "metadata.json", "notes.jsonl", "RUN.md")):
        raise StateError(f"unknown run id {run_id!r}: no run records in {home}")
    state = load_run(root, run_id) if (home / "run.json").is_file() else None
    data = review_metrics(home)
    data.update(id=run_id, model=state.get("model") if state else None,
                template=state.get("template") if state else None, codex=state.get("codex") if state else None,
                reference=state.get("reference") if state else None,
                player_minutes_including_wait=None, player_minutes_excluding_wait=None,
                player_wait_minutes=None, player_chase_wait_minutes=None,
                player_work_during_wait_minutes=None, plan_check_rounds=None, stages=[])
    if state:
        at = at or now()
        rows = {s["name"]: s for s in state["stages"]}
        start, end = rows["intake"].get("started"), rows["player"].get("started")
        if start and end:
            if instant(end) < instant(start):
                raise StateError("player started before intake")
            total = seconds(start, end)
            wait = waiting_seconds(state, start, end)
            chase_wait = waiting_seconds(state, start, end, blocked_only=False)
            data.update(player_minutes_including_wait=total / 60,
                        player_minutes_excluding_wait=(total - wait) / 60, player_wait_minutes=wait / 60,
                        player_chase_wait_minutes=chase_wait / 60, player_work_during_wait_minutes=(chase_wait - wait) / 60)
        data["plan_check_rounds"] = rows["plan_check"].get("rounds", 0)
        data["stages"] = [{"name": s["name"], "status": s["status"], "minutes": stage_minutes(s, at),
                           "waiting_minutes": stage_minutes(s, at, "waiting_on_chase")} for s in state["stages"]]
    else:
        data["warnings"].append("no run.json; stage timings and plan-check rounds unavailable (no prose inferred)")
    return data


def number(value):
    return "n/a" if value is None else f"{value:.2f}"


def metrics_text(data):
    lines = [f"Run {data['id']}",
             f"Intake -> player: {number(data['player_minutes_excluding_wait'])} min excluding Chase waits; "
             f"{number(data['player_minutes_including_wait'])} min including waits; {number(data['player_wait_minutes'])} min waiting",
             f"Chase wait before player: {number(data['player_chase_wait_minutes'])} min total; "
             f"{number(data['player_work_during_wait_minutes'])} min overlapped running work (not deducted)",
             f"Plan-check rounds: {data['plan_check_rounds'] if data['plan_check_rounds'] is not None else 'n/a'}",
             f"Video: {number(data['duration_seconds'])} seconds",
             f"Notes/min video: {number(data['notes_per_minute'])} all ({data['notes']} notes); "
             f"{number(data['picture_notes_per_minute'])} picture ({data['picture_notes']} notes); {data['sound_notes']} sound notes",
             f"Note rounds until first approval: {data['note_rounds_until_approval'] if data['note_rounds_until_approval'] is not None else 'n/a'} "
             f"(includes abandoned branches); approved line: {data['approved_line_rounds'] if data['approved_line_rounds'] is not None else 'n/a'}; "
             f"total so far: {data['note_rounds']}",
             f"First passing approval: {data['first_approval'] or 'none recorded'}",
             "Stage                 Status               Active min   Chase wait min"]
    for s in data["stages"]:
        lines.append(f"{s['name']:<21} {s['status']:<20} {s['minutes']:>10.2f} {s['waiting_minutes']:>16.2f}")
    lines += [f"NOTE: {w}" for w in data["warnings"]]
    return "\n".join(lines)


def cell(value):
    return str(value if value is not None else "n/a").replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def report(root):
    stamp = now()
    headers = ["Run", "Created", "Model", "Template", "Codex", "Reference", "Now", "Player min excl wait",
               "Player min incl wait", "Blocked Chase wait min", "Total Chase wait min", "Work during wait min", "Plan checks", "Video sec", "Notes/min all",
               "Notes/min picture", "Notes all/picture/sound", "Note rounds to approval", "Approved-line rounds",
               "Note rounds total", "Stage active/wait min", "Notes"]
    lines = ["# Editing metrics", "", f"Generated {stamp}", "",
             "Player time ends at the first start player (browser opened). Stage minutes count running intervals only. "
             "Only wait intervals without any running stage are deducted; research may overlap the cut listen. "
             "Notes/min counts unique saved ids, including dropped notes; picture and sound are separated. "
             "Rounds to first passing approval count actual note rounds, including abandoned branches, excluding the baseline snapshot. "
             "A historical approval does not establish current delivery approval. Missing measurements are n/a.", "",
             "| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for path in sorted((Path(root) / "work").glob("*/run.json")):
        try:
            state = load_run(root, path.parent.name)
            d = metrics(root, path.parent.name, at=stamp)
            values = [d["id"], state["created"], d["model"], d["template"], d["codex"], d["reference"], position(state)[0],
                      number(d["player_minutes_excluding_wait"]), number(d["player_minutes_including_wait"]), number(d["player_wait_minutes"]),
                      number(d["player_chase_wait_minutes"]), number(d["player_work_during_wait_minutes"]), d["plan_check_rounds"], number(d["duration_seconds"]), number(d["notes_per_minute"]), number(d["picture_notes_per_minute"]),
                      f"{d['notes']}/{d['picture_notes']}/{d['sound_notes']}", d["note_rounds_until_approval"], d["approved_line_rounds"], d["note_rounds"],
                      "; ".join(f"{s['name']} {s['minutes']:.2f}/{s['waiting_minutes']:.2f}" for s in d["stages"]), "; ".join(d["warnings"])]
        except (StateError, OSError) as e:
            values = [path.parent.name] + [None] * (len(headers) - 2) + [f"ERROR: {e}"]
        lines.append("| " + " | ".join(cell(v) for v in values) + " |")
    target = Path(root) / "reports" / "metrics.md"
    atomic_write(target, "\n".join(lines) + "\n")
    return target


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=ROOT, help="project root containing work/ and reports/")
    subs = ap.add_subparsers(dest="command", required=True)
    init = subs.add_parser("init")
    init.add_argument("id")
    for name in ("model", "template", "reference"):
        init.add_argument(f"--{name}")
    init.add_argument("--codex", action="store_true")
    for command in COMMANDS:
        sub = subs.add_parser(command)
        sub.add_argument("id")
        sub.add_argument("stage")
        if command != "start":
            sub.add_argument("--note")
    for command in ("status", "metrics"):
        subs.add_parser(command).add_argument("id")
    subs.add_parser("report")
    args = ap.parse_args(argv)
    try:
        if args.command == "init":
            init_run(args.root, args.id, args.model, args.template, args.codex, args.reference)
            print(f"Initialized {args.id}: {run_home(args.root, args.id) / 'run.json'}")
        elif args.command in COMMANDS:
            row = change(args.root, args.id, args.stage, COMMANDS[args.command], getattr(args, "note", None))
            print(f"{args.id}: {row['name']} {row['status']} ({row['minutes']:.2f} active min)")
        elif args.command == "status":
            print(status_text(load_run(args.root, args.id)))
        elif args.command == "metrics":
            print(metrics_text(metrics(args.root, args.id)))
        else:
            print(report(args.root))
    except (StateError, OSError, UnicodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
