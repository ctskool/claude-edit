"""claude-edit setup and doctor: detects your machine (Windows / macOS, NVIDIA / Apple Silicon / CPU), installs or checks
everything the skills need, and writes config/config.json. Safe to re-run.

  python setup.py              check, install what is missing (asks before system installs), write config
  python setup.py --check      doctor only: report, change nothing
  python setup.py --yes        install without asking
  python setup.py --no-matte   skip the cut-out model (torch, ~1-3 GB); cut-out formats and /claude-edit-versus need it
  python setup.py --smoke      also run the smoke test: 5 s synthetic clip -> encode -> matte -> whisper -> 5 s render
  python setup.py --import-pack <Creator-Skill-Pack/skills>   all 10 layout formats from your own copy of the pack
                                                              (rotation, frost and popout are bundled and imported anyway)

Standard library only, Python 3.10+. macOS paths are implemented but have not been run on a Mac yet.
"""
import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
IS_WIN, IS_MAC = sys.platform == "win32", sys.platform == "darwin"
VENV = os.path.join(ROOT, ".venv")
VPY = os.path.join(VENV, "Scripts", "python.exe") if IS_WIN else os.path.join(VENV, "bin", "python")
CONFIG = os.path.join(ROOT, "config", "config.json")

RVM_COMMIT = "53d74c6826735f01f4406b5ca9075eee27bec094"
RVM_ZIP = f"https://github.com/PeterL1n/RobustVideoMatting/archive/{RVM_COMMIT}.zip"
RVM_WEIGHTS = {
    "rvm_mobilenetv3.pth": "3c7c1d92033f7c38d6577c481d13a195d7d80a159b960f4f3119ac7b534cf4f8",
    "rvm_resnet50.pth": "c191a807251164c073dce5fa408e7a816070d539b882b2a3150330a9fec112ce",
}
RVM_RELEASE = "https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/"
# fontsource files the ivory style and the versus template use (OFL-1.1, from node_modules/@fontsource/*/files)
FONTS = {
    "instrument-serif": ["latin-400-italic", "latin-400-normal"],
    "inter": ["latin-400-normal", "latin-500-normal", "latin-600-normal", "latin-700-normal"],
    "inter-tight": ["latin-500-normal", "latin-600-italic", "latin-600-normal", "latin-700-italic", "latin-700-normal",
                    "latin-800-italic", "latin-800-normal", "latin-900-italic", "latin-900-normal"],
    "jetbrains-mono": ["latin-400-normal", "latin-500-normal", "latin-700-normal"],
    "newsreader": ["latin-400-italic", "latin-400-normal", "latin-500-italic", "latin-500-normal"],
    "space-grotesk": ["latin-500-normal", "latin-700-normal"],
}

results = []


def say(status, what, detail=""):
    results.append((status, what, detail))
    mark = {"OK": "  ok ", "FIXED": "fixed", "NEEDS YOU": " todo", "SKIP": " skip", "WARN": " warn", "FAIL": " FAIL"}[status]
    print(f"[{mark}] {what}" + (f" - {detail}" if detail else ""), flush=True)


def run(cmd, **kw):
    kw.setdefault("capture_output", True)
    kw.setdefault("text", True)
    kw.setdefault("encoding", "utf-8")
    kw.setdefault("errors", "replace")
    return subprocess.run(cmd, **kw)


def have(exe):
    return shutil.which(exe) is not None


def ask(question, a):
    if a.check:
        return False
    if a.yes:
        return True
    try:
        return input(f"  {question} [y/N] ").strip().lower() in ("y", "yes")
    except EOFError:
        return False


def npm_cmd(*args):
    return (["npm.cmd"] if IS_WIN else ["npm"]) + list(args)


def npx_cmd(*args):
    return (["npx.cmd"] if IS_WIN else ["npx"]) + list(args)


def download(url, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = dst + ".part"
    with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f, 1 << 20)
    os.replace(tmp, dst)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# --------------------------------------------------------------------------------------------------------- detection
def detect():
    arch = platform.machine().lower()
    info = {"os": "windows" if IS_WIN else ("macos" if IS_MAC else "linux"), "arch": arch, "gpu": "cpu", "gpu_name": None}
    if have("nvidia-smi"):
        r = run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"])
        if r.returncode == 0 and r.stdout.strip():
            info.update(gpu="nvidia", gpu_name=r.stdout.strip().splitlines()[0])
    elif IS_MAC and arch == "arm64":
        info.update(gpu="apple", gpu_name=run(["sysctl", "-n", "machdep.cpu.brand_string"]).stdout.strip() or "Apple Silicon")
    return info


