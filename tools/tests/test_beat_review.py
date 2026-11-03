"""Rounds, notes, waivers and the approval check: tools/beat_review/review.py and approval.py, and the waivers in tools/beat_check/output.py.

Usage: python tools/tests/test_beat_review.py

Logic only, in temp folders, with real small videos made by ffmpeg, and no browser. The real runs, three note rounds, a go-back, planted cache errors and clean reruns, are in
stage1/phase3-rounds.md, with their scripts in stage1/phase3-evidence/. The fixture is never written.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent.parent
NEEDS_FIXTURE = unittest.skipUnless((ROOT / "work/beat-fixture/v2/editorial/beats.lock.json").is_file(),
                                    "needs work/beat-fixture, the author's 107 s test edit, which does not ship")
sys.path[:0] = [str(ROOT / "tools" / "beat_review"), str(ROOT / "tools" / "beat_check"), str(ROOT / "tools" / "beat_render"), str(ROOT / "tools")]
import approval
import numpy as np
import output
import review
import run as runner
import sentinel
import sound_mix
import store
from common import sha

WIDTH, HEIGHT, FRAMES = 96, 160, 60


def video(path, shift=0, spot=None, count=FRAMES, retime=None):
    """A clip whose frame n has mean brightness 16 + 3n. spot is (first, last): frames that get a white box. retime stretches timestamps, which frame pairing must not notice."""
    boxes = f",drawbox=x=20:y=30:w=24:h=24:color=white:t=fill:enable='between(n,{spot[0]},{spot[1]})'" if spot else ""
    setpts = f",setpts=PTS*{retime}" if retime else ""
    source = f"color=c=black:s={WIDTH}x{HEIGHT}:r=30:d=4,format=yuv420p,geq=lum='16+3*(N+{shift})':cb=128:cr=128{boxes}{setpts}"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", source, "-frames:v", str(count), "-c:v", "libx264", "-preset", "ultrafast", "-qp", "0", "-pix_fmt", "yuv420p", "-bf", "0", str(path)], check=True)


class Project:
    """A real project shape, with a valid ownership map and pictures in a real store layout."""

    def __init__(self, base):
        self.home = Path(base) / "work" / "t"
        self.project = self.home / "v2" / "editorial"
        (self.project / "tools_local").mkdir(parents=True)
        (self.home / "raw").mkdir()
        self.root = self.home / "beat"
        store.open_store(self.root)
        self.words = [["hello", 0.0, 0.5, 0], ["there", 0.6, 1.0, 1], ["world", 1.5, 1.9, 2]]
        (self.home / "raw" / "cut_words.json").write_text(json.dumps(self.words), encoding="utf8")
        (self.home / "beats.json").write_text('{"beats": []}', encoding="utf8")
        (self.project / "plan.json").write_text(json.dumps({"beats": [{"id": "b01", "say": "one"}, {"id": "b02", "say": "two"}]}), encoding="utf8")
        (self.project / "tools_local" / "scenes.py").write_text("word = 'a'\n", encoding="utf8")
        self.lock = {"revision": "lock1", "fps": 30, "total_frames": FRAMES, "beats": [{"beat_id": "b01", "start_frame": 0, "end_frame": 30, "layout": "split"}, {"beat_id": "b02", "start_frame": 30, "end_frame": 60, "layout": "full"}]}
        store.write_json(self.project / "beats.lock.json", self.lock)
        self.pictures = 0
        self.build("v1")

    def build(self, html):
        (self.project / "index.html").write_text(html, encoding="utf8")
        body = {"schema": 1, "html_sha256": sound_mix.file_hash(self.project / "index.html")}
        self.map = {**body, "composition_rev": sha(body)}
        store.write_json(self.project / "ownership.json", self.map)

    def picture(self, status="UNVERIFIED", keys=("k1", "k2"), checks=True, where="current.json", **clip):
        """Stitches a picture: a real file, its records, and check reports that pass unless told otherwise."""
        self.pictures += 1
        tmp = self.root / "tmp" / f"p{self.pictures}.mp4"
        video(tmp, shift=self.pictures, **clip)
        h = sound_mix.file_hash(tmp)
        rev = self.map["composition_rev"]
        folder = self.root / "stitched" / f"review-{h[:16]}-{rev[:16]}"
        folder.mkdir()
        shutil.move(tmp, folder / "review.mp4")
        beats = [{"beat_id": b["beat_id"], "key": k, "content_hash": k, "start_frame": b["start_frame"], "end_frame": b["end_frame"]} for b, k in zip(self.lock["beats"], keys)]
        store.write_json(folder / "stitch.json", {"file": "review.mp4", "file_sha256": h, "composition_rev": rev, "lock_revision": "lock1", "profile": "review", "beats": beats})
        store.write_json(folder / "beats.lock.json", self.lock)
        shutil.copy(self.project / "ownership.json", folder / "ownership.json")
        entry = {"stitched": folder.name, "file": str(folder / "review.mp4"), "file_sha256": h, "composition_rev": rev, "lock_revision": "lock1", "status": status}
        store.write_json(self.root / where, {**store.read_json(self.root / where, {}), "review": entry})
        if where == "current.json":
            attempts = store.read_json(self.root / "last_attempt.json", {})
            attempts.pop("review", None)
            store.write_json(self.root / "last_attempt.json", attempts)
        if checks:
            self.report(h, rev)
        return h

    def report(self, h, rev, output_checks=None, events=()):
        folder = self.root / "checks" / rev[:16]
        folder.mkdir(parents=True, exist_ok=True)
        cs = {name: {"status": "PASS", "problems": []} for name in ("binding", "O1", "O2", "O3")}
        cs["O4"] = {"status": "PASS", "problems": [], "flash": {"status": "PASS", "flashes": [], "double_cuts": []}}
        cs["O5"] = {"status": "PASS", "failed": [], "failed_count": 0, "clip_suspects_uncleared": [], "frames_no_reference": 0, "frames_compared": 9}
        cs["O6"] = {"status": "PASS", "blocking": []}
        cs["loudness"] = {"status": "UNVERIFIED"}
        store.write_json(folder / f"output-{h[:16]}.json", {"checks": {**cs, **(output_checks or {})}, "waived": []})
        store.write_json(folder / f"source-{h[:16]}.json", {"findings": [], "events": list(events)})


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)  # a still may still be decoding
        self.p = Project(self.dir.name)
        self.project = self.p.project

    def tearDown(self):
        self.dir.cleanup()


class Waivers(unittest.TestCase):
    def report(self):
        return {"checks": {"O4": {"status": "FAIL", "problems": [], "flash": {"status": "FAIL", "flashes": [], "double_cuts": [{"frames": [1611, 1612]}]}},
                           "O5": {"status": "PASS", "failed": [], "failed_count": 0, "clip_suspects_uncleared": [], "frames_no_reference": 0, "frames_compared": 9}}}

    def record(self):
        return {"beats": [{"beat_id": "b27", "key": "k"}]}

    def test_a_waived_double_cut_stops_failing_and_is_still_reported(self):
        report = self.report()
        output.apply_waivers(report, [{"check": "O4.double_cut", "frames": [1612, 1611], "why": "looked", "source": "fixture.json"}], self.record())
        self.assertEqual(report["checks"]["O4"]["status"], "PASS")
        self.assertEqual(report["waived"], [{"check": "O4.double_cut", "frames": [1611, 1612], "why": "looked", "from": "fixture.json"}])

    def test_other_frames_are_not_waived(self):
        report = self.report()
        output.apply_waivers(report, [{"check": "O4.double_cut", "frames": [1611], "why": "x", "source": "s"}], self.record())
        self.assertEqual(report["checks"]["O4"]["status"], "FAIL")
        self.assertEqual(report["waived"], [])

    def test_another_check_is_not_waived(self):
        report = self.report()
        output.apply_waivers(report, [{"check": "O4.flash", "frames": [1611, 1612], "why": "x", "source": "s"}], self.record())
        self.assertEqual(report["checks"]["O4"]["status"], "FAIL")

    def test_one_of_two_double_cuts_still_fails(self):
        report = self.report()
        report["checks"]["O4"]["flash"]["double_cuts"].append({"frames": [20, 21]})
        output.apply_waivers(report, [{"check": "O4.double_cut", "frames": [1611, 1612], "why": "x", "source": "s"}], self.record())
        self.assertEqual(report["checks"]["O4"]["status"], "FAIL")
        self.assertEqual(report["checks"]["O4"]["flash"]["double_cuts"], [{"frames": [20, 21]}])
        self.assertEqual(len(report["waived"]), 1)

    def test_a_join_problem_is_never_excused_by_a_flash_waiver(self):
        report = self.report()
        report["checks"]["O4"]["problems"] = ["b01|b02: frame 29 differs"]
        output.apply_waivers(report, [{"check": "O4.double_cut", "frames": [1611, 1612], "why": "x", "source": "s"}], self.record())
        self.assertEqual(report["checks"]["O4"]["status"], "FAIL")

    def test_a_waiver_lapses_when_its_beat_is_another_segment(self):
        waiver = [{"check": "O4.double_cut", "frames": [1611, 1612], "why": "x", "source": "s", "keys": {"b27": "old"}}]
        report = self.report()
        output.apply_waivers(report, waiver, self.record())
        self.assertEqual(report["checks"]["O4"]["status"], "FAIL")

    def test_a_waiver_holds_for_a_final_of_the_same_composition_and_no_other(self):
        row = {"check": "O4.double_cut", "frames": [10, 11], "why": "one card rising", "keys": {"b01": "review-key"}, "composition_rev": "rev1", "profile": "review", "source": "waivers.json"}
        final = {"profile": "final", "composition_rev": "rev1"}
        self.assertIsNotNone(output.waiver_for("O4.double_cut", [10, 11], [row], {"b01": "final-key"}, final))
        self.assertIsNone(output.waiver_for("O4.double_cut", [10, 11], [row], {"b01": "final-key"}, {**final, "composition_rev": "rev2"}), "an edit brings it back")
        self.assertIsNone(output.waiver_for("O4.double_cut", [10, 11], [row], {"b01": "other"}, {"profile": "review", "composition_rev": "rev1"}), "at its own profile the key still decides")
        self.assertIsNone(output.waiver_for("O4.double_cut", [20, 22], [row], {"b01": "final-key"}, final), "other frames, as at another frame rate")
        old = {k: v for k, v in row.items() if k not in ("composition_rev", "profile")}
        self.assertIsNone(output.waiver_for("O4.double_cut", [10, 11], [old], {"b01": "final-key"}, final))

    def test_a_waived_sample_clears_o5_only_when_nothing_is_left(self):
        report = self.report()
        report["checks"]["O4"] = {"status": "PASS", "problems": [], "flash": {"status": "PASS", "flashes": [], "double_cuts": []}}
        report["checks"]["O5"].update(status="FAIL", failed=[{"frame": 5}, {"frame": 6}], failed_count=2)
        record = {**self.record(), "file_sha256": "render"}
        output.apply_waivers(report, [{"check": "O5.sample", "frames": [5], "why": "x", "source": "s", "picture_sha": "render"}], record)
        self.assertEqual(report["checks"]["O5"]["status"], "FAIL")
        output.apply_waivers(report, [{"check": "O5.sample", "frames": [6], "why": "x", "source": "s", "picture_sha": "render"}], record)
        self.assertEqual(report["checks"]["O5"]["status"], "PASS")

    def test_both_files_are_read_and_motionlint_rows_are_left_to_conform(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d) / "x"
            project = home / "v2" / "editorial"
            project.mkdir(parents=True)
            (home / "fixture.json").write_text(json.dumps({"waivers": [{"check": "motionlint", "starts_with": "face_full:", "why": "h"}, {"check": "O4.double_cut", "frames": [1], "why": "f"}]}), encoding="utf8")
            (home / "waivers.json").write_text(json.dumps([{"check": "O5.sample", "frames": [2], "why": "c"}]), encoding="utf8")
            rows = output.waivers_of(project, home / "beat")
        self.assertEqual([(w["check"], w["source"]) for w in rows], [("O5.sample", "waivers.json"), ("O4.double_cut", "fixture.json")])

    @NEEDS_FIXTURE
    def test_the_fixture_waiver_is_the_agreed_one(self):
        rows = [w for w in store.read_json(ROOT / "work" / "beat-fixture" / "fixture.json")["waivers"] if w["check"] == "O4.double_cut"]
        self.assertEqual(rows, [{"check": "O4.double_cut", "frames": [1611, 1612], "why": "Claude looked at frames 1608 to 1615: one card rising smoothly. Test bed only."}])


class Notes(Base):
    def setUp(self):
        super().setUp()
        self.h = self.p.picture()

    def note(self, **fields):
        return review.add_note(self.project, {"text": "move it", "frame": 12, "scope": "frame", "picture_sha": self.h, **fields})

    def test_a_note_is_bound_to_its_picture_frame_time_and_word(self):
        n = self.note(frame=33)
        self.assertEqual((n["picture_sha"], n["composition_rev"], n["lock_revision"]), (self.h, self.p.map["composition_rev"], "lock1"))
        self.assertEqual((n["frame"], n["time"], n["beat_id"]), (33, 1.1, "b02"))
        self.assertEqual((n["word_id"], n["word"]), (1, "there"))
        rows = (self.p.home / "notes.jsonl").read_text(encoding="utf8").splitlines()
        self.assertEqual(json.loads(rows[0])["id"], n["id"])

    def test_the_word_between_two_words_is_the_nearest(self):
        self.assertEqual(review.nearest_word(self.p.words, 1.4)[3], 2)
        self.assertEqual(review.nearest_word(self.p.words, 0.54)[3], 0)
        self.assertIsNone(review.nearest_word([], 1))

    def test_a_note_returns_in_under_100_ms_before_its_still_exists(self):
        times = []
        for frame in range(1, 6):
            started = time.perf_counter()
            self.note(frame=frame)
            times.append(time.perf_counter() - started)
        self.assertLess(sorted(times)[2], 0.1, times)

    def test_the_still_is_the_frame_by_number_not_a_neighbour(self):
        n = self.note(frame=40)
        deadline = time.time() + 20
        while not Path(n["still"]).is_file() or Path(n["still"]).stat().st_size == 0:
            self.assertLess(time.time(), deadline, "no still")
            time.sleep(0.05)
        time.sleep(0.3)
        from PIL import Image
        mean = float(np.asarray(Image.open(n["still"]).convert("L")).mean())
        want = float(np.asarray(Image.open(self.exact_frame(40)).convert("L")).mean())
        other = float(np.asarray(Image.open(self.exact_frame(41)).convert("L")).mean())
        self.assertLess(abs(mean - want), abs(mean - other))

    def exact_frame(self, n):
        out = Path(self.dir.name) / f"exact{n}.png"
        record = review.picture(self.project)
        data = sentinel.scan(record["file"], WIDTH, HEIGHT, [n])[1][n]
        from PIL import Image
        Image.fromarray(approval.rgb(data, WIDTH, HEIGHT)).save(out)
        return out

    def test_a_whole_video_note_has_no_frame_and_no_still(self):
        n = review.add_note(self.project, {"text": "good pace", "scope": "video", "picture_sha": self.h})
        self.assertEqual((n["frame"], n["time"], n["still"], n["word_id"]), (None, None, None, None))

    def test_refusals(self):
        for bad in ({"text": "  "}, {"frame": 60}, {"frame": -1}, {"frame": "3"}, {"frame": True}, {"scope": "beat"}, {"picture_sha": "nope"}):
            with self.assertRaises(ValueError, msg=bad):
                self.note(**bad)
        self.assertFalse((self.p.home / "notes.jsonl").exists())

    def test_a_note_on_an_older_picture_is_flagged_and_never_carried_into_a_round(self):
        new = self.p.picture()
        old = self.note()
        fresh = self.note(picture_sha=new)
        self.assertTrue(old["older_picture"])
        self.assertFalse(fresh["older_picture"])
        frozen = review.freeze(self.project)
        self.assertEqual([n["id"] for n in frozen["notes"]], [fresh["id"]])
        self.assertEqual([n["id"] for n in frozen["flagged"]], [old["id"]])
        self.assertTrue(frozen["flagged"][0]["older_picture"])

    def test_a_round_freezes_one_set_and_a_later_note_is_not_in_it(self):
        a = self.note()
        first = review.freeze(self.project)
        self.assertEqual(review.freeze(self.project)["notes_rev"], first["notes_rev"])
        self.note(text="another")
        self.assertNotEqual(review.freeze(self.project)["notes_rev"], first["notes_rev"])
        self.assertEqual([n["id"] for n in first["notes"]], [a["id"]])

    def test_a_note_a_round_closed_stays_as_evidence_and_is_not_frozen_again(self):
        n = self.note()
        frozen = review.freeze(self.project)
        self.p.build("v2")
        new = self.p.picture()
        closed = review.close_round(self.project, done=[n["id"]])
        self.assertEqual(closed["notes_rev"], frozen["notes_rev"])
        self.assertEqual(review.freeze(self.project)["notes"], [])
        shown = [x for x in review.state(self.project)["notes"] if x["id"] == n["id"]][0]
        self.assertTrue(shown["closed"])
        self.assertFalse(shown["older_picture"])
        self.assertEqual(new, review.picture(self.project)["file_sha256"])


class NoteLedger(Base):
    """A note closes only on a round's word, and only on the line the head stands on."""

    def edit(self, word):
        (self.project / "tools_local" / "scenes.py").write_text(f"word = '{word}'\n", encoding="utf8")
        self.p.build(f"v-{word}")
        return self.p.picture(keys=("k1", f"k-{word}"))

    def setUp(self):
        super().setUp()
        self.first = self.p.picture()

    def note(self, text="change this", frame=3, picture_sha=None):
        return review.add_note(self.project, {"text": text, "frame": frame, "scope": "frame", "picture_sha": picture_sha or self.first})

    def shown(self, note):
        return next(n for n in review.state(self.project)["notes"] if n["id"] == note["id"])

    def test_a_round_with_no_edit_closes_nothing_and_the_note_is_offered_again(self):
        n = self.note()
        review.freeze(self.project)
        self.assertEqual(review.close_round(self.project)["changed_beats"], [])
        self.assertFalse(self.shown(n)["closed"])
        self.assertTrue(self.shown(n)["not_done"])
        self.assertEqual([x["id"] for x in review.freeze(self.project)["notes"]], [n["id"]])

    def test_only_the_notes_a_round_names_are_done(self):
        a, b = self.note(text="move it"), self.note(text="give me a new shirt")
        review.freeze(self.project)
        self.edit("b")
        review.close_round(self.project, done=[a["id"]], not_done={b["id"]: "that needs body pixels we do not have"})
        self.assertTrue(self.shown(a)["closed"])
        left = self.shown(b)
        self.assertEqual((left["closed"], left["older_picture"], left["not_done"]), (False, False, "that needs body pixels we do not have"))

    def test_a_note_left_undone_is_carried_to_the_next_round_on_the_new_picture_and_a_later_round_can_do_it(self):
        n = self.note()
        review.freeze(self.project)
        self.edit("b")
        review.close_round(self.project, not_done={n["id"]: "ran out of road"})
        frozen = review.freeze(self.project)
        self.assertEqual(([x["id"] for x in frozen["notes"]], frozen["flagged"]), ([n["id"]], []))
        self.edit("c")
        review.close_round(self.project, done=[n["id"]])
        self.assertTrue(self.shown(n)["closed"])
        self.assertIsNone(self.shown(n)["not_done"])

    def test_a_round_can_only_speak_for_its_frozen_notes(self):
        n = self.note()
        review.freeze(self.project)
        late = self.note(text="after the freeze")
        with self.assertRaisesRegex(ValueError, "frozen"):
            review.close_round(self.project, done=[late["id"]])
        with self.assertRaisesRegex(ValueError, "needs a reason"):
            review.close_round(self.project, not_done={n["id"]: " "})
        with self.assertRaisesRegex(ValueError, "both"):
            review.close_round(self.project, done=[n["id"]], not_done={n["id"]: "no"})

    def test_a_note_left_undone_holds_approval_until_he_drops_it(self):
        n = self.note()
        review.freeze(self.project)
        self.edit("b")
        review.close_round(self.project, not_done={n["id"]: "real footage"})
        h = review.picture(self.project)["file_sha256"]
        with self.assertRaisesRegex(ValueError, "still open"):
            review.approve(self.project, h)
        review.drop_note(self.project, n["id"])
        shown = self.shown(n)
        self.assertEqual((shown["closed"], shown["dropped"], shown["not_done"]), (True, True, None))
        self.assertEqual(review.freeze(self.project)["notes"], [])
        approval.write_once(approval.approvals(self.p.root) / f"{h[:16]}.json", {"approved_file_sha256": h, "composition_rev": self.p.map["composition_rev"], "lock_revision": "lock1", "profile": {}, "result": "PASS"})
        self.assertEqual(review.approve(self.project, h)["state"], "approved")

    def test_a_note_that_does_not_exist_cannot_be_dropped(self):
        with self.assertRaisesRegex(ValueError, "no note"):
            review.drop_note(self.project, "nope")

    def test_going_back_undoes_what_the_later_rounds_did_and_flags_it(self):
        a = self.note(text="round one")
        review.freeze(self.project)
        self.edit("b")
        first = review.close_round(self.project, done=[a["id"]])
        b = self.note(text="round two", picture_sha=review.picture(self.project)["file_sha256"])
        review.freeze(self.project)
        self.edit("c")
        review.close_round(self.project, done=[b["id"]])
        review.go_back(self.project, first["parent"])
        for note in (a, b):
            shown = self.shown(note)
            self.assertEqual((shown["closed"], shown["undone"], shown["older_picture"]), (False, True, True), note["text"])
        frozen = review.freeze(self.project)
        self.assertEqual(frozen["notes"], [])
        self.assertEqual(sorted(x["text"] for x in frozen["flagged"]), ["round one", "round two"])
        review.go_back(self.project, first["n"])
        self.assertTrue(self.shown(a)["closed"], "back on the line that did it")
        self.assertTrue(self.shown(b)["undone"])

    def test_a_round_left_behind_says_nothing_about_a_note_it_left_undone(self):
        n = self.note()
        base = review.freeze(self.project)
        self.assertEqual(base["notes"][0]["id"], n["id"])
        self.edit("b")
        r = review.close_round(self.project, not_done={n["id"]: "no"})
        review.go_back(self.project, r["parent"])
        shown = self.shown(n)
        self.assertEqual((shown["closed"], shown["not_done"], shown["undone"], shown["older_picture"]), (False, None, False, False), "open again on the picture it was left on")

    def test_a_note_on_an_approved_picture_takes_the_approval_back(self):
        h = review.picture(self.project)["file_sha256"]
        approval.write_once(approval.approvals(self.p.root) / f"{h[:16]}.json", {"approved_file_sha256": h, "composition_rev": self.p.map["composition_rev"], "lock_revision": "lock1", "profile": {}, "result": "PASS"})
        self.assertEqual(review.approve(self.project, h)["state"], "approved")
        n = self.note()
        self.assertEqual(review.approval_status(self.project)["state"], "none")
        review.drop_note(self.project, n["id"])
        self.assertEqual(review.approve(self.project, h)["state"], "approved", "the record still stands, so no second render")


