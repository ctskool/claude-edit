"""Import the Creator Skill Pack layout formats into formats/ and make them run on Windows + macOS.

  python tools/import_formats.py                                          the 3 bundled formats (rotation, frost, popout)
  python tools/import_formats.py <path to Creator-Skill-Pack/skills>      all 10, from your own copy of the pack
                                                                          (or: python setup.py --import-pack <path>)
  python tools/import_formats.py --refill                                 re-apply config/profile.json to imported formats

rotation, frost and popout ship in pack/ (redistributed with the pack author's permission; see pack/README.md). The other
seven need your own copy of the pack. This script copies the skills, applies the port fixes below as pattern rules, builds
the pack profile in formats/profile/ from config/profile.json + formats-kit/pack-defaults.json, and fills every
placeholder with the pack's own setup/apply_profile.py. formats/ is git-ignored.

Port fixes (each is a regex rule applied to engine/*.py and scripts/*.py):
  - GSAP from the project's assets/gsap.min.js instead of the jsDelivr CDN (renders offline, pinned 3.13)
  - person cut-out through tools/matte.py (Robust Video Matting on CUDA / MPS / CPU) instead of `hyperframes remove-background`
  - Windows font fallbacks (Arial, Segoe UI) next to the macOS ones; Windows-safe file:// URLs; shutil.rmtree for `rm -rf`
  - Chrome found by tools/common.chrome_path() (Windows, macOS, Linux) through $CLAUDE_EDIT_CHROME
  - ranking face boxes with OpenCV instead of a Swift / Apple Vision helper; business engine at 30 fps; decimals in captions
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import ROOT, profile  # noqa: E402

FMT = os.path.join(ROOT, "formats")
KIT = os.path.join(ROOT, "formats-kit")
PROFILE_DIR = os.path.join(FMT, "profile")
BUNDLED_DIR = os.path.join(ROOT, "pack")
BUNDLED = ["business-short-form-reels", "explainer-panel-reel", "glass-explainer-reel"]   # rotation, popout, frost
SKILLS = ["business-short-form-reels", "explainer-panel-reel", "depth-ui-reel", "fitted-stacked-captions", "glass-explainer-reel",
          "visual-essay-reel", "cutout-backdrop-reel", "cutout-grid-reel", "image-cluster-reel", "ranking-format"]
# repo fonts (fontsource, OFL) under the file names the pack profile expects
FONT_FILES = {"SpaceGrotesk-Bold.woff2": "space-grotesk-latin-700-normal.woff2",
              "SpaceGrotesk-Regular.woff2": "space-grotesk-latin-500-normal.woff2",
              "InterTight-ExtraBold.woff2": "inter-tight-latin-800-normal.woff2",
              "InstrumentSerif-Italic.woff2": "instrument-serif-latin-400-italic.woff2"}

MATTE = ('[os.environ.get("CLAUDE_EDIT_PY", sys.executable), os.path.join(os.environ.get("CLAUDE_EDIT_ROOT", "."), "tools", '
         '"matte.py"), \\2, \\3]')
FU_DEF = "import pathlib as _pl; FU = lambda p: _pl.Path(p).resolve().as_uri()   # Windows-safe file:// URL (claude-edit port)\n"

# (file glob relative to the skill, pattern, replacement, flags) - applied in order; each counts its hits
RULES = [
    ("*/*.py", r"https://cdn\.jsdelivr\.net/npm/gsap@[\d.]+/dist/gsap\.min\.js", "assets/gsap.min.js", 0),
    ("*/*.py", r"\[\s*(['\"])npx\1\s*,\s*\1hyperframes\1\s*,\s*\1remove-background\1\s*,\s*([^,\]]+?)\s*,\s*\1-o\1\s*,\s*([^,\]]+?)\s*,"
               r"\s*\1--quality\1\s*,\s*\1best\1\s*\]", MATTE, 0),
    ("*/*.py", r"(['\"])/Library/Fonts/Arial\.ttf\1", r"\g<0>, \1C:/Windows/Fonts/arial.ttf\1", 0),
    ("scripts/common.py", r"(?P<i>[ \t]*)except Exception:\n(?P<j>[ \t]*)return ImageFont\.load_default\(\)",
     "\\g<i>except Exception:\n\\g<j>pass\n\\g<i>try:\n\\g<j>return ImageFont.truetype(\"C:/Windows/Fonts/arial.ttf\", size)\n"
     "\\g<i>except Exception:\n\\g<j>return ImageFont.load_default()", 0),
    ("scripts/common.py", r"d = arg if os\.sep in arg else", 'd = arg if (os.sep in arg or "/" in arg) else', 0),
    ("*/*.py", r"file://'\s*\+\s*(\w+)\s*\+\s*'", r"'+FU(\1)+'", 0),
    ("*/*.py", r"(['\"])url\('file://%s'\)\1\s*%\s*(\w+)", r"\1url('%s')\1%FU(\2)", 0),
    ("*/*.py", r"file://\{([^{}]+)\}", r"{FU(\1)}", 0),
    ("*/*.py", r"subprocess\.run\(\[\s*'rm'\s*,\s*'-rf'\s*,\s*([^\]]+?)\s*\]\)", r"shutil.rmtree(\1, ignore_errors=True)", 0),
    ("*/*.py", r"os\.environ\.get\((['\"])CHROME\1\)", r"os.environ.get(\1CHROME\1), os.environ.get(\1CLAUDE_EDIT_CHROME\1)", 0),
    ("engine/kit.py", r'"SF Pro Text","HelvR"', '"SF Pro Text","Segoe UI","HelvR"', 0),
    ("engine/reel_engine.py", r'data-fps="24"', 'data-fps="30"', 0),
    ("engine/rank_engine.py", r'"MainF", Impact, sans-serif', '"MainF", sans-serif', 0),
    ("scripts/cluster_reel.py", r"re\.search\(r'\[\.\?!\]',c\)", r"re.search(r'[.?!]',re.sub(r'(?<=\\d)\\.(?=\\d)','',c))", 0),
    ("scripts/10_review.py", r'PJ = f"\{PROJECTS_ROOT\}/\{slug\}-panel"', 'PJ = os.environ.get("FMT_PROJECT") or f"{PROJECTS_ROOT}/{slug}-panel"', 0),
    ("scripts/layout.py", r'bin_ = os\.path\.join\(W, "face_boxes"\)\n.*?\.splitlines\(\)\n',
     "# claude-edit port: OpenCV Haar faces instead of the Swift / Apple Vision helper (same rows \"path x y w h\"). The Haar box\n"
     "# runs mid-forehead to the mouth; its height is scaled so the \"* 1.06\" chin rule below lands on the chin.\n"
     "import cv2\n"
     "_det = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, \"haarcascade_frontalface_default.xml\")); out = []\n"
     "for _f in frames:\n"
     "    _g = cv2.imread(_f, cv2.IMREAD_GRAYSCALE); _r = _det.detectMultiScale(_g, 1.1, 6, minSize=(160, 160))\n"
     "    if len(_r):\n"
     "        _x, _y, _w, _h = max(_r, key=lambda b: b[2] * b[3]); out.append(f\"{_f} {_x} {_y} {_w} {_h * 1.22 / 1.06:.1f}\")\n",
     re.S),
]


def patch_skill(d):
    hits = {}
    for k, (pat_glob, pat, rep, flags) in enumerate(RULES):
        for f in glob.glob(os.path.join(d, pat_glob)):
            s = open(f, encoding="utf-8").read()
            s2, n = re.subn(pat, rep, s, flags=flags)
            if n:
                if "FU(" in s2 and "FU = lambda" not in s2:
                    s2 = re.sub(r"^(import [^\n]+\n)", lambda m: m.group(1) + FU_DEF, s2, count=1, flags=re.M)
                if "shutil.rmtree" in s2 and not re.search(r"^import .*\bshutil\b", s2, re.M):
                    s2 = re.sub(r"^(import [^\n]+\n)", lambda m: m.group(1) + "import shutil\n", s2, count=1, flags=re.M)
                if "sys.executable" in s2 and not re.search(r"^import .*\bsys\b", s2, re.M):
                    s2 = re.sub(r"^(import [^\n]+\n)", lambda m: m.group(1) + "import sys\n", s2, count=1, flags=re.M)
                open(f, "w", encoding="utf-8", newline="\n").write(s2)
                hits[k] = hits.get(k, 0) + n
    return hits


def build_profile():
    """formats/profile/: the pack-format profile from config/profile.json + formats-kit/pack-defaults.json."""
    os.makedirs(os.path.join(PROFILE_DIR, "assets", "fonts"), exist_ok=True)
    p = json.load(open(os.path.join(KIT, "pack-defaults.json"), encoding="utf-8"))
    mine = profile()
    for k, v in mine.items():
        if not k.startswith("_") and k not in ("skills", "style_overrides", "caption_fixes", "glossary"):
            p[k] = v
    for k, v in (mine.get("skills") or {}).items():
        p["skills"].setdefault(k, {}).update(v)
    for k, fallback in (("niche", "short-form videos"), ("creator_name", "Creator"), ("brand_name", "Brand"), ("handle", "@handle")):
        if not str(p.get(k) or "").strip():
            print(f"note: config/profile.json has no {k!r} yet - using {fallback!r} (fill it in, then --refill)")
            p[k] = fallback
    work = os.path.join(ROOT, "work").replace(os.sep, "/")
    p.update({"work_root": work, "projects_root": work, "sfx_dir": os.path.join(PROFILE_DIR, "assets", "sfx").replace(os.sep, "/"),
              "asset_dirs": work + "/<id>/shared", "media_drive": "none", "transcriber": "local"})
    for name, src in FONT_FILES.items():
        s = os.path.join(ROOT, "assets", "fonts", src)
        if os.path.exists(s):
            shutil.copy2(s, os.path.join(PROFILE_DIR, "assets", "fonts", name))
    for f in glob.glob(os.path.join(ROOT, "config", "fonts", "*")):          # the user's own font files, if any
        shutil.copy2(f, os.path.join(PROFILE_DIR, "assets", "fonts", os.path.basename(f)))
    sfx = os.path.join(PROFILE_DIR, "assets", "sfx")
    shutil.copytree(os.path.join(ROOT, "assets", "sfx"), sfx, dirs_exist_ok=True)
    m = json.load(open(os.path.join(KIT, "sfx_map.json"), encoding="utf-8"))
    m["dir"] = sfx
    json.dump(m, open(os.path.join(PROFILE_DIR, "assets", "sfx_map.json"), "w", encoding="utf-8"), indent=1)
    av = os.path.join(ROOT, "config", "avatar.jpg")
    if os.path.exists(av):
        shutil.copy2(av, os.path.join(PROFILE_DIR, "assets", "avatar.jpg"))
    json.dump(p, open(os.path.join(PROFILE_DIR, "profile.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return p


def fill(skill):
    env = dict(os.environ, PYTHONUTF8="1", CREATOR_PROFILE_DIR=PROFILE_DIR)
    r = subprocess.run([sys.executable, os.path.join(FMT, skill, "setup", "apply_profile.py")], env=env, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout + r.stderr).strip().splitlines()[-1:] or [""]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pack", nargs="?", help="your pack's skills/ folder (all 10 formats); omit for the 3 bundled in pack/")
    ap.add_argument("--refill", action="store_true", help="only rebuild formats/profile and re-fill the imported formats")
    a = ap.parse_args()
    if not os.path.isdir(os.path.join(ROOT, "assets", "fonts")):
        sys.exit("assets/ missing: run `python setup.py` first")
    if not a.refill:
        if a.pack:
            src, todo = (a.pack if os.path.isdir(os.path.join(a.pack, SKILLS[0])) else os.path.join(a.pack, "skills")), SKILLS
            missing = [s for s in SKILLS if not os.path.isdir(os.path.join(src, s))]
            if missing:
                sys.exit(f"not a Creator Skill Pack skills folder (missing {', '.join(missing)}): {a.pack}")
        else:
            src, todo = BUNDLED_DIR, BUNDLED
        os.makedirs(FMT, exist_ok=True)
        total = {}
        for s in todo:
            d = os.path.join(FMT, s)
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(os.path.join(src, s), d, ignore=shutil.ignore_patterns(".pristine", ".configured", "__pycache__"))
            for k, n in patch_skill(d).items():
                total[k] = total.get(k, 0) + n
        unused = [k for k in range(len(RULES)) if k not in total]
        print(f"patched: {sum(total.values())} edits from {len(total)}/{len(RULES)} rules"
              + (f" (rules {unused} matched nothing - the pack may have changed; check those formats)" if unused and todo is SKILLS else ""))
        for f in ("README.md", "BUILDER_BRIEF.md"):
            shutil.copy2(os.path.join(KIT, f), os.path.join(FMT, f))
    if not os.path.isdir(FMT):
        sys.exit("no formats imported yet")
    build_profile()
    bad = 0
    for s in SKILLS:
        if not os.path.isdir(os.path.join(FMT, s)):
            continue
        rc, last = fill(s)
        bad += rc != 0
        print(f"  {'ok' if rc == 0 else 'FAIL'} {s}: {last[0][:120]}")
    print("formats ready: python tools/formats.py list" if not bad else f"{bad} format(s) failed to fill - see above")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
