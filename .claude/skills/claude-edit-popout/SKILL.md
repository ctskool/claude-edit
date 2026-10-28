---
name: claude-edit-popout
description: Shortcut for /claude-edit that makes only the "popout" format (formerly "panel"). You in a panel at the bottom with your head popping above it, red-block headings and diagrams building above.
argument-hint: <raw takes or video>
disable-model-invocation: true
---

# /claude-edit-popout

Menu name `popout`; folders and tool arguments still use the internal key `panel`.

Read `.claude/skills/claude-edit/SKILL.md` (in this repo) and run it for: $ARGUMENTS

Build ONLY the `panel` format. Follow the main skill for the shared steps (0b raw cut if raw takes, 1 prep, 2-3 recut-plan for facts.json + assets), then its Formats section for ONLY `panel`: `python tools/formats.py media <id>`, `python tools/formats.py new <id> panel`, one builder agent briefed from formats/BUILDER_BRIEF.md, then `python tools/formats.py render <id> panel` (draft first). Rules: formats/explainer-panel-reel/SKILL.md; library notes in formats/README.md.

- Looks like: You in a panel at the bottom with your head popping above it, red-block headings and diagrams building above.
- Use it when: a structured explainer (steps, how-it-works).
- Known issues: headings at y ~190 like glass; close-up captions under the chin land below the 1500 safe line.
- Gallery: `docs/index.html` (published as the repo's GitHub Pages site).
