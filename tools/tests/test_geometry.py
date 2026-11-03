"""Geometry regressions, using only temporary handmade projects.

  python -B tools/tests/test_geometry.py
  python -B tools/tests/test_geometry.py --browser
  python -B tools/tests/test_geometry.py --fixture

Default tests exercise verdicts and CLI with recorded DOM measurements.
--browser also seeks a small handmade GSAP page through the real pinned
HyperFrames browser. --fixture checks both approved editorial projects read-only (all events). These never render, rebuild the fixture, or write reports in it.
"""
import contextlib
import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "beat_check"))
import geometry as g

BROWSER = "--browser" in sys.argv
FIXTURE = "--fixture" in sys.argv
sys.argv[:] = [s for s in sys.argv if s not in ("--browser", "--fixture")]


def event(**kw):
    e = dict(event_id="b01.e1", beat_id="b01", frame=30, target="#mark",
             geometry={"target_box": [100, 200, 120, 40]}, layout="split",
             text_containers={}, what="outline on target", owner="scene.s")
    e.update(kw)
    return e


def node(selector="#mark", rect=None, **kw):
    n = dict(selector=selector, box=rect or [100, 200, 120, 40], visible=True,
             unsupported=None, text="target", loaded=True, markPaint=True)
    n.update(kw)
    return n


def snapshot(**kw):
    n = node()
    s = dict(viewport=[1080, 1920], elements=[dict(n, scene=[0, 0, 1080, 960])],
             texts=[dict(selector="#label", box=[100, 200, 120, 40], ink=[[100, 205, 100, 25]],
                         scene=[0, 0, 1080, 960], card=[90, 190, 160, 70], overflow=[0, 0], inline=False)],
             media=[], selected={"#mark": dict(count=1, nodes=[n])}, unknown=[])
    s.update(kw)
    return s


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf8")


def make_project(path, html="<html><body>handmade fixture</body></html>", count=1):
    path.mkdir(parents=True, exist_ok=True)
    (path / "index.html").write_text(html, encoding="utf8")
    own = dict(schema=1, html_sha256=hashlib.sha256((path/"index.html").read_bytes()).hexdigest(),
               fps=30, total_frames=90, owners=[dict(id="scene.s", kind="scene", roots=["#scene"])])
    own["composition_rev"] = g.digest(own)
    write_json(path / "ownership.json", own)
    events, beats = [], []
    for i in range(count):
        id_ = f"b{i+1:02}"
        beats.append(dict(id=id_, start=i, end=i+1, layout="split", crops=[], actions=[], sub_anchors=[],
                          anchor=dict(event_id=id_+".e1", t=i+1, what="outline", geometry={"target_box": [100, 200, 120, 40]})))
        events.append(dict(event_id=id_+".e1", beat_id=id_, kind="anchor", frame=30*(i+1), target="#mark",
                           owner="scene.s", expect="present"))
    doc = dict(schema=1, composition_rev=own["composition_rev"], html_sha256=own["html_sha256"],
               fps=30, total_frames=90, events=events)
    write_json(path / "events.json", doc)
    write_json(path / "plan.json", dict(beats=beats))
    return path


