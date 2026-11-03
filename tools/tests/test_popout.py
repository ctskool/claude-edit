"""tools/popout.py: the size math, the page pieces, and the kit build's split path."""
import json, re, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import popout

IVORY = json.loads((ROOT / "templates" / "ivory" / "template.json").read_text(encoding="utf8"))["popout"]
# 1030-2's measurement, from work/1030-2-popout/v2/editorial/assets/popout.json
MEASURED = {"head_top_min": 128.0, "head_top_median": 164.0, "head_cx": 1960.8}


class Geometry(unittest.TestCase):
    def test_runs_to_the_frame_bottom(self):
        g = popout.geometry(MEASURED, IVORY, 3840, 2160)
        self.assertEqual(g["clip_y"] + g["clip_h"], popout.FRAME_H)

    def test_highest_head_clears_the_caption(self):
        g = popout.geometry(MEASURED, IVORY, 3840, 2160)
        self.assertGreaterEqual(g["clip_y"] + MEASURED["head_top_min"] * g["scale"], IVORY["clear_y"] - 2)

    def test_matches_the_picked_variant(self):
        # Chase picked variant 2 on 1030-2: a 2244 px crop at y 996. The tool's own pick must land within a few px.
        g = popout.geometry(MEASURED, IVORY, 3840, 2160)
        self.assertLess(abs(g["crop"][0] - 2244), 20)
        self.assertLess(abs(g["clip_y"] - 996), 6)

    def test_crop_stays_inside_the_camera(self):
        for cx in (100, 1920, 3800):
            g = popout.geometry({**MEASURED, "head_cx": cx}, IVORY, 3840, 2160)
            w, _, x0, _ = g["crop"]
            self.assertGreaterEqual(x0, 0)
            self.assertLessEqual(x0 + w, 3840)

    def test_lower_caption_means_smaller(self):
        a = popout.geometry(MEASURED, IVORY, 3840, 2160)
        b = popout.geometry(MEASURED, {**IVORY, "clear_y": 1300}, 3840, 2160)
        self.assertLess(b["scale"], a["scale"])

    def test_max_scale_caps_the_size(self):
        g = popout.geometry(MEASURED, {**IVORY, "max_scale": 0.3}, 3840, 2160)
        self.assertLessEqual(g["scale"], 0.3)


class Page(unittest.TestCase):
    G = {**popout.geometry(MEASURED, IVORY, 3840, 2160), "edge": 135, "radius": 36, "card_css": IVORY["card_css"],
         "cam": "assets/popout_cam.mp4", "fg": "assets/popout_fg.webm"}

    def test_face_wrap_keeps_the_bottom_half(self):
        # tools/beat_render/refs.mjs refuses a split reference unless #face-wrap is exactly the bottom half
        css = popout.css(self.G)
        self.assertRegex(css, r"#face-wrap \{ position: absolute; left: 0; top: 960px; width: 1080px; height: 960px;")

    def test_markup_ids_and_tracks(self):
        html = popout.markup(self.G, 57.65)
        for needle in ('id="face-wrap"', 'id="panel-bg"', 'id="panel-clip"', 'id="face" class="clip"', 'id="face-fg" class="clip"',
                       'src="assets/popout_cam.mp4"', 'src="assets/popout_fg.webm"', 'data-duration="57.65"'):
            self.assertIn(needle, html)
        self.assertEqual(sorted(re.findall(r'data-track-index="(\d+)"', html)), ["0", "1"])

    def test_twin_copies_face_tweens_only(self):
        js = '\n'.join(['tl.set("#face", { scale: 1.08 }, A(1));', 'tl.to("#face-wrap", { opacity: 0 }, 2);', 'tl.to("#face", { scale: 1 }, 3);'])
        out = popout.twin(js).split("\n")
        self.assertEqual(out, ['tl.set("#face", { scale: 1.08 }, A(1));', 'tl.set("#face-fg", { scale: 1.08 }, A(1));',
                               'tl.to("#face-wrap", { opacity: 0 }, 2);', 'tl.to("#face", { scale: 1 }, 3);', 'tl.to("#face-fg", { scale: 1 }, 3);'])

    def test_roots_follow_face(self):
        self.assertEqual(popout.roots({"a": ["#face"], "b": ["#x"], "c": ["#face", "#face-fg"]}),
                         {"a": ["#face", "#face-fg"], "b": ["#x"], "c": ["#face", "#face-fg"]})


class Kit(unittest.TestCase):
    def test_split_markup_unchanged(self):
        # the default path must emit the same face line it did before popout existed
        src = (ROOT / "templates" / "ivory" / "build_kit" / "tools_local" / "build.py").read_text(encoding="utf8")
        self.assertIn('<div id="face-wrap"><video id="face" class="clip" src="assets/face_half.mp4" muted playsinline data-start="0" data-duration="{END}" data-track-index="0"></video></div>', src)
        self.assertIn('if plan.get("bottom") == "popout":', src)

    def test_ivory_offers_popout(self):
        for k in ("card_x", "card_w", "clear_y", "radius", "card_css"):
            self.assertIn(k, IVORY)


if __name__ == "__main__":
    unittest.main()
