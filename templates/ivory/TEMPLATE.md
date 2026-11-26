# Ivory template

Chase's baseline look: a split-screen short, graphics on an ivory panel above his real face cam. [Chase]
To the tools it is `editorial`: spec `styles/editorial/STYLE.md`, flag `--pack editorial`. [Ours]
Layout numbers in STYLE.md and these rule files are at 1080x1920. Publish is 1080x1920 at 30 fps since 2026-11-24 (4K30 only when he asks; 60 fps only when he asks). [Chase]

## Status: in use

- **These rules are in daily use.** [Ours] 1030-2 was the first video through them (2026-11-01); about a dozen shorts have followed. The lock test was never run and was dropped on 2026-11-22.
- **`/claude-edit` is the editor, with the player and note rounds.** [Chase] 2026-11-02 he made the former `/claude-edit-next` the real one. The old multi-style skill is archived.

## What makes it ivory

- **The Keep list holds on every frame.** [Chase]
  Ivory canvas. Serif headline with one italic clay word. Rebuilt vector UI cards. Mono caption chips on the seam.
  HUD continuity. Real artifacts, never fake "test" slides. Split face cam, no cut-out. Verified numbers only.
  Why: this list is what he chose as the look. Met when: `ledger.md`'s Keep drift line finds nothing.
- **Nothing from a donor's look comes in.** [Ours] Why: `HOUSE.md` lets donor rules pass, not donor looks.
  Met when: its banned list is absent from the composition.
- **The rebuilt-cards rule stands as written.** [Chase]
  Whether real captures or rebuilt cards lead is an open decision in `HOUSE.md`. Flag it. Never settle it here.
- **Ivory does not opt in to full-screen face edits.** `templates/ivory/template.json` sets `full_face` false. [Chase]
  Why: he wants them only in certain templates, or when he asks for one on an edit. Met when: a run with no request from him reads false, as `layout.md` sets out.

## Read order

Read top to bottom. Each role reads only its rows.

| # | File | What it decides | Read by |
|---|---|---|---|
| 1 | `templates/HOUSE.md` | Standards for every template, checks, review, handoff | Everyone |
| 2 | `templates/story.md` | Which lines survive the cut | Spine only |
| 3 | `templates/ivory/TEMPLATE.md` | This page | Everyone past the spine |
| 4 | `templates/ivory/picker.md` | Which visual a line gets | Planner, builder |
| 5 | `templates/ivory/layout.md` | Split, full-graphic, full-face when `full_face` is on, frame bands, the seam | Planner, builder |
| 6 | `templates/ivory/captures.md` | How assets are sourced and shown | Researcher, assets, planner, builder |
| 7 | `templates/ivory/captions.md` | The chip | Builder |
| 8 | `templates/ivory/sound.md` | Cues | Builder |
| 9 | `templates/ivory/ledger.md` | What a first render must not carry | Planner, builder, reviewers |
| 10 | `styles/editorial/STYLE.md` | Every look number | Planner, builder |

- **Chase wins every conflict, then measured numbers, then prose.** [Chase] [Ours]
  Why: STYLE.md says measured numbers beat its prose, and his house rules beat donor numbers.
  Met when: a conflict in the plan names which line won.
- **Trial ideas stay off. Open decisions stay open.** [Chase]
  Why: only his yes writes a rule. Met when: no trial runs and no open decision is settled in a build.

## What ivory owns

Templates own assets and edit style. The spine stays neutral. [Chase]

| Owned by ivory | Owned by the spine, once per raw |
|---|---|
| Which visual each line gets | The cut, transcript and voice audio |
| Layout and switching | Word timings and BIG joins |
| How each asset is shown | Verified facts, kept for every template on this raw [Ours] |
| Chip look, timing, placement | His own clips and captures, kept the same way [Ours] |
| Sound cues and levels | The optional trim list |
| Which listed trims it takes, before graphics | |

- **A template picks. The spine never does.** [Chase] Why: facts must match across versions, while the look need not.
  Met when: a second template re-runs no transcript, cut or audio step.

## Where look details live

These older files stay the source. Point at them, and never copy their numbers into this page.

| Detail | Source |
|---|---|
| Palette, type, components, motion, banned list, all layout numbers | `styles/editorial/STYLE.md` |
| Measured donor numbers | `styles/editorial/REFERENCE-ANALYSIS.md`, `styles/CALIBRATION.md` |
| Menu base under `picker.md` | `styles/VISUAL_MENU.md` |
| Reference frames and sheets | `reference/full/`, `reference/sheets/` |
| Component kits | `styles/editorial/kit/editorial-chiefofstaff`, `styles/editorial/kit/editorial-vibecoding` |
| Proven code to reuse | `work/1022-2/v2/editorial` |

- **If a rule file quotes a number and STYLE.md differs, STYLE.md wins and the gap gets flagged.** [Ours]
  Why: two copies drift. Met when: the handoff names the line under what is still open.
  Why: images go through `codex exec`. Met when: `ASSETS.md` lists `codex exec` for every generated image.
- **No kit is the base yet.** [Ours] Why: production runs on neither kit, and the choice waits for the Phase 2 proof.
  Met when: builds keep reusing the proven project until a base is named here.

## Not in this folder yet

From the game plan's Phase 5, not built: `values.json` and `refs/`. [Ours] Built since: the kit, as `build_kit/` (every build starts from its `new_project.py`), and sound as data (`sound.json` per project, from `sound.md` and `sfx/sfx.json`). `plan.json` ties each event to a word (`word_i`) under a fixed `event_id`, but its time is still a number written by hand.
A build is still one HyperFrames project. An edit re-renders the beats it touches (`tools/beat_render/run.py change`), not the whole video; a change to the shell, to timing or a new clip still renders every beat.
