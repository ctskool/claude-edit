# claude-edit v2: release plan

Written 2026-11-02, before any file was copied. This repo moves from the old menu-of-looks editor (v1, last pushed 2026-10-29) to the current `/claude-edit`: one raw talking-head take in, a one-minute cut listen, a whole first edit in the ivory template, a browser player for notes at exact seconds, note rounds, approval, sound and the final.

Nothing is pushed until Chase says so in chat.

## What happens to v1

v1's files are removed, and the repo starts again from one root commit, so its history holds none of them:

- `pack/` (the rotation, frost and popout looks) and `formats-kit/`, `licenses/` for it
- `setup.py`, `config/`, `examples/`, `release/`, the old `docs/` gallery and its media
- the old `.claude/skills/` (claude-edit menu, shortcuts, versus, setup and the vendored HyperFrames skills)
- `templates/editorial`, `templates/smoke`, the old `tools/`, `CLAUDE.md`, `LICENSING-REPORT.md`, `THIRD_PARTY.md`, `NOTICE`

`LICENSE` (MIT) stays. The GitHub Pages setting (main, `/docs`) stays, so the new gallery goes in `docs/` and no repo setting changes. The old `gallery-v1` release and tag are deleted, since they held v1's history.

## v2 layout

```
.claude/skills/claude-edit/SKILL.md   the skill (portable copy, see below)
README.md  INSTALL.md  LICENSE  licenses/  RELEASE-AUDIT.md  PLAN.md
requirements.txt  package.json  package-lock.json  .gitignore  .gitattributes
templates/HOUSE.md  templates/story.md
templates/ivory/                       rules, build_kit/, library/, CANDIDATES.md, sfx/ (shippable sounds only)
styles/CALIBRATION.md  styles/editorial/   STYLE.md, REFERENCE-ANALYSIS.md, kit/ (creators anonymised, as v1 did)
references/HOW.md  references/README.md   how to measure your own references; no reels ship
examples/ivory-edit/                   text-only structure of one approved edit (1030-2): beats, facts, plan, storyboard, tools_local
tools/                                 only what the skill calls, plus its tests
  rawcut.py prep_source.py make_words.py transcribe.py asr.py align_words.py face_retime.py
  run_state.py taste_from_notes.py library.py capture_cache.py capture_shots.py post_card.py
  doctor.py paths.py fetch_sounds.py reference.py motionlint.py gates.py finish.py deliver.py sound_mix.py
  popout.py matte.py                   optional popout bottom (needs Robust Video Matting, installed by the user)
  beat_render/ beat_check/ beat_review/ beat_review_v2/ (default look + skins/)
  workflows/next/                      recut-plan.js recut-build.js recut-build-parallel.js sound-cues.js
  tests/                               tests for the shipped tools; fixture-only tests skip without the fixture
media/                                 banner, before/after, player capture (README images)
docs/                                  Pages gallery: index.html, catalog.json, clips/, posters/
scripts/                               build-gallery.mjs, build-banner.mjs, capture-player.py, templates
```

Left out of v2 on purpose: `work/` (all project data), other creators' reels and transcripts under `references/`, Pixabay sound files, other people's animation cards, the old look packs, anything from image services other than Codex, `tools/capcut/` (not wired), `tools/moves/`, most of `tools/plan_page/`, `tools/sfx_audition/`, `tools/replica/`, crown/face-synth tools, `formats.py`, the archived player layout (`beat_review_v2/_sol-layout/`), `styles/relay`, `styles/mascot`, `templates/moves`, `templates/relay`, `templates/mascot`, `templates/_archive`.

No credit or attribution to people ships (Chase, 2026-11-03): no rule tags naming people, no names in docs or code headers. `licenses/` holds only the notices that shipped fonts and GSAP require.

## Portability

All changes below are made in this copy only. `C:\Users\Chase\shorts` stays as it is while `work/1102-1` is mid note round.

1. Apply every literal old/new replacement in `reports/2026-11-02-portability-audit.md` to the files that ship (a script applies them and lists any whose old text no longer matches; those get done by hand).
2. The two deferred items: the root/path edits, and `tools/beat_render/ownership.py` `IGNORED` gaining `tools_local/chunks/` and `plan.parts/`.
3. Point the workflows' example project at `examples/ivory-edit` instead of `work/beat-fixture` and `work/1022-2`; fonts and vendor files come from the kit.
4. The player: the skill opens the v2 player (`tools/beat_review_v2/server.py`) in its default look; skins stay optional.
5. Plain Claude Code first: Codex stays behind the `codex` flag; the skill says how to run a workflow with native subagents when there is no Workflow host.
6. `doctor.py` flags any absolute path to Chase's machine left in shipped files.

## Showcase

- Banner: real frames from the 1030-2 edit, built by `scripts/build-banner.mjs`.
- Before/after: 1030-2's raw cut beside its delivered final (`out/1030-2_ivory_final_v2.mp4`), same timeline.
- Player: a short capture of the v2 player with a note left at an exact second, made on a scratch copy of 1030-2 so the real project is never touched.
- Gallery: `docs/catalog.json` drives `docs/index.html` through `scripts/build-gallery.mjs`. A slot waits for the top-five edit (`work/1102-1`), filled only after Chase approves that edit and says it can be used.
- Renders check first that nothing else is rendering on this machine.

## Done means

Committed locally, not pushed. A fresh clone in a temp folder passes `python tools/doctor.py` (no FAIL) and the test suite; the results go in the report with what is unverified (Mac, a stranger's first run) and the exact push command.
