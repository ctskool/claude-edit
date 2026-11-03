"""Doctor tests: fake dependencies, no installs, browsers, GPU jobs or renders."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import doctor
import paths


class Paths(unittest.TestCase):
    def test_default_is_above_tools_not_cwd(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(paths.project_root(), Path(paths.__file__).resolve().parent.parent)

    def test_override_and_work_folder_with_spaces(self):
        with tempfile.TemporaryDirectory(prefix="claude edit ") as d:
            with mock.patch.dict(os.environ, {"CLAUDE_EDIT_ROOT": d}):
                self.assertEqual(paths.project_root(), Path(d).resolve())
                self.assertEqual(paths.work_folder("demo", "raw"), Path(d).resolve() / "work/demo/raw")
                self.assertFalse(paths.work_folder().exists())

    def test_empty_override_and_escape(self):
        with mock.patch.dict(os.environ, {"CLAUDE_EDIT_ROOT": "  "}):
            self.assertEqual(paths.project_root(), Path(paths.__file__).resolve().parent.parent)
        for value in ("../outside", str(Path(tempfile.gettempdir()).resolve())):
            with self.assertRaises(ValueError):
                paths.work_folder(value)


class Imports(unittest.TestCase):
    def test_inventory_reads_nested_and_conditional_imports(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "tools/nested").mkdir(parents=True)
            (root / "tools/helper.py").write_text("", encoding="utf8")
            (root / "tools/nested/tool.py").write_text(
                "import os, json, numpy as np\nfrom PIL import Image\nimport helper\n"
                "from . import sibling\nif False:\n    from demucs.hf import get_hf_model\n"
                "def later():\n    import new_dependency\n", encoding="utf8")
            found, errors = doctor.inventory(root)
            self.assertFalse(errors)
            self.assertEqual(set(found), {"numpy", "PIL", "demucs", "new_dependency"})
            self.assertTrue(found["new_dependency"][0].endswith("tool.py:8"))

    def test_inventory_reports_invalid_source(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "tools").mkdir()
            (root / "tools/bad.py").write_text("def !", encoding="utf8")
            self.assertEqual(len(doctor.inventory(root)[1]), 1)

    def test_required_and_optional_missing_packages(self):
        with mock.patch.object(doctor, "inventory", return_value=({"mystery": ["tools/x.py:1"]}, [])), \
                mock.patch.object(doctor, "run", return_value=(1, "missing")):
            rows = {r.name: r for r in doctor.check_packages(Path("."))}
        self.assertEqual(rows["package numpy"].status, "FAIL")
        for name in ("demucs", "earshot", "torch", "transformers", "soundfile"):
            self.assertEqual(rows["package " + name].status, "WARN")
        self.assertEqual(rows["package mystery"].status, "FAIL")
        self.assertIn("Identify", rows["package mystery"].hint)

    def test_demucs_checks_actual_hf_api(self):
        self.assertIn("from demucs.hf import get_hf_model", doctor.IMPORT_PROBES["demucs"])


class Probes(unittest.TestCase):
    def test_python_floor(self):
        self.assertEqual(doctor.check_python((3, 9, 9)).status, "FAIL")
        self.assertEqual(doctor.check_python((3, 10, 0)).status, "PASS")

    def test_command_failure_and_optional_codex(self):
        with mock.patch.object(doctor.shutil, "which", return_value=None):
            self.assertEqual(doctor.check_command("ffmpeg", Path(".")).status, "FAIL")
            self.assertEqual(doctor.check_command("codex", Path("."), optional=True).status, "WARN")

    def test_node_minimum(self):
        with mock.patch.object(doctor.shutil, "which", return_value="node"), \
                mock.patch.object(doctor, "run", return_value=(0, "v20.5.0")):
            self.assertEqual(doctor.check_command("node", Path("."), 22).status, "FAIL")
        with mock.patch.object(doctor.shutil, "which", return_value="node"), \
                mock.patch.object(doctor, "run", return_value=(0, "v22.3.0")):
            self.assertEqual(doctor.check_command("node", Path("."), 22).status, "PASS")

    def test_npm_shim_uses_node_no_cmd_shell(self):
        with mock.patch.object(doctor.shutil, "which", side_effect=lambda n: "node.exe" if n == "node" else "npm.cmd"), \
                mock.patch.object(Path, "is_file", return_value=True):
            command = doctor.npm_command("npm", "--version")
        self.assertEqual(command[0], "node.exe")
        self.assertTrue(command[1].endswith("npm-cli.js"))
        self.assertEqual(command[-1], "--version")

    def test_hyperframes_pin_and_no_install(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "node_modules/hyperframes").mkdir(parents=True)
            manifest = root / "node_modules/hyperframes/package.json"
            manifest.write_text(json.dumps({"version": doctor.HF_PIN}), encoding="utf8")
            with mock.patch.object(doctor, "npm_command", return_value=["npx", "--no-install", "hyperframes", "--version"]) as command, \
                    mock.patch.object(doctor, "run", return_value=(0, doctor.HF_PIN)):
                self.assertEqual(doctor.check_hyperframes(root).status, "PASS")
                command.assert_called_once_with("npx", "--no-install", "hyperframes", "--version")
                manifest.write_text(json.dumps({"version": "9.0.0"}), encoding="utf8")
                self.assertEqual(doctor.check_hyperframes(root).status, "FAIL")

    def test_subprocess_failure_and_timeout_are_results(self):
        for error in (OSError("denied"), subprocess.TimeoutExpired("probe", 20)):
            with mock.patch.object(doctor.subprocess, "run", side_effect=error):
                rc, text = doctor.run(["probe"], Path("."))
                self.assertEqual(rc, 1)
                self.assertTrue(text)

    def test_probes_disable_bytecode_and_network_model_downloads(self):
        with mock.patch.object(doctor.subprocess, "run", return_value=types.SimpleNamespace(returncode=0, stdout="ok", stderr="")) as run:
            doctor.run(["probe"], Path("."))
        kwargs = run.call_args.kwargs
        self.assertEqual(kwargs["env"]["PYTHONDONTWRITEBYTECODE"], "1")
        self.assertEqual(kwargs["env"]["HF_HUB_OFFLINE"], "1")
        self.assertNotIn("shell", kwargs)
        self.assertEqual(kwargs["timeout"], 20)

    def test_encoder_listing_does_not_encode(self):
        with mock.patch.object(doctor.shutil, "which", return_value="ffmpeg"), \
                mock.patch.object(doctor, "run", return_value=(0, "libx264 aac libvpx-vp9")) as run:
            self.assertEqual(doctor.check_ffmpeg_features(Path(".")).status, "PASS")
        self.assertEqual(run.call_args.args[0], ["ffmpeg", "-hide_banner", "-encoders"])


class Transcription(unittest.TestCase):
    def probe(self, cuda=True, gpu_encode=True, cache=True, cpu=True):
        calls = []
        def dlls():
            calls.append("dlls")
        def compute(device):
            calls.append(device)
            if device == "cuda" and not cuda:
                raise RuntimeError("no CUDA")
            if device == "cpu" and not cpu:
                raise RuntimeError("no CPU runtime")
            return {"float16"} if device == "cuda" else {"int8"}
        class Model:
            def __init__(self, name, **kwargs):
                self.device = kwargs["device"]
                calls.append((name, kwargs))
                if not cache:
                    raise RuntimeError("model is not cached")
            def transcribe(self, samples):
                if self.device == "cuda" and not gpu_encode:
                    raise RuntimeError("cublas64_12.dll missing at first encode")
                return iter([]), None
        modules = {
            "asr": types.SimpleNamespace(cuda_dll_dirs=dlls),
            "ctranslate2": types.SimpleNamespace(get_supported_compute_types=compute),
            "numpy": types.SimpleNamespace(zeros=lambda *a, **kw: [], float32="float32"),
            "faster_whisper": types.SimpleNamespace(WhisperModel=Model),
        }
        output = io.StringIO()
        before = list(sys.path)
        try:
            with mock.patch.dict(sys.modules, modules), mock.patch.object(sys, "argv", ["probe", "tools"]), contextlib.redirect_stdout(output):
                try:
                    exec(compile(doctor.TRANSCRIPTION_PROBE, "probe", "exec"), {})
                except SystemExit as e:
                    self.assertEqual(e.code, 0)
        finally:
            sys.path[:] = before
        return json.loads(output.getvalue()), calls

    def test_gpu_probes_first_encode_after_dll_setup(self):
        data, calls = self.probe()
        self.assertEqual(data["status"], "PASS")
        self.assertEqual(calls[:2], ["dlls", "cuda"])
        self.assertEqual(calls[2][0], "large-v3")
        self.assertTrue(calls[2][1]["local_files_only"])

    def test_mac_cpu_fallback_is_warning_and_turbo(self):
        data, calls = self.probe(cuda=False)
        self.assertEqual(data["status"], "WARN")
        self.assertIn("slower", data["detail"])
        self.assertEqual(calls[-1][0], "large-v3-turbo")
        self.assertEqual(calls[-1][1]["compute_type"], "int8")

    def test_lazy_dll_failure_does_not_claim_cuda_pass(self):
        data, _ = self.probe(gpu_encode=False)
        self.assertEqual(data["status"], "WARN")
        self.assertIn("cublas", data["detail"])

    def test_uncached_model_warns_without_downloading(self):
        data, calls = self.probe(cuda=False, cache=False)
        self.assertEqual(data["status"], "WARN")
        self.assertIn("not verified", data["detail"])
        for call in calls:
            if isinstance(call, tuple):
                self.assertTrue(call[1]["local_files_only"])

    def test_no_runtime_fails(self):
        self.assertEqual(self.probe(cuda=False, cpu=False)[0]["status"], "FAIL")

    def test_probe_timeout_and_malformed_output_fail(self):
        for response in ((1, "timeout"), (0, "not json")):
            with mock.patch.object(doctor, "run", return_value=response):
                self.assertEqual(doctor.check_transcription(Path(".")).status, "FAIL")


class BrowsersAndDisk(unittest.TestCase):
    def test_mac_standard_and_user_applications(self):
        with mock.patch.object(doctor.shutil, "which", return_value=None):
            values = doctor.browser_candidates("darwin", {}, Path("/Users/student"))
        self.assertIn("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", values)
        self.assertIn("/Users/student/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge", values)

    def test_windows_and_custom_browser(self):
        with mock.patch.object(doctor.shutil, "which", return_value=None):
            values = doctor.browser_candidates("win32", {"CHROME_PATH": "custom browser", "LOCALAPPDATA": "local"}, Path("home"))
        self.assertEqual(values[0], "custom browser")
        self.assertTrue(any("Microsoft" in p and p.endswith("msedge.exe") for p in values))

    def test_browsers_require_playwright_and_hyperframes_too(self):
        with mock.patch.object(doctor, "browser_candidates", return_value=[]), \
                mock.patch.object(doctor, "run", return_value=(1, "missing browser")), \
                mock.patch.dict(os.environ, {}, clear=True):
            rows = doctor.check_browsers(Path("."))
        self.assertEqual([r.status for r in rows], ["FAIL", "FAIL", "FAIL"])
        self.assertIn("playwright install chromium", rows[1].windows)

    def test_hyperframes_check_never_calls_downloading_finder(self):
        with mock.patch.object(doctor, "browser_candidates", return_value=[]), \
                mock.patch.object(doctor, "run", return_value=(1, "missing")) as run, \
                mock.patch.dict(os.environ, {}, clear=True):
            doctor.check_browsers(Path("."))
        script = run.call_args.args[0][-1]
        self.assertIn("m.findSystemBrowser()", script)
        self.assertNotIn("m.findBrowser()", script)
        self.assertNotIn("ensureBrowser()", script)

    def test_disk_thresholds_and_errors(self):
        for gib, status in ((4, "FAIL"), (5, "WARN"), (24, "WARN"), (25, "PASS")):
            self.assertEqual(doctor.check_disk(Path("."), gib * doctor.GIB).status, status)
        with mock.patch.object(doctor.shutil, "disk_usage", side_effect=OSError("denied")):
            self.assertEqual(doctor.check_disk(Path(".")).status, "FAIL")


class Output(unittest.TestCase):
    def test_exit_codes_commands_and_hint_flag(self):
        for status, expected in (("PASS", 0), ("WARN", 0), ("FAIL", 1)):
            row = doctor.result(status, "test", "detail\ncontinued", ("win fix", "mac fix"), "explanation")
            for hints in (False, True):
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    self.assertEqual(doctor.show([row], hints), expected)
                self.assertIn(status + " test: detail continued", out.getvalue())
                self.assertIn("Windows: win fix", out.getvalue())
                self.assertIn("macOS:   mac fix", out.getvalue())
                self.assertEqual("Hint: explanation" in out.getvalue(), hints)

    def test_cli_routes_fix_hints(self):
        with mock.patch.object(doctor, "collect", return_value=[]), mock.patch.object(doctor, "show", return_value=0) as show:
            self.assertEqual(doctor.main(["--fix-hints"]), 0)
            show.assert_called_once_with([], True)

    def test_author_paths_warn_until_removed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            folder = root / "tools/workflows"
            folder.mkdir(parents=True)
            workflow = folder / "plan.js"
            user = "Chase"  # joined at run time, so this file does not trip the check it tests
            for path in (f"C:\\Users\\{user}\\shorts", f"C:/Users/{user}/shorts", f"/Users/{user}/shorts"):
                workflow.write_text(f"const S = '{path}'", encoding="utf8")
                self.assertEqual(doctor.check_portability(root).status, "WARN", path)
            workflow.write_text("const S = String(A.root)", encoding="utf8")
            self.assertEqual(doctor.check_portability(root).status, "PASS")
            workflow.write_text("const S = 'C:/Users/" + user + "er/x'", encoding="utf8")
            self.assertEqual(doctor.check_portability(root).status, "PASS", "another user's folder is not the author's")

    def test_cli_handles_unreadable_root(self):
        with mock.patch.object(doctor, "collect", side_effect=OSError("denied")), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(doctor.main([]), 1)


if __name__ == "__main__":
    unittest.main()
