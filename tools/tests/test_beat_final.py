"""The final path, Workstream E. ffmpeg, the stitch and the checks are real, on a small project of testsrc segments. No browser runs here: the whole renders are in stage1/phase5-final.md."""
import argparse, contextlib, hashlib, io, json, re, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(TOOLS), str(TOOLS / "beat_review"), str(TOOLS / "beat_render"), str(TOOLS / "beat_check")]
import deliver
import final
import lock as beat_lock
import ownership
import sentinel
import sound_mix as sound
import stitch as stitcher
import store
from common import frame_of, sha

BUILD = r'''
import json, math, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ED = HERE.parent
sys.path[:0] = [TOOLS_BEAT_RENDER, TOOLS]
import lock, ownership, sound_mix
from common import frame_of, sha
sys.path.insert(0, str(HERE))
import scenes
FPS = 30
plan = json.loads((ED / "plan.json").read_text(encoding="utf8"))
meta = json.loads((ED.parent.parent / "metadata.json").read_text(encoding="utf8"))
timeline = (HERE / "timeline.js").read_text(encoding="utf8")
beat_lock = lock.write(ED, plan, meta["duration"], FPS)
html = f"""<!doctype html><div id="root" data-composition-id="main" data-duration="{meta['duration']}" data-width="1080" data-height="1920" data-fps="30">
<video id="face" class="clip" src="assets/face.mp4" data-start="{scenes.start(0.5)}" data-duration="1" data-media-start="0"></video>
<img src="assets/card.png">
<script src="assets/mod.js"></script>
<script>{timeline}</script>
<audio id="voice" src="assets/voice.m4a"></audio>
</div>
"""
(ED / "index.html").write_text(html, encoding="utf8", newline="\n")
known = {"assets/face.mp4", "assets/card.png", "assets/mod.js", "assets/only_in_module.png"}
files = {rel: sound_mix.file_hash(ED / rel) for rel in sorted(known)}
authoring = {rel: sound_mix.file_hash(ED / rel) for rel in [*plan["composition_files"], "plan.json"]}
media = [{"id": "face", "src": "assets/face.mp4", "sha256": files["assets/face.mp4"], "data-start": str(scenes.start(0.5)), "data-duration": "1", "data-media-start": "0"}]
timing = {"duration": meta["duration"], "runs": [], "windows": []}
m = {"schema": ownership.SCHEMA, "template": "ivory", "html_sha256": sound_mix.file_hash(ED / "index.html"), "lock_revision": beat_lock["revision"], "fps": FPS, "total_frames": beat_lock["total_frames"],
     "shared": {"shell_hash": sha(html), "timing_hash": sha({**timing, "lock_revision": beat_lock["revision"]}), "media_hash": sha(media), "files_hash": sha({"files": files, "library": []}), "files": files, "library": [], "unused": [], "unconfined": [], "timing": timing, "media": media},
     "ignored": ownership.IGNORED, "owners": [], "chains": []}
m["composition_rev"] = sha(m)
m["authoring"] = authoring
(ED / "ownership.json").write_text(json.dumps(m, indent=1) + "\n", encoding="utf8", newline="\n")
events = [{"event_id": "b1.e1", "beat_id": "b1", "kind": "anchor", "t": 0.2, "frame": frame_of(0.2, FPS)}, {"event_id": "b2.e1", "beat_id": "b2", "kind": "anchor", "t": 0.85, "frame": frame_of(0.85, FPS)}]
(ED / "events.json").write_text(json.dumps({"schema": 1, "composition_rev": m["composition_rev"], "fps": FPS, "events": events}) + "\n", encoding="utf8", newline="\n")
'''
SCENES = '''import math
from common import frame_of
def start(start):
    f0 = frame_of(start, 30)
    return math.floor(f0 / 30 * 1e5) / 1e5
'''
TIMELINE = "const END = 1.6, FPS = 30;\nconst A = (t) => t - 0.004;\n"
MODULE = 'const card = "assets/only_in_module.png";\n'


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True, capture_output=True)


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value), encoding="utf8")


