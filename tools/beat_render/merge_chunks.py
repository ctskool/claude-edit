#!/usr/bin/env python3
"""Deterministically merge parallel ivory fragments; never execute chunk Python.

Usage: python tools/beat_render/merge_chunks.py {plan,build} PROJECT
plan.lead.json: {"plan": {top-level fields, "captions": {shared caption fields}},
"chunks": [{"id":"c1","prefix":"c1-","start":0,"end":5,"beats":["b01"]}],
"shared": {HUD, CTA, caption style, shared components and approved EXTRA_ROOTS}}.
plan.parts/<chunk>.json: {"chunk":"c1","beats":[...],"captions":{"chunks":[]},
"storyboard":"..."}. Beat and event ids retain upstream names.

tools_local/chunks/<chunk>/ contains exactly scenes.py, timeline.js, owners.py.
scenes.py: ONLY unindented S.append(own("c1-sc", <literal/f-string markup>)).
Markup may call kit helpers with literal arguments. No imports, assignments,
functions, variables or arbitrary evaluation. All DOM ids carry the prefix.
timeline.js: ONLY own("scene.c1-sc"); blocks, no closing own(null), no shell.
owners.py: ONLY literal WINDOWS, EVENT_BINDS, COPY_BINDS assignments.
Shared CSS/helpers/HUD/logos belong to Setup. Selectors must stay in their own
scene except EXTRA_ROOTS already authorized in Setup's assembled owners.py.
All validation precedes writes. @CHUNKS sections replace rather than append.
Build --check-chunk c1 validates just that chunk without writing or requiring
other chunks to exist; builders use it before reporting success.

ownership.py IGNORED holds tools_local/chunks/, plan.parts/ and plan.lead.json, so a
fragment or manifest change invalidates only what the merged sources change.
"""
import argparse
import ast
import copy
import json
import math
import os
from pathlib import Path
import re
import sys
import textwrap

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import confine

TABLES = {"WINDOWS": list, "EVENT_BINDS": dict, "COPY_BINDS": list}
HELPERS = {"img", "vid", "plate", "vplate", "card", "ol", "drawn", "title", "lbl", "use",
           "boxstyle", "imgstyle", "map_box"}
ID_HELPERS = {"img", "vid", "plate", "vplate", "card", "ol", "drawn", "title", "lbl"}
DEFAULT_HELPERS = {"A": 1, "show": 2, "hide": 2, "pop": 2, "popFirst": 2,
                   "slotPop": 2, "rise": 2, "cutIn": 2, "on": 2, "off": 2,
                   "drawRect": 2, "drawPath": 2, "word": 2}
BLOCK = re.compile(r'^[ \t]*own\("scene\.([\w-]+)"\);[ \t]*$', re.M)
DOM_ID = re.compile(r'''\bid\s*=\s*["']([^"']+)["']''')
SELECTOR = re.compile(r"#([\w-]+)")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate id/key {key!r}")
        result[key] = value
    return result


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)


def write_outputs(outputs):
    """Stage every output before replacing destinations."""
    staged = []
    try:
        for path, text in outputs.items():
            tmp = path.with_name(path.name + ".merge-tmp")
            with tmp.open("w", encoding="utf-8", newline="\n") as out:
                out.write(text)
            staged.append((tmp, path))
        for tmp, path in staged:
            os.replace(tmp, path)
    finally:
        for tmp, _ in staged:
            tmp.unlink(missing_ok=True)


