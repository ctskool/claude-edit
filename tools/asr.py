"""faster-whisper loader shared by transcribe.py and rawcut.py: GPU first, loud if it has to fall back."""
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


def load_whisper(name):
    """float16 on CUDA, probed with a silent clip because cuBLAS loads lazily on the first encode. On the CPU large-v3 needs
    about 11 GB of commit (mkl_malloc fails on a busy machine), so the fallback is turbo."""
    cuda_dll_dirs()
    import numpy as np
    from faster_whisper import WhisperModel
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
