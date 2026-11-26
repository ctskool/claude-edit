Read this only when you need to know whether a stage or tool is proven, before relying on it or telling Chase it works. A run never needs it.

Rewritten 2026-11-22 from what the author has shipped with it on his own machine (Windows, an NVIDIA card): 32 delivered 4K30 finals of shorts (2026-11-01 to 2026-11-19) and four long-form videos. Nothing here was measured on another machine; `INSTALL.md` says what is tested on macOS and without an NVIDIA card. The one-command installer (2026-11-23) was run from a clean state on Windows only; the macOS installer, Mac GPU transcription (`mlx-whisper`) and Mac hardware decode were written on Windows and have not run on a Mac. A row marked "(2026-11-11)" keeps its older wording and was not re-checked. "Section N" means that section of `SKILL.md` and its side file.

| Stage | Status | The honest detail |
|---|---|---|
| Raw to final, a short | Works | Every short since 1030-2 (2026-11-01). The newest runs: 1117-audit, 1117-code-mode, 1118-astryx, 1118-rea, each delivered in three looks |
| Spine and cut (`rawcut.py`, `prep_source.py`) | Works | Every video. `verify` exits 0 either way, so read its lines. RUN-ON and NUMBER lines since 2026-11-09 |
| Cut review page | Works | The standing cut listen since 2026-11-12: he fixes joins by ear and approves there. Lip-sync offset since 2026-11-16, only when he reports it |
| One-agent build (the light path) | Works | The only path since 2026-11-12, and what built every short after it. A three-look short costs about $53 at API price, most of it rework and sound (2026-11-18 test) |
| Pilot look | Works | Section 4. In use on shorts since 2026-11-10 |
| Kit looks | Works | `charcoal`, `neo-brutalist`, `collage` delivered and posted on several shorts; `charcoal-light` and `inverse` as hook-variant recolours. `cobalt` and `paper` exist and have not been delivered on a short that I can find |
| Remaking a short in another kit look | Works | `look_version.py` in the run folder (1117-code-mode, 1118-rea), `hook-variants.md` |
| Hand-built looks: `blueprint`, `sky` | Partly | One short each (rea), posted as trials 2026-11-20. In the player since 2026-11-22 (`tools/look_player.py`): sky ran load, a note round, changed-beat marks and Approve to a delivered 4K30; blueprint ran the load only. No real note from him has gone through either. A round re-renders the whole short; `player --partial` is parked, slower than that |
| A look from a reference | Partly | Section 4 (`reference-look.md`), by hand. Three runs on one take (2026-11-10) |
| Hook variants | Works | Hooks 2 and 3 on 1114-tools, 1116-craft, 1116-yogurt. A shared body passes Instagram's duplicate check with a recolour, a new caption font and one hook difference (2026-11-17) |
| Review render | Works | `tools/beat_render/run.py`, queued on `gpu_lock` since 2026-11-16 |
| Jump check | Partly | `tools/beat_check/jumps.py`, advisory. It cannot see a jump that starts on a tween's own first frame (2026-11-11) |
| Geometry check | Partly | `tools/beat_check/geometry.py`, advisory in the build's QA. Many checks read UNVERIFIED until plans give targets as boxes or selectors (2026-11-11) |
| `motionlint.py`, `flash_scan.py` | Works | Both run inside the checks on every stitched picture |
| Player, notes and rounds | Works | `tools/beat_review_v2/` over `tools/beat_review/`, port 4750. Real rounds on every short. Its tests need the author's fixture edit, which does not ship, so they skip |
| Approval | Works | His Approve click writes the record and starts the final (`autofinal.py`). The fresh-render check is by hand only (`deep=True`) |
| Sound, shorts | Works | `sound.json`, the cue lane and listening preview in the player. Levels from reference measurements and the vetted slices (`templates/ivory/sound.md`) |
| Final, shorts | Works | 1080p30 by default from the Approve click since 2026-11-24 (4K30 only when he asks: `final.json` or `--spec 4k30`); 32 delivered at 4K30 before that. From a tool shell use `autofinal.py run --picture <sha>` in a background task, not `start`. Whole 4K60 only on a fixture copy |
| Popout bottom | Partly | `tools/popout.py`. Proven on a copy of 1030-2 at review size. Never on a new raw or through a 4K final (2026-11-11) |
| Full-face setting | Partly | Resolved by hand at intake. `tools/tests/test_full_face.py` covers motionlint and the rule files' wording (2026-11-11) |
| Effects from `/animate` and `/vfx` | Partly | `effects-bridge.md`. `/vfx` orbit run for real on 1102-1; `/animate` not yet run through a note round (2026-11-11) |
| Library and capture cache | Partly | `tools/library.py`, `templates/ivory/library/`, `tools/capture_cache.py`. The harvest step runs at approval (`short-finish.md`); whether a build has reused a library scene was not re-checked (2026-11-11) |
| Notes into rules | Partly | `tools/taste_from_notes.py`, `templates/ivory/CANDIDATES.md`. No candidate marked keep or strike yet (2026-11-11) |
| Reference breakdown | Partly | `references/HOW.md`, `tools/reference.py`, the HyperFrames measure tools pinned at 0.9.13. Used for look and structure notes, never fed through an edit automatically |
| `run.json` state | Partly | `tools/run_state.py`. Its stage names are the archived pipeline's, so a run leaves `research` and `plan_check` pending |
| Install and doctor | Partly | `tools/doctor.py`, `INSTALL.md`. Passes on Chase's machine. Never tried on a Mac or a clean machine (2026-11-11) |
| Charcoal, 16:9 long-form | Works, by hand | Four delivered at 4K: 1109-fable, 1110-slop, 1113-nod, 1116-plugins. Slice rendering on the GPU, the stills storyboard, the pilot, notes by segment. His approval is in chat: `run.py`, the ownership map and the Approve click do not know this template |
| Sound, long-form | Asked per video | Since 2026-11-22 it is asked once per video; his answer so far is no, so no cue path has been run on a long-form video |