def manifest(project):
    lead = read_json(project / "plan.lead.json")
    chunks = lead["chunks"]
    require(isinstance(chunks, list) and chunks, "lead has no chunks")
    seen, beat_ids, end = set(), set(), 0
    for chunk in chunks:
        key = chunk["id"]
        require(isinstance(key, str) and re.fullmatch(r"[a-z][a-z0-9]*", key), f"unsafe chunk id {key!r}")
        require(key not in seen, f"duplicate id across chunks: {key}")
        seen.add(key)
        require(chunk["prefix"] == key + "-", f"{key}: prefix must be {key}-")
        require(number(chunk["start"]) and number(chunk["end"]) and
                chunk["start"] == end and chunk["end"] > end,
                f"{key}: out-of-order windows or gap/overlap in chunk boundaries")
        end = chunk["end"]
        require(isinstance(chunk["beats"], list) and chunk["beats"], f"{key}: no beats")
        for bid in chunk["beats"]:
            require(isinstance(bid, str) and bid not in beat_ids, f"duplicate beat id across chunks: {bid!r}")
            beat_ids.add(bid)
    duration = read_json(project.parent.parent / "metadata.json")["duration"]
    require(number(duration) and number(lead["plan"]["duration"]) and duration == end and lead["plan"]["duration"] == duration,
            "duration does not match metadata.json")
    return lead


def events(beat):
    result = {}
    for event in [beat["anchor"], *beat["sub_anchors"], *beat["actions"]]:
        require(isinstance(event, dict) and isinstance(event.get("event_id"), str) and
                event["event_id"], f"{beat['id']}: event missing event_id")
        eid = event["event_id"]
        require(eid not in result, f"duplicate event id {eid}")
        result[eid] = event
    return result


def validate_plan(project, lead, plan):
    require(number(plan["duration"]), "plan duration must be a finite number")
    beats = plan["beats"]
    expected = [bid for c in lead["chunks"] for bid in c["beats"]]
    require([b["id"] for b in beats] == expected, "ordered beats differ from lead chunks")
    source = read_json(project.parent.parent / "beats.json")["beats"]
    require([b["id"] for b in source] == expected, "ordered beats differ from beats.json")
    seen, end = set(), 0
    for beat, original in zip(beats, source):
        start, stop = beat["start"], beat["end"]
        require(number(start) and number(stop) and start == end and stop > start,
                f"{beat['id']}: beats must touch end to start, no gap or overlap")
        require(math.floor(stop * 30 + 1e-6) > math.floor(start * 30 + 1e-6), f"{beat['id']}: empty beat at 30 fps")
        require(start == original["start"] and stop == original["end"], f"{beat['id']}: timing differs from beats.json")
        end = stop
        ids = events(beat)
        require(not seen.intersection(ids), f"duplicate event id across chunks: {sorted(seen.intersection(ids))}")
        seen.update(ids)
        upstream = [original.get("anchor"), *original.get("sub_anchors", []), *original.get("actions", [])]
        upstream_ids = {e["event_id"] for e in upstream if isinstance(e, dict) and e.get("event_id")}
        require(upstream_ids <= set(ids), f"{beat['id']}: event_id lost from beats.json")
    require(end == plan["duration"] == lead["plan"]["duration"], "last beat duration does not match metadata.json")
    by_id = {b["id"]: b for b in beats}
    for left, right in zip(lead["chunks"], lead["chunks"][1:]):
        require(by_id[left["beats"][-1]]["layout"] != by_id[right["beats"][0]]["layout"],
                f"{right['id']}: boundary is inside a layout run")
    for c in lead["chunks"]:
        require(by_id[c["beats"][0]]["start"] == c["start"] and by_id[c["beats"][-1]]["end"] == c["end"],
                f"{c['id']}: beats escape chunk window")
    old_path = project / "plan.json"
    if old_path.exists():
        for beat in read_json(old_path)["beats"]:
            require(beat["id"] in by_id and set(events(beat)) <= set(events(by_id[beat["id"]])),
                    f"{beat['id']}: existing event_id lost in revision")



