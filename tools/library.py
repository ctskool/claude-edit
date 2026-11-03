"""Harvest approved ivory scenes as documented, parameterised reuse templates."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import textwrap

from paths import project_root
ROOT = project_root()
LIBRARY = ROOT / "templates" / "ivory" / "library"
DATA = re.compile(r"<!-- LIBRARY_DATA\n(.*?)\nLIBRARY_DATA -->", re.S)
BLOCK = re.compile(r'^\s*own\(["\'](scene\.[^"\']+)["\']\);[ \t]*$', re.M)
SLOT = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def resolve_project(value):
    path = Path(value)
    if not path.exists() and len(path.parts) == 1:
        path = ROOT / "work" / value
    path = path.resolve()
    if (path / "v2" / "editorial").is_dir():
        return path / "v2" / "editorial"
    if path.name == "editorial" and path.parent.name == "v2":
        return path
    raise ValueError("expected work/<id> or work/<id>/v2/editorial")


def approval(project):
    """Require an active passing record bound to these exact authoring bytes."""
    video = project.parent.parent
    folder = video / "beat" / "approvals"
    try:
        active = load(folder / "active.json")
        picture = active["file_sha256"]
        if not re.fullmatch(r"[0-9a-f]{64}", picture):
            raise ValueError("bad approved file hash")
        record_path = folder / (picture[:16] + ".json")
        record = load(record_path)
        owners = load(project / "ownership.json")
        if record.get("result") not in ("PASS", "RECONCILED"):
            raise ValueError("no passing approval record")
        if record.get("approved_file_sha256") != picture:
            raise ValueError("approval picture mismatch")
        for key in ("composition_rev", "lock_revision"):
            if not record.get(key) or record[key] != active.get(key) or record[key] != owners.get(key):
                raise ValueError("stale approval: " + key)
        authoring = owners["authoring"]
        required = {"plan.json", "tools_local/scenes.py", "tools_local/timeline.js", "tools_local/owners.py", "tools_local/style.css", "tools_local/build.py"}
        if not required.issubset(authoring):
            raise ValueError("approval has no complete authoring fingerprint")
        for name, expected in authoring.items():
            source = (project / name).resolve()
            if project not in source.parents or sha(source) != expected:
                raise ValueError("authoring changed since approval: " + name)
        if owners.get("html_sha256") != sha(project / "index.html"):
            raise ValueError("approved HTML changed")
        return record_path, record
    except (OSError, KeyError, TypeError) as exc:
        raise ValueError("approved project required: " + str(exc)) from exc


def fingerprint(project):
    """The harvester reads source; it never imports or builds a project's code."""
    names = ["plan.json", "ownership.json", "index.html", "beats.lock.json"]
    names += ["tools_local/" + n for n in ("scenes.py", "timeline.js", "owners.py", "style.css", "build.py")]
    return {name: sha(project / name) for name in names}


def segment(source, node):
    # Only remove indentation before the first token. Dedenting all lines would
    # change literal HTML and can leave the statement unexpectedly indented
    # when a multiline f-string has its closing tag at column zero.
    return ast.get_source_segment(source, node)



def defined(node):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return {node.name}
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}


def loaded(node):
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


def scene_regions(source):
    """AST boundaries preserve multiline strings and pull local dependencies."""
    tree = ast.parse(source)
    build = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "build"), None)
    if build is None:
        raise ValueError("scenes.py has no build()")
    definitions, scenes = {}, {}
    for node in build.body:
        matches = [n for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                   and n.func.id == "own" and n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str)]
        # Only direct scene append statements, never an own() inside a helper.
        if isinstance(node, ast.Expr) and matches:
            if len(matches) != 1:
                raise ValueError("ambiguous own() region")
            name = matches[0].args[0].value
            if name in scenes:
                raise ValueError("duplicate scene: " + name)
            pending, selected = list(loaded(node) - {"S"}), {}
            while pending:
                symbol = pending.pop()
                dep = definitions.get(symbol)
                if dep is not None and id(dep) not in selected:
                    selected[id(dep)] = dep
                    pending.extend(loaded(dep) - defined(dep))
            deps = sorted(selected.values(), key=lambda n: n.lineno)
            scenes[name] = "\n\n".join(segment(source, n) for n in deps + [node])
        else:
            for name in defined(node):
                definitions[name] = node
    if not scenes:
        raise ValueError("no literal own() scene regions found")
    return scenes, tree