def check_python():
    v = sys.version_info
    if v < (3, 10):
        say("FAIL", "Python", f"{platform.python_version()} - need 3.10 or newer")
        sys.exit(1)
    if v >= (3, 14):
        say("WARN", "Python", f"{platform.python_version()} - faster-whisper / torch wheels may lag; 3.11-3.13 is safest")
    else:
        say("OK", "Python", platform.python_version())


def ensure_tool(name, exe, win_pkg, mac_pkg, a, version_flag="-version"):
    if have(exe):
        out = run([exe, version_flag]).stdout
        say("OK", name, out.splitlines()[0][:80] if out else exe)
        return True
    if IS_WIN and have("winget"):
        cmd = ["winget", "install", "-e", "--id", win_pkg, "--accept-source-agreements", "--accept-package-agreements"]
    elif IS_MAC and have("brew"):
        cmd = ["brew", "install", mac_pkg]
    else:
        say("NEEDS YOU", name, f"install it ({'winget install ' + win_pkg if IS_WIN else 'brew install ' + mac_pkg}) and re-run")
        return False
    if not ask(f"{name} is missing. Run `{' '.join(cmd)}`?", a):
        say("NEEDS YOU", name, f"run: {' '.join(cmd)}")
        return False
    r = subprocess.run(cmd)
    if r.returncode == 0:
        say("FIXED", name, "installed - open a new terminal if it is not found yet")
        return have(exe)
    say("FAIL", name, f"`{' '.join(cmd)}` failed")
    return False


def pick_encoder(gpu):
    """The fastest H.264 encoder that really works here (a build can list nvenc without a usable GPU)."""
    encs = run(["ffmpeg", "-hide_banner", "-encoders"]).stdout
    order = (["h264_nvenc"] if gpu == "nvidia" else []) + (["h264_videotoolbox"] if IS_MAC else []) + ["libx264"]
    for enc in order:
        if enc not in encs:
            continue
        r = run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=1280x720:r=30:d=0.5", "-c:v", enc,
                 "-f", "null", "-"])
        if r.returncode == 0:
            return enc
    return "libx264"


def pick_hwaccel(gpu):
    accels = run(["ffmpeg", "-hide_banner", "-hwaccels"]).stdout.split()
    if gpu == "nvidia" and "cuda" in accels:
        return "cuda"
    if IS_MAC and "videotoolbox" in accels:
        return "videotoolbox"
    return None


def check_node(a):
    if not ensure_tool("Node.js", "node", "OpenJS.NodeJS.LTS", "node", a, "--version"):
        return False
    major = int(run(["node", "--version"]).stdout.strip().lstrip("v").split(".")[0] or 0)
    if major < 22:
        say("NEEDS YOU", "Node.js version", f"v{major} - HyperFrames needs 22 or newer")
        return False
    return True


def npm_install(a):
    hf = os.path.join(ROOT, "node_modules", "hyperframes", "package.json")
    if os.path.exists(hf) and json.load(open(hf, encoding="utf-8"))["version"] == "0.8.184":
        say("OK", "npm packages", "hyperframes 0.8.184, gsap, fontsource, simple-icons")
        return True
    if a.check:
        say("NEEDS YOU", "npm packages", "run python setup.py (npm install)")
        return False
    lock = os.path.exists(os.path.join(ROOT, "package-lock.json"))
    r = subprocess.run(npm_cmd("ci" if lock else "install", "--no-fund", "--no-audit"), cwd=ROOT)
    if r.returncode:
        say("FAIL", "npm packages", "npm install failed (see above)")
        return False
    say("FIXED", "npm packages", "installed")
    return True


def check_chrome(a):
    r = run(npx_cmd("hyperframes", "browser", "path"), cwd=ROOT)
    if r.returncode == 0 and r.stdout.strip():
        say("OK", "Chrome for HyperFrames", r.stdout.strip().splitlines()[-1][-90:])
        return True
    if a.check:
        say("NEEDS YOU", "Chrome for HyperFrames", "run: npx hyperframes browser ensure")
        return False
    r = subprocess.run(npx_cmd("hyperframes", "browser", "ensure"), cwd=ROOT)
    say("FIXED" if r.returncode == 0 else "FAIL", "Chrome for HyperFrames", "downloaded" if r.returncode == 0 else "npx hyperframes browser ensure failed")
    return r.returncode == 0


