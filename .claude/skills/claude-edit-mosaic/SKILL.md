---
name: claude-edit-mosaic
description: Shortcut for /claude-edit that makes only the "mosaic" format (formerly "grid"). You cut out in the centre over four tiles that change together: big stat tiles mixed with real screenshots.
argument-hint: <raw takes or video>
disable-model-invocation: true
---

# /claude-edit-mosaic

Menu name `mosaic`; folders and tool arguments still use the internal key `grid`.

Read `.claude/skills/claude-edit/SKILL.md` (in this repo) and run it for: $ARGUMENTS

Build ONLY the `grid` format. Follow the main skill for the shared steps (0b raw cut if raw takes, 1 prep, 2-3 recut-plan for facts.json + assets), then its Formats section for ONLY `grid`: `python tools/formats.py media <id>`, `python tools/formats.py new <id> grid`, one builder agent briefed from formats/BUILDER_BRIEF.md, then `python tools/formats.py render <id> grid` (draft first). Rules: formats/cutout-grid-reel/SKILL.md (grid_reel.py, PIL + ffmpeg); library notes in formats/README.md.

- Looks like: You cut out in the centre over four tiles that change together: big stat tiles mixed with real screenshots.
- Use it when: a video with several figures or products to compare.
- Known issues: builder-written hooks were placeholders on the first test video; images are real assets only unless you supply or allow others.
- Gallery: `docs/index.html` (published as the repo's GitHub Pages site).
