---
name: claude-edit-tiers
description: Shortcut for /claude-edit that makes only the "tiers" format (formerly "ranking"). An S-to-F tier table under a wide shot of you; item cards pop up when named and drop into their tier.
argument-hint: <raw takes or video>
disable-model-invocation: true
---

# /claude-edit-tiers

Menu name `tiers`; folders and tool arguments still use the internal key `ranking`.

Read `.claude/skills/claude-edit/SKILL.md` (in this repo) and run it for: $ARGUMENTS

Build ONLY the `ranking` format. Follow the main skill for the shared steps (0b raw cut if raw takes, 1 prep, 2-3 recut-plan for facts.json + assets), then its Formats section for ONLY `ranking`: `python tools/formats.py media <id>`, `python tools/formats.py new <id> ranking`, one builder agent briefed from formats/BUILDER_BRIEF.md, then `python tools/formats.py render <id> ranking` (draft first). Rules: formats/ranking-format/SKILL.md (rank_engine.py from plan.json); library notes in formats/README.md.

- Looks like: An S-to-F tier table under a wide shot of you; item cards pop up when named and drop into their tier.
- Use it when: ONLY a video that really ranks things (tier letters imply a verdict).
- Known issues: title at y ~190 like glass; uses _media/cam_wide_top.mp4 because no table spot clears the tight face.
- Gallery: `docs/index.html` (published as the repo's GitHub Pages site).
