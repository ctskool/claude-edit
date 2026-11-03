#!/usr/bin/env python3
"""The path from a new raw: the ivory build kit, what recut-build.js tells its agents, and the skill's flow. stage1/phase6-new-raw-path.md.

python tools/tests/test_new_raw_path.py                       logic, plus real builds of a tiny stand-in project. No render
python tools/tests/test_new_raw_path.py --mechanical <work>   one-scene-per-few-beats build of <work>, a folder with words, beats, shared and assets

The mechanical build is the smallest honest stand-in for a builder agent. It proves the path, not the look: every scene is a card, a real plate and the beat's copy.
"""
import html, json, math, os, re, shutil, subprocess, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "templates" / "ivory" / "build_kit"
WORKFLOWS = ROOT / "tools" / "workflows" / "next"
SKILL = ROOT / ".claude" / "skills" / "claude-edit" / "SKILL.md"
UNIT = ROOT / "work" / f"beat-t4-unit-{os.getpid()}"
sys.path[:0] = [str(KIT), str(ROOT / "tools" / "beat_render"), str(ROOT / "tools" / "beat_check"), str(ROOT / "tools" / "tests")]
import new_project
import lock as beat_lock
import ownership
from common import frame_of

FPS = 30
PANEL = {"split": (90, 130, 900, 330), "full-graphic": (90, 130, 900, 560)}
ROWS_AT = {"split": 500, "full-graphic": 740}
ROWS = 5  # rows in a column, of two


