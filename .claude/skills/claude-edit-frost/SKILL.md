---
name: claude-edit-frost
description: Shortcut for /claude-edit that makes only the "frost" format (formerly "glass"). You in a rounded panel at the bottom, glass cards above: notifications, score counters, price cards, calendar.
argument-hint: <raw takes or video>
disable-model-invocation: true
---

# /claude-edit-frost

Menu name `frost`; folders and tool arguments still use the internal key `glass`.

Read `.claude/skills/claude-edit/SKILL.md` (in this repo) and run it for: $ARGUMENTS

Build ONLY the `glass` format. Follow the main skill for the shared steps (0b raw cut if raw takes, 1 prep, 2-3 recut-plan for facts.json + assets), then its Formats section for ONLY `glass`: `python tools/formats.py media <id>`, `python tools/formats.py new <id> glass`, one builder agent briefed from formats/BUILDER_BRIEF.md, then `python tools/formats.py render <id> glass` (draft first). Rules: formats/glass-explainer-reel/SKILL.md; library notes in formats/README.md.

- Looks like: You in a rounded panel at the bottom, glass cards above: notifications, score counters, price cards, calendar.
- Use it when: a polished explainer with several distinct points.
- Known issues: headings sit at y ~190 (pack default) inside Instagram's top-bar band - move to ~290+.
- Gallery: `docs/index.html` (published as the repo's GitHub Pages site).