def flip(path, at=20000):
    with open(path, "r+b") as f:
        f.seek(at)
        b = f.read(1)
        f.seek(at)
        f.write(bytes([b[0] ^ 0xFF]))


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shared = tempfile.TemporaryDirectory()
        cls.media = Path(cls.shared.name)
        ff("-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=30:duration=1.6", "-c:v", "libx264", "-preset", "ultrafast", "-g", "15", cls.media / "face.mp4")
        ff("-f", "lavfi", "-i", "testsrc2=size=2560x1440:rate=30:duration=1.6", "-c:v", "libx264", "-preset", "ultrafast", "-g", "15", cls.media / "face_4k.mp4")
        ff("-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=30:duration=1.6", "-vf", "tpad=start=2:start_mode=clone,trim=end_frame=48", "-c:v", "libx264", "-preset", "ultrafast", cls.media / "face_late.mp4")
        ff("-f", "lavfi", "-i", "testsrc2=size=2560x1440:rate=30:duration=1.0", "-c:v", "libx264", "-preset", "ultrafast", cls.media / "face_short.mp4")
        ff("-f", "lavfi", "-i", "sine=frequency=300:sample_rate=48000:duration=1.6", "-ac", "2", "-c:a", "aac", cls.media / "voice.m4a")
        ff("-f", "lavfi", "-i", "color=c=white:s=16x16:d=0.04", "-frames:v", "1", cls.media / "card.png")

    @classmethod
    def tearDownClass(cls):
        cls.shared.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name).resolve() / "work"
        self.home = self.work / "p"
        self.project = self.home / "v2" / "editorial"
        (self.project / "assets").mkdir(parents=True)
        (self.project / "tools_local").mkdir()
        shutil.copy(self.media / "face.mp4", self.project / "assets" / "face.mp4")
        shutil.copy(self.media / "voice.m4a", self.project / "assets" / "voice.m4a")
        shutil.copy(self.media / "card.png", self.project / "assets" / "card.png")
        shutil.copy(self.media / "card.png", self.project / "assets" / "only_in_module.png")
        (self.project / "assets" / "mod.js").write_text(MODULE, encoding="utf8")
        (self.project / "tools_local" / "build.py").write_text(BUILD.replace("TOOLS_BEAT_RENDER", repr(str(TOOLS / "beat_render"))).replace("[" + repr(str(TOOLS / "beat_render")) + ", TOOLS]", "[" + repr(str(TOOLS / "beat_render")) + ", " + repr(str(TOOLS)) + "]"), encoding="utf8")
        (self.project / "tools_local" / "scenes.py").write_text(SCENES, encoding="utf8")
        (self.project / "tools_local" / "timeline.js").write_text(TIMELINE, encoding="utf8")
        self.plan = {"duration": 1.6, "composition_files": ["tools_local/build.py", "tools_local/scenes.py", "tools_local/timeline.js"], "cta_start": 1.5,
                     "beats": [{"id": "b1", "start": 0, "end": 0.85, "layout": "split", "anchor": {"event_id": "b1.e1", "t": 0.2}}, {"id": "b2", "start": 0.85, "end": 1.6, "layout": "split", "anchor": {"event_id": "b2.e1", "t": 0.85}}]}
        write(self.project / "plan.json", self.plan)
        write(self.home / "metadata.json", {"duration": 1.6})
        final.rebuild(self.project)
        self.m, self.lock = final.built(self.project)
        write(self.project / "sound.json", {"version": 1, "picture_rev": sound.picture_rev(self.project), "cues": [], "empty_reason": "Nothing earns a cue."})
        self.root = store.open_store(store.root_of(self.project))
        self.approve()

    def approve(self, composition_rev=None, result="PASS", active=True):
        """A review picture and its record, as Track 1's approve leaves them, with a made-up file hash."""
        rev = composition_rev or self.m["composition_rev"]
        profile = final.complete_profile("review")
        file_sha = hashlib.sha256(rev.encode()).hexdigest()
        store.write_json(self.mkdir(self.root / "stitched" / f"review-{file_sha[:16]}-{rev[:16]}") / "stitch.json", {"file_sha256": file_sha, "profile_hash": sha(profile), "composition_rev": rev})
        store.write_json(self.mkdir(self.root / "approvals") / f"{file_sha[:16]}.json", {"approved_file_sha256": file_sha, "composition_rev": rev, "lock_revision": self.lock["revision"], "profile": profile, "fresh_file_sha256": "f" * 64,
                                                                                         "method": {"how": "test"}, "frames_compared": 48, "worst_psnr": 45.0, "worst_block": 3.0, "result": result, "created": "now"})
        if active:
            store.write_json(self.root / "approvals" / "active.json", {"file_sha256": file_sha, "composition_rev": rev, "lock_revision": self.lock["revision"]})

    @staticmethod
    def mkdir(path):
        path.mkdir(parents=True, exist_ok=True)
        return path

    def stitched(self, home, profile=None):
        """Segments and a stitch in a bundle's own store, as run.py leaves them. testsrc, closed GOPs, no B-frames."""
        ed = final.editorial(home)
        m, lock = final.built(ed)
        root = store.open_store(store.root_of(ed))
        profile = profile or final.complete_profile("final")
        ph = sha(profile)
        engine = "e" * 64
        keys = {}
        offset = 0.0
        for b in lock["beats"]:
            id_ = b["beat_id"]
            key = keys[id_] = ownership.input_key(b, lock, m, ph, engine)
            n = b["end_frame"] - b["start_frame"]
            folder = self.mkdir(store.segment_dir(root, ph, key))
            ff("-f", "lavfi", "-i", f"testsrc2=size={profile['width']}x{profile['height']}:rate={lock['fps']}:duration={n / lock['fps'] + 0.2}", "-frames:v", n, "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30", "-bf", "0", "-g", n, "-pix_fmt", "yuv420p", folder / "segment.mp4")
            rows, _, _ = sentinel.scan(folder / "segment.mp4", profile["width"], profile["height"])
            (folder / "segment.framemd5").write_text("\n".join(rows) + "\n", encoding="utf8", newline="\n")
            video = folder / "segment.mp4"
            store.write_json(folder / "segment.json", {"schema": 1, "beat_id": id_, "start_frame": b["start_frame"], "end_frame": b["end_frame"], "input_key": key, "profile": profile["name"], "profile_hash": ph, "profile_full": profile,
                                                       "file": "segment.mp4", "file_sha256": sound.file_hash(video), "bytes": video.stat().st_size, "decoded": {"frames": n, "content_hash": sha("\n".join(rows))}, "stream": stitcher.probe_video(video)})
        bed = stitcher.audio_bed(ed, root)
        record, folder = stitcher.stitch(root, ed, lock, m, profile, ph, engine, keys, bed)
        return folder / record["file"]

    def refused(self, text, fn, *args, **kwargs):
        with self.assertRaises(ValueError) as e:
            fn(*args, **kwargs)
        self.assertIn(text, str(e.exception))


