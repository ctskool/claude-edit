# claude-edit

This repo turns talking-head recordings into motion-graphics shorts with Claude Code + HyperFrames.

- Entry points: `/claude-edit` (main skill, `.claude/skills/claude-edit/SKILL.md`), `/claude-edit-<menu name>` shortcuts,
  `/claude-edit-versus`, `/claude-edit-setup`.
- If `config/config.json` is missing, run `python setup.py` first (it detects the OS / GPU and installs or checks
  everything). Tools read the machine config through `tools/common.py`; never hard-code paths, encoders or devices.
- Run tools as `python tools/<tool>.py ...` from the repo root; they re-run themselves inside `.venv`.
- Never run two HyperFrames renders at once. Per-video work goes in `work/<id>/`, renders in `out/` (both git-ignored).
- Never put a number on screen that is not in `work/<id>/facts.json` (with a source) or the transcript.
