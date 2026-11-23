"""deliver.PhoneCopy: the phone copy is made beside the checks, falls back to libx264, and is gone when a delivery fails."""
import subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import deliver


def frames(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries", "stream=nb_read_packets,codec_name,width,height",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip().split(",")
    return out


class PhoneCopyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        cls.src = cls.dir / "final.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=2160x3840:rate=30:duration=1", "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
                        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", str(cls.src)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_a_4k_file_becomes_a_1080_wide_copy_with_every_frame(self):
        out = self.dir / "a.mp4"
        job = deliver.PhoneCopy(self.src, out, 2160)
        job.wait()
        codec, width, height, n = frames(out)
        self.assertEqual((codec, width, height, n), ("h264", "1080", "1920", "30"))

    def test_without_a_graphics_card_encoder_it_uses_libx264(self):
        out = self.dir / "b.mp4"
        saved = deliver.PhoneCopy.ENCODERS
        deliver.PhoneCopy.ENCODERS = [["-c:v", "no_such_encoder"], saved[-1]]
        try:
            job = deliver.PhoneCopy(self.src, out, 2160)
            job.wait()
        finally:
            deliver.PhoneCopy.ENCODERS = saved
        self.assertEqual(frames(out)[3], "30")
        self.assertIn("libx264", " ".join(job.commands[-1]))

    def test_no_encoder_at_all_raises_on_wait(self):
        out = self.dir / "c.mp4"
        saved = deliver.PhoneCopy.ENCODERS
        deliver.PhoneCopy.ENCODERS = [["-c:v", "no_such_encoder"]]
        try:
            job = deliver.PhoneCopy(self.src, out, 2160)
            with self.assertRaises(ValueError):
                job.wait()
        finally:
            deliver.PhoneCopy.ENCODERS = saved
        self.assertFalse(out.exists())

    def test_drop_leaves_no_file_whether_it_was_finished_or_still_running(self):
        out = self.dir / "d.mp4"
        job = deliver.PhoneCopy(self.src, out, 2160)
        job.drop()                      # at once: may still be encoding
        self.assertFalse(out.exists())
        job = deliver.PhoneCopy(self.src, out, 2160)
        job.wait()
        self.assertTrue(out.exists())
        job.drop()                      # after it finished: a failed check still leaves nothing
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