class ChipGrid(unittest.TestCase):
    def test_a_chip_may_move_only_onto_the_source_grid(self):
        snapped = final.source_frame_time(45.417)
        base = {"events": [{"event_id": "cap.w1", "t": 45.417, "frame": 1363}]}
        final.check_events(base, {"events": [{"event_id": "cap.w1", "t": snapped, "frame": 2726}]}, 2)
        with self.assertRaises(final.Refused):
            final.check_events(base, {"events": [{"event_id": "cap.w1", "t": snapped, "frame": 2725}]}, 2)
        with self.assertRaises(final.Refused):
            final.check_events(base, {"events": [{"event_id": "cap.w1", "t": 45.5, "frame": 2726}]}, 2)

    def test_any_other_event_keeps_its_time(self):
        base = {"events": [{"event_id": "b24.e1", "t": 45.417, "frame": 1363}]}
        with self.assertRaises(final.Refused):
            final.check_events(base, {"events": [{"event_id": "b24.e1", "t": final.source_frame_time(45.417), "frame": 2726}]}, 2)


class PictureRev(Base):
    def rev(self):
        return sound.picture_rev(self.project)

    def test_asset_only_a_module_names_moves_it(self):
        before = self.rev()
        ff("-f", "lavfi", "-i", "color=c=red:s=16x16:d=0.04", "-frames:v", "1", self.project / "assets" / "only_in_module.png")
        self.assertNotEqual(before, self.rev())

    def test_authoring_source_moves_it_even_if_the_plan_lists_nothing(self):
        self.plan.pop("composition_files")
        write(self.project / "plan.json", self.plan)
        before = self.rev()
        (self.project / "tools_local" / "scenes.py").write_text(SCENES + "# edited\n", encoding="utf8")
        self.assertNotEqual(before, self.rev())

    def test_a_module_the_page_loads_moves_it(self):
        before = self.rev()
        (self.project / "assets" / "mod.js").write_text(MODULE + "// edited\n", encoding="utf8")
        self.assertNotEqual(before, self.rev())

    def test_render_profile_and_cues_do_not_move_it(self):
        before = self.rev()
        self.mkdir(self.project / "renders")
        (self.project / "renders" / "x.render.json").write_text("{}", encoding="utf8")
        (self.project / "assets" / "mod.js").write_text(MODULE + '// "assets/sfx/hit.wav"\n', encoding="utf8")
        moved = self.rev()
        self.assertNotEqual(before, moved)  # the module's own text changed
        self.mkdir(self.project / "assets" / "sfx")
        ff("-f", "lavfi", "-i", "sine=frequency=900:duration=0.1", self.project / "assets" / "sfx" / "hit.wav")
        self.assertEqual(moved, self.rev())
        sheet = sound.sheet_of(self.project)
        sheet["cues"] = [{"t": 1, "at": 1, "gain": 0.1, "dur": 0.1, "file": "assets/sfx/hit.wav"}]
        write(self.project / "sound.json", sheet)
        self.assertEqual(moved, self.rev())

    def test_rebind_says_so_and_refuses_a_moved_event(self):
        sheet = sound.sheet_of(self.project)
        sheet["cues"] = [{"t": 0.2, "at": 0.2, "gain": 0.1, "dur": 0.1, "file": "x.wav", "event_id": "b1.e1"}]
        write(self.project / "sound.json", sheet)
        (self.project / "tools_local" / "scenes.py").write_text(SCENES + "# edited\n", encoding="utf8")
        self.refused("needs a reason", sound.rebind, self.project, " ")
        new = sound.rebind(self.project, "test")
        self.assertEqual(new, self.rev())
        self.assertEqual(sound.sheet_of(self.project)["rebound"][0]["to"], new)
        sheet = sound.sheet_of(self.project)
        sheet["cues"][0]["t"] = 0.4
        write(self.project / "sound.json", sheet)
        self.refused("moved", sound.rebind, self.project, "test")

    def test_rebind_against_the_approved_events_keeps_an_approved_offset(self):
        sheet = sound.sheet_of(self.project)
        sheet["cues"] = [{"t": 0.207, "at": 0.207, "gain": 0.1, "dur": 0.1, "file": "x.wav", "event_id": "b1.e1"}]  # 7 ms off its event
        write(self.project / "sound.json", sheet)
        events = sound.events_of(sound.plan_of(self.project))
        self.refused("moved", sound.rebind, self.project, "test")
        self.assertEqual(sound.rebind(self.project, "test", events), self.rev())
        self.refused("moved", sound.rebind, self.project, "test", {**events, "b1.e1": events["b1.e1"] + 0.1})


