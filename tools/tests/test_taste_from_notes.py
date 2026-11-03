"""Temp-folder coverage for taste evidence and human-marked promotion; no renders."""
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
# Avoid pycache writes beside existing repository tools when importing by filename.
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("taste_from_notes", ROOT / "tools" / "taste_from_notes.py")
taste = importlib.util.module_from_spec(spec)
spec.loader.exec_module(taste)


def read_lf(path):
    """Path.read_text(newline=) is Python 3.13+; this reads without newline translation on 3.10+."""
    with open(path, encoding="utf-8", newline="\n") as f:
        return f.read()


def put_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8", newline="\n")


def candidate(number=1, rule="When a card continues, do hold its rows still.",
              target="templates/ivory/layout.md", keep=" ", strike=" ",
              evidence=None, count=1):
    evidence = evidence or [('one', 'b01', 'keep the rows still')]
    tags = " ".join(f"[notes {video}: {beat}, {json.dumps(quote, ensure_ascii=False)}]"
                    for video, beat, quote in evidence)
    return (f"{number}. **{rule}** {tags}\n"
            f"   Target: {chr(96)}{target}{chr(96)}\n"
            f"   Seen in: {count} " + ("video\n" if count == 1 else "videos\n") +
            "   Why: A repeated entrance makes the join hitch.\n"
            "   Met when: Rows do not move on the cut frame.\n"
            f"   - [{keep}] keep [{strike}] strike\n\n")


class Temporary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()