def timeline_blocks(source):
    matches = list(BLOCK.finditer(source))
    closing = re.search(r"^\s*own\(null\);", source[matches[-1].end():], re.M) if matches else None
    if not matches or closing is None:
        raise ValueError("timeline has no complete scene blocks")
    stop = matches[-1].end() + closing.start()
    out = {}
    for i, match in enumerate(matches):
        name = match[1].removeprefix("scene.")
        if name in out:
            raise ValueError("duplicate timeline block: " + name)
        end = matches[i + 1].start() if i + 1 < len(matches) else stop
        block = source[match.start():end]
        block = re.sub(r"^\s*// @BLOCKS\s*$", "", block, flags=re.M)
        out[name] = textwrap.dedent(block.strip("\n")).rstrip()
    return out


def windows(source):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "WINDOWS" for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError("owners.py has no literal WINDOWS table")


def helper_sources(region, tree):
    """Keep custom module helpers too; ordinary kit helpers remain dependencies."""
    kit_path = ROOT / "templates" / "ivory" / "build_kit" / "tools_local" / "scenes.py"
    kit = ast.parse(kit_path.read_text(encoding="utf-8"))
    kit_names = {n.name for n in kit.body if isinstance(n, ast.FunctionDef)}
    funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name != "build"}
    needed, selected = list(loaded(ast.parse(region))), {}
    while needed:
        name = needed.pop()
        if name in funcs and name not in kit_names and name not in selected:
            selected[name] = funcs[name]
            needed.extend(loaded(funcs[name]) - defined(funcs[name]))
    return sorted(selected.values(), key=lambda n: n.lineno), sorted(set(needed) & kit_names)


def parameterise(scene, python, javascript):
    """Literal slots are source substitutions, not Python/JS format strings."""
    slots = {}
    def slot(kind, value, help_text):
        for key, row in slots.items():
            if row["kind"] == kind and row["example"] == value:
                return "{{" + key + "}}"
        key = "SCENE_ID" if kind == "scene" else kind.upper() + "_" + str(1 + sum(r["kind"] == kind for r in slots.values()))
        slots[key] = {"kind": kind, "example": value, "fill": help_text}
        return "{{" + key + "}}"
    combined = python + "\n" + javascript
    replacements = {scene: slot("scene", scene, "Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds.")}
    # Includes dynamic ids such as ls-c{i} in locally defined row helpers.
    prefixes = sorted(set(re.findall(r'''(?:id=["']|#|(?:card|plate|vplate|drawn|lbl|ol|mark|pill|eqpill|title)\(\s*f?["'])([a-zA-Z][a-zA-Z0-9]*-)[a-zA-Z]''', combined)) - {"sc-"})
    for prefix in prefixes:
        replacements[prefix] = slot("id_prefix", prefix, "Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds.")
    for asset in sorted(set(re.findall(r'[\w./-]+\.(?:png|jpe?g|webp|mp4|svg)', python))):
        replacements[asset] = slot("asset", asset, "Asset path relative to assets/; use real media and remeasure crop/box coordinates.")
    tree = ast.parse(python)
    lines = python.splitlines(keepends=True)
    offsets, total = [], 0
    for line in lines:
        offsets.append(total)
        total += len(line)
    edits = []
    for call in (n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)):
        indexes = {"lbl": [3], "title": [3, 4, 5], "pill": [2], "eqpill": [2]}.get(call.func.id, [])
        for i in indexes:
            if len(call.args) <= i:
                continue
            node = call.args[i]
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str) or not node.value:
                continue
            # AST columns are UTF-8 byte offsets, not character offsets.
            def pos(line, column):
                return offsets[line - 1] + len(lines[line - 1].encode("utf-8")[:column].decode("utf-8"))
            a, b = pos(node.lineno, node.col_offset), pos(node.end_lineno, node.end_col_offset)
            original = python[a:b]
            quote = original[0]
            if quote not in ("'", '"') or original.startswith(quote * 3):
                raise ValueError("unsupported display-copy literal")
            value = slot("copy", original[1:-1], "Exact verified display copy; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS.")
            edits.append((a, b, quote + value + quote))
    for a, b, value in sorted(edits, reverse=True):
        python = python[:a] + value + python[b:]
    def html_copy(match):
        text = match[0]
        if not text.strip() or text.strip().startswith('"'):
            return text
        value = slot("copy", text.strip(), "Exact verified HTML text; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS.")
        return text.replace(text.strip(), value)
    python = re.sub(r'(?<=>)[^<>{}\n]+(?=<)', html_copy, python)
    # One pass prevents values from replacing portions of inserted slot names.
    pattern = re.compile("|".join(re.escape(v) for v in sorted(replacements, key=lambda s: (-len(s), s))))
    return pattern.sub(lambda m: replacements[m[0]], python), pattern.sub(lambda m: replacements[m[0]], javascript), slots