class Bundle(Base):
    def test_freeze_is_complete_and_rebuilds(self):
        home = final.freeze(self.project)
        self.assertEqual(final.bundle_problems(home), [])
        ed = final.editorial(home)
        self.assertEqual(ownership.load(ed)["composition_rev"], self.m["composition_rev"])
        self.assertEqual(sound.picture_rev(ed), sound.picture_rev(self.project))
        self.assertTrue((ed / "tools_local" / "build.py").is_file())
        self.assertTrue((home / "metadata.json").is_file())
        self.assertFalse(final.bundle_problems(home))

    def test_freeze_refuses_sources_that_do_not_make_this_html(self):
        (self.project / "index.html").write_text((self.project / "index.html").read_text(encoding="utf8") + "<!-- by hand -->", encoding="utf8")
        m = json.loads((self.project / "ownership.json").read_text(encoding="utf8"))
        m["html_sha256"] = sound.file_hash(self.project / "index.html")
        body = {k: v for k, v in m.items() if k not in ("composition_rev", "authoring")}
        m["composition_rev"] = sha(body)
        write(self.project / "ownership.json", m)
        self.refused("do not rebuild", final.freeze, self.project)

    def test_a_changed_file_is_a_problem(self):
        home = final.freeze(self.project)
        shutil.copy(self.media / "face_4k.mp4", final.editorial(home) / "assets" / "face.mp4")
        self.assertIn("assets/face.mp4: differs from the frozen bundle", final.bundle_problems(home))

    def test_a_changed_waiver_list_is_a_problem(self):
        write(self.home / "waivers.json", [{"check": "O4.double_cut", "frames": [1, 2], "why": "x"}])
        home = final.freeze(self.project)
        self.assertEqual(final.bundle_problems(home), [])
        write(home / "waivers.json", [])
        self.assertEqual(final.bundle_problems(home), ["waivers.json: differs from the frozen bundle"])
        (home / "waivers.json").unlink()
        self.assertEqual(final.bundle_problems(home), ["waivers.json: differs from the frozen bundle"])

    def test_an_added_file_is_a_problem(self):
        home = final.freeze(self.project)
        (final.editorial(home) / "assets" / "new.png").write_bytes(b"x")
        self.assertTrue(final.bundle_problems(home))


