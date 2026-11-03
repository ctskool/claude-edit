"""Workstream C's two checks: tools/beat_check/conform.py and output.py. CONTRACT.md section 7.

Usage: python tools/tests/test_beat_check.py            everything, about 6 minutes
       python tools/tests/test_beat_check.py --quick    logic only, no browser, no render

The deliberate failures run for real. Source faults are real edits to a temp copy of the fixture, rebuilt by its real build.py and measured in a real browser.
Output faults run on a temp copy of the store's review picture, and the stuck-layout fault is a real capture with the viewport fault injected. The fixture itself is only read.
The fixture already fails on its own (phase2-checks.md), so each test names the event or check it broke and asserts that was not failing before.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(ROOT / "tools" / "beat_check"), str(ROOT / "tools" / "beat_render"), str(ROOT / "tools")]
import conform
import events
import lock as beat_lock
import output
import ownership
import run as runner
import sentinel
import sound_mix
import store
from common import sha

FIXTURE = ROOT / "work" / "beat-fixture"
ED = FIXTURE / "v2" / "editorial"
NEEDS_FIXTURE = unittest.skipUnless((ROOT / "work/beat-fixture/v2/editorial/beats.lock.json").is_file(),
                                    "needs work/beat-fixture, the author's 107 s test edit, which does not ship")
RENDER = ROOT / "tools" / "beat_render" / "render.mjs"
EVIDENCE = ROOT / "reports" / "2026-10-31-moves-plan-page" / "stage1" / "phase2-evidence" / "checks-failure-tests.json"
SKIP = shutil.ignore_patterns("__pycache__", "renders", "snaps*", ".hyperframes", "*.tmp")
TIMELINE = "tools_local/timeline.js"
SCENES = "tools_local/scenes.py"
PLAN = "plan.json"
WORD_LINE = 'tl.fromTo("#gr-word", { y: -22, opacity: 0 }, { y: 0, opacity: 1, duration: 0.35, ease: "back.out(1.6)", immediateRender: false }, 19.12);'
RECORD = []


def event(**fields):
    base = {"event_id": "b11.e1", "beat_id": "b11", "kind": "anchor", "owner": "o", "t": 19.12, "frame": 574, "word_id": 66, "word": "personal", "word_start": 19.12, "lead_frames": 0,
            "target": "#x", "expect": "appear", "copy": "personal life", "hold_frames": 30, "assets": [], "carried": None}
    base.update(fields)
    return base


def seen(visible=True, text="personal life", state="s0", node=1, symbols=()):
    return {"visible": visible, "text": text, "state": state, "node": node, "symbols": list(symbols)}


def page(rows, target="#x"):
    """frame -> measurement of one target."""
    return {f: {target: m} for f, m in rows.items()}


class Points(unittest.TestCase):
    owners = {"o": {"frames": [[500, 600], [700, 800]]}}

    def test_after_is_half_a_second(self):
        p = conform.points(event(), self.owners, 3214)
        self.assertEqual((p["before"], p["after"]), (573, 589))
        self.assertEqual(p["span"], list(range(574, 590)))

    def test_after_clamps_to_one_frame_before_the_owner_ends(self):
        self.assertEqual(conform.points(event(frame=595), self.owners, 3214)["after"], 599)

    def test_hold_shorter_than_half_a_second_reads_inside_it(self):
        self.assertEqual(conform.points(event(hold_frames=6), self.owners, 3214)["after"], 579)

    def test_frame_zero_has_no_frame_before_it(self):
        self.assertIsNone(conform.points(event(frame=0, owner=None), self.owners, 3214)["before"])

    def test_designed_lead_reads_earlier(self):
        self.assertEqual(conform.points(event(lead_frames=6), self.owners, 3214)["before"], 567)

    def test_copy_reads_on_its_one_frame(self):
        p = conform.points(event(kind="copy"), self.owners, 3214)
        self.assertEqual((p["before"], p["after"], p["span"]), (None, 574, [574]))

    def test_caption_is_also_read_just_past_its_end(self):
        p = conform.points(event(kind="caption", end_frame=600, hold_frames=26), self.owners, 3214)
        self.assertEqual((p["hold"], p["gone"]), (599, 600))


class Time(unittest.TestCase):
    p = {"before": 573, "after": 589, "span": [574, 575, 576, 589], "hold": None, "gone": None}

    def judge(self, frames, **fields):
        return conform.judge_time(event(**fields), self.p, page(frames))

    def test_appear_on_its_word(self):
        status, onset, _ = self.judge({573: seen(visible=False), 574: seen(), 575: seen(), 576: seen(), 589: seen()})
        self.assertEqual((status, onset), ("PASS", 574))

    def test_too_early_is_fail(self):
        status, _, why = self.judge({573: seen(), 574: seen(), 575: seen(), 576: seen(), 589: seen()})
        self.assertEqual(status, "FAIL")
        self.assertIn("too early", why)

    def test_never_is_fail(self):
        off = seen(visible=False)
        status, _, why = self.judge({573: off, 574: off, 575: off, 576: off, 589: off})
        self.assertEqual(status, "FAIL")
        self.assertIn("never", why)

    def test_the_words_must_be_there_not_just_the_box(self):
        wrong = seen(text="personal lives")
        status, _, _ = self.judge({573: seen(visible=False), 574: wrong, 575: wrong, 576: wrong, 589: wrong})
        self.assertEqual(status, "FAIL")

    def test_change(self):
        a, b = seen(state="a"), seen(state="b")
        status, onset, _ = self.judge({573: a, 574: a, 575: b, 576: b, 589: b}, expect="change", copy=None)
        self.assertEqual((status, onset), ("PASS", 575))

    def test_no_change_is_fail(self):
        a = seen(state="a")
        status, _, why = self.judge({573: a, 574: a, 575: a, 576: a, 589: a}, expect="change", copy=None)
        self.assertEqual(status, "FAIL")
        self.assertIn("nothing changed", why)

    def test_a_frame_never_measured_is_unverified(self):
        self.assertEqual(self.judge({589: seen()})[0], "UNVERIFIED")

    def test_target_not_in_the_page_is_fail(self):
        self.assertEqual(self.judge({573: None, 574: None, 575: None, 576: None, 589: None})[0], "FAIL")


class Word(unittest.TestCase):
    def off(self, frames, **fields):
        return conform.word_problem(event(t=19.12 + frames / 30, **fields), 30)

    def test_two_frames_either_way_for_an_anchor(self):
        self.assertIsNone(self.off(2))
        self.assertIsNone(self.off(-2))
        self.assertIn("follows", self.off(2.5))
        self.assertIn("leads", self.off(-2.5))

    def test_a_chip_may_lead_five(self):
        self.assertIsNone(self.off(-5, kind="caption"))
        self.assertIn("leads", self.off(-5.5, kind="caption"))

    def test_a_named_lead_widens_the_lead_only(self):
        self.assertIsNone(self.off(-6, lead_frames=6))
        self.assertIn("follows", self.off(3, lead_frames=6))


class Verdicts(unittest.TestCase):
    def test_worst(self):
        self.assertEqual(conform.worst(["PASS", "UNVERIFIED", "FAIL"]), "FAIL")
        self.assertEqual(conform.worst(["PASS", "UNVERIFIED"]), "UNVERIFIED")
        self.assertEqual(conform.worst(["PASS"]), "PASS")
        self.assertEqual(conform.worst([]), "UNVERIFIED")

    def test_an_event_with_no_bind_is_unverified_never_pass(self):
        m = {"owners": [], "fps": 30, "total_frames": 3214}
        row = conform.judge_event(event(target=None, expect=None), {}, m, [], ROOT, {}, {})
        self.assertEqual(row["status"], "UNVERIFIED")

    def test_text_inside_a_capture_stays_unverified(self):
        m = {"owners": [], "fps": 30, "total_frames": 3214}
        e = event(kind="copy", expect="present", copy="Research", image="assets/x.png", word_start=None, hold_frames=None)
        row = conform.judge_event(e, page({574: seen(text="")}), m, [], ROOT, {}, {})
        self.assertEqual(row["checks"]["copy"], "UNVERIFIED")
        self.assertEqual(row["status"], "UNVERIFIED")

    def test_unverified_is_not_a_pass_to_the_renderer(self):
        self.assertEqual(conform.CODES["UNVERIFIED"], output.CODES["UNVERIFIED"])
        self.assertEqual(runner.CHECK_STATUS.get(conform.CODES["UNVERIFIED"], "UNVERIFIED"), "UNVERIFIED")
        self.assertEqual(runner.CHECK_STATUS[conform.CODES["FAIL"]], "FAIL")
        self.assertEqual(runner.CHECK_STATUS[conform.CODES["PASS"]], "PASS")

    def test_a_page_that_could_not_be_measured_is_not_a_check_that_looked(self):
        unmeasured = {"status": "UNVERIFIED", "findings": [{"status": "UNVERIFIED", "check": "measurement", "message": "timed out"}]}
        self.assertEqual(conform.exit_code(unmeasured), conform.NOT_MEASURED)
        self.assertNotIn(conform.NOT_MEASURED, runner.CHECK_STATUS)

    def test_a_check_that_looked_and_could_not_tell_keeps_its_exit(self):
        looked = {"status": "UNVERIFIED", "findings": [{"status": "UNVERIFIED", "check": "floor", "message": "x"}]}
        self.assertEqual(conform.exit_code(looked), conform.CODES["UNVERIFIED"])

    def test_a_failure_stays_a_failure_even_with_no_measurement(self):
        failed = {"status": "FAIL", "findings": [{"status": "UNVERIFIED", "check": "measurement", "message": "x"}, {"status": "FAIL", "check": "render", "message": "x"}]}
        self.assertEqual(conform.exit_code(failed), conform.CODES["FAIL"])

    def test_a_measurement_that_timed_out_reaches_the_exit_code(self):
        with mock.patch.object(conform.subprocess, "run", side_effect=subprocess.TimeoutExpired("node", 1)):
            with tempfile.TemporaryDirectory() as tmp:
                report = conform.audit_only(ED, tmp)
        self.assertEqual(report["status"], "UNVERIFIED")
        self.assertEqual(conform.exit_code(report), conform.NOT_MEASURED)

    def test_no_file_is_not_a_check_that_looked(self):
        self.assertEqual(output.main([str(ROOT / "work" / "no-such-folder" / "review.mp4")]), output.NOT_CHECKED)
        self.assertNotIn(output.NOT_CHECKED, runner.CHECK_STATUS)

    def test_carried_same_node_passes_replaced_node_fails(self):
        chains = [{"id": "hud", "objects": ["#p"]}]
        e = event(carried={"chain": "hud"}, target="#p", expect="change")
        p = {"before": 10, "after": 25}
        nodes = {}
        ok = {10: {"#p": seen(node=7)}, 25: {"#p": seen(node=7)}}
        self.assertEqual(conform.judge_carried(e, p, ok, chains, nodes)[0], "PASS")
        replaced = {10: {"#p": seen(node=7)}, 25: {"#p": seen(node=8)}}
        status, why = conform.judge_carried(e, p, replaced, chains, nodes)
        self.assertEqual(status, "FAIL")
        self.assertIn("not the node", why)

    def test_a_reset_that_measures_wrong_fails_unless_the_build_dropped_it(self):
        chain = {"id": "hud", "objects": ["#p"], "carries": ["y"], "resets": [{"frame": 100, "values": {"#p": {"y": 0}}}], "dropped": []}
        self.assertTrue(conform.judge_resets([chain], {"100": [0]})[0]["matches"])
        self.assertFalse(conform.judge_resets([chain], {"100": [5]})[0]["matches"])
        self.assertTrue(conform.judge_resets([{**chain, "dropped": [{"frame": 100}]}], {"100": [5]})[0]["dropped"])


class Contract(unittest.TestCase):
    def test_lines_skip_style_keys_and_walk_lists(self):
        self.assertEqual(events.lines({"title": "Skill backbone", "italic": "backbone"}), ["Skill backbone"])
        self.assertEqual(events.lines({"doors": [{"name": "A", "line": "b"}, {"name": "C"}]}), ["A", "b", "C"])

    def test_a_copy_line_with_no_row_stays_in_the_contract_unbound(self):
        rows = events.copy_events([{"id": "b01", "copy": {"title": "X"}}], [], 30)
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0]["target"])

    def test_a_row_for_copy_the_beats_do_not_have_raises(self):
        with self.assertRaises(ValueError):
            events.copy_events([{"id": "b01", "copy": {"title": "X"}}], [("b01", "Y", "o", "#y", 1.0)], 30)

    @NEEDS_FIXTURE
    def test_the_fixture_meets_the_contracts_floor(self):
        doc = events.load(ED)
        bound = conform.floor(doc["events"], beat_lock.load(ED))
        self.assertTrue(bound["met"], bound)
        self.assertEqual(bound["want"], {"caption": 156, "anchor": 45, "carried": 11, "copy_beats": 24})

    def test_the_floor_comes_from_the_project_not_this_fixture(self):
        rows = [event(kind="caption", beat_id="b01"), event(kind="anchor", beat_id="b01"), event(kind="anchor", beat_id="b02"), event(kind="carried", beat_id="b01"), event(kind="copy", beat_id="b01")]
        bound = conform.floor(rows, {"beats": [{"beat_id": "b01", "layout": "split"}, {"beat_id": "b02", "layout": "full-face"}]})
        self.assertEqual(bound["want"], {"caption": 1, "anchor": 1, "carried": 1, "copy_beats": 1})
        self.assertTrue(bound["met"])

    def test_an_unbound_event_breaks_the_floor(self):
        bound = conform.floor([event(kind="caption", beat_id="b01", target=None)], {"beats": [{"beat_id": "b01", "layout": "split"}]})
        self.assertFalse(bound["met"])

    @NEEDS_FIXTURE
    def test_the_builder_has_no_round_left_on_a_frame(self):
        for name in ("build.py", "scenes.py"):
            text = (ED / "tools_local" / name).read_text(encoding="utf8")
            self.assertNotRegex(text, r"round\([^)]*(FPS|\* ?30)", name)
            self.assertIn("frame_of", text)


class SceneRoots(unittest.TestCase):
    m = {"fps": 30, "total_frames": 300, "shared": {"timing": {"windows": [["sc-a", 0, 2], ["sc-b", 2, 3], ["sc-b", 5, 6]]}}}

    def test_a_root_is_read_only_where_it_should_be_hidden(self):
        rows = conform.root_frames(self.m)
        self.assertEqual(rows["59"], ["#sc-b"])
        self.assertEqual(rows["60"], ["#sc-a"])
        self.assertEqual(rows["90"], ["#sc-a", "#sc-b"], "the gap between sc-b's two windows")
        self.assertEqual(rows["299"], ["#sc-a", "#sc-b"])

    def test_every_edge_is_inside_the_video(self):
        self.assertTrue(all(0 <= int(f) < 300 for f in conform.root_frames(self.m)))

    def test_a_root_seen_outside_its_window_is_named_with_its_first_frame(self):
        self.assertEqual(conform.judge_roots({"100": [], "150": ["#sc-a"], "200": ["#sc-a", "#sc-b"]}), ["#sc-a shows on frame 150, outside its window", "#sc-b shows on frame 200, outside its window"])


class ReportNames(unittest.TestCase):
    def test_a_report_bound_to_a_file_names_it(self):
        self.assertEqual(conform.report_name({"scope": "all", "render_sha16": "abc"}), "source-abc.json")

    def test_two_profiles_write_two_reports(self):
        self.assertNotEqual(conform.report_name({"scope": "all", "render_sha16": "aaa"}), conform.report_name({"scope": "all", "render_sha16": "bbb"}))

    def test_a_partial_scope_never_reads_as_the_whole(self):
        name = conform.report_name({"scope": ["b02"], "render_sha16": "abc"})
        self.assertRegex(name, r"^source-[0-9a-f]{8}-abc\.json$")
        self.assertNotEqual(name, conform.report_name({"scope": "all", "render_sha16": "abc"}))

    def test_no_render_keeps_the_plain_name(self):
        self.assertEqual(conform.report_name({"scope": "all"}), "source.json")

    def test_the_audit_has_its_own_report(self):
        self.assertEqual(conform.report_name({"scope": "audit"}), "audit.json")


class Motionlint(unittest.TestCase):
    def lint(self, html, waivers):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "v2" / "editorial"
            project.mkdir(parents=True)
            (project / "index.html").write_text(html, encoding="utf8")
            (Path(tmp) / "fixture.json").write_text(json.dumps({"waivers": waivers}), encoding="utf8")
            return conform.motionlint(project)

    WAIVER = [{"check": "motionlint", "starts_with": "face_full:", "why": "historical_full_face"}]

    def test_the_waived_message_is_waived_and_reported(self):
        status, _, waived = self.lint('<video src="assets/face_full.mp4">', self.WAIVER)
        self.assertEqual(status, "PASS")
        self.assertEqual(len(waived), 1)

    def test_any_other_error_still_counts(self):
        status, why, _ = self.lint('<video src="assets/face_full.mp4"><script>Math.random()</script>', self.WAIVER)
        self.assertEqual(status, "FAIL")
        self.assertIn("Math.random", why)

    def test_no_waiver_no_pass(self):
        self.assertEqual(self.lint('<video src="assets/face_full.mp4">', [])[0], "FAIL")


def sub(project, rel, old, new):
    path = project / rel
    text = path.read_bytes().decode("utf8")
    if text.count(old) != 1:
        raise ValueError(f"{rel}: expected one {old!r}, found {text.count(old)}")
    path.write_bytes(text.replace(old, new).encode("utf8"))


def write_record(name, **fields):
    RECORD.append({"test": name, **fields})


@NEEDS_FIXTURE
class SourceFaults(unittest.TestCase):
    """Real edits, real builds, a real browser. On a temp copy two levels under work/, as the fixture is, because build.py finds tools/ from there."""

    @classmethod
    def setUpClass(cls):
        cls.base = Path(tempfile.mkdtemp(prefix="beat-check-", dir=ROOT / "work"))
        for name in ("metadata.json", "words.json", "beats.json", "fixture.json"):
            shutil.copy(FIXTURE / name, cls.base / name)
        cls.project = cls.base / "v2" / "editorial"
        shutil.copytree(ED, cls.project, ignore=SKIP)
        cls.saved = {rel: (cls.project / rel).read_bytes() for rel in (TIMELINE, SCENES, PLAN, "tools_local/owners.py")}
        cls.build()
        report = conform.conform(cls.project)
        cls.baseline = {r["event_id"]: r["status"] for r in report["events"]}
        cls.baseline_findings = [f for f in report["findings"] if f["status"] == "FAIL"]
        write_record("baseline", status=report["status"], counts=report["counts"], failing=sorted(k for k, v in cls.baseline.items() if v == "FAIL"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base, ignore_errors=True)

    @classmethod
    def build(cls):
        subprocess.run([sys.executable, str(cls.project / "tools_local" / "build.py")], cwd=cls.project, check=True, capture_output=True)

    def tearDown(self):
        for rel, data in self.saved.items():
            (self.project / rel).write_bytes(data)
        self.build()

    def check(self, *beats):
        self.build()
        report = conform.conform(self.project, list(beats) or None)
        return report, {r["event_id"]: r for r in report["events"]}

    def assert_broke(self, name, report, rows, event_id, check, words):
        row = rows[event_id]
        self.assertEqual(row["status"], "FAIL", row)
        self.assertEqual(row["checks"][check], "FAIL", row)
        self.assertNotEqual(self.baseline[event_id], "FAIL")
        self.assertEqual(report["status"], "FAIL")
        self.assertIn(words, " ".join(row["problems"]))
        write_record(name, event=event_id, status=row["status"], problems=row["problems"], overall=report["status"])

    def test_a_clean_scope_is_not_fail_and_not_pass(self):
        report, _ = self.check("b11")
        self.assertEqual(report["status"], "UNVERIFIED")
        write_record("clean scope b11", overall=report["status"], counts=report["counts"])

    def test_label_that_never_appears(self):
        sub(self.project, TIMELINE, WORD_LINE, "")
        report, rows = self.check("b11")
        self.assert_broke("label never appears", report, rows, "b11.e1", "time", "never there")

    def test_label_that_appears_early(self):
        sub(self.project, TIMELINE, WORD_LINE, WORD_LINE.replace("19.12", "18.6"))
        report, rows = self.check("b11")
        self.assert_broke("label appears early", report, rows, "b11.e1", "time", "too early")

    def test_label_that_arrives_late_but_inside_the_half_second(self):
        sub(self.project, TIMELINE, WORD_LINE, WORD_LINE.replace("19.12", "19.45"))
        report, rows = self.check("b11")
        self.assert_broke("label arrives 10 frames late", report, rows, "b11.e1", "word", "after its word")

    def test_caption_moved_off_its_word_in_the_plan(self):
        path = self.project / PLAN
        plan = json.loads(path.read_text(encoding="utf8"))
        chunks = plan["captions"]["chunks"]
        i = next(n for n, c in enumerate(chunks) if c["words"][0] == 66)
        chunks[i]["on"] = round(chunks[i]["on"] - 0.3, 3)
        chunks[i - 1]["off"] = chunks[i]["on"]
        path.write_text(json.dumps(plan, indent=1, ensure_ascii=False), encoding="utf8", newline="\n")
        report, rows = self.check("b11")
        cap = next(k for k in rows if k.startswith("cap.w0066"))
        self.assert_broke("caption early by plan", report, rows, cap, "word", "leads its word")

    def test_wrong_word_in_a_graphic(self):
        sub(self.project, SCENES, ">personal life</div>", ">personal lives</div>")
        report, rows = self.check("b11")
        self.assert_broke("wrong word", report, rows, "b11.e1", "time", "never there")
        self.assertEqual(rows["b11.copy1"]["checks"]["copy"], "FAIL")

    def test_a_visible_parent_cannot_vouch_for_a_hidden_child(self):
        sub(self.project, SCENES, ">personal life</div>", '><span style="opacity:0">personal life</span></div>')
        report, rows = self.check("b11")
        self.assert_broke("hidden child", report, rows, "b11.e1", "time", "never there")

    def test_missing_asset(self):
        path = self.project / "assets" / "stills" / "jarvis-toggle.png"
        path.unlink()  # after a good build, as a lost file would be. A rebuild would stop first, and so does that
        try:
            report = conform.conform(self.project, ["b07"])
            with self.assertRaises(subprocess.CalledProcessError):
                self.build()
        finally:
            shutil.copy(ED / "assets" / "stills" / "jarvis-toggle.png", path)
        rows = {r["event_id"]: r for r in report["events"]}
        self.assert_broke("missing asset", report, rows, "b07.e1", "assets", "jarvis-toggle.png")
        self.assertTrue(any(f["check"] == "assets" and f["status"] == "FAIL" for f in report["findings"]))

    def test_replaced_carried_object(self):
        sub(self.project, TIMELINE, "// ---------- captions: hard swap, height from the build ----------",
            'tl.call(() => { const o = $("#plugs"), n = o.cloneNode(true); o.replaceWith(n); }, null, 40.12);')
        report, rows = self.check()
        self.assert_broke("replaced carried object", report, rows, "hud.seat3", "carried", "not the node")

    def test_the_timeline_is_watched_and_every_real_position_is_a_number(self):
        self.build()
        report = conform.audit_only(self.project)
        self.assertEqual(report["status"], "PASS", report["findings"])

    def test_a_relative_position_in_the_shell_fails_the_audit(self):
        sub(self.project, TIMELINE, "// ---------- captions: hard swap, height from the build ----------", 'const late = ">"; tl.to("#strip", { y: 0, duration: 0.1 }, late);')
        self.build()
        report = conform.audit_only(self.project)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("tl.to() placed by >", " ".join(f["message"] for f in report["findings"]))

    def test_a_missing_position_the_build_reader_cannot_see_fails_the_audit(self):
        sub(self.project, TIMELINE, "// ---------- captions: hard swap, height from the build ----------", 'const none = undefined; tl.set("#strip", { y: 0 }, none);')
        self.build()
        report = conform.audit_only(self.project)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("tl.set() placed by undefined", " ".join(f["message"] for f in report["findings"]))

    def test_a_position_that_is_not_a_real_number_fails_the_audit(self):
        sub(self.project, TIMELINE, "// ---------- captions: hard swap, height from the build ----------", 'tl.set("#strip", { y: 0 }, A(undefined));')
        self.build()
        report = conform.audit_only(self.project)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("tl.set() placed by NaN", " ".join(f["message"] for f in report["findings"]))

    def test_a_root_with_no_box_counts_as_shown(self):
        sub(self.project, SCENES, '<div id="sc-dr" class="scene">', '<div id="sc-dr" class="scene" style="display:contents">')
        self.build()
        report = conform.audit_only(self.project)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("#sc-dr shows", " ".join(f["message"] for f in report["findings"]))

    def test_a_block_writing_into_another_owner(self):
        sub(self.project, TIMELINE, '// ---- b13 vitals', 'tl.set("#gr-word", { x: 1 }, 21.1);')
        report, _ = self.check("b13")
        audit = [f for f in report["findings"] if f["check"] == "owner_audit"]
        self.assertEqual(audit[0]["status"], "FAIL", audit)
        self.assertIn("scene.sc-vit", audit[0]["message"])
        self.assertEqual(report["status"], "FAIL")
        write_record("owner audit", findings=audit)

    def test_a_write_on_an_extra_root_outside_its_window(self):
        sub(self.project, TIMELINE, 'tl.set("#cab3", { attr: { "stroke-dashoffset": 110 } }, A(37.133));', 'tl.set("#cab3", { attr: { "stroke-dashoffset": 110 } }, 40);')
        report, _ = self.check("b19")
        audit = [f for f in report["findings"] if f["check"] == "owner_audit" and f["status"] == "FAIL"]
        self.assertTrue(audit and "outside its window" in audit[0]["message"], report["findings"])
        write_record("extra root window", findings=audit)

    def root_problems(self, report):
        return [f for f in report["findings"] if f["check"] == "owner_audit" and f["status"] == "FAIL"]

    def test_a_block_writing_its_own_root_outside_its_window(self):
        """Finding F16: show the skills card 0.3 s early. One line in its own block, and every other check passes it."""
        sub(self.project, TIMELINE, '        hide("#sk-h1", 30.617);', '        show("#sc-sk", 29.8);\n        hide("#sk-h1", 30.617);')
        self.build()
        report = conform.audit_only(self.project)
        problems = self.root_problems(report)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("writes a scene root: #sc-sk" in f["message"] for f in problems), report["findings"])
        self.assertTrue(any("#sc-sk shows on frame" in f["message"] for f in problems), report["findings"])
        write_record("own root outside its window", findings=problems)

    def test_a_block_writing_its_own_root_past_its_window(self):
        """Finding F23: 'hold this card longer'. It showed from frame 990 to the end of the video."""
        sub(self.project, TIMELINE, '        pop("#dr-tile", 28.69);', '        tl.set("#sc-dr", { opacity: 1 }, 33);\n        pop("#dr-tile", 28.69);')
        self.build()
        problems = self.root_problems(conform.audit_only(self.project))
        self.assertTrue(any("writes a scene root: #sc-dr" in f["message"] for f in problems), problems)
        write_record("own root past its window", findings=problems)

    def test_a_root_left_visible_by_its_markup(self):
        """The same class with no tween at all, which no audit of tweens can see."""
        sub(self.project, SCENES, '<div id="sc-dr" class="scene">', '<div id="sc-dr" class="scene" style="opacity:1">')
        self.build()
        report = conform.audit_only(self.project)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("#sc-dr shows on frame" in f["message"] for f in self.root_problems(report)), report["findings"])

    def test_a_clean_page_passes_the_audit_alone(self):
        report = conform.audit_only(self.project)
        self.assertEqual(report["status"], "PASS", report["findings"])
        self.assertTrue(report["path"].endswith("audit.json"))

    def test_a_build_that_fails_leaves_no_map(self):
        """Finding F21: an event table that no longer matches, after index.html and the map were written."""
        sub(self.project, "tools_local/owners.py", '("b11", "personal life", "scene.sc-grid", "#gr-w1", 19.7)', '("b11", "personal lives", "scene.sc-grid", "#gr-w1", 19.7)')
        with self.assertRaises(subprocess.CalledProcessError):
            self.build()
        self.assertFalse((self.project / "ownership.json").exists())
        self.assertIsNone(ownership.load(self.project))

    def test_a_page_error_fails_the_run(self):
        sub(self.project, TIMELINE, "// ---------- captions: hard swap, height from the build ----------", 'queueMicrotask(() => { throw new Error("planted"); });')
        report, _ = self.check("b13")
        self.assertTrue(any(f["check"] == "runtime" and "planted" in f["message"] for f in report["findings"]), report["findings"])
        self.assertEqual(report["status"], "FAIL")
        write_record("page error", overall=report["status"])

    def test_a_contract_of_another_page_fails_and_no_contract_is_not_a_pass(self):
        path = self.project / "events.json"
        doc = json.loads(path.read_text(encoding="utf8"))
        doc["composition_rev"] = "0" * 64
        path.write_text(json.dumps(doc), encoding="utf8")
        self.assertEqual(conform.conform(self.project, ["b11"])["status"], "FAIL")
        path.unlink()
        self.assertEqual(conform.conform(self.project, ["b11"])["status"], "UNVERIFIED")


def run_node(verb, job, tmp):
    path = tmp / f"{verb}.json"
    path.write_text(json.dumps(job), encoding="utf8")
    subprocess.run(["node", str(RENDER), verb, str(path)], cwd=ROOT, check=True, capture_output=True, timeout=600)


@NEEDS_FIXTURE
class OutputFaults(unittest.TestCase):
    """A temp copy of the review picture's own files: stitched folder, segments and references."""

    @classmethod
    def setUpClass(cls):
        current = store.latest(FIXTURE / "beat", "review")
        cls.source = FIXTURE / "beat" / "stitched" / current["stitched"]
        record = store.read_json(cls.source / "stitch.json")
        cls.ph = record["profile_hash"]
        cls.record = record
        cls.tmp = Path(tempfile.mkdtemp(prefix="beat-check-store-", dir=ROOT / "work"))
        cls.root = cls.tmp / "beat"
        store.open_store(cls.root)
        for beat in record["beats"]:
            for top in ("segments", "refs"):
                src = FIXTURE / "beat" / top / cls.ph[:16] / beat["key"]
                if src.is_dir():
                    shutil.copytree(src, cls.root / top / cls.ph[:16] / beat["key"])
        cls.folder = cls.root / "stitched" / current["stitched"]
        shutil.copytree(cls.source, cls.folder)
        cls.file = cls.folder / "review.mp4"
        cls.baseline = output.check(cls.file, ED, cls.root)
        write_record("output baseline", status=cls.baseline["status"], checks={k: v["status"] for k, v in cls.baseline["checks"].items()})

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def beat(self, id_):
        return next(b for b in self.record["beats"] if b["beat_id"] == id_)

    def copy_stitched(self, name):
        folder = self.root / "stitched" / name
        shutil.copytree(self.folder, folder)
        return folder, folder / "review.mp4"

    def test_the_baseline_binds_to_this_exact_file(self):
        self.assertEqual(self.baseline["file_sha256"], self.record["file_sha256"])
        self.assertEqual(self.baseline["checks"]["binding"]["status"], "PASS")
        for name in ("O1", "O2", "O3"):
            self.assertEqual(self.baseline["checks"][name]["status"], "PASS", name)
        self.assertGreater(self.baseline["checks"]["O7"]["frames_not_compared"], 0)

    def test_corrupted_segment(self):
        beat = self.beat("b10")
        path = store.segment_dir(self.root, self.ph, beat["key"]) / "segment.mp4"
        original = path.read_bytes()
        data = bytearray(original)
        for at in range(len(data) // 2, len(data) // 2 + 64):
            data[at] ^= 0xFF
        path.write_bytes(bytes(data))
        try:
            report = output.check(self.file, ED, self.root)
        finally:
            path.write_bytes(original)
        self.assertEqual(self.baseline["checks"]["O2"]["status"], "PASS")
        self.assertEqual(report["checks"]["O2"]["status"], "FAIL")
        self.assertIn("b10: segment file changed", " ".join(report["checks"]["O2"]["problems"]))
        self.assertEqual(report["status"], "FAIL")
        write_record("corrupted segment", O2=report["checks"]["O2"]["problems"], overall=report["status"])

    def test_o5_names_the_beat_of_a_bad_reference(self):
        beat = self.beat("b19")
        folder = store.refs_dir(self.root, self.ph, beat["key"])
        path = folder / f"{beat['start_frame']}.jpg"
        original = path.read_bytes()
        shutil.copy(next(store.refs_dir(self.root, self.ph, self.beat("b40")["key"]).glob("*.jpg")), path)
        try:
            report = output.check(self.file, ED, self.root)
        finally:
            path.write_bytes(original)
        self.assertEqual(report["checks"]["O5"]["status"], "FAIL")
        self.assertEqual(report["checks"]["O5"]["failed_beats"], ["b19"])

    def test_corrupted_segment_also_refuses_to_stitch(self):
        beat = self.beat("b10")
        record = store.read_json(store.segment_dir(self.root, self.ph, beat["key"]) / "segment.json")
        import stitch as stitcher
        problems = stitcher.check_segments({"beats": [{"beat_id": "b10", "start_frame": beat["start_frame"], "end_frame": beat["end_frame"]}], "total_frames": beat["end_frame"]},
                                           {"b10": beat["key"]}, self.ph, {"b10": {**record, "start_frame": 0}}, {"b10": "something else"})
        self.assertTrue(any("file hash differs" in p for p in problems), problems)

    def test_corrupted_stitched_file(self):
        folder, path = self.copy_stitched("corrupt")
        data = bytearray(path.read_bytes())
        for at in range(len(data) // 2, len(data) // 2 + 4096):
            data[at] ^= 0xFF
        path.write_bytes(bytes(data))
        report = output.check(path, ED, self.root)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["checks"]["binding"]["status"], "FAIL")
        write_record("corrupted stitched file", binding=report["checks"]["binding"]["problems"], O2=report["checks"].get("O2", {}).get("problems"), overall=report["status"])

    def test_a_lost_frame(self):
        folder, path = self.copy_stitched("short")
        total = self.record["beats"][-1]["end_frame"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(self.file), "-frames:v", str(total - 1), "-map", "0", "-c", "copy", str(path)], check=True)
        report = output.check(path, ED, self.root)
        self.assertEqual(report["checks"]["O1"]["status"], "FAIL")
        write_record("lost frame", O1=report["checks"]["O1"]["problems"])

    def test_missing_references_are_not_a_pass(self):
        folder, path = self.copy_stitched("norefs")
        moved = self.root / "refs-away"
        os.replace(self.root / "refs", moved)
        try:
            (self.root / "refs").mkdir()
            report = output.check(path, ED, self.root)
        finally:
            shutil.rmtree(self.root / "refs")
            os.replace(moved, self.root / "refs")
        self.assertEqual(report["checks"]["O5"]["status"], "UNVERIFIED")
        self.assertEqual(report["checks"]["O5"]["frames_compared"], 0)

    def test_planted_flash_goes_red_at_540(self):
        folder, path = self.copy_stitched("flash")
        draw = "drawbox=enable='eq(n\\,650)':x=0:y=450:w=iw:h=60:color=0xEAEAE2:t=fill"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(self.file), "-vf", draw, "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-bf", "0", "-c:a", "copy", str(path)], check=True)
        report = output.check(path, ED, self.root)
        flashes = report["checks"]["O4"]["flash"]["flashes"]
        self.assertEqual(report["checks"]["O4"]["status"], "FAIL")
        self.assertIn(650, [f["frames"][0] for f in flashes])
        self.assertEqual(self.baseline["checks"]["O4"]["flash"]["flashes"], [])
        write_record("planted flash at 540", flashes=flashes)

    def fault_segment(self, id_):
        """A real capture of this beat with the viewport fault shown partway, from the fixture's plan and page. Nothing in the fixture is written."""
        beat = self.beat(id_)
        m = ownership.load(ED)
        profile = json.loads((ROOT / "tools" / "beat_render" / "profiles.json").read_text(encoding="utf8"))["profiles"]["review"]
        plan = store.plan_dir(FIXTURE / "beat", runner.plan_key(m, profile))
        work = self.tmp / "fault"
        work.mkdir(exist_ok=True)
        job = {"plan": str(plan), "project": str(ED), "compiled": str(work / "compiled"), "scratch": str(work / "scratch"), "profile": profile}
        run_node("prepare", {**job, "result": str(work / "prepare-result.json")}, work)
        video = work / f"{id_}.mp4"
        ranges = [{"id": id_, "start": beat["start_frame"], "end": beat["end_frame"], "path": str(video), "inject": {"kind": "viewport"}}]
        run_node("capture", {**job, "ranges": ranges, "result": str(work / "capture-result.json"), "fresh": False, "page_rotate_frames": profile["page_rotate_frames"]}, work)
        return beat, video, profile

    def test_stuck_layout_fault(self):
        id_ = "b10"
        beat, video, profile = self.fault_segment(id_)
        rows, _, suspects = sentinel.scan(video, profile["width"], profile["height"])
        self.assertTrue(suspects, "the injected capture should show the clip")
        seg = store.segment_dir(self.root, self.ph, beat["key"])
        keep = {name: (seg / name).read_bytes() for name in ("segment.mp4", "segment.framemd5", "segment.json")}
        # Two cases. Bad frames that disagree with their segment, and the case that matters: a bad segment that got published with matching hashes, as if the sentinel had missed it.
        folder, path = self.copy_stitched("stuck")
        listing = self.tmp / "concat.txt"
        parts = [store.segment_dir(self.root, self.ph, b["key"]) / "segment.mp4" if b["beat_id"] != id_ else video for b in self.record["beats"]]
        listing.write_text("\n".join(f"file '{p.as_posix()}'" for p in parts) + "\n", encoding="utf8", newline="\n")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-i", str(self.file), "-map", "0:v:0", "-map", "1:a:0", "-c", "copy", "-movflags", "+faststart", str(path)], check=True)
        disagree = output.check(path, ED, self.root)
        self.assertEqual(disagree["checks"]["O2"]["status"], "FAIL")
        self.assertEqual(disagree["checks"]["O5"]["status"], "FAIL")

        stitched = store.read_json(folder / "stitch.json")
        stitched["file_sha256"] = sound_mix.file_hash(path)
        row = next(b for b in stitched["beats"] if b["beat_id"] == id_)
        row["content_hash"] = sha("\n".join(rows))
        store.write_json(folder / "stitch.json", stitched)
        record = json.loads(keep["segment.json"])
        record.update(file_sha256=sound_mix.file_hash(video), bytes=video.stat().st_size)
        record["decoded"]["content_hash"] = row["content_hash"]
        shutil.copy(video, seg / "segment.mp4")
        (seg / "segment.framemd5").write_text("\n".join(rows) + "\n", encoding="utf8", newline="\n")
        store.write_json(seg / "segment.json", record)
        try:
            published = output.check(path, ED, self.root)
        finally:
            for name, data in keep.items():
                (seg / name).write_bytes(data)
        o5 = published["checks"]["O5"]
        self.assertEqual(published["checks"]["O2"]["status"], "PASS")
        self.assertEqual(o5["status"], "FAIL")
        self.assertGreater(o5["clip_suspects"], 0)
        inside = [f for f in o5["failed"] if beat["start_frame"] <= f["frame"] < beat["end_frame"]]
        self.assertTrue(inside, o5)
        self.assertLess(min(f["psnr"] for f in inside), 20)
        self.assertEqual(published["status"], "FAIL")
        write_record("stuck layout", beat=id_, frames_clipped=len(suspects), disagree_O2=disagree["checks"]["O2"]["problems"], published_O2="PASS", O5_failed=inside, clip_suspects=o5["clip_suspects"], overall=published["status"])


def main():
    quick = "--quick" in sys.argv
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    fast = (Points, Time, Word, Verdicts, Contract, SceneRoots, ReportNames, Motionlint)
    slow = () if quick else (SourceFaults, OutputFaults)
    for case in fast + slow:
        suite.addTests(loader.loadTestsFromTestCase(case))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not quick and EVIDENCE.parent.is_dir():
        EVIDENCE.write_text(json.dumps({"testsRun": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "rows": RECORD}, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
