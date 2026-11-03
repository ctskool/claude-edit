"""Check a claude-edit installation without installing, downloading, or rendering."""
import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

sys.dont_write_bytecode = True

try:
    from .paths import project_root
except ImportError:
    from paths import project_root

MIN_PYTHON = (3, 10)
MIN_NODE = 22
HF_PIN = "0.8.184"  # tools/beat_render/{run.py,hf.mjs}
GIB = 1024 ** 3
# Derived from imports throughout tools/, including imports inside functions.
# Optional means the normal split edit can run without that feature after audit edits.
PACKAGES = {
    "numpy": ("numpy", False),
    "PIL": ("Pillow", False),
    "cv2": ("opencv-python", False),
    "playwright": ("playwright", False),
    "faster_whisper": ("faster-whisper", False),
    "torch": ("torch", True),
    "transformers": ('"transformers>=5.13,<6"', True),
    "soundfile": ("soundfile", True),
    "demucs": ("-e _ext/demucs-lib", True),
    "earshot": ("-e _ext/earshot", True),
}
IMPORT_PROBES = {
    "PIL": "from PIL import Image, ImageDraw, ImageFont",
    "playwright": "from playwright.sync_api import sync_playwright",
    "faster_whisper": "from faster_whisper import WhisperModel",
    "transformers": "from transformers import AutoModelForTokenClassification, AutoProcessor",
    "demucs": "from demucs.hf import get_hf_model; from demucs.apply import apply_model",
    "earshot": "from earshot.forge import bank",
}
FIX = {
    "python": ("winget install --exact --id Python.Python.3.12", "brew install python@3.12"),
    "node": ("winget install --exact --id OpenJS.NodeJS.LTS", "brew install node"),
    "ffmpeg": ("winget install --exact --id Gyan.FFmpeg", "brew install ffmpeg-full && brew unlink ffmpeg; brew link --force ffmpeg-full"),
    "browser": ("winget install --exact --id Google.Chrome", "brew install --cask google-chrome"),
    "disk": ('Start-Process "ms-settings:storagesense"', 'open "x-apple.systempreferences:com.apple.settings.Storage"'),
}


@dataclass
class Check:
    status: str
    name: str
    detail: str
    windows: str
    macos: str
    hint: str = ""


def result(status, name, detail, commands, hint=""):
    return Check(status, name, detail, commands[0], commands[1], hint)


def same(command):
    return command, command


def run(command, root, timeout=20):
    """No shell; bound every probe, and never write Python bytecode."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", HF_HUB_OFFLINE="1")
    try:
        p = subprocess.run([str(x) for x in command], cwd=root, env=env,
                           capture_output=True, text=True, errors="replace", timeout=timeout)
        return p.returncode, (p.stdout + "\n" + p.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)


def npm_command(name, *args):
    """Use npm's JS entry on Windows, avoiding shell quoting and .cmd launch issues."""
    exe = shutil.which(name)
    if not exe:
        return None
    if Path(exe).suffix.lower() in (".cmd", ".bat"):
        script = Path(exe).parent / "node_modules" / "npm" / "bin" / (name + "-cli.js")
        node = shutil.which("node")
        return [node, str(script), *args] if node and script.is_file() else None
    return [exe, *args]


def inventory(root):
    """Read imports, excluding stdlib, relative imports and modules shipped in tools/."""
    files = sorted((root / "tools").rglob("*.py"))
    # Modules the repo ships elsewhere (the build kit's new_project.py, for one) are local too.
    local = {p.stem for p in files} | {p.stem for p in (root / "templates").rglob("*.py")} | {"tools", "model"}
    local |= {p.name for p in (root / "tools").iterdir() if p.is_dir()}
    found, errors = {}, []
    for path in files:
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        except (OSError, SyntaxError, UnicodeError) as e:
            errors.append(str(e))
            continue
        for item in ast.walk(tree):
            names = []
            if isinstance(item, ast.Import):
                names = [a.name.split(".")[0] for a in item.names]
            elif isinstance(item, ast.ImportFrom) and not item.level and item.module:
                names = [item.module.split(".")[0]]
            for name in names:
                if name not in sys.stdlib_module_names and name not in local:
                    found.setdefault(name, []).append(f"{path.relative_to(root)}:{item.lineno}")
    return found, errors