class FrameGap(unittest.TestCase):
    """The pair behind frame 139 of the 4K60: a show and its tween on two times."""

    def gaps(self, code):
        import confine
        return confine.frame_gaps(code)

    def test_a_show_and_a_tween_at_plain_t_is_flagged_when_a_60_fps_frame_falls_between(self):
        self.assertEqual(self.gaps('show("#a", 2.32);\ntl.fromTo("#a", { x: 0 }, { x: 1, duration: 1 }, 2.32);'), [('"#a"', "2.32")])

    def test_the_same_pair_with_no_frame_between_is_not(self):
        self.assertEqual(self.gaps('show("#a", 2.5);\ntl.to("#a", { x: 1, duration: 1 }, 2.5);'), [], "the 60 fps frame at 2.5 is at the tween's time")

    def test_a_tween_on_a_shared_time_is_not(self):
        self.assertEqual(self.gaps('show("#a", 2.32);\ntl.fromTo("#a", { x: 0 }, { x: 1, duration: 1 }, A(2.32));'), [])
        self.assertEqual(self.gaps('show("#a", 2.32);\ntl.to("#b", { x: 1, duration: 1 }, 2.32);'), [])

    @unittest.skipUnless((TOOLS.parent / "work/beat-fixture").is_dir(), "needs work/beat-fixture, the author's 107 s test edit, which does not ship")
    def test_the_kit_has_none_of_its_own_and_the_fixture_shows_the_one_that_fired(self):
        root = TOOLS.parent
        self.assertEqual(self.gaps((root / "templates/ivory/build_kit/tools_local/timeline.js").read_text(encoding="utf8")), [])
        self.assertIn(('"#ho-vit"', "2.32"), self.gaps((root / "work/beat-fixture/v2/editorial/tools_local/timeline.js").read_text(encoding="utf8")))


class SoundRevision(Base):
    """A sound note after the first final: the normal second pass."""

    def setUp(self):
        super().setUp()
        self.bundle = final.freeze(self.project)
        self.picture = self.stitched(self.bundle)

    def new_sheet(self, reason):
        sheet = sound.sheet_of(self.project)
        write(self.project / "sound.json", {**sheet, "empty_reason": reason})
        return sound.file_hash(self.project / "sound.json")

    def test_the_old_bundle_is_refused_once_the_sheet_moves(self):
        self.new_sheet("A second pass.")
        self.refused("old sound", final.accept, self.project, self.picture)

    def test_a_new_sheet_is_a_new_bundle_of_the_same_picture_and_the_old_one_is_untouched(self):
        before = sound.file_hash(final.editorial(self.bundle) / "sound.json")
        digest = self.new_sheet("A second pass.")
        revision = final.freeze(self.project)
        self.assertEqual(revision.name, f"{self.bundle.name}-sound-{sha([sound.sound_identity(self.project), final.home_rows(self.home)])[:8]}")
        self.assertEqual(sound.file_hash(final.editorial(self.bundle) / "sound.json"), before)
        self.assertEqual(final.bundle_problems(self.bundle), [])
        self.assertEqual(final.bundle_problems(revision), [])
        ed = final.editorial(revision)
        self.assertEqual(sound.file_hash(ed / "sound.json"), digest)
        self.assertEqual(sound.picture_rev(ed), store.read_json(self.bundle / final.BUNDLE)["picture_rev"])
        self.assertEqual(final.freeze(self.project), revision, "the same sheet is the same bundle")
        self.assertEqual(len(list(self.work.glob("*.building"))), 0)

    def test_the_segments_are_shared_not_rendered_again(self):
        self.new_sheet("A second pass.")
        revision = final.freeze(self.project)
        old = next(self.bundle.glob("beat/segments/*/*/segment.mp4"))
        same = revision / old.relative_to(self.bundle)
        self.assertEqual(old.stat().st_ino, same.stat().st_ino)

    def test_the_revision_is_accepted_and_delivers_the_new_sheet(self):
        digest = self.new_sheet("A second pass.")
        revision = final.freeze(self.project)
        picture = self.stitched(revision)
        seen = final.accept(self.project, picture)
        self.assertEqual(seen["project"], final.editorial(revision))
        self.assertEqual(sound.file_hash(seen["project"] / "sound.json"), digest)

    def test_going_back_to_the_first_sheet_is_the_first_bundle(self):
        first = (self.project / "sound.json").read_bytes()
        self.new_sheet("A second pass.")
        final.freeze(self.project)
        (self.project / "sound.json").write_bytes(first)
        self.assertEqual(final.freeze(self.project), self.bundle)
        self.assertEqual(final.accept(self.project, self.picture)["project"], final.editorial(self.bundle))

    def test_a_derivative_is_held_to_the_project_sheet_not_its_own_rebound_one(self):
        shutil.copy(self.media / "face_4k.mp4", self.work / "face_4k.mp4")
        sheet = sound.file_hash(self.project / "sound.json")
        derived = final.derive(self.bundle, "4k60")
        record = store.read_json(derived / final.BUNDLE)
        self.assertEqual(record["sheet_sha256"], sheet)
        self.assertNotEqual(record["files"]["sound.json"], sheet)


