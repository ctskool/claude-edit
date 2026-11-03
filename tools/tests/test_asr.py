"""tools/asr.py: a GPU that crashes the probe process must fall back to the CPU instead of killing the run."""
import subprocess
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import asr


class Model:
    made = []

    def __init__(self, name, **kwargs):
        self.name, self.device = name, kwargs["device"]
        Model.made.append((name, kwargs["device"]))

    def transcribe(self, samples):
        return iter([]), None


def fakes(devices=1):
    return {
        "ctranslate2": types.SimpleNamespace(get_cuda_device_count=lambda: devices),
        "numpy": types.SimpleNamespace(zeros=lambda *a, **kw: [], float32="float32"),
        "faster_whisper": types.SimpleNamespace(WhisperModel=Model),
    }


class GpuProbe(unittest.TestCase):
    def setUp(self):
        Model.made = []

    def load(self, probe=None, devices=1):
        with mock.patch.dict(sys.modules, fakes(devices)), mock.patch.object(asr, "cuda_dll_dirs"), \
                mock.patch.object(subprocess, "run", return_value=probe) as run, mock.patch("sys.stderr"):
            return asr.load_whisper("large-v3"), run

    def test_crashed_probe_falls_back_to_cpu_turbo(self):
        crash = subprocess.CompletedProcess([], 3221225477, "", "")
        model, _ = self.load(crash)
        self.assertEqual((model.name, model.device), ("large-v3-turbo", "cpu"))
        self.assertNotIn(("large-v3", "cuda"), Model.made)  # CUDA is never touched in this process

    def test_working_probe_loads_cuda(self):
        model, run = self.load(subprocess.CompletedProcess([], 0, "", ""))
        self.assertEqual((model.name, model.device), ("large-v3", "cuda"))
        self.assertEqual(run.call_args[0][0][-1], "large-v3")

    def test_no_cuda_device_skips_the_probe(self):
        model, run = self.load(devices=0)
        self.assertEqual(model.device, "cpu")
        run.assert_not_called()

    def test_hung_probe_falls_back(self):
        with mock.patch.dict(sys.modules, fakes()), \
                mock.patch.object(subprocess, "run", side_effect=subprocess.TimeoutExpired("probe", 300)):
            ok, why = asr.gpu_ok("large-v3")
        self.assertFalse(ok)
        self.assertIn("hung", why)


if __name__ == "__main__":
    unittest.main()