class State(Base):
    def test_a_failed_picture_is_shown_with_its_findings_and_cannot_be_approved(self):
        self.p.picture()
        h = self.p.picture(status="FAIL", where="last_attempt.json", checks=False)
        rev = self.p.map["composition_rev"]
        self.p.report(h, rev, {"O4": {"status": "FAIL", "problems": [], "flash": {"status": "FAIL", "flashes": [], "double_cuts": [{"frames": [7, 8], "diffs": [9, 9]}]}}})
        s = review.state(self.project)
        self.assertEqual((s["picture"]["file_sha256"], s["picture"]["status"], s["picture"]["source"]), (h, "FAIL", "last_attempt"))
        self.assertEqual([(f["id"], f["frames"], f["waived"]) for f in s["findings"]], [("O4.double_cut:7-8", [7, 8], False)])
        self.assertFalse(s["approvable"])
        with self.assertRaisesRegex(ValueError, "fix or waive"):
            review.approve(self.project, h)

    def test_unverified_is_counted_and_blocks_nothing(self):
        h = self.p.picture(checks=False)
        self.p.report(h, self.p.map["composition_rev"], events=[{"event_id": "b01.e1", "kind": "action", "status": "UNVERIFIED", "frame": 3}, {"event_id": "b01.e2", "kind": "action", "status": "UNVERIFIED", "frame": 4}])
        s = review.state(self.project)
        self.assertEqual(s["unverified"], {"loudness": 1, "action": 2})
        self.assertTrue(s["approvable"])

    def test_a_check_that_never_ran_blocks(self):
        self.p.picture(checks=False)
        s = review.state(self.project)
        self.assertEqual(sorted(f["check"] for f in s["findings"]), ["output", "source"])
        self.assertFalse(s["approvable"])

    def test_a_failed_run_with_no_report_saying_why_fails_closed(self):
        self.p.picture(status="FAIL", where="last_attempt.json")
        self.assertFalse(review.state(self.project)["approvable"])

    def test_beats_carry_script_layout_and_what_changed(self):
        self.p.picture(keys=("k1", "k2"))
        review.close_round(self.project)
        self.p.build("v2")
        self.p.picture(keys=("k1", "k3"))
        review.close_round(self.project)
        s = review.state(self.project)
        self.assertEqual([(b["id"], b["script"], b["layout"], b["changed"]) for b in s["beats"]], [("b01", "one", "split", False), ("b02", "two", "full", True)])
        self.assertEqual((s["fps"], s["frames"], s["beats"][1]["start"]), (30, 60, 1.0))
        self.assertEqual(s["rounds"][1]["changed_beats"], ["b02"])

    def test_no_picture_yet(self):
        s = review.state(self.project)
        self.assertIsNone(s["picture"])
        self.assertEqual(len(s["beats"]), 2)
        self.assertFalse(s["approvable"])