# ------------------------------------------------------------------------------------------------------ python venv
def ensure_venv(a):
    if not os.path.exists(VPY):
        if a.check:
            say("NEEDS YOU", "Python venv", ".venv missing - run python setup.py")
            return False
        subprocess.run([sys.executable, "-m", "venv", VENV], check=True)
        run([VPY, "-m", "pip", "install", "-q", "--upgrade", "pip"])
    missing = run([VPY, "-c", "import faster_whisper, numpy, cv2, PIL, playwright"]).returncode
    if not a.check:
        # always (fast when satisfied): keeps the version pins in requirements.txt enforced on existing venvs
        r = subprocess.run([VPY, "-m", "pip", "install", "-q", "-r", os.path.join(ROOT, "requirements.txt")])
        if r.returncode:
            say("FAIL", "Python packages", "pip install -r requirements.txt failed")
            return False
        say("FIXED" if missing else "OK", "Python packages", "faster-whisper, numpy, opencv, pillow, playwright in .venv")
        missing = 0
    elif missing:
        say("NEEDS YOU", "Python packages", "run python setup.py")
        return False
    else:
        say("OK", "Python packages", ".venv has faster-whisper, numpy, opencv, pillow, playwright")
    pw = run([VPY, "-c", "from playwright.sync_api import sync_playwright as s\nwith s() as p: print(p.chromium.executable_path)"])
    exe = pw.stdout.strip().splitlines()[-1] if pw.returncode == 0 and pw.stdout.strip() else ""
    if exe and os.path.exists(exe):
        say("OK", "Playwright Chromium (screenshots)")
    elif not a.check:
        r = subprocess.run([VPY, "-m", "playwright", "install", "chromium"])
        say("FIXED" if r.returncode == 0 else "WARN", "Playwright Chromium (screenshots)",
            "installed" if r.returncode == 0 else "playwright install chromium failed - screenshots will not work")
    else:
        say("NEEDS YOU", "Playwright Chromium (screenshots)", ".venv python -m playwright install chromium")
    return True


def ensure_torch(info, a):
    code = ("import torch;d='cuda' if torch.cuda.is_available() else ('mps' if getattr(torch.backends,'mps',None) and "
            "torch.backends.mps.is_available() else 'cpu');print(torch.__version__, d)")
    r = run([VPY, "-c", code])
    want = {"nvidia": "cuda", "apple": "mps"}.get(info["gpu"], "cpu")
    if r.returncode == 0:
        ver, dev = r.stdout.split()[-2:]
        if dev == want:
            say("OK", "torch (cut-out model)", f"{ver} on {dev}")
            return dev
        if a.check:
            say("WARN", "torch (cut-out model)", f"{ver} runs on {dev}, expected {want}")
            return dev
    elif a.check:
        say("NEEDS YOU", "torch (cut-out model)", "not installed - run python setup.py (or --no-matte)")
        return None
    if info["gpu"] == "nvidia":
        idx = ["--index-url", "https://download.pytorch.org/whl/cu128"]    # CUDA 12.8 wheels (needed for RTX 50xx)
    elif IS_MAC:
        idx = []                                                          # default macOS wheels include MPS
    else:
        idx = ["--index-url", "https://download.pytorch.org/whl/cpu"]
    print(f"  installing torch for {want} (large download)...", flush=True)
    rr = subprocess.run([VPY, "-m", "pip", "install", "--upgrade", "torch", "torchvision", *idx])
    if rr.returncode:
        say("FAIL", "torch (cut-out model)", "pip install torch failed")
        return None
    r = run([VPY, "-c", code])
    dev = r.stdout.split()[-1] if r.returncode == 0 else None
    say("FIXED" if dev else "FAIL", "torch (cut-out model)", f"runs on {dev}")
    return dev


