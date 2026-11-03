"""Source conformance: a beat and event contract measured from the composition, with no selection.json. CONTRACT.md section 7.

  python tools/beat_check/conform.py <project> --all
  python tools/beat_check/conform.py <project> --beats b02,b03 [--render <stitched.mp4>] [--store <root>]
  python tools/beat_check/conform.py <project> --audit [--store <root>]

Writes beat/checks/<rev16>/source.json, or source-<scope8>.json for --beats, with -<file_sha16> added when --render names a file, so one profile's report never replaces another's.
--audit is the owner audit alone, which run.py needs before it renders. It writes audit.json. Exit 0 PASS, 1 FAIL, 3 UNVERIFIED, 4 it could not measure the page.
A pass here says the page holds what the plan says. It says nothing about pixels: the broken whole render was good source producing bad frames, and only output.py sees that.
"""
import argparse, json, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import project_root
ROOT = project_root()
sys.path[:0] = [str(HERE), str(ROOT / "tools" / "beat_render"), str(ROOT / "tools")]
import events as contract
import lock as beat_lock
import ownership
import sound_mix
import store
from common import frame_of, sha

MEASURE = HERE / "conform.mjs"
MOTIONLINT = ROOT / "tools" / "motionlint.py"
READ_FRAMES = 15  # 0.5 s, measure.mjs's "readable just after"
WORD_FRAMES = 2  # how far an anchor may sit from its word
CHIP_LEAD_FRAMES = 5  # a caption chip may open this far ahead. The measured worst is 0.14 s
PASS, FAIL, UNVERIFIED = "PASS", "FAIL", "UNVERIFIED"
NA = "n/a"
CODES = {PASS: 0, FAIL: 1, UNVERIFIED: 3}
NOT_MEASURED = 4  # no evidence at all, which is not the UNVERIFIED of a check that looked and could not tell
ORDER = ("anchor", "sub_anchor", "action", "caption", "carried", "copy")
MEASURE_SECONDS = 900


def worst(statuses):
    statuses = list(statuses)
    return FAIL if FAIL in statuses else UNVERIFIED if UNVERIFIED in statuses or not statuses else PASS


def norm(text):
    return " ".join((text or "").split())


def points(event, owners, total):
    """The frames an event is read on. after is 0.5 s past its frame, clamped to one frame before its owner's interval ends."""
    frame = event["frame"]
    end = contract.interval_end(owners.get(event["owner"]), frame, total)
    if event["kind"] == "copy":
        return {"before": None, "after": frame, "span": [frame], "hold": None, "gone": None}
    hold = event.get("hold_frames")
    after = min(frame + READ_FRAMES, end - 1, total - 1)
    if hold:
        after = min(after, frame + hold - 1)
    after = max(after, frame)
    gone = event.get("end_frame") if event["kind"] == "caption" and event.get("end_frame", total) < total else None
    before = frame - 1 - (event.get("lead_frames") or 0)
    return {"before": before if before >= 0 else None, "after": after, "span": list(range(frame, after + 1)),
            "hold": min(frame + hold - 1, total - 1) if hold else None, "gone": gone}


def chain_objects(event, chains):
    chain = next(c for c in chains if c["id"] == event["carried"]["chain"])
    return list(chain["objects"])


def frames_needed(selected, owners, total, chains):
    """frame -> selectors, for every bound event."""
    frames = {}

    def want(frame, *selectors):
        if frame is not None:
            frames.setdefault(frame, set()).update(selectors)

    for e in selected:
        if not e.get("target") or "frame" not in e:
            continue
        p = points(e, owners, total)
        for frame in [p["before"], p["hold"], p["gone"], *p["span"]]:
            want(frame, e["target"])
        if e.get("carried"):
            for frame in (p["before"], p["after"]):
                want(frame, *chain_objects(e, chains))
    return {str(f): sorted(s) for f, s in frames.items()}


def root_frames(m):
    """frame -> the scene roots that must be hidden on it. Every window edge, both sides, for all roots at once. A root shown outside its windows paints on beats that do not depend on its owner."""
    fps, total = m["fps"], m["total_frames"]
    spans = {}
    for name, a, b in m["shared"]["timing"]["windows"]:
        spans.setdefault("#" + name, []).append((frame_of(a, fps), min(frame_of(b, fps), total)))
    edges = {0, total - 1}
    for rows in spans.values():
        for a, b in rows:
            edges |= {a - 1, a, b - 1, b}
    return {str(f): [root for root, rows in spans.items() if not any(a <= f < b for a, b in rows)] for f in sorted(e for e in edges if 0 <= e < total)}