def readouts(plan):
    """Whole-plan read-outs, never targets or claims about rendered motion."""
    runs, lengths = [], []
    for b in plan["beats"]:
        lengths.append(b["end"] - b["start"])
        if runs and runs[-1][2] == b["layout"]:
            runs[-1][1] = b["end"]
        else:
            runs.append([b["start"], b["end"], b["layout"]])
    shares = {layout: round(100 * sum(b["end"] - b["start"] for b in plan["beats"]
                                    if b["layout"] == layout) / plan["duration"], 3)
              for layout in ("split", "full-graphic", "full-face")}
    absence = max((end - start for start, end, layout in runs if layout == "full-graphic"), default=0)
    times = {0, plan["duration"]}
    times.update(b["start"] for b in plan["beats"])
    times.update(e["t"] for b in plan["beats"] for e in events(b).values() if number(e.get("t")))
    ordered = sorted(t for t in times if 0 <= t <= plan["duration"])
    static = sum(max(0, b - a - 1.5) for a, b in zip(ordered, ordered[1:]))
    return {"duration": plan["duration"], "beat_count": len(lengths), "layout_shares_pct": shares,
            "beat_lengths_s": lengths, "longest_face_absence_s": absence,
            "static_band_estimate_s": round(static, 3),
            "static_estimate_basis": "time beyond 1.5 s between planned beat/event times; rendered motion is unverified"}


def merge_plan(project):
    lead = manifest(project)
    parts_dir = project / "plan.parts"
    require({p.stem for p in parts_dir.glob("*.json")} == {c["id"] for c in lead["chunks"]},
            "plan.parts files differ from lead chunks (missing or stale part)")
    plan = copy.deepcopy(lead["plan"])
    plan["beats"] = []
    plan.setdefault("captions", {})["chunks"] = []
    boards = []
    for chunk in lead["chunks"]:
        part = read_json(parts_dir / (chunk["id"] + ".json"))
        require(set(part) == {"chunk", "beats", "captions", "storyboard"},
                f"{chunk['id']}: part may not override shared top-level fields")
        require(part["chunk"] == chunk["id"] and [b["id"] for b in part["beats"]] == chunk["beats"],
                f"{chunk['id']}: ordered beats differ from manifest")
        require(set(part["captions"]) == {"chunks"}, f"{chunk['id']}: caption style touches the shell")
        for cap in part["captions"]["chunks"]:
            require(cap["beat"] in chunk["beats"], f"{chunk['id']}: caption belongs to another chunk")
        plan["beats"].extend(part["beats"])
        plan["captions"]["chunks"].extend(part["captions"]["chunks"])
        require(isinstance(part["storyboard"], str), f"{chunk['id']}: storyboard must be text")
        boards.append(f"## {chunk['id']}\n\n{part['storyboard'].strip()}\n")
    validate_plan(project, lead, plan)
    plan["captions"]["chunks"].sort(key=lambda c: (c["on"], c["off"], c["beat"]))
    boards.append("## Whole-plan read-outs (never targets)\n\n" + json.dumps(readouts(plan), indent=1) + "\n")
    write_outputs({project / "plan.json": json.dumps(plan, indent=1, ensure_ascii=False) + "\n",
                   project / "STORYBOARD.md": "# Storyboard\n\n" + "\n".join(boards)})
    print(f"PASS plan: {len(lead['chunks'])} chunks, {len(plan['beats'])} beats; events preserved")


def literal(node, where):
    try:
        for item in ast.walk(node):
            if isinstance(item, ast.Dict):
                keys = [ast.literal_eval(k) for k in item.keys]
                require(len(keys) == len(set(keys)), f"{where}: duplicate id/key in dictionary")
        return ast.literal_eval(node)
    except (TypeError, SyntaxError) as exc:
        raise ValueError(f"{where}: only literal owner rows are allowed") from exc


def tables(text, fragment=False):
    found = {}
    for node in ast.parse(text).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in TABLES or (not fragment and name in ("EXTRA_ROOTS", "BLOCK_HELPERS")):
                require(name not in found, f"duplicate table {name}")
                found[name] = (literal(node.value, name), node.value)
                continue
        require(not fragment, "chunk touching the shell: owners.py allows only WINDOWS, EVENT_BINDS, COPY_BINDS")
    require(set(TABLES) <= set(found), "missing WINDOWS, EVENT_BINDS or COPY_BINDS")
    for name, kind in TABLES.items():
        require(isinstance(found[name][0], kind), f"{name}: expected {kind.__name__}")
    return found


