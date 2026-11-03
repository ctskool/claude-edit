"""Approved harvest tests. Run: python -B tools/tests/test_library.py (no renders)."""
import ast
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import library

SCENES = '''"""Synthetic scene source: imports must never execute."""
raise RuntimeError("do not import donor code")
def mark(id_, b):
    return f'<div id="{id_}">{b}</div>'
def build():
    S = []
    POST = "posts/example.png"
    BOX = (90, 200, 900, 400)
    def pill(id_, y, text, strike):
        return f'<div id="{id_}">{text}</div>'
    S.append(own("sc-one", f\'\'\'<div id="sc-one" class="scene">
      {card("aa-card", BOX)}
      {plate("aa-pl", POST, (0, 0, 900, 400), BOX)}
      {lbl("aa-tag", 100, 600, "A verified phrase", 34)}
      <span id="aa-n">4x</span><span id="aa-eq">=</span>
    </div>\'\'\'))
    S.append(own("sc-two", f\'\'\'<div id="sc-two" class="scene">
      {pill("bb-pill", 200, "Old name", "bb-strike")}
      <span id="bb-caption">Another phrase</span>
    </div>\'\'\'))
    return "".join(S)
'''
TIMELINE = '''(function () {
    own("scene.sc-one");
    cutIn("#aa-card", 0, 2);
    own("scene.sc-two");
    on("#bb-pill", 2.1);
    // @BLOCKS
    own(null);
    on("#shell", 0);
})();
'''


