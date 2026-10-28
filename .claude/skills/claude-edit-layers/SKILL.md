---
name: claude-edit-layers
description: Shortcut for /claude-edit that makes only the "layers" format (formerly "depth"). You full frame the whole time, real interfaces sliding in beside and behind your head, captions on your hair.
argument-hint: <raw takes or video>
disable-model-invocation: true
---

# /claude-edit-layers

Menu name `layers`; folders and tool arguments still use the internal key `depth`.

Read `.claude/skills/claude-edit/SKILL.md` (in this repo) and run it for: $ARGUMENTS

Build ONLY the `depth` format. Follow the main skill for the shared steps (0b raw cut if raw takes, 1 prep, 2-3 recut-plan for facts.json + assets), then its Formats section for ONLY `depth`: `python tools/formats.py media <id>`, `python tools/formats.py new <id> depth`, one builder agent briefed from formats/BUILDER_BRIEF.md, then `python tools/formats.py render <id> depth` (draft first). Rules: formats/depth-ui-reel/SKILL.md; library notes in formats/README.md.

- Looks like: You full frame the whole time, real interfaces sliding in beside and behind your head, captions on your hair.
- Use it when: a video recorded with a WIDER camera shot.
- Known issues: squeezed by a tight camera framing; captions() strips '.', counter() rounds to whole numbers, camera() hard-codes its transform-origin.
- Gallery: `docs/index.html` (published as the repo's GitHub Pages site).