def ensure_rvm(a):
    code_dir = os.path.join(ROOT, "vendor", "RobustVideoMatting")
    if os.path.exists(os.path.join(code_dir, "model", "__init__.py")):
        say("OK", "Robust Video Matting code", f"vendor/RobustVideoMatting ({RVM_COMMIT[:7]}, GPL-3.0, not committed)")
    elif a.check:
        say("NEEDS YOU", "Robust Video Matting code", "run python setup.py")
    else:
        with tempfile.TemporaryDirectory() as td:
            z = os.path.join(td, "rvm.zip")
            download(RVM_ZIP, z)
            with zipfile.ZipFile(z) as zf:
                zf.extractall(td)
            src = os.path.join(td, f"RobustVideoMatting-{RVM_COMMIT}")
            os.makedirs(os.path.dirname(code_dir), exist_ok=True)
            if os.path.exists(code_dir):
                shutil.rmtree(code_dir)
            shutil.copytree(src, code_dir)
        say("FIXED", "Robust Video Matting code", f"downloaded {RVM_COMMIT[:7]} (GPL-3.0)")
    wdir = os.path.join(ROOT, "vendor", "rvm-weights")
    for name, digest in RVM_WEIGHTS.items():
        p = os.path.join(wdir, name)
        if os.path.exists(p) and sha256(p) == digest:
            continue
        if a.check:
            say("NEEDS YOU", f"RVM weights {name}", "run python setup.py")
            continue
        download(RVM_RELEASE + name, p)
        if sha256(p) != digest:
            os.remove(p)
            say("FAIL", f"RVM weights {name}", "checksum mismatch - download removed")
            continue
        say("FIXED", f"RVM weights {name}", "downloaded + verified")
    if all(os.path.exists(os.path.join(wdir, n)) for n in RVM_WEIGHTS):
        say("OK", "RVM weights", "rvm_mobilenetv3.pth + rvm_resnet50.pth (SHA-256 verified)")


# ------------------------------------------------------------------------------------------------------- shared assets
def ensure_assets(a):
    nm = os.path.join(ROOT, "node_modules")
    if not os.path.exists(os.path.join(nm, "hyperframes")):
        say("SKIP", "shared assets", "needs npm packages first")
        return
    out = os.path.join(ROOT, "assets")
    copied = 0
    # sound effects: HyperFrames' bundled Pixabay set (Pixabay Content License - not committed to this repo)
    sfx_src = os.path.join(nm, "hyperframes", "dist", "skills", "media-use", "audio", "assets", "sfx")
    for dst in (os.path.join(out, "sfx"), os.path.join(ROOT, ".claude", "skills", "media-use", "audio", "assets", "sfx")):
        os.makedirs(dst, exist_ok=True)
        for f in os.listdir(sfx_src) if os.path.isdir(sfx_src) else []:
            if f.endswith(".mp3") and not os.path.exists(os.path.join(dst, f)) and not a.check:
                shutil.copy2(os.path.join(sfx_src, f), os.path.join(dst, f)); copied += 1
    for fam, files in FONTS.items():
        for f in files:
            src = os.path.join(nm, "@fontsource", fam, "files", f"{fam}-{f}.woff2")
            dst = os.path.join(out, "fonts", f"{fam}-{f}.woff2")
            if os.path.exists(src) and not os.path.exists(dst) and not a.check:
                os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(src, dst); copied += 1
    g = os.path.join(out, "vendor", "gsap.min.js")
    if not os.path.exists(g) and not a.check:
        os.makedirs(os.path.dirname(g), exist_ok=True); shutil.copy2(os.path.join(nm, "gsap", "dist", "gsap.min.js"), g); copied += 1
    n_sfx = len([f for f in os.listdir(os.path.join(out, "sfx")) if f.endswith(".mp3")]) if os.path.isdir(os.path.join(out, "sfx")) else 0
    say("FIXED" if copied else ("OK" if n_sfx else "NEEDS YOU"), "shared assets",
        f"assets/sfx ({n_sfx} sounds), assets/fonts, assets/vendor/gsap.min.js")