class Accept(Base):
    def setUp(self):
        super().setUp()
        self.bundle = final.freeze(self.project)
        self.picture = self.stitched(self.bundle)

    def test_a_valid_picture_passes_with_its_approval(self):
        seen = final.accept(self.project, self.picture)
        self.assertEqual(seen["frames"], self.lock["total_frames"])
        self.assertEqual(seen["approval"]["result"], "PASS")
        self.assertEqual(seen["project"], final.editorial(self.bundle))

    def test_no_record(self):
        shutil.rmtree(self.root / "approvals")
        self.refused("no approval record", final.accept, self.project, self.picture)

    def test_record_for_another_composition(self):
        shutil.rmtree(self.root / "approvals")
        self.approve("a" * 64)
        self.refused("no approval record for composition", final.accept, self.project, self.picture)

    def test_a_failed_record(self):
        shutil.rmtree(self.root / "approvals")
        self.approve(result="FAIL")
        self.refused("did not pass", final.accept, self.project, self.picture)

    def test_a_later_picture_cleared_it(self):
        (self.root / "approvals" / "active.json").unlink()
        self.refused("not the approved picture any more", final.accept, self.project, self.picture)

    def test_project_moved_on(self):
        (self.project / "tools_local" / "timeline.js").write_text(TIMELINE + "// moved\n", encoding="utf8")
        final.rebuild(self.project)
        self.refused("not at the approved composition", final.accept, self.project, self.picture)

    def test_a_changed_segment(self):
        root = store.root_of(final.editorial(self.bundle))
        record = store.read_json(self.picture.parent / "stitch.json")
        flip(store.segment_dir(root, record["profile_hash"], record["beats"][0]["key"]) / "segment.mp4", 2000)
        self.refused("file hash differs", final.accept, self.project, self.picture)

    def test_a_changed_picture(self):
        flip(self.picture, 2000)
        self.refused("not the one stitch.json describes", final.accept, self.project, self.picture)

    def test_a_key_that_is_not_this_composition(self):
        m = json.loads((self.picture.parent / "ownership.json").read_text(encoding="utf8"))
        m["shared"]["files"]["assets/card.png"] = "0" * 64
        write(self.picture.parent / "ownership.json", m)
        self.refused("not of this composition", final.accept, self.project, self.picture)

    def test_timestamps(self):
        with patch.object(final.stitcher, "timestamp_problems", return_value=["packet 3 at 9.0"]):
            self.refused("packet 3", final.accept, self.project, self.picture)

    def test_decoded_rows(self):
        with patch.object(final.store, "rows_of", return_value=["00"]):
            self.refused("rows", final.accept, self.project, self.picture)

    def test_an_unlisted_swap_in_the_bundle(self):
        ff("-f", "lavfi", "-i", "color=c=red:s=16x16:d=0.04", "-frames:v", "1", final.editorial(self.bundle) / "assets" / "card.png")
        self.refused("differs from the frozen bundle", final.accept, self.project, self.picture)

    def test_listing_a_swap_authorizes_nothing(self):
        self.refused("does not authorize", final.accept, self.project, self.picture, True, ["assets/face.mp4"])

    def test_a_profile_that_is_not_the_publish_profile(self):
        other = {**final.complete_profile("final"), "encoder": {**final.complete_profile("final")["encoder"], "crf": 30}}
        shutil.rmtree(store.root_of(final.editorial(self.bundle)) / "segments")
        shutil.rmtree(store.root_of(final.editorial(self.bundle)) / "stitched")
        picture = self.stitched(self.bundle, other)
        self.refused("not the complete publish profile", final.accept, self.project, picture)

    def test_a_picture_from_outside_a_bundle(self):
        picture = self.stitched(self.home)
        self.refused("frozen bundle", final.accept, self.project, picture)


