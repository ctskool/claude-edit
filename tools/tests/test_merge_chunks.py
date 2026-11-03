"""Temp-only tests for deterministic plan/build merging and every refusal class.

Usage: python tools/tests/test_merge_chunks.py
No renderer, project builder, media probe, or live work directory is executed.
"""
import ast
from contextlib import redirect_stderr, redirect_stdout
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/beat_render"))
import merge_chunks as merge

KIT = ROOT / "templates/ivory/build_kit/tools_local"


def put_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def beat(bid, start, end, layout):
    return {"id": bid, "start": start, "end": end, "layout": layout, "say": "Hello",
            "anchor": {"event_id": bid + ".e1", "t": start, "what": "Hello"},
            "sub_anchors": [], "actions": [], "proof_span": None, "proof_span_source": "no audio proof",
            "assets": [], "crops": []}


class MergeChunks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name) / "work" / "stub"
        self.project = self.work / "v2" / "editorial"
        self.parts = self.project / "plan.parts"
        self.local = self.project / "tools_local"
        self.parts.mkdir(parents=True)
        self.local.mkdir()
        for name in ("scenes.py", "timeline.js", "owners.py"):
            (self.local / name).write_text((KIT / name).read_text(encoding="utf-8"), encoding="utf-8")
        self.beats = [beat("b1", 0, 1, "split"), beat("b2", 1, 2, "split"), beat("b3", 2, 4, "full-graphic")]
        self.lead = {"plan": {"duration": 4, "cta_start": None, "cta_start_source": "no CTA",
                     "allow_full_face": False, "allow_full_face_source": "template", "captions": {"style": "mono"},
                     "composition_files": ["tools_local/" + n for n in ("build.py", "scenes.py", "timeline.js", "style.css", "owners.py")]},
                     "chunks": [{"id":"c1","prefix":"c1-","start":0,"end":2,"beats":["b1","b2"]},
                                {"id":"c2","prefix":"c2-","start":2,"end":4,"beats":["b3"]}],
                     "shared": {"hud": [], "caption_style": "mono"}}
        put_json(self.work / "metadata.json", {"duration":4})
        put_json(self.work / "beats.json", {"beats":self.beats})
        self.save_lead()
        for chunk in self.lead["chunks"]:
            selected = [copy.deepcopy(b) for b in self.beats if b["id"] in chunk["beats"]]
            captions = [{"beat":b["id"],"text":"Hello","words":[i],"on":b["start"],"off":b["end"],
                         "position":"seam" if b["layout"] == "split" else "takeover","accent":False,"accent_words":[]}
                        for i,b in enumerate(selected)]
            put_json(self.parts / (chunk["id"] + ".json"), {"chunk":chunk["id"],"beats":selected,
                     "captions":{"chunks":captions},"storyboard":"Measured read-outs and sources"})
            folder = self.local / "chunks" / chunk["id"]
            folder.mkdir(parents=True)
            root = chunk["prefix"] + "scene"
            (folder / "scenes.py").write_text('S.append(own("' + root + '", f\'\'\'<div id="' + root +
                '" class="scene">{lbl("' + root + '-copy", 80, 120, "Hello", 44)}</div>\'\'\'))\n', encoding="utf-8")
            (folder / "timeline.js").write_text('own("scene.' + root + '");\non("#' + root + '-copy", ' + str(chunk["start"]) + ');\n', encoding="utf-8")
            binds = {b["anchor"]["event_id"]:("scene."+root,"#"+root+"-copy","appear","Hello",None)
                     for b in selected}
            copies = [(b["id"],"Hello","scene."+root,"#"+root+"-copy",b["start"]) for b in selected]
            (folder / "owners.py").write_text("WINDOWS = " + repr([["#"+root,chunk["start"],chunk["end"]]]) +
                "\nEVENT_BINDS = " + repr(binds) + "\nCOPY_BINDS = " + repr(copies) + "\n", encoding="utf-8")

    def save_lead(self):
        put_json(self.project / "plan.lead.json", self.lead)

    def part(self, key="c1"):
        return merge.read_json(self.parts / (key + ".json"))

    def save_part(self, value, key="c1"):
        put_json(self.parts / (key + ".json"), value)

    def fragment(self, name, key="c1"):
        return self.local / "chunks" / key / name

    def change(self, path, old, new):
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new), encoding="utf-8")

    def run_mode(self, mode):
        with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
            code = merge.main([mode, str(self.project)])
        return code, out.getvalue() + err.getvalue()

    def plan_ok(self):
        code, output = self.run_mode("plan")
        self.assertEqual(code, 0, output)

    def refused(self, mode, text):
        watched = [self.project / "plan.json", self.project / "STORYBOARD.md"]
        watched += [self.local / n for n in ("scenes.py", "timeline.js", "owners.py")]
        before = {p:p.read_bytes() if p.exists() else None for p in watched}
        code, output = self.run_mode(mode)
        self.assertEqual(code, 1, output)
        self.assertIn("MERGE REFUSED:", output)
        self.assertIn(text, output)
        self.assertEqual(before, {p:p.read_bytes() if p.exists() else None for p in watched})

    def test_plan_orders_beats_keeps_events_and_is_byte_idempotent(self):
        self.plan_ok()
        plan = merge.read_json(self.project / "plan.json")
        self.assertEqual([b["id"] for b in plan["beats"]], ["b1","b2","b3"])
        self.assertEqual([list(merge.events(b)) for b in plan["beats"]], [["b1.e1"],["b2.e1"],["b3.e1"]])
        self.assertEqual(plan["captions"]["style"], "mono")
        before = {p:p.read_bytes() for p in (self.project / "plan.json", self.project / "STORYBOARD.md")}
        self.plan_ok()
        self.assertEqual(before, {p:p.read_bytes() for p in before})

    def test_build_order_spanning_scene_and_byte_idempotence(self):
        self.plan_ok()
        code, output = self.run_mode("build")
        self.assertEqual(code, 0, output)
        sources = {p:p.read_bytes() for p in (self.local / n for n in ("scenes.py","timeline.js","owners.py"))}
        owners = merge.tables((self.local / "owners.py").read_text(encoding="utf-8"))
        self.assertEqual(owners["WINDOWS"][0], [["#c1-scene",0,2],["#c2-scene",2,4]])
        js = (self.local / "timeline.js").read_text(encoding="utf-8")
        self.assertLess(js.index('own("scene.c1-scene")'), js.index('own("scene.c2-scene")'))
        ast.parse((self.local / "scenes.py").read_text(encoding="utf-8"))
        code, output = self.run_mode("build")
        self.assertEqual(code, 0, output)
        self.assertEqual(sources, {p:p.read_bytes() for p in sources})

    def test_gap_and_overlap_refuse_without_writing(self):
        for start in (0.9, 1.1):
            with self.subTest(start=start):
                part = self.part()
                part["beats"][1]["start"] = start
                self.save_part(part)
                self.refused("plan", "no gap or overlap")

    def test_wrong_duration_refuses(self):
        put_json(self.work / "metadata.json", {"duration":5})
        self.refused("plan", "duration does not match metadata.json")

    def test_reordered_or_missing_beat_refuses(self):
        part = self.part()
        part["beats"].reverse()
        self.save_part(part)
        self.refused("plan", "ordered beats differ")

    def test_layout_run_boundary_refuses(self):
        part = self.part("c2")
        part["beats"][0]["layout"] = "split"
        self.save_part(part,"c2")
        self.refused("plan", "inside a layout run")

    def test_event_lost_on_revision_refuses(self):
        self.plan_ok()
        part = self.part()
        part["beats"][0]["anchor"]["event_id"] = "renumbered"
        self.save_part(part)
        self.refused("plan", "event_id lost")

    def test_existing_plan_event_not_in_upstream_is_preserved(self):
        self.plan_ok()
        plan = merge.read_json(self.project / "plan.json")
        plan["beats"][0]["actions"].append({"event_id":"b1.extra","t":0.5,"what":"extra"})
        put_json(self.project / "plan.json", plan)
        self.refused("plan", "existing event_id lost")

    def test_duplicate_event_across_parts_refuses(self):
        part = self.part("c2")
        part["beats"][0]["anchor"]["event_id"] = "b1.e1"
        self.save_part(part,"c2")
        self.refused("plan", "duplicate event id across chunks")

    def test_duplicate_chunk_id_refuses(self):
        self.lead["chunks"][1]["id"] = "c1"
        self.save_lead()
        self.refused("plan", "duplicate id across chunks")

    def test_unsafe_chunk_id_refuses(self):
        self.lead["chunks"][0]["id"] = "../escape"
        self.save_lead()
        self.refused("plan", "unsafe chunk id")

    def test_part_cannot_override_shell(self):
        part = self.part()
        part["duration"] = 99
        self.save_part(part)
        self.refused("plan", "shared top-level")

    def test_missing_or_stale_part_refuses(self):
        (self.parts / "c1.json").rename(self.parts / "stale.json")
        self.refused("plan", "missing or stale part")

    def test_nonfinite_beat_refuses(self):
        part = self.part()
        part["beats"][0]["end"] = float("nan")
        self.save_part(part)
        self.refused("plan", "no gap or overlap")

    def test_missing_prefix_refuses(self):
        self.plan_ok()
        self.change(self.fragment("scenes.py"), "c1-scene-copy", "unprefixed")
        self.refused("build", "missing its chunk prefix")

    def test_duplicate_dom_id_across_chunks_refuses(self):
        self.plan_ok()
        self.change(self.fragment("scenes.py","c2"), "c2-scene-copy", "c1-scene-copy")
        self.refused("build", "duplicate id across chunks")

    def test_duplicate_helper_generated_id_refuses(self):
        self.plan_ok()
        self.change(self.fragment("scenes.py"), "</div>", '<span id="c1-scene-copy"></span></div>')
        self.refused("build", "duplicate id inside region")

    def test_block_without_region_refuses(self):
        self.plan_ok()
        self.change(self.fragment("timeline.js"), "scene.c1-scene", "scene.c1-orphan")
        self.refused("build", "block or region without its partner")

    def test_region_without_block_refuses(self):
        self.plan_ok()
        with self.fragment("scenes.py").open("a", encoding="utf-8") as out:
            out.write('S.append(own("c1-orphan", \'<div id="c1-orphan" class="scene"></div>\'))\n')
        self.refused("build", "block or region without its partner")

    def test_out_of_order_windows_refuse(self):
        self.plan_ok()
        self.change(self.fragment("owners.py"), "[['#c1-scene', 0, 2]]", "[['#c1-scene', 1, 2], ['#c1-scene', 0, 1]]")
        self.refused("build", "out-of-order windows")

    def test_window_outside_chunk_refuses(self):
        self.plan_ok()
        self.change(self.fragment("owners.py"), "[['#c1-scene', 0, 2]]", "[['#c1-scene', 0, 3]]")
        self.refused("build", "window outside chunk")

    def test_region_without_window_refuses(self):
        self.plan_ok()
        self.change(self.fragment("owners.py"), "[['#c1-scene', 0, 2]]", "[]")
        self.refused("build", "region without window")

    def test_chunk_cannot_assign_shared_owner_table(self):
        self.plan_ok()
        with self.fragment("owners.py").open("a", encoding="utf-8") as out:
            out.write("HUD = []\n")
        self.refused("build", "chunk touching the shell")

    def test_chunk_python_is_not_executed(self):
        self.plan_ok()
        self.fragment("scenes.py").write_text('raise RuntimeError("MUST NEVER EXECUTE")\n', encoding="utf-8")
        self.refused("build", "chunk touching the shell")

    def test_timeline_shell_prologue_refuses(self):
        self.plan_ok()
        path = self.fragment("timeline.js")
        path.write_text('tl.set("#face", {opacity:0}, 0);\n' + path.read_text(encoding="utf-8"), encoding="utf-8")
        self.refused("build", "timeline prologue")

    def test_closing_shell_marker_refuses(self):
        self.plan_ok()
        with self.fragment("timeline.js").open("a", encoding="utf-8") as out:
            out.write("own(null);\n")
        self.refused("build", "no own(null)")

    def test_shell_selector_refuses(self):
        self.plan_ok()
        self.change(self.fragment("timeline.js"), "#c1-scene-copy", "#face")
        self.refused("build", "chunk touching the shell")

    def test_computed_or_global_selector_refuses(self):
        self.plan_ok()
        self.change(self.fragment("timeline.js"), '"#c1-scene-copy"', '\'body\'')
        self.refused("build", "exact literal owned id")

    def test_shell_read_refuses(self):
        self.plan_ok()
        self.change(self.fragment("timeline.js"), ', 0);', ', END);')
        # confine.py words it for helpers too ("on() with a time that is not a number").
        self.refused("build", "that is not a number")

    def test_unsafe_markup_refuses(self):
        self.plan_ok()
        self.change(self.fragment("scenes.py"), "</div>", "<script>alert(1)</script></div>")
        self.refused("build", "chunk touching the shell")

    def test_unbalanced_markup_refuses(self):
        self.plan_ok()
        self.change(self.fragment("scenes.py"), "</div>", "")
        self.refused("build", "not closed")

    def test_bind_cannot_touch_shared_owner(self):
        self.plan_ok()
        self.change(self.fragment("owners.py"), "'scene.c1-scene'", "'hud.strip'")
        self.refused("build", "foreign bind owner")

    def test_duplicate_bind_key_refuses(self):
        self.plan_ok()
        self.change(self.fragment("owners.py"), "EVENT_BINDS = {", "EVENT_BINDS = {'b1.e1': ('scene.c1-scene', '#c1-scene-copy'), ")
        self.refused("build", "duplicate id/key")

    def test_wrong_fragment_file_refuses(self):
        self.plan_ok()
        (self.fragment("style.css")).write_text("body {}", encoding="utf-8")
        self.refused("build", "only three fragments")

    def test_repeat_replaces_changed_fragment(self):
        self.plan_ok()
        self.assertEqual(self.run_mode("build")[0],0)
        self.change(self.fragment("scenes.py"), '"Hello"', '"Changed"')
        code, output = self.run_mode("build")
        self.assertEqual(code,0,output)
        text = (self.local / "scenes.py").read_text(encoding="utf-8")
        self.assertEqual(text.count('own("c1-scene"'),1)
        self.assertIn('"Changed"',text)

    def test_authorized_extra_root_and_shared_rows_survive(self):
        self.plan_ok()
        self.change(self.local / "owners.py", "EXTRA_ROOTS = {}", 'EXTRA_ROOTS = {"scene.c1-scene": ["#face"]}')
        self.change(self.local / "owners.py", "HUD = []", 'HUD = [["strip", 0]]')
        self.change(self.fragment("timeline.js"), '"#c1-scene-copy"', '"#face"')
        code, output = self.run_mode("build")
        self.assertEqual(code,0,output)
        text = (self.local / "owners.py").read_text(encoding="utf-8")
        self.assertIn('HUD = [["strip", 0]]',text)
        self.assertIn('"scene.c1-scene": ["#face"]',text)

    def test_missing_marker_refuses(self):
        self.plan_ok()
        self.change(self.local / "scenes.py", "# @SCENES", "# removed")
        self.refused("build", "unmarked content after # @SCENES")


    def test_check_chunk_needs_no_other_fragments_and_writes_nothing(self):
        self.plan_ok()
        # Leave c2 absent while a parallel worker is still preparing it.
        folder = self.fragment("scenes.py", "c2").parent
        for path in folder.iterdir():
            path.unlink()
        folder.rmdir()
        before = {p:p.read_bytes() for p in (self.local / n for n in ("scenes.py","timeline.js","owners.py"))}
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            code = merge.main(["build", str(self.project), "--check-chunk", "c1"])
        self.assertEqual(code, 0)
        self.assertEqual(before, {p:p.read_bytes() for p in before})

    def test_check_chunk_rejects_bad_fragment(self):
        self.plan_ok()
        self.change(self.fragment("timeline.js"), "#c1-scene-copy", "#face")
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
            code = merge.main(["build", str(self.project), "--check-chunk", "c1"])
        self.assertEqual(code, 1)
        self.assertIn("chunk touching the shell", err.getvalue())

    def test_blocks_out_of_window_order_refuse(self):
        self.plan_ok()
        with self.fragment("scenes.py").open("a", encoding="utf-8") as out:
            out.write('S.append(own("c1-second", \'<div id="c1-second" class="scene"></div>\'))\n')
        self.change(self.fragment("owners.py"), "[['#c1-scene', 0, 2]]",
                    "[['#c1-scene', 0, 1], ['#c1-second', 1, 2]]")
        path = self.fragment("timeline.js")
        path.write_text('own("scene.c1-second");\n' + path.read_text(encoding="utf-8"), encoding="utf-8")
        self.refused("build", "blocks not in window order")

    def test_computed_selector_cannot_escape_prefix_checks(self):
        self.plan_ok()
        self.change(self.fragment("timeline.js"), '"#c1-scene-copy"', '\'#\' + \'face\'')
        self.refused("build", "exact literal owned id")

    def test_shared_event_and_copy_rows_are_retained(self):
        self.plan_ok()
        self.change(self.local / "owners.py", "EVENT_BINDS = {}",
                    'EVENT_BINDS = {"hud-event": ("hud.strip", "#strip", "appear", "Shared", None)}')
        self.change(self.local / "owners.py", "COPY_BINDS = []",
                    'COPY_BINDS = [("b1", "Shared", "hud.strip", "#strip", 0)]')
        code, output = self.run_mode("build")
        self.assertEqual(code, 0, output)
        tables = merge.tables((self.local / "owners.py").read_text(encoding="utf-8"))
        self.assertIn("hud-event", tables["EVENT_BINDS"][0])
        self.assertEqual(tables["COPY_BINDS"][0][0][1], "Shared")



    def test_upstream_descriptive_events_without_ids_are_supported(self):
        source = copy.deepcopy(self.beats)
        for b in source:
            b["anchor"].pop("event_id")
        put_json(self.work / "beats.json", {"beats":source})
        self.plan_ok()

    def test_contiguous_windows_for_one_spanning_scene(self):
        self.plan_ok()
        self.change(self.fragment("owners.py"), "[['#c1-scene', 0, 2]]",
                    "[['#c1-scene', 0, 1], ['#c1-scene', 1, 2]]")
        code, output = self.run_mode("build")
        self.assertEqual(code, 0, output)
        text = (self.local / "scenes.py").read_text(encoding="utf-8")
        self.assertEqual(text.count('own("c1-scene"'), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