# ------------------------------------------------------------------------------------------------------------- config
def write_config(info, enc, hw, torch_dev, a):
    cfg = {}
    if os.path.exists(CONFIG):
        cfg = json.load(open(CONFIG, encoding="utf-8"))
    cfg.update({
        "os": info["os"], "arch": info["arch"], "gpu": info["gpu"], "gpu_name": info["gpu_name"],
        "encoder": enc, "hwaccel": hw,
        "whisper_device": "cuda" if info["gpu"] == "nvidia" else "cpu",
        "matte_device": torch_dev or {"nvidia": "cuda", "apple": "mps"}.get(info["gpu"], "cpu"),
        "python": VPY,
        "updated": time.strftime("%Y-%m-%d %H:%M"),
    })
    cfg.setdefault("recordings_dir", os.path.expanduser("~/Videos" if IS_WIN else "~/Movies"))
    cfg.setdefault("chrome", None)
    if a.check:
        say("OK" if os.path.exists(CONFIG) else "NEEDS YOU", "config/config.json", "exists" if os.path.exists(CONFIG) else "missing")
        return cfg
    os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
    json.dump(cfg, open(CONFIG, "w", encoding="utf-8"), indent=1)
    say("OK", "config/config.json", f"{cfg['os']} / {cfg['gpu']} / {enc} / whisper {cfg['whisper_device']} / matte {cfg['matte_device']}")
    prof = os.path.join(ROOT, "config", "profile.json")
    if not os.path.exists(prof):
        shutil.copy2(os.path.join(ROOT, "config", "profile.example.json"), prof)
        say("NEEDS YOU", "config/profile.json", "created from the example - fill in your brand (or say /claude-edit-setup)")
    else:
        brand = json.load(open(prof, encoding="utf-8")).get("brand_name")
        if brand in (None, "", "Your Brand"):
            say("WARN", "config/profile.json", "still the example brand - fill it in (or say /claude-edit-setup)")
        else:
            say("OK", "config/profile.json", brand)
    return cfg


