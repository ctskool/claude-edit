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


def load_whisper(name):
    """float16 on CUDA, probed with a silent clip because cuBLAS loads lazily on the first encode. On the CPU large-v3 needs
    about 11 GB of commit (mkl_malloc fails on a busy machine), so the fallback is turbo."""
    cuda_dll_dirs()
    import numpy as np
    from faster_whisper import WhisperModel
    try:
        model = WhisperModel(name, device="cuda", compute_type="float16")
        list(model.transcribe(np.zeros(16000, dtype=np.float32))[0])
        return model
    except Exception as e:
        print(f"\n!!! GPU TRANSCRIPTION FAILED ({str(e)[:120]})\n!!! falling back to large-v3-turbo on the CPU, ~20x slower\n",
              file=sys.stderr)
        return WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