def size_of(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,duration", "-of", "json", str(path)], capture_output=True, text=True, check=True)
    s = json.loads(r.stdout)["streams"][0]
    return s["width"], s["height"], float(s.get("duration", 0))


def copy_lines(copy):
    sys.path.append(str(ROOT / "tools" / "beat_check"))
    import events
    return events.lines(copy or {})


def layouts(beats):
    return {b["id"]: "full-graphic" if b.get("layout_hint") == "takeover" else "split" for b in beats}


def groups(beats, layout, size=3):
    """Runs of one layout, at most size beats each."""
    out = []
    for b in beats:
        if out and layout[out[-1][-1]["id"]] == layout[b["id"]] and len(out[-1]) < size:
            out[-1].append(b)
        else:
            out.append([b])
    return out


def first_asset(group, project):
    for b in group:
        for a in b.get("assets", []):
            name = a.split(" ")[0]
            if name.endswith((".png", ".mp4")) and (project / "assets" / name).is_file():
                return name
    return None


def fit(w, h, box):
    x, y, bw, bh = box
    s = min(bw / w, bh / h)
    fw, fh = round(w * s), round(h * s)
    return (x + (bw - fw) // 2, y + (bh - fh) // 2, fw, fh)


def plan_of(root, beats, words, layout):
    meta = json.loads((root / "metadata.json").read_text(encoding="utf8"))
    rows = []
    for b in beats:
        a = b["anchor"]
        rows.append({"id": b["id"], "start": b["start"], "end": b["end"], "dur": round(b["end"] - b["start"], 3), "say": b.get("say", ""), "words": b["words"], "layout": layout[b["id"]],
                     "anchor": {"word_i": a["word"], "t": a["t"], "phrase": words[a["word"]]["text"], "what": a["what"], "event_id": f"{b['id']}.e1"},
                     "sub_anchors": [], "actions": [], "proof_span": None, "assets": [], "component": "mechanical card"})
    chunks = []
    n = len(words)
    for i in range(0, n, 3):
        ids = list(range(i, min(i + 3, n)))
        owner = next(b for b in beats if b["start"] <= max(words[i]["start"], beats[0]["start"]) < b["end"])
        chunks.append({"i": len(chunks), "beat": owner["id"], "text": " ".join(words[k]["text"] for k in ids).upper(), "words": ids, "accent": False, "accent_words": [],
                       "on": round(max(0, words[i]["start"] - 0.067), 3), "off": 0, "position": "takeover" if layout[owner["id"]] == "full-graphic" else "seam"})
    for a, b in zip(chunks, chunks[1:]):
        a["off"] = b["on"]
    chunks[-1]["off"] = meta["duration"]
    return {"project": root.name, "role": "mechanical build through the ivory kit: proves the path, not the look", "duration": meta["duration"], "beats": rows, "captions": {"chunks": chunks},
            "cta_start": beats[-1]["start"], "allow_full_face": False, "allow_full_face_source": "template",
            "composition_files": ["tools_local/build.py", "tools_local/scenes.py", "tools_local/timeline.js", "tools_local/style.css", "tools_local/owners.py"]}


def scene_parts(n, group, layout, project):
    """Python for one scene's markup and JS for its block, as a builder would write them. Each beat's copy shows from its anchor to the beat's end."""
    sid, tag, lay = f"sc-{n:02d}", f"s{n:02d}", layout[group[0]["id"]]
    start, end = group[0]["start"], group[-1]["end"]
    parts = [f'card("{tag}-card", (72, 112, 936, {PANEL[lay][3] + 36}))']
    src = first_asset(group, project)
    if src:
        w, h, duration = size_of(project / "assets" / src)
        box = fit(w, h, PANEL[lay])
        if src.endswith(".mp4"):
            stills = []
            if duration < end - start:
                held = project / "assets" / "held" / f"{tag}.png"
                held.parent.mkdir(exist_ok=True)
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-sseof", "-0.04", "-i", str(project / "assets" / src), "-frames:v", "1", "-update", "1", str(held)], check=True, capture_output=True)
                stills = [(f"{tag}-held", f"held/{tag}.png", "")]
            parts.append(f'vplate("{tag}-pl", {stills!r}, "{src}", (0, 0, {w}, {h}), {box}, {start}, {min(round(end - start, 3), round(duration, 3))}, 0)')
        else:
            parts.append(f'plate("{tag}-pl", "{src}", (0, 0, {w}, {h}), {box})')
    js, events_, copy = [f'        own("scene.{sid}");', f'        // ---- {group[0]["id"]}-{group[-1]["id"]}'], {}, []
    for b in group:
        t, stop = b["anchor"]["t"], b["end"]
        lines = copy_lines(b.get("copy")) or [b.get("say", b["id"])]
        for k, line in enumerate(lines[:ROWS * 2]):
            row = f'{tag}-{b["id"]}-{k}'
            parts.append(f'lbl("{row}", {90 + 460 * (k // ROWS)}, {ROWS_AT[lay] + 48 * (k % ROWS)}, {html.escape(line, quote=False)!r}, 30, "opacity:0")')
            js.append(f'        show("#{row}", {t});')
            if stop != end:
                js.append(f'        hide("#{row}", {stop});')
            if b.get("copy"):
                copy.append((b["id"], line, f"scene.{sid}", f"#{row}", round(max(t, stop - 0.1), 3)))
        events_[f'{b["id"]}.e1'] = (f"scene.{sid}", f'#{tag}-{b["id"]}-0', "appear", None, max(frame_of(stop, FPS) - frame_of(t, FPS), 1))
    python = f'''    S.append(own("{sid}", '<div id="{sid}" class="scene{" full" if lay == "full-graphic" else ""}">' + {" + ".join(parts)} + '</div>'))'''
    return sid, python, "\n".join(js), events_, copy


def write_table(owners_text, name, value):
    old = f"\n{name} = []"
    if old not in owners_text:
        old = f"\n{name} = {{}}"
    if name == "HUD_LABEL":
        old = '\nHUD_LABEL = ""'
    if old not in owners_text:
        raise ValueError(f"owners.py has no {name} table")
    return owners_text.replace(old, f"\n{name} = {value!r}", 1)


def mechanical_build(root, size=3, seats=3):
    """Sets root up from the kit, writes plan.json and the project's tables, and runs its build. Returns the build's CompletedProcess."""
    root = Path(root)
    beats = json.loads((root / "beats.json").read_text(encoding="utf8"))["beats"]
    words = json.loads((root / "words.json").read_text(encoding="utf8"))
    words = words["words"] if isinstance(words, dict) else words
    project = root / "v2" / "editorial"
    if not (project / "tools_local").exists():
        project = new_project.setup(root)
    layout = layouts(beats)
    (project / "plan.json").write_text(json.dumps(plan_of(root, beats, words, layout), indent=1, ensure_ascii=False) + "\n", encoding="utf8", newline="\n")
    cut = groups(beats, layout, size)
    windows, binds, copy, python, blocks = [], {}, [], [], []
    for n, group in enumerate(cut, 1):
        sid, py, js, ev, co = scene_parts(n, group, layout, project)
        windows.append([f"#{sid}", group[0]["start"], group[-1]["end"]])
        python.append(py)
        blocks.append(js)
        binds.update(ev)
        copy += co
    hud = [["strip", beats[0]["anchor"]["t"]]] + [[f"seat{i}", cut[min(1 + i * 2, len(cut) - 1)][0]["anchor"]["t"]] for i in range(seats)] if seats else []
    tools = project / "tools_local"
    text = (tools / "owners.py").read_text(encoding="utf8")
    for name, value in (("WINDOWS", windows), ("HUD", hud), ("HUD_LABEL", "KIT TEST" if hud else ""), ("HUD_PLUGS", [["i-grid", "ic"], ["i-mic", "ic"], ["i-branch", "ic"]][:seats]),
                        ("HUD_BINDS", {"strip": "#strip", **{f"seat{i}": f"#plugs .plug:nth-child({i + 1})" for i in range(seats)}} if hud else {}),
                        ("EVENT_BINDS", binds), ("COPY_BINDS", copy)):
        text = write_table(text, name, value)
    (tools / "owners.py").write_text(text, encoding="utf8", newline="\n")
    (tools / "scenes.py").write_text((tools / "scenes.py").read_text(encoding="utf8").replace("    # @SCENES", "\n".join(python)), encoding="utf8", newline="\n")
    (tools / "timeline.js").write_text((tools / "timeline.js").read_text(encoding="utf8").replace("        // @BLOCKS", "\n\n".join(blocks)), encoding="utf8", newline="\n")
    return build(project)


def build(project):
    return subprocess.run([sys.executable, "-B", "tools_local/build.py"], cwd=project, capture_output=True, text=True, encoding="utf8", errors="replace")


# ---- a stand-in small enough to build in a test


def stand_in(root):
    """A raw with six seconds of words and three beats. Dummy media bytes: nothing here renders."""
    shutil.rmtree(root, ignore_errors=True)
    (root / "assets").mkdir(parents=True)
    (root / "shared" / "logos").mkdir(parents=True)
    (root / "assets" / "face_half.mp4").write_bytes(b"not a real video")
    (root / "assets" / "voice.m4a").write_bytes(b"not real audio")
    (root / "metadata.json").write_text(json.dumps({"duration": 6.0, "fps": 60}), encoding="utf8")
    text = "one two three four five six seven eight nine".split()
    (root / "words.json").write_text(json.dumps([{"i": i, "text": w, "start": round(i * 0.6, 3), "end": round(i * 0.6 + 0.5, 3)} for i, w in enumerate(text)]), encoding="utf8")
    beats = [{"id": "b01", "start": 0.0, "end": 2.0, "words": [0, 2], "say": "one two three", "layout_hint": "split", "anchor": {"word": 1, "t": 0.6, "what": "first card"}, "copy": {"title": "A plain card"}},
             {"id": "b02", "start": 2.0, "end": 4.0, "words": [3, 5], "say": "four five six", "layout_hint": "split", "anchor": {"word": 4, "t": 2.4, "what": "second card"}, "copy": {"title": "B plain card"}},
             {"id": "b03", "start": 4.0, "end": 6.0, "words": [6, 8], "say": "seven eight nine", "layout_hint": "takeover", "anchor": {"word": 7, "t": 4.2, "what": "takeover"}, "copy": {"title": "C full card"}}]
    (root / "beats.json").write_text(json.dumps({"beats": beats}), encoding="utf8")
    return root


class Kit(unittest.TestCase):
    def test_no_one_off_content_is_left(self):
        banned = re.compile(r"1030|1022|sc-hook|sc-grid|cab3|\bb56\b|jarvis|agentic|obsidian|migrate_fixture|sfx_timeline", re.I)
        for path in sorted((KIT / "tools_local").iterdir()) + sorted((KIT / "project").iterdir()) + [KIT / "new_project.py"]:
            if path.is_file():
                self.assertEqual(banned.findall(path.read_text(encoding="utf8")), [], path.name)

    def test_only_the_kits_own_fonts_ship(self):
        css = (KIT / "tools_local" / "style.css").read_text(encoding="utf8")
        named = set(re.findall(r'assets/fonts/([\w.-]+)', css))
        self.assertEqual(named, {p.name for p in (KIT / "assets" / "fonts").iterdir()})

    def test_comments_do_not_trip_the_js_marker_reader(self):
        js = (KIT / "tools_local" / "timeline.js").read_text(encoding="utf8")
        self.assertEqual(len(re.findall(r"\bown\(", js)), 3, "the function, and own(null) twice")

    def test_the_frame_grid_is_where_a_derivative_edits_it(self):
        sys.path.insert(0, str(ROOT / "tools" / "beat_review"))
        import final
        for rel, pattern, _ in final.FPS_EDITS:
            text = (KIT / rel).read_text(encoding="utf8")
            self.assertEqual(len(re.findall(pattern, text, flags=re.M)), 1, f"{rel}: {pattern}")

    def test_block_helpers_exist_in_the_shell(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("kit_owners", KIT / "tools_local" / "owners.py")
        owners = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(owners)
        js = (KIT / "tools_local" / "timeline.js").read_text(encoding="utf8")
        for name in owners.BLOCK_HELPERS:
            self.assertTrue(re.search(rf"(function {name}\(|const {name} = )", js), name)

    def test_cut_in_and_show_share_the_first_visible_frame(self):
        js = (KIT / "tools_local" / "timeline.js").read_text(encoding="utf8")
        expr = re.search(r"const fIn = \(t\) => (.*?);", js)[1]
        times = [i / 1000 for i in range(2000)]
        for fps in (30, 60):
            r = subprocess.run(["node", "-e", f"const FPS={fps}; const fIn=(t)=>{expr}; console.log(JSON.stringify({json.dumps(times)}.map(fIn)))"], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            for t, actual in zip(times, json.loads(r.stdout)):
                self.assertEqual(actual, frame_of(t, fps) / fps, (t, fps))


class KitProject(unittest.TestCase):
    """Real builds on a stand-in. Each test edits its own copy of the sources back to clean."""

    @classmethod
    def setUpClass(cls):
        cls.root = stand_in(UNIT)
        cls.result = mechanical_build(cls.root, size=2, seats=1)
        cls.project = cls.root / "v2" / "editorial"
        cls.clean = {name: (cls.project / "tools_local" / name).read_text(encoding="utf8") for name in ("build.py", "scenes.py", "timeline.js", "owners.py")}
        cls.plan = (cls.project / "plan.json").read_text(encoding="utf8")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def tearDown(self):
        for name, text in self.clean.items():
            (self.project / "tools_local" / name).write_text(text, encoding="utf8", newline="\n")
        (self.project / "plan.json").write_text(self.plan, encoding="utf8", newline="\n")

    def edit(self, name, old, new):
        path = self.project / "tools_local" / name
        text = path.read_text(encoding="utf8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding="utf8", newline="\n")

    def stopped(self, needle):
        r = build(self.project)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("BUILD STOPPED", r.stderr)
        self.assertIn(needle, r.stderr)
        self.assertIn("README.md", r.stderr)
        self.assertFalse((self.project / "ownership.json").exists(), "run.py would accept a stopped build")

    def test_the_first_build_writes_all_three_files(self):
        self.assertEqual(self.result.returncode, 0, self.result.stderr)
        for name in ("beats.lock.json", "ownership.json", "events.json", "index.html"):
            self.assertTrue((self.project / name).is_file(), name)

    def test_the_build_is_one_run_py_accepts(self):
        self.assertEqual(build(self.project).returncode, 0)
        lock = beat_lock.load(self.project)
        m = ownership.load(self.project)
        self.assertIsNotNone(m)
        self.assertEqual(m["lock_revision"], lock["revision"])
        import run
        self.assertEqual(run.stale_files(self.project, m), [])

    def test_scenes_are_local_and_nothing_stays_in_the_shell(self):
        self.assertEqual(build(self.project).returncode, 0)
        m = ownership.load(self.project)
        self.assertEqual(m["shared"]["unconfined"], {})
        self.assertTrue([o for o in m["owners"] if o["kind"] == "scene"])
        self.assertEqual({o["kind"] for o in m["owners"]}, {"scene", "caption", "hud"})

    def test_a_label_position_stops_the_build(self):
        self.edit("timeline.js", '        // ---- b01', '        tl.to("#s01-card", { x: 1, duration: 0.2, ease: "none" }, "<");\n        // ---- b01')
        self.stopped("label or relative position")

    def test_a_tween_with_no_position_stops_the_build(self):
        self.edit("timeline.js", '        // ---- b01', '        tl.to("#s01-card", { x: 1, duration: 0.2, ease: "none" });\n        // ---- b01')
        self.stopped("with no position")

    def test_a_position_that_is_not_a_number_stops_the_build(self):
        self.edit("timeline.js", '        // ---- b01', '        tl.to("#s01-card", { x: 1, duration: 0.2, ease: "none" }, END);\n        // ---- b01')
        self.stopped("not a number")

    def test_a_chained_tween_stops_the_build(self):
        self.edit("timeline.js", '        // ---- b01', '        tl.to("#s01-card", { x: 1, duration: 0.2, ease: "none" }, 1).to("#s01-card", { x: 2, duration: 0.2, ease: "none" }, 1.5);\n        // ---- b01')
        self.stopped("chained")

    def test_a_region_that_is_not_one_element_stops_the_build(self):
        self.edit("scenes.py", "+ '</div>'))", "+ '</div><div></div>'))")
        self.stopped("top-level elements")

    def test_a_scene_taking_a_shell_id_stops_the_build(self):
        self.edit("scenes.py", 'card("s01-card"', 'card("strip"')
        self.stopped("#strip")

    def test_a_scene_with_no_window_stops_the_build(self):
        self.edit("owners.py", "WINDOWS = [['#sc-01', 0.0, 4.0], ['#sc-02', 4.0, 6.0]]", "WINDOWS = [['#sc-01', 0.0, 4.0]]")
        self.stopped("windows and owners differ")

    def test_a_tag_off_the_list_warns_a_whole_render_and_still_builds(self):
        self.edit("scenes.py", '''class="scene">' + ''', '''class="scene"><canvas></canvas>' + ''')
        r = build(self.project)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("WHOLE RENDER: scene.sc-01", r.stdout)
        self.assertIn("contains <canvas>", r.stdout)
        self.assertIn("scene.sc-01", ownership.load(self.project)["shared"]["unconfined"])

    def test_a_template_literal_warns_a_whole_render(self):
        self.edit("timeline.js", '        // ---- b01', '        show(`#s01-card`, 1);\n        // ---- b01')
        r = build(self.project)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("WHOLE RENDER: scene.sc-01", r.stdout)
        self.assertIn("template literal", r.stdout)

    def test_a_copy_bind_with_no_line_stops_the_build(self):
        self.edit("owners.py", "A plain card", "Not in beats")
        self.stopped("copy binds that match no line")

    def test_a_plan_missing_what_the_build_needs_stops_it_in_words(self):
        plan = json.loads(self.plan)
        del plan["composition_files"]
        plan_path = self.project / "plan.json"
        plan_path.write_text(json.dumps(plan), encoding="utf8")
        self.stopped('no "composition_files"')

    def test_a_full_face_beat_needs_the_permission(self):
        plan = json.loads(self.plan)
        plan["beats"][0]["layout"] = "full-face"
        (self.project / "plan.json").write_text(json.dumps(plan), encoding="utf8")
        self.stopped("allow_full_face is not true")

    def test_an_event_with_no_id_stops_the_build(self):
        plan = json.loads(self.plan)
        del plan["beats"][1]["anchor"]["event_id"]
        (self.project / "plan.json").write_text(json.dumps(plan), encoding="utf8")
        self.stopped("no event_id")

    def test_a_plan_that_does_not_reach_the_duration_stops_the_build(self):
        plan = json.loads(self.plan)
        plan["beats"][-1]["end"] = 5.5
        (self.project / "plan.json").write_text(json.dumps(plan), encoding="utf8")
        self.stopped("metadata.json's duration")

    def test_a_chip_never_opens_further_ahead_of_its_word_than_the_source_check_allows(self):
        # The third chip lands within the snap of the 4.0 switch, 6 frames ahead of its first word, so its old chip stops on the switch and it waits.
        plan = json.loads(self.plan)
        first, last = plan["captions"]["chunks"][-2:]
        first.update(words=[3, 4, 5, 6], off=4.1)
        last.update(words=[7, 8], text="EIGHT NINE", on=4.1, position="takeover")
        (self.project / "plan.json").write_text(json.dumps(plan), encoding="utf8")
        self.assertEqual(build(self.project).returncode, 0)
        caps, _ = ownership.data_of((self.project / "index.html").read_text(encoding="utf8"), "CAPS")
        self.assertEqual(caps[-2][1], 4.0)
        self.assertEqual(caps[-1][0], 4.1)

    def test_a_scene_at_time_zero_is_up_on_the_first_frame(self):
        js = (KIT / "tools_local" / "timeline.js").read_text(encoding="utf8")
        self.assertIn("if (a > 0) show(s, a); else tl.set(s, { opacity: 1, immediateRender: true }, 0);", js)

    def test_new_project_refuses_to_overwrite_a_builders_sources(self):
        before = (self.project / "tools_local" / "scenes.py").read_bytes()
        shared = self.root / "shared" / "scenes" / "late.png"
        shared.parent.mkdir(exist_ok=True)
        shared.write_bytes(b"new shared image")
        self.assertEqual(new_project.setup(self.root), self.project)
        self.assertEqual((self.project / "tools_local" / "scenes.py").read_bytes(), before)
        self.assertEqual((self.project / "assets" / "scenes" / "late.png").read_bytes(), shared.read_bytes())

    def test_missing_duration_stops_before_a_render(self):
        plan = json.loads(self.plan)
        del plan["duration"]
        (self.project / "plan.json").write_text(json.dumps(plan), encoding="utf8")
        self.stopped('no "duration"')

    def test_wrong_duration_stops_before_a_render(self):
        for duration in (5.0, "6", True, None):
            with self.subTest(duration=duration):
                plan = json.loads(self.plan)
                plan["duration"] = duration
                (self.project / "plan.json").write_text(json.dumps(plan), encoding="utf8")
                self.stopped("duration must equal metadata.json")

    def test_missing_script_text_stops_before_the_player_is_blank(self):
        plan = json.loads(self.plan)
        del plan["beats"][0]["say"]
        (self.project / "plan.json").write_text(json.dumps(plan), encoding="utf8")
        self.stopped('no "say"')

    def test_full_face_media_start_uses_the_source_grid_at_both_output_rates(self):
        plan = json.loads(self.plan)
        plan["allow_full_face"] = True
        plan["allow_full_face_source"] = "test request"
        plan["beats"][0]["end"] = plan["beats"][1]["start"] = 2.051
        plan["beats"][1]["layout"] = "full-face"
        (self.project / "assets" / "face_full.mp4").write_bytes(b"test media, no render")
        (self.project / "plan.json").write_text(json.dumps(plan), encoding="utf8")
        for fps in (30, 60):
            if fps == 60:
                self.edit("build.py", "FPS = 30", "FPS = 60")
                self.edit("build.py", 'data-fps="30"', 'data-fps="60"')
            r = build(self.project)
            self.assertEqual(r.returncode, 0, r.stderr)
            text = (self.project / "index.html").read_text(encoding="utf8")
            tag = re.search(r'<video id="ff-b02"[^>]+>', text)[0]
            f0 = frame_of(2.051, 30)
            old_start = math.floor(f0 / 30 * 1e5) / 1e5
            old_media = math.ceil(f0 / 30 * 1e4) / 1e4
            self.assertEqual(float(re.search(r'data-start="([^"]+)"', tag)[1]), old_start)
            self.assertEqual(float(re.search(r'data-media-start="([^"]+)"', tag)[1]), old_media)

    def test_a_missing_scene_image_stops_in_words(self):
        self.edit("scenes.py", "    S = []", '    S = []\n    plate("missing-pl", "scenes/missing.png", (0, 0, 100, 100), (0, 0, 100, 100))')
        self.stopped("missing.png")

    def test_extra_roots_report_their_rebuild_cost(self):
        self.edit("owners.py", "EXTRA_ROOTS = {}", 'EXTRA_ROOTS = {"scene.sc-01": ["#face"]}')
        self.edit("timeline.js", "        // ---- b01", '        tl.set("#face", {scale: 1.08}, A(0.6));\n        tl.set("#face", {scale: 1}, A(1.6));\n        // ---- b01')
        r = build(self.project)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("WHOLE RENDER: scene.sc-01", r.stdout)
        self.assertIn("extra roots", r.stdout)
        scene = next(o for o in ownership.load(self.project)["owners"] if o["id"] == "scene.sc-01")
        self.assertEqual(scene["frames"], [[0, 180]])

    def test_new_project_refuses_a_project_with_no_spine(self):
        with self.assertRaises(ValueError) as e:
            new_project.setup(self.root / "nothing-here")
        self.assertIn("metadata.json", str(e.exception))


class SetUp(unittest.TestCase):
    def test_face_full_stays_out_unless_asked(self):
        root = stand_in(UNIT.with_name(UNIT.name + "-setup"))
        try:
            project = new_project.setup(root)
            self.assertTrue((project / "assets" / "face_half.mp4").is_file())
            self.assertFalse((project / "assets" / "face_full.mp4").exists())
            self.assertTrue((project / "assets" / "vendor" / "gsap.min.js").is_file())
            self.assertEqual(json.loads((project / "meta.json").read_text(encoding="utf8"))["id"], root.name + "-editorial")
            self.assertEqual(json.loads((project / "package.json").read_text(encoding="utf8"))["scripts"]["render"], "npx --yes hyperframes@0.8.184 render")
        finally:
            shutil.rmtree(root, ignore_errors=True)


class Workflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import test_full_face as tf
        cls.tf = tf
        cls.args = {"id": "t1", "styles": ["editorial"]}
        cls.run_ok = tf.run_workflow("recut-build.js", cls.args)
        cls.prompts = {p["label"]: p["prompt"] for p in cls.run_ok["prompts"]}
        cls.source = (WORKFLOWS / "recut-build.js").read_text(encoding="utf8")

    def test_the_builder_starts_from_the_kit_not_an_old_project(self):
        build_prompt = self.prompts["build:editorial"]
        self.assertIn("new_project.py t1", build_prompt)
        self.assertNotIn("tools_local\\ build machinery", build_prompt)
        self.assertNotIn("1022-2", self.source)

    def test_the_builder_is_told_what_it_must_write(self):
        build_prompt = self.prompts["build:editorial"]
        for word in ("WINDOWS", "EVENT_BINDS", "COPY_BINDS", "HUD_BINDS", "BUILD STOPPED", "WHOLE RENDER", "conform.py", "--audit", "number", "build.py", "README.md"):
            self.assertIn(word, build_prompt, word)

    def test_the_director_writes_the_fields_the_build_needs(self):
        direct = self.prompts["direct:editorial"]
        for word in ("event_id", "proof_span", "cta_start", "composition_files", "sub_anchors", "captions"):
            self.assertIn(word, direct, word)

    def test_a_failed_plan_check_still_refuses_and_the_builder_never_runs(self):
        run = self.tf.run_workflow("recut-build.js", self.args, {"ok": False, "issues": ["stub"]})
        self.assertEqual([p["label"] for p in run["prompts"]], ["direct:editorial", "plancheck:editorial"])
        self.assertIs(run["result"][0]["refused"], True)

    def test_a_style_with_no_kit_is_refused_before_any_agent(self):
        run = self.tf.run_workflow("recut-build.js", {"id": "t1", "styles": ["dense"]})
        self.assertEqual(run["prompts"], [])
        self.assertIs(run["result"][0]["refused"], True)
        self.assertIn("kit", run["result"][0]["reason"])

    def test_the_old_ref_argument_changes_nothing(self):
        self.assertEqual(self.tf.dry_run("recut-build.js", {**self.args, "ref": "1022-2"}), self.prompts)

    def test_plan_issues_return_to_the_director(self):
        prompts = self.tf.dry_run("recut-build.js", {**self.args, "planIssues": ["wrong proof span"]})
        direct = prompts["direct:editorial"]
        for text in ("wrong proof span", "revise the existing plan.json", "keep every event_id"):
            self.assertIn(text, direct)

    def test_builder_retry_skips_direct_but_rechecks_the_existing_plan(self):
        run = self.tf.run_workflow("recut-build.js", {**self.args, "skipDirect": True, "note": "fix owner audit"})
        self.assertEqual([p["label"] for p in run["prompts"]], ["plancheck:editorial", "build:editorial"])
        self.assertIn("fix owner audit", run["prompts"][-1]["prompt"])
        run = self.tf.run_workflow("recut-build.js", {**self.args, "skipDirect": True}, {"ok": False, "issues": ["stale"]})
        self.assertEqual([p["label"] for p in run["prompts"]], ["plancheck:editorial"])
        self.assertIs(run["result"][0]["refused"], True)

    def test_intake_notes_reach_all_content_agents(self):
        note = 'Use the pricing page; no GitHub screenshot.'
        for script in ("recut-plan.js", "recut-build.js"):
            run = self.tf.run_workflow(script, {**self.args, "note": note})
            for row in run["prompts"]:
                self.assertIn(note, row["prompt"], row["label"])

    def test_null_stage_results_stop_the_content_workflow(self):
        labels = ["research", "assets", "plan", "check", "plan-revise"]
        for i, label in enumerate(labels):
            with self.subTest(label=label):
                run = self.tf.run_workflow("recut-plan.js", self.args, replies={label: None})
                self.assertEqual([p["label"] for p in run["prompts"]], labels[:i + 1])
                self.assertTrue(run["result"].get("error"))

    def test_null_director_stops_before_plan_check_or_build(self):
        run = self.tf.run_workflow("recut-build.js", self.args, replies={"direct:editorial": None})
        self.assertEqual([p["label"] for p in run["prompts"]], ["direct:editorial"])
        self.assertIs(run["result"][0]["refused"], True)

    def test_source_check_is_in_the_pre_render_qa_loop(self):
        prompt = self.prompts["build:editorial"]
        self.assertLess(prompt.index("--audit"), prompt.index("--all"))
        self.assertIn("exit 3", prompt)
        self.assertIn("no FAIL", prompt)
        schema = next(p["schema"] for p in self.run_ok["prompts"] if p["label"] == "build:editorial")
        self.assertIn("source_check", schema["required"])

    def test_scene_images_belong_to_the_director(self):
        # Scene images exist only with Codex; without it the director plans none.
        prompts = {p["label"]: p["prompt"] for p in self.tf.run_workflow("recut-build.js", {**self.args, "codex": True})["prompts"]}
        self.assertIn("shared/scenes", prompts["direct:editorial"])
        self.assertIn("ASSETS.md", prompts["direct:editorial"])
        self.assertIn("generate any missing scene image", prompts["direct:editorial"])
        self.assertNotIn("generate any missing scene image", prompts["build:editorial"])
        self.assertIn("plan no scene images", self.prompts["direct:editorial"])

    def test_short_clips_have_a_held_frame_recipe(self):
        for text in ("vplate", "stills", "assets/held", "ffmpeg"):
            self.assertIn(text, self.prompts["build:editorial"])

    def test_proof_and_cta_have_transcript_sources(self):
        prompts = self.tf.dry_run("recut-plan.js", self.args)
        for label in ("plan", "check"):
            for text in ("proof_span", "cta_start", "word", "sound.md"):
                self.assertIn(text, prompts[label])

    def test_revision_beats_skip_direct_when_both_are_requested(self):
        prompts = self.tf.dry_run("recut-build.js", {**self.args, "skipDirect": True, "planIssues": ["fix crop"]})
        self.assertIn("fix crop", prompts["direct:editorial"])


class Skill(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SKILL.read_text(encoding="utf8")

    def test_the_flow_is_named_in_order(self):
        at = [self.text.index(w) for w in ("## 2. Spine", "## 3. Facts", "## 4. First edit", "## 5. Review render", "## 6. Player", "## 7. Note round", "## 8. Approval", "## 9. Sound", "## 10. Final")]
        self.assertEqual(at, sorted(at))

    def test_the_old_pre_build_stage_is_gone(self):
        for word in ("plan-picks", "selection.json", "picture-preview"):
            self.assertNotIn(word, self.text, word)

    def test_it_says_what_to_do_with_refused(self):
        self.assertIn("refused: true", self.text)

    def test_the_note_round_is_all_there(self):
        for word in ("freeze(", "ownership", "never generated HTML", "beats.json", "copy", "real footage", "verified numbers", "his note wins", "python tools_local/build.py", "run.py change", "close_round(", "done", "not done", "BUILD STOPPED", "WHOLE RENDER"):
            self.assertIn(word, self.text, word)

    def test_the_player_port(self):
        self.assertIn("4750", self.text)

    def test_moves_stay_out(self):
        self.assertIn("Moves stay out", self.text)

    def test_listening_stop_precedes_source_prep(self):
        stop = self.text.index("**Stop for the one-minute cut listen.**")
        self.assertLess(stop, self.text.index("python tools/prep_source.py"))
        self.assertLess(stop, self.text.index("python tools/make_words.py"))

    def test_intake_and_retry_arguments_are_documented(self):
        for text in ("planIssues", "skipDirect", "intake notes", "assets.notes", "revision", "check"):
            self.assertIn(text, self.text)
        self.assertRegex(self.text, r"Create `work/<id>/RUN.md`[^\n]*intake notes")

    def test_flagged_notes_name_the_explicit_adopt_call(self):
        self.assertIn("review.freeze(project, adopt=[", self.text)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--mechanical":
        result = mechanical_build(Path(sys.argv[2]))
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        sys.exit(result.returncode)
    unittest.main()