def check_python(version=None):
    version = sys.version_info[:3] if version is None else version
    ok = tuple(version[:2]) >= MIN_PYTHON
    return result("PASS" if ok else "FAIL", "Python", ".".join(map(str, version)) + "; need 3.10+",
                  FIX["python"], "Use the same active virtual environment for pip, doctor and Claude Code.")


def check_packages(root):
    found, errors = inventory(root)
    rows = [result("FAIL" if errors else "PASS", "import inventory",
                   "; ".join(errors) if errors else f"read all tools/**/*.py; {len(found)} external imports",
                   same("python -m compileall -q tools"), "A parse/read failure must be repaired before trusting this inventory.")]
    # The fixed map also checks packages if a student received only the core tools.
    for name in sorted(set(PACKAGES) | set(found)):
        if name not in PACKAGES:
            rows.append(result("FAIL", "package " + name, "unmapped external import: " + ", ".join(found[name]),
                               same("python -m pip install -r requirements.txt"),
                               "Identify the owning distribution and update the doctor map and requirements; do not guess a PyPI name."))
            continue
        package, optional = PACKAGES[name]
        code = IMPORT_PROBES.get(name, "import " + name)
        if name in ("demucs", "earshot"):
            folder = "demucs-lib" if name == "demucs" else "earshot"
            code = "import sys; sys.path.insert(0, " + repr(str(root / "_ext" / folder)) + "); " + code
        rc, out = run([sys.executable, "-B", "-c", code], root)
        rows.append(result("PASS" if rc == 0 else "WARN" if optional else "FAIL", "package " + name,
                           "import works" if rc == 0 else out[-400:], same("python -m pip install " + package),
                           ("Optional: alignment/popout (torch/transformers), reference stems (demucs.hf), or sound-bank development (soundfile/earshot). "
                            "The Demucs checkout must expose demucs.hf; installing arbitrary PyPI demucs is insufficient.") if optional else ""))
    return rows


TRANSCRIPTION_PROBE = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
from asr import cuda_dll_dirs
cuda_dll_dirs()
import ctranslate2
import numpy as np
from faster_whisper import WhisperModel
error = ""
try:
    types = ctranslate2.get_supported_compute_types("cuda")
    if "float16" not in types:
        raise RuntimeError("CUDA float16 unavailable")
    m = WhisperModel("large-v3", device="cuda", compute_type="float16", local_files_only=True)
    list(m.transcribe(np.zeros(16000, dtype=np.float32))[0])
    print(json.dumps({"status": "PASS", "detail": "large-v3 CUDA float16: cached model encoded one second of silence"}))
    sys.exit(0)
except Exception as e:
    error = str(e)[:240]
try:
    types = ctranslate2.get_supported_compute_types("cpu")
    if "int8" not in types:
        raise RuntimeError("CPU int8 unavailable")
    try:
        m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", local_files_only=True)
        list(m.transcribe(np.zeros(16000, dtype=np.float32))[0])
        detail = "CPU large-v3-turbo int8 encoded silence"
    except Exception as e:
        detail = "CPU int8 runtime available; cached turbo model not verified: " + str(e)[:180]
    print(json.dumps({"status": "WARN", "detail": detail + "; much slower (~20x on the author's GPU machine); CUDA large-v3 not verified: " + error}))
except Exception as e:
    print(json.dumps({"status": "FAIL", "detail": "No usable CPU/CUDA runtime: " + str(e)[:240] + "; CUDA: " + error}))