class Digest(Temporary):
    def setUp(self):
        super().setUp()
        self.home = self.root / "work" / "example"
        self.project = self.home / "v2" / "editorial"
        self.folder = self.home / "beat" / "rounds"
        self.notes = [
            {"id": "n1", "text": "Keep the rows still.\nNo hitch.", "scope": "frame",
             "beat_id": "b01", "time": 1.25, "frame": 30, "picture_sha": "old", "composition_rev": "old-rev"},
            {"id": "n2", "text": "This card too", "scope": "frame", "beat_id": "b02",
             "time": 3, "picture_sha": "old", "composition_rev": "old-rev"},
            {"id": "n3", "text": "Sound is quiet", "scope": "sound", "beat_id": "b02",
             "time": 3, "cue_index": 0, "cue_time": 3, "cue_name": "click", "sheet_identity": "sheet"},
            {"id": "n4", "text": "Across the whole video", "scope": "video", "beat_id": None},
        ]
        self.write_notes()
        self.old = {"beats": [
            {"id": "b01", "layout": "split", "component": "Post card", "say": "First line", "transition_in": "entrance"},
            {"id": "b02", "layout": "split", "component": "Post card", "say": "Second line"},
        ]}
        self.new = json.loads(json.dumps(self.old))
        self.new["beats"][0]["transition_in"] = "hold"
        self.new["beats"][0]["component"] = "Replacement card"
        self.old_beats = {"beats": [{"id": "b01", "say": "First line"}, {"id": "b02", "say": "Second line"}]}
        self.round0 = {"n": 0, "parent": None, "picture_sha": "old", "composition_rev": "old-rev",
                       "note_ids": [], "not_done": {}, "changed_beats": [], "manifest": {
                           "plan.json": self.blob(self.old), "home/beats.json": self.blob(self.old_beats)}}
        self.round1 = {"n": 1, "parent": 0, "picture_sha": "new", "composition_rev": "new-rev",
                       "note_ids": ["n1"], "not_done": {"n2": "waiting for asset"}, "changed_beats": ["b01"],
                       "report": "Held rows at the join", "manifest": {
                           "plan.json": self.blob(self.new), "home/beats.json": self.blob(self.old_beats)}}
        put_json(self.folder / "0000.json", self.round0)
        put_json(self.folder / "0001.json", self.round1)
        put_json(self.folder / "head.json", {"n": 1})
        put_json(self.project / "plan.json", self.new)
        put_json(self.home / "beats.json", self.old_beats)
        put_json(self.home / "beat" / "changes" / "0001.json", {
            "file_sha256": "new", "composition_rev": "new-rev", "profile": "review",
            "rendered": ["b01"], "wall_s": 2.5, "invalidate": {"reasons": [{"files": ["tools_local/timeline.js"]}]}})
        put_json(self.home / "beat" / "changes" / "0002.json", {
            "file_sha256": "unrelated", "composition_rev": "other", "report": "WRONG REPORT"})
        put_json(self.home / "sound_rounds.json", [{"done": ["n3"], "not_done": {}, "created": "then"}])

    def write_notes(self):
        self.home.mkdir(parents=True, exist_ok=True)
        (self.home / "notes.jsonl").write_text(
            "\n".join(json.dumps(n) for n in self.notes) + "\n", encoding="utf-8", newline="\n")

    def blob(self, document):
        content = json.dumps(document).encode("utf-8")
        key = hashlib.sha256(content).hexdigest()
        path = self.folder / "blobs" / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return key

    def test_digest_is_deterministic_and_writes_only_digest(self):
        before = {p.relative_to(self.home): p.read_bytes() for p in self.home.rglob("*") if p.is_file()}
        path = taste.digest(self.home)
        first = path.read_bytes()
        self.assertEqual(path, self.home / "taste-digest.md")
        taste.digest(self.home)
        self.assertEqual(first, path.read_bytes())
        after = {p.relative_to(self.home): p.read_bytes() for p in self.home.rglob("*") if p.is_file() and p != path}
        self.assertEqual(before, after)

    def test_every_note_context_group_and_response_is_evidence(self):
        text = taste.digest_text(self.home)
        for note in self.notes:
            self.assertIn(taste.inline(note["text"]), text)
            self.assertIn("Note " + note["id"], text)
        self.assertIn('Layout: "split"', text)
        self.assertIn('Component: "Post card"', text)
        self.assertIn('Line: "First line"', text)
        self.assertIn("Time (s): 1.25", text)
        self.assertIn("Frame: 30", text)
        self.assertIn("Scope: video", text)
        self.assertIn("Scope: sound", text)
        self.assertIn("plan: round 0 snapshot", text)
        self.assertIn('Component: "Post card"; 2 beats', text)
        self.assertIn('Layout: "split"; 2 beats', text)
        self.assertIn("round 1: done (active)", text)
        self.assertIn("not done: waiting for asset", text)
        self.assertIn("sound round 1: done", text)
        self.assertIn("Held rows at the join", text)
        self.assertIn("tools_local/timeline.js", text)
        self.assertIn('-  "transition_in": "entrance"', text)
        self.assertIn('+  "transition_in": "hold"', text)
        self.assertNotIn("WRONG REPORT", text)
        self.assertIn("no recorded response (open or not recorded)", text)
        self.assertIn("A done flag does not say what sound changed", text)

    def test_go_back_dropped_and_frozen_are_not_accepted_outcomes(self):
        put_json(self.folder / "head.json", {"n": 0})
        put_json(self.home / "dropped_notes.json", [{"id": "n2", "by": "chase"}])
        put_json(self.folder / "frozen.json", {"note_ids": ["n4"]})
        text = taste.digest_text(self.home)
        self.assertIn("done (undone by go back)", text)
        self.assertIn("dropped by Chase", text)
        self.assertIn("a freeze is not a completed response", text)

    def test_missing_snapshots_are_labelled_and_editorial_beats_are_supported(self):
        for path in self.folder.glob("*.json"):
            path.unlink()
        (self.home / "beats.json").unlink()
        put_json(self.project / "beats.json", self.old_beats)
        text = taste.digest_text(self.home)
        self.assertIn("current file fallback (not historical evidence)", text)
        self.assertIn("unknown (no head.json)", text)
        self.assertIn('Line: "First line"', text)

    def test_missing_plan_is_reported_as_null(self):
        for path in self.folder.glob("*.json"):
            path.unlink()
        (self.project / "plan.json").unlink()
        (self.home / "beats.json").unlink()
        text = taste.digest_text(self.home)
        self.assertIn("Component: null", text)
        self.assertIn("Line: null", text)

    def test_invalid_notes_and_round_cycles_fail_clearly(self):
        self.notes.append(self.notes[0])
        self.write_notes()
        with self.assertRaisesRegex(ValueError, "duplicate note"):
            taste.digest_text(self.home)
        self.notes.pop()
        self.write_notes()
        self.round0["parent"] = 1
        put_json(self.folder / "0000.json", self.round0)
        with self.assertRaisesRegex(ValueError, "cycle"):
            taste.digest_text(self.home)

    def test_external_output_is_read_only_and_cannot_overwrite_run_evidence(self):
        before = (self.home / "notes.jsonl").read_bytes()
        dest = self.root / "inspection.md"
        self.assertEqual(taste.digest(self.home, dest), dest)
        self.assertFalse((self.home / "taste-digest.md").exists())
        with self.assertRaisesRegex(ValueError, "only taste-digest.md"):
            taste.digest(self.home, self.home / "notes.jsonl")
        self.assertEqual(before, (self.home / "notes.jsonl").read_bytes())