class Library(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.video = self.root / "sample"
        self.project = self.make_project(self.video)
        self.output = self.root / "library"

    def make_project(self, video):
        project = video / "v2" / "editorial"
        local = project / "tools_local"
        local.mkdir(parents=True)
        (local / "scenes.py").write_text(SCENES, encoding="utf-8")
        (local / "timeline.js").write_text(TIMELINE, encoding="utf-8")
        (local / "owners.py").write_text('WINDOWS = [["#sc-one", 0, 2], ["#sc-two", 2, 4]]\n', encoding="utf-8")
        (local / "style.css").write_text(".scene {}\n", encoding="utf-8")
        (local / "build.py").write_text('raise RuntimeError("must not execute")\n', encoding="utf-8")
        beats = [{"id": "b01", "scene": "sc-one", "start": 0, "end": 2, "component": "post card plate", "why": "Use a real quote"},
                 {"id": "b02", "scene": "sc-two", "start": 2, "end": 4, "component": "before-after", "why": "Show a rename"}]
        (project / "plan.json").write_text(json.dumps({"beats": beats}), encoding="utf-8")
        (project / "index.html").write_text("<html></html>", encoding="utf-8")
        (project / "beats.lock.json").write_text("{}", encoding="utf-8")
        folder = video / "beat" / "approvals"
        folder.mkdir(parents=True)
        picture, revision, lock = "a" * 64, "b" * 64, "c" * 64
        active = {"file_sha256": picture, "composition_rev": revision, "lock_revision": lock}
        (folder / "active.json").write_text(json.dumps(active), encoding="utf-8")
        record = {"approved_file_sha256": picture, "composition_rev": revision, "lock_revision": lock, "result": "PASS"}
        (folder / (picture[:16] + ".json")).write_text(json.dumps(record), encoding="utf-8")
        names = ["plan.json"] + ["tools_local/" + n for n in ("scenes.py", "timeline.js", "owners.py", "style.css", "build.py")]
        owners = {"composition_rev": revision, "lock_revision": lock, "html_sha256": library.sha(project / "index.html"),
                  "authoring": {n: library.sha(project / n) for n in names}}
        (project / "ownership.json").write_text(json.dumps(owners), encoding="utf-8")
        snaps = project / "snaps_build"
        snaps.mkdir()
        (snaps / "frame-00-at-1s.png").write_bytes(b"snapshot reference, not rendered")
        return project

    def harvest(self, project=None, **kwargs):
        with redirect_stdout(io.StringIO()):
            return library.harvest(project or self.project, self.output, **kwargs)

    def bytes_in_video(self):
        return {p.relative_to(self.video).as_posix(): p.read_bytes() for p in self.video.rglob("*") if p.is_file()}

    def test_harvest_is_read_only_and_dry_run_writes_nothing(self):
        before = self.bytes_in_video()
        self.harvest(dry_run=True)
        self.assertFalse(self.output.exists())
        entries = self.harvest()
        self.assertEqual(self.bytes_in_video(), before)
        self.assertEqual(set(entries), {"post-card", "before-after"})
        self.assertIn("frame-00-at-1s.png", (self.output / "post-card.md").read_text(encoding="utf-8"))
        self.assertIn("Used in sample, beats b01", (self.output / "post-card.md").read_text(encoding="utf-8"))

    def test_dependencies_are_self_contained_without_resetting_scene_list(self):
        regions, _ = library.scene_regions(SCENES)
        self.assertIn('POST = "posts/example.png"', regions["sc-one"])
        self.assertIn("BOX =", regions["sc-one"])
        self.assertNotIn("S = []", regions["sc-one"])
        self.assertNotIn("sc-two", regions["sc-one"])
        self.assertIn("def pill", regions["sc-two"])
        self.assertNotIn("POST =", regions["sc-two"])
        ast.parse(regions["sc-one"])
        ast.parse(regions["sc-two"])

    def test_slots_cover_copy_ids_and_assets_and_restore_valid_source(self):
        entries = self.harvest()
        v = entries["post-card"]["variants"][0]
        self.assertIn("{{SCENE_ID}}", v["python"])
        self.assertIn("#{{ID_PREFIX_1}}card", v["javascript"])
        self.assertEqual({r["example"] for r in v["slots"].values() if r["kind"] == "copy"}, {"A verified phrase", "4x", "="})
        self.assertNotIn("border-", [r["example"] for r in v["slots"].values() if r["kind"] == "id_prefix"])
        restored = v["python"]
        for key, row in v["slots"].items():
            restored = restored.replace("{{" + key + "}}", row["example"])
        self.assertNotRegex(restored, library.SLOT)
        self.assertIn("POST =", restored)
        self.assertIn(">=</span>", restored)
        ast.parse(restored)

    def test_escaped_copy_restores_its_source_literal(self):
        source = 'S.append(own("sc-x", lbl("xx-label", 1, 2, "Say \\"hi\\"", 40)))'
        python, javascript, slots = library.parameterise("sc-x", source, 'own("scene.sc-x");')
        for key, row in slots.items():
            python = python.replace("{{" + key + "}}", row["example"])
        self.assertEqual(python, source)
        ast.parse(python)

    def test_repeat_harvest_is_idempotent_and_proven_counts_videos(self):
        first = self.harvest()
        bytes_before = {p.name: p.read_bytes() for p in self.output.iterdir()}
        second = self.harvest()
        self.assertEqual(first, second)
        self.assertEqual(bytes_before, {p.name: p.read_bytes() for p in self.output.iterdir()})
        other = self.make_project(self.root / "another-video")
        third = self.harvest(other)
        self.assertEqual(library.proven(third["post-card"]), 2)
        self.assertEqual(len(third["post-card"]["variants"]), 2)

    def test_failed_missing_and_stale_approval_refused(self):
        record = self.video / "beat" / "approvals" / ("a" * 16 + ".json")
        value = library.load(record)
        value["result"] = "FAIL"
        record.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            self.harvest()
        value["result"] = "PASS"
        value["composition_rev"] = "d" * 64
        record.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            self.harvest()
        record.unlink()
        with self.assertRaises(ValueError):
            self.harvest()
        self.assertFalse(self.output.exists())

    def test_reconciled_record_is_passing_but_active_record_required(self):
        record = self.video / "beat" / "approvals" / ("a" * 16 + ".json")
        value = library.load(record)
        value["result"] = "RECONCILED"
        record.write_text(json.dumps(value))
        self.harvest()
        (record.parent / "active.json").unlink()
        with self.assertRaises(ValueError):
            self.harvest()

    def test_source_changes_after_approval_are_refused(self):
        for relative in ("plan.json", "tools_local/scenes.py", "tools_local/owners.py", "index.html"):
            path = self.project / relative
            original = path.read_bytes()
            path.write_bytes(original + b"\n")
            with self.subTest(path=relative), self.assertRaises(ValueError):
                self.harvest()
            path.write_bytes(original)
        self.assertFalse(self.output.exists())

    def test_destination_cannot_be_in_source_tree(self):
        with self.assertRaises(ValueError):
            library.harvest(self.project, self.project / "library")

    def test_timeline_boundaries_exclude_shell_and_detect_duplicates(self):
        blocks = library.timeline_blocks(TIMELINE)
        self.assertEqual(set(blocks), {"sc-one", "sc-two"})
        self.assertNotIn("#shell", blocks["sc-two"])
        self.assertNotIn("@BLOCKS", blocks["sc-two"])
        self.assertNotIn("sc-two", blocks["sc-one"])
        with self.assertRaises(ValueError):
            library.timeline_blocks(TIMELINE.replace('own("scene.sc-two")', 'own("scene.sc-one")'))

    def test_list_show_and_unknown_component_exit_codes(self):
        self.harvest()
        for command in (["list"], ["show", "post-card"]):
            out = io.StringIO()
            with redirect_stdout(out):
                result = library.main(["--library-dir", str(self.output)] + command)
            self.assertEqual(result, 0, out.getvalue())
            self.assertIn("post-card", out.getvalue())
        with redirect_stdout(io.StringIO()):
            self.assertEqual(library.main(["--library-dir", str(self.output), "show", "unknown"]), 2)
            self.assertEqual(library.main(["--library-dir", str(self.output), "show", "../escape"]), 2)

    def test_fixture_is_only_parsed_never_built(self):
        project = library.ROOT / "work/beat-fixture/v2/editorial"
        if not project.exists():
            self.skipTest("fixture not installed")
        before = library.fingerprint(project)
        regions, _ = library.scene_regions((project / "tools_local/scenes.py").read_text(encoding="utf-8"))
        blocks = library.timeline_blocks((project / "tools_local/timeline.js").read_text(encoding="utf-8"))
        self.assertEqual(set(regions), set(blocks))
        self.assertIn("sc-rp", regions)
        self.assertIn("W, K =", regions["sc-rp"])
        self.assertEqual(before, library.fingerprint(project))

    def test_real_1030_2_dry_run_preserves_source_hashes(self):
        project = library.ROOT / "work/1030-2/v2/editorial"
        if not project.exists():
            self.skipTest("approved project not installed")
        before = library.fingerprint(project)
        entries = self.harvest(project, dry_run=True)
        self.assertEqual(sum(len(e["variants"]) for e in entries.values()), 20)
        self.assertTrue(all(library.proven(e) == 1 for e in entries.values()))
        self.assertEqual(before, library.fingerprint(project))
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
