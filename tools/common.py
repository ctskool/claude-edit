"""Shared machine config for every tool: paths, encoder, decode acceleration, Whisper / matting device.

`python setup.py` detects the machine and writes config/config.json; tools read it through cfg(). Every value has a
safe default, so a tool still runs (slower) on a machine where setup has not been run yet.

  from common import ROOT, cfg, encoder_args, hwaccel_args, strip_hw, matte_python, whisper_device
"""
import json
import os
import platform
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "config", "config.json")
PROFILE = os.path.join(ROOT, "config", "profile.json")
IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
VENV = os.path.join(ROOT, ".venv")
VENV_PY = os.path.join(VENV, "Scripts", "python.exe") if IS_WIN else os.path.join(VENV, "bin", "python")

_cache = None

for _s in (sys.stdout, sys.stderr):                 # Windows consoles default to cp1252; tool output has ◆ ✓ → etc.
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def _in_venv():
    try:
        return os.path.samefile(sys.prefix, VENV)
    except OSError:
        return False


# Any tool importing this module re-runs itself in the repo's .venv (made by setup.py), so `python tools/x.py` works
# with whatever `python` is on PATH. CLAUDE_EDIT_NO_VENV=1 turns this off.
if (os.path.exists(VENV_PY) and not _in_venv() and not os.environ.get("CLAUDE_EDIT_NO_VENV")
        and sys.argv and sys.argv[0].endswith(".py") and os.path.basename(sys.argv[0]) != "setup.py"):
    sys.exit(subprocess.run([VENV_PY, *sys.argv]).returncode)


def cfg():
    """config/config.json merged over the defaults (os, gpu, encoder, whisper, matte, chrome, recordings)."""
    global _cache
    if _cache is None:
        c = defaults()
        if os.path.exists(CONFIG):
            with open(CONFIG, encoding="utf-8") as f:
                c.update(json.load(f))
        _cache = c
    return _cache


def defaults():
    gpu = "nvidia" if shutil.which("nvidia-smi") else ("apple" if IS_MAC and platform.machine() == "arm64" else "cpu")
    return {
        "os": "windows" if IS_WIN else ("macos" if IS_MAC else "linux"),
        "gpu": gpu,
        "encoder": {"nvidia": "h264_nvenc", "apple": "h264_videotoolbox"}.get(gpu, "libx264"),
        "hwaccel": {"nvidia": "cuda", "apple": "videotoolbox"}.get(gpu),
        "whisper_device": "cuda" if gpu == "nvidia" else "cpu",
        "matte_device": {"nvidia": "cuda", "apple": "mps"}.get(gpu, "cpu"),
        "chrome": None,
        "recordings_dir": os.path.expanduser("~/Videos" if IS_WIN else "~/Movies"),
    }


def profile():
    """config/profile.json (the user's brand), falling back to config/profile.example.json."""
    for p in (PROFILE, os.path.join(ROOT, "config", "profile.example.json")):
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                return json.load(f)
    return {}


def encoder_args(quality="high"):
    """ffmpeg video encoder args for H.264 at near-lossless ("high", intermediate cuts) or delivery ("final") quality.
    NVENC on NVIDIA, VideoToolbox on a Mac, libx264 everywhere else."""
    enc = cfg()["encoder"]
    if enc == "h264_nvenc":
        cq = "17" if quality == "high" else "21"
        return ["-c:v", "h264_nvenc", "-preset", "p6", "-rc", "vbr", "-cq", cq, "-b:v", "0", "-maxrate", "120M",
                "-bufsize", "240M"]
    if enc == "h264_videotoolbox":
        br = "80M" if quality == "high" else "16M"
        return ["-c:v", "h264_videotoolbox", "-b:v", br, "-maxrate", br, "-allow_sw", "1"]
    return ["-c:v", "libx264", "-preset", "fast" if quality == "high" else "medium", "-crf", "16" if quality == "high" else "19"]


def hwaccel_args():
    """Decode acceleration flags for ffmpeg input (empty when there is none). Pair with strip_hw() for the retry."""
    hw = cfg().get("hwaccel")
    return ["-hwaccel", hw] if hw else []