def judge_roots(shown):
    """One row per scene root seen outside its windows, with the first frame."""
    first = {}
    for frame in sorted(shown, key=int):
        for root in shown[frame]:
            first.setdefault(root, int(frame))
    return [f"{root} shows on frame {frame}, outside its window" for root, frame in sorted(first.items())]


def job_of(project, m, selected, out, chains, windows):
    owners = {o["id"]: o for o in m["owners"]}
    scenes = [o for o in m["owners"] if o["kind"] == "scene"]
    resets = {}
    for chain in chains:
        for reset in chain.get("resets", []):
            resets.setdefault(str(reset["frame"]), []).extend([obj, prop] for obj, props in reset["values"].items() for prop in props)
    frames = frames_needed(selected, owners, m["total_frames"], chains)
    for frame in resets:
        frames.setdefault(frame, [])
    return {"project": str(project), "out": str(out), "fps": m["fps"], "frames": frames, "resets": resets, "root_frames": root_frames(m), "image_roots": {o["id"]: o["roots"] for o in scenes},
            "owners": [{"id": o["id"], "roots": o["roots"], "windows": [[a, b] for name, a, b in windows if "scene." + name == o["id"]]} for o in scenes]}


def readable(seen, event):
    """Whether what this event names is on screen in one measurement."""
    if not seen or not seen["visible"]:
        return False
    if event.get("symbol"):
        return event["symbol"] in seen["symbols"]
    if event.get("copy") and not event.get("image"):
        return norm(event["copy"]) in norm(seen["text"])
    return True


def word_problem(event, fps):
    """Rule on the plan's own numbers. None when it holds."""
    if event.get("word_start") is None or event.get("t") is None:
        return None
    off = (event["t"] - event["word_start"]) * fps
    lead = CHIP_LEAD_FRAMES if event["kind"] == "caption" else WORD_FRAMES + (event.get("lead_frames") or 0)
    if off < -lead - 1e-6:
        return f"leads its word by {-off:.1f} frames, at most {lead}"
    if off > WORD_FRAMES + 1e-6:
        return f"follows its word by {off:.1f} frames, at most {WORD_FRAMES}"
    return None


def judge_time(event, p, frames):
    """Returns (status, onset, problem). Too early and never are both FAIL."""
    at = lambda f: frames.get(f, {}).get(event["target"])
    expect = event["expect"]
    before, after = (at(p["before"]) if p["before"] is not None else None), at(p["after"])
    if p["after"] not in frames or (p["before"] is not None and p["before"] not in frames):
        return UNVERIFIED, None, "frame not measured"
    if expect == "change":
        if p["before"] is None:
            return UNVERIFIED, None, "no frame before it to compare"
        if not before or not after:
            return FAIL, None, f"{event['target']} is not in the page"
        onset = next((f for f in p["span"] if at(f) and at(f)["state"] != before["state"]), None)
        return (PASS, onset, None) if onset is not None else (FAIL, None, f"nothing changed on {event['target']} from frame {p['before']} to {p['after']}")
    if not any(at(f) for f in [p["after"], *([p["before"]] if p["before"] is not None else [])]):
        return FAIL, None, f"{event['target']} is not in the page"
    if expect == "appear":
        if p["before"] is not None and readable(before, event):
            return FAIL, None, f"already there at frame {p['before']}, before its word: too early"
        onset = next((f for f in p["span"] if readable(at(f), event)), None)
        return (PASS, onset, None) if onset is not None else (FAIL, None, f"never there, frames {p['span'][0]} to {p['span'][-1]}")
    if expect == "present":
        missing = [f for f in ([p["before"]] if p["before"] is not None else []) + [p["after"]] if not readable(at(f), event)]
        return (FAIL, None, f"not there at frame {missing[0]}") if missing else (PASS, p["span"][0], None)
    return UNVERIFIED, None, f"unknown expect {expect}"