class Waive(Base):
    def failed(self, keys=("k1", "k2")):
        h = self.p.picture(status="FAIL", where="last_attempt.json", checks=False, keys=keys)
        self.p.report(h, self.p.map["composition_rev"], {"O4": {"status": "FAIL", "problems": [], "flash": {"status": "FAIL", "flashes": [], "double_cuts": [{"frames": [7, 8], "diffs": [9, 9]}]}}})
        return h

    def test_a_click_makes_it_approvable_without_a_new_check(self):
        self.failed()
        w = review.waive(self.project, "O4.double_cut:7-8", "looked at it")
        self.assertEqual((w["check"], w["frames"], w["why"], w["by"], w["keys"]), ("O4.double_cut", [7, 8], "looked at it", "chase", {"b01": "k1"}))
        s = review.state(self.project)
        self.assertTrue(s["findings"][0]["waived"], "still reported")
        self.assertTrue(s["approvable"])

    def test_waivers_append_and_keep_every_row(self):
        self.failed()
        review.waive(self.project, "O4.double_cut:7-8", "one")
        path = self.p.home / "waivers.json"
        rows = store.read_json(path)
        store.write_json(path, rows + [{"check": "x", "frames": [1], "why": "older row"}])
        h = self.p.picture(status="FAIL", where="last_attempt.json", checks=False)
        self.p.report(h, self.p.map["composition_rev"], {"O5": {"status": "FAIL", "failed": [{"frame": 2}], "failed_count": 1, "clip_suspects_uncleared": []}})
        review.waive(self.project, "O5.sample:2", "two")
        self.assertEqual([r["why"] for r in store.read_json(path)], ["one", "older row", "two"])

    def test_it_needs_a_reason_and_a_real_finding(self):
        self.failed()
        with self.assertRaises(ValueError):
            review.waive(self.project, "O4.double_cut:7-8", "  ")
        with self.assertRaises(ValueError):
            review.waive(self.project, "O4.double_cut:1-2", "x")

    def test_damage_to_the_file_cannot_be_waived(self):
        h = self.p.picture(status="FAIL", where="last_attempt.json", checks=False)
        self.p.report(h, self.p.map["composition_rev"], {"O2": {"status": "FAIL", "problems": ["b01: frame 3 differs from its segment"]}})
        finding = review.state(self.project)["findings"][0]
        with self.assertRaisesRegex(ValueError, "fixed"):
            review.waive(self.project, finding["id"], "no")

    def test_an_edit_to_the_beat_brings_the_finding_back(self):
        self.failed()
        review.waive(self.project, "O4.double_cut:7-8", "looked")
        self.failed(keys=("k9", "k2"))
        s = review.state(self.project)
        self.assertFalse(s["findings"][0]["waived"])
        self.assertFalse(s["approvable"])

    def test_a_later_edit_elsewhere_keeps_it(self):
        self.failed()
        review.waive(self.project, "O4.double_cut:7-8", "looked")
        self.failed(keys=("k1", "k9"))
        self.assertTrue(review.state(self.project)["approvable"])

    def test_a_source_fail_is_a_finding_and_can_be_waived(self):
        h = self.p.picture(status="FAIL", where="last_attempt.json", checks=False)
        self.p.report(h, self.p.map["composition_rev"], events=[{"event_id": "b02.e1", "kind": "anchor", "status": "FAIL", "frame": 33, "problems": ["time: late"]}])
        s = review.state(self.project)
        self.assertEqual(s["findings"][0]["id"], "source.b02.e1:33")
        review.waive(self.project, "source.b02.e1:33", "fine")
        self.assertTrue(review.state(self.project)["approvable"])