def family(component, python):
    text = component.lower()
    if "repo" in text or "repo-" in python:
        return "repo-card"
    if "command" in text or "terminal" in text:
        return "command-line"
    if "before-state" in text or "before-after" in text:
        return "before-after"
    if "list card" in text or "list item" in text or "numbered" in text:
        return "list-card"
    if "assumed math" in text or "number card" in text or "equation" in text:
        return "number-card"
    if "table" in text:
        return "compare-table"
    if "vplate(" in python:
        return "clip-card"
    if "post art" in text or "post's own art" in text:
        return "art-card"
    if "post" in text and ("plate(" in python):
        return "post-card"
    if python.count("plate(") > 1:
        return "stacked-capture"
    if "doc" in text or "support-page" in text or "support.png" in python:
        return "docs-card"
    if "diagram" in text:
        return "diagram"
    if "plate(" in python:
        return "capture-card"
    return "text-panel"


def snapshot(project, intervals):
    candidates = []
    for dirname in ("snaps_build", "snaps", "snapshots"):
        folder = project / dirname
        if not folder.is_dir():
            continue
        for path in folder.iterdir():
            match = re.search(r"(?:-at-|^)(\d+(?:\.\d+)?)s?\.(?:png|jpg|jpeg)$", path.name, re.I)
            if match:
                at = float(match[1])
                if any(a <= at < b for _, a, b in intervals):
                    candidates.append((abs(at - (intervals[0][1] + intervals[0][2]) / 2), str(path.resolve())))
    return min(candidates)[1] if candidates else None


def collect(project):
    project = resolve_project(project)
    before = fingerprint(project)
    record_path, record = approval(project)
    source = (project / "tools_local" / "scenes.py").read_text(encoding="utf-8-sig")
    js = (project / "tools_local" / "timeline.js").read_text(encoding="utf-8-sig")
    owner_source = (project / "tools_local" / "owners.py").read_text(encoding="utf-8-sig")
    regions, tree = scene_regions(source)
    blocks, wins = timeline_blocks(js), windows(owner_source)
    if set(regions) != set(blocks) or set(regions) != {r[0].lstrip("#") for r in wins}:
        raise ValueError("scene regions, timeline blocks and WINDOWS differ")
    plan = load(project / "plan.json")
    video = project.parent.parent
    project_name = video.name
    variants = []
    for scene, region in regions.items():
        intervals = [r for r in wins if r[0] == "#" + scene]
        beats = [b for b in plan["beats"] if b.get("scene", "").removeprefix("scene.") == scene]
        if not beats:
            beats = [b for b in plan["beats"] if any(b["start"] < end and b["end"] > start for _, start, end in intervals)]
        if not beats or any(not b.get("component") for b in beats):
            raise ValueError("scene has no plan component: " + scene)
        helpers, _ = helper_sources(region, tree)
        if helpers:
            region = "\n\n".join(segment(source, n) for n in helpers) + "\n\n" + region
        components = list(dict.fromkeys(b["component"] for b in beats))
        name = family("; ".join(components), region)
        py, block, slots = parameterise(scene, region, blocks[scene])
        variants.append({"family": name, "project": project_name, "project_path": str(video), "scene": scene,
                         "revision": record["composition_rev"], "approval": str(record_path), "approval_result": record["result"],
                         "beats": [b["id"] for b in beats], "components": components,
                         "purpose": list(dict.fromkeys(str(b.get("why") or b.get("say") or b["component"]) for b in beats)),
                         "windows": intervals, "snapshot": snapshot(project, intervals),
                         "python": py, "javascript": block, "slots": slots,
                         "source_sha256": {n: before[n] for n in ("tools_local/scenes.py", "tools_local/timeline.js", "tools_local/owners.py", "plan.json")},
                         "owner_notes": [line for line in owner_source.splitlines() if '"scene.' + scene + '"' in line and "EXTRA_ROOTS" in line]})
    if fingerprint(project) != before:
        raise ValueError("source changed while reading; nothing harvested")
    return project, variants, before