def judge_copy(event, p, frames):
    seen = frames.get(p["after"], {}).get(event["target"])
    if event.get("symbol"):
        return (PASS, None) if readable(seen, event) else (FAIL, f"mark {event['symbol']} is not visible at frame {p['after']}")
    if event.get("image"):
        if not seen or not seen["visible"]:
            return FAIL, f"{event['target']} is not visible at frame {p['after']}"
        return UNVERIFIED, f"'{event['copy']}' is inside {event['image']}, which the page cannot read"
    if not event.get("copy"):
        return NA, None
    if readable(seen, event):
        return PASS, None
    return FAIL, f"'{event['copy']}' not in visible own-text at frame {p['after']}: '{(seen or {}).get('text', '')[:80]}'"


def judge_hold(event, p, frames):
    if p["hold"] is None:
        return NA, None
    seen = frames.get(p["hold"], {}).get(event["target"])
    if event["expect"] == "appear" and not readable(seen, event):
        return FAIL, f"gone by frame {p['hold']}, held {event['hold_frames']} frames from {event['frame']}"
    if p["gone"] is not None:
        last = frames.get(p["gone"], {}).get(event["target"])
        if readable(last, event):
            return FAIL, f"still up at frame {p['gone']}, past its end"
    return PASS, None


def judge_carried(event, p, frames, chains, seen_nodes):
    """Same DOM node on both sides of the link, and the same node the chain has had all along. A replaced object is a different node with the same selector."""
    problems = []
    for selector in [event["target"], *chain_objects(event, chains)]:
        for frame in (p["before"], p["after"]):
            if frame is None:
                continue
            node = frames.get(frame, {}).get(selector)
            if node is None:
                problems.append(f"{selector} missing at frame {frame}")
                continue
            first = seen_nodes.setdefault(selector, (node["node"], frame))
            if first[0] != node["node"]:
                problems.append(f"{selector} at frame {frame} is not the node from frame {first[1]}")
    return (FAIL, "; ".join(problems[:4])) if problems else (PASS, None)


def judge_assets(event, project, images):
    missing = [a for a in event.get("assets", []) if not (project / a).is_file()]
    owner = images.get(event.get("owner"))
    broken = owner["broken"] if owner else []
    if missing or broken:
        return FAIL, f"missing {missing}, did not load {broken}"
    return (PASS, None) if event.get("assets") or owner else (NA, None)


def judge_event(event, frames, m, chains, project, images, seen_nodes):
    owners = {o["id"]: o for o in m["owners"]}
    fps = m["fps"]
    row = {"event_id": event["event_id"], "kind": event["kind"], "beat_id": event["beat_id"], "frame": event.get("frame"), "target": event.get("target"), "checks": {}, "problems": []}

    def mark(name, status, problem):
        row["checks"][name] = status
        if problem:
            row["problems"].append(f"{name}: {problem}")

    mark("assets", *judge_assets(event, project, images))
    if not event.get("target") or "frame" not in event:
        mark("bind", UNVERIFIED, "no bind in this project's tables")
        row["status"] = worst(row["checks"].values())
        return row
    p = points(event, owners, m["total_frames"])
    status, onset, problem = judge_time(event, p, frames)
    mark("time", status, problem)
    row["onset"] = onset
    mark("copy", *judge_copy(event, p, frames))
    mark("hold", *judge_hold(event, p, frames))
    word = word_problem(event, fps)
    late = None
    if onset is not None and event.get("word_start") is not None:
        lag = onset - frame_of(event["word_start"], fps)
        row["lag_frames"] = lag
        if lag > WORD_FRAMES:
            late = f"first shows {lag} frames after its word, at most {WORD_FRAMES}"
    if event.get("word_start") is None:
        mark("word", NA, None)
    else:
        mark("word", FAIL if word or late else PASS, word or late)
    if event.get("carried"):
        mark("carried", *judge_carried(event, p, frames, chains, seen_nodes))
    row["status"] = worst(s for s in row["checks"].values() if s != NA)
    return row


def judge_resets(chains, measured):
    """A declared reset must measure as declared on its frame, or the builder drops it. Only one that survived the build's four rules can fail a run."""
    rows = []
    for chain in chains:
        dropped = {d["frame"] for d in chain.get("dropped", [])}
        for reset in chain.get("resets", []):
            frame = reset["frame"]
            want = [v for props in reset["values"].values() for v in props.values()]
            got = measured.get(str(frame))
            same = got is not None and len(got) == len(want) and all(close(a, b) for a, b in zip(want, got))
            rows.append({"chain": chain["id"], "frame": frame, "matches": same, "dropped": frame in dropped})
    return rows