# --------------------------------------------------------------------------------------------------------- smoke test
def smoke(cfg, do_matte):
    d = os.path.join(ROOT, "work", "_smoke")
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(d)
    py = VPY if os.path.exists(VPY) else sys.executable
    t0 = time.time()
    src = os.path.join(d, "source.mp4")
    r = run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=1920x1080:r=30:d=5", "-f", "lavfi", "-i",
             "sine=frequency=330:sample_rate=48000:duration=5", "-shortest", "-pix_fmt", "yuv420p", "-c:a", "aac", src])
    say("OK" if r.returncode == 0 else "FAIL", "smoke: synthetic 5 s clip", r.stderr.strip()[-120:])
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import common
    common._cache = None
    enc = os.path.join(d, "encoded.mp4")
    r = run(["ffmpeg", "-v", "error", "-y", *common.hwaccel_args(), "-i", src, "-an", *common.encoder_args("high"),
             "-pix_fmt", "yuv420p", enc])
    if r.returncode and common.hwaccel_args():
        r = run(common.strip_hw(["ffmpeg", "-v", "error", "-y", *common.hwaccel_args(), "-i", src, "-an",
                                 *common.encoder_args("high"), "-pix_fmt", "yuv420p", enc]))
    say("OK" if r.returncode == 0 else "FAIL", f"smoke: encode with {cfg['encoder']}", r.stderr.strip()[-160:])
    r = run([py, "-c", "import sys;sys.path.insert(0,'tools');import common;m=common.load_whisper('tiny');"
             "s,_=m.transcribe(sys.argv[1]);list(s);print(m.model.device)", src], cwd=ROOT, env=dict(os.environ, CLAUDE_EDIT_NO_VENV="1"))
    used = r.stdout.strip().splitlines()[-1] if r.returncode == 0 and r.stdout.strip() else ""
    status = "FAIL" if r.returncode else ("OK" if used == cfg["whisper_device"] else "WARN")
    say(status, f"smoke: faster-whisper (expected {cfg['whisper_device']})",
        f"tiny model ran on {used}" if r.returncode == 0 else r.stderr.strip()[-200:])
    if do_matte:
        r = run([py, os.path.join(ROOT, "tools", "matte.py"), src, os.path.join(d, "cut.webm")], cwd=ROOT)
        say("OK" if r.returncode == 0 else "FAIL", f"smoke: cut-out ({cfg['matte_device']})",
            (r.stdout.strip() or r.stderr.strip())[-200:])
    else:
        say("SKIP", "smoke: cut-out", "--no-matte")
    proj = os.path.join(d, "render")
    shutil.copytree(os.path.join(ROOT, "templates", "smoke"), proj)
    os.makedirs(os.path.join(proj, "assets"), exist_ok=True)
    for sub in ("fonts", "vendor"):
        shutil.copytree(os.path.join(ROOT, "assets", sub), os.path.join(proj, "assets", sub), dirs_exist_ok=True)
    shutil.copy2(enc if os.path.exists(enc) else src, os.path.join(proj, "assets", "clip.mp4"))
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-c:a", "aac", os.path.join(proj, "assets", "tone.m4a")])
    r = run([py, os.path.join(ROOT, "tools", "render.py"), "one", proj, "_smoke", "--quality", "draft"], cwd=ROOT)
    ok = r.returncode == 0 and os.path.exists(os.path.join(ROOT, "out", "_smoke.mp4"))
    dur = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
               os.path.join(ROOT, "out", "_smoke.mp4")]).stdout.strip() if ok else ""
    say("OK" if ok else "FAIL", "smoke: 5 s HyperFrames render -> out/_smoke.mp4",
        f"{dur} s" if ok else (r.stdout + r.stderr).strip()[-300:])
    say("OK", "smoke: total", f"{time.time() - t0:.0f} s")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--no-matte", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--import-pack")
    a = ap.parse_args()

    print("claude-edit setup" + (" (check only)" if a.check else ""), flush=True)
    info = detect()
    say("OK", "machine", f"{info['os']} {info['arch']}, GPU: {info['gpu_name'] or 'none (CPU)'}")
    if IS_MAC:
        say("WARN", "macOS support", "implemented but not yet tested on a Mac - please report what fails")
    check_python()
    ff = ensure_tool("ffmpeg", "ffmpeg", "Gyan.FFmpeg", "ffmpeg", a)
    enc = pick_encoder(info["gpu"]) if ff else "libx264"
    hw = pick_hwaccel(info["gpu"]) if ff else None
    if ff:
        say("OK", "video encoder", f"{enc}" + (f", decode {hw}" if hw else ""))
    node = check_node(a)
    if node:
        npm_install(a) and check_chrome(a)
    ensure_venv(a)
    torch_dev = None
    if a.no_matte:
        say("SKIP", "cut-out model", "--no-matte (cut-out formats and /claude-edit-versus need it)")
    elif os.path.exists(VPY):
        torch_dev = ensure_torch(info, a)
        ensure_rvm(a)
    if info["gpu"] == "nvidia" and os.path.exists(VPY) and not a.check and run([VPY, "-c", "import torch"]).returncode:
        # no torch to borrow cuBLAS / cuDNN from: GPU Whisper needs them as pip packages
        r = run([VPY, "-m", "pip", "install", "-q", "nvidia-cublas-cu12", "nvidia-cudnn-cu12>=9,<10"])
        say("FIXED" if r.returncode == 0 else "WARN", "CUDA libraries for Whisper",
            "cuBLAS + cuDNN installed" if r.returncode == 0 else "install failed - Whisper will run on the CPU")
    ensure_assets(a)
    cfg = write_config(info, enc, hw, torch_dev, a)
    have = all(os.path.isdir(os.path.join(ROOT, "formats", s))
               for s in ("business-short-form-reels", "explainer-panel-reel", "glass-explainer-reel"))
    if a.import_pack or (not have and not a.check and os.path.isdir(os.path.join(ROOT, "assets", "fonts"))):
        r = subprocess.run([VPY if os.path.exists(VPY) else sys.executable, os.path.join(ROOT, "tools", "import_formats.py")]
                           + ([a.import_pack] if a.import_pack else []))
        what = "all 10 imported" if a.import_pack else "rotation, frost, popout installed"
        say("OK" if r.returncode == 0 else "FAIL", "layout formats", what if r.returncode == 0 else "import failed")
    elif have:
        say("OK", "layout formats", "installed")
    if a.smoke and not a.check:
        smoke(cfg, not a.no_matte)

    bad = [r for r in results if r[0] in ("FAIL", "NEEDS YOU")]
    print("\n" + ("All set. Open this folder in Claude Code and type: /claude-edit <your video>" if not bad else
                  f"{len(bad)} item(s) need attention:\n" + "\n".join(f"  - {w}: {d}" for _, w, d in bad)))
    sys.exit(1 if any(r[0] == "FAIL" for r in results) else 0)


if __name__ == "__main__":
    main()
