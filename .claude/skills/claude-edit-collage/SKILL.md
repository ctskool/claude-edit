---
name: claude-edit-collage
description: Shortcut for /claude-edit that makes only the "collage" format (formerly "cluster"). Small image cards above your head that change every few seconds, tiny captions beside your cheek.
argument-hint: <raw takes or video>
disable-model-invocation: true
---

# /claude-edit-collage

Menu name `collage`; folders and tool arguments still use the internal key `cluster`.

Read `.claude/skills/claude-edit/SKILL.md` (in this repo) and run it for: $ARGUMENTS

Build ONLY the `cluster` format. Follow the main skill for the shared steps (0b raw cut if raw takes, 1 prep, 2-3 recut-plan for facts.json + assets), then its Formats section for ONLY `cluster`: `python tools/formats.py media <id>`, `python tools/formats.py new <id> cluster`, one builder agent briefed from formats/BUILDER_BRIEF.md, then `python tools/formats.py render <id> cluster` (draft first). Rules: formats/image-cluster-reel/SKILL.md (cluster_reel.py); library notes in formats/README.md.

- Looks like: Small image cards above your head that change every few seconds, tiny captions beside your cheek.
- Use it when: a metaphor / meme-image video with a wide shot.
- Known issues: weakest on the first test video: needs metaphor images (yours, or a source you choose) and a wider shot.
- Gallery: `docs/index.html` (published as the repo's GitHub Pages site).