class Derivative(Base):
    def swap(self, name="face_4k.mp4", **fields):
        row = {"path": "assets/face.mp4", "file": str(self.media / name), "source": "test camera", "why": "sharper", "authorized_by": "chase"}
        return {"swaps": [{**row, **fields}]}

    def setUp(self):
        super().setUp()
        self.bundle = final.freeze(self.project)

    def test_fps_map_and_rebinding(self):
        home = final.derive(self.bundle, "4k60", self.swap())
        ed = final.editorial(home)
        record = store.read_json(home / final.DERIVATIVE)
        new_lock = beat_lock.load(ed)
        self.assertEqual(new_lock["fps"], 60)
        self.assertEqual(new_lock["total_frames"], 96)
        self.assertEqual(self.lock["beats"][1]["start_frame"], 26)  # the source-grid cut stays on review frame 26 and final frame 52
        fmap = record["frame_map"]
        self.assertEqual(fmap["beats"], [["b1", 0, 26, 0, 52], ["b2", 26, 48, 52, 96]])
        self.assertEqual(fmap["factor"], 2)
        self.assertEqual(record["base_composition_rev"], self.m["composition_rev"])
        self.assertNotEqual(record["composition_rev"], self.m["composition_rev"])
        self.assertEqual(record["swaps"][0]["path"], "assets/face.mp4")
        self.assertEqual(record["swaps"][0]["best_offset"], 0)
        self.assertEqual(sound.sheet_of(ed)["picture_rev"], sound.picture_rev(ed))
        self.assertEqual(record["sound"]["to"], sound.picture_rev(ed))
        self.assertEqual(final.bundle_problems(home), [])
        self.assertEqual(sound.file_hash(ed / "plan.json"), sound.file_hash(final.editorial(self.bundle) / "plan.json"))

    def test_4k30_keeps_the_review_grid_and_only_swaps(self):
        home = final.derive(self.bundle, "4k30", self.swap())
        record = store.read_json(home / final.DERIVATIVE)
        self.assertEqual(beat_lock.load(final.editorial(home))["fps"], 30)
        self.assertEqual(record["source_edits"], [])
        self.assertEqual(record["swaps"][0]["path"], "assets/face.mp4")
        self.assertEqual(final.complete_profile("final-4k30")["fps"], 30)
        self.assertEqual(final.complete_profile("final-4k30")["width"], 2160)

    def test_a_swapped_final_passes_accept(self):
        home = final.derive(self.bundle, "4k60", self.swap())
        with patch.object(final, "complete_profile", lambda name: {"name": name, "width": 540, "height": 960, "fps": 60}):
            picture = self.stitched(home, final.complete_profile("final-4k60"))
            self.refused("does not authorize", final.accept, self.project, picture, True, [])
            seen = final.accept(self.project, picture, True, ["assets/face.mp4"])
        self.assertEqual(seen["swaps"], ["assets/face.mp4"])

    def test_swap_needs_authorization(self):
        self.refused("does not authorize", final.derive, self.bundle, "4k60", self.swap(authorized_by=""))

    def test_swap_with_a_wrong_length(self):
        self.refused("frames at", final.derive, self.bundle, "4k60", self.swap("face_short.mp4"))

    def test_swap_on_the_wrong_frames(self):
        self.refused("not aligned", final.derive, self.bundle, "4k60", self.swap("face_late.mp4"))

    def test_swap_outside_the_project(self):
        self.refused("one existing video", final.derive, self.bundle, "4k60", self.swap(path="../x.mp4"))

    def test_a_derivative_edited_after_the_fact(self):
        home = final.derive(self.bundle, "4k60", self.swap())
        record = store.read_json(home / final.DERIVATIVE)
        record["swaps"][0]["authorized_by"] = "someone else"
        store.write_json(home / final.DERIVATIVE, record)
        with patch.object(final, "complete_profile", lambda name: {"name": name, "width": 540, "height": 960, "fps": 60}):
            picture = self.stitched(home, final.complete_profile("final-4k60"))
            self.refused("not the record", final.accept, self.project, picture, True, ["assets/face.mp4"])

    def test_stale_sound_is_not_laundered(self):
        ed = final.editorial(self.bundle)
        sheet = sound.sheet_of(ed)
        sheet["picture_rev"] = "0" * 64
        record = store.read_json(self.bundle / final.BUNDLE)
        write(ed / "sound.json", sheet)
        record["files"]["sound.json"] = sound.file_hash(ed / "sound.json")
        store.write_json(self.bundle / final.BUNDLE, record)
        self.refused("stale", final.derive, self.bundle, "4k60", self.swap())

    def test_a_builder_whose_grid_was_not_read(self):
        ed = final.editorial(self.bundle)
        (ed / "tools_local" / "timeline.js").write_text("const FPS=30;\n", encoding="utf8")
        sound.rebind(ed, "test")
        record = store.read_json(self.bundle / final.BUNDLE)
        record["files"].update({rel: sound.file_hash(ed / rel) for rel in ("tools_local/timeline.js", "sound.json")})
        store.write_json(self.bundle / final.BUNDLE, record)
        self.refused("matched 0 times", final.derive, self.bundle, "4k60", self.swap())
        self.assertEqual(list(self.work.glob("*.building")), [], "a refusal leaves nothing behind")

    def test_check_html_refuses_anything_off_the_grid(self):
        a, b = self.work / "a.html", self.work / "b.html"
        a.write_text('<div data-fps="30">\n<p>one</p>\n', encoding="utf8")
        b.write_text('<div data-fps="60">\n<p>two</p>\n', encoding="utf8")
        self.refused("outside its frame grid", final.check_html, a, b)

    def test_frame_map_refuses_other_shapes(self):
        lock = json.loads(json.dumps(self.lock))
        lock.update(fps=45)
        self.refused("whole multiple", final.frame_map, self.lock, lock)
        moved = json.loads(json.dumps(beat_lock.derive(self.plan, 1.6, 60)))
        moved["beats"][1]["start_frame"] = 40
        self.refused("b2", final.frame_map, self.lock, moved)

    def test_events_must_stay_at_their_times(self):
        base = {"events": [{"event_id": "a", "t": 1.0, "frame": 30}]}
        self.assertEqual(final.check_events(base, {"events": [{"event_id": "a", "t": 1.0, "frame": 60}]}, 2)["events"], 1)
        self.refused("moved", final.check_events, base, {"events": [{"event_id": "a", "t": 1.1, "frame": 60}]}, 2)
        self.refused("moved", final.check_events, base, {"events": [{"event_id": "a", "t": 1.0, "frame": 62}]}, 2)
        self.refused("differ", final.check_events, base, {"events": []}, 2)