def read_library(folder):
    entries = {}
    if folder.exists():
        for path in sorted(folder.glob("*.md")):
            if path.name == "INDEX.md":
                continue
            match = DATA.search(path.read_text(encoding="utf-8"))
            if not match:
                raise ValueError("unrecognized library file; refusing overwrite: " + str(path))
            value = json.loads(match[1])
            if value.get("schema") != 1 or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value.get("name", "")) or not isinstance(value.get("variants"), list):
                raise ValueError("invalid library entry: " + str(path))
            entries[value["name"]] = value
    return entries


def proven(entry):
    return len({v["project"] for v in entry["variants"]})


def relative(path, folder):
    return Path(os.path.relpath(path, folder)).as_posix()


def format_entry(entry, folder):
    rows = ["# " + entry["name"], "", "Proven: " + str(proven(entry)) + " approved video(s). Variants: " + str(len(entry["variants"])) + ".", "",
            "Use the closest variant and adapt it to the new beat. Slots use literal {{NAME}} substitution, never str.format: Python f-string braces and JS objects must survive.", "",
            "Fill every slot in both snippets with the same value. ID prefixes end in '-'. Escape copy for its surrounding Python string and for HTML. Slots are authoring source fragments, not executable input. The examples reconstruct the approved source.", "",
            "The Python scene statement belongs in scenes.py build(); any def helpers shown belong before its use. It depends on the ivory build-kit imports/helpers and the project's CSS. Compare custom helpers and CSS with the linked approved source. Namespace local variables/helpers if needed. Do not import or run the donor project.", "",
            "Retiming is required: every timeline position and clip start/duration below is an example in donor seconds. Replace with the new plan's numeric times, retain A(t) alignment, and remeasure asset crops, geometry and highlight boxes. Copy no donor fact or figure without facts.json.", "",
            "Add WINDOWS, EVENT_BINDS and COPY_BINDS in owners.py for the new scene and stable plan event_ids. Inspect EXTRA_ROOTS in the donor owners.py for external targets and their render cost. Rebuild from the kit and run the owner/source checks; these snippets alone are not a ready composition.", ""]
    for i, v in enumerate(entry["variants"], 1):
        rows += ["## Variant " + str(i) + ": " + v["scene"], "", "Used in " + v["project"] + ", beats " + ", ".join(v["beats"]) + ".", "",
                 "Approval: " + v["approval_result"] + "; composition " + v["revision"] + ".", "",
                 "Plan component: " + "; ".join(v["components"]), "", "For: " + " ".join(v["purpose"]), "",
                 "Source: [scenes.py](" + relative(Path(v["project_path"]) / "v2/editorial/tools_local/scenes.py", folder) + "), [owners.py](" + relative(Path(v["project_path"]) / "v2/editorial/tools_local/owners.py", folder) + ").", "",
                 "Window examples: " + json.dumps(v["windows"]) + ".", ""]
        if v["owner_notes"]:
            rows += ["External ownership: " + " ".join(v["owner_notes"]), ""]
        if v["snapshot"]:
            rows += ["![Existing build snapshot (reference; not an approval frame)](" + relative(v["snapshot"], folder) + ")", ""]
        else:
            rows += ["Still: no existing timed snapshot found. No render was started.", ""]
        rows += ["| Slot | Example | Fill with |", "| --- | --- | --- |"]
        for key, row in v["slots"].items():
            example = str(row["example"]).replace("|", "&#124;").replace("\n", " ")
            rows.append("| " + key + " | " + example + " | " + row["fill"] + " |")
        rows += ["", "Python template:", "", "\x60\x60\x60python", v["python"], "\x60\x60\x60", "", "Timeline template:", "", "\x60\x60\x60javascript", v["javascript"], "\x60\x60\x60", ""]
    # Machine state travels with the documented entry; no extra database file.
    rows += ["<!-- LIBRARY_DATA", json.dumps(entry, ensure_ascii=False, indent=2), "LIBRARY_DATA -->", ""]
    return "\n".join(rows)


