---
name: claude-edit-wrap
description: Shortcut for /claude-edit that makes only the "wrap" format (formerly "fitted"). A caption style: one big accent word with the small words fitted around its letters; can sit over other formats.
argument-hint: <raw takes or video>
disable-model-invocation: true
---

# /claude-edit-wrap

Menu name `wrap`; folders and tool arguments still use the internal key `fitted`.

Read `.claude/skills/claude-edit/SKILL.md` (in this repo) and run it for: $ARGUMENTS

Build ONLY the `fitted` format. Follow the main skill for the shared steps (0b raw cut if raw takes, 1 prep, 2-3 recut-plan for facts.json + assets), then its Formats section for ONLY `fitted`: `python tools/formats.py media <id>`, `python tools/formats.py new <id> fitted`, one builder agent briefed from formats/BUILDER_BRIEF.md, then `python tools/formats.py render <id> fitted` (draft first). Rules: formats/fitted-stacked-captions/SKILL.md (fit_captions.py); library notes in formats/README.md.

- Looks like: A caption style: one big accent word with the small words fitted around its letters; can sit over other formats.
- Use it when: a caption-led version, or as the caption layer on another format.
- Known issues: with the tight framing the stacks cover the nose - no room under the chin.
- Gallery: `docs/index.html` (published as the repo's GitHub Pages site).
