---
name: claude-edit-scenes
description: Shortcut for /claude-edit that makes only the "scenes" format (formerly "backdrop"). You cut out in a corner over a full-screen image per idea, hard cuts every 1.5-3 s, hook over a collage.
argument-hint: <raw takes or video>
disable-model-invocation: true
---

# /claude-edit-scenes

Menu name `scenes`; folders and tool arguments still use the internal key `backdrop`.

Read `.claude/skills/claude-edit/SKILL.md` (in this repo) and run it for: $ARGUMENTS

Build ONLY the `backdrop` format. Follow the main skill for the shared steps (0b raw cut if raw takes, 1 prep, 2-3 recut-plan for facts.json + assets), then its Formats section for ONLY `backdrop`: `python tools/formats.py media <id>`, `python tools/formats.py new <id> backdrop`, one builder agent briefed from formats/BUILDER_BRIEF.md, then `python tools/formats.py render <id> backdrop` (draft first). Rules: formats/cutout-backdrop-reel/SKILL.md (cutout_reel.py); library notes in formats/README.md.

- Looks like: You cut out in a corner over a full-screen image per idea, hard cuts every 1.5-3 s, hook over a collage.
- Use it when: a fast, punchy video with one image per idea.
- Known issues: scale jumps between shots; needs chosen images (no image search without your OK); hooks were placeholders.
- Gallery: `docs/index.html` (published as the repo's GitHub Pages site).