'''


def check_transcription(root):
    rc, out = run([sys.executable, "-B", "-c", TRANSCRIPTION_PROBE, str(root / "tools")], root, timeout=60)
    data = None
    for line in reversed(out.splitlines()):
        try:
            candidate = json.loads(line)
            if isinstance(candidate, dict) and candidate.get("status") in ("PASS", "WARN", "FAIL"):
                data = candidate
                break
        except ValueError:
            pass
    data = data if rc == 0 and data else {"status": "FAIL", "detail": out[-500:] or "probe did not finish"}
    cpu = 'python -c "from faster_whisper import WhisperModel; WhisperModel(\'large-v3-turbo\', device=\'cpu\', compute_type=\'int8\')"'
    cuda = 'python -m pip install nvidia-cublas-cu12 "nvidia-cudnn-cu12>=9,<10"'
    if data["status"] == "PASS":
        win_fix = 'python -c "import sys; sys.path.insert(0,\'tools\'); from asr import load_whisper; load_whisper(\'large-v3\')"'
    elif "cublas" in data["detail"].lower() or "cudnn" in data["detail"].lower():
        win_fix = cuda
    elif data["status"] == "FAIL":
        win_fix = "python -m pip install --upgrade faster-whisper"
        cpu = win_fix
    else:
        win_fix = cpu
    return result(data["status"], "transcription", data["detail"], (win_fix, cpu),
                  "No model downloads here. The normal loader tries large-v3 on CUDA, then turbo int8 on CPU, including on Apple Silicon. "
                  "Windows needs cuBLAS 12/cuDNN 9 DLL folders on PATH before lazy first encode: tools/asr.py already adds nvidia/*/bin and torch/lib. "
                  "See reports/transcription-2026-10-30/REPORT.md. GPU cache warmup is documented in INSTALL.md; never treat nvidia-smi alone as proof.")


def check_command(name, root, minimum=None, optional=False):
    command = npm_command(name, "--version") if name in ("npm", "npx") else ([shutil.which(name), "--version"] if shutil.which(name) else None)
    if name in ("ffmpeg", "ffprobe") and command:
        command[-1] = "-version"
    # npm-installed Codex has a .cmd shim; Node runs its JS entry directly.
    if name == "codex" and command and Path(command[0]).suffix.lower() == ".cmd":
        script = Path(command[0]).parent / "node_modules/@openai/codex/bin/codex.js"
        command = [shutil.which("node") or "node", str(script), "--version"]
    rc, out = run(command, root) if command else (1, name + " not found on PATH")
    ok = rc == 0
    if minimum and ok:
        match = re.search(r"v?(\d+)\.", out)
        ok = bool(match and int(match[1]) >= minimum)
    fixes = FIX["node"] if name in ("node", "npm") else FIX.get(name, FIX["ffmpeg"])
    if name == "codex":
        fixes = same("npm install -g @openai/codex")
    if name == "claude":
        fixes = ('irm https://claude.ai/install.ps1 | iex', 'curl -fsSL https://claude.ai/install.sh | bash')
    return result("PASS" if ok else "WARN" if optional else "FAIL", name,
                  (out.splitlines()[0] if out else "no version output") + (f"; need {minimum}+" if minimum else ""), fixes,
                  "Optional: scene images and a second Codex reviewer. Without it, pass codex: false and use two Claude reviewers." if name == "codex" else "")


def check_hyperframes(root):
    fixes = same("npm install --save-dev --save-exact hyperframes@" + HF_PIN)
    command = npm_command("npx", "--no-install", "hyperframes", "--version")
    rc, out = run(command, root) if command else (1, "npx not reachable")
    try:
        version = json.loads((root / "node_modules/hyperframes/package.json").read_text(encoding="utf8"))["version"]
    except (OSError, ValueError, KeyError):
        version = "missing"
    ok = rc == 0 and version == HF_PIN
    return result("PASS" if ok else "FAIL", "HyperFrames", f"local {version}, required {HF_PIN}; npx exit {rc}; {out[:160]}", fixes,
                  "The renderer imports pinned internal APIs. A reachable newer global CLI is insufficient. No render or automatic npx install is attempted.")


def check_node_packages(root):
    code = "for (const p of ['gsap','@fontsource/newsreader','@fontsource/inter','@fontsource/jetbrains-mono']) require.resolve(p+'/package.json');"
    rc, out = run([shutil.which("node") or "node", "-e", code], root)
    return result("PASS" if rc == 0 else "FAIL", "Node assets", "GSAP and ivory fonts resolve" if rc == 0 else out[-300:], same("npm ci"))


def browser_candidates(system=None, env=None, home=None):
    env = os.environ if env is None else env
    home = Path.home() if home is None else Path(home)
    system = sys.platform if system is None else system
    candidates = [env[k] for k in ("CHROME_PATH", "CHROME_BIN", "PUPPETEER_EXECUTABLE_PATH", "HYPERFRAMES_BROWSER_PATH") if env.get(k)]
    if system == "win32":
        for prefix in (env.get("PROGRAMFILES", "C:/Program Files"), env.get("PROGRAMFILES(X86)", "C:/Program Files (x86)"), env.get("LOCALAPPDATA", str(home / "AppData/Local"))):
            candidates.extend(str(Path(prefix) / rel) for rel in ("Google/Chrome/Application/chrome.exe", "Microsoft/Edge/Application/msedge.exe"))
    elif system == "darwin":
        # macOS paths stay POSIX even when this runs (or is tested) on Windows.
        for prefix in (PurePosixPath("/Applications"), PurePosixPath(home.as_posix()) / "Applications"):
            candidates.extend(str(prefix / rel) for rel in ("Google Chrome.app/Contents/MacOS/Google Chrome", "Microsoft Edge.app/Contents/MacOS/Microsoft Edge"))
    candidates.extend(p for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "chrome", "msedge") if (p := shutil.which(name)))
    return candidates


def check_browsers(root):
    found = next((p for p in browser_candidates() if Path(p).is_file() and os.access(p, os.X_OK)), None)
    rows = [result("PASS" if found else "FAIL", "Chrome/Edge", found or "no browser executable found", FIX["browser"],
                   "Discovery only; no browser is launched. CHROME_PATH can name a custom executable.")]
    code = "from pathlib import Path; from playwright.sync_api import sync_playwright; p=sync_playwright().start(); e=p.chromium.executable_path; p.stop(); assert Path(e).is_file(), e; print(e)"
    rc, out = run([sys.executable, "-B", "-c", code], root)
    rows.append(result("PASS" if rc == 0 else "FAIL", "Playwright Chromium", out if rc == 0 else out[-300:], same("python -m playwright install chromium"),
                       "capture_shots.py and post_card.py launch the Playwright-managed Chromium, independent of system Chrome/Edge."))
    # Both browser path and findBrowser can download; only findSystemBrowser is read-only.
    override = os.environ.get("HYPERFRAMES_BROWSER_PATH") or os.environ.get("PUPPETEER_EXECUTABLE_PATH")
    if override and Path(override).is_file():
        rows.append(result("PASS", "HyperFrames browser", override, same("npx hyperframes browser ensure")))
        return rows
    code = ("const fs=require('fs'),path=require('path'); const {pathToFileURL}=require('url'); "
            "const d=path.join(path.dirname(require.resolve('hyperframes/package.json')),'dist'); "
            "const f=fs.readdirSync(d).find(f=>f.endsWith('.js')&&fs.readFileSync(path.join(d,f),'utf8').includes('async function findBrowser(')); "
            "if(!f)throw Error('browser finder not found'); import(pathToFileURL(path.join(d,f)).href).then(async m=>{const b=m.findSystemBrowser();if(!b)throw Error('no system browser; set HYPERFRAMES_BROWSER_PATH');console.log(b.executablePath)}).catch(e=>{console.error(e.message);process.exitCode=1});")
    rc, out = run([shutil.which("node") or "node", "-e", code], root)
    rows.append(result("PASS" if rc == 0 else "FAIL", "HyperFrames browser", out if rc == 0 else out[-300:], same("npx hyperframes browser ensure"),
                       "Checks pinned HyperFrames' system finder without launching Chrome or downloading. A managed-cache-only installation needs HYPERFRAMES_BROWSER_PATH."))
    return rows


def check_disk(root, free=None):
    try:
        free = shutil.disk_usage(root).free if free is None else free
        status = "FAIL" if free < 5 * GIB else "WARN" if free < 25 * GIB else "PASS"
        detail = f"{free / GIB:.1f} GiB free on project volume; 5 GiB minimum, 25 GiB recommended"
    except OSError as e:
        status, detail = "FAIL", str(e)
    return result(status, "disk space", detail, FIX["disk"],
                  "Opens storage settings; manually free space, then rerun doctor. Raw footage, browser/model caches and finals can need much more. Nothing is deleted.")


def check_layout(root):
    needed = (".claude/skills/claude-edit/SKILL.md", "templates/HOUSE.md", "templates/ivory/TEMPLATE.md", "templates/ivory/build_kit", "templates/ivory/build_kit/assets/fonts", "templates/ivory/build_kit/assets/vendor/gsap.min.js", "templates/ivory/sfx/sfx.json", "tools/asr.py", "examples/ivory-edit/v2/editorial/plan.json", "package.json", "package-lock.json")
    missing = [p for p in needed if not (root / p).exists()]
    return result("FAIL" if missing else "PASS", "project files", "missing: " + ", ".join(missing) if missing else str(root),
                  same("git clone https://github.com/ctskool/claude-edit.git"),
                  "Clone the whole repository (including the hidden .claude folder), not just SKILL.md.")



def check_ffmpeg_features(root):
    rc, out = run([shutil.which("ffmpeg") or "ffmpeg", "-hide_banner", "-encoders"], root)
    missing = [name for name in ("libx264", "aac", "libvpx-vp9") if not re.search(r"\b" + re.escape(name) + r"\b", out)]
    return result("PASS" if rc == 0 and not missing else "FAIL", "ffmpeg encoders",
                  "libx264, aac, libvpx-vp9 available (listed only; no encoding)" if rc == 0 and not missing else "missing/unreadable: " + ", ".join(missing),
                  FIX["ffmpeg"], "NVIDIA encoding is optional only after the rawcut software fallback in the audit is applied.")


def check_ffmpeg_filters(root):
    """Homebrew's plain ffmpeg has no drawtext, which finish.py's contact sheet needs; ffmpeg-full has it."""
    rc, out = run([shutil.which("ffmpeg") or "ffmpeg", "-hide_banner", "-filters"], root)
    ok = rc == 0 and re.search(r"\bdrawtext\b", out)
    return result("PASS" if ok else "FAIL", "ffmpeg filters",
                  "drawtext available (listed only)" if ok else "drawtext missing: the final delivery's contact sheet will fail",
                  FIX["ffmpeg"], "On a Mac, Homebrew's ffmpeg lacks drawtext; use ffmpeg-full.")


def check_optional_assets(root):
    missing = [p for p in ("vendor/RobustVideoMatting/model", "vendor/rvm-weights/rvm_resnet50.pth") if not (root / p).exists()]
    rows = [result("WARN" if missing else "PASS", "popout assets (optional)",
                   "missing: " + ", ".join(missing) if missing else "RVM code and default weights present; CUDA execution not checked",
                   same("see INSTALL.md, Optional: popout"),
                   "Split is the default and needs none of this. Popout needs an NVIDIA GPU and Robust Video Matting (GPL-3.0), which you install yourself from its own GitHub.")]
    try:
        palette = json.loads((root / "templates/ivory/sfx/sfx.json").read_text(encoding="utf8"))
        fetched = {n for f in json.loads((root / "templates/ivory/sfx/fetch.json").read_text(encoding="utf8"))["files"] for n in f["sounds"]}
        missing = [name for name in palette["sounds"] if not (root / "templates/ivory/sfx" / f"{name}.wav").is_file()]
        detail = (f"{len(palette['sounds']) - len(missing)} of {len(palette['sounds'])} slices ready; missing: " + ", ".join(missing)) if missing else "every palette slice is ready"
    except (OSError, ValueError, KeyError, TypeError) as e:
        fetched, missing, detail = set(), ["palette"], str(e)
    only_fetch = bool(missing) and set(missing) <= fetched
    rows.append(result("WARN" if missing else "PASS", "sound palette", detail,
                       same("python tools/fetch_sounds.py") if only_fetch else same("git checkout -- templates/ivory/sfx"),
                       "Some sounds may be used in videos but not passed on, so they never ship: fetch_sounds.py downloads them on this machine and cuts their slices. "
                       "Until then the sound step plans without them." if only_fetch else "A shipped slice is missing: restore templates/ivory/sfx from git."))
    return rows



PERSONAL_PATH = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+" + "Chase" + r"\b|/Users/" + "Chase" + r"\b|/home/" + "chase" + r"\b", re.I)  # split so this line does not match itself
SCANNED = (".claude", "templates", "tools", "styles", "examples", "references", "scripts")
TEXT = {".py", ".js", ".mjs", ".md", ".json", ".html", ".css", ".txt", ".sh"}


def check_portability(root):
    """Absolute paths from the author's machine left in shipped files. Each one breaks on any other computer."""
    hits = []
    for top in SCANNED:
        for file in sorted((root / top).rglob("*")):
            if file.suffix not in TEXT or not file.is_file() or "__pycache__" in file.parts or "node_modules" in file.parts:
                continue
            try:
                if PERSONAL_PATH.search(file.read_text(encoding="utf8", errors="ignore")):
                    hits.append(file.relative_to(root).as_posix())
            except OSError:
                continue
    return result("WARN" if hits else "PASS", "portable paths",
                  f"{len(hits)} file(s) still name the author's folders: " + ", ".join(hits[:12]) if hits else "no absolute paths from the author's machine",
                  same("python tools/doctor.py --fix-hints"),
                  "Tools find the project with tools/paths.py (CLAUDE_EDIT_ROOT overrides it). Replace each absolute path with one relative to the project root.")


def collect(root):
    rows = [check_python(), check_layout(root)]
    if sys.version_info < MIN_PYTHON:
        return rows  # inventory needs sys.stdlib_module_names (3.10).
    rows += check_packages(root)
    rows += [check_command("node", root, MIN_NODE), check_command("npm", root), check_hyperframes(root), check_node_packages(root)]
    rows += [check_command("ffmpeg", root), check_command("ffprobe", root), check_ffmpeg_features(root), check_ffmpeg_filters(root), check_transcription(root)]
    rows += check_optional_assets(root)
    rows += check_browsers(root)
    rows += [check_command("claude", root), check_command("codex", root, optional=True), check_disk(root)]
    rows.append(check_portability(root))
    return rows


def show(rows, fix_hints=False):
    for row in rows:
        detail = " ".join(str(row.detail).split())
        print(f"{row.status} {row.name}: {detail}")
        print(f"  Windows: {row.windows}")
        print(f"  macOS:   {row.macos}")
        if fix_hints and row.hint:
            print("  Hint: " + row.hint)
    counts = {s: sum(r.status == s for r in rows) for s in ("PASS", "WARN", "FAIL")}
    print("\n" + ", ".join(f"{counts[s]} {s}" for s in counts))
    return 1 if counts["FAIL"] else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fix-hints", action="store_true", help="explain fixes; never installs or changes anything")
    a = ap.parse_args(argv)
    try:
        rows = collect(project_root())
    except (OSError, ValueError) as e:
        rows = [result("FAIL", "doctor", str(e), same("python tools/doctor.py --fix-hints"), "Check CLAUDE_EDIT_ROOT and project read permissions.")]
    return show(rows, a.fix_hints)


if __name__ == "__main__":
    raise SystemExit(main())