class Boxes(unittest.TestCase):
    def test_invalid_boxes(self):
        for value in (None, [], [0, 0, -1, 20], [0, 0, 10, float("nan")], [True, 0, 10, 20]):
            with self.subTest(value=value):
                self.assertIsNone(g.box(value))

    def test_largest_edge_excess_not_center_distance(self):
        self.assertEqual(g.outside([100, 100, 150, 40], [100, 100, 120, 40]), 30)
        self.assertEqual(g.outside([-12, -5, 10, 10], [0, 0, 1080, 1920]), 12)

    def test_tolerance_and_twenty_pixel_boundary(self):
        for shift, wanted in ((0, "PASS"), (3, "PASS"), (3.01, "WARN"), (20, "WARN"), (20.01, "FAIL")):
            with self.subTest(shift=shift):
                status, px = g.judge_mark([100+shift, 200, 120, 40], [100, 200, 120, 40])
                self.assertEqual(status, wanted)
                self.assertAlmostEqual(px, shift)

    def test_width_error_with_same_center(self):
        self.assertEqual(g.judge_mark([80, 200, 160, 40], [100, 200, 120, 40]), ("WARN", 20))

    def test_underlines_compare_target_bottom_and_span(self):
        self.assertEqual(g.judge_mark([100, 245, 120, 3], [100, 200, 120, 40], "underline", gap=5), ("PASS", 0))
        self.assertEqual(g.judge_mark([100, 200, 120, 3], [100, 200, 120, 40], "underline", gap=5), ("FAIL", 45))

    def test_circle_padding(self):
        self.assertEqual(g.judge_mark([95, 195, 130, 50], [100, 200, 120, 40], "circle", padding=5), ("PASS", 0))

    def test_different_element_fails_even_with_zero_error(self):
        self.assertEqual(g.judge_mark([0, 0, 10, 10], [0, 0, 10, 10], different=True), ("FAIL", 0))

    def test_crop_edges_slice_but_touching_and_excluded_text_do_not(self):
        self.assertEqual(g.crop_cuts([0, 0, 100, 50], [20, 40, 40, 20]), [("bottom", 10)])
        self.assertEqual(g.crop_cuts([0, 0, 100, 40], [20, 40, 40, 20]), [])
        self.assertEqual(g.crop_cuts([0, 0, 100, 50], [200, 40, 40, 20]), [])
        self.assertEqual(g.crop_cuts([0, 0, 100, 50], [10, 10, 20, 20]), [])

    def test_all_four_crop_edges(self):
        self.assertEqual(g.crop_cuts([20, 20, 20, 20], [10, 10, 40, 40]),
                         [("left", 10), ("right", 10), ("top", 10), ("bottom", 10)])