class Deliver(Base):
    def setUp(self):
        super().setUp()
        self.addCleanup(patch.stopall)
        patch.object(deliver, "ROOT", self.work).start()
        self.bundle = final.freeze(self.project)
        self.picture = self.stitched(self.bundle)

    def args(self, base="t", mode="final", stitched=True, swaps=(), picture=None):
        return argparse.Namespace(project=str(self.project), base=base, mode=mode, picture=picture, adopt_picture=False, stitched=str(self.picture) if stitched else None, fps=None, resolution=None, source_swap=[list(swaps)] if swaps else [])

    def run_quiet(self, a):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = deliver.deliver(a)
        return code, out.getvalue()

    def test_reviewed_final_needs_a_stitched_picture(self):
        self.refused("needs --stitched", deliver.deliver, self.args(stitched=False))

    def test_a_reviewed_final_will_not_take_a_plain_picture(self):
        self.refused("needs --stitched", deliver.deliver, self.args(stitched=False, picture=str(self.picture)))

    def test_refuses_without_a_record_and_writes_nothing(self):
        shutil.rmtree(self.root / "approvals")
        self.refused("no approval record", deliver.deliver, self.args())
        self.assertFalse((self.work / "out" / "t.mp4").exists())
        self.assertFalse((final.editorial(self.bundle) / "renders" / "t.render.json").exists())

    def test_listing_a_swap_with_no_stitched_picture(self):
        self.refused("does not authorize", deliver.deliver, self.args(stitched=False, mode="picture-preview", swaps=["assets/face.mp4"]))

    def test_a_stale_sheet_stops_the_final(self):
        ed = final.editorial(self.bundle)
        sheet = sound.sheet_of(ed)
        sheet["picture_rev"] = "0" * 64
        write(ed / "sound.json", sheet)
        record = store.read_json(self.bundle / final.BUNDLE)
        record["files"]["sound.json"] = sound.file_hash(ed / "sound.json")
        store.write_json(self.bundle / final.BUNDLE, record)
        self.refused("stale", deliver.deliver, self.args())

    def test_delivers_binds_once_and_checks_the_delivered_file(self):
        code, out = self.run_quiet(self.args())
        self.assertEqual(code, 0, out)
        report = json.loads((self.work / "out" / "t-delivery.json").read_text(encoding="utf8"))
        ed = final.editorial(self.bundle)
        bound = json.loads((ed / "renders" / "t.render.json").read_text(encoding="utf8"))
        self.assertTrue(bound["stitched"])
        self.assertEqual(bound["composition_rev"], self.m["composition_rev"])
        self.assertEqual(report["approval"]["result"], "PASS")
        self.assertEqual(report["checks"]["output"]["statuses"]["O1"], "PASS")
        self.assertEqual(report["checks"]["output"]["statuses"]["O2"], "PASS")
        self.assertEqual(report["checks"]["output"]["statuses"]["O3"], "PASS")
        self.assertEqual(report["sound_audition"], "UNVERIFIED until Chase listens")
        self.assertIn(report["status"], ("PASS", "UNVERIFIED"))
        self.assertFalse(report["hyperframes_invoked"])
        self.refused("refusing to overwrite", deliver.deliver, self.args())

    def test_binding_is_exclusive(self):
        path = self.work / "bound.json"
        deliver.write_once(path, {"a": 1})
        self.refused("already exists", deliver.write_once, path, {"a": 2})
        self.assertEqual(json.loads(path.read_text(encoding="utf8")), {"a": 1})
        self.assertEqual([p.name for p in self.work.glob("bound.json*")], ["bound.json"])


if __name__ == "__main__":
    unittest.main()
