"""Isolated run-state tests. Usage: python -B tools/tests/test_run_state.py."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

# Importing the tool must not create bytecode in the shared tools directory.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run_state as rs


def stamp(hm):
    return f"2026-11-01T{hm}:00-06:00"


class RunStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.clock = patch.object(rs, "now", return_value=stamp("08:00"))
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.state = rs.init_run(self.root, "sample", "Opus 5.5", "ivory", True, "agent-types")
        self.home = self.root / "work" / "sample"

    def act(self, time, name, status, note=None):
        with patch.object(rs, "now", return_value=stamp(time)):
            return rs.change(self.root, "sample", name, status, note)

    def json(self, relative, value):
        path = self.home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = rs.main(["--root", str(self.root), *args])
        return code, out.getvalue(), err.getvalue()

    def fixture_review(self):
        """1030-2 shapes: duration seconds, 0000 baseline, four rounds, sound notes."""
        self.json("metadata.json", {"duration": 57.65, "fps": 60.0})
        notes = [{"id": f"p{i}", "scope": "frame", "frame": i * 30, "time": i,
                  "picture_sha": "a" * 64, "older_picture": False,
                  "created": f"2026-11-01T20:4{i}:17"} for i in range(4)]
        notes += [{"id": f"s{i}", "scope": "sound", "cue_index": i,
                   "created": f"2026-11-01T22:3{i}:05"} for i in range(4)]
        (self.home / "notes.jsonl").write_text(
            "\n".join(json.dumps(n) for n in notes) + "\n\n", encoding="utf-8")
        for n in range(5):
            self.json(f"beat/rounds/{n:04d}.json",
                      {"n": n, "parent": n - 1 if n else None,
                       "picture_sha": ("b" if n == 4 else "a") * 64,
                       "composition_rev": "c" * 64, "lock_revision": "d" * 64,
                       "notes_rev": f"rev{n}" if n else None,
                       "note_ids": [f"p{n-1}"] if n else [], "not_done": {},
                       "created": f"2026-11-01T21:{n * 5:02d}:00"})
        self.json("beat/rounds/head.json", {"n": 4})
        self.json("beat/rounds/frozen.json", {"note_ids": ["new"]})
        self.json("beat/rounds/left-deadbeef.json", {"created": "2026-11-01T21:10:00"})
        approval = {"approved_file_sha256": "b" * 64, "composition_rev": "c" * 64,
                    "lock_revision": "d" * 64, "result": "PASS", "created": "2026-11-01T21:33:01"}
        self.json("beat/approvals/" + "b" * 16 + ".json", approval)
        self.json("beat/approvals/active.json", {"file_sha256": "b" * 64, "approved": "2026-11-01T21:33:01"})
        self.json("beat/approvals/compare-" + "b" * 16 + ".json", {"result": "FAIL"})
        self.json("sound_rounds.json", [{"done": ["s0"], "not_done": {}, "created": "2026-11-01T22:40:00"}])
        self.json("dropped_notes.json", [{"id": "s1", "by": "chase"}])

    def test_init_schema_and_no_overwrite(self):
        loaded = rs.load_run(self.root, "sample")
        self.assertEqual(loaded["id"], "sample")
        self.assertEqual(loaded["model"], "Opus 5.5")
        self.assertEqual(loaded["template"], "ivory")
        self.assertIs(loaded["codex"], True)
        self.assertEqual(loaded["reference"], "agent-types")
        self.assertIsNotNone(datetime.fromisoformat(loaded["created"]).utcoffset())
        self.assertEqual([s["name"] for s in loaded["stages"]], list(rs.STAGES))
        for s in loaded["stages"]:
            self.assertEqual(s["status"], "pending")
            self.assertIsNone(s["started"])
            self.assertIsNone(s["ended"])
            self.assertEqual(s["minutes"], 0)
            self.assertEqual(s["note"], "")
        self.assertEqual(next(s for s in loaded["stages"] if s["name"] == "plan_check")["rounds"], 0)
        before = (self.home / "run.json").read_bytes()
        with self.assertRaisesRegex(rs.StateError, "already"):
            rs.init_run(self.root, "sample")
        self.assertEqual((self.home / "run.json").read_bytes(), before)

    def test_defaults_and_init_existing_legacy_home(self):
        legacy = self.root / "work" / "legacy"
        legacy.mkdir()
        prose = legacy / "RUN.md"
        prose.write_text("His words", encoding="utf-8")
        data = rs.init_run(self.root, "legacy")
        self.assertIs(data["codex"], False)
        self.assertIsNone(data["model"])
        self.assertEqual(prose.read_text(encoding="utf-8"), "His words")

    def test_local_clock_has_offset(self):
        self.clock.stop()
        self.assertIsNotNone(datetime.fromisoformat(rs.now()).utcoffset())

    def test_running_wait_resume_done_and_live_minutes(self):
        self.act("08:00", "intake", "running")
        self.act("08:05", "intake", "waiting_on_chase", "Which raw?")
        row = self.act("08:35", "intake", "running")
        self.assertEqual(row["minutes"], 5)
        self.assertEqual(row["started"], stamp("08:00"))
        text = rs.status_text(rs.load_run(self.root, "sample"), at=stamp("08:37"))
        self.assertIn("resume intake", text)
        self.assertIn("37.00 min", text)
        row = self.act("08:40", "intake", "done", 'Chase: "this take"')
        self.assertEqual(row["minutes"], 10)
        self.assertEqual(row["ended"], stamp("08:40"))
        self.assertEqual(rs.stage_minutes(row, stamp("09:00"), "waiting_on_chase"), 30)
        self.assertEqual(row["note"], 'Chase: "this take"')
        self.assertEqual(rs.position(rs.load_run(self.root, "sample"))[1], "start spine")

    def test_duplicate_commands_are_idempotent(self):
        self.act("08:00", "intake", "running")
        self.act("08:03", "intake", "running")
        self.act("08:05", "intake", "waiting_on_chase")
        self.act("08:10", "intake", "waiting_on_chase")
        row = self.act("08:15", "intake", "done")
        again = self.act("08:20", "intake", "done", "exact words")
        self.assertEqual(len(again["intervals"]), 2)
        self.assertEqual(again["minutes"], 5)
        self.assertEqual(again["ended"], row["ended"])
        self.assertEqual(again["note"], "exact words")

    def test_plan_rounds_count_attempts_not_resume_or_duplicate_start(self):
        self.act("08:00", "plan_check", "running")
        self.act("08:02", "plan_check", "refused", "missing asset")
        self.act("08:02", "plan_check", "refused")
        self.act("08:03", "plan_check", "running")
        self.act("08:04", "plan_check", "running")
        self.act("08:05", "plan_check", "waiting_on_chase")
        self.act("08:15", "plan_check", "running")
        row = self.act("08:17", "plan_check", "done")
        self.assertEqual(row["rounds"], 2)
        self.assertEqual(row["minutes"], 6)

    def test_fail_retry_accumulates_active_time(self):
        self.act("08:00", "build", "running")
        failed = self.act("08:10", "build", "failed", "owner audit FAIL")
        self.assertEqual(failed["minutes"], 10)
        self.assertIn("owner audit FAIL", rs.position(rs.load_run(self.root, "sample"))[1])
        self.act("08:30", "build", "running")
        row = self.act("08:35", "build", "done")
        self.assertEqual(row["minutes"], 15)
        self.assertEqual(row["started"], stamp("08:00"))

    def test_concurrent_research_keeps_listen_wait_and_counts_blocked_wait_only(self):
        self.act("08:00", "intake", "running")
        self.act("08:05", "intake", "done")
        self.act("08:05", "cut_listen", "waiting_on_chase", "listen")
        self.act("08:10", "research", "running")
        status = rs.status_text(rs.load_run(self.root, "sample"), at=stamp("08:15"))
        self.assertIn("cut_listen (waiting_on_chase), research (running)", status)
        self.assertIn("wait for Chase", status)
        self.assertIn("resume research", status)
        self.act("08:25", "research", "done")
        self.act("09:05", "cut_listen", "done")
        self.act("09:10", "player", "running")
        data = rs.metrics(self.root, "sample")
        self.assertEqual(data["player_minutes_including_wait"], 70)
        self.assertEqual(data["player_chase_wait_minutes"], 60)
        self.assertEqual(data["player_work_during_wait_minutes"], 15)
        self.assertEqual(data["player_wait_minutes"], 45)
        self.assertEqual(data["player_minutes_excluding_wait"], 25)

    def test_terminal_without_start_is_zero_and_note_rounds_sort_numerically(self):
        for n in (10, 2, 1):
            row = self.act("08:00", f"note_round_{n}", "done")
            self.assertEqual(row["minutes"], 0)
        names = [s["name"] for s in rs.load_run(self.root, "sample")["stages"]]
        self.assertEqual(names[names.index("player") + 1:names.index("approval")],
                         ["note_round_1", "note_round_2", "note_round_10"])

    def test_unknown_id_stage_and_traversal_are_exit_two(self):
        cases = [("status", "missing"), ("metrics", "missing"),
                 ("done", "missing", "intake"), ("start", "sample", "typo"),
                 ("start", "sample", "note_round_0"), ("start", "sample", "note_round_x"),
                 ("init", "../outside"), ("status", r"..\outside"), ("status", "C:drive")]
        for args in cases:
            with self.subTest(args=args):
                code, out, err = self.cli(*args)
                self.assertEqual(code, 2)
                self.assertIn("ERROR:", err)
                self.assertEqual(out, "")
        self.assertEqual([p.name for p in (self.root / "work").iterdir()], ["sample"])

    def test_corrupt_state_is_clear_error(self):
        (self.home / "run.json").write_text("{bad", encoding="utf-8")
        code, _, err = self.cli("status", "sample")
        self.assertEqual(code, 2)
        self.assertIn("run.json", err)

    def test_invalid_state_fields_are_clear_errors(self):
        for field, value in (("status", ["running"]), ("minutes", -1), ("note", None)):
            with self.subTest(field=field):
                state = json.loads(json.dumps(self.state))
                state["stages"][0][field] = value
                self.json("run.json", state)
                code, _, err = self.cli("status", "sample")
                self.assertEqual(code, 2)
                self.assertIn("run.json", err)

    def test_empty_directory_is_not_a_known_legacy_run(self):
        (self.root / "work/empty").mkdir()
        code, _, err = self.cli("metrics", "empty")
        self.assertEqual(code, 2)
        self.assertIn("unknown run id", err)

    def test_first_player_latency_waits_and_stage_time(self):
        self.act("08:00", "intake", "running")
        self.act("08:05", "intake", "done")
        self.act("08:05", "cut_listen", "running")
        self.act("08:06", "cut_listen", "waiting_on_chase")
        self.act("08:36", "cut_listen", "done")
        self.act("08:36", "build", "running")
        self.act("08:46", "build", "failed")
        self.act("08:56", "build", "running")
        self.act("09:06", "build", "done")
        self.act("09:10", "player", "running")
        self.act("09:11", "player", "waiting_on_chase")
        self.act("10:00", "player", "done")
        self.act("10:01", "player", "running")  # repeat review does not move first opening
        data = rs.metrics(self.root, "sample", at=stamp("10:02"))
        self.assertEqual(data["player_minutes_including_wait"], 70)
        self.assertEqual(data["player_minutes_excluding_wait"], 40)
        self.assertEqual(data["player_wait_minutes"], 30)
        build = next(s for s in data["stages"] if s["name"] == "build")
        self.assertEqual(build["minutes"], 20)
        self.assertEqual(build["waiting_minutes"], 0)
        self.assertIn("excluding Chase waits", rs.metrics_text(data))

    def test_wait_intervals_are_unioned_and_clipped(self):
        def interval(a, b):
            return {"status": "waiting_on_chase", "started": stamp(a), "ended": stamp(b) if b else None}
        state = {"stages": [{"intervals": [interval("07:50", "08:10"), interval("08:05", "08:20")]},
                            {"intervals": [interval("08:50", None)]}]}
        self.assertEqual(rs.waiting_seconds(state, stamp("08:00"), stamp("09:00")), 30 * 60)

    def test_offset_changes_use_elapsed_instants(self):
        self.assertEqual(rs.seconds("2026-11-01T01:30:00-05:00", "2026-11-01T01:30:00-06:00"), 3600)
        self.assertEqual(rs.seconds("2026-11-01T23:55:00-06:00", "2026-11-02T00:05:00-06:00"), 600)

    def test_completed_run_elapsed_stops_at_final(self):
        state = rs.load_run(self.root, "sample")
        for s in state["stages"]:
            s.update(status="done", ended=stamp("09:00"))
        text = rs.status_text(state, at=stamp("12:00"))
        self.assertIn("Elapsed: 60.00", text)
        self.assertIn("Now: complete", text)

    def test_review_real_shapes_and_read_only_metrics(self):
        self.fixture_review()
        before = {str(p.relative_to(self.home)): p.read_bytes()
                  for p in self.home.rglob("*") if p.is_file()}
        data = rs.metrics(self.root, "sample")
        self.assertEqual(data["duration_seconds"], 57.65)
        self.assertEqual((data["notes"], data["picture_notes"], data["sound_notes"]), (8, 4, 4))
        self.assertAlmostEqual(data["notes_per_minute"], 8 * 60 / 57.65)
        self.assertAlmostEqual(data["picture_notes_per_minute"], 4 * 60 / 57.65)
        self.assertEqual(data["note_rounds"], 4)
        self.assertEqual(data["note_rounds_until_approval"], 4)
        self.assertEqual(data["approved_line_rounds"], 4)
        self.assertEqual(data["first_approval"], "2026-11-01T21:33:01")
        after = {str(p.relative_to(self.home)): p.read_bytes()
                 for p in self.home.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_legacy_run_without_state_still_reads_review_metrics(self):
        self.fixture_review()
        (self.home / "run.json").unlink()
        code, out, err = self.cli("metrics", "sample")
        self.assertEqual((code, err), (0, ""))
        self.assertIn("8.33 all", out)
        self.assertIn("4.16 picture", out)
        self.assertIn("no run.json", out)
        self.assertFalse((self.home / "run.json").exists())
        self.assertEqual(self.cli("status", "sample")[0], 2)

    def test_go_back_counts_effort_and_approved_line_separately(self):
        self.fixture_review()
        branch = json.loads((self.home / "beat/rounds/0004.json").read_text(encoding="utf-8"))
        branch["parent"] = 1  # rounds 2 and 3 happened but were abandoned
        self.json("beat/rounds/0004.json", branch)
        self.json("beat/rounds/head.json", {"n": 0})  # later go-back must not rewrite first-approval history
        data = rs.metrics(self.root, "sample")
        self.assertEqual(data["note_rounds_until_approval"], 4)
        self.assertEqual(data["approved_line_rounds"], 2)

    def test_later_rounds_and_failed_approvals_do_not_change_first_approval(self):
        self.fixture_review()
        self.json("beat/rounds/0005.json", {"n": 5, "parent": 4, "notes_rev": "new",
                  "note_ids": ["later"], "created": "2026-11-01T22:00:00"})
        self.json("beat/approvals/" + "e" * 16 + ".json",
                  {"result": "FAIL", "approved_file_sha256": "e" * 64, "created": "2026-11-01T20:00:00"})
        self.json("beat/approvals/" + "f" * 16 + ".json",
                  {"result": "RECONCILED", "approved_file_sha256": "f" * 64, "created": "2026-11-01T23:00:00"})
        (self.home / "beat/approvals/active.json").unlink()
        data = rs.metrics(self.root, "sample")
        self.assertEqual(data["note_rounds"], 5)
        self.assertEqual(data["note_rounds_until_approval"], 4)

    def test_no_approval_is_unknown_not_zero(self):
        self.fixture_review()
        (self.home / ("beat/approvals/" + "b" * 16 + ".json")).unlink()
        data = rs.metrics(self.root, "sample")
        self.assertIsNone(data["note_rounds_until_approval"])
        self.assertIsNone(data["first_approval"])
        self.assertEqual(data["note_rounds"], 4)

    def test_zero_note_rounds_before_approval(self):
        self.fixture_review()
        for n in range(1, 5):
            (self.home / f"beat/rounds/{n:04d}.json").unlink()
        a = json.loads((self.home / ("beat/approvals/" + "b" * 16 + ".json")).read_text(encoding="utf-8"))
        a["approved_file_sha256"] = "a" * 64
        self.json("beat/approvals/" + "b" * 16 + ".json", a)
        data = rs.metrics(self.root, "sample")
        self.assertEqual(data["note_rounds_until_approval"], 0)
        self.assertEqual(data["approved_line_rounds"], 0)

    def test_missing_or_bad_duration_is_unavailable(self):
        for value in (None, 0, -1, True, "57.65", float("nan")):
            with self.subTest(value=value):
                self.json("metadata.json", {"duration": value})
                data = rs.metrics(self.root, "sample")
                self.assertIsNone(data["notes_per_minute"])
                self.assertIsNone(data["duration_seconds"])
                self.assertTrue(data["warnings"])
        (self.home / "metadata.json").unlink()
        self.assertIsNone(rs.metrics(self.root, "sample")["duration_seconds"])

    def test_duplicate_note_ids_count_once(self):
        self.fixture_review()
        path = self.home / "notes.jsonl"
        text = path.read_text(encoding="utf-8")
        path.write_text(text + text.splitlines()[0] + "\n", encoding="utf-8")
        self.assertEqual(rs.metrics(self.root, "sample")["notes"], 8)

    def test_corrupt_notes_and_metadata_are_errors_with_paths(self):
        (self.home / "notes.jsonl").write_text('{"id":"good"}\n{bad\n', encoding="utf-8")
        code, _, err = self.cli("metrics", "sample")
        self.assertEqual(code, 2)
        self.assertIn("notes.jsonl:2", err)
        (self.home / "notes.jsonl").unlink()
        self.json("metadata.json", [])
        code, _, err = self.cli("metrics", "sample")
        self.assertEqual(code, 2)
        self.assertIn("metadata.json", err)

    def test_report_one_row_per_run_and_escapes_values(self):
        self.fixture_review()
        rs.init_run(self.root, "second", "Sol | test\nmodel", "ivory")
        rs.init_run(self.root, "broken")
        (self.root / "work/broken/run.json").write_text("{bad", encoding="utf-8")
        (self.root / "work/legacy").mkdir()
        before = {str(p.relative_to(self.root)): p.read_bytes()
                  for p in (self.root / "work").rglob("*") if p.is_file()}
        code, out, err = self.cli("report")
        self.assertEqual((code, err), (0, ""))
        self.assertIn("metrics.md", out)
        report = (self.root / "reports/metrics.md").read_text(encoding="utf-8")
        for run_id in ("sample", "second", "broken"):
            self.assertEqual(report.count(f"| {run_id} |"), 1)
        self.assertNotIn("| legacy |", report)
        self.assertIn("Sol \\| test model", report)
        self.assertIn("ERROR:", report)
        self.assertIn("8/4/4", report)
        after = {str(p.relative_to(self.root)): p.read_bytes()
                 for p in (self.root / "work").rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_atomic_failure_preserves_old_file_and_cleans_temp(self):
        target = self.home / "run.json"
        before = target.read_bytes()
        with patch.object(rs.os, "replace", side_effect=OSError("rename blocked")):
            code, _, err = self.cli("start", "sample", "intake")
        self.assertEqual(code, 2)
        self.assertIn("rename blocked", err)
        self.assertEqual(target.read_bytes(), before)
        self.assertEqual(list(self.home.glob("*.tmp")), [])

    def test_atomic_success_uses_same_directory_and_complete_json(self):
        original = rs.os.replace
        calls = []
        def replace(src, dest):
            src, dest = Path(src), Path(dest)
            self.assertEqual(src.parent, dest.parent)
            self.assertEqual(json.loads(src.read_text(encoding="utf-8"))["stages"][0]["status"], "running")
            calls.append(dest)
            original(src, dest)
        with patch.object(rs.os, "replace", side_effect=replace):
            self.act("08:00", "intake", "running")
        self.assertEqual(calls, [self.home / "run.json"])
        self.assertEqual(list(self.home.glob("*.tmp")), [])

    def test_cli_commands_and_notes(self):
        for command, expected in (("start", "running"), ("wait", "waiting_on_chase"),
                                  ("refused", "refused"), ("fail", "failed"), ("done", "done")):
            args = [command, "sample", "intake"]
            if command != "start":
                args += ["--note", "Chase's words"]
            code, out, err = self.cli(*args)
            self.assertEqual((code, err), (0, ""))
            self.assertIn(expected, out)
        self.assertEqual(self.cli("status", "sample")[0], 0)
        code, _, err = self.cli("init", "cli", "--model", "Sol", "--template", "ivory", "--codex", "--reference", "ref")
        self.assertEqual((code, err), (0, ""))
        self.assertIs(rs.load_run(self.root, "cli")["codex"], True)


if __name__ == "__main__":
    unittest.main()