class Rounds(Base):
    def setUp(self):
        super().setUp()
        self.first = self.p.picture()
        self.r0 = review.close_round(self.project)

    def edit(self, word="b"):
        (self.project / "tools_local" / "scenes.py").write_text(f"word = '{word}'\n", encoding="utf8")
        (self.p.home / "beats.json").write_text(f'{{"beats": ["{word}"]}}', encoding="utf8")
        self.p.build(f"v-{word}")
        return self.p.picture(keys=("k1", f"k-{word}"))

    def test_round_numbers_and_parents(self):
        self.assertEqual((self.r0["n"], self.r0["parent"], self.r0["changed_beats"]), (0, None, []))
        self.edit()
        r1 = review.close_round(self.project)
        self.assertEqual((r1["n"], r1["parent"], r1["changed_beats"]), (1, 0, ["b02"]))

    def test_closing_twice_is_one_round(self):
        self.assertEqual(review.close_round(self.project), self.r0)
        self.assertEqual(len(review.all_rounds(self.p.root)), 1)

    def test_a_project_that_is_not_the_newest_picture_cannot_close(self):
        self.p.build("v2")
        with self.assertRaisesRegex(ValueError, "run.py change"):
            review.close_round(self.project)

    def test_go_back_restores_every_file_and_the_picture(self):
        self.edit()
        review.close_round(self.project)
        (self.project / "tools_local" / "new.py").write_text("x", encoding="utf8")
        back = review.go_back(self.project, 0)
        self.assertEqual((self.project / "tools_local" / "scenes.py").read_text(encoding="utf8"), "word = 'a'\n")
        self.assertEqual((self.p.home / "beats.json").read_text(encoding="utf8"), '{"beats": []}')
        self.assertEqual(store.read_json(self.project / "ownership.json")["composition_rev"], self.r0["composition_rev"])
        self.assertFalse((self.project / "tools_local" / "new.py").exists())
        self.assertIn("tools_local/new.py", back["removed"])
        self.assertEqual(review.picture(self.project)["file_sha256"], self.first)
        self.assertEqual(review.state(self.project)["head"], 0)

    def test_what_was_here_is_kept_when_going_back(self):
        self.edit()
        review.close_round(self.project)
        (self.project / "tools_local" / "scenes.py").write_text("unsaved = 1\n", encoding="utf8")
        review.go_back(self.project, 0)
        left = store.read_json(next((self.p.root / "rounds").glob("left-*.json")))
        blob = self.p.root / "rounds" / "blobs" / left["manifest"]["tools_local/scenes.py"]
        self.assertEqual(blob.read_text(encoding="utf8"), "unsaved = 1\n")

    def test_a_round_on_a_failed_picture_goes_back_to_that_failed_picture(self):
        (self.project / "tools_local" / "scenes.py").write_text("word = 'c'\n", encoding="utf8")
        self.p.build("v3")
        failed = self.p.picture(status="FAIL", where="last_attempt.json")
        review.close_round(self.project)
        self.edit()
        n = review.close_round(self.project)["n"]
        review.go_back(self.project, n - 1)
        pic = review.picture(self.project)
        self.assertEqual((pic["file_sha256"], pic["source"], pic["status"]), (failed, "last_attempt", "FAIL"))

    def test_a_further_edit_after_going_back_is_a_new_round_on_that_parent(self):
        self.edit("b")
        review.close_round(self.project)
        self.edit("c")
        review.close_round(self.project)
        review.go_back(self.project, 1)
        self.edit("d")
        r = review.close_round(self.project)
        self.assertEqual((r["n"], r["parent"]), (3, 1))
        self.assertEqual([x["n"] for x in review.state(self.project)["rounds"]], [0, 1, 2, 3])

    def test_going_back_needs_the_store_free(self):
        self.edit()
        review.close_round(self.project)
        store.write_json(self.p.root / "run.lock", {"pid": os.getpid()})
        with self.assertRaisesRegex(RuntimeError, "another run"):
            review.go_back(self.project, 0)
        self.assertEqual((self.project / "tools_local" / "scenes.py").read_text(encoding="utf8"), "word = 'b'\n")
        (self.p.root / "run.lock").unlink()

    def test_nothing_is_touched_if_a_rounds_bytes_are_lost(self):
        self.edit()
        review.close_round(self.project)
        round0 = store.read_json(self.p.root / "rounds" / "0000.json")
        (self.p.root / "rounds" / "blobs" / round0["manifest"]["tools_local/scenes.py"]).unlink()
        with self.assertRaisesRegex(ValueError, "lost"):
            review.go_back(self.project, 0)
        self.assertEqual((self.project / "tools_local" / "scenes.py").read_text(encoding="utf8"), "word = 'b'\n")

    def test_no_such_round_and_a_changed_picture_refuse(self):
        with self.assertRaises(ValueError):
            review.go_back(self.project, 9)
        with open(review.picture(self.project)["file"], "ab") as f:
            f.write(b"x")
        with self.assertRaisesRegex(ValueError, "gone or changed"):
            review.go_back(self.project, 0)

    def test_a_round_is_real_copies(self):
        round0 = store.read_json(self.p.root / "rounds" / "0000.json")
        blob = self.p.root / "rounds" / "blobs" / round0["manifest"]["tools_local/scenes.py"]
        self.assertEqual(os.stat(blob).st_nlink, 1)