def strip_generated(text, comment, name):
    begin, end = f"{comment} @CHUNKS {name} BEGIN", f"{comment} @CHUNKS {name} END"
    if begin not in text and end not in text:
        return text
    require(text.count(begin) == text.count(end) == 1, f"damaged merge markers for {name}")
    pattern = re.compile(r"^[ \t]*" + re.escape(begin) + r"\n.*?^[ \t]*" + re.escape(end) + r"\n", re.M | re.S)
    result, count = pattern.subn("", text)
    require(count == 1, f"damaged merge markers for {name}")
    return result


def insert_marker(text, marker, body, comment, name, indent=""):
    clean = strip_generated(text, comment, name)
    require(clean.count(marker) == 1, f"expected exactly one {marker}")
    at = clean.index("\n", clean.index(marker)) + 1
    section = f"{indent}{comment} @CHUNKS {name} BEGIN\n"
    section += textwrap.indent(body.rstrip() + "\n", indent)
    section += f"{indent}{comment} @CHUNKS {name} END\n"
    return clean[:at] + section + clean[at:]


def replace_tables(text, added):
    clean = text
    for name in TABLES:
        clean = strip_generated(clean, "#", name)
    parsed, replacements = tables(clean), []
    lines = clean.splitlines(keepends=True)
    for name, value in added.items():
        base, node = parsed[name]
        require(not base if name == "WINDOWS" else True, "chunk touching the shell: unmarked scene WINDOWS already exist")
        if isinstance(base, dict):
            require(not set(base).intersection(value), f"duplicate event id in Setup and chunks: {set(base).intersection(value)}")
        opening, closing = ("{", "}") if isinstance(base, dict) else ("[", "]")
        rows = ([repr(k) + ": " + repr(v) + "," for k, v in base.items()]
                if isinstance(base, dict) else [repr(v) + "," for v in base])
        more = ([repr(k) + ": " + repr(v) + "," for k, v in value.items()]
                if isinstance(value, dict) else [repr(v) + "," for v in value])
        replacement = opening + "\n" + "".join("    " + row + "\n" for row in rows)
        replacement += f"    # @CHUNKS {name} BEGIN\n"
        replacement += "".join("    " + row + "\n" for row in more)
        replacement += f"    # @CHUNKS {name} END\n" + closing
        # AST columns are UTF-8 byte offsets, not character offsets.
        start = sum(map(len, lines[:node.lineno - 1])) + len(lines[node.lineno - 1].encode()[:node.col_offset].decode())
        end = sum(map(len, lines[:node.end_lineno - 1])) + len(lines[node.end_lineno - 1].encode()[:node.end_col_offset].decode())
        replacements.append((start, end, replacement))
    for start, end, replacement in sorted(replacements, reverse=True):
        clean = clean[:start] + replacement + clean[end:]
    return clean


def prefixed(name, prefix):
    require(isinstance(name, str) and name.startswith(prefix) and re.fullmatch(r"[A-Za-z][\w-]*", name),
            f"id {name!r} missing its chunk prefix {prefix}")


