---
name: claude-edit-evidence
description: Shortcut for /claude-edit that makes only the "evidence" format (formerly "essay"). Dark frame, you cut out low, an evidence wall of real posts, charts and pricing with a source line on each.
argument-hint: <raw takes or video>
disable-model-invocation: true
---

# /claude-edit-evidence

Menu name `evidence`; folders and tool arguments still use the internal key `essay`.

Read `.claude/skills/claude-edit/SKILL.md` (in this repo) and run it for: $ARGUMENTS

Build ONLY the `essay` format. Follow the main skill for the shared steps (0b raw cut if raw takes, 1 prep, 2-3 recut-plan for facts.json + assets), then its Formats section for ONLY `essay`: `python tools/formats.py media <id>`, `python tools/formats.py new <id> essay`, one builder agent briefed from formats/BUILDER_BRIEF.md, then `python tools/formats.py render <id> essay` (draft first). Rules: formats/visual-essay-reel/SKILL.md; library notes in formats/README.md.

- Looks like: Dark frame, you cut out low, an evidence wall of real posts, charts and pricing with a source line on each.
- Use it when: a claim-heavy video where receipts matter.
- Known issues: evidence text is small on a phone; the lower third was left as glow on the first test video.
- Gallery: `docs/index.html` (published as the repo's GitHub Pages site).