def close(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) < 1e-3
    return str(a) == str(b)


def motionlint(project):
    """Every error counts, except exactly what fixture.json waives. The waiver is reported every time."""
    r = subprocess.run([sys.executable, str(MOTIONLINT), str(project / "index.html"), "--pack", "editorial"], capture_output=True, text=True, encoding="utf8", errors="replace")
    errors = [line[6:] for line in r.stdout.splitlines() if line.startswith("ERROR ")]
    fixture = store.read_json(project.parents[1] / "fixture.json", {})
    rules = [w for w in fixture.get("waivers", []) if w.get("check") == "motionlint"]
    waived = [{"message": e[:120], "why": w["why"]} for e in errors for w in rules if e.startswith(w["starts_with"])]
    left = [e for e in errors if not any(e.startswith(w["starts_with"]) for w in rules)]
    if r.returncode not in (0, 1, 2):
        return UNVERIFIED, f"motionlint exited {r.returncode}", waived
    return (FAIL, "; ".join(left[:5]), waived) if left else (PASS, f"{len(errors)} error(s), {len(waived)} waived", waived)


def render_binding(project, root, m, render):
    """Which exact render this source check belongs to. A named render of another composition is a FAIL."""
    if render:
        path = Path(render).resolve()
        record = store.read_json(path.parent / "stitch.json")
        if record is None:
            return [], (UNVERIFIED, f"no stitch.json beside {path}")
        if record.get("composition_rev") != m["composition_rev"]:
            return [], (FAIL, f"{path.name} is a render of {record.get('composition_rev', '')[:16]}, this page is {m['composition_rev'][:16]}")
        return [{"profile": record["profile"], "file": str(path), "file_sha256": sound_mix.file_hash(path)}], (PASS, "named render is of this composition")
    rows = []
    for name, entry in store.read_json(Path(root) / "current.json", {}).items():
        path = Path(entry["file"])
        if entry["composition_rev"] == m["composition_rev"] and path.is_file() and sound_mix.file_hash(path) == entry["file_sha256"]:
            rows.append({"profile": name, "file": str(path), "file_sha256": entry["file_sha256"]})
    return rows, (PASS, f"{len(rows)} render(s) of this composition") if rows else (UNVERIFIED, "no stitched picture of this composition")


def in_scope(event, beats, ranges):
    if beats is None or event["beat_id"] in beats:
        return True
    frame = event.get("frame")
    return frame is not None and any(a <= frame < b for a, b in ranges)


def counts(rows):
    table = {}
    for row in rows:
        kind = table.setdefault(row["kind"], {PASS: 0, FAIL: 0, UNVERIFIED: 0})
        kind[row["status"]] += 1
    return {k: table[k] for k in ORDER if k in table}


def floor(all_events, lock):
    """Contract section 7's floor, from this project's own tables: what must be measured rather than left UNVERIFIED."""
    faces = {b["beat_id"] for b in lock["beats"] if b["layout"] == "full-face"}
    wants = {"caption": lambda e: e["kind"] == "caption", "anchor": lambda e: e["kind"] == "anchor" and e["beat_id"] not in faces, "carried": lambda e: e["kind"] == "carried"}
    want = {name: sum(1 for e in all_events if test(e)) for name, test in wants.items()}
    bound = {name: sum(1 for e in all_events if test(e) and e.get("target")) for name, test in wants.items()}
    want["copy_beats"] = len({e["beat_id"] for e in all_events if e["kind"] == "copy"})
    bound["copy_beats"] = len({e["beat_id"] for e in all_events if e["kind"] == "copy" and e.get("target")})
    return {"want": want, "bound": bound, "met": all(bound[k] >= v for k, v in want.items())}