def strip_hw(cmd):
    """The same ffmpeg command without -hwaccel <x> (software decode fallback)."""
    out, skip = [], False
    for c in cmd:
        if skip:
            skip = False
            continue
        if c == "-hwaccel":
            skip = True
            continue
        out.append(c)
    return out


def run_hw(cmd, **kw):
    """subprocess.run with hardware decode, retried once in software if it fails."""
    r = subprocess.run(cmd, **kw)
    if r.returncode and "-hwaccel" in cmd:
        r = subprocess.run(strip_hw(cmd), **kw)
    return r


def whisper_device():
    """(device, compute_type) for faster-whisper: CUDA fp16 on NVIDIA, CPU int8 otherwise (no Metal backend)."""
    return ("cuda", "float16") if cfg()["whisper_device"] == "cuda" else ("cpu", "int8")


def cuda_dll_dirs():
    """Windows: CTranslate2 needs cuBLAS 12 + cuDNN 9 DLLs on the search path. torch's CUDA wheels (installed by setup.py
    for the cut-out model) and the nvidia-*-cu12 pip packages ship them; add whichever exist."""
    if not IS_WIN:
        return
    import glob
    import importlib.util
    dirs = []
    spec = importlib.util.find_spec("torch")
    if spec and spec.submodule_search_locations:
        dirs.append(os.path.join(list(spec.submodule_search_locations)[0], "lib"))
    site = os.path.dirname(os.path.dirname(spec.origin)) if spec and spec.origin else None
    for base in filter(None, [site] + [p for p in sys.path if p.endswith("site-packages")]):
        dirs += glob.glob(os.path.join(base, "nvidia", "*", "bin"))
    for d in dict.fromkeys(dirs):
        if os.path.isdir(d):
            os.add_dll_directory(d)
            os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")


def load_whisper(name):
    """faster-whisper model on the configured device; CUDA is probed with a silent clip (cuBLAS loads lazily)."""
    dev, ct = whisper_device()
    if dev == "cuda":
        cuda_dll_dirs()
    from faster_whisper import WhisperModel
    if dev == "cuda":
        try:
            import numpy as np
            m = WhisperModel(name, device="cuda", compute_type=ct)
            list(m.transcribe(np.zeros(16000, dtype=np.float32))[0])
            return m
        except Exception as e:  # GPU unavailable or unsupported -> CPU fallback
            print(f"cuda unavailable ({str(e)[:80]}); using cpu", file=sys.stderr)
    return WhisperModel(name, device="cpu", compute_type="int8")


def matte_python():
    """The Python that has torch for tools/matte.py: the repo's .venv (setup.py installs torch there), else this one."""
    return VENV_PY if os.path.exists(VENV_PY) else sys.executable


def chrome_path():
    """A Chrome / Edge / Chromium binary for the tools that drive a browser directly (HyperFrames brings its own)."""
    c = cfg().get("chrome")
    if c and os.path.exists(c):
        return c
    cands = []
    if IS_WIN:
        for base in (os.environ.get("PROGRAMFILES", r"C:\Program Files"), os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
                     os.environ.get("LOCALAPPDATA", "")):
            cands += [os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"),
                      os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe")]
    elif IS_MAC:
        cands = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                 "/Applications/Chromium.app/Contents/MacOS/Chromium",
                 "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                 "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"]
    else:
        cands = [shutil.which(n) or "" for n in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge")]
    return next((p for p in cands if p and os.path.exists(p)), None)


def file_url(path):
    """file:// URL that works on Windows (file:///C:/...) and POSIX (file:///Users/...)."""
    from pathlib import Path
    return Path(os.path.abspath(path)).as_uri()


def npx():
    """npx executable name (npx.cmd on Windows when called without a shell)."""
    return "npx.cmd" if IS_WIN else "npx"


def utf8_env(**extra):
    """os.environ with PYTHONUTF8=1 (the engines print characters cp1252 cannot encode) plus extra values."""
    return dict(os.environ, PYTHONUTF8="1", **extra)
