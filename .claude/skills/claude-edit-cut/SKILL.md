---
name: claude-edit-cut
description: Shortcut for /claude-edit that makes only the "cut" version. Your raw takes after the tight cut: last good take of each line, pauses trimmed, verified word for word.
argument-hint: <raw takes or video>
disable-model-invocation: true
---

# /claude-edit-cut

Read `.claude/skills/claude-edit/SKILL.md` (in this repo) and run it for: $ARGUMENTS

Build ONLY the `cut` cut. Run ONLY step 0b (tools/rawcut.py session / transcribe / drops.json / cut / verify / render / times) and hand over work/<id>/raw/cut.mp4 (+ cam_cut.mp4 when a CAMERA file exists) with the BIG joins. No prep, no graphics.

- Looks like: Your raw takes after the tight cut: last good take of each line, pauses trimmed, verified word for word.
- Use it when: you only want the clean cut (to edit by hand, or to check before choosing versions).
- Known issues: none known; BIG joins are visible face-cam jumps that a later version must cover.
- Gallery: `docs/index.html` (published as the repo's GitHub Pages site).
