"""A hand-built look's short in the player (tools/look_player.py): load, changed beats, a note round, and what arms Approve.
Small generated videos stand in for the renders; nothing here runs HyperFrames."""
import json, shutil, subprocess, sys, tempfile, types, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools" / "beat_review"), str(ROOT / "tools" / "beat_render"), str(ROOT / "tools" / "beat_check"), str(ROOT / "tools")]
import look_player
import review


def video(path, box_at=None):
    """4 s at 30 fps with a tone; box_at puts a white box on screen from that second on."""
    draw = f",drawbox=x=40:y=40:w=120:h=80:color=white:t=fill:enable='gte(t,{box_at})'" if box_at is not None else ""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=0x204080:s=270x480:r=30:d=4{draw}", "-f", "lavfi", "-i", "sine=f=440:d=4",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(path)], check=True)


class LookPlayer(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp(dir=ROOT / "work", prefix="_test-look-"))
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)
        self.project = self.home / "v2" / "sky"
        self.project.mkdir(parents=True)
        (self.project / "index.html").write_text("<html>one</html>", encoding="utf8")
        words = [{"i": i, "text": t, "start": s, "end": s + .4} for i, (t, s) in enumerate([("first", .1), ("beat", .6), ("second", 2.1), ("beat.", 2.6)])]
        (self.home / "words.json").write_text(json.dumps(words), encoding="utf8")
        self.spec = types.SimpleNamespace(OUT=self.project, NAME="t", END=4.0, BEATS=[0, 2.0], WORDS=self.home / "words.json", __file__=str(self.project / "short.py"))
        (self.project / "short.py").write_text("# spec", encoding="utf8")

    def load(self, name, box_at=None):
        mp4 = self.home / name
        video(mp4, box_at)
        look_player.load(self.spec, mp4, "sky")
        return review.state(self.project)

    def test_load_gives_the_player_its_beats_and_arms_approve(self):
        s = self.load("a.mp4")
        self.assertEqual([(b["id"], b["start_frame"], b["end_frame"], b["script"]) for b in s["beats"]], [("b01", 0, 60, "first beat"), ("b02", 60, 120, "second beat.")])
        self.assertTrue(s["approvable"])
        self.assertEqual(s["findings"], [])
        self.assertEqual(review.composition(self.project)["engine"], "sky")

    def test_a_round_closes_its_note_and_marks_only_the_changed_beat(self):
        s = self.load("a.mp4")
        note = review.add_note(self.project, {"text": "add a box", "frame": 90, "scope": "frame", "picture_sha": s["picture"]["file_sha256"]})
        self.assertEqual(note["beat_id"], "b02")
        self.assertEqual([n["id"] for n in review.freeze(self.project)["notes"]], [note["id"]])
        (self.project / "index.html").write_text("<html>two</html>", encoding="utf8")
        s = self.load("b.mp4", box_at=2.5)
        self.assertEqual([b["changed"] for b in s["beats"]], [False, True])
        self.assertEqual(review.close_round(self.project, done=[note["id"]])["changed_beats"], ["b02"])
        s = review.state(self.project)
        self.assertTrue(s["notes"][0]["closed"])
        self.assertTrue(s["approvable"])
        # the picture before is still its own file: a later load never writes over it
        first = review.all_rounds(review.root_of(self.project))[0]
        self.assertEqual(look_player.file_hash(first["entry"]["file"]), first["picture_sha"])

    def test_an_edit_after_the_load_is_no_longer_that_picture(self):
        self.load("a.mp4")
        (self.project / "index.html").write_text("<html>moved on</html>", encoding="utf8")
        self.assertIsNone(review.composition(self.project))
        with self.assertRaises(ValueError):
            review.close_round(self.project)

    def test_a_render_of_the_wrong_length_blocks_approval(self):
        self.spec.END = 9.0
        s = self.load("a.mp4")
        self.assertFalse(s["approvable"])
        self.assertIn("END", s["findings"][0]["message"])


if __name__ == "__main__":
    unittest.main()
