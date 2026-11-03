"""Beat renderer, non-render logic: tools/beat_render/run.py, store.py, stitch.py and sentinel.py.

Usage: python tools/tests/test_beat_render.py
Nothing here opens a browser or writes to the fixture. Store tests use a temp folder, and the decode and stitch tests encode a few synthetic frames with ffmpeg.
Rendering is proven on the fixture, in stage1/phase2-renderer.md.
"""
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
NEEDS_FIXTURE = unittest.skipUnless((ROOT / "work/beat-fixture/v2/editorial/beats.lock.json").is_file(),
                                    "needs work/beat-fixture, the author's 107 s test edit, which does not ship")
HERE_RENDER = ROOT / "tools" / "beat_render"
sys.path.insert(0, str(ROOT / "tools" / "beat_render"))
import lock as beat_lock
import ownership
import qualify
import run as runner
import sentinel
import stitch as stitcher
import store
import tied
from common import sha

W, H = 54, 96


def lock_of(frames):
    beats, at = [], 0
    for i, n in enumerate(frames):
        beats.append({"beat_id": f"b{i + 1:02d}", "start_frame": at, "end_frame": at + n, "plan_start": at / 30, "plan_end": (at + n) / 30, "layout": "split"})
        at += n
    return {"schema": 1, "revision": "rev", "fps": 30, "total_frames": at, "duration": at / 30, "beats": beats}


def record(beat, key="k", profile_hash="p", file_sha="s", **changes):
    frames = beat["end_frame"] - beat["start_frame"]
    r = {"beat_id": beat["beat_id"], "start_frame": beat["start_frame"], "end_frame": beat["end_frame"], "input_key": key, "profile_hash": profile_hash, "file": "segment.mp4", "file_sha256": file_sha,
         "decoded": {"frames": frames, "content_hash": "c"},
         "stream": {"codec": "h264", "pix_fmt": "yuv420p", "width": 540, "height": 960, "r_frame_rate": "30/1", "time_base": "1/90000", "has_b_frames": 0, "packets": frames}}
    r.update(changes)
    return r


def plain(value, width=W, height=H):
    return bytes([value]) * sentinel.frame_bytes(width, height)


def encode(path, frames, width=W, height=H, gop=None):
    """frames: raw yuv420p bytes. A closed-GOP, no-B-frame file, as render.mjs writes."""
    args = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{width}x{height}", "-r", "30", "-i", "pipe:0",
            "-c:v", "libx264", "-preset", "ultrafast", "-qp", "0", "-bf", "0", "-g", str(gop or len(frames)), "-x264-params", "scenecut=0:open-gop=0:repeat-headers=1", "-pix_fmt", "yuv420p", "-video_track_timescale", "90000", str(path)]
    subprocess.run(args, input=b"".join(frames), check=True)


def noise(seed, width=W, height=H):
    return np.random.default_rng(seed).integers(0, 255, sentinel.frame_bytes(width, height), dtype=np.uint8).tobytes()