class Promote(Temporary):
    def setUp(self):
        super().setUp()
        self.path = self.root / taste.CANDIDATES
        self.path.parent.mkdir(parents=True)
        for rel in taste.TARGETS:
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Rules\n\n- **Existing.** [Chase]\n  Why: Existing. Met when: Existing.\n", encoding="utf-8", newline="\n")
        self.header = "# Candidates\n\nFormat stays.\n\n## Candidates\n\n"

    def write(self, *blocks):
        self.path.write_text(self.header + "".join(blocks), encoding="utf-8", newline="\n")

    def snapshot(self):
        return {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}

    def test_empty_and_unmarked_are_byte_for_byte_no_ops(self):
        for blocks in [(), (candidate(),)]:
            self.write(*blocks)
            before = self.snapshot()
            self.assertEqual(taste.promote(self.root), [])
            self.assertEqual(before, self.snapshot())

    def test_keep_moves_strike_removes_unmarked_stays_and_rerun_is_no_op(self):
        pending = candidate(3, "When a new panel arrives, do show the subject first.")
        self.write(candidate(keep="x"), candidate(2, "When captions swap, do keep them still.", strike="x"), pending)
        actions = taste.promote(self.root, "2026-11-02")
        text = read_lf(self.root / "templates/ivory/layout.md")
        self.assertEqual(len(actions), 2)
        self.assertIn("Moved:", actions[0])
        self.assertIn("Struck:", actions[1])
        self.assertIn("## From his notes", text)
        self.assertIn("- **When a card continues, do hold its rows still.** [Chase] 2026-11-02.", text)
        self.assertIn('[notes one: b01, "keep the rows still"] Seen in: 1 video.', text)
        self.assertIn("  Why: A repeated entrance makes the join hitch. Met when: Rows do not move on the cut frame.", text)
        self.assertNotIn("When captions swap", text)
        self.assertEqual(read_lf(self.path), self.header + pending)
        before = self.snapshot()
        self.assertEqual(taste.promote(self.root), [])
        self.assertEqual(before, self.snapshot())

    def test_all_allowed_targets_and_existing_section_insertion(self):
        for i, rel in enumerate(sorted(taste.TARGETS), 1):
            path = self.root / rel
            path.write_text("# Rules\n\n## From his notes\n\n- **Old.** [Chase]\n\n## Later\n\nStay here.\n", encoding="utf-8", newline="\n")
            self.write(candidate(i, target=rel, keep="X"))
            taste.promote(self.root, "2026-11-02")
            text = read_lf(path)
            self.assertEqual(text.count("## From his notes"), 1)
            self.assertLess(text.index("When a card continues"), text.index("## Later"))
            self.assertIn("Stay here.", text)

    def test_repeated_video_tags_count_videos_not_notes_and_keep_exact_quotes(self):
        evidence = [('one', 'b01', 'Use "this" [not that].'), ('one', 'b02', 'Again'), ('two', 'video', 'Same rule')]
        self.write(candidate(evidence=evidence, count=2, keep="x"))
        taste.promote(self.root, "2026-11-02")
        text = read_lf(self.root / "templates/ivory/layout.md")
        self.assertIn("Seen in: 2 videos.", text)
        self.assertEqual([json.loads(m[3]) for m in taste.NOTE_TAG.finditer(text)], [r[2] for r in evidence])

    def test_invalid_or_ambiguous_list_never_partly_promotes(self):
        bad = [
            candidate(2, keep="x", strike="x"),
            candidate(2, keep="x", count=2),
            candidate(2, keep="x", target="../../outside.md"),
            candidate(2, keep="x").replace("   Why:", "   Surprise:"),
            candidate(2, keep="x").replace("When a card continues, do hold its rows still.", "Vague advice"),
            candidate(2, keep="x").replace('[notes one: b01, "keep the rows still"]', "[seen]"),
            candidate(2, keep="x").replace("   - [x] keep [ ] strike", ""),
        ]
        for block in bad:
            with self.subTest(block=block):
                self.write(candidate(target="templates/HOUSE.md", keep="x"), block)
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    taste.promote(self.root)
                self.assertEqual(before, self.snapshot())

    def test_missing_target_and_existing_rule_conflict_never_partly_promote(self):
        self.write(candidate(keep="x"))
        path = self.root / "templates/ivory/layout.md"
        path.unlink()
        before = self.snapshot()
        with self.assertRaises(OSError):
            taste.promote(self.root)
        self.assertEqual(before, self.snapshot())
        path.write_text("# Rules\n\n- **When a card continues, do hold its rows still.** [Chase] Other evidence.\n", encoding="utf-8", newline="\n")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "different evidence"):
            taste.promote(self.root)
        self.assertEqual(before, self.snapshot())

    def test_retry_after_interrupted_candidate_write_does_not_duplicate(self):
        self.write(candidate(keep="x"))
        original_write = taste.atomic_write
        def fail_candidate(path, data):
            if path == self.path:
                raise OSError("interrupted")
            return original_write(path, data)
        with mock.patch.object(taste, "atomic_write", side_effect=fail_candidate):
            with self.assertRaises(OSError):
                taste.promote(self.root, "2026-11-02")
        actions = taste.promote(self.root, "2026-11-03")
        text = read_lf(self.root / "templates/ivory/layout.md")
        self.assertIn("Already present:", actions[0])
        self.assertEqual(text.count("**When a card continues"), 1)
        self.assertEqual(read_lf(self.path), self.header)

    def test_crlf_and_bom_are_preserved(self):
        self.write(candidate(keep="x"))
        self.path.write_bytes(b"\xef\xbb\xbf" + self.path.read_bytes().replace(b"\n", b"\r\n"))
        path = self.root / "templates/ivory/layout.md"
        path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes().replace(b"\n", b"\r\n"))
        taste.promote(self.root, "2026-11-02")
        for file in (self.path, path):
            raw = file.read_bytes()
            self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
            self.assertNotIn(b"\n", raw.replace(b"\r\n", b""))

    def test_main_prints_actions_and_reports_errors(self):
        self.write(candidate(keep="x"))
        stream = io.StringIO()
        with redirect_stdout(stream):
            self.assertEqual(taste.main(["promote", "--root", str(self.root)]), 0)
        self.assertIn("Moved:", stream.getvalue())
        stream = io.StringIO()
        with redirect_stderr(stream):
            self.assertEqual(taste.main(["digest", str(self.root / "missing")]), 2)
        self.assertIn("ERROR:", stream.getvalue())


class RealEvidence(unittest.TestCase):
    def test_1030_2_read_only_when_available(self):
        home = ROOT / "work" / "1030-2"
        if not (home / "notes.jsonl").is_file():
            self.skipTest("finished run is not available")
        paths = [home / p for p in ("notes.jsonl", "beats.json", "sound_rounds.json", "taste-digest.md",
                                    "v2/editorial/plan.json", "beat/rounds/head.json")]
        paths += sorted((home / "beat" / "rounds").glob("*.json"))
        before = {p: p.read_bytes() if p.exists() else None for p in paths}
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "taste-digest.md"
            taste.digest(home, target)
            first = read_lf(target)
            self.assertEqual(first, taste.digest_text(home))
            for note in taste.notes_of(home):
                self.assertIn(taste.inline(note["text"]), first)
            self.assertIn("Picture round responses", first)
            self.assertIn("Sound rounds", first)
        self.assertEqual(before, {p: p.read_bytes() if p.exists() else None for p in paths})


if __name__ == "__main__":
    unittest.main()