class Verdicts(unittest.TestCase):
    def text(self, **kw):
        s = snapshot()
        s["texts"][0].update(kw)
        return next(r for r in g.judge_snapshot(event(), s) if r["check"] == "text_overflow")

    def test_scroll_metrics_do_not_override_rendered_ink(self):
        self.assertEqual(self.text(overflow=[100, 100])["status"], "PASS")

    def test_horizontal_and_vertical_ink(self):
        for ink, excess in (([[100, 205, 131, 25]], 11), ([[100, 205, 100, 50]], 15)):
            row = self.text(ink=ink)
            self.assertEqual((row["status"], row["px"]), ("WARN", excess))

    def test_ink_tolerance_boundaries(self):
        for excess, status in ((0, "PASS"), (4, "PASS"), (4.01, "WARN"), (20, "WARN"), (20.01, "FAIL")):
            with self.subTest(excess=excess):
                row = self.text(ink=[[100, 205, 120+excess, 25]], card=None)
                self.assertEqual(row["status"], status)
                self.assertAlmostEqual(row["px"], excess)

    def test_large_vertical_ink_is_still_failure(self):
        row = self.text(box=[100, 200, 120, 10], ink=[[100, 200, 100, 40]], card=None)
        self.assertEqual((row["status"], row["px"]), ("FAIL", 30))

    def test_all_wrapped_range_rects_are_checked(self):
        row = self.text(ink=[[100, 200, 80, 20], [100, 225, 150, 20]], card=None)
        self.assertEqual((row["status"], row["px"]), ("FAIL", 30))

    def test_scene_ink_in_split_and_full_graphic(self):
        n = dict(selector="#label", box=[100, 940, 120, 100], ink=[[100, 970, 100, 25]],
                 scene=[0, 0, 1080, 1920], inline=False)
        for layout, status in (("split", "FAIL"), ("full-graphic", "PASS")):
            row = next(r for r in g.judge_snapshot(event(layout=layout), snapshot(texts=[n])) if r["check"] == "text_overflow")
            self.assertEqual(row["status"], status)

    def test_shell_uses_frame_in_split_layout(self):
        self.assertEqual(self.text(scene=None, card=None, box=[100, 1200, 120, 40],
                                   ink=[[100, 1205, 100, 25]])["status"], "PASS")

    def test_mid_transition_is_unverified_never_failure(self):
        self.assertEqual(self.text(moving=True, ink=[[-100, 0, 500, 500]])["status"], "UNVERIFIED")
        s = snapshot(elements=[dict(selector="#moving", box=[-100, 0, 1080, 960], moving=True)])
        row = next(r for r in g.judge_snapshot(event(), s) if r["check"] == "off_canvas")
        self.assertEqual(row["status"], "UNVERIFIED")

    def test_ink_past_card_even_when_own_box_is_wide_enough(self):
        row = self.text(box=[100, 200, 200, 40], ink=[[100, 205, 160, 25]], card=[90, 190, 160, 70])
        self.assertEqual((row["status"], row["px"]), ("WARN", 10))

    def test_nested_inline_text_past_block_parent(self):
        row = self.text(inline=True, card=None, containers=[[100, 200, 50, 40]])
        self.assertEqual((row["status"], row["px"]), ("FAIL", 50))

    def test_text_outside_scene(self):
        row = self.text(box=[100, 950, 120, 40], ink=[[100, 955, 100, 25]], card=None)
        self.assertEqual((row["status"], row["px"]), ("WARN", 20))

    def test_inline_zero_metrics_are_not_automatic_overflow(self):
        self.assertEqual(self.text(inline=True, box=[100, 200, 0, 0])["status"], "PASS")

    def test_unsupported_text_is_unverified(self):
        self.assertEqual(self.text(unsupported="perspective")["status"], "UNVERIFIED")
        self.assertEqual(self.text(cardError="missing card")["status"], "UNVERIFIED")

    def test_off_canvas_and_split_panel(self):
        for rect, px in (([1070, 200, 30, 20], 20), ([100, 950, 30, 30], 20), ([-10, 200, 30, 20], 10)):
            s = snapshot(elements=[dict(selector="#bad", box=rect, scene=[0, 0, 1080, 1920])])
            row = next(r for r in g.judge_snapshot(event(), s) if r["check"] == "off_canvas")
            self.assertEqual((row["status"], row["px"]), ("FAIL", px))

    def test_full_graphic_can_use_bottom_panel(self):
        s = snapshot(elements=[dict(selector="#good", box=[100, 1200, 100, 100], scene=[0, 0, 1080, 1920])])
        row = next(r for r in g.judge_snapshot(event(layout="full-graphic"), s) if r["check"] == "off_canvas")
        self.assertEqual(row["status"], "PASS")

    def test_empty_page_does_not_pass(self):
        rows = g.judge_snapshot(event(), snapshot(elements=[], texts=[]))
        self.assertTrue(rows)
        self.assertTrue(all(r["status"] == "UNVERIFIED" for r in rows))

    def test_no_target_hidden_target_and_legacy_prose_never_pass(self):
        for e, s in ((event(target=None), snapshot()), (event(geometry={}), snapshot()),
                     (event(), snapshot(selected={"#mark": dict(count=1, nodes=[node(visible=False)])}))):
            with self.subTest(event=e):
                self.assertEqual(g.judge_highlight(e, s)[0]["status"], "UNVERIFIED")

    def test_selector_must_match_exactly_once(self):
        for count in (0, 2):
            s = snapshot(selected={"#mark": dict(count=count, nodes=[])})
            self.assertEqual(g.judge_highlight(event(), s)[0]["status"], "UNVERIFIED")

    def test_unpainted_marker_box_cannot_pass(self):
        s = snapshot()
        s["selected"]["#mark"]["nodes"][0]["markPaint"] = False
        self.assertEqual(g.judge_highlight(event(), s)[0]["status"], "UNVERIFIED")

    def test_marker_cannot_be_its_own_target(self):
        self.assertEqual(g.judge_highlight(event(geometry={"target_selector": "#mark"}), snapshot())[0]["status"], "UNVERIFIED")

    def test_mismatched_bind_is_wrong_element(self):
        row = g.judge_highlight(event(geometry={"mark_selector": "#other", "target_box": [100, 200, 120, 40]}), snapshot())[0]
        self.assertEqual(row["status"], "FAIL")

    def test_neighbour_ten_pixels_away_is_still_wrong_element(self):
        s = snapshot()
        s["selected"]["#wanted"] = dict(count=1, nodes=[node("#wanted", [90, 200, 120, 40])])
        s["elements"].append(dict(selector="#other", box=[100, 200, 120, 40]))
        row = g.judge_highlight(event(geometry={"target_selector": "#wanted"}), s)[0]
        self.assertEqual((row["status"], row["px"]), ("FAIL", 10))

    def test_target_text_identity(self):
        s = snapshot()
        s["selected"]["#wanted"] = dict(count=1, nodes=[node("#wanted", text="wrong line")])
        row = g.judge_highlight(event(geometry={"target_selector": "#wanted", "target_text": "right line"}), s)[0]
        self.assertEqual(row["status"], "FAIL")

    def test_tolerance_cannot_hide_large_errors(self):
        row = g.judge_highlight(event(geometry={"target_box": [100, 200, 120, 40], "tolerance_px": 30}), snapshot())[0]
        self.assertEqual(row["status"], "UNVERIFIED")