def scene_fragments(text, prefix, seen=()):
    """Read the restricted expression grammar and collect helper-generated DOM ids."""
    regions = {}
    allowed = (ast.Constant, ast.JoinedStr, ast.FormattedValue, ast.Call, ast.Name,
               ast.Load, ast.List, ast.Tuple, ast.Dict, ast.UnaryOp, ast.USub, ast.UAdd)
    for stmt in ast.parse(text).body:
        require(isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call),
                "chunk touching the shell: scenes.py may only append own() regions")
        call = stmt.value
        require(isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) and
                call.func.value.id == "S" and call.func.attr == "append" and len(call.args) == 1 and not call.keywords,
                "chunk touching the shell: expected S.append(own(...))")
        own = call.args[0]
        require(isinstance(own, ast.Call) and isinstance(own.func, ast.Name) and own.func.id == "own" and
                len(own.args) == 2 and not own.keywords, "expected own(root, markup)")
        root = literal(own.args[0], "scene root")
        require(root not in regions, f"duplicate region id {root}")
        require(root not in seen, f"duplicate id across chunks: {root}")
        prefixed(root, prefix)
        ids, markup = [], own.args[1]
        require(isinstance(markup, (ast.Constant, ast.JoinedStr)), "markup must be literal or f-string")
        for node in ast.walk(markup):
            require(isinstance(node, allowed), "chunk touching the shell: unsupported scene expression")
            if isinstance(node, ast.Name):
                require(node.id in HELPERS, f"chunk touching the shell: scene reads {node.id}")
            if isinstance(node, ast.FormattedValue):
                require(isinstance(node.value, ast.Call) and node.conversion == -1 and node.format_spec is None,
                        "dynamic markup/id is outside the fragment grammar")
            if isinstance(node, ast.Call):
                require(isinstance(node.func, ast.Name) and node.func.id in HELPERS and not node.keywords,
                        "chunk touching the shell: unsupported scene call")
                values = [literal(arg, node.func.id) for arg in node.args]
                if node.func.id in ID_HELPERS:
                    require(values and isinstance(values[0], str), "helper id must be literal")
                    ident = values[0]
                    ids.append(ident)
                    suffixes = {"plate": ["-p", "-i"], "vplate": ["-p", "-v"], "drawn": ["-r"], "title": ["-2"]}
                    ids.extend(ident + s for s in suffixes.get(node.func.id, []))
                    if node.func.id == "title":
                        require(len(values) >= 6, "title needs six arguments")
                        ids.extend(ident + s for s, v in [("-1", values[3]), ("-3", values[5])] if v)
                    if node.func.id == "vplate":
                        ids.extend(row[0] for row in values[1])
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                ids.extend(DOM_ID.findall(node.value))
        require(root in ids, f"region {root}: missing literal root id")
        require(len(set(ids)) == len(ids), f"duplicate id inside region {root}")
        require(not set(ids).intersection(seen), f"duplicate id across chunks: {sorted(set(ids).intersection(seen))}")
        for ident in ids:
            prefixed(ident, prefix)
        shape = confine.read_region("scene." + root, markup_shape(markup))
        require(not shape.reach, f"chunk touching the shell: {root}: {shape.reach}")
        require("scene" in shape.top[0][1].get("class", "").split(), f"{root}: root needs class scene")
        for item in ast.walk(markup):
            if isinstance(item, ast.Constant) and isinstance(item.value, str) and "<" in item.value:
                parsed = confine.Region()
                parsed.feed(item.value)
                require(not parsed.reach, f"chunk touching the shell: {root}: {parsed.reach}")
        refs = list(shape.refs)
        for item in ast.walk(markup):
            if isinstance(item, ast.Constant) and isinstance(item.value, str):
                refs.extend(confine.ID_REF.findall(item.value))
        flat_refs = [r if isinstance(r, str) else next((v for v in r if v), "") for r in refs]
        require(all(r in ids or r.startswith(("logo-", "i-")) for r in flat_refs),
                f"chunk touching the shell: {root} references another scene or shell id")
        regions[root] = (ast.get_source_segment(text, stmt), set(ids))
    require(regions, "chunk has no regions")
    return regions



def markup_shape(node):
    """Shape-only expansion of known helpers; never read media or execute fragments."""
    if isinstance(node, ast.Constant):
        require(isinstance(node.value, str), "markup must be a string")
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(markup_shape(v) for v in node.values)
    call = node.value
    values = [literal(arg, call.func.id) for arg in call.args]
    name = call.func.id
    if name in ID_HELPERS:
        ident = values[0]
        # Geometry and styles are checked by build.py/conform; here check the
        # actual outer markup and every literal HTML payload a helper receives.
        return '<div id="' + ident + '"></div>'
    require(name == "use", "only DOM-producing helpers may be interpolated in markup")
    return "<svg></svg>"