def judge_page(measured, finding):
    """What the page itself says: errors, failed requests, the owner audit and the scene roots."""
    for error in measured["errors"]:
        finding(FAIL, "runtime", error)
    for request in measured["failed_requests"]:
        finding(FAIL, "assets", f"page request failed: {request}")
    audit = measured["audit"]
    if audit["missing"]:
        finding(UNVERIFIED, "owner_audit", "the page has no window.__own")
    elif audit["problems"]:
        for row in audit["problems"]:
            finding(FAIL, "owner_audit", f"{row['owner']}: {row['problem']}")
    else:
        finding(PASS, "owner_audit", f"{audit['tweens']} tweens stay inside their owners' roots")
    shown = judge_roots(measured["roots_shown"])
    for row in shown:
        finding(FAIL, "owner_audit", row)
    if not shown:
        finding(PASS, "scene_roots", f"every scene root hidden outside its windows, on {len(measured['roots_shown'])} frames")


def run_measure(project, m, selected, chains, finding):
    """Measures in a real page. None, with a finding, if it could not."""
    with tempfile.TemporaryDirectory() as tmp:
        job = Path(tmp) / "job.json"
        out = Path(tmp) / "measured.json"
        job.write_text(json.dumps(job_of(project, m, selected, out, chains, m["shared"]["timing"]["windows"])), encoding="utf8")
        try:
            subprocess.run(["node", str(MEASURE), str(job)], cwd=ROOT, check=True, timeout=MEASURE_SECONDS, capture_output=True, text=True, encoding="utf8", errors="replace")
            return json.loads(out.read_text(encoding="utf8"))
        except subprocess.CalledProcessError as e:
            finding(UNVERIFIED, "measurement", f"measurement failed: {(e.stderr or e.stdout or '')[-600:]}")
        except (OSError, ValueError, subprocess.TimeoutExpired) as e:
            finding(UNVERIFIED, "measurement", str(e))
    return None


def exit_code(report):
    measured = not any(f["status"] == UNVERIFIED and f["check"] in ("measurement", "contract", "lock") for f in report["findings"])
    return CODES[report["status"]] if measured or report["status"] == FAIL else NOT_MEASURED


def audit_only(project, root=None):
    """The owner audit alone, for run.py to run before it renders anything."""
    project = Path(project).resolve()
    root = store.open_store(root or store.root_of(project))
    report = {"schema": 1, "check": "audit", "project": str(project), "scope": "audit", "findings": [], "events": []}

    def finding(status, check, message):
        report["findings"].append({"status": status, "check": check, "message": message})

    m = ownership.load(project)
    if m is None:
        finding(UNVERIFIED, "contract", "no valid ownership.json for this index.html")
        return finish(report, root, None)
    report.update(composition_rev=m["composition_rev"], html_sha256=m["html_sha256"])
    measured = run_measure(project, m, [], m["chains"], finding)
    if measured is not None:
        report["hyperframes"] = measured["hyperframes"]
        judge_page(measured, finding)
    return finish(report, root, m)