def format_index(entries):
    rows = ["# Proven ivory components", "", "Read this before directing an ivory video. Prefer a proven component that fits the spoken idea; adapt its closest variant before inventing a new one. House rules, the current facts and Chase's notes govern the adaptation.", "",
            "Proven counts distinct approved video ids, not beats or repeat harvests. Each variant links its source, plan component, purpose, slots and an existing snapshot where available. The fixture is reference data, not automatically proven.", "",
            "| Component | Proven videos | Variants | Used for |", "| --- | ---: | ---: | --- |"]
    for name, entry in sorted(entries.items()):
        purpose = entry["variants"][0]["components"][0].replace("|", "/").replace("\n", " ")
        rows.append(f"| [{name}]({name}.md) | {proven(entry)} | {len(entry['variants'])} | {purpose} |")
    rows += ["", "Run from the repository root:", "", "\x60\x60\x60text", "python tools/library.py list", "python tools/library.py show post-card", "python tools/library.py harvest work/<id>/v2/editorial --dry-run", "python tools/library.py harvest work/<id>/v2/editorial", "\x60\x60\x60", "",
             "Harvest reads only: no project imports, builds, snapshots or renders. It requires an active PASS/RECONCILED record in the video's beat/approvals/, a matching composition/lock, and unchanged approved authoring hashes. --dry-run performs the same checks and extraction without writing. Repeating a harvest does not add a proven video.", "",
             "Reuse: inspect a variant with show, fill every literal {{SLOT}}, retime timeline calls and media to the new plan, remeasure crops/highlights, carry the required CSS/helpers, then author new WINDOWS/EVENT_BINDS/COPY_BINDS and run the kit's checks. Existing snapshot links are references and may predate approval. No number, price or claim inherits verification from a component.", ""]
    return "\n".join(rows)


def harvest(value, folder=LIBRARY, dry_run=False):
    project = resolve_project(value)
    folder = Path(folder).resolve()
    video = project.parent.parent
    if folder == video or video in folder.parents or folder in video.parents:
        raise ValueError("library destination must be outside the source video tree")
    project, variants, before = collect(project)
    entries = read_library(folder)
    for v in variants:
        entry = entries.setdefault(v["family"], {"schema": 1, "name": v["family"], "variants": []})
        identity = (v["project"], v["scene"], v["revision"])
        if not any((old["project"], old["scene"], old["revision"]) == identity for old in entry["variants"]):
            entry["variants"].append(v)
    # Compute everything before any write. All output targets are library files.
    outputs = {name + ".md": format_entry(entry, folder) for name, entry in sorted(entries.items())}
    outputs["INDEX.md"] = format_index(entries)
    if fingerprint(project) != before:
        raise ValueError("source changed before publication; nothing harvested")
    if not dry_run:
        folder.mkdir(parents=True, exist_ok=True)
        for name, content in outputs.items():
            target = folder / name
            if target.is_symlink():
                raise ValueError("refusing library symlink: " + str(target))
            if not target.exists() or target.read_text(encoding="utf-8") != content:
                target.write_text(content, encoding="utf-8")
    print("READ-ONLY source check PASS:", video)
    print("DRY RUN" if dry_run else "HARVESTED", len(variants), "scenes;", len(entries), "component families")
    return entries


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library-dir", type=Path, default=LIBRARY, help="alternate output for tests or a preview")
    sub = parser.add_subparsers(dest="command", required=True)
    harvest_parser = sub.add_parser("harvest")
    harvest_parser.add_argument("project")
    harvest_parser.add_argument("--dry-run", action="store_true")
    sub.add_parser("list")
    show_parser = sub.add_parser("show")
    show_parser.add_argument("name")
    args = parser.parse_args(argv)
    try:
        if args.command == "harvest":
            harvest(args.project, args.library_dir, args.dry_run)
        elif args.command == "list":
            print(format_index(read_library(args.library_dir)))
        else:
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.name):
                raise ValueError("invalid component name")
            entries = read_library(args.library_dir)
            if args.name not in entries:
                raise ValueError("unknown component: " + args.name)
            text = format_entry(entries[args.name], args.library_dir)
            print(text.split("<!-- LIBRARY_DATA", 1)[0].rstrip())
        return 0
    except (OSError, ValueError, SyntaxError, KeyError, TypeError, AttributeError, StopIteration) as exc:
        print("REFUSED", str(exc))
        return 2


if __name__ == "__main__":
    sys.exit(main())
