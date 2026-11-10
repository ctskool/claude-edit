#!/usr/bin/env python3
"""Sets up work/<id>/v2/editorial from this kit, so a new raw builds a project run.py accepts. README.md beside this file says what the builder writes next.

python templates/ivory/build_kit/new_project.py <id> [--full-face] [--work <folder>]

Keeps an existing project's sources and adds missing shared assets on a retry. Hard-links work/<id>/shared/* and the face and voice files, and falls back to a copy.
The kit's fonts and GSAP are always copied, and win over any in shared/.
"""
import argparse, json, os, shutil, sys
from pathlib import Path

KIT = Path(__file__).resolve().parent
sys.path.insert(0, str(KIT.parents[2] / "tools"))
from paths import project_root
SHORTS = project_root()
KIT_ASSETS = ("fonts", "vendor")  # the kit's own, so a project never depends on an older project's copies


def link(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def link_tree(src, dst):
    for path in sorted(src.rglob("*")):
        if path.is_file():
            target = dst / path.relative_to(src)
            if not target.exists():
                link(path, target)


def setup(root, full_face=False):
    """root: the work/<id> folder. Returns the project folder, or raises ValueError with what is missing."""
    root = Path(root).resolve()
    missing = [n for n in ("metadata.json", "beats.json", "words.json", "assets/face_half.mp4", "assets/voice.m4a") + (("assets/face_full.mp4",) if full_face else ()) if not (root / n).is_file()]
    if missing:
        raise ValueError(f"{root} is missing {', '.join(missing)}: run the spine and recut-plan first")
    project = root / "v2" / "editorial"
    project.mkdir(parents=True, exist_ok=True)
    if not (project / "tools_local").exists():
        shutil.copytree(KIT / "tools_local", project / "tools_local", ignore=shutil.ignore_patterns("__pycache__"))
        for path in (KIT / "project").iterdir():
            shutil.copy2(path, project / path.name)
        (project / "meta.json").write_text(json.dumps({"id": f"{root.name}-editorial", "name": f"{root.name}-editorial"}, indent=2) + "\n", encoding="utf8", newline="\n")
        for name in KIT_ASSETS:
            shutil.copytree(KIT / "assets" / name, project / "assets" / name)
    for font in sorted((KIT / "looks").glob("*/fonts/*")):  # every look's fonts, so plan.json "look" can change without a second setup
        if not (project / "assets" / "fonts" / font.name).exists():
            shutil.copy2(font, project / "assets" / "fonts" / font.name)
    shared = root / "shared"
    if shared.is_dir():
        for path in sorted(shared.iterdir()):
            if path.is_dir() and path.name not in KIT_ASSETS:
                link_tree(path, project / "assets" / path.name)
    for name in ("face_half.mp4", "voice.m4a") + (("face_full.mp4",) if full_face else ()):
        if not (project / "assets" / name).exists():
            link(root / "assets" / name, project / "assets" / name)
    return project


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("id")
    p.add_argument("--full-face", action="store_true", help="only when the run has allow_full_face true")
    p.add_argument("--work", default=str(SHORTS / "work"))
    args = p.parse_args()
    try:
        print(setup(Path(args.work) / args.id, args.full_face))
    except ValueError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