def check_targets(block, allowed, helpers):
    """Selectors must be exact literal ids, so computed/global selectors cannot escape."""
    code = confine.no_comments(block)
    pattern = re.compile(r"(?<![\w$.])(?:tl\.(?:to|set|from|fromTo)|" +
                         "|".join(re.escape(h) for h in helpers if h != "A") + r")\s*\(")
    for match in pattern.finditer(code):
        args = confine.split_args(code, match.end() - 1)
        target = args[0].strip() if args else ""
        require(len(target) >= 3 and target[0] in "\"'" and target[-1] == target[0] and
                re.fullmatch(r"#[\w-]+", target[1:-1]) and target[2:-1] in allowed,
                f"chunk touching the shell: target must be an exact literal owned id: {target}")


def block_fragments(text):
    clean, marks = confine.no_comments(text), list(BLOCK.finditer(text))
    require(marks and not confine.no_comments(text[:marks[0].start()]).strip(),
            "chunk touching the shell: timeline prologue or missing block")
    require(len(re.findall(r"\bown\s*\(", clean)) == len(marks),
            "chunk touching the shell: only scene own markers are allowed, no own(null)")
    result = {}
    for i, mark in enumerate(marks):
        key = mark[1]
        require(key not in result, f"duplicate block id {key}")
        stop = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        result[key] = text[mark.start():stop].strip()
    return result


def validate_bind(bind, regions, extra):
    require(isinstance(bind, (list, tuple)) and len(bind) >= 2, "bind must name owner and target")
    owner, target = bind[:2]
    require(isinstance(owner, str) and owner.startswith("scene.") and owner[6:] in regions,
            f"chunk touching the shell: foreign bind owner {owner!r}")
    allowed = regions[owner[6:]][1] | {s[1:] for s in extra.get(owner, [])}
    require(isinstance(target, str) and target.startswith("#") and re.fullmatch(r"#[\w-]+", target) and
            target[1:] in allowed, f"chunk touching the shell: foreign bind target {target!r}")


