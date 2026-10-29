---
name: claude-edit-setup
description: First-run setup and doctor for this repo - detects Windows / macOS and NVIDIA / Apple Silicon / CPU, installs or checks ffmpeg, Node, HyperFrames, the Python venv, faster-whisper and the cut-out model, writes config/config.json, then asks for the user's brand and writes config/profile.json. Use when the user says "/claude-edit-setup", "set up claude-edit", "redo my setup", "change my brand", "is everything installed", or when config/config.json is missing.
argument-hint: [--check] [--no-matte]
---

# /claude-edit-setup

1. Run `python setup.py --smoke $ARGUMENTS` from the repo root (use `python3` if `python` is not found; on Windows
   `py -3` also works). It asks before any system install (winget on Windows, Homebrew on macOS) - those prompts need
   the user's terminal, so if it stops on one, show the exact command and ask the user to run it, then re-run setup.
   Without a GPU suggest `--no-matte` unless they want the cut-out formats or /claude-edit-versus (it then runs on the
   CPU, slowly).
2. Report each `todo` / `FAIL` line with its fix. On macOS say that the Mac path is new and ask them to report problems.
3. Brand (`config/profile.json`; skip what is already filled unless they asked to redo it). Ask one question at a time:
   name to show, brand name, handle, main platform, one line on what the videos are about, accent colour (hex - or read
   it from a logo / site they give), background colour, fonts (headline, captions, accent word; the repo ships Space
   Grotesk, Inter Tight, Instrument Serif - open licence - and their own font files can go in `config/fonts/`), product
   or people names Whisper should spell right (`glossary`), anything that must never appear on screen (`never_show`),
   and optionally a square profile picture saved as `config/avatar.jpg`. Write the answers into `config/profile.json`
   (keys as in `config/profile.example.json`).
4. Layout formats: rotation, frost and popout are installed by `setup.py` (else `python tools/import_formats.py`);
   after a brand change, `python tools/import_formats.py --refill`.
5. Tell them what to try first: `/claude-edit <video>` (ivory), `/claude-edit-cut <raw takes>`, `/claude-edit-versus <take>`.
