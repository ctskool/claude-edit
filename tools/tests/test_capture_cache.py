"""Capture cache tests, no browser/network. Run: python -B tools/tests/test_capture_cache.py"""
from contextlib import redirect_stdout
from datetime import datetime, timezone, timedelta
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import capture_cache as cache


class CaptureCache(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cache = self.root / "cache"
        self.output = self.root / "output"
        self.tool = self.root / "capture_shots.py"
        self.tool.write_text("# fake backend\n", encoding="utf-8")
        self.now = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
        self.item = {"name": "docs", "url": "https://docs.example.com/intro"}
        self.calls = []
        self.wall = False

    def runner(self, command, check):
        self.assertIs(check, False)
        self.assertEqual(command[1], str(self.tool))
        stage, spec = Path(command[2]), json.loads(Path(command[3]).read_text(encoding="utf-8"))
        self.calls.append(spec)
        for item in spec:
            (stage / (item["name"] + ".png")).write_bytes(cache.PNG + b"fake image")
            value = {"url": item["url"], "dpr": 2, "boxes": [{"tag": "h1", "text": "Docs", "x": 3, "y": 8, "w": 20, "h": 10}], "login_wall": self.wall}
            (stage / (item["name"] + ".json")).write_text(json.dumps(value), encoding="utf-8")
        return SimpleNamespace(returncode=0)

    def capture(self, spec=None, **kwargs):
        out = io.StringIO()
        with redirect_stdout(out):
            result = cache.capture(self.output, [self.item] if spec is None else spec, cache=self.cache, tool=self.tool,
                                   runner=self.runner, now=kwargs.pop("now", self.now), **kwargs)
        return result, out.getvalue()

    def test_miss_then_renamed_hit_copies_both_files_exactly(self):
        result, text = self.capture()
        self.assertEqual(result, 0, text)
        first = {ext: (self.output / ("docs" + ext)).read_bytes() for ext in (".png", ".json")}
        result, text = self.capture([{**self.item, "name": "renamed"}])
        self.assertEqual(result, 0, text)
        self.assertIn("HIT renamed", text)
        self.assertEqual(len(self.calls), 1)
        for ext in first:
            self.assertEqual((self.output / ("renamed" + ext)).read_bytes(), first[ext])
        meta = json.loads((self.cache / cache.capture_key(self.item, self.tool) / "meta.json").read_text())
        self.assertEqual(meta["captured_at"], self.now.isoformat())
        self.assertEqual(meta["source_spec"], self.item)

    def test_defaults_selector_alias_and_nested_options(self):
        explicit = {**self.item, "name": "other", "theme": "light", "width": 1280, "height": 800, "full_page": False, "hide": []}
        self.assertEqual(cache.capture_key(explicit, self.tool), cache.capture_key(self.item, self.tool))
        a = {**self.item, "selector": "main", "options": {"hide": ["nav"]}}
        b = {**self.item, "element": "main", "hide": ["nav"]}
        self.assertEqual(cache.capture_key(a, self.tool), cache.capture_key(b, self.tool))
        self.capture([a])
        self.assertEqual(self.calls[0][0]["element"], "main")
        self.assertEqual(self.calls[0][0]["hide"], ["nav"])
        self.assertNotIn("selector", self.calls[0][0])

    def test_every_option_and_backend_version_change_identity(self):
        key = cache.capture_key(self.item, self.tool)
        for extra in ({"url": "https://docs.example.com/next"}, {"theme": "dark"}, {"width": 1000}, {"height": 900},
                      {"element": "article"}, {"full_page": True}, {"hide": ["nav"]}, {"future_option": {"z": 1}}):
            with self.subTest(extra=extra):
                self.assertNotEqual(key, cache.capture_key({**self.item, **extra}, self.tool))
        self.tool.write_text("# backend changed\n")
        self.assertNotEqual(key, cache.capture_key(self.item, self.tool))

    def test_mixed_batch_and_same_key_aliases_capture_only_unique_misses(self):
        self.capture()
        spec = [self.item, {"name": "new", "url": "https://example.com/new"}, {"name": "alias", "url": "https://example.com/new"}]
        result, text = self.capture(spec)
        self.assertEqual(result, 0, text)
        self.assertEqual(len(self.calls[-1]), 1)
        self.assertIn("HITS 1 MISSES 2 CAPTURED 1", text)
        self.assertEqual((self.output / "new.png").read_bytes(), (self.output / "alias.png").read_bytes())

    def test_expiry_is_strict_and_refresh_preserves_old_generation(self):
        self.capture()
        keydir = self.cache / cache.capture_key(self.item, self.tool)
        original = {p.name: p.read_bytes() for p in keydir.iterdir()}
        self.capture(now=self.now + timedelta(days=7))
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(len(list(keydir.glob("v-*"))), 1)
        for name, content in original.items():
            self.assertEqual((keydir / name).read_bytes(), content)
        self.capture(now=self.now + timedelta(days=7, hours=1))
        self.assertEqual(len(self.calls), 2)

    def test_future_timestamp_and_zero_age_are_misses(self):
        self.capture()
        self.capture(now=self.now - timedelta(hours=1))
        self.capture(max_age_days=0)
        self.assertEqual(len(self.calls), 3)

    def test_corrupt_png_and_missing_boxes_are_never_hits(self):
        self.capture()
        keydir = self.cache / cache.capture_key(self.item, self.tool)
        (keydir / "capture.png").write_bytes(b"broken")
        self.capture()
        self.assertEqual(len(self.calls), 2)
        newest = list(keydir.glob("v-*"))[0]
        (newest / "capture.json").unlink()
        self.capture()
        self.assertEqual(len(self.calls), 3)

    def test_login_wall_cannot_poison_cache(self):
        self.wall = True
        result, text = self.capture()
        self.assertEqual(result, 1)
        self.assertIn("sign-in wall", text)
        self.assertFalse(list(self.cache.rglob("meta.json")))
        self.wall = False
        self.assertEqual(self.capture()[0], 0)
        self.assertEqual(len(self.calls), 2)

    def test_backend_failure_is_propagated_without_cache_entry(self):
        with patch.object(self, "runner", return_value=SimpleNamespace(returncode=9)):
            result, text = self.capture()
        self.assertEqual(result, 9, text)
        self.assertFalse(list(self.cache.rglob("meta.json")))

    def test_changing_numbers_warn_on_miss_and_hit(self):
        for url in ("https://github.com/org/repo", "https://example.com/pricing"):
            item = {**self.item, "url": url}
            for _ in range(2):
                result, text = self.capture([item])
                self.assertEqual(result, 0, text)
                self.assertIn("check the numbers against facts.json", text)
        self.assertTrue(cache.numbers(self.item, {"boxes": [{"text": "$19/month"}]}))
        self.assertFalse(cache.numbers(self.item, {"boxes": [{"text": "Introduction"}]}))

    def test_prune_is_opt_in_and_keeps_unrelated_files(self):
        self.capture()
        keydir = self.cache / cache.capture_key(self.item, self.tool)
        (keydir / "keep.txt").write_text("untouched")
        self.capture(now=self.now + timedelta(days=8))
        self.assertTrue((keydir / "meta.json").exists())
        self.capture(now=self.now + timedelta(days=8), do_prune=True)
        self.assertFalse((keydir / "meta.json").exists())
        self.assertTrue((keydir / "keep.txt").exists())
        self.assertEqual(len(list(keydir.glob("v-*/meta.json"))), 1)

    def test_invalid_specs_refused_before_any_capture(self):
        for bad in ({**self.item, "name": "../escape"}, {**self.item, "name": "a/b"},
                    {**self.item, "width": True}, {**self.item, "url": "file:///secret"},
                    {**self.item, "selector": "main", "element": "aside"}, {**self.item, "options": []},
                    {**self.item, "width": 0}, {**self.item, "theme": "auto"}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.capture([bad])
        with self.assertRaises(ValueError):
            self.capture([self.item, self.item])
        for age in (-1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                self.capture(max_age_days=age)
        self.assertFalse(self.calls)

    def test_output_cache_overlap_refused(self):
        with self.assertRaises(ValueError):
            cache.capture(self.cache / "out", [], cache=self.cache, tool=self.tool)

    def test_cli_reads_bom_and_reports_bad_json(self):
        path = self.root / "spec.json"
        path.write_text(json.dumps([self.item]), encoding="utf-8-sig")
        with patch.object(cache, "capture", return_value=0) as invoke:
            self.assertEqual(cache.main([str(self.output), str(path), "--max-age-days", "3", "--prune"]), 0)
            self.assertEqual(invoke.call_args.args[1], [self.item])
            self.assertTrue(invoke.call_args.kwargs["do_prune"])
        path.write_text("invalid")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(cache.main([str(self.output), str(path)]), 2)


if __name__ == "__main__":
    unittest.main()