def merge_build(project, check_chunk=None):
    lead, plan = manifest(project), read_json(project / "plan.json")
    validate_plan(project, lead, plan)
    local = project / "tools_local"
    require(check_chunk is None or check_chunk in {c["id"] for c in lead["chunks"]}, "unknown check chunk")
    require(check_chunk is not None or {p.name for p in (local / "chunks").iterdir() if p.is_dir()} == {c["id"] for c in lead["chunks"]},
            "build chunk directories differ from lead chunks")
    original = {name: (local / name).read_text(encoding="utf-8") for name in ("scenes.py", "timeline.js", "owners.py")}
    base_owners = original["owners.py"]
    for name in TABLES:
        base_owners = strip_generated(base_owners, "#", name)
    base = tables(base_owners)
    extra, helpers = base.get("EXTRA_ROOTS", ({},))[0], base.get("BLOCK_HELPERS", (DEFAULT_HELPERS,))[0]
    merged = {"WINDOWS": [], "EVENT_BINDS": {}, "COPY_BINDS": []}
    all_ids, regions_out, blocks_out, prev_end = set(), [], [], 0
    for chunk in lead["chunks"]:
        if check_chunk is not None and chunk["id"] != check_chunk:
            continue
        folder = local / "chunks" / chunk["id"]
        require({p.name for p in folder.iterdir()} == set(original), f"{chunk['id']}: chunk touching the shell: only three fragments allowed")
        regions = scene_fragments((folder / "scenes.py").read_text(encoding="utf-8"), chunk["prefix"], all_ids)
        blocks = block_fragments((folder / "timeline.js").read_text(encoding="utf-8"))
        require(set(regions) == set(blocks), f"{chunk['id']}: block or region without its partner")
        rows = {k: v[0] for k, v in tables((folder / "owners.py").read_text(encoding="utf-8"), True).items()}
        first = {}
        for row in rows["WINDOWS"]:
            require(isinstance(row, (list, tuple)) and len(row) == 3, "WINDOWS row needs selector, start, end")
            sel, start, end = row
            require(isinstance(sel, str) and sel.startswith("#"), "window needs root selector")
            root = sel[1:]
            prefixed(root, chunk["prefix"])
            require(root in regions, f"window {sel} has no region")
            require(number(start) and number(end) and chunk["start"] <= start < end <= chunk["end"] and start >= prev_end,
                    f"{chunk['id']}: out-of-order windows, overlap, or window outside chunk")
            prev_end = end
            first.setdefault(root, start)
        require(set(first) == set(regions), f"{chunk['id']}: region without window")
        require(list(blocks) == sorted(first, key=first.get), f"{chunk['id']}: blocks not in window order")
        for root in sorted(regions, key=first.get):
            source, ids = regions[root]
            require(not all_ids.intersection(ids), f"duplicate id across chunks: {sorted(all_ids.intersection(ids))}")
            all_ids.update(ids)
            owner = "scene." + root
            allowed_ids = ids | {sel[1:] for sel in extra.get(owner, [])}
            reach = confine.block_reach(blocks[root], helpers)
            problems = confine.block_problems(blocks[root], helpers, reach)
            require(not problems, f"{owner}: {'; '.join(problems)}")
            require(not reach, f"chunk touching the shell: {owner}: {'; '.join(reach)}")
            for sel in SELECTOR.findall(confine.no_comments(BLOCK.sub("", blocks[root], count=1))):
                require(sel in allowed_ids, f"chunk touching the shell: {owner} targets #{sel}")
            check_targets(BLOCK.sub("", blocks[root], count=1), allowed_ids, helpers)
            regions_out.append(source)
            blocks_out.append(blocks[root])
        chunk_events = {eid for b in plan["beats"] if b["id"] in chunk["beats"] for eid in events(b)}
        for eid, bind in rows["EVENT_BINDS"].items():
            require(eid not in merged["EVENT_BINDS"], f"duplicate event id across chunks: {eid}")
            require(eid in chunk_events, f"{chunk['id']}: event belongs to another chunk or is unknown: {eid}")
            validate_bind(bind, regions, extra)
            merged["EVENT_BINDS"][eid] = bind
        for row in rows["COPY_BINDS"]:
            require(len(row) in (5, 6) and row[0] in chunk["beats"], f"{chunk['id']}: invalid copy bind or foreign beat")
            validate_bind((row[2], row[3]), regions, extra)
            merged["COPY_BINDS"].append(row)
        merged["WINDOWS"].extend(rows["WINDOWS"])
    if check_chunk is not None:
        print(f"PASS chunk: {check_chunk}; fragments validated, no files written")
        return
    clean_scenes = strip_generated(original["scenes.py"], "#", "SCENES")
    tail = clean_scenes.split("# @SCENES", 1)
    require(len(tail) == 2 and re.fullmatch(r'''\s*return ["']\\n["']\.join\(S\)\s*''', tail[1]),
            "chunk touching the shell: unmarked content after # @SCENES")
    clean_js = strip_generated(original["timeline.js"], "//", "BLOCKS")
    require("// @BLOCKS" in clean_js and re.match(r"\s*own\(null\);", clean_js.split("// @BLOCKS", 1)[1]),
            "chunk touching the shell: unmarked content after // @BLOCKS")
    write_outputs({
        local / "scenes.py": insert_marker(original["scenes.py"], "# @SCENES", "\n".join(regions_out), "#", "SCENES", "    "),
        local / "timeline.js": insert_marker(original["timeline.js"], "// @BLOCKS", "\n\n".join(blocks_out), "//", "BLOCKS", "        "),
        local / "owners.py": replace_tables(original["owners.py"], merged),
    })
    print(f"PASS build: {len(lead['chunks'])} chunks, {len(regions_out)} regions and blocks")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "build"))
    parser.add_argument("project", type=Path)
    parser.add_argument("--check-chunk", help="build mode: validate only this chunk; write nothing")
    args = parser.parse_args(argv)
    try:
        require(args.mode == "build" or args.check_chunk is None, "--check-chunk requires build mode")
        if args.mode == "plan":
            merge_plan(args.project.resolve())
        else:
            merge_build(args.project.resolve(), args.check_chunk)
    except (OSError, ValueError, KeyError, TypeError, SyntaxError, IndexError) as exc:
        print(f"MERGE REFUSED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
