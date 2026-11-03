"""Phase 1 sound exit tests. ffmpeg is real; only HyperFrames is stubbed."""
import argparse, contextlib, io, json, re, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import sound_mix as sound
import deliver


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True, capture_output=True)


def write(path, value):
    Path(path).write_text(json.dumps(value), encoding="utf8")


class SoundStep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = tempfile.TemporaryDirectory()
        cls.media = Path(cls.fixture.name)
        ff("-f", "lavfi", "-i", "testsrc2=size=1080x1920:rate=10:duration=2.4", "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "35", cls.media / "picture.mp4")
        ff("-f", "lavfi", "-i", "sine=frequency=400:sample_rate=48000:duration=2.4", "-ac", "2", "-c:a", "aac", cls.media / "voice.m4a")
        ff("-i", cls.media / "picture.mp4", "-i", cls.media / "voice.m4a", "-c:v", "copy", "-af", "volume=6", "-c:a", "aac", cls.media / "render-with-audio.mp4")
        ff("-f", "lavfi", "-i", "sine=frequency=1200:sample_rate=48000:duration=0.15", "-ac", "2", cls.media / "cue.wav")

    @classmethod
    def tearDownClass(cls):
        cls.fixture.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.project = self.root / "project"
        (self.project / "assets" / "sfx").mkdir(parents=True)
        (self.project / "renders").mkdir()
        self.picture = self.project / "picture.mp4"
        shutil.copyfile(self.media / "picture.mp4", self.picture)
        shutil.copyfile(self.media / "picture.mp4", self.project / "assets" / "clip.mp4")
        shutil.copyfile(self.media / "voice.m4a", self.project / "assets" / "voice.m4a")
        for name in sound.palette()["sounds"]:
            shutil.copyfile(self.media / "cue.wav", self.project / "assets" / "sfx" / (name + ".wav"))
        self.html = '<div data-duration="2.4"><video src="assets/clip.mp4"></video>\n<audio id="voice" src="assets/voice.m4a"></audio>\n</div>'
        (self.project / "index.html").write_text(self.html, encoding="utf8")
        self.plan = {"duration": 2.4, "cta_start": 2.2, "beats": [{"id": "b1", "start": 0, "end": 2.4, "layout": "split",
                     "anchor": {"event_id": "b1.e1", "t": 0.4, "description": "card lands"},
                     "actions": [{"event_id": "b1.e2", "t": 1.7, "description": "row lands"}]}]}
        self.save_plan()
        self.sheet = {"version": 1, "picture_rev": sound.picture_rev(self.project), "cues": [], "empty_reason": "Nothing earns a cue."}
        self.save_sheet()
        self.addCleanup(patch.stopall)
        patch.object(deliver, "ROOT", self.root).start()

    def save_plan(self, refresh=False):
        write(self.project / "plan.json", self.plan)
        if refresh:
            self.sheet["picture_rev"] = sound.picture_rev(self.project)
            self.save_sheet()

    def save_sheet(self):
        write(self.project / "sound.json", self.sheet)

    def cue(self, name="pop-hero", t=0.4, eid="b1.e1", **kwargs):
        return {"t": t, "at": t, "gain": 0.1, "dur": 0.15, "media_start": 0,
                "file": f"assets/sfx/{name}.wav", "event": "card lands", "stressed_word": None,
                "placement": "attack on event", "event_id": eid, **kwargs}

    def capture(self, fn, *args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            result = fn(*args)
        return result, buf.getvalue()

    def args(self, base="test", mode="final", picture=None, adopt=False, **kwargs):
        return argparse.Namespace(project=str(self.project), base=base, mode=mode, picture=picture,
                                  adopt_picture=adopt, fps=None, resolution=None, source_swap=[], **kwargs)

    def stub_hyperframes(self, command, **kwargs):
        if "hyperframes" in command and "render" in command:  # npx or node npx-cli.js, as doctor.npm_command builds it
            self.hf_calls.append(command)
            shutil.copyfile(self.picture, self.project / command[command.index("-o") + 1])
            return subprocess.CompletedProcess(command, 0)
        return self.real_run(command, **kwargs)

    def enable_render_stub(self):
        self.hf_calls = []
        self.real_run = deliver.run
        patch.object(deliver, "run", side_effect=self.stub_hyperframes).start()

    def bind(self, base="approved"):
        return deliver.bind_picture(self.project, self.picture, base, sound.picture_rev(self.project))

    def test_stale_blocks_final_before_render(self):
        self.plan["beats"][0]["anchor"]["t"] = 0.8
        self.save_plan()
        with patch.object(deliver, "render") as render:
            with self.assertRaisesRegex(ValueError, "stale"):
                deliver.deliver(self.args())
            render.assert_not_called()

    def test_picture_preview_on_stale_edit_is_voice_only(self):
        self.sheet["cues"] = [self.cue(gain=30)]
        self.save_sheet()
        before = (self.project / "sound.json").read_bytes()
        self.plan["beats"][0]["anchor"]["description"] = "new picture"
        self.save_plan()
        self.enable_render_stub()
        shutil.copyfile(self.media / "render-with-audio.mp4", self.picture)
        self.assertEqual(deliver.deliver(self.args(mode="picture-preview")), 0)
        self.assertEqual(len(self.hf_calls), 1)
        self.assertEqual((self.project / "sound.json").read_bytes(), before)
        expected = self.root / "voice.wav"
        sound.mix(self.project, str(expected), voice_only=True)
        np.testing.assert_array_equal(sound.decode(expected), sound.decode(self.project / "renders" / "test.mix.wav"))
        np.testing.assert_array_equal(sound.decode(expected), sound.decode(self.project / "renders" / "test.mux.mov"))
        m = json.loads((self.root / "out" / "test-delivery.json").read_text())
        self.assertIsNone(m["sound_sheet_sha256"])
        self.assertEqual(m["status"], "PASS")

    def test_empty_sheet_final_and_media_checks(self):
        self.enable_render_stub()
        self.assertEqual(deliver.deliver(self.args()), 0)
        self.assertEqual(len(self.hf_calls), 1)
        output = self.root / "out" / "test.mp4"
        self.assertEqual(sound.check_media(output), 0)
        manifest = self.root / "out" / "test-delivery.json"
        m = json.loads(manifest.read_text())
        self.assertEqual(set(m["checks"]), {"check-sheet", "check-mix", "check-media", "gates"})
        m["duration"] = 6
        write(manifest, m)
        rc, text = self.capture(sound.check_media, output)
        self.assertEqual(rc, 1)
        self.assertIn("FAIL duration", text)

    def test_empty_final_needs_reason(self):
        self.sheet.pop("empty_reason")
        self.save_sheet()
        with self.assertRaisesRegex(ValueError, "empty_reason"):
            deliver.deliver(self.args())

    def test_missing_sheet_refused_even_with_legacy_plan(self):
        (self.project / "sound.json").unlink()
        self.plan["sfx_timeline"] = []
        self.save_plan()
        with self.assertRaisesRegex(ValueError, "requires sound.json"):
            deliver.deliver(self.args())

    def test_swapped_clip_same_path_goes_stale(self):
        before = sound.picture_rev(self.project)
        (self.project / "assets" / "clip.mp4").write_bytes(b"replacement")
        self.assertNotEqual(sound.picture_rev(self.project), before)
        self.assertEqual(self.capture(sound.stale, self.project)[0], 1)
        with self.assertRaisesRegex(ValueError, "stale"):
            deliver.deliver(self.args())

    def test_voice_and_plan_only_media_go_stale(self):
        self.plan["plate"] = "assets/plan-only.png"
        (self.project / "assets" / "plan-only.png").write_bytes(b"plate")
        self.save_plan(refresh=True)
        before = sound.picture_rev(self.project)
        (self.project / "assets" / "plan-only.png").write_bytes(b"new plate")
        self.assertNotEqual(sound.picture_rev(self.project), before)
        before = sound.picture_rev(self.project)
        with open(self.project / "assets" / "voice.m4a", "ab") as f:
            f.write(b"changed voice")
        self.assertNotEqual(sound.picture_rev(self.project), before)

    def test_stale_picture_refused_even_with_current_sheet(self):
        self.bind()
        self.plan["beats"][0]["anchor"]["description"] = "changed picture"
        self.save_plan(refresh=True)
        with patch.object(deliver, "render") as render:
            with self.assertRaisesRegex(ValueError, "no matching render manifest"):
                deliver.deliver(self.args(picture=str(self.picture)))
            render.assert_not_called()

    def test_unbound_and_replaced_picture_refused(self):
        with self.assertRaisesRegex(ValueError, "no matching render manifest"):
            deliver.reuse_picture(self.project, self.picture, sound.picture_rev(self.project))
        self.bind()
        with open(self.picture, "ab") as f:
            f.write(b"new render bytes")
        with self.assertRaisesRegex(ValueError, "no matching render manifest"):
            deliver.reuse_picture(self.project, self.picture, sound.picture_rev(self.project))

    def test_sound_only_delivery_never_calls_hyperframes(self):
        self.bind()
        self.sheet["cues"] = [self.cue()]
        self.save_sheet()
        _, measured = self.capture(sound.check_mix, self.project)
        under = float(re.search(r"cue track ([\d.-]+) LU", measured)[1])
        self.sheet["cues"][0]["gain"] *= 10 ** ((under - 22) / 20)
        self.save_sheet()
        with patch.object(deliver, "render", side_effect=AssertionError("HyperFrames called")) as render:
            self.assertEqual(deliver.deliver(self.args(picture=str(self.picture))), 0)
            render.assert_not_called()

    def test_existing_output_is_never_overwritten(self):
        (self.root / "out").mkdir()
        existing = self.root / "out" / "test.mp4"
        existing.write_bytes(b"keep this output")
        with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
            deliver.deliver(self.args())
        self.assertEqual(existing.read_bytes(), b"keep this output")

    def test_cue_bytes_changed_after_checks_stop_before_mixing(self):
        self.sheet["cues"] = [self.cue()]
        self.save_sheet()
        self.bind()
        real_reuse = deliver.reuse_picture
        def changed(*args, **kwargs):
            result = real_reuse(*args, **kwargs)
            (self.project / self.sheet["cues"][0]["file"]).write_bytes(b"changed after checks")
            return result
        real_run = subprocess.run
        def checked(command, **kwargs):
            if len(command) > 1 and str(command[1]).endswith('sound_mix.py'):
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
            return real_run(command, **kwargs)
        # Changing the cue happens after both sound checks have returned.
        with patch.object(deliver.subprocess, "run", side_effect=checked), patch.object(deliver, "reuse_picture", side_effect=changed), patch.object(sound, "mix") as mix:
            with self.assertRaisesRegex(ValueError, "inputs changed after checks"):
                deliver.deliver(self.args(picture=str(self.picture)))
            mix.assert_not_called()

    def test_cue_identity_names_every_file_and_refuses_missing_media(self):
        self.sheet["cues"] = [self.cue()]
        self.save_sheet()
        identity = sound.sound_identity(self.project)
        cue = self.project / self.sheet["cues"][0]["file"]
        self.assertEqual(identity["cue_files"], {self.sheet["cues"][0]["file"]: sound.file_hash(cue)})
        cue.unlink()
        with self.assertRaisesRegex(ValueError, "missing cue media"):
            sound.sound_identity(self.project)

    def test_reused_picture_must_match_requested_fps_and_resolution(self):
        self.bind()
        for kwargs, expected in (({"fps": 60}, "fps"), ({"resolution": "portrait-4k"}, "dimensions")):
            with self.subTest(kwargs=kwargs):
                with self.assertRaisesRegex(ValueError, expected):
                    deliver.reuse_picture(self.project, self.picture, sound.picture_rev(self.project), **kwargs)

    def test_adopt_picture_warns_and_writes_binding_without_render(self):
        with patch.object(deliver, "render", side_effect=AssertionError("HyperFrames called")) as render:
            rc, text = self.capture(deliver.deliver, self.args(picture=str(self.picture), adopt=True))
            self.assertEqual(rc, 0)
            self.assertIn("human assertion", text)
            render.assert_not_called()
        m = json.loads((self.project / "renders" / "test.render.json").read_text())
        self.assertTrue(m["adopted"])
        self.assertEqual(m["width"], 1080)
        self.assertEqual(m["fps"], 10)

    def test_cues_and_audio_tags_do_not_change_revision(self):
        before = sound.picture_rev(self.project)
        self.sheet["cues"] = [self.cue()]
        self.save_sheet()
        self.plan["sfx_timeline"] = [self.cue()]
        self.save_plan()
        self.assertEqual(sound.picture_rev(self.project), before)
        text = self.html.replace("</div>", '  <audio id="sfx-1" src="assets/sfx/pop.wav" data-start="0.2"></audio> <!-- event -->\n</div>')
        (self.project / "index.html").write_text(text, encoding="utf8")
        self.assertEqual(sound.picture_rev(self.project), before)
        text = text.replace('sfx/pop.wav', 'sfx/click.wav').replace('start="0.2"', 'start="1.8"')
        (self.project / "index.html").write_text(text, encoding="utf8")
        self.assertEqual(sound.picture_rev(self.project), before)
        (self.project / "assets" / "sfx" / "click.wav").write_bytes(b"new sound")
        self.assertEqual(sound.picture_rev(self.project), before)

    def test_zero_cues_mix_graph_and_check_alias(self):
        args, graph = sound.cue_graph([], self.project)
        silent = self.root / "silence.wav"
        ff(*args, "-filter_complex", graph, "-map", "[m]", "-t", "0.2", silent)
        self.assertFalse(np.any(sound.decode(silent)))
        mixed = self.root / "mixed.wav"
        sound.mix(self.project, str(mixed))
        self.assertGreater(len(sound.decode(mixed)), 0)
        rc, text = self.capture(sound.check, self.project)
        self.assertEqual(rc, 0, text)
        self.assertIn("no cue track", text)

    def test_old_plan_fallback_and_migration_match_samples(self):
        (self.project / "sound.json").unlink()
        c = self.cue()
        c.pop("event_id")
        self.plan["sfx_timeline"] = [c]
        self.save_plan()
        before = self.root / "before.wav"
        sound.mix(self.project, str(before))
        rc, text = self.capture(sound.check_sheet, self.project)
        self.assertEqual(rc, 0, text)
        self.assertIn("old plan fallback", text)
        self.assertIn("legacy.0.4", text)
        original_plan = (self.project / "plan.json").read_bytes()
        sound.migrate(self.project)
        after = self.root / "after.wav"
        sound.mix(self.project, str(after))
        np.testing.assert_array_equal(sound.decode(before), sound.decode(after))
        self.assertEqual((self.project / "plan.json").read_bytes(), original_plan)
        self.assertEqual(sound.sheet_of(self.project)["cues"][0]["event_id"], "legacy.0.4")
        with self.assertRaisesRegex(ValueError, "already exists"):
            sound.migrate(self.project)

    def test_each_sheet_failure(self):
        cases = [
            ("palette", [self.cue(file="assets/sfx/alien.wav")], "not in sfx.json"),
            ("special", [self.cue("deep-hit")], "needs requested_by"),
            ("event", [self.cue(eid="missing")], "missing from plan.json"),
            ("spacing", [self.cue(), self.cue("click", t=0.7, eid="b1.e2")], "cue spacing"),
            ("repeat", [self.cue(), self.cue(t=1.7, eid="b1.e2")], "back-to-back"),
            ("duplicate event", [self.cue(), self.cue("click", t=1.7)], "more than one cue"),
            ("CTA", [self.cue(t=2.25)], "CTA span"),
            ("CTA tail", [self.cue(t=2.1, at=2.1, dur=0.15)], "CTA span"),
            ("number", [self.cue(gain=float("nan"))], "finite numbers"),
            ("span", [self.cue(dur=-1)], "invalid cue time"),
            ("media start", [self.cue(media_start=3)], "past end"),
        ]
        for name, cues, expected in cases:
            with self.subTest(name=name):
                self.sheet["cues"] = cues
                self.save_sheet()
                rc, text = self.capture(sound.check_sheet, self.project)
                self.assertEqual(rc, 1, text)
                self.assertIn(expected, text)

    def test_share_counts_source_file_not_slice(self):
        self.plan["duration"], self.plan["cta_start"] = 20, 19
        names = ["pop", "click", "pop-soft", "whoosh-a", "pop-hero", "whoosh-b", "bell", "whoosh-c"]
        self.sheet["cues"] = [self.cue(n, t=i*2, eid=f"legacy.{i*2}") for i, n in enumerate(names)]
        self.save_plan(refresh=True)
        rc, text = self.capture(sound.check_sheet, self.project)
        self.assertEqual(rc, 1, text)
        self.assertIn("source-file share Pop 1.wav: 3/8", text)

    def test_proof_overlap_counts_actual_audible_tail(self):
        self.plan["beats"][0]["proof_span"] = [0.5, 0.9]
        self.sheet["cues"] = [self.cue()]
        self.save_plan(refresh=True)
        rc, text = self.capture(sound.check_sheet, self.project)
        self.assertEqual(rc, 1, text)
        self.assertIn("audible span overlaps proof_span", text)

    def test_sheet_revision_and_missing_media_fail(self):
        self.sheet["picture_rev"] = "stale"
        self.sheet["cues"] = [self.cue()]
        self.save_sheet()
        (self.project / "assets" / "sfx" / "pop-hero.wav").unlink()
        rc, text = self.capture(sound.check_sheet, self.project)
        self.assertEqual(rc, 1, text)
        self.assertIn("stale picture_rev", text)
        self.assertIn("missing cue media", text)

    def test_invalid_sheet_schema_and_event_time_fail(self):
        for key, value in (("version", 2), ("cues", {})):
            with self.subTest(key=key):
                before = self.sheet[key]
                self.sheet[key] = value
                self.save_sheet()
                rc, text = self.capture(sound.check_sheet, self.project)
                self.assertEqual(rc, 1, text)
                self.assertIn("requires version 1 and cues array", text)
                self.sheet[key] = before
        self.plan["beats"][0]["anchor"].pop("t")
        self.sheet["cues"] = [self.cue()]
        self.save_plan(refresh=True)
        rc, text = self.capture(sound.check_sheet, self.project)
        self.assertEqual(rc, 1, text)
        self.assertIn("has no time", text)

    def test_special_sound_with_request_passes(self):
        self.sheet["cues"] = [self.cue("deep-hit", requested_by="Chase: use a deep hit on the card")]
        self.save_sheet()
        rc, text = self.capture(sound.check_sheet, self.project)
        self.assertEqual(rc, 0, text)

    def test_bare_css_media_replacement_changes_revision(self):
        (self.project / "plate.png").write_bytes(b"first plate")
        (self.project / "index.html").write_text(self.html + '<style>body {background: url(plate.png)}</style>', encoding="utf8")
        before = sound.picture_rev(self.project)
        (self.project / "plate.png").write_bytes(b"new plate")
        self.assertNotEqual(sound.picture_rev(self.project), before)

    def test_missing_cta_and_tail_to_face_only_warn(self):
        self.plan.pop("cta_start")
        self.plan["beats"].append({"start": 0.5, "layout": "full-face"})
        self.sheet["cues"] = [self.cue()]
        self.save_plan(refresh=True)
        rc, text = self.capture(sound.check_sheet, self.project)
        self.assertEqual(rc, 0, text)
        self.assertIn("CTA span UNVERIFIED", text)
        self.assertIn("audible tail past cut", text)

    def test_stale_lists_moved_event(self):
        self.sheet["cues"] = [self.cue()]
        self.save_sheet()
        self.plan["beats"][0]["anchor"]["t"] = 0.9
        self.save_plan()
        rc, text = self.capture(sound.stale, self.project)
        self.assertEqual(rc, 1)
        self.assertIn("moved event b1.e1: cue 0.400s -> event 0.900s", text)

    def test_mix_level_fails_but_density_only_warns(self):
        self.plan["duration"] = 14
        self.sheet["cues"] = [self.cue(t=0.4+i*1.3, eid=f"legacy.{i}", gain=1) for i in range(9)]
        self.save_plan(refresh=True)
        rc, text = self.capture(sound.check_mix, self.project)
        self.assertEqual(rc, 1, text)
        under = float(re.search(r"cue track ([\d.-]+) LU", text)[1])
        for c in self.sheet["cues"]:
            c["gain"] *= 10 ** ((under - 22) / 20)
        self.save_sheet()
        rc, text = self.capture(sound.check_mix, self.project)
        self.assertEqual(rc, 0, text)
        self.assertIn("WARN 9 cues", text)
        self.assertIn("busiest 30 s: 9 cues", text)

    def test_media_without_audio_and_manifest_fails(self):
        rc, text = self.capture(sound.check_media, self.picture)
        self.assertEqual(rc, 1)
        self.assertIn("FAIL delivered audio stream present", text)
        self.assertIn("missing delivery manifest", text)

    def test_media_loudness_and_peak_failures(self):
        bad = self.root / "bad.mp4"
        ff("-i", self.picture, "-f", "lavfi", "-i", "sine=frequency=400:sample_rate=48000:duration=2.4", "-af", "volume=8", "-c:v", "copy", "-c:a", "aac", bad)
        write(self.root / "bad-delivery.json", {"output_sha256": sound.file_hash(bad), "duration": 2.4, "fps": 10})
        rc, text = self.capture(sound.check_media, bad)
        self.assertEqual(rc, 1, text)
        self.assertIn("FAIL delivered loudness", text)
        self.assertIn("FAIL delivered true peak", text)

    def test_sound_workflow_and_build_contract_stub(self):
        sys.path.insert(0, str(TOOLS / "tests"))
        from test_full_face import dry_run
        prompts = dry_run("sound-cues.js", {"id": "t1", "note": "Keep the card silent"})
        p = prompts["sound-cues"]
        for text in ("sound.md", "sfx.json", "event_id", "check-sheet", "Keep the card silent", "only art direction"):
            self.assertIn(text, p)
        build = dry_run("recut-build.js", {"id": "t1"})
        self.assertIn("immutable event_id", build["direct:editorial"])
        self.assertIn("no cue <audio> tags", build["build:editorial"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