def conform(project, beats=None, render=None, root=None):
    project = Path(project).resolve()
    root = store.open_store(root or store.root_of(project))
    report = {"schema": 1, "check": "source", "project": str(project), "scope": "all" if beats is None else sorted(beats), "findings": [], "events": []}
    if render and Path(render).is_file():
        report["render_sha16"] = sound_mix.file_hash(Path(render))[:16]

    def finding(status, check, message):
        report["findings"].append({"status": status, "check": check, "message": message})

    m = ownership.load(project)
    try:
        lock = beat_lock.load(project)
    except (OSError, ValueError, KeyError) as e:
        lock = None
        finding(UNVERIFIED, "lock", f"beats.lock.json: {e}")
    doc = contract.load(project)
    if m is None or lock is None or doc is None:
        finding(UNVERIFIED, "contract", f"nothing to measure against: ownership {'ok' if m else 'missing or stale'}, events {'ok' if doc else 'missing'}")
        return finish(report, root, None)
    report.update(composition_rev=m["composition_rev"], html_sha256=m["html_sha256"], lock_revision=lock["revision"], events_sha256=sha(doc))
    if m["lock_revision"] != lock["revision"]:
        finding(FAIL, "contract", "ownership.json is not of this beats.lock.json")
    if doc.get("composition_rev") != m["composition_rev"]:
        finding(FAIL, "contract", "events.json is not of this page: run the build")
        return finish(report, root, m)

    rows, binding = render_binding(project, root, m, render)
    report["renders"] = rows
    finding(binding[0], "render", binding[1])
    status, message, waived = motionlint(project)
    finding(status, "motionlint", message)
    report["waivers"] = waived
    report["floor"] = floor(doc["events"], lock)
    if not report["floor"]["met"]:
        finding(UNVERIFIED, "floor", f"bound {report['floor']['bound']}, this project has {report['floor']['want']}")

    chains = m["chains"]
    known = {b["beat_id"]: b for b in lock["beats"]}
    unknown = sorted(set(beats or []) - set(known))
    if unknown:
        finding(FAIL, "scope", f"no such beats: {unknown}")
    ranges = [(known[b]["start_frame"], known[b]["end_frame"]) for b in (beats or []) if b in known]
    selected = [e for e in doc["events"] if in_scope(e, beats, ranges)]
    measured = run_measure(project, m, selected, chains, finding)
    if measured is None:
        report["events"] = [{"event_id": e["event_id"], "kind": e["kind"], "beat_id": e["beat_id"], "status": UNVERIFIED, "checks": {}, "problems": ["not measured"]} for e in selected]
        return finish(report, root, m, doc)

    report["hyperframes"] = measured["hyperframes"]
    report["seek_ms"] = measured["seek_ms"]
    report["frames_measured"] = len(measured["frames"])
    judge_page(measured, finding)
    broken = {k: v for k, v in measured["images"].items() if v["broken"]}
    for owner, row in broken.items():
        finding(FAIL, "assets", f"{owner}: {row['broken']} did not load")
    report["images_checked"] = sum(v["count"] for v in measured["images"].values())
    resets = judge_resets(chains, measured["resets"])
    report["resets"] = resets
    for row in resets:
        if not row["matches"] and not row["dropped"]:
            finding(FAIL, "carried", f"reset at frame {row['frame']} in {row['chain']} does not measure as declared")

    frames = {int(f): v for f, v in measured["frames"].items()}
    seen_nodes = {}
    report["events"] = [judge_event(e, frames, m, chains, project, measured["images"], seen_nodes) for e in sorted(selected, key=lambda x: x.get("frame", 0))]
    return finish(report, root, m, doc)


def finish(report, root, m, doc=None):
    rows = report["events"]
    report["counts"] = counts(rows)
    statuses = [f["status"] for f in report["findings"]] + [r["status"] for r in rows]
    if not rows and report["scope"] != "audit":
        statuses.append(UNVERIFIED)
    report["status"] = worst(statuses)
    if m:
        folder = Path(root) / "checks" / m["composition_rev"][:16]
        folder.mkdir(parents=True, exist_ok=True)
        name = report_name(report)
        report["path"] = str(folder / name)
        store.write_json(folder / name, report)
    return report


def report_name(report):
    """One file per scope and per render. A report bound to one file never replaces the report of another."""
    if report["scope"] == "audit":
        return "audit.json"
    parts = ["source"] + ([] if report["scope"] == "all" else [sha(report["scope"])[:8]]) + ([report["render_sha16"]] if "render_sha16" in report else [])
    return "-".join(parts) + ".json"


def summary(report):
    for f in report["findings"]:
        if f["status"] != PASS:
            print(f"{f['status']} {f['check']}: {f['message']}")
    for kind, row in report["counts"].items():
        print(f"{kind}: {row[PASS]} pass, {row[FAIL]} fail, {row[UNVERIFIED]} unverified")
    for r in report["events"]:
        if r["status"] == FAIL:
            print(f"FAIL {r['event_id']} frame {r.get('frame')}: {'; '.join(r['problems'])}")
    print(report["status"], report.get("path", ""))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("project")
    scope = ap.add_mutually_exclusive_group(required=True)
    scope.add_argument("--all", action="store_true")
    scope.add_argument("--beats", help="comma-separated beats")
    scope.add_argument("--audit", action="store_true", help="the owner audit alone")
    ap.add_argument("--render", help="the stitched file this check binds to. Default: every current picture of this composition")
    ap.add_argument("--store")
    a = ap.parse_args(argv)
    report = audit_only(a.project, a.store) if a.audit else conform(a.project, None if a.all else [b for b in a.beats.split(",") if b], a.render, a.store)
    summary(report)
    return exit_code(report)


if __name__ == "__main__":
    sys.exit(main())