class Temp(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.root = store.open_store(Path(self.dir.name) / "beat")


class VersionPin(unittest.TestCase):
    def test_other_version_fails_closed(self):
        with self.assertRaises(runner.Refused):
            runner.check_version("0.8.185")

    def test_missing_package_fails_closed(self):
        with mock.patch.object(runner, "installed_version", return_value=None):
            with self.assertRaises(runner.Refused):
                runner.check_version()

    def test_pin_passes(self):
        runner.check_version("0.8.184")

    def test_pin_matches_hf_mjs(self):
        self.assertIn(f"PINNED='{runner.PIN}'", (ROOT / "tools/beat_render/hf.mjs").read_text(encoding="utf8"))

    def test_installed_is_the_pin(self):
        self.assertEqual(runner.installed_version(), runner.PIN)


class Profiles(unittest.TestCase):
    def test_workers_are_not_hashed(self):
        data = json.loads(runner.PROFILES.read_text(encoding="utf8"))
        _, h, workers = runner.load_profile("review", 3)
        self.assertEqual(h, sha(data["profiles"]["review"]))
        self.assertEqual(workers, 3)
        self.assertEqual(runner.load_profile("review", 5)[1], h)

    def test_every_field_is_hashed(self):
        data = json.loads(runner.PROFILES.read_text(encoding="utf8"))["profiles"]["review"]
        for change in ({"width": 541}, {"capture": {**data["capture"], "quality": 81}}, {"encoder": {**data["encoder"], "crf": 19}}, {"threads": {**data["threads"], "encoder": 3}}, {"page_rotate_frames": 241}):
            self.assertNotEqual(sha({**data, **change}), sha(data), change)

    def test_unmeasured_worker_count_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "profiles.json"
            path.write_text(json.dumps({"workers": {"x": None}, "profiles": {"x": {"name": "x"}}}), encoding="utf8")
            with mock.patch.object(runner, "PROFILES", path):
                with self.assertRaises(runner.Refused):
                    runner.load_profile("x", None)
                self.assertEqual(runner.load_profile("x", 2)[2], 2)

    def test_unknown_profile_refuses(self):
        with self.assertRaises(runner.Refused):
            runner.load_profile("nope", 1)

    def test_shipped_profiles_have_no_b_frames_and_rotate(self):
        data = json.loads(runner.PROFILES.read_text(encoding="utf8"))
        for p in data["profiles"].values():
            self.assertEqual(p["encoder"]["bframes"], 0)
            self.assertGreater(p["page_rotate_frames"], 0)
            self.assertEqual(p["width"] / 1080, p["dpr"])


class PlanKey(unittest.TestCase):
    def test_review_and_final_share_a_plan(self):
        m = {"shared": {"timing_hash": "t", "media_hash": "m"}}
        data = json.loads(runner.PROFILES.read_text(encoding="utf8"))["profiles"]
        self.assertEqual(runner.plan_key(m, data["review"]), runner.plan_key(m, data["final"]))

    def test_timing_or_media_change_the_plan(self):
        m = {"shared": {"timing_hash": "t", "media_hash": "m"}}
        p = {"fps": 30, "extraction": "auto"}
        base = runner.plan_key(m, p)
        self.assertNotEqual(base, runner.plan_key({"shared": {"timing_hash": "t2", "media_hash": "m"}}, p))
        self.assertNotEqual(base, runner.plan_key({"shared": {"timing_hash": "t", "media_hash": "m2"}}, p))


class CheckStatus(unittest.TestCase):
    def test_exit_codes(self):
        for code, status, finished in ((0, "PASS", True), (1, "FAIL", True), (3, "UNVERIFIED", True), (4, "UNVERIFIED", False), (9, "UNVERIFIED", False)):
            self.assertEqual(runner.check_status([sys.executable, "-c", f"raise SystemExit({code})"], 60), (status, finished))

    def test_a_check_that_hangs_is_stopped_and_did_not_finish(self):
        started = time.perf_counter()
        self.assertEqual(runner.check_status([sys.executable, "-c", "import time; time.sleep(60)"], 2), ("UNVERIFIED", False))
        self.assertLess(time.perf_counter() - started, 30)


class Tied(unittest.TestCase):
    """Windows ties children with a job object; macOS and Linux with a watcher. Either way a killed parent takes them with it."""
    def test_a_child_dies_with_its_parent_and_a_grandchild_with_it(self):
        with tempfile.TemporaryDirectory() as d:
            pids = Path(d) / "pids.txt"
            child = f"import subprocess,sys,time; g=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); open(r'{pids}','w').write(str(__import__('os').getpid())+' '+str(g.pid)); time.sleep(60)"
            parent = f"import sys; sys.path.insert(0, r'{HERE_RENDER}'); import tied, time; p = tied.spawn([sys.executable, '-c', {child!r}]); print(p.tied, flush=True); time.sleep(60)"
            run = subprocess.Popen([sys.executable, "-c", parent], stdout=subprocess.PIPE, text=True)
            self.assertEqual(run.stdout.readline().strip(), "True")
            for _ in range(100):
                if pids.exists() and len(pids.read_text().split()) == 2:
                    break
                time.sleep(0.1)
            child_pid, grandchild_pid = pids.read_text().split()
            self.assertTrue(store.alive(int(child_pid)))
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/PID", str(run.pid)], capture_output=True)
            else:
                run.kill()
            run.wait()
            run.stdout.close()
            for _ in range(50):
                if not store.alive(int(child_pid)) and not store.alive(int(grandchild_pid)):
                    break
                time.sleep(0.1)
            self.assertFalse(store.alive(int(child_pid)))
            self.assertFalse(store.alive(int(grandchild_pid)))

    def test_a_child_this_process_outlives_runs_normally(self):
        p = tied.spawn([sys.executable, "-c", "raise SystemExit(7)"])
        self.assertEqual(p.wait(), 7)


class StaleFiles(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.project = Path(self.dir.name)
        (self.project / "assets").mkdir()
        (self.project / "assets/a.png").write_bytes(b"a")
        (self.project / "assets/v.mp4").write_bytes(b"v")
        (self.project / "shared.js").write_bytes(b"s")
        (self.project / "plan.json").write_bytes(b"{}")
        (self.project / "index.html").write_bytes(b"<html>")
        hash_of = lambda rel: runner.sound_mix.file_hash(self.project / rel)
        self.map = {"authoring": {"plan.json": hash_of("plan.json")},
                    "shared": {"files": {"shared.js": hash_of("shared.js")}, "media": [{"src": "assets/v.mp4", "sha256": hash_of("assets/v.mp4")}], "unused": []},
                    "owners": [{"assets": {"assets/a.png": hash_of("assets/a.png")}}]}

    def test_clean_project_has_none(self):
        self.assertEqual(runner.stale_files(self.project, self.map), [])

    def test_changed_owner_asset(self):
        (self.project / "assets/a.png").write_bytes(b"b")
        self.assertEqual(runner.stale_files(self.project, self.map), ["assets/a.png"])

    def test_changed_source_without_a_build(self):
        (self.project / "plan.json").write_bytes(b"{ }")
        self.assertIn("plan.json", runner.stale_files(self.project, self.map))

    def test_new_unknown_file(self):
        (self.project / "new.js").write_bytes(b"n")
        self.assertIn("new.js", runner.stale_files(self.project, self.map))

    def test_deleted_shared_file(self):
        (self.project / "shared.js").unlink()
        self.assertIn("shared.js", runner.stale_files(self.project, self.map))

    def test_ignored_file_is_not_stale(self):
        (self.project / "STORYBOARD.md").write_bytes(b"x")
        self.assertEqual(runner.stale_files(self.project, self.map), [])

    def test_stamp_moves_with_an_ignored_file_the_page_reads(self):
        (self.project / "assets" / "sfx").mkdir()
        path = self.project / "assets" / "sfx" / "bg.png"
        path.write_bytes(b"one")
        m = {**self.map, "composition_rev": "c", "shared": {**self.map["shared"], "files": {"assets/sfx/bg.png": "x"}}}
        before = runner.project_stamp(self.project, m)
        path.write_bytes(b"two two")
        self.assertNotEqual(runner.project_stamp(self.project, m), before)

    def test_stamp_moves_with_a_file(self):
        before = runner.project_stamp(self.project, {"composition_rev": "r"})
        (self.project / "shared.js").write_bytes(b"longer")
        self.assertNotEqual(before, runner.project_stamp(self.project, {"composition_rev": "r"}))


class Assign(unittest.TestCase):
    def test_every_beat_once_in_time_order(self):
        beats = lock_of([60, 10, 10, 10, 90, 20, 30])["beats"]
        slots = runner.assign(beats, 3)
        self.assertEqual(sorted(b["beat_id"] for s in slots for b in s), sorted(b["beat_id"] for b in beats))
        for slot in slots:
            starts = [b["start_frame"] for b in slot]
            self.assertEqual(starts, sorted(starts))

    def test_balanced_by_frames(self):
        beats = lock_of([30] * 12)["beats"]
        self.assertEqual([sum(b["end_frame"] - b["start_frame"] for b in s) for s in runner.assign(beats, 4)], [90] * 4)

    def test_no_empty_worker(self):
        self.assertEqual(len(runner.assign(lock_of([30])["beats"], 4)), 1)


class RenderSet(unittest.TestCase):
    def setUp(self):
        self.lock = lock_of([30, 30, 30])
        self.keys = {"b01": "a", "b02": "b", "b03": "c"}

    def test_a_touched_beat_whose_key_is_stored_reuses_it(self):
        todo, missed = runner.render_set(self.lock, self.keys, ["b02"], lambda b: True, dict(self.keys))
        self.assertEqual(todo, [])
        self.assertEqual(missed, [])

    def test_force_renders_a_touched_beat_whose_key_is_stored(self):
        todo, _ = runner.render_set(self.lock, self.keys, ["b02"], lambda b: True, dict(self.keys), force=True)
        self.assertEqual(todo, ["b02"])

    def test_a_touched_beat_with_a_new_key_renders(self):
        todo, _ = runner.render_set(self.lock, self.keys, ["b02"], lambda b: b != "b02", {**self.keys, "b02": "old"})
        self.assertEqual(todo, ["b02"])

    def test_missing_segment_renders(self):
        todo, missed = runner.render_set(self.lock, self.keys, [], lambda b: b != "b03", dict(self.keys))
        self.assertEqual(todo, ["b03"])
        self.assertEqual(missed, [])

    def test_changed_key_that_invalidate_missed_is_named_and_rendered(self):
        old = {**self.keys, "b03": "old"}
        todo, missed = runner.render_set(self.lock, self.keys, ["b01"], lambda b: b != "b03", old)
        self.assertEqual(todo, ["b03"])
        self.assertEqual(missed, ["b03"])

    def test_a_missed_key_that_is_stored_is_still_named(self):
        todo, missed = runner.render_set(self.lock, self.keys, [], lambda b: True, {**self.keys, "b03": "old"})
        self.assertEqual(todo, [])
        self.assertEqual(missed, ["b03"])

    def test_engine_change_renders_everything_and_is_not_a_bug(self):
        todo, missed = runner.render_set(self.lock, {"b01": "x", "b02": "y", "b03": "z"}, [], lambda b: False, self.keys, engine_changed=True)
        self.assertEqual(todo, ["b01", "b02", "b03"])
        self.assertEqual(missed, [])

    def test_nothing_changed_renders_nothing(self):
        self.assertEqual(runner.render_set(self.lock, self.keys, [], lambda b: True, dict(self.keys)), ([], []))


class Worst(unittest.TestCase):
    def test_order(self):
        self.assertEqual(runner.worst(["PASS", "UNVERIFIED", "FAIL"]), "FAIL")
        self.assertEqual(runner.worst(["PASS", "UNVERIFIED"]), "UNVERIFIED")
        self.assertEqual(runner.worst(["PASS"]), "PASS")

    def test_no_evidence_is_never_pass(self):
        self.assertEqual(runner.worst([]), "UNVERIFIED")


class Samples(unittest.TestCase):
    def test_first_middle_last(self):
        self.assertEqual(sentinel.samples({"start_frame": 66, "end_frame": 121}), [66, 93, 120])

    def test_one_frame_beat(self):
        self.assertEqual(sentinel.samples({"start_frame": 5, "end_frame": 6}), [5])

    def test_events_inside_only(self):
        events = [{"frame": 70}, {"frame": 65}, {"frame": 121}, {"frame": 93}]
        self.assertEqual(sentinel.samples({"start_frame": 66, "end_frame": 121}, events), [66, 70, 93, 120])

    def test_expected_chip_and_face(self):
        m = {"owners": [{"id": "cap.w0006-0008", "kind": "caption", "frames": [[65, 74]]}, {"id": "cap.w0009-0010", "kind": "caption", "frames": [[74, 80]]}, {"id": "scene.x", "kind": "scene", "frames": [[0, 100]]}]}
        split = {"beat_id": "b02", "layout": "split"}
        self.assertEqual(sentinel.expected(73, split, m), {"layout": "split", "chips": ["cap.w0006-0008"], "face": None})
        self.assertEqual(sentinel.expected(90, {"beat_id": "b03", "layout": "full-face"}, m), {"layout": "full-face", "chips": [], "face": "ff-b03"})


class Compare(unittest.TestCase):
    def test_identical_is_99(self):
        self.assertEqual(sentinel.psnr(plain(100), plain(100), W, H), 99.0)

    def test_matches_ffmpeg_psnr_avg(self):
        a, b = noise(1), noise(2)
        ours = sentinel.psnr(a, b, W, H)
        r = subprocess.run(["ffmpeg", "-hide_banner", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{W}x{H}", "-i", "pipe:0", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{W}x{H}", "-i", _write(self, b),
                            "-lavfi", "psnr", "-f", "null", "-"], input=a, capture_output=True)
        text = r.stderr.decode()
        self.assertAlmostEqual(ours, float(text.split("average:")[1].split()[0]), delta=0.02)

    def test_region_sees_only_the_lower_half(self):
        top = bytearray(plain(100))
        for row in range(H // 2):
            top[row * W:(row + 1) * W] = bytes([0]) * W
        self.assertLess(sentinel.psnr(bytes(top), plain(100), W, H), 30)
        self.assertEqual(sentinel.psnr(bytes(top), plain(100), W, H, H // 2), 99.0)

    def test_size_mismatch_raises(self):
        with self.assertRaises(ValueError):
            sentinel.psnr(b"12", plain(1), W, H)

    def test_fail_on_either_measure(self):
        bad = plain(0)
        r = sentinel.compare({10: bad, 11: plain(100)}, {10: plain(100), 11: plain(100)}, [10, 11], W, H, H // 2)
        self.assertEqual(r["status"], "FAIL")
        self.assertEqual([x["frame"] for x in r["failed"]], [10])

    def test_region_alone_fails_a_frame(self):
        lower = bytearray(plain(100))
        lower[W * 80:W * 96] = bytes([0]) * (W * 16)
        whole, region = sentinel.psnr(bytes(lower), plain(100), W, H), sentinel.psnr(bytes(lower), plain(100), W, H, H // 2)
        self.assertLess(region, whole)
        r = sentinel.compare({0: bytes(lower)}, {0: plain(100)}, [0], W, H, H // 2, minimum=(whole + region) / 2)
        self.assertEqual(r["status"], "FAIL")

    def test_invalid_reference_is_unverified_not_pass(self):
        r = sentinel.compare({1: plain(100), 2: plain(100)}, {1: plain(100), 2: None}, [1, 2], W, H, H // 2)
        self.assertEqual(r["status"], "UNVERIFIED")
        self.assertEqual(r["unverified"], [2])

    def labelled(self, word):
        """A busy frame with a small rectangle in one place: what a wrong word is to the eye, and nearly nothing to a whole-frame number."""
        frame = bytearray(noise(5, 540, 960))
        for y in range(300, 318):
            for x in range(100, 124):
                frame[y * 540 + x] = word
        return bytes(frame)

    def test_a_small_wrong_word_passes_psnr_and_fails_on_its_block(self):
        a, b = self.labelled(10), self.labelled(200)
        self.assertGreater(sentinel.psnr(a, b, 540, 960), sentinel.PSNR_MIN)
        self.assertGreater(sentinel.worst_block(a, b, 540, 960), sentinel.BLOCK_MAX)
        seen = sentinel.compare({7: a}, {7: b}, [7], 540, 960, 480)
        self.assertEqual(seen["status"], "FAIL")
        self.assertGreater(seen["failed"][0]["block"], sentinel.BLOCK_MAX)

    def test_an_even_small_difference_stays_under_the_block_line(self):
        a = np.frombuffer(noise(5, 540, 960), dtype=np.uint8)
        b = np.clip(a.astype(np.int16) + 4, 0, 255).astype(np.uint8)
        seen = sentinel.compare({7: a.tobytes()}, {7: b.tobytes()}, [7], 540, 960, 480)
        self.assertEqual(seen["failed"], [])
        self.assertLessEqual(seen["max_block"], sentinel.BLOCK_MAX)

    def test_a_word_on_a_block_edge_is_not_split(self):
        a = bytearray(540 * 960 * 3 // 2)
        b = bytearray(a)
        for y in range(20, 26):
            for x in range(20, 28):  # straddles the first 24 px block's right and bottom edges
                b[y * 540 + x] = 200
        self.assertEqual(sentinel.worst_block(bytes(a), bytes(b), 540, 960), 8 * 6 * 200 / (24 * 24))

    def test_the_block_scales_with_the_frame(self):
        a = bytes(1080 * 1920 * 3 // 2)
        b = bytearray(a)
        for y in range(10, 58):
            for x in range(10, 58):
                b[y * 1080 + x] = 100
        self.assertEqual(sentinel.worst_block(a, bytes(b), 1080, 1920, 24), 100)
        self.assertGreaterEqual(sentinel.worst_block(a, bytes(b), 1080, 1920), 50)

    def test_no_reference_at_all_is_unverified(self):
        self.assertEqual(sentinel.compare({1: plain(100)}, {}, [1], W, H, H // 2)["status"], "UNVERIFIED")


def _write(test, data):
    d = tempfile.mkdtemp()
    test.addCleanup(shutil.rmtree, d, True)
    path = Path(d) / "b.yuv"
    path.write_bytes(data)
    return str(path)


class Clipped(unittest.TestCase):
    width, height = 540, 960

    def frame(self, fill):
        y = np.full((self.height, self.width), 200, dtype=np.uint8)
        fill(y)
        return y.tobytes() + bytes([128]) * (self.width * self.height // 2)

    def test_observed_signature_is_flagged(self):
        def inside_only(y):
            y[:300, :400] = np.random.default_rng(0).integers(0, 255, (300, 400), dtype=np.uint8)
        self.assertTrue(sentinel.clipped(self.frame(inside_only), self.width, self.height))

    def test_a_normal_frame_is_not(self):
        def face(y):
            y[480:, :] = np.random.default_rng(1).integers(0, 255, (480, 540), dtype=np.uint8)
        self.assertFalse(sentinel.clipped(self.frame(face), self.width, self.height))

    def test_content_right_of_the_edge_is_not(self):
        def card(y):
            y[100:200, 430:500] = 20
        self.assertFalse(sentinel.clipped(self.frame(card), self.width, self.height))

    def test_content_below_the_edge_is_not(self):
        def chip(y):
            y[500:540, 100:300] = 20
        self.assertFalse(sentinel.clipped(self.frame(chip), self.width, self.height))


class Decode(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.frames = [noise(i) for i in range(6)]
        self.video = Path(self.dir.name) / "a.mp4"
        encode(self.video, self.frames)

    def test_rows_are_framemd5_rows(self):
        rows, _, _ = sentinel.scan(self.video, W, H)
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(self.video), "-an", "-vf", "format=yuv420p", "-c:v", "rawvideo", "-f", "framemd5", "-"], capture_output=True, text=True, check=True)
        self.assertEqual(rows, [line.split(",")[-1].strip() for line in r.stdout.splitlines() if not line.startswith("#")])

    def test_lossless_rows_match_input(self):
        rows, picked, _ = sentinel.scan(self.video, W, H, [0, 5])
        self.assertEqual(rows, [hashlib.md5(f).hexdigest() for f in self.frames])
        self.assertEqual(picked[5], self.frames[5])

    def test_pairing_is_by_frame_number_not_timestamp(self):
        """A re-mux through rounded milliseconds changes no decoded row."""
        moved = Path(self.dir.name) / "moved.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(self.video), "-c", "copy", "-video_track_timescale", "1000", str(moved)], check=True)
        self.assertEqual(sentinel.scan(moved, W, H)[0], sentinel.scan(self.video, W, H)[0])

    def test_a_timestamp_gap_is_not_padded(self):
        """Without passthrough, rawvideo's constant rate invents frames, and the count is not what decoded."""
        gap = Path(self.dir.name) / "gap.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=64x64:rate=30:duration=3", "-vf", "select='not(eq(n,40))'", "-fps_mode", "vfr", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(gap)], check=True)
        self.assertEqual(len(sentinel.scan(gap, 64, 64)[0]), stitcher.probe_video(gap)["packets"])

    @NEEDS_FIXTURE
    def test_a_badly_damaged_file_does_not_hang(self):
        """More stderr than a pipe holds. A pipe nobody read kept ffmpeg alive for good."""
        source = store.latest(ROOT / "work/beat-fixture/beat", "review")
        data = bytearray(Path(source["file"]).read_bytes())
        for i in range(100000, len(data), 2048):
            data[i] ^= 0xff
        damaged = Path(self.dir.name) / "damaged.mp4"
        damaged.write_bytes(data)
        done = {}

        def go():
            try:
                done["rows"] = len(sentinel.scan(damaged, 540, 960)[0])
            except RuntimeError as e:
                done["error"] = str(e)

        worker = threading.Thread(target=go, daemon=True)
        worker.start()
        worker.join(180)
        self.assertTrue(done, "scan still blocked after 180 s")

    def test_broken_file_raises(self):
        bad = Path(self.dir.name) / "bad.mp4"
        bad.write_bytes(b"not a video")
        with self.assertRaises(RuntimeError):
            sentinel.scan(bad, W, H)

    def test_suspects_keep_bytes_up_to_the_limit(self):
        with mock.patch.object(sentinel, "clipped", return_value=True):
            rows, picked, suspects = sentinel.scan(self.video, W, H, keep_suspects=2)
        self.assertEqual(suspects, list(range(6)))
        self.assertEqual(sorted(picked), [0, 1])

    def test_stream_parameters_and_timestamps(self):
        p = stitcher.probe_video(self.video)
        self.assertEqual((p["codec"], p["pix_fmt"], p["has_b_frames"], p["packets"], p["r_frame_rate"]), ("h264", "yuv420p", 0, 6, "30/1"))


class CheckSegments(unittest.TestCase):
    def setUp(self):
        self.lock = lock_of([30, 40])
        self.keys = {"b01": "k1", "b02": "k2"}
        b = self.lock["beats"]
        self.records = {"b01": record(b[0], "k1", file_sha="s1"), "b02": record(b[1], "k2", file_sha="s2")}
        self.hashes = {"b01": "s1", "b02": "s2"}

    def problems(self):
        return stitcher.check_segments(self.lock, self.keys, "p", self.records, self.hashes)

    def test_clean(self):
        self.assertEqual(self.problems(), [])

    def test_missing_segment(self):
        self.records["b02"] = None
        self.assertTrue(any("no segment" in p for p in self.problems()))

    def test_stale_key(self):
        self.keys["b02"] = "new"
        self.assertTrue(any("key is stale" in p for p in self.problems()))

    def test_wrong_profile(self):
        self.records["b01"]["profile_hash"] = "other"
        self.assertTrue(any("profile differs" in p for p in self.problems()))

    def test_file_hash(self):
        self.hashes["b01"] = "tampered"
        self.assertTrue(any("file hash differs" in p for p in self.problems()))

    def test_short_decode(self):
        self.records["b02"]["decoded"]["frames"] = 39
        self.assertTrue(any("decoded 39" in p for p in self.problems()))

    def test_declared_range_cannot_hide_a_short_decode(self):
        """The spike checked declared ranges only. Contents are what count."""
        self.records["b01"]["stream"]["packets"] = 29
        self.assertTrue(any("29 packets" in p for p in self.problems()))

    def test_b_frames(self):
        self.records["b02"]["stream"]["has_b_frames"] = 2
        self.assertTrue(any("B-frames" in p for p in self.problems()))

    def test_stream_parameters_must_match(self):
        self.records["b02"]["stream"]["width"] = 1080
        self.assertTrue(any("stream parameters differ" in p for p in self.problems()))

    def test_gap(self):
        self.lock["beats"][1]["start_frame"] = 31
        self.records["b02"]["start_frame"] = 31
        self.assertTrue(any("expected 30" in p for p in self.problems()))

    def test_segment_for_another_beat(self):
        self.records["b02"] = record(self.lock["beats"][0], "k2", file_sha="s2")
        self.assertTrue(any("segment is for b01" in p for p in self.problems()))

    def test_total_frames(self):
        self.lock["total_frames"] = 71
        self.assertTrue(any("expected 71" in p for p in self.problems()))


class Timestamps(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.video = Path(self.dir.name) / "a.mp4"
        encode(self.video, [noise(i) for i in range(6)])

    def with_audio(self, name, extra=()):
        out = Path(self.dir.name) / name
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(self.video), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-shortest", "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", *extra, str(out)], check=True)
        return out

    def test_clean(self):
        self.assertEqual(stitcher.timestamp_problems(self.with_audio("ok.mp4"), 30, 6), [])

    def test_no_audio(self):
        self.assertTrue(any("no audio" in p for p in stitcher.timestamp_problems(self.video, 30, 6)))

    def test_wrong_count(self):
        self.assertTrue(any("expected 7" in p for p in stitcher.timestamp_problems(self.with_audio("ok.mp4"), 30, 7)))

    def test_wrong_rate(self):
        self.assertTrue(any("packet 1" in p for p in stitcher.timestamp_problems(self.with_audio("ok.mp4"), 60, 6)))


class Segments(Temp):
    def built(self, key, data=b"video", profile="p"):
        folder = store.new_tmp(self.root)
        (folder / "segment.mp4").write_bytes(data)
        (folder / "segment.framemd5").write_text("aa\nbb\n", encoding="utf8")
        store.write_json(folder / "segment.json", {"input_key": key, "profile_hash": profile, "file": "segment.mp4", "bytes": len(data), "file_sha256": hashlib.sha256(data).hexdigest(), "decoded": {"content_hash": sha("aa\nbb")}})
        return folder

    def test_publish_then_find(self):
        store.publish(self.root, self.built("k"), "p", "k")
        self.assertEqual(store.find(self.root, "p", "k")["bytes"], 5)
        self.assertEqual(store.rows_of(self.root, "p", "k"), ["aa", "bb"])

    def test_unpublished_is_not_found(self):
        self.built("k")
        self.assertIsNone(store.find(self.root, "p", "k"))

    def test_folder_without_record_is_not_a_segment(self):
        folder = store.segment_dir(self.root, "p", "k")
        folder.mkdir(parents=True)
        (folder / "segment.mp4").write_bytes(b"partial")
        self.assertIsNone(store.find(self.root, "p", "k"))

    def test_truncated_file_is_not_found(self):
        store.publish(self.root, self.built("k"), "p", "k")
        (store.segment_dir(self.root, "p", "k") / "segment.mp4").write_bytes(b"v")
        self.assertIsNone(store.find(self.root, "p", "k"))

    def test_record_of_another_key_is_not_found(self):
        store.publish(self.root, self.built("other"), "p", "k")
        self.assertIsNone(store.find(self.root, "p", "k"))

    def test_other_profile_is_not_found(self):
        store.publish(self.root, self.built("k"), "p", "k")
        self.assertIsNone(store.find(self.root, "q", "k"))

    def test_forced_render_replaces(self):
        store.publish(self.root, self.built("k", b"old"), "p", "k")
        store.publish(self.root, self.built("k", b"newer"), "p", "k")
        self.assertEqual(store.find(self.root, "p", "k")["bytes"], 5)

    def stitched_names(self, key):
        folder = self.root / "stitched" / "review-abc"
        folder.mkdir(exist_ok=True)
        store.write_json(folder / "stitch.json", {"beats": [{"key": key}]})

    def test_a_segment_a_stitched_picture_names_is_not_replaced(self):
        store.publish(self.root, self.built("k", b"old"), "p", "k")
        self.stitched_names("k")
        with self.assertRaisesRegex(ValueError, "only --force"):
            store.publish(self.root, self.built("k", b"newer"), "p", "k")
        self.assertEqual(store.find(self.root, "p", "k")["bytes"], 3)

    def test_force_replaces_what_a_stitched_picture_names(self):
        store.publish(self.root, self.built("k", b"old"), "p", "k")
        self.stitched_names("k")
        store.publish(self.root, self.built("k", b"newer"), "p", "k", force=True)
        self.assertEqual(store.find(self.root, "p", "k")["bytes"], 5)

    def test_a_damaged_segment_a_picture_names_can_be_replaced(self):
        store.publish(self.root, self.built("k", b"old"), "p", "k")
        self.stitched_names("k")
        (store.segment_dir(self.root, "p", "k") / "segment.mp4").write_bytes(b"x")
        store.publish(self.root, self.built("k", b"newer"), "p", "k")
        self.assertEqual(store.find(self.root, "p", "k")["bytes"], 5)

    def test_a_flipped_byte_is_found_by_size_and_not_intact(self):
        store.publish(self.root, self.built("k"), "p", "k")
        self.assertIsNotNone(store.intact(self.root, "p", "k"))
        (store.segment_dir(self.root, "p", "k") / "segment.mp4").write_bytes(b"vidxo")
        self.assertIsNotNone(store.find(self.root, "p", "k"))
        self.assertIsNone(store.intact(self.root, "p", "k"))

    def test_changed_rows_are_not_intact(self):
        store.publish(self.root, self.built("k"), "p", "k")
        (store.segment_dir(self.root, "p", "k") / "segment.framemd5").write_text("aa\ncc\n", encoding="utf8")
        self.assertIsNone(store.intact(self.root, "p", "k"))

    def test_an_old_record_with_no_hash_is_not_intact(self):
        folder = self.built("k")
        store.write_json(folder / "segment.json", {"input_key": "k", "profile_hash": "p", "file": "segment.mp4", "bytes": 5})
        store.publish(self.root, folder, "p", "k")
        self.assertIsNone(store.intact(self.root, "p", "k"))

    def test_a_flipped_byte_a_picture_names_can_be_replaced(self):
        store.publish(self.root, self.built("k"), "p", "k")
        self.stitched_names("k")
        (store.segment_dir(self.root, "p", "k") / "segment.mp4").write_bytes(b"vidxo")
        store.publish(self.root, self.built("k", b"video"), "p", "k")
        self.assertIsNotNone(store.intact(self.root, "p", "k"))

    def test_clear_tmp_leaves_published_segments(self):
        store.publish(self.root, self.built("k"), "p", "k")
        self.built("abandoned")
        store.clear_tmp(self.root)
        self.assertEqual(list((self.root / "tmp").iterdir()), [])
        self.assertIsNotNone(store.find(self.root, "p", "k"))


class RunLock(Temp):
    def test_second_run_refuses_while_the_first_lives(self):
        store.lock(self.root)
        with self.assertRaises(RuntimeError):
            store.lock(self.root)
        store.unlock(self.root)

    def test_dead_run_is_taken_over_and_its_tmp_cleared(self):
        (self.root / "run.lock").write_text(json.dumps({"pid": 999999}), encoding="utf8")
        store.new_tmp(self.root)
        with mock.patch.object(store, "alive", return_value=False):
            store.lock(self.root)
        self.assertEqual(list((self.root / "tmp").iterdir()), [])
        store.unlock(self.root)

    def test_the_lock_file_holds_its_pid_from_the_moment_it_exists(self):
        real = os.link
        seen = {}

        def link(source, target):
            seen["bytes"] = Path(source).read_bytes()
            real(source, target)

        with mock.patch.object(os, "link", link):
            store.lock(self.root)
        self.assertEqual(json.loads(seen["bytes"]), {"pid": os.getpid()})
        self.assertEqual(store.read_json(self.root / "run.lock"), {"pid": os.getpid()})
        self.assertEqual([p.name for p in self.root.glob("run.lock*")], ["run.lock"], "no temp left beside it")
        store.unlock(self.root)

    def test_two_runs_racing_for_the_name_cannot_both_win(self):
        results = []
        barrier = threading.Barrier(8)

        def go():
            barrier.wait()
            try:
                store.lock(self.root)
                results.append("won")
            except RuntimeError:
                results.append("refused")

        with mock.patch.object(store, "clear_tmp"):
            threads = [threading.Thread(target=go) for _ in range(8)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
        self.assertEqual(sorted(results), ["refused"] * 7 + ["won"])
        store.unlock(self.root)

    @unittest.skipUnless(os.name == "nt", "Windows liveness must never use os.kill")
    def test_alive_never_signals_a_process(self):
        """os.kill on Windows terminates. Liveness goes through tasklist only."""
        with mock.patch.object(os, "kill") as kill:
            self.assertTrue(store.alive(os.getpid()))
            self.assertFalse(store.alive(999999))
        kill.assert_not_called()


class Evict(Temp):
    def segment(self, key, size, when):
        folder = store.segment_dir(self.root, "p", key)
        folder.mkdir(parents=True)
        (folder / "segment.mp4").write_bytes(b"x" * size)
        store.write_json(folder / "segment.json", {"input_key": key})
        os.utime(folder / "segment.json", (when, when))
        os.utime(folder, (when, when))

    def limit(self, n):
        store.write_json(self.root / "store.json", {"limit_bytes": n})

    def test_under_limit_removes_nothing(self):
        self.segment("a", 100, 1000)
        self.limit(10 ** 6)
        self.assertEqual(store.evict(self.root)["removed"], 0)

    def test_oldest_goes_first(self):
        self.segment("old", 1000, 1000)
        self.segment("new", 1000, 2000)
        self.limit(1500)
        self.assertEqual(store.evict(self.root)["removed"], 1)
        self.assertFalse(store.segment_dir(self.root, "p", "old").exists())
        self.assertTrue(store.segment_dir(self.root, "p", "new").exists())

    def test_refs_follow_the_limit_too(self):
        self.segment("a", 1000, 5000)
        ref = store.refs_dir(self.root, "pppppppppppppppp", "b")
        ref.mkdir(parents=True)
        (ref / "1.jpg").write_bytes(b"y" * 1000)
        os.utime(ref, (1000, 1000))
        self.limit(1500)
        store.evict(self.root)
        self.assertFalse(ref.exists())

    def test_stitched_picture_protects_its_segments(self):
        self.segment("kept", 1000, 1000)
        self.segment("loose", 1000, 2000)
        folder = self.root / "stitched" / "review-abc"
        folder.mkdir()
        store.write_json(folder / "stitch.json", {"beats": [{"key": "kept"}]})
        store.write_json(self.root / "current.json", {"review": {"stitched": "review-abc"}})
        self.limit(1500)
        store.evict(self.root)
        self.assertTrue(store.segment_dir(self.root, "p", "kept").exists())
        self.assertFalse(store.segment_dir(self.root, "p", "loose").exists())

    def test_everything_protected_reports_over_limit_and_keeps_it(self):
        self.segment("kept", 1000, 1000)
        folder = self.root / "stitched" / "review-abc"
        folder.mkdir()
        store.write_json(folder / "stitch.json", {"beats": [{"key": "kept"}]})
        self.limit(10)
        result = store.evict(self.root)
        self.assertTrue(result["over_limit"])
        self.assertTrue(store.segment_dir(self.root, "p", "kept").exists())


class Current(Temp):
    entry = {"stitched": "review-a", "file": "x", "file_sha256": "s", "composition_rev": "c", "lock_revision": "l"}

    def test_a_picture_that_did_not_fail_is_current(self):
        self.assertTrue(store.set_current(self.root, "review", self.entry, "UNVERIFIED"))
        self.assertEqual(store.read_json(self.root / "current.json")["review"]["status"], "UNVERIFIED")

    def test_a_failed_picture_is_a_last_attempt_and_current_stays(self):
        store.set_current(self.root, "review", self.entry, "UNVERIFIED")
        self.assertFalse(store.set_current(self.root, "review", {**self.entry, "stitched": "review-b"}, "FAIL"))
        self.assertEqual(store.read_json(self.root / "current.json")["review"]["stitched"], "review-a")
        self.assertEqual(store.read_json(self.root / "last_attempt.json")["review"]["stitched"], "review-b")

    def test_the_first_picture_failing_leaves_no_current_at_all(self):
        store.set_current(self.root, "review", self.entry, "FAIL")
        self.assertFalse((self.root / "current.json").exists())

    def test_change_diffs_against_the_last_picture_stitched(self):
        store.set_current(self.root, "review", self.entry, "UNVERIFIED")
        self.assertEqual(store.latest(self.root, "review")["stitched"], "review-a")
        store.set_current(self.root, "review", {**self.entry, "stitched": "review-b"}, "FAIL")
        self.assertEqual(store.latest(self.root, "review")["stitched"], "review-b")

    def test_a_good_picture_clears_its_last_attempt_only(self):
        store.set_current(self.root, "review", self.entry, "FAIL")
        store.set_current(self.root, "final", self.entry, "FAIL")
        store.set_current(self.root, "review", {**self.entry, "stitched": "review-c"}, "UNVERIFIED")
        self.assertEqual(list(store.read_json(self.root / "last_attempt.json")), ["final"])
        self.assertEqual(store.latest(self.root, "review")["stitched"], "review-c")

    def test_no_picture_at_all(self):
        self.assertIsNone(store.latest(self.root, "review"))


class Unfinished(Temp):
    """A check that did not finish told us nothing, whatever a review picture's best status reads."""

    entry = {"stitched": "review-a"}

    def test_it_is_not_current(self):
        store.set_current(self.root, "review", {"stitched": "review-old"}, "UNVERIFIED")
        self.assertFalse(store.set_current(self.root, "review", self.entry, "UNVERIFIED", finished=False))
        self.assertEqual(store.read_json(self.root / "current.json")["review"]["stitched"], "review-old")
        self.assertEqual(store.read_json(self.root / "last_attempt.json")["review"]["stitched"], "review-a")

    def test_the_next_finished_picture_clears_it(self):
        store.set_current(self.root, "review", self.entry, "UNVERIFIED", finished=False)
        self.assertTrue(store.set_current(self.root, "review", {"stitched": "review-b"}, "UNVERIFIED"))
        self.assertNotIn("review", store.read_json(self.root / "last_attempt.json"))


class Damaged(Temp):
    """A segment of the right size with the wrong bytes. The run counts it as missing, so it heals without a forced whole render."""

    def setUp(self):
        super().setUp()
        run = self.run = runner.Run.__new__(runner.Run)
        run.root, run.profile, run.profile_hash, run.inject = self.root, {"name": "review"}, "p", None
        run.lock = lock_of([30, 30])
        run.beats = {b["beat_id"]: b for b in run.lock["beats"]}
        run.keys = {"b01": "k1", "b02": "k2"}
        run.ensure_plan = run.prepare = lambda *a: None
        for key in run.keys.values():
            folder = store.new_tmp(self.root)
            (folder / "segment.mp4").write_bytes(b"video")
            (folder / "segment.framemd5").write_text("aa\nbb\n", encoding="utf8")
            store.write_json(folder / "segment.json", {"input_key": key, "profile_hash": "p", "file": "segment.mp4", "bytes": 5, "file_sha256": hashlib.sha256(b"video").hexdigest(), "decoded": {"content_hash": sha("aa\nbb")}})
            store.publish(self.root, folder, "p", key)
        (store.segment_dir(self.root, "p", "k2") / "segment.mp4").write_bytes(b"vidxo")

    def test_stored_says_no_to_a_flipped_segment(self):
        self.assertTrue(self.run.stored("b01"))
        self.assertFalse(self.run.stored("b02"))

    def test_draft_renders_only_the_damaged_beat(self):
        with mock.patch.object(runner, "render_and_finish", side_effect=lambda run, change, tmp, todo, started, **k: change):
            change = runner.draft(self.run, mock.Mock(force=False, inject_beats=None), None, 0)
        self.assertEqual((change["rendered"], change["reused"], change["damaged"]), (["b02"], ["b01"], ["b02"]))

    def test_change_renders_only_the_damaged_beat_and_it_is_no_bug(self):
        self.run.map = {}
        folder = self.root / "stitched" / "review-x"
        folder.mkdir()
        store.write_json(folder / "ownership.json", {"m": 1})
        store.write_json(folder / "stitch.json", {"beats": [{"beat_id": "b01", "key": "k1"}, {"beat_id": "b02", "key": "k2"}], "engine_hash": "e", "profile_hash": "p"})
        store.set_current(self.root, "review", {"stitched": "review-x"}, "UNVERIFIED")
        self.run.engine = "e"
        empty = {"beats": [], "share": 0, "new_media_plan": False, "all_reasons": [], "owners_changed": []}
        with mock.patch.object(runner.ownership, "invalidate", return_value=empty), mock.patch.object(runner, "render_and_finish", side_effect=lambda run, change, tmp, todo, started, **k: (change, k)):
            change, options = runner.change_cmd(self.run, mock.Mock(force=False, inject_beats=None, kind=None), None, 0)
        self.assertEqual((change["rendered"], change["under_invalidated"], change["damaged"], options["failed"]), (["b02"], [], ["b02"], False))


class Plans(Temp):
    def test_keeps_two_newest_keyed_plans_and_anything_else(self):
        for i, name in enumerate(["aaaaaaaaaaaaaaaa", "bbbbbbbbbbbbbbbb", "cccccccccccccccc"]):
            folder = self.root / "plans" / name
            folder.mkdir()
            (folder / "plan.json").write_text("{}", encoding="utf8")
            os.utime(folder / "plan.json", (1000 + i, 1000 + i))
        (self.root / "plans" / "phase1").mkdir()
        store.prune_plans(self.root)
        self.assertEqual(sorted(p.name for p in (self.root / "plans").iterdir()), ["bbbbbbbbbbbbbbbb", "cccccccccccccccc", "phase1"])


class ChangeRecords(Temp):
    def test_numbers_rise(self):
        self.assertEqual(store.next_change(self.root).name, "0001.json")
        store.write_json(store.next_change(self.root), {})
        self.assertEqual(store.next_change(self.root).name, "0002.json")


class StitchEnd(Temp):
    """A real concat of three synthetic closed-GOP segments, and a real refusal when one is tampered with."""

    def setUp(self):
        super().setUp()
        self.project = Path(self.dir.name) / "project"
        self.project.mkdir()
        (self.project / "ownership.json").write_text("{}", encoding="utf8")
        (self.project / "beats.lock.json").write_text("{}", encoding="utf8")
        self.lock = lock_of([4, 3, 5])
        self.profile = {"name": "review", "width": W, "height": H}
        self.keys, self.rows = {}, []
        n = 0
        for b in self.lock["beats"]:
            frames = [noise(n + i) for i in range(b["end_frame"] - b["start_frame"])]
            n += len(frames)
            folder = store.new_tmp(self.root)
            video = folder / "segment.mp4"
            encode(video, frames)
            rows = sentinel.scan(video, W, H)[0]
            self.rows += rows
            key = "k" + b["beat_id"]
            self.keys[b["beat_id"]] = key
            (folder / "segment.framemd5").write_text("\n".join(rows) + "\n", encoding="utf8")
            store.write_json(folder / "segment.json", {**record(b, key, "p", runner.sound_mix.file_hash(video)), "bytes": video.stat().st_size, "decoded": {"frames": len(rows), "content_hash": sha("\n".join(rows))}, "stream": stitcher.probe_video(video)})
            store.publish(self.root, folder, "p", key)
        self.bed = Path(self.dir.name) / "bed.m4a"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", "0.4", "-c:a", "aac", str(self.bed)], check=True)

    def go(self):
        return stitcher.stitch(self.root, self.project, self.lock, {"composition_rev": "c"}, self.profile, "p", "e", self.keys, self.bed)

    def test_rows_match_and_the_stitch_leaves_current_alone(self):
        record_, folder = self.go()
        self.assertEqual(sentinel.scan(folder / "review.mp4", W, H)[0], self.rows)
        self.assertFalse((self.root / "current.json").exists(), "only a run that checked the picture moves it")
        self.assertTrue((folder / "stitch.json").is_file())
        self.assertEqual([b["start_frame"] for b in record_["beats"]], [0, 4, 7])

    def stitch_as(self, rev):
        return stitcher.stitch(self.root, self.project, self.lock, {"composition_rev": rev}, self.profile, "p", "e", self.keys, self.bed)

    def test_two_compositions_with_the_same_bytes_keep_their_own_records(self):
        (self.project / "ownership.json").write_text('{"composition_rev": "a"}', encoding="utf8")
        first, folder_a = self.stitch_as("a" * 64)
        (self.project / "ownership.json").write_text('{"composition_rev": "b"}', encoding="utf8")
        second, folder_b = self.stitch_as("b" * 64)
        self.assertEqual(first["file_sha256"], second["file_sha256"], "stitching is byte-repeatable")
        self.assertNotEqual(folder_a, folder_b)
        self.assertEqual(store.read_json(folder_a / "stitch.json")["composition_rev"], "a" * 64)
        self.assertEqual(store.read_json(folder_b / "stitch.json")["composition_rev"], "b" * 64)
        self.assertEqual(store.read_json(folder_a / "ownership.json")["composition_rev"], "a")
        self.assertEqual(store.read_json(folder_b / "ownership.json")["composition_rev"], "b")

    def test_the_same_composition_again_takes_the_newest_records(self):
        self.stitch_as("c" * 64)
        (self.project / "ownership.json").write_text('{"note": "newer"}', encoding="utf8")
        _, folder = self.stitch_as("c" * 64)
        self.assertEqual(store.read_json(folder / "ownership.json"), {"note": "newer"})

    def test_an_entry_names_its_own_folder_and_composition(self):
        record_, folder = self.stitch_as("d" * 64)
        entry = stitcher.current_entry(record_, folder)
        self.assertEqual((entry["stitched"], entry["composition_rev"]), (folder.name, "d" * 64))
        self.assertTrue(Path(entry["file"]).is_file())

    def test_tampered_segment_refuses_and_leaves_nothing(self):
        video = store.segment_dir(self.root, "p", self.keys["b02"]) / "segment.mp4"
        data = bytearray(video.read_bytes())
        data[len(data) // 2] ^= 0xff
        video.write_bytes(bytes(data))
        with self.assertRaises(ValueError) as caught:
            self.go()
        self.assertIn("file hash differs", str(caught.exception))
        self.assertEqual(list((self.root / "stitched").iterdir()), [])
        self.assertFalse((self.root / "current.json").exists())

    def test_missing_segment_refuses(self):
        shutil.rmtree(store.segment_dir(self.root, "p", self.keys["b03"]))
        with self.assertRaises(ValueError):
            self.go()

    def test_rows_that_disagree_refuse_after_the_concat(self):
        path = store.segment_dir(self.root, "p", self.keys["b01"]) / "segment.framemd5"
        path.write_text("0\n1\n2\n3\n", encoding="utf8")
        with self.assertRaises(ValueError) as caught:
            self.go()
        self.assertIn("first difference at frame 0", str(caught.exception))
        self.assertEqual(list((self.root / "stitched").iterdir()), [])


class Refusals(unittest.TestCase):
    """A stale or damaged project never reaches a browser."""

    def args(self, project):
        return mock.Mock(project=str(project), profile="review", workers=1, store=None, inject_fault=None, inject_beats=None, inject_rounds=1)

    def project(self, d, lock_=None):
        project = Path(d) / "work" / "x" / "v2" / "editorial"
        project.mkdir(parents=True)
        (project / "index.html").write_text("<html>", encoding="utf8")
        store.write_json(project / "beats.lock.json", lock_ or lock_of([30]))
        return project

    def test_no_map_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(runner.Refused):
                runner.Run(self.args(self.project(d)))

    def test_map_of_another_page_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            project = self.project(d)
            store.write_json(project / "ownership.json", {"schema": 1, "html_sha256": "other", "composition_rev": "x"})
            with self.assertRaises(runner.Refused):
                runner.Run(self.args(project))

    def test_other_version_refuses_before_reading_the_project(self):
        with mock.patch.object(runner, "installed_version", return_value="0.9.0"):
            with self.assertRaises(runner.Refused):
                runner.Run(self.args("does-not-exist"))

    def test_store_sits_outside_the_project(self):
        self.assertEqual(store.root_of(ROOT / "work/beat-fixture/v2/editorial"), (ROOT / "work/beat-fixture/beat").resolve())


class NoDeclarations(unittest.TestCase):
    def test_a_project_with_no_lock_refuses_and_gives_no_traceback(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "plan.json").write_text("{}", encoding="utf8")
            (Path(d) / "index.html").write_text("<html>", encoding="utf8")
            r = subprocess.run([sys.executable, str(ROOT / "tools/beat_render/run.py"), "draft", d, "--profile", "review"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("REFUSED", r.stdout)
        self.assertNotIn("Traceback", r.stderr)

    def test_a_lock_edited_by_hand_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            lock_ = beat_lock.derive({"beats": [{"id": "b1", "start": 0, "end": 2, "layout": "split"}]}, 2, 30)
            lock_["total_frames"] = 59
            store.write_json(Path(d) / "beats.lock.json", lock_)
            with self.assertRaises(runner.Refused):
                runner.Run(mock.Mock(project=d, profile="review", workers=1, store=None, inject_fault=None, inject_beats=None, inject_rounds=1, force=False))


@NEEDS_FIXTURE
class StorePath(unittest.TestCase):
    def test_a_relative_store_is_made_absolute(self):
        """ffmpeg reads concat.txt's paths from the tmp folder, so a relative one fails after every segment rendered."""
        fixture = ROOT / "work/beat-fixture/v2/editorial"
        with tempfile.TemporaryDirectory(dir=ROOT / "work") as d:
            relative = os.path.relpath(d, os.getcwd())
            run = runner.Run(mock.Mock(project=str(fixture), profile="review", workers=1, store=relative, inject_fault=None, inject_beats=None, inject_rounds=1, force=False))
            self.assertTrue(run.root.is_absolute())
            self.assertTrue(store.segment_dir(run.root, "p", "k").is_absolute())


def receipt(folder, frame, first, problems=()):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{frame}.jpg").write_bytes(b"x")
    store.write_json(folder / f"{frame}.jpg.json", {"frame": frame, "want": {}, "problems": list(problems), "stepped_from": first})


class References(Temp):
    """Findings F3, F20 and F26: a beat's references are one set, stepped from its first frame. The same key must give the same references however the store was filled."""

    def setUp(self):
        super().setUp()
        self.run = runner.Run.__new__(runner.Run)
        self.run.root, self.run.profile_hash, self.run.events = self.root, "p" * 16, []
        self.run.keys = {"b01": "k1"}
        self.run.map = {"owners": []}
        self.beat = {"beat_id": "b01", "start_frame": 100, "end_frame": 130, "layout": "split"}
        self.folder = store.refs_dir(self.root, "p" * 16, "k1")

    def all_good(self):
        for frame in (100, 114, 129):
            receipt(self.folder, frame, 100)

    def test_a_complete_set_needs_nothing(self):
        self.all_good()
        self.assertEqual(self.run.ref_jobs([self.beat]), [])

    def test_one_missing_sample_recaptures_the_whole_set_from_the_first_frame(self):
        self.all_good()
        (self.folder / "114.jpg").unlink()
        jobs = self.run.ref_jobs([self.beat])
        self.assertEqual([j["frame"] for j in jobs], [100, 114, 129])
        self.assertTrue(all(j["from"] == 100 and j["beat"] == "b01" for j in jobs))

    def test_a_reference_filled_in_from_elsewhere_is_not_valid(self):
        """The b19 fault: a clean receipt with no sign of how the page got there."""
        self.all_good()
        store.write_json(self.folder / "129.jpg.json", {"frame": 129, "want": {}, "problems": []})
        self.assertEqual(len(self.run.ref_jobs([self.beat])), 3)

    def test_a_reference_stepped_from_another_frame_is_not_valid(self):
        self.all_good()
        receipt(self.folder, 129, 114)
        self.assertEqual(len(self.run.ref_jobs([self.beat])), 3)

    def test_a_failed_probe_recaptures(self):
        self.all_good()
        receipt(self.folder, 114, 100, ["viewport 800x600"])
        self.assertEqual(len(self.run.ref_jobs([self.beat])), 3)

    def test_a_suspect_frame_joins_the_set(self):
        self.all_good()
        self.assertEqual([j["frame"] for j in self.run.ref_jobs([self.beat], {"b01": [120]})], [100, 114, 120, 129])

    def test_load_stills_treats_an_unstepped_reference_as_none(self):
        self.all_good()
        store.write_json(self.folder / "129.jpg.json", {"frame": 129, "want": {}, "problems": []})
        with mock.patch.object(sentinel, "decode_stills", side_effect=lambda paths, w, h: [noise(9)] * len(paths)):
            stills = sentinel.load_stills(self.folder, [100, 129], W, H)
        self.assertIsNotNone(stills[100])
        self.assertIsNone(stills[129])

    def test_refs_mjs_turns_sessions_over_between_beats_only(self):
        text = (ROOT / "tools/beat_render/refs.mjs").read_text(encoding="utf8")
        self.assertIn("if(r.beat!==beat){", text)
        self.assertIn("stepped_from:r.from", text)
        self.assertNotIn("if(session&&used>=job.page_frames){await closeSession(session);session=null;}\n  if(!session)", text)


class Inspect(Temp):
    def test_a_segment_that_will_not_decode_is_a_problem_to_retry(self):
        run = runner.Run.__new__(runner.Run)
        run.events, run.frame_size = [], (W, H)
        folder = Path(self.dir.name) / "segment-under-test"
        folder.mkdir()
        video = folder / "segment.mp4"
        encode(video, [noise(i) for i in range(30)])
        video.write_bytes(video.read_bytes()[:video.stat().st_size // 2])
        store.write_json(str(video) + ".json", {"injected": None})
        seen = run.inspect({"beat_id": "b01", "start_frame": 0, "end_frame": 30}, folder)
        self.assertIn("does not decode", seen["problem"])
        self.assertTrue(seen["started"])

    def test_a_worker_that_left_no_result_says_so(self):
        run = runner.Run.__new__(runner.Run)
        seen = run.inspect({"beat_id": "b01", "start_frame": 0, "end_frame": 30}, Path(self.dir.name))
        self.assertEqual(seen["problem"], "no result from the worker")


class Publish(Temp):
    """What render_round may publish, with the capture and decode stubbed."""

    def setUp(self):
        super().setUp()
        self.lock = lock_of([30, 30])
        self.run = runner.Run.__new__(runner.Run)
        run = self.run
        run.root, run.lock, run.project = self.root, self.lock, Path(self.dir.name)
        run.beats = {b["beat_id"]: b for b in self.lock["beats"]}
        run.keys = {"b01": "k1", "b02": "k2"}
        run.profile, run.profile_hash, run.engine, run.workers, run.events = {"name": "review", "page_rotate_frames": 240}, "p", "e", 2, []
        run.map, run.timings, run.inject, run.stamp, run.plan, run.force = {"composition_rev": "c"}, {}, None, "stamp", "plan", False
        run.frame_size, run.region_top = (W, H), H // 2
        run.seen = {}
        run.verdicts = {}
        run.ref_jobs = lambda *a: []
        run.start_refs = lambda *a: None
        run.inspect = lambda beat, folder: self.fake_seen(beat, folder)
        run.judge = lambda beat, seen: run.verdicts[beat["beat_id"]]
        self.patches = [mock.patch.object(runner, "node", return_value=mock.Mock()), mock.patch.object(runner, "finish_all", return_value=[0]),
                        mock.patch.object(runner.ownership, "load", return_value={"composition_rev": "c"}), mock.patch.object(runner, "project_stamp", return_value="stamp")]
        for patch in self.patches:
            patch.start()
            self.addCleanup(patch.stop)

    def fake_seen(self, beat, folder):
        (folder / "segment.mp4").write_bytes(b"video")
        return {"problem": None, "started": True, "rows": ["aa"] * 30, "picked": {}, "suspects": [], "stream": {"packets": 30},
                "result": {"page_frames_before": 0, "capture_ms": 1, "injected": self.run.seen.get(beat["beat_id"])}}

    def verdict(self, status):
        return {"status": status, "sampled": [0], "failed": [{"frame": 0}] if status == "FAIL" else [], "unverified": [], "unsampled": 29, "min_psnr": 40, "min_psnr_region": 40, "psnr_min": 34, "max_block": 3, "block_max": 10, "clip_suspects": 0}

    def go(self):
        tmp = store.new_tmp(self.root)
        return self.run.render_round(tmp, ["b01", "b02"], 0)

    def test_clean_beats_publish(self):
        self.run.verdicts = {"b01": self.verdict("PASS"), "b02": self.verdict("PASS")}
        passed, failures = self.go()
        self.assertEqual(sorted(passed), ["b01", "b02"])
        self.assertEqual(failures, {})

    def test_a_beat_with_no_valid_reference_is_never_published(self):
        unverified = {**self.verdict("UNVERIFIED"), "unverified": [12]}
        self.run.verdicts = {"b01": self.verdict("PASS"), "b02": unverified}
        passed, failures = self.go()
        self.assertEqual(passed, ["b01"])
        self.assertIn("no valid reference", failures["b02"]["why"])
        self.assertIsNone(store.find(self.root, "p", "k2"))

    def test_a_dead_references_process_is_rerun_before_anything_is_judged(self):
        """References arrive on the second capture, so a judge that ran first would have seen none."""
        calls = []
        have = {"refs": False}

        def jobs(*a):
            return [] if have["refs"] else [{"frame": 0}]

        def start(tmp, rows, name):
            calls.append(name)
            return mock.Mock() if rows else None

        def finish(procs, seconds):
            if len(calls) == 2:
                have["refs"] = True
            return [1] * len(procs)

        self.run.ref_jobs, self.run.start_refs = jobs, start
        self.run.judge = lambda beat, seen: self.verdict("PASS") if have["refs"] else self.verdict("UNVERIFIED")
        with mock.patch.object(runner, "finish_all", finish):
            passed, failures = self.go()
        self.assertEqual(calls, ["round0-refs", "round0-refs-again"])
        self.assertEqual(sorted(passed), ["b01", "b02"])
        self.assertEqual(failures, {})

    def test_references_that_never_come_fail_the_round(self):
        self.run.ref_jobs = lambda *a: [{"frame": 0}]
        self.run.start_refs = lambda *a: mock.Mock()
        self.run.verdicts = {"b01": self.verdict("UNVERIFIED"), "b02": self.verdict("UNVERIFIED")}
        passed, failures = self.go()
        self.assertEqual(passed, [])
        self.assertEqual(sorted(failures), ["b01", "b02"])

    def test_a_segment_that_will_not_decode_is_retried_not_a_crash(self):
        self.run.inspect = lambda beat, folder: {"problem": "does not decode: x", "started": True}
        passed, failures = self.go()
        self.assertEqual(passed, [])
        self.assertIn("does not decode", failures["b01"]["why"])

    def test_failed_sample_is_not_published(self):
        self.run.verdicts = {"b01": self.verdict("FAIL"), "b02": self.verdict("PASS")}
        passed, failures = self.go()
        self.assertEqual(passed, ["b02"])
        self.assertIn("sentinel failed", failures["b01"]["why"])
        self.assertIsNone(store.find(self.root, "p", "k1"))
        self.assertFalse(store.segment_dir(self.root, "p", "k1").exists())

    def test_a_failed_sample_drops_that_beats_references(self):
        """A bad stored reference used to be permanent: every retry was judged against it."""
        self.run.ref_path = runner.Run.ref_path.__get__(self.run)
        receipt(store.refs_dir(self.root, "p", "k1"), 5, 0)
        receipt(store.refs_dir(self.root, "p", "k2"), 5, 30)
        self.run.verdicts = {"b01": self.verdict("FAIL"), "b02": self.verdict("PASS")}
        self.go()
        self.assertFalse((store.refs_dir(self.root, "p", "k1") / "5.jpg.json").exists())
        self.assertTrue((store.refs_dir(self.root, "p", "k2") / "5.jpg.json").exists())

    def test_injected_fault_that_passed_is_never_published(self):
        self.run.seen = {"b01": "viewport"}
        self.run.verdicts = {"b01": self.verdict("PASS"), "b02": self.verdict("PASS")}
        passed, failures = self.go()
        self.assertEqual(passed, ["b02"])
        self.assertTrue(failures["b01"]["undetected"])
        self.assertIsNone(store.find(self.root, "p", "k1"))

    def test_project_that_moved_publishes_nothing(self):
        self.run.verdicts = {"b01": self.verdict("PASS"), "b02": self.verdict("PASS")}
        with mock.patch.object(runner, "project_stamp", return_value="moved"):
            with self.assertRaises(runner.Refused):
                self.go()
        self.assertIsNone(store.find(self.root, "p", "k1"))
        self.assertIsNone(store.find(self.root, "p", "k2"))

    def test_retries_stop_after_two_and_name_the_beat(self):
        self.run.render_round = mock.Mock(return_value=([], {"b01": {"why": "x", "started": True}}))
        log, unresolved = self.run.render(store.new_tmp(self.root), ["b01"])
        self.assertEqual(self.run.render_round.call_count, 1 + runner.RETRIES)
        self.assertEqual(unresolved, ["b01"])
        self.assertEqual(len(log), 3)


class Flow(Temp):
    """The order of a run, with the capture, stitch and checks stubbed."""

    def setUp(self):
        super().setUp()
        self.lock = lock_of([30, 30])
        run = self.run = runner.Run.__new__(runner.Run)
        run.root, run.lock, run.project, run.timings = self.root, self.lock, Path(self.dir.name), {}
        run.beats = {b["beat_id"]: b for b in self.lock["beats"]}
        run.keys = {"b01": "k1", "b02": "k2"}
        run.profile, run.profile_hash, run.engine, run.workers, run.events, run.stamp = {"name": "review", "width": W, "height": H}, "p", "e", 2, [], "stamp"
        run.map, run.inject = {"composition_rev": "c"}, None
        run.ref_jobs, run.start_refs = (lambda *a: []), (lambda *a: None)
        run.lock["revision"] = "l"
        self.order = []
        self.folder = self.root / "stitched" / "review-x"
        self.folder.mkdir()
        self.record = {"file": "review.mp4", "file_sha256": "s" * 64, "composition_rev": "c", "lock_revision": "l"}
        run.owner_audit = lambda: self.order.append("audit") or "PASS"
        run.render = lambda tmp, todo: (self.order.append("render"), ([{"round": 0, "beats": todo, "published": todo, "failures": {}}], []))[1]
        run.run_checks = lambda picture, beats: self.order.append("checks") or ({"source": "UNVERIFIED", "output": "UNVERIFIED"}, [])
        real = store.set_current
        self.patches = [mock.patch.object(runner.stitcher, "audio_bed", return_value="bed"), mock.patch.object(runner.ownership, "load", return_value={"composition_rev": "c"}),
                        mock.patch.object(runner, "project_stamp", return_value="stamp"), mock.patch.object(runner.stitcher, "stitch", side_effect=lambda *a: self.order.append("stitch") or (self.record, self.folder)),
                        mock.patch.object(runner.store, "find", return_value={"beat_id": "b01", "sentinel": {"status": "PASS", "sampled": [0, 1], "unsampled": 28, "min_psnr": 40, "min_psnr_region": 40}}),
                        mock.patch.object(runner.store, "set_current", side_effect=lambda *a: self.order.append("current") or real(*a))]
        for patch in self.patches:
            patch.start()
            self.addCleanup(patch.stop)

    def go(self, todo=("b01",), **kwargs):
        self.change = {"rendered": list(todo)}
        return runner.render_and_finish(self.run, self.change, store.new_tmp(self.root), list(todo), time.perf_counter(), **kwargs)

    def records(self):
        return store.read_json(sorted((self.root / "changes").glob("*.json"))[-1])

    def test_the_audit_runs_first_and_current_moves_last(self):
        self.assertEqual(self.go(), 0)
        self.assertEqual(self.order, ["audit", "render", "stitch", "checks", "current"])
        self.assertEqual(store.read_json(self.root / "current.json")["review"]["stitched"], "review-x")

    def test_a_failed_audit_renders_nothing_and_says_what_it_would_have(self):
        self.run.owner_audit = lambda: "FAIL"
        self.assertEqual(self.go(), 1)
        self.assertEqual(self.order, [])
        record = self.records()
        self.assertEqual((record["status"], record["owner_audit"], record["rendered"], record["would_render"]), ("FAIL", "FAIL", [], ["b01"]))
        self.assertFalse((self.root / "current.json").exists())

    def test_an_audit_that_could_not_run_stops_too(self):
        self.run.owner_audit = lambda: "UNVERIFIED"
        self.assertEqual(self.go(), 1)
        self.assertEqual(self.order, [])

    def test_failed_checks_leave_current_where_it_was(self):
        store.set_current(self.root, "review", {"stitched": "review-old"}, "UNVERIFIED")
        self.run.run_checks = lambda picture, beats: ({"source": "PASS", "output": "FAIL"}, [])
        self.assertEqual(self.go(), 1)
        self.assertEqual(store.read_json(self.root / "current.json")["review"]["stitched"], "review-old")
        self.assertEqual(store.read_json(self.root / "last_attempt.json")["review"]["stitched"], "review-x")
        self.assertFalse(self.records()["current_moved"])

    def test_under_invalidation_leaves_current_where_it_was_with_clean_checks(self):
        self.assertEqual(self.go(failed=True), 1)
        self.assertFalse((self.root / "current.json").exists())

    def test_a_stitch_refusal_writes_a_record(self):
        with mock.patch.object(runner.stitcher, "stitch", side_effect=ValueError("b02: key is stale")):
            self.assertEqual(self.go(), 1)
        record = self.records()
        self.assertEqual(record["status"], "FAIL")
        self.assertIn("key is stale", record["refused"])

    def test_a_stitch_that_ffmpeg_refuses_writes_a_record(self):
        with mock.patch.object(runner.stitcher, "stitch", side_effect=subprocess.CalledProcessError(1, "ffmpeg")):
            self.assertEqual(self.go(), 1)
        self.assertEqual(self.records()["status"], "FAIL")

    def test_the_sentinel_block_says_it_is_from_render_time(self):
        self.go()
        record = self.records()
        self.assertNotIn("sentinel", record)
        self.assertEqual(record["sentinel_at_render"]["frames_sampled"], 4)

    def test_missing_references_are_their_own_result_and_never_exit_0(self):
        self.run.ref_jobs = lambda *a: [{"frame": 7}, {"frame": 7}, {"frame": 9}]
        self.run.start_refs = lambda *a: mock.Mock()
        with mock.patch.object(runner, "finish_all", return_value=[0]):
            self.assertEqual(self.go(), 3)
        self.assertEqual(self.records()["references_missing"], [7, 9])

    def test_a_check_that_did_not_finish_stays_out_of_current_and_exits_3(self):
        store.set_current(self.root, "review", {"stitched": "review-old"}, "UNVERIFIED")
        self.run.run_checks = lambda picture, beats: ({"source": "UNVERIFIED", "output": "UNVERIFIED"}, ["source", "output"])
        self.assertEqual(self.go(), 3)
        record = self.records()
        self.assertEqual(record["checks_unfinished"], ["source", "output"])
        self.assertFalse(record["current_moved"])
        self.assertEqual(store.read_json(self.root / "current.json")["review"]["stitched"], "review-old")
        self.assertEqual(store.read_json(self.root / "last_attempt.json")["review"]["stitched"], "review-x")

    def test_a_hang_reaches_the_record_through_the_real_checks(self):
        del self.run.run_checks
        self.run.project = Path(self.dir.name)
        with mock.patch.object(runner, "check_status", return_value=("UNVERIFIED", False)):
            self.assertEqual(self.go(), 3)
        self.assertEqual(self.records()["checks_unfinished"], ["source", "output"])

    def test_one_check_unfinished_is_enough(self):
        self.run.run_checks = lambda picture, beats: ({"source": "UNVERIFIED", "output": "UNVERIFIED"}, ["output"])
        self.assertEqual(self.go(), 3)
        self.assertFalse((self.root / "current.json").exists())

    def test_a_failed_check_is_still_a_failure_with_one_unfinished(self):
        self.run.run_checks = lambda picture, beats: ({"source": "FAIL", "output": "UNVERIFIED"}, ["output"])
        self.assertEqual(self.go(), 1)

    def scoped(self, change):
        seen = []
        self.run.run_checks = lambda picture, beats: seen.append(beats) or ({"source": "UNVERIFIED", "output": "UNVERIFIED"}, [])
        self.change = change
        runner.render_and_finish(self.run, change, store.new_tmp(self.root), [], time.perf_counter())
        return seen[0]

    def test_the_source_check_covers_a_touched_beat_that_reused_its_segment(self):
        self.assertEqual(self.scoped({"rendered": ["b02"], "invalidate": {"beats": ["b01", "b02"]}}), ["b01", "b02"])

    def test_the_source_check_also_covers_what_rendered_untouched(self):
        self.assertEqual(self.scoped({"rendered": ["b02"], "invalidate": {"beats": ["b01"]}}), ["b01", "b02"])

    def test_a_draft_has_no_invalidate_so_its_scope_is_what_rendered(self):
        self.assertEqual(self.scoped({"rendered": ["b02"]}), ["b02"])

    def test_nothing_touched_and_nothing_rendered_is_an_empty_scope(self):
        self.assertEqual(self.scoped({"rendered": [], "invalidate": {"beats": []}}), [])

    def reports(self, *rounds):
        """Each run of output.py finds the next of these. rounds: (status, failed_beats)."""
        report = self.root / "checks" / "c" / f"output-{'s' * 16}.json"
        report.parent.mkdir(parents=True)
        rows = iter(rounds)
        calls = []

        def output(picture):
            status, failed = next(rows)
            calls.append(status)
            store.write_json(report, {"checks": {"O5": {"status": "FAIL" if failed else "PASS", "failed_beats": failed}}})
            return status, True

        self.run.output_check = output
        self.run.source_check = lambda picture, beats: ("UNVERIFIED", True)
        del self.run.run_checks
        return calls

    def poisoned(self):
        self.run.recapture = mock.Mock()
        self.run.forget_refs = mock.Mock()

    def test_o5_failing_on_a_reused_beat_recaptures_its_references_once_and_compares_again(self):
        calls = self.reports(("FAIL", ["b02"]), ("UNVERIFIED", []))
        self.poisoned()
        self.assertEqual(self.go(("b01",)), 0)
        self.assertEqual(calls, ["FAIL", "UNVERIFIED"])
        self.run.forget_refs.assert_called_once_with(self.run.beats["b02"])
        record = self.records()
        self.assertEqual(record["references_recaptured"], ["b02"])
        self.assertEqual(record["checks"]["output"], "UNVERIFIED")
        self.assertEqual(store.read_json(self.root / "current.json")["review"]["stitched"], "review-x")

    def test_a_real_defect_still_fails_after_the_recapture_and_runs_once_more_at_most(self):
        calls = self.reports(("FAIL", ["b02"]), ("FAIL", ["b02"]))
        self.poisoned()
        self.assertEqual(self.go(("b01",)), 1)
        self.assertEqual(calls, ["FAIL", "FAIL"])
        self.assertFalse((self.root / "current.json").exists())

    def test_a_beat_that_just_rendered_is_not_recaptured(self):
        calls = self.reports(("FAIL", ["b01"]))
        self.poisoned()
        self.assertEqual(self.go(("b01",)), 1)
        self.assertEqual(calls, ["FAIL"])
        self.run.forget_refs.assert_not_called()

    def test_a_failure_that_is_not_o5_recaptures_nothing(self):
        calls = self.reports(("FAIL", []))
        self.poisoned()
        self.assertEqual(self.go(("b01",)), 1)
        self.assertEqual(calls, ["FAIL"])
        self.run.forget_refs.assert_not_called()

    def test_every_later_round_counts_as_a_retry_started_or_not(self):
        self.run.render = lambda tmp, todo: ([{"round": 0, "beats": ["b01", "b02"], "published": ["b02"], "failures": {"b01": {"why": "no result from the worker", "started": False}}},
                                              {"round": 1, "beats": ["b01"], "published": ["b01"], "failures": {}}], [])
        self.go(("b01", "b02"))
        self.assertEqual(self.records()["retried"], ["b01"])


class QualifyCompare(unittest.TestCase):
    def test_runs_under_30_and_frame_pairing(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            clean = [noise(i) for i in range(8)]
            reference = d / "ref.mp4"
            encode(reference, clean)
            first = d / "a.mp4"
            encode(first, clean[2:4])
            second = d / "b.mp4"
            encode(second, [clean[4], plain(0), plain(0), clean[7]])
            result = qualify.compare_chunks([{"start": 2, "path": str(first)}, {"start": 4, "path": str(second)}], reference, W, H, H // 2)
        self.assertEqual(result["frames"], 6)
        self.assertEqual(result["runs_under_30"], [[5, 7]])


if __name__ == "__main__":
    unittest.main()
