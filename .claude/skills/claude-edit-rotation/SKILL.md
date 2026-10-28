---
name: claude-edit-rotation
description: Shortcut for /claude-edit that makes only the "rotation" format (formerly "business"). Rotates you full screen, split screen and full-screen animation, every switch on a cut; price rings, posts, stat columns, sound effects.
argument-hint: <raw takes or video>
disable-model-invocation: true
---

# /claude-edit-rotation

Menu name `rotation`; folders and tool arguments still use the internal key `business`.

Read `.claude/skills/claude-edit/SKILL.md` (in this repo) and run it for: $ARGUMENTS

Build ONLY the `business` format. Follow the main skill for the shared steps (0b raw cut if raw takes, 1 prep, 2-3 recut-plan for facts.json + assets), then its Formats section for ONLY `business`: `python tools/formats.py media <id>`, `python tools/formats.py new <id> business`, one builder agent briefed from formats/BUILDER_BRIEF.md, then `python tools/formats.py render <id> business` (draft first). Rules: formats/business-short-form-reels/SKILL.md; library notes in formats/README.md.

- Looks like: Rotates you full screen, split screen and full-screen animation, every switch on a cut; price rings, posts, stat columns, sound effects.
- Use it when: most videos - the best all-rounder (ranked first in an independent review).
- Known issues: reel_engine strips '.' from caption words (work around in build.py); split scenes hidden under a face window trip content_overlap in check (filler scenes fix it).
- Gallery: `docs/index.html` (published as the repo's GitHub Pages site).