class SettledAndStateCoverage(unittest.TestCase):
    def test_same_state_is_judged_once_and_keeps_all_frames(self):
        cache = {}
        with mock.patch.object(g, "node_verdict", wraps=g.node_verdict) as judge:
            rows = g.judge_snapshot(event(), snapshot(), cache)
            rows += g.judge_snapshot(event(frame=45, event_id="b01.e2"), snapshot(), cache)
            self.assertEqual(judge.call_count, 2)  # one element and one text state
        combined = g.combine_findings(rows)
        label = next(r for r in combined if r["element"] == "#label")
        self.assertEqual(label["frames"], [30, 45])
        self.assertEqual(label["frame_span"], [30, 45])
        self.assertEqual(len(label["states"]), 1)

    def test_changed_state_keeps_worst_frame_and_evidence(self):
        rows = g.judge_snapshot(event(), snapshot())
        bad = snapshot()
        bad["texts"][0]["ink"] = [[100, 205, 151, 25]]
        rows += g.judge_snapshot(event(frame=50), bad)
        rows += g.judge_snapshot(event(frame=60), snapshot())
        label = next(r for r in g.combine_findings(rows) if r["element"] == "#label")
        self.assertEqual((label["status"], label["px"], label["frame"]), ("FAIL", 31, 50))
        self.assertEqual(label["frames"], [30, 50, 60])
        self.assertEqual(len(label["states"]), 2)
        self.assertEqual(label["ink"], [[100, 205, 151, 25]])

    def test_settled_fit_does_not_use_mid_entrance_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            p = make_project(Path(temp)/"p")
            moving = snapshot(elements=[dict(selector="#move", box=[-100, 0, 100, 100])])
            moving["texts"][0]["ink"] = [[-100, 0, 400, 100]]
            moving["settled"] = dict(snapshot(), frame=36, timing_verified=True)
            with mock.patch.object(g, "run_measure", return_value={"frames": {"30": moving}}):
                report = g.geometry(p)
            self.assertFalse(any(r["status"] == "FAIL" for r in report["findings"]), report)
            self.assertEqual(report["events"][0]["settled_frame"], 36)
            self.assertTrue(all(r["frame"] == 36 for r in report["findings"] if r["check"] in ("off_canvas", "text_overflow")))

    def test_resting_defect_is_not_hidden_by_settling(self):
        with tempfile.TemporaryDirectory() as temp:
            p = make_project(Path(temp)/"p")
            s = snapshot()
            bad = snapshot()
            bad["texts"][0]["ink"] = [[100, 205, 151, 25]]
            s["settled"] = dict(bad, frame=36, timing_verified=True)
            with mock.patch.object(g, "run_measure", return_value={"frames": {"30": s}}):
                report = g.geometry(p)
            row = next(r for r in report["findings"] if r["check"] == "text_overflow")
            self.assertEqual((row["status"], row["frame"]), ("FAIL", 36))

    def test_crop_selectors_and_hold_limit_reach_browser_request(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            e = event(beat_end=2, crops=[dict(plate_selector="#capture")])
            def measured(command, **kw):
                job = g.read_json(Path(command[-1]))
                row = job["frames"]["30"]
                self.assertIn("#capture", row["selectors"])
                self.assertEqual(row["limit"], 2)
                write_json(Path(job["out"]), {"frames": {"30": snapshot()}})
            with mock.patch.object(g.subprocess, "run", side_effect=measured):
                result = g.run_measure(p, 30, [e], dict(total_frames=90, owners=[]))
            self.assertIn("30", result["frames"])


class Metadata(unittest.TestCase):
    def test_capture_dpr_and_nontext_boxes(self):
        meta = dict(dpr=2, boxes=[dict(tag="h1", text="Title", x=10, y=20, w=100, h=30),
                                  dict(tag="img", text="logo", x=1, y=2, w=3, h=4)])
        self.assertEqual(g.text_boxes(meta), [dict(text="Title", box=[20, 40, 200, 60])])

    def test_page_origin_and_explicit_image_units(self):
        meta = dict(dpr=2, units="css", origin="page", crop_css=[100, 200, 300, 400],
                    text_boxes=[dict(x=110, y=220, w=30, h=40, text="Line")])
        self.assertEqual(g.text_boxes(meta)[0]["box"], [20, 40, 60, 80])
        meta.update(units="image", origin="local")
        self.assertEqual(g.text_boxes(meta)[0]["box"], [110, 220, 30, 40])

    def test_empty_or_invalid_metadata_never_proves_no_text(self):
        for meta in ({}, {"boxes": []}, {"text_boxes": [[0, 0, -10, 20]]},
                     {"dpr": 0, "text_boxes": [[0, 0, 10, 20]]}):
            with self.subTest(meta=meta), self.assertRaises(ValueError):
                g.text_boxes(meta)

    def test_sidecar_and_inventory_and_path_confinement(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "p"
            (p / "assets").mkdir(parents=True)
            asset = p / "assets/a.png"
            asset.write_bytes(b"fixture")
            write_json(asset.with_suffix(".json"), {"text_boxes": [[10, 20, 30, 40]]})
            self.assertEqual(g.asset_text(p, "assets/a.png")[0][0]["box"], [10, 20, 30, 40])
            asset.with_suffix(".json").unlink()
            fence = chr(96)*3
            (p / "ASSETS.md").write_text(fence+"json\n"+json.dumps({"assets": {"assets/a.png": {"text_boxes": [[1, 2, 3, 4]]}}})+"\n"+fence, encoding="utf8")
            self.assertEqual(g.asset_text(p, "assets/a.png")[0][0]["box"], [1, 2, 3, 4])
            with self.assertRaises(ValueError):
                g.asset_text(p, "../outside.png")

    def test_crop_uses_actual_page_window_not_planned_window(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "p"
            (p / "assets").mkdir(parents=True)
            (p / "assets/a.png").write_bytes(b"fixture")
            write_json(p/"assets/a.json", {"text_boxes": [dict(box=[20, 40, 40, 20], text="line")]})
            image = node("#image", [100, 200, 200, 100], src="assets/a.png", natural=[200, 100],
                         fit="fill", source_crop=[0, 0, 100, 50])
            beat = dict(id="b01", crops=[dict(asset="assets/a.png", rect_src=[0, 0, 100, 40])])
            rows = g.judge_crops(p, beat, snapshot(media=[image]), 30)
            self.assertTrue(any(r["check"] == "crop_plan" and r["status"] == "WARN" for r in rows))
            self.assertTrue(any(r["check"] == "crop_text" and r["status"] == "WARN" and r["px"] == 10 for r in rows))

    def test_built_image_maps_source_box(self):
        image = node("#image", [100, 200, 400, 200], src="a.png", natural=[200, 100], fit="fill")
        self.assertEqual(g.image_box(snapshot(media=[image]), "a.png", [10, 20, 30, 40]), [120, 240, 60, 80])
        with self.assertRaises(ValueError):
            g.image_box(snapshot(media=[image, image]), "a.png", [10, 20, 30, 40])
        image["fit"] = "cover"
        with self.assertRaises(ValueError):
            g.image_box(snapshot(media=[image]), "a.png", [10, 20, 30, 40])


class ContractAndCLI(unittest.TestCase):
    def test_read_binds_without_executing_python(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            (p/"tools_local").mkdir()
            (p/"tools_local/owners.py").write_text("raise RuntimeError('must not execute')\nEVENT_BINDS = {'b01.e1': ('scene.s', '#mark', 'appear', None, None)}\n", encoding="utf8")
            self.assertEqual(g.literal_binds(p)["b01.e1"][1], "#mark")

    def test_missing_plan_event_gets_a_job_without_invented_frame(self):
        plan = {"beats": [dict(id="b01", layout="split", anchor={"event_id": "b01.e1", "t": 1}, actions=[], sub_anchors=[])]}
        jobs = g.jobs_of(plan, {"events": []})
        self.assertEqual(jobs[0]["event_id"], "b01.e1")
        self.assertNotIn("frame", jobs[0])

    def test_stale_event_time_cannot_measure_a_different_frame(self):
        plan = {"beats": [dict(id="b01", anchor={"event_id": "b01.e1", "t": 2})]}
        jobs = g.jobs_of(plan, {"fps": 30, "events": [dict(event_id="b01.e1", frame=30)]})
        self.assertNotIn("frame", jobs[0])
        self.assertIn("rebuild", jobs[0]["frame_problem"])

    def test_unbound_event_summary_is_unverified(self):
        with tempfile.TemporaryDirectory() as temp:
            p = make_project(Path(temp)/"p")
            doc = g.read_json(p/"events.json")
            doc["events"][0]["target"] = None
            write_json(p/"events.json", doc)
            with mock.patch.object(g, "run_measure", return_value={"frames": {"30": snapshot()}}):
                report = g.geometry(p)
            self.assertEqual(report["events"][0]["status"], "UNVERIFIED")
            self.assertEqual(g.exit_code(report), 0)

    def test_caption_lead_uses_layout_at_sample_frame(self):
        plan = dict(beats=[dict(id="b01", start=0, end=1, layout="full-graphic"),
                           dict(id="b02", start=1, end=2, layout="split")])
        doc = dict(fps=30, events=[dict(event_id="cap.lead", beat_id="b02", frame=27)])
        e = g.jobs_of(plan, doc)[0]
        self.assertEqual((e["layout"], e["fit_beat_id"], e["beat_end"]), ("full-graphic", "b01", 1))

    def test_scope_selects_events_not_only_anchors(self):
        plan = {"beats": [dict(id="b01", anchor={"event_id": "b01.e1"}), dict(id="b02", anchor={"event_id": "b02.e1"})]}
        doc = {"fps": 30, "events": [dict(event_id="cap.one", beat_id="b01", frame=5)]}
        self.assertEqual([e["event_id"] for e in g.jobs_of(plan, doc, ["b01"])], ["b01.e1", "cap.one"])

    def test_stale_page_is_exit_four_without_browser(self):
        with tempfile.TemporaryDirectory() as temp:
            p = make_project(Path(temp)/"p")
            (p/"index.html").write_text("changed", encoding="utf8")
            with mock.patch.object(g, "run_measure") as run:
                report = g.geometry(p)
            run.assert_not_called()
            self.assertEqual(g.exit_code(report), 4)
            self.assertFalse(report["measured"])

    def test_bad_event_revision_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            p = make_project(Path(temp)/"p")
            doc = g.read_json(p/"events.json")
            doc["composition_rev"] = "wrong"
            write_json(p/"events.json", doc)
            self.assertEqual(g.exit_code(g.geometry(p)), 4)

    def test_unavailable_browser_is_exit_four(self):
        with tempfile.TemporaryDirectory() as temp:
            p = make_project(Path(temp)/"p")
            with mock.patch.object(g, "run_measure", side_effect=OSError("browser denied")):
                report = g.geometry(p)
            self.assertEqual(g.exit_code(report), 4)
            self.assertIn("browser denied", report["findings"][0]["message"])

    def test_partial_measurement_is_exit_four(self):
        with tempfile.TemporaryDirectory() as temp:
            p = make_project(Path(temp)/"p", count=2)
            with mock.patch.object(g, "run_measure", return_value={"frames": {"30": snapshot()}}):
                report = g.geometry(p)
            self.assertEqual((g.exit_code(report), report["frames_measured"]), (4, 1))

    def test_cli_prints_findings_and_writes_only_requested_report(self):
        with tempfile.TemporaryDirectory() as temp:
            p = make_project(Path(temp)/"p")
            before = {f.name: f.read_bytes() for f in p.iterdir()}
            output = Path(temp)/"report.json"
            with mock.patch.object(g, "run_measure", return_value={"frames": {"30": snapshot()}}), contextlib.redirect_stdout(io.StringIO()) as text:
                code = g.main([str(p), "--beats", "b01", "--json", str(output)])
            self.assertEqual(code, 0)
            report = g.read_json(output)
            self.assertEqual((report["status"], report["scope"]), ("PASS", ["b01"]))
            self.assertIn("PASS b01", text.getvalue())
            self.assertIn("px)", text.getvalue())
            self.assertEqual(before, {f.name: f.read_bytes() for f in p.iterdir()})

    def test_fails_are_exit_one_even_with_unverified_findings(self):
        with tempfile.TemporaryDirectory() as temp:
            p = make_project(Path(temp)/"p")
            s = snapshot()
            s["texts"][0]["ink"] = [[100, 205, 150, 25]]
            s["selected"]["#mark"]["nodes"][0]["visible"] = False
            with mock.patch.object(g, "run_measure", return_value={"frames": {"30": s}}):
                report = g.geometry(p)
            self.assertEqual((report["status"], g.exit_code(report)), ("FAIL", 1))

    def test_unknown_beat_is_a_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            p = make_project(Path(temp)/"p")
            self.assertEqual(g.exit_code(g.geometry(p, ["no-such-beat"])), 1)

    def test_unverified_and_warn_without_fail_exit_zero_after_measurement(self):
        for status in ("WARN", "UNVERIFIED"):
            self.assertEqual(g.exit_code(dict(measured=True, findings=[{"status": status}])), 0)


HANDMADE = """<!doctype html><html><head>
<meta name="viewport" content="width=1080,height=1920">
<script src="gsap.min.js"></script>
<style>
*{box-sizing:border-box;margin:0}html,body,#root{width:1080px;height:1920px;overflow:hidden}
.scene{position:absolute;width:1080px;height:960px}
.box{position:absolute;width:100px;height:60px;top:200px;left:300px}
#mark{border:3px solid red;left:310px}
#wide{position:absolute;left:100px;top:100px;width:60px;white-space:nowrap;font:20px monospace}
#tall{position:absolute;left:100px;top:140px;width:200px;height:10px;font:20px monospace;overflow:hidden}
#outside{position:absolute;left:1070px;top:300px;width:30px;height:30px}
#low{position:absolute;left:100px;top:950px;width:30px;height:30px}
#clip{position:absolute;left:500px;top:300px;width:100px;height:50px;overflow:hidden}
#clip img{position:absolute;width:200px;height:100px}
#hidden{opacity:0}#hidden div{position:absolute;left:-500px;width:100px;height:100px}
/* Overflow plant is unclipped; intentional parent clipping is the roller below. */
#parent{position:absolute;left:700px;top:300px;width:30px;height:40px}
#roller{position:absolute;left:800px;top:400px;width:30px;height:40px;overflow:hidden}
#roller span{position:absolute;left:-10px;top:-5px;white-space:nowrap;font:20px monospace}
#empty-group{position:absolute;left:-200px;top:-200px;width:1400px;height:1300px}
#empty-group div{position:absolute;left:300px;top:600px;width:20px;height:20px;background:red}
</style></head><body><div id="root" data-composition-id="main" data-width="1080" data-height="1920" data-duration="3">
<div id="scene" class="scene"><div id="wide">a line far too wide</div><div id="tall">tall</div>
<div id="target" class="box"></div><div id="mark" class="box"></div>
<div id="outside"></div><div id="low"></div><div id="hidden"><div id="hidden-child"></div></div>
<div id="clip"><img id="capture" src="capture.svg"></div>
<div id="parent"><span id="inline">nested text too wide</span></div>
<div id="roller"><span id="rolling">0123456789</span></div>
<div id="empty-group"><div id="painted-child"></div><div id="painted-outside" style="left:0;top:0"></div></div>
</div></div>
<script>
const tl=gsap.timeline({paused:true});
tl.set('#mark',{x:30},2);
tl.set('#mark',{opacity:0},2.5);
tl.set('#root',{opacity:1},2.999);
window.__timelines={main:tl};
</script></body></html>"""


@unittest.skipUnless(BROWSER, "pass --browser to seek the handmade page in Chromium")
class BrowserMeasurements(unittest.TestCase):
    def test_handmade_page_at_three_event_frames(self):
        with tempfile.TemporaryDirectory(prefix="geometry-test-") as temp:
            p = make_project(Path(temp)/"p", HANDMADE, count=3)
            shutil.copyfile(ROOT/"work/beat-fixture/v2/editorial/assets/vendor/gsap.min.js", p/"gsap.min.js")
            (p/"capture.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100"><rect width="200" height="100" fill="white"/><text x="10" y="58" font-size="20">measured text</text></svg>', encoding="utf8")
            write_json(p/"capture.json", {"text_boxes": [dict(box=[10, 40, 180, 20], text="measured text")]})
            plan = g.read_json(p/"plan.json")
            doc = g.read_json(p/"events.json")
            for beat, e, frame in zip(plan["beats"], doc["events"], (30, 60, 75)):
                e["frame"] = frame
                beat["anchor"]["t"] = frame/30
                beat["anchor"]["geometry"] = {"target_selector": "#target"}
                beat["crops"] = [dict(asset="capture.svg", rect_src=[0, 0, 100, 50], plate_selector="#capture")]
            write_json(p/"plan.json", plan)
            write_json(p/"events.json", doc)
            report = g.geometry(p)
            self.assertTrue(report["measured"], report)
            self.assertEqual(report["frames_measured"], 3)
            rows = report["findings"]
            self.assertTrue(any(r["element"] == "#wide" and r["check"] == "text_overflow" and r["status"] == "FAIL" for r in rows), rows)
            self.assertTrue(any(r["element"] == "#tall" and r["check"] == "text_overflow" and r["status"] == "WARN" for r in rows), rows)
            self.assertTrue(any(r["element"] == "#inline" and r["check"] == "text_overflow" and r["status"] == "FAIL" for r in rows), rows)
            self.assertFalse(any(r["element"] == "#empty-group" for r in rows), rows)
            self.assertTrue(any(r["element"] == "#rolling" and r["check"] == "text_overflow" and r["status"] == "PASS" for r in rows), rows)
            self.assertTrue(any(r["element"] == "#painted-outside" and r["check"] == "off_canvas" and r["status"] == "FAIL" for r in rows), rows)
            for element in ("#outside", "#low"):
                self.assertTrue(any(r["element"] == element and r["check"] == "off_canvas" and r["status"] == "FAIL" for r in rows), rows)
            self.assertFalse(any(r["element"] == "#hidden-child" for r in rows))
            self.assertFalse(any(r["element"] == "#capture" and r["check"] == "off_canvas" and r["status"] == "FAIL" for r in rows))
            marks = {r["element"]: r["status"] for r in rows if r["check"] == "highlight"}
            self.assertEqual(marks, {"b01.e1": "WARN", "b02.e1": "FAIL", "b03.e1": "UNVERIFIED"})
            self.assertTrue(any(r["check"] == "crop_text" and r["status"] == "WARN" for r in rows), rows)


    def test_entrance_settles_and_continuous_motion_is_unverified(self):
        html = HANDMADE
        html = html.replace("tl.set('#mark',{x:30},2);", """
        tl.fromTo('#outside',{x:-100},{x:-200,duration:.4,ease:'none'},0);
        tl.fromTo('#low',{x:0},{x:30,duration:3,ease:'none'},0);
        """)
        with tempfile.TemporaryDirectory(prefix="geometry-hold-") as temp:
            p = make_project(Path(temp)/"p", html)
            shutil.copyfile(ROOT/"work/beat-fixture/v2/editorial/assets/vendor/gsap.min.js", p/"gsap.min.js")
            (p/"capture.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100"/>', encoding="utf8")
            plan, doc = g.read_json(p/"plan.json"), g.read_json(p/"events.json")
            plan["beats"][0].update(end=3, anchor=dict(event_id="b01.e1", t=0, what=""))
            doc["events"][0].update(frame=0, target="#outside")
            write_json(p/"plan.json", plan)
            write_json(p/"events.json", doc)
            report = g.geometry(p)
            self.assertTrue(report["measured"], report)
            self.assertEqual(report["events"][0]["settled_frame"], 12)
            rows = report["findings"]
            outside = next(r for r in rows if r["element"] == "#outside" and r["check"] == "off_canvas")
            self.assertEqual(outside["status"], "PASS", outside)
            low = next(r for r in rows if r["element"] == "#low" and r["check"] == "off_canvas")
            self.assertEqual(low["status"], "UNVERIFIED", low)
            self.assertTrue(any(r["element"] == "#wide" and r["status"] == "FAIL" for r in rows))


@unittest.skipUnless(FIXTURE, "pass --fixture for a read-only run of the real editorial project")
class RealFixture(unittest.TestCase):
    def check_project(self, name):
        project = ROOT/"work"/name/"v2/editorial"
        # Missing old prose targets/binds stay UNVERIFIED; approved fit must not FAIL.
        files = [project/name for name in ("index.html", "plan.json", "events.json", "ownership.json", "tools_local/owners.py")]
        before = {str(p): p.read_bytes() for p in files}
        report = g.geometry(project)
        self.assertTrue(report["measured"], report)
        self.assertGreater(report["frames_measured"], 1)
        self.assertTrue(report["events"])
        self.assertEqual([r for r in report["findings"] if r["status"] == "FAIL"], [], report)
        self.assertEqual(before, {str(p): p.read_bytes() for p in files})

    def test_real_project_read_only(self):
        self.check_project("beat-fixture")

    def test_delivered_project_read_only(self):
        self.check_project("1030-2")


if __name__ == "__main__":
    unittest.main()