class Compare(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.d = Path(self.dir.name)

    def tearDown(self):
        self.dir.cleanup()

    def test_the_window_finds_a_spot_anywhere_even_on_the_right_edge(self):
        for x in (0, 37, 516):
            d = np.zeros((960, 540), np.int16)
            d[100:124, x:x + 24] = 50
            value, y, at = approval.worst_window(d, 24)
            self.assertGreaterEqual(value, 12, x)
            self.assertLess(abs(at - x), 24)

    def test_a_spot_across_a_block_edge_is_not_split(self):
        d = np.zeros((960, 540), np.int16)
        d[12:36, 12:36] = 40
        self.assertEqual(approval.worst_window(d, 24)[0], 40)

    def test_identical_files_read_identical(self):
        video(self.d / "a.mp4")
        n = approval.compare(self.d / "a.mp4", self.d / "a.mp4")
        self.assertEqual((n["frames_compared"], n["identical"], n["worst_block"], n["worst_psnr"]), (FRAMES, FRAMES, 0.0, 99.0))

    def test_a_defect_for_a_few_frames_is_found_on_those_frames(self):
        video(self.d / "a.mp4")
        video(self.d / "b.mp4", spot=(20, 22))
        n = approval.compare(self.d / "a.mp4", self.d / "b.mp4")
        self.assertEqual(sorted(n["rows"]), [20, 21, 22])
        self.assertGreater(n["worst_block"], 30)

    def test_frames_pair_by_number_not_by_time(self):
        video(self.d / "a.mp4")
        video(self.d / "b.mp4", retime=1.5)
        n = approval.compare(self.d / "a.mp4", self.d / "b.mp4")
        self.assertEqual(n["identical"], FRAMES)

    def test_a_frame_count_that_differs_is_a_fail_whatever_the_pixels_say(self):
        video(self.d / "a.mp4")
        video(self.d / "b.mp4", count=FRAMES - 1)
        n = approval.compare(self.d / "a.mp4", self.d / "b.mp4")
        self.assertEqual(approval.decide(n, self.limits())[0], "FAIL")

    def limits(self, overlap=False):
        return {"pass_under": {"block": 6, "fine": 8, "chroma": 4}, "fail_over": {"block": 12, "fine": 16, "chroma": 10}, "overlap": overlap}

    def numbers(self, *row):
        return {"frames_approved": 5, "frames_fresh": 5, "frames_compared": 5, "rows": {3: [40, *row, 0, 0]}}

    def test_the_three_zones(self):
        self.assertEqual(approval.decide(self.numbers(5, 7, 3), self.limits())[0], "PASS")
        self.assertEqual(approval.decide(self.numbers(7, 7, 3), self.limits())[0], "RECONCILE")
        self.assertEqual(approval.decide(self.numbers(5, 7, 5), self.limits())[0], "RECONCILE")
        self.assertEqual(approval.decide(self.numbers(13, 7, 3), self.limits())[0], "FAIL")
        self.assertEqual(approval.decide(self.numbers(5, 7, 11), self.limits())[0], "FAIL")

    def test_overlap_or_no_qualification_means_no_automatic_pass(self):
        self.assertEqual(approval.decide(self.numbers(1, 1, 1), self.limits(overlap=True))[0], "RECONCILE")
        self.assertEqual(approval.decide(self.numbers(1, 1, 1), None)[0], "RECONCILE")

    def test_regions_group_runs_and_name_the_beat(self):
        rows = {f: [30, 20, 20, 0, 5, 6] for f in (10, 11, 12, 40)}
        lock = {"beats": [{"beat_id": "b01", "start_frame": 0, "end_frame": 30}, {"beat_id": "b02", "start_frame": 30, "end_frame": 60}]}
        found = approval.regions({"rows": rows}, {"block": 6, "fine": 8, "chroma": 4}, lock)
        self.assertEqual(sorted((r["first"], r["last"], r["beat"]) for r in found), [(10, 12, "b01"), (40, 40, "b02")])

    def test_a_region_across_a_join_names_both_beats(self):
        rows = {f: [30, 20, 20, 0, 5, 6] for f in (28, 29, 30, 31)}
        lock = {"beats": [{"beat_id": "b01", "start_frame": 0, "end_frame": 30}, {"beat_id": "b02", "start_frame": 30, "end_frame": 60}]}
        self.assertEqual(approval.regions({"rows": rows}, {"block": 6, "fine": 8, "chroma": 4}, lock)[0]["beats"], ["b01", "b02"])

    def test_a_real_difference_makes_a_crop(self):
        video(self.d / "a.mp4")
        video(self.d / "b.mp4", spot=(20, 22))
        n = approval.compare(self.d / "a.mp4", self.d / "b.mp4")
        found = approval.regions(n, {"block": 6, "fine": 8, "chroma": 4})
        approval.write_crops(self.d / "a.mp4", self.d / "b.mp4", found, WIDTH, HEIGHT, self.d / "crops")
        self.assertTrue(Path(found[0]["image"]).stat().st_size > 100)


class Requalify(unittest.TestCase):
    """The limits come from one rule, whichever run set them. The numbers are the real ones of stage1/phase3-approval-qualification.json."""
    plants = {"cube": (38.97, 49.97, 21.62), "word": (39.7, 73.1, 2.39), "dot": (2.81, 6.46, 11.51), "letter": (8.98, 27.93, 1.37)}

    def judged(self, block, fine=7.74, chroma=3.89):
        import qualify_approval
        plants = {name: {"against": [{"worst_block": b, "worst_fine": f, "worst_chroma": c}]} for name, (b, f, c) in self.plants.items()}
        return qualify_approval.judged({"block": block, "fine": fine, "chroma": chroma}, plants)

    def test_the_noise_seen_in_real_checks_still_catches_and_stops_every_plant(self):
        doc = self.judged(5.87)
        self.assertEqual(doc["limits"]["pass_under"], {"block": 6.8, "fine": 8.95, "chroma": 4.52})
        self.assertFalse(doc["limits"]["overlap"])
        self.assertEqual(doc["inside_clean_noise"], [])
        self.assertTrue(all(doc["stopped_by"].values()), doc["stopped_by"])

    def test_noise_past_a_plant_turns_off_the_automatic_pass(self):
        doc = self.judged(8.0, 30.0, 12.0)
        self.assertIn("dot", doc["inside_clean_noise"])
        self.assertTrue(doc["limits"]["overlap"])


class Approval(Base):
    def setUp(self):
        super().setUp()
        self.h = self.p.picture()
        self.folder = approval.approvals(self.p.root)
        self.tag = self.h[:16]

    def record(self, result="PASS", **fields):
        return {"approved_file_sha256": self.h, "composition_rev": self.p.map["composition_rev"], "lock_revision": "lock1", "profile": {"name": "review"}, "fresh_file_sha256": "f", "method": {}, "frames_compared": 60,
                "worst_psnr": 45, "worst_block": 3, "result": result, "created": "now", **fields}

    def test_a_record_is_written_once(self):
        path = self.folder / f"{self.tag}.json"
        approval.write_once(path, self.record())
        with self.assertRaises(FileExistsError):
            approval.write_once(path, self.record("FAIL"))
        self.assertEqual(store.read_json(path)["result"], "PASS")
        self.assertEqual([p.name for p in self.folder.iterdir()], [path.name], "no temp file left")

    def test_the_record_has_the_agreed_fields_and_the_complete_profile(self):
        numbers = {"frames_compared": 60, "worst_psnr": 44.1, "worst_block": 3.2, "worst_fine": 4, "worst_chroma": 1, "identical": 10}
        record = approval.record_of(review.picture(self.project), "f" * 64, numbers, "PASS")
        for field in ("approved_file_sha256", "composition_rev", "lock_revision", "profile", "fresh_file_sha256", "method", "frames_compared", "worst_psnr", "worst_block", "result", "created"):
            self.assertIn(field, record)
        self.assertEqual(record["profile"]["encoder"]["crf"], 20)

    def test_refuses_a_picture_that_is_not_the_newest_or_not_the_project(self):
        new = self.p.picture()
        with self.assertRaisesRegex(ValueError, "newest"):
            review.approve(self.project, self.h)
        self.p.build("edited")
        with self.assertRaisesRegex(ValueError, "moved on"):
            review.approve(self.project, new)

    def test_refuses_a_file_that_changed_on_disk(self):
        with open(review.picture(self.project)["file"], "ab") as f:
            f.write(b"x")
        with self.assertRaisesRegex(ValueError, "on disk"):
            review.approve(self.project, self.h)

    def test_starts_its_own_process_and_says_running(self):
        with mock.patch.object(approval.subprocess, "Popen") as popen, mock.patch.object(store, "alive", return_value=True):
            popen.return_value.pid = 123
            s = review.approve(self.project, self.h)
        self.assertEqual((s["state"], s["stage"]), ("running", "starting"))
        self.assertIn("check", popen.call_args.args[0])
        self.assertIn(self.h, popen.call_args.args[0])

    def test_a_second_ask_does_not_start_a_second_check(self):
        store.write_json(self.folder / f"running-{self.tag}.json", {"pid": 1, "stage": "rendering", "started": "x"})
        with mock.patch.object(approval.subprocess, "Popen") as popen, mock.patch.object(store, "alive", return_value=True):
            self.assertEqual(review.approve(self.project, self.h)["stage"], "rendering")
        popen.assert_not_called()

    def test_a_check_that_died_reads_as_an_error(self):
        store.write_json(self.folder / f"running-{self.tag}.json", {"pid": 1, "stage": "rendering", "started": "x"})
        with mock.patch.object(store, "alive", return_value=False):
            self.assertEqual(review.approval_status(self.project)["state"], "error")

    def test_a_passing_record_approves_and_any_picture_change_clears_it(self):
        approval.write_once(self.folder / f"{self.tag}.json", self.record())
        self.assertEqual(review.approval_status(self.project)["state"], "none", "a record alone is not his approval")
        self.assertEqual(review.approve(self.project, self.h)["state"], "approved")
        self.p.build("v2")
        self.p.picture()
        self.assertEqual(review.approval_status(self.project)["state"], "none")

    def test_coming_back_to_an_approved_picture_does_not_approve_it_again_by_itself(self):
        review.close_round(self.project)
        approval.write_once(self.folder / f"{self.tag}.json", self.record())
        review.approve(self.project, self.h)
        self.p.build("v2")
        self.p.picture()
        review.close_round(self.project)
        self.assertFalse((self.folder / "active.json").exists())
        review.go_back(self.project, 0)
        self.assertEqual(review.approval_status(self.project)["state"], "none")
        self.assertEqual(review.approve(self.project, self.h)["state"], "approved", "the record still stands, so no second render")

    def test_a_render_that_moves_the_picture_clears_it(self):
        store.write_json(self.folder / "active.json", {"file_sha256": "old"})
        runner.clear_approval(self.p.root, "old")
        self.assertTrue((self.folder / "active.json").exists(), "the same picture again")
        runner.clear_approval(self.p.root, "new")
        self.assertFalse((self.folder / "active.json").exists())
        runner.clear_approval(self.p.root, "new")

    def fresh(self, h="f" * 64, source_events=()):
        """A fresh store as a finished run leaves it."""
        fresh = self.p.home / "fresh"
        rev = self.p.map["composition_rev"]
        folder = fresh / "stitched" / f"review-{h[:16]}-{rev[:16]}"
        checks = fresh / "checks" / rev[:16]
        for path in (folder, checks, fresh / "changes"):
            path.mkdir(parents=True, exist_ok=True)
        store.write_json(folder / "stitch.json", {"beats": []})
        (folder / "review.mp4").write_bytes(b"x")
        store.write_json(checks / f"output-{h[:16]}.json", {"checks": {}, "waived": []})
        store.write_json(checks / f"source-{h[:16]}.json", {"findings": [], "events": list(source_events)})
        store.write_json(fresh / "changes" / "0001.json", {"stitched": str(folder / "review.mp4"), "file_sha256": h, "composition_rev": rev, "status": "UNVERIFIED"})
        return fresh

    def judged(self, worst, fresh=None):
        numbers = {"frames_approved": 60, "frames_fresh": 60, "frames_compared": 60, "identical": 50, "width": WIDTH, "height": HEIGHT, "worst_psnr": 40.0, "worst_block": worst, "worst_fine": 1.0, "worst_chroma": 1.0,
                   "worst_frame": {}, "rows": {12: [40.0, worst, 1.0, 1.0, 0, 0]}}
        limits = {"pass_under": {"block": 6, "fine": 8, "chroma": 4}, "fail_over": {"block": 12, "fine": 26, "chroma": 10}, "overlap": False}
        with mock.patch.object(approval, "compare", return_value=numbers), mock.patch.object(approval, "qualification", return_value=limits), mock.patch.object(approval, "write_crops"):
            approval.run_check(self.project, self.h, reuse=fresh or self.fresh())
        self.assertFalse((self.folder / f"running-{self.tag}.json").exists())
        return review.approval_status(self.project)

    def test_a_clean_check_writes_the_record_and_approves(self):
        s = self.judged(3)
        self.assertEqual((s["state"], s["record"]["result"], s["record"]["fresh_file_sha256"]), ("approved", "PASS", "f" * 64))

    def test_a_real_difference_writes_a_failed_record_and_names_its_beat(self):
        s = self.judged(30)
        self.assertEqual((s["state"], s["record"]["result"], s["regions"][0]["beats"]), ("failed", "FAIL", ["b01"]))
        with self.assertRaisesRegex(ValueError, "--only b01"):
            review.approve(self.project, self.h)

    def test_an_open_note_stops_approve_reconcile_and_a_passing_check(self):
        note = {"text": "this", "frame": 3, "scope": "frame", "picture_sha": self.h}
        waiting = self.judged(8)
        self.assertEqual(waiting["state"], "reconcile")
        n = review.add_note(self.project, note)
        with self.assertRaisesRegex(ValueError, "still open"):
            review.approve(self.project, self.h)
        with self.assertRaisesRegex(ValueError, "still open"):
            review.reconcile(self.project, self.h, "noise")
        self.assertEqual(review.approval_status(self.project)["state"], "reconcile")
        self.assertFalse((self.folder / f"{self.tag}.json").exists())
        review.drop_note(self.project, n["id"])
        self.assertEqual(review.reconcile(self.project, self.h, "noise")["state"], "approved")

    def test_a_note_during_a_clean_check_keeps_the_record_and_withholds_the_approval(self):
        n = review.add_note(self.project, {"text": "this", "frame": 3, "scope": "frame", "picture_sha": self.h})
        s = self.judged(3)
        self.assertEqual((s["state"], s["record"]["result"]), ("none", "PASS"))
        self.assertFalse((self.folder / "active.json").exists())
        review.drop_note(self.project, n["id"])
        self.assertEqual(review.approve(self.project, self.h)["state"], "approved")

    def test_the_grey_zone_writes_no_record_until_chase_calls_it(self):
        s = self.judged(8)
        self.assertEqual(s["state"], "reconcile")
        self.assertFalse((self.folder / f"{self.tag}.json").exists())
        self.assertEqual(review.reconcile(self.project, self.h, "noise")["record"]["result"], "RECONCILED")

    def test_a_fail_only_the_all_beats_check_finds_blocks_with_no_record_and_shows_in_state(self):
        event = {"event_id": "b02.e1", "kind": "anchor", "status": "FAIL", "frame": 33, "problems": ["late"]}
        s = self.judged(3, self.fresh(source_events=[event]))
        self.assertEqual(s["state"], "blocked")
        self.assertFalse((self.folder / f"{self.tag}.json").exists(), "a record could never be replaced after a waive")
        self.assertIn("source.b02.e1:33", [f["id"] for f in review.state(self.project)["findings"]])
        review.waive(self.project, "source.b02.e1:33", "fine")
        self.assertEqual(self.judged(3)["state"], "approved")

    def test_a_render_that_never_finished_is_an_error_and_no_verdict(self):
        fresh = self.p.home / "fresh"
        (fresh / "changes").mkdir(parents=True)
        store.write_json(fresh / "changes" / "0001.json", {"refused": "x"})
        with mock.patch.object(approval, "compare") as compare:
            approval.run_check(self.project, self.h, reuse=fresh)
        compare.assert_not_called()
        self.assertEqual(review.approval_status(self.project)["state"], "error")
        self.assertFalse((self.folder / f"{self.tag}.json").exists())

    def test_a_failed_record_stops_this_picture_for_good(self):
        approval.write_once(self.folder / f"{self.tag}.json", self.record("FAIL", regions_dir="here"))
        self.assertEqual(review.approval_status(self.project)["state"], "failed")
        with self.assertRaisesRegex(ValueError, "written once"):
            review.approve(self.project, self.h)

    def test_a_record_of_another_composition_is_not_this_picture(self):
        approval.write_once(self.folder / f"{self.tag}.json", self.record(composition_rev="other"))
        with self.assertRaisesRegex(ValueError, "another composition"):
            review.approve(self.project, self.h)

    def test_reconcile_needs_waiting_regions_and_a_reason(self):
        with self.assertRaisesRegex(ValueError, "no regions"):
            review.reconcile(self.project, self.h, "fine")
        store.write_json(self.folder / f"reconcile-{self.tag}.json", {"why": "grey zone", "regions": [], "regions_dir": "r", "record": self.record("RECONCILE")})
        self.assertEqual(review.approval_status(self.project)["state"], "reconcile")
        with self.assertRaises(ValueError):
            review.reconcile(self.project, self.h, " ")
        s = review.reconcile(self.project, self.h, "I looked, it is noise")
        self.assertEqual((s["state"], s["record"]["result"], s["record"]["why"]), ("approved", "RECONCILED", "I looked, it is noise"))


class Native(unittest.TestCase):
    def fake(self, only):
        run = mock.Mock(beats={"b01": 1, "b02": 2}, inject=None, root=Path("r"), profile_hash="p" * 32, keys={"b01": "k1", "b02": "k2"})
        run.stored = lambda b: False
        finished = {}

        def render_and_finish(run_, change, tmp, todo, started, stitch_after=True, failed=False):
            finished.update(change=change, todo=todo, stitch_after=stitch_after)
            return 0

        with mock.patch.object(runner, "render_and_finish", render_and_finish), mock.patch.object(runner, "damaged", return_value=[]):
            runner.draft(run, mock.Mock(force=False, inject_beats=None, only=only), Path("t"), 0)
        return finished

    def test_only_renders_that_beat_and_never_stitches(self):
        done = self.fake("b02")
        self.assertEqual((done["todo"], done["stitch_after"]), (["b02"], False))
        self.assertTrue(done["change"]["segments"]["b02"].endswith("segment.mp4"))

    def test_an_unknown_beat_refuses(self):
        with self.assertRaises(runner.Refused):
            self.fake("b99")

    def test_a_plain_draft_still_stitches(self):
        done = self.fake(None)
        self.assertEqual((done["todo"], done["stitch_after"]), (["b01", "b02"], True))


if __name__ == "__main__":
    unittest.main(verbosity=1)
