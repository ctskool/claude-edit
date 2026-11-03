"""Regression cases from review2. Only temporary projects are written."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_beat_final as f
import test_beat_review as r


class SoundFiles(f.Base):
    def test_delivery_rechecks_live_cues_after_binding_the_frozen_picture(self):
        import argparse
        import subprocess
        cue = self.cue()
        base = f.final.freeze(self.project)
        picture = self.stitched(base)
        real_bind, real_run = f.deliver.bind_stitched, subprocess.run
        def changed(*args, **kwargs):
            result = real_bind(*args, **kwargs)
            cue.write_bytes(b'live sound changed during delivery')
            return result
        def checked(command, **kwargs):
            if len(command) > 1 and str(command[1]).endswith('sound_mix.py'):
                return subprocess.CompletedProcess(command, 0, stdout='', stderr='')
            return real_run(command, **kwargs)
        args = argparse.Namespace(project=str(self.project), base='live-cue', mode='final', picture=None, adopt_picture=False, fps=None, resolution=None, source_swap=[], stitched=str(picture))
        with patch.object(f.deliver, 'ROOT', self.work), patch.object(f.deliver, 'bind_stitched', side_effect=changed), patch.object(subprocess, 'run', side_effect=checked), patch.object(f.sound, 'mix') as mix:
            with self.assertRaisesRegex(ValueError, 'inputs changed after checks'):
                f.deliver.deliver(args)
            mix.assert_not_called()

    def cue(self, data=b"first cue"):
        path = self.project / "assets/sfx/click.wav"
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(data)
        sheet = f.sound.sheet_of(self.project)
        sheet["cues"] = [{"file": "assets/sfx/click.wav", "at": 0.2, "t": 0.2, "gain": 0.1, "event_id": "b1.e1"}]
        f.write(self.project / "sound.json", sheet)
        return path

    def test_new_cue_is_carried_without_changing_old_bundle(self):
        old = f.final.freeze(self.project)
        cue = self.cue()
        new = f.final.freeze(self.project)
        self.assertEqual((f.final.editorial(new) / "assets/sfx/click.wav").read_bytes(), cue.read_bytes())
        self.assertFalse((f.final.editorial(old) / "assets/sfx/click.wav").exists())
        self.assertEqual(f.final.bundle_problems(new), [])

    def test_replaced_cue_changes_identity_and_refuses_old_picture(self):
        cue = self.cue()
        old = f.final.freeze(self.project)
        picture = self.stitched(old)
        cue.write_bytes(b"replacement cue")
        self.refused("old sound", f.final.accept, self.project, picture)
        new = f.final.freeze(self.project)
        self.assertNotEqual(old, new)
        self.assertEqual((f.final.editorial(old) / "assets/sfx/click.wav").read_bytes(), b"first cue")
        self.assertEqual((f.final.editorial(new) / "assets/sfx/click.wav").read_bytes(), b"replacement cue")

    def test_missing_sheet_or_cue_refuses_even_with_existing_bundle(self):
        cue = self.cue()
        f.final.freeze(self.project)
        cue.unlink()
        self.refused("cue", f.final.freeze, self.project)
        (self.project / "sound.json").unlink()
        self.refused("sound.json", f.final.freeze, self.project)

    def test_clicked_waiver_after_freeze_makes_immutable_revision(self):
        old = f.final.freeze(self.project)
        # Simulate the file written by the click route; never write a real project waiver.
        f.write(self.home / "waivers.json", [{"check": "O4.double_cut", "frames": [1, 2], "why": "test click"}])
        new = f.final.freeze(self.project)
        self.assertNotEqual(new, old)
        self.assertFalse((old / "waivers.json").exists())
        self.assertEqual(f.final.home_rows(new), f.final.home_rows(self.home))
        self.assertEqual(f.final.bundle_problems(new), [])

    def test_derivative_prints_and_records_helper_gaps_at_its_own_rate(self):
        import contextlib
        import io
        timeline = self.project / 'tools_local/timeline.js'
        timeline.write_text(f.TIMELINE + 'show("#a", 57.567); cutIn("#a", 57.567, 59);', encoding='utf8')
        f.final.rebuild(self.project)
        f.sound.rebind(self.project, 'test timeline')
        base = f.final.freeze(self.project)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            new = f.final.derive(base, '4k60')
        self.assertIn('FRAME GAP: show("#a", 57.567)', out.getvalue())
        self.assertEqual(f.store.read_json(new / f.final.DERIVATIVE)['frame_gaps'], [{'selector': '"#a"', 'show_time': '57.567', 'fps': 60}])


@unittest.skipUnless((f.TOOLS.parent / 'work/beat-fixture/v2/editorial/beats.lock.json').is_file(), "needs work/beat-fixture, the author's 107 s test edit, which does not ship")
class SourceGrid(unittest.TestCase):
    def test_page_grid_is_checked_as_well_as_the_lock(self):
        base = {'duration': 46, 'runs': [[0, 45.417, 'split'], [45.417, 46, 'full-face']], 'windows': [['a', 0, 45.417]]}
        with self.assertRaisesRegex(f.final.Refused, 'source grid'):
            f.final.check_timing(base, base, 30, 60)
        from common import source_frame_time
        cut = source_frame_time(45.417)
        new = {'duration': 46, 'runs': [[0, cut, 'split'], [cut, 46, 'full-face']], 'windows': [['a', 0, cut]]}
        self.assertEqual(f.final.check_timing(base, new, 30, 60), {'runs': 2, 'windows': 1})

    def test_legacy_derivative_moves_real_face_tags_and_layout_runs_together(self):
        import ast
        import math
        import tempfile
        from types import SimpleNamespace
        from common import source_frame_time
        fixture = f.TOOLS.parent / "work/beat-fixture/v2/editorial"
        plan = json.loads((fixture / "plan.json").read_text(encoding="utf8"))
        duration = f.beat_lock.load(fixture)["duration"]
        with tempfile.TemporaryDirectory() as tmp:
            ed = Path(tmp)
            (ed / 'tools_local').mkdir()
            for name in ('build.py', 'scenes.py', 'timeline.js'):
                (ed / 'tools_local' / name).write_bytes((fixture / 'tools_local' / name).read_bytes())
            scene_bytes = (ed / 'tools_local/scenes.py').read_bytes()
            f.final.edit_sources(ed, 60)
            self.assertEqual((ed / 'tools_local/scenes.py').read_bytes(), scene_bytes, 'scene clips keep their source grid')
            tree = ast.parse((ed / 'tools_local/build.py').read_text(encoding='utf8'))
            nodes = [n for n in tree.body if (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ('runs', 'face_vids', 'tables') for t in n.targets)) or (isinstance(n, ast.For) and ast.unparse(n.iter) == "plan['beats']")]
            owners = ast.parse((fixture / 'tools_local/owners.py').read_text(encoding='utf8'))
            windows = next(ast.literal_eval(n.value) for n in owners.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'WINDOWS' for t in n.targets))
            env = {'plan': plan, 'END': duration, 'FPS': 60, 'math': math, 'frame_of': f.frame_of, 'source_frame_time': source_frame_time, 'owners': SimpleNamespace(WINDOWS=windows, HUD=[]), 'caps': []}
            exec(compile(ast.Module(body=nodes, type_ignores=[]), '<real ivory face and layout grid>', 'exec'), env)
        old_runs = plan['computed_stats']['layout_runs']
        for old, new in zip(old_runs, env['runs']):
            self.assertEqual(f.frame_of(new[0], 60), 2 * f.frame_of(old[0], 30))
        for old, new in zip(windows, env['tables']['WINDOWS']):
            self.assertEqual(new, [old[0], source_frame_time(old[1]), source_frame_time(old[2])])
        tags = {f.sound.attrs(tag)['id']: f.sound.attrs(tag) for tag in env['face_vids']}
        for beat, frame in (('b24', 2726), ('b32', 3680)):
            self.assertEqual(math.ceil(float(tags['ff-' + beat]['data-start']) * 60 - 1e-6), frame)
            self.assertAlmostEqual(float(tags['ff-' + beat]['data-media-start']), math.ceil(frame / 60 * 1e4) / 1e4)

    def test_final_beat_starts_are_review_frames_times_two(self):
        fixture = f.TOOLS.parent / "work/beat-fixture/v2/editorial"
        plan = json.loads((fixture / "plan.json").read_text(encoding="utf8"))
        old = f.beat_lock.load(fixture)
        new = f.beat_lock.derive(plan, old["duration"], 60)
        self.assertEqual([b["start_frame"] for b in new["beats"]], [2 * b["start_frame"] for b in old["beats"]])
        self.assertEqual(new["beats"][23]["start_frame"], 2726)
        self.assertEqual(new["beats"][31]["start_frame"], 3680)

    def test_review_lock_and_all_segment_keys_stay_identical(self):
        fixture = f.TOOLS.parent / "work/beat-fixture/v2/editorial"
        old = f.beat_lock.load(fixture)
        plan = json.loads((fixture / "plan.json").read_text(encoding="utf8"))
        new = f.beat_lock.derive(plan, old["duration"], 30)
        self.assertEqual((fixture / "beats.lock.json").read_bytes(), (json.dumps(new, indent=1, ensure_ascii=False) + "\n").encode())
        m = f.ownership.load(fixture)
        root = f.store.root_of(fixture)
        entry = f.store.latest(root, 'review')
        stitched = f.store.read_json(root / 'stitched' / entry['stitched'] / 'stitch.json')
        self.assertEqual(m['composition_rev'], stitched['composition_rev'])
        ph, engine = stitched['profile_hash'], stitched['engine_hash']
        self.assertEqual(ph, f.sha(f.final.complete_profile('review')))
        published = {b['beat_id']: b['key'] for b in stitched['beats']}
        for a, b in zip(old["beats"], new["beats"]):
            self.assertEqual(f.ownership.input_key(a, old, m, ph, engine), f.ownership.input_key(b, new, m, ph, engine))
            self.assertEqual(f.ownership.input_key(b, new, m, ph, engine), published[b['beat_id']])

    def test_frame_map_refuses_an_early_layout_cut(self):
        plan = {"beats": [{"id": "a", "start": 0, "end": 45.417, "layout": "split"}, {"id": "b", "start": 45.417, "end": 46, "layout": "full-face"}]}
        old = f.beat_lock.derive(plan, 46, 30)
        new = f.beat_lock.derive(plan, 46, 60)
        new["beats"][0]["end_frame"] = new["beats"][1]["start_frame"] = 2725
        with self.assertRaises(f.final.Refused):
            f.final.frame_map(old, new)


class FramePairs(unittest.TestCase):
    def gaps(self, code, fps=60):
        import confine
        return confine.frame_gaps(code, fps)

    def test_show_plus_helpers_and_mixed_quotes(self):
        for helper in ('on', 'rise', 'pop', 'word', 'cutIn'):
            with self.subTest(helper=helper):
                self.assertIn(('"#a"', '57.567'), self.gaps(f'show("#a", 57.567); {helper}(\'#a\', 57.567, 59);'))

    def test_child_selector_and_later_time(self):
        self.assertIn(('"#a"', '2.32'), self.gaps('show("#a", 2.32); tl.fromTo("#a .child", {}, {x: 1}, 2.36);'))

    def test_raw_set_and_tween_pair(self):
        self.assertIn(('"#a"', '2.32'), self.gaps('tl.set("#a", {opacity: 1}, A(2.32)); tl.to("#a", {x: 1}, 2.32);'))

    def test_project_helper_parameters_are_checked(self):
        self.assertTrue(self.gaps('function arrive(sel, t) { show(sel, t); tl.fromTo(sel, {}, {x: 1}, t); } arrive("#a", 2.32);'))

    def test_fixed_cut_in_uses_the_same_frame_at_both_rates(self):
        code = 'const fIn = (t) => Math.ceil((t - 0.004) * FPS - 1e-6) / FPS; show("#a", 57.567); cutIn("#a", 57.567, 59);'
        for fps in (30, 60):
            self.assertEqual(self.gaps(code, fps), [])


class BuildCleanup(unittest.TestCase):
    def test_cli_reports_plain_value_error_as_a_refusal(self):
        import contextlib
        import io
        with patch.object(f.final, 'build', side_effect=ValueError('cue event moved')), contextlib.redirect_stdout(io.StringIO()) as out:
            code = f.final.main(['build', 'unused', '--spec', '1080p30', '--workers', '1'])
        self.assertEqual(code, 2)
        self.assertIn('REFUSED: cue event moved', out.getvalue())

    def test_every_exception_removes_the_partial_copy(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'bundle'
            for error in (ValueError('cue moved'), OSError('disk full'), KeyboardInterrupt()):
                with self.subTest(error=type(error).__name__), self.assertRaises(type(error)):
                    with f.final.building(target) as work:
                        work.mkdir()
                        (work / 'asset').write_bytes(b'partial')
                        raise error
                self.assertFalse(target.with_name('bundle.building').exists())


class QualificationSources(unittest.TestCase):
    def test_widen_labels_reused_and_unknown_sources_honestly(self):
        import argparse
        import tempfile
        import qualify_approval
        numbers = dict.fromkeys(('frames_compared', 'identical', 'worst_psnr', 'worst_block', 'worst_fine', 'worst_chroma', 'worst_frame'), 1)
        with tempfile.TemporaryDirectory() as tmp:
            for reused in (True, False, None):
                path = Path(tmp) / 'compare.json'
                f.write(path, {**numbers, 'render': {'reused_fresh': reused, 'fresh_file_sha256': 'hash'}})
                doc = {'clean_pairs': {}, 'clean_worst': dict.fromkeys(r.approval.METRICS, 1)}
                with patch.object(r.approval, 'EVIDENCE', Path(tmp) / 'evidence.json'), patch.object(qualify_approval, 'write_limits') as write_limits:
                    f.write(r.approval.EVIDENCE, doc)
                    qualify_approval.widen(argparse.Namespace(compare=[str(path)]))
                row = write_limits.call_args.args[0]['clean_pairs'][str(path)]
                self.assertEqual(row['reused_fresh'], reused)
                self.assertEqual(row['render']['fresh_file_sha256'], 'hash')
                self.assertIn('unknown' if reused is None else 'reused' if reused else 'whole fresh', row['from'])


class FrozenNotes(r.Base):
    def note(self):
        picture = self.p.picture()
        return r.review.add_note(self.project, {"text": "make this clearer", "scope": "video", "picture_sha": picture})["id"]

    def test_frozen_note_holds_after_picture_moves_and_second_freeze_keeps_set(self):
        note = self.note()
        frozen = r.review.freeze(self.project)
        self.p.build("v2")
        self.p.picture()
        self.assertEqual([n["id"] for n in r.review.open_notes(self.project, self.p.root, r.review.picture(self.project))], [note])
        self.assertEqual(r.review.freeze(self.project)["notes_rev"], frozen["notes_rev"])
        r.review.close_round(self.project, done=[note])
        self.assertEqual(r.review.open_notes(self.project, self.p.root, r.review.picture(self.project)), [])

    def test_not_done_clears_existing_approval(self):
        note = self.note()
        r.review.freeze(self.project)
        self.p.build("v2")
        picture = self.p.picture()
        r.store.write_json(self.p.root / "approvals/active.json", {"file_sha256": picture})
        r.review.close_round(self.project, not_done={note: "needs another pass"})
        self.assertFalse((self.p.root / "approvals/active.json").exists())

    def test_no_freeze_refuses_stray_ids_even_when_picture_matches_head(self):
        self.p.picture()
        r.review.close_round(self.project)
        for kwargs in ({"done": ["stray"]}, {"not_done": {"stray": "why"}}):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(ValueError, "frozen notes"):
                r.review.close_round(self.project, **kwargs)

    def test_adopt_flagged_note_keeps_its_id(self):
        note = self.note()
        r.review.close_round(self.project)
        self.p.build("v2")
        self.p.picture()
        r.review.close_round(self.project)
        self.assertEqual([n["id"] for n in r.review.freeze(self.project)["flagged"]], [note])
        adopted = r.review.freeze(self.project, adopt=[note])
        self.assertEqual([n["id"] for n in adopted["notes"]], [note])
        r.review.close_round(self.project, done=[note])
        self.assertEqual(r.review.open_notes(self.project, self.p.root, r.review.picture(self.project)), [])

    def test_final_gate_refuses_a_frozen_note_even_with_a_stale_active_approval(self):
        self.note()
        r.review.freeze(self.project)
        self.p.build('v2')
        picture = self.p.picture()
        r.store.write_json(self.p.root / 'approvals/active.json', {'file_sha256': picture})
        with self.assertRaisesRegex(f.final.Refused, 'notes still open'):
            f.final.approval_of(self.project, self.p.map['composition_rev'], 'lock1')

    def test_adopted_undone_note_left_not_done_stays_open(self):
        note = self.note()
        r.review.freeze(self.project)
        self.p.build('v2')
        self.p.picture()
        r.review.close_round(self.project, done=[note])
        r.review.go_back(self.project, 0)
        r.review.freeze(self.project, adopt=[note])
        r.review.close_round(self.project, not_done={note: 'needs another pass'})
        self.assertEqual([n['id'] for n in r.review.open_notes(self.project, self.p.root, r.review.picture(self.project))], [note])


class OutputWaivers(r.Waivers):
    def test_sample_without_a_picture_identity_is_not_a_global_waiver(self):
        w = {'check': 'O5.sample', 'frames': [4]}
        self.assertIsNone(r.output.waiver_for('O5.sample', [4], [w], {}, {'file_sha256': 'render'}))

    def test_sample_does_not_cross_renders_even_when_segment_keys_match(self):
        w = {"check": "O5.sample", "frames": [4], "keys": {"b27": "k"}, "picture_sha": "old", "composition_rev": "same", "profile": "review"}
        for key, profile in (("k", "review"), ("new", "final")):
            self.assertIsNone(r.output.waiver_for("O5.sample", [4], [w], {"b27": key}, {"file_sha256": "new", "composition_rev": "same", "profile": profile}))

    def test_clip_waiver_changes_output_status(self):
        report = self.report()
        report["checks"]["O4"]["flash"] = {"status": "PASS", "flashes": [], "double_cuts": []}
        report["checks"]["O5"].update(status="FAIL", clip_suspects_uncleared=[4])
        r.output.apply_waivers(report, [{"check": "O5.clip", "frames": [4], "why": "looked", "source": "test"}], self.record())
        self.assertEqual(report["checks"]["O5"]["status"], "PASS")
        self.assertEqual(report["waived"][0]["check"], "O5.clip")

    def test_scan_keeps_all_fourteen_findings_for_clicks(self):
        rows = [{"frames": [2 * i, 2 * i + 1], "diffs": [30, 30]} for i in range(14)]
        def scan(args, **kwargs):
            Path(args[args.index("--json") + 1]).write_text(json.dumps({"verdict": "FAIL", "flashes": [], "double_cuts": rows, "unexpected": []}))
            return type("Result", (), {"returncode": 1})()
        with patch.object(r.output.subprocess, "run", side_effect=scan), patch.object(r.output, "expected_cuts", return_value=[]):
            flash = r.output.flash("test.mp4", {"fps": 60}, {}, 1080)
        self.assertEqual(len(flash["double_cuts"]), 14)
        report = self.report()
        report["checks"]["O4"]["flash"] = flash
        waivers = [{"check": "O4.double_cut", "frames": row["frames"], "why": "looked", "source": "test"} for row in rows[:12]]
        r.output.apply_waivers(report, waivers, self.record())
        self.assertEqual(report["checks"]["O4"]["status"], "FAIL")
        self.assertEqual(report["checks"]["O4"]["flash"]["double_cuts"], rows[12:])


if __name__ == "__main__":
    unittest.main()
