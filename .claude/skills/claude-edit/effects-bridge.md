Read this when a note names an effect from `/animate` or `/vfx`, before changing anything for that note. It is the effects part of section 7, step 5 (`short-notes.md`), moved here unchanged from `SKILL.md`.

**Effects from other skills** [Chase, 2026-11-03]. When a note names an effect from `/animate` or `/vfx` ("glass widgets here", "use the head-to-head from animate"), use that skill's real output. Never rebuild a look-alike in ivory's own style. If the skill isn't installed in this Claude Code, say so, and leave the note in `not_done` with that reason.
- **`/animate`:**
  - Run `animate vars <name>`. Fill the vars with his words and only numbers in `facts.json`.
  - Render it with `--output top` (1080x960, the top panel) for a split beat, or `--output full` for a full-graphic beat, no `--draft`.
  - Copy the MP4 to `work/<id>/shared/clips/animate-<name>-<beat>.mp4` and run `new_project.py <id>` again to link it.
  - Replace that beat's scene content with a `vplate` of it at the panel box. Hold its last frame with `stills` if it is shorter than the window.
  - Bind the beat's anchor as `present` on the plate, since a clip's content cannot be measured.
- **`/vfx`:**
  - It works on his whole frame, so that beat becomes a full-screen face beat. His note is the full-face request of step 5: record his words, and treat it as covering that beat only.
  - Prep the vertical source once: `vfx prep work/<id>/raw/cut.mp4` for a face-only take, or `raw/cam_cut.mp4` when the take is a screen-over-face split. Check one frame first, since the camera file can be rotated. Composition time is cut time.
  - Render with `--from`/`--to` set to the beat window and `--at` on the landing word's time, with his real words and names, no `--draft`. Check it with `/vfx`'s own contact sheet step.
  - Copy the video to `work/<id>/shared/clips/vfx-<effect>-<beat>.mp4` and link it.
  - Make that beat a `scene full`, with a muted `vplate` of it filling the frame. Voice and captions stay the edit's own.
  - Move those beats' caption chunks to `position: "fullface"`. At the split's seam they sit on his chin. (Found on 1102-1's first orbit, 2026-11-03.)
  - Bind the anchor to the first spoken word in the window, not the cut, or the event check fails. Use `--at` for the landing word.
  - Card numbers (stars, counts) come from `facts.json`, never the effect's built-in defaults.
  - End the HUD strip's run when the effect starts, since it covers the effect on full-frame beats. Chase noted it on 1102-1, round 3.
  - Every `/vfx` effect keeps his real pixels (a cut-out, never synthesized), so the real-footage rule holds.
- **Cost:** a clip the project hasn't used costs a new media plan; on 1030-2 one new clip re-rendered every beat. Tell him the render reach before running.
- **Record it:** put the skill, effect, vars, command and output path in `RUN.md`. The first real run of each is unproven, so step through those beats by eye before closing the round.
