"""The Apple GPU transcription route (asr.MlxWhisper), with a stand-in for mlx-whisper so it runs on any machine.

It proves the wrapper, not mlx-whisper itself: the times of each speech span land back on the whole file, the result has
the shape transcribe.py and rawcut.py read, and a failing call is done again on the CPU model instead of stopping a run.
"""
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import asr  # noqa: E402


def fake(calls, fail=False):
    def transcribe(audio, **kw):
        if fail:
            raise RuntimeError("metal said no")
        calls.append((len(audio), kw))
        return {"language": "en", "segments": [{"start": 0.5, "end": 1.5, "text": " hello there",
                                                 "words": [{"word": " hello", "start": 0.5, "end": 0.9, "probability": 0.9},
                                                           {"word": " there", "start": 1.0, "end": 1.5, "probability": 0.8}]}]}
    return types.SimpleNamespace(transcribe=transcribe)


class Mlx(unittest.TestCase):
    def test_each_speech_span_is_moved_back_onto_the_file(self):
        calls, audio = [], np.zeros(16000 * 30, dtype=np.float32)
        model = asr.MlxWhisper("large-v3", cpu=None)
        with mock.patch.dict(sys.modules, {"mlx_whisper": fake(calls)}), \
                mock.patch.object(model, "spans", return_value=[(16000 * 2, 16000 * 6), (16000 * 20, 16000 * 24)]):
            segments, info = model.transcribe(audio, language="en", word_timestamps=True, vad_filter=True, initial_prompt="Claude")
        self.assertEqual([round(s.start, 2) for s in segments], [2.5, 20.5])
        self.assertEqual([(w.word, round(w.start, 2), round(w.end, 2)) for w in segments[1].words], [(" hello", 20.5, 20.9), (" there", 21.0, 21.5)])
        self.assertEqual((info.language, info.duration), ("en", 30.0))
        self.assertEqual([n for n, _ in calls], [64000, 64000])
        self.assertEqual(calls[0][1]["path_or_hf_repo"], "mlx-community/whisper-large-v3-mlx")
        self.assertEqual(calls[0][1]["initial_prompt"], "Claude")

    def test_a_failing_call_is_done_again_on_the_cpu(self):
        cpu = mock.Mock(); cpu.transcribe.return_value = ("cpu segments", "cpu info")
        model = asr.MlxWhisper("large-v3", cpu=lambda: cpu)
        with mock.patch.dict(sys.modules, {"mlx_whisper": fake([], fail=True)}):
            out = model.transcribe(np.zeros(16000, dtype=np.float32), language="en", vad_filter=False, beam_size=5)
        self.assertEqual(out, ("cpu segments", "cpu info"))
        self.assertEqual(cpu.transcribe.call_args.kwargs["beam_size"], 5)

    def test_only_an_apple_silicon_mac_with_the_package_uses_it(self):
        with mock.patch.object(sys, "platform", "win32"):
            self.assertFalse(asr.mlx_ok())
        with mock.patch.object(sys, "platform", "darwin"), mock.patch("platform.machine", return_value="arm64"), \
                mock.patch("importlib.util.find_spec", return_value=object()):
            self.assertTrue(asr.mlx_ok())
            with mock.patch.dict("os.environ", {"CLAUDE_EDIT_ASR": "cpu"}):
                self.assertFalse(asr.mlx_ok())


if __name__ == "__main__":
    unittest.main()
