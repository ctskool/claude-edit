"""Whisper loader shared by transcribe.py and rawcut.py: NVIDIA GPU first, an Apple Silicon Mac's GPU through mlx-whisper when it
is installed, else the CPU, and loud whenever it has to fall back."""
import glob
import os
import sys

_DLL_HANDLES = []


def cuda_dll_dirs():
    """Windows: CTranslate2 loads cuBLAS 12 + cuDNN 9 by name and only searches its own folder, so the pip nvidia-*-cu12
    packages (or torch's lib folder) must be added by hand. Without this every run silently dropped to the CPU."""
    if os.name != "nt":
        return
    dirs = []
    for base in sys.path:
        if base.endswith("site-packages"):
            dirs += glob.glob(os.path.join(base, "nvidia", "*", "bin")) + [os.path.join(base, "torch", "lib")]
    for d in dict.fromkeys(dirs):
        if os.path.isdir(d):
            _DLL_HANDLES.append(os.add_dll_directory(d))
            os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")


GPU_PROBE = r'''
import sys
sys.path.insert(0, sys.argv[1])
from asr import cuda_dll_dirs
cuda_dll_dirs()
import numpy as np
from faster_whisper import WhisperModel
m = WhisperModel(sys.argv[2], device="cuda", compute_type="float16")
list(m.transcribe(np.zeros(16000, dtype=np.float32))[0])
'''


def gpu_ok(name, timeout=300):
    """Try CUDA in a throwaway process first. A driver fault (0xC0000005 on Windows, often another app such as a video
    export holding the GPU) kills the process outright, so an in-process try/except never gets to fall back."""
    import subprocess
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() == 0:
            return False, "no CUDA device (normal on a Mac)"
    except Exception as e:
        return False, str(e)[:120]
    try:
        p = subprocess.run([sys.executable, "-c", GPU_PROBE, os.path.dirname(os.path.abspath(__file__)), name],
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, f"GPU probe hung for {timeout} s"
    if p.returncode == 0:
        return True, ""
    tail = (p.stderr or p.stdout).strip().splitlines()
    return False, f"GPU probe exited with code {p.returncode}" + (f": {tail[-1][:120]}" if tail else " (crashed)")


MLX_REPOS = {"large-v3": "mlx-community/whisper-large-v3-mlx", "large-v3-turbo": "mlx-community/whisper-large-v3-turbo"}


def mlx_ok():
    """An Apple Silicon Mac with mlx-whisper installed: Whisper then runs on the Mac's own GPU instead of the CPU.
    CLAUDE_EDIT_ASR=cpu turns it off."""
    import importlib.util
    import platform
    if sys.platform != "darwin" or platform.machine() != "arm64" or os.environ.get("CLAUDE_EDIT_ASR", "").lower() == "cpu":
        return False
    return importlib.util.find_spec("mlx_whisper") is not None


class _Part:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class MlxWhisper:
    """mlx-whisper behind the two faster-whisper calls the tools make: transcribe(audio or path, ...) -> (segments, info),
    each segment with .start .end .text .words, each word with .word .start .end .probability.

    mlx-whisper has no voice filter of its own, so vad_filter uses faster-whisper's (the same Silero model and defaults the
    NVIDIA route uses): each speech span is transcribed alone and its times are moved back onto the whole file. Anything
    that goes wrong in a call is said out loud and that call is done again on the CPU, so a run slows down, never stops.
    Written on Windows and not yet run on a Mac (2026-11-23)."""

    def __init__(self, name, cpu):
        self.repo, self.cpu = MLX_REPOS.get(name, name), cpu

    def spans(self, audio, vad_filter):
        if not vad_filter:
            return [(0, len(audio))]
        from faster_whisper.vad import VadOptions, get_speech_timestamps
        return [(int(t["start"]), int(t["end"])) for t in get_speech_timestamps(audio, VadOptions())]

    def run(self, audio, language, initial_prompt, condition_on_previous_text, vad_filter):
        import importlib
        import numpy as np
        mlx_whisper = importlib.import_module("mlx_whisper")   # by name: only a Mac has it, and the doctor lists every plain import
        if not isinstance(audio, np.ndarray):
            from faster_whisper.audio import decode_audio
            audio = decode_audio(audio, sampling_rate=16000)
        segments = []
        for a0, a1 in self.spans(audio, vad_filter):
            off = a0 / 16000
            r = mlx_whisper.transcribe(audio[a0:a1], path_or_hf_repo=self.repo, word_timestamps=True, language=language,
                                       initial_prompt=initial_prompt, condition_on_previous_text=condition_on_previous_text)
            language = language or r.get("language")
            for s in r["segments"]:
                words = [_Part(word=w["word"], start=w["start"] + off, end=w["end"] + off, probability=w.get("probability", 0.0))
                         for w in s.get("words") or []]
                segments.append(_Part(start=s["start"] + off, end=s["end"] + off, text=s["text"], words=words))
        return segments, _Part(language=language or "en", duration=len(audio) / 16000)

    def transcribe(self, audio, language=None, word_timestamps=True, vad_filter=False, initial_prompt=None,
                   condition_on_previous_text=True, **more):
        try:
            return self.run(audio, language, initial_prompt, condition_on_previous_text, vad_filter)
        except Exception as e:
            print(f"\n!!! APPLE GPU TRANSCRIPTION FAILED ({str(e)[:160]})\n!!! doing this part again on the CPU, much slower\n", file=sys.stderr)
            return self.cpu().transcribe(audio, language=language, word_timestamps=word_timestamps, vad_filter=vad_filter,
                                         initial_prompt=initial_prompt, condition_on_previous_text=condition_on_previous_text, **more)


def load_whisper(name):
    """float16 on CUDA, probed with a silent clip because cuBLAS loads lazily on the first encode. On the CPU large-v3 needs
    about 11 GB of commit (mkl_malloc fails on a busy machine), so the fallback is turbo."""
    cuda_dll_dirs()
    import numpy as np
    from faster_whisper import WhisperModel
    if mlx_ok():
        cache = []

        def cpu():
            cache or cache.append(WhisperModel("large-v3-turbo", device="cpu", compute_type="int8"))
            return cache[0]
        try:
            model = MlxWhisper(name, cpu)
            model.run(np.zeros(16000, dtype=np.float32), "en", None, False, False)   # loads (first time: downloads) the model
            print(f"transcribing on the Apple GPU (mlx-whisper, {model.repo})", file=sys.stderr)
            return model
        except Exception as e:
            print(f"\n!!! APPLE GPU TRANSCRIPTION UNAVAILABLE ({str(e)[:160]})", file=sys.stderr)
    ok, why = gpu_ok(name)
    if ok:
        try:
            model = WhisperModel(name, device="cuda", compute_type="float16")
            list(model.transcribe(np.zeros(16000, dtype=np.float32))[0])
            return model
        except Exception as e:
            why = str(e)[:120]
    print(f"\n!!! GPU TRANSCRIPTION UNAVAILABLE ({why})\n!!! falling back to large-v3-turbo on the CPU, ~20x slower\n",
          file=sys.stderr)
    return WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
