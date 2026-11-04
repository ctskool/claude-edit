---
name: claude-edit
description: A video editor for talking-head videos. Takes your raw take through the spine and a one-minute cut listen to a whole first edit in the ivory template, a review render and a player where you leave notes at exact seconds. Claude changes only what you noted, you approve, then sound and the final.
argument-hint: "<raw takes> [template] [notes]"
disable-model-invocation: true
---

# /claude-edit

Chase Hannegan built this editor on his own videos. In this skill and every rule file, **Chase (he, his) means the person running it: the user.** A `[Chase]` tag records where a rule came from. **No output counts toward a lock yet.**

Run it for: $ARGUMENTS

Project root: resolve once at intake with `python -c "from tools.paths import project_root; print(project_root().as_posix())"`. Store that result as `root`, change the working directory to it, and pass `root` to every workflow call, including retries and sound notes. `CLAUDE_EDIT_ROOT` overrides the checkout location. Run `python tools/doctor.py --fix-hints` before a new installation's first edit. Template: `ivory` is the only one, and tools call it `editorial`.

Workflow hosting: `Workflow(...)` is not a built-in plain Claude Code command. If this session has no Workflow host, read the indicated workflow and run its phases through native Claude Code subagents: each `agent` is one fresh subagent; preserve the prompt, schema, result fields and all null/refusal/check/retry gates, and wait at each phase dependency. Supply the same resolved args, including root and codex. Do not execute these files with plain Node (they use host globals and top-level return). If neither a Workflow host nor native subagents is available, report that missing capability before starting the edit.
Use Python and native tool argv arrays for file operations. Quote every path when forming a shell command, including paths containing spaces. Detect executables with Python shutil.which, never shell where/which commands.
First read `templates/HOUSE.md`, then `templates/ivory/TEMPLATE.md` for the read order. Chase wins every conflict.
Trial ideas stay off. Open decisions stay open: keep current behaviour and flag them.

**The flow.** Raw in, spine and one-minute cut listen, whole edit in ivory, review render, player, notes, he says go in chat, note round, repeat, approval, sound, final. He reacts to his own edit. There is no pick list before the build. **Moves stay out of this flow for now.**

`P=work/<id>/v2/editorial` below. Every Python line runs from the project root.

## What works today

| Stage | Status | The honest detail |
|---|---|---|
| Raw plus notes | Works | `work/1030-2` finished the whole flow on 2026-11-01, the only one so far |
| `run.json` state and metrics | Partly | `tools/run_state.py` (added 2026-11-02): state, `status` for resume, `metrics`, `report`. 30 tests on temp folders; no real run has used it yet |
| Install and doctor | Partly | `tools/doctor.py`, `INSTALL.md`, `tools/paths.py`. Paths are project-relative and every workflow takes `root`. Doctor passes on a fresh clone on Windows and on a Mac (2026-11-03, with `ffmpeg-full`). No whole edit has run on a Mac, and no stranger has run a whole edit yet |
| Research during the cut listen | Partly | `recut-plan.js` `stage: research` / `beats` (added 2026-11-02). Stub-tested, never real |
| Plan check | Partly | Blockers vs warnings, two rounds at most (2026-11-02). Stub-tested; the top-five run is its first real use |
| Parallel build | Partly | `recut-build-parallel.js` and `tools/beat_render/merge_chunks.py` (added 2026-11-02). 60 stub and merge tests; never a real run. `ownership.py` ignores the chunk fragments since 2026-11-03, so note rounds re-render only what changed |
| Effects from `/animate` and `/vfx` | Partly | Note-round bridge in section 7, written 2026-11-03 (render with the skill, drop in as a clip; `/vfx` makes that beat full-face). Both skills come from the Chase Animations pack. `/vfx` orbit run once for real on a later edit (43/43 beats re-rendered, 5.5 min; 0 findings). `/animate` not yet run |
| Library and capture cache | Partly | `tools/library.py`, `templates/ivory/library/` (20 scenes from 1030-2 in 9 families), `tools/capture_cache.py` (added 2026-11-02). Tested; never used by a director yet |
| Notes into rules | Partly | `tools/taste_from_notes.py`, `templates/ivory/CANDIDATES.md` (added 2026-11-02). Digest checked on 1030-2's notes; no candidate marked yet |
| Geometry check | Partly | `tools/beat_check/geometry.py`, advisory in both build workflows' QA since 2026-11-02 (Chase: advisory for the next two videos, then a gate if it stays clean). Calibrated: 0 FAIL on the fixture (was 1102) and on 1030-2, 62 tests. Many checks read UNVERIFIED until plans give targets as boxes or selectors. Never run on a new build |
| `rawcut.py`, `prep_source.py` | Works | `verify` exits 0 either way, so read its lines. Face clips are preview size |
| Story read-through | Partly | Rules exist in `story.md`, run by hand, never tried on a raw |
| One-minute cut listen | Works | Chase approved keeping this hand stop on 2026-10-31 |
| Facts and assets | Partly | `tools/workflows/next/recut-plan.js` passed a stub dry run, never a real one |
| Ivory build | Partly | `recut-build.js` starts from `templates/ivory/build_kit`. The kit is proven by a mechanical build of `work/1023-test` in a copy, `stage1/phase6-new-raw-path.md`. Agents have not run through it for real |
| Review render | Works | `tools/beat_render/run.py`. Proven on the fixture and on that kit build |
| Player and notes | Partly | `tools/beat_review_v2/` (page and look) over `tools/beat_review/` (notes, rounds, approval), port 4750. Same notes, rounds and approval as the page `work/1030-2` used for four note rounds; the top-five edit is the first to run in this look |
| Note round | Partly | Instructions below. Scripted rounds only until Phase 6 |
| Approval | Yes | His Approve click writes `beat/approvals/<file_sha16>.json` at once and starts the final (`autofinal.py`); the fresh-render check is by hand only (`deep=True`) |
| Popout bottom | Partly | `tools/popout.py` and ivory's kit. Proven on a copy of 1030-2 at review size (`work/1030-2-popout`). Never on a new raw, and never through a 4K final |
| Reference | Partly | `references/HOW.md`, `tools/reference.py measure`. Measuring tested on our own 1030-2 final only. Never through an edit |
| Full-face setting | Partly | Resolved by hand at intake. `tools/tests/test_full_face.py` covers motionlint and stub dry runs of both workflows, never a real run |
| `motionlint.py`, `flash_scan.py` | Works | Both run inside the checks on every stitched picture |
| Sound | Partly | `sound.json`, sheet/stem/media checks. The cue agent ran live once on 1030-2. Cue lane, listening preview and sound notes are in the player, not yet used on a real sound round |
| Final | Yes | `tools/beat_review/final.py` and `deliver.py --stitched`. 1080p delivered PASS on two new raws; 4K30 delivered PASS on one (2026-11-03), the default now. Whole 4K60 delivered PASS only on a copy of the fixture with a test approval |
| CapCut finish | Not built | Not part of this release |
| Lock | Not built | `templates/ivory/LOCK.md` is empty on purpose |

## 1. Intake and state

- Takes: raw OBS `.mkv` files at the paths supplied in $ARGUMENTS; resolve each to an absolute path. If no path was supplied, ask for the take path. Confirm which by frame grabs and a quick transcript. A finished export is not handled here yet: say so.
- Template: any name but ivory, stop and say only ivory exists here. Everything left is notes.
- Full-face: read `templates/<name>/template.json`. `allow_full_face = template.full_face OR Chase's request for this edit`. A missing file, a missing field or anything but the Boolean `true` reads false. Ivory reads false.
- His request counts only when he asks in words for a full-screen face on this edit. Skipping a page or running auto or lock mode grants nothing.
- Bottom: `split`, unless he asks for popout in words ("popout", "the pop out version"). Then the template's `template.json` must have a `popout` block. If it doesn't, say this template has no popout yet. Record `bottom` and `bottom_source` (his exact words, or `default`) in `RUN.md`. Popout needs the clean camera from section 2. Rules: `templates/HOUSE.md` "Popout bottom".
- Reference: only when he names one in words ("like the agent-types reel", a slug in `references/`). Its kept rules in `references/<slug>/taste.md` go into the intake notes as "Reference <slug>, kept rules:" followed by each rule verbatim. They pass to both workflows through `note`, so every agent gets them. Struck rules and `[seen]` rules he hasn't marked never go. With no `taste.md`, or none marked yet, stop: run layers 1 to 3 of `references/HOW.md` and wait for his keep or strike. Record `reference` and `reference_source` (his words) in `RUN.md`. House rules and his notes win over a reference rule. Take ideas, not the creator's fonts, colours, logos or characters.
- `allow_full_face_source` is `template`, or his exact words when they turned it on. A workflow has no file access, so resolve both here and pass both to `recut-plan.js` and `recut-build.js`. If either changes before the build, re-run the plan. After the build, a note turns it on as section 7 says.
- Codex: the skill assumes plain Claude Code. Run `codex --version` once. Only exit 0 sets `codex = true`; anything else is false. With Codex, generated scene images and a Sol reviewer join the run; without it, no beat is a scene and the defects round uses two Claude reviewers. Record `codex` in `RUN.md` and pass it to both workflows.
- Keep each take in `work/<id>/keep/`. Use Python `os.link(source, destination)` with absolute paths; if linking fails (including a different volume or a filesystem without hard links), use `shutil.copy2(source, destination)` and record the copy in RUN.md. Never replace an existing destination.
- Root: `root` is this project folder as an absolute path. Pass it to every workflow; they cannot find it themselves. On a new machine, run `python tools/doctor.py` first and stop on any FAIL. `INSTALL.md` says how to fix each one.
- State lives in `work/<id>/run.json`. Start a run with `python tools/run_state.py init <id> --model "<model>" --template ivory` (add `--codex` when `codex` is true, and `--reference <slug>` when he named one). At every stage boundary run `start <id> <stage>` before the work and `done <id> <stage> --note "<result>"` after checking its output. Use `wait` while waiting on Chase, `refused` for a refusal and `fail` for a failure. A resumed or compacted session runs `python tools/run_state.py status <id>` first and checks the real outputs before carrying on. Stages: intake, spine, cut_listen, research, facts_assets_beats, direction, plan_check, build, review_render, defects, player, note_round_N, approval, sound, final.
- Create `work/<id>/RUN.md` for what a person reads: raws, template, intake notes in his exact words (the `note` argument below), `allow_full_face` and `allow_full_face_source`, rule files read, open items and next step. Timings live in `run.json`, not here.

## 2. Spine, once per raw

Follow `templates/story.md`. `R=work/<id>/raw`.
```bash
python tools/rawcut.py session $R "<take1.mkv>" "<take2.mkv>"
python tools/rawcut.py transcribe $R
# write $R/drops.json by story.md, each dropped range naming its reason
python tools/rawcut.py cut $R ; python tools/rawcut.py verify $R
python tools/rawcut.py render $R ; python tools/rawcut.py times $R
```
- Keep the wrong-to-right list in `$R/corrections.json`. No tool reads it yet, so pass each pair as `--fix`.
- Run the full read-through in `story.md`, with its fresh reader, before `render`.
- **Stop for the one-minute cut listen.** Make a small phone copy of `$R/cut.mp4`, send it with the cut report from `story.md`, and wait. Nothing past this point runs until he answers, with one exception:
- **Research runs while he listens.** Right after sending the cut, start section 3's workflow with `stage: "research"` and `words: root + "/work/" + id + "/raw/cut_words.json"`. It verifies facts and captures screenshots, which need only the cut and its words, and writes nothing that depends on his answer. Note in `RUN.md` that it ran on this cut.

After his answer, prepare the source and corrected words, then begin section 3:
```bash
python tools/prep_source.py $R/cut.mp4 work/<id> --face-top 0.52
# a face-only take (no screen above the face): python tools/prep_source.py $R/cut.mp4 work/<id> --no-camera --face-top 0.15 --face-bottom 0.63
#   pick the head-and-shoulders window from a frame grab; a camera file rotated against the take also needs --no-camera
python tools/make_words.py work/<id>/transcript.json work/<id>/words.json --fix "wrong=right"
```

## 3. Facts, assets and beats

`Workflow({scriptPath: "tools/workflows/next/recut-plan.js", args: {id, source: root + "/work/" + id + "/raw/cut.mp4", hints: [urls], jumpcuts: [BIG join seconds from times], allowFullFace, allowFullFaceSource, codex, root, note: "<intake notes verbatim>"}})`
- If the research stage finished and he kept the cut as it was, run this with `stage: "beats"`: it skips research and assets and plans from what they wrote. If he changed the cut, run it without `stage`, so research and the clips follow the new cut. If research is still running, wait for it; never start a second one.

It writes `facts.json`, `ASSETS.md`, `shared/` and `beats.json`, which carries `allow_full_face` and `allow_full_face_source`. Every agent reads `HOUSE.md`, the ivory rules and STYLE.md, and gets the intake notes. Before section 4, read the returned `error`, `assets.notes`, `check` and `revision`, and put unresolved items in `RUN.md`. A null assets, plan, check or attempted revision stops the workflow. A revision is not a passing check: verify its listed fixes against the files before continuing. The director independently re-checks the resulting content. `beats.json` also records `cta_start`, `proof_span` and their transcript/clip sources under the sound rules; null needs a reason.

## 4. First edit: the whole video in ivory

`Workflow({scriptPath: "tools/workflows/next/recut-build-parallel.js", args: {id, styles: ["editorial"], allowFullFace, allowFullFaceSource, codex, root, chunks: 4, note: "<intake notes verbatim>"}})`
The work is split into about 4 chunks at layout boundaries:
- A lead director makes the shared calls.
- Chunk directors plan their beats in parallel, and `tools/beat_render/merge_chunks.py plan` joins them into `plan.json`. A second agent checks the whole plan once.
- Chunk builders write their scenes in parallel into `tools_local/chunks/<chunk>/`, and `merge_chunks.py build` stitches them in window order.
- One integrator runs the full QA and fixes what crosses chunks. A failed chunk retries on its own, once.

Directors read the proven components in `templates/ivory/library/INDEX.md` first. `recut-build.js` is the same flow in one piece. Use it if the parallel workflow refuses for a merge reason, and say so in `RUN.md`. Retries below take either file. The builders write `$P` from `templates/ivory/build_kit`. Its first build writes `beats.lock.json`, `ownership.json` and `events.json`, without which `run.py` refuses the project. Nothing falls back to all-shared. When `codex` is true, the director owns scene images before its plan check (without Codex there are no scene beats): it generates missing `shared/scenes/<beat>.png` through Codex's built-in image tool (from Claude Code, `codex exec`), and records prompts and dimensions in `ASSETS.md`. Setup can run again to link newly added shared assets while keeping existing sources. The builder emits only the voice audio tag.

**`refused: true`.** The build did not run. Direction may have updated `plan.json`, `STORYBOARD.md`, scene images and `ASSETS.md`. Read the workflow's result:
- `plan_check.issues` lists what failed. Fix an upstream defect in `beats.json`, `facts.json` or an asset, through `recut-plan.js` if needed. For a `plan.json` defect, call `Workflow({scriptPath: "tools/workflows/next/recut-build.js", args: {id, styles: ["editorial"], allowFullFace, allowFullFaceSource, codex, root, note: "<intake notes verbatim>", planIssues: result[0].plan_check.issues}})`. The director reads and revises the existing plan, keeps every `event_id`, and the independent check runs again. A hand edit must not be overwritten by blind direction.
- An empty or missing `plan_check` means the check never answered. Run it again once.
- `reason` means a style with no kit. Stop and say only ivory exists here.
- **Two plan-check rounds at most:** the first check, then one revision with `planIssues`. If the second still refuses, stop and put its issues in front of Chase. Do not start a third round on your own.
- Only `issues` refuse. They are blockers: a number not in `facts.json`, a missing asset, a highlight aimed at the wrong thing, broken timing, a broken layout rule, hidden content. Polish comes back as `warnings`, and the build runs with them. Pixel placement is not the plan check's job at all: the builders run `tools/beat_check/geometry.py` on the built page (text overflow, off the frame, highlights off target, crops slicing text). It is advisory until it has run clean on two new builds [Chase, 2026-11-02]: builders fix the FAILs they agree are real and name the ones they judge false, with frames, and it never blocks a build. Note in `RUN.md` how many of its FAILs were real, so we can tell when to make it a gate. Copy warnings and geometry WARN or UNVERIFIED findings to `RUN.md` and the handoff, and the defects round checks them on the real picture.
- Never build by hand past a refusal, and never edit the check.

For a builder retry after a passed plan, call `Workflow({scriptPath: "tools/workflows/next/recut-build.js", args: {id, styles: ["editorial"], allowFullFace, allowFullFaceSource, codex, root, note: "<intake notes verbatim, then the build/audit failure>", skipDirect: true}})`. This skips Direct, re-checks the existing `plan.json`, and builds only if it still passes. `planIssues` takes precedence over `skipDirect`. A failed owner audit or source check uses this route; a plan defect uses `planIssues`.

**Popout.** With `bottom` popout in `RUN.md`, after a passing build and before section 5:
```bash
python tools/popout.py make $P          # about 3 min: measure his head, crop the camera, cut-out, assets/popout.json
```
Read its line and any WARN. A flicker warning means look at the cut-out by eye, and use split for this video if the edge halos or flickers. Then set `"bottom": "popout"` and `"bottom_source"` in `$P/plan.json` and run `python $P/tools_local/build.py`. With `bottom` split, the build is byte for byte what it was before popout existed. A later note that switches the bottom does the same steps, and it re-renders every beat. A switch after sound leaves `sound.json` on the old picture, and the player then plays voice only. Popout moves no event, so run `python tools/sound_mix.py rebind $P --why "<the switch>"`, then `check-sheet`. Chase hit this on 2026-11-02.

Read `build.owner_audit`, which must start PASS, and `build.whole_render`. Each row states its rebuild reach and cost; put it in `RUN.md`. A build result that is not a PASS audit goes back to the builder with `skipDirect: true`. Read `build.source_check`, the actual pre-render `conform.py --all` exit code and summary: exit 3 is expected without a render, with no FAIL lines; every FAIL must be fixed before section 5. Exit 4 means the page was not measured and stops the stage.

## 5. Review render

Long job: run it in the background, and never two renders at once.
```bash
python tools/beat_render/run.py draft $P --profile review
```
Every beat at the review profile, voice only, stitched, with both checks on the stitched picture. Exit 0 means both checks finished and neither failed. The status then reads UNVERIFIED at best, because the review bed's loudness is not measured until delivery. Exit 1 is a FAIL, 2 refused with nothing rendered, 3 missing references or a check that did not finish. `beat/current.json` moves only if both checks ran to the end and neither failed. Any other picture goes in `beat/last_attempt.json`.
- A refusal or a failed owner audit means a source problem. Fix it in `$P/tools_local`, `python tools_local/build.py` from `$P`, then run again.
- A FAIL: fix the source, as section 7 does, and run `run.py change`. Read `findings` from `review.state(project)`. Only Chase can waive a finding, by clicking it in the player. Claude never writes a waiver, and says what the frames show so he can decide.

**One defects-only round, on this picture.** Run `HOUSE.md`'s Review contract once. Chase does not see this round. No gauntlet.
1. Cut contact sheets from the stitched picture, one every 2 s or so. Give two fresh reviewers the sheets, `HOUSE.md`'s defect list, banned findings and the plan-check warnings. One is a Claude subagent. The other is Sol when `codex` is true:
   `codex exec -m gpt-6.1-sol --sandbox read-only --skip-git-repo-check -i <sheet> -`, prompt on stdin. Fallback model: gpt-5.6-sol.
   Without Codex it is a second Claude subagent that reviews the sheets in reverse order and starts from the warnings, so the two do not read alike.
2. One cheap skeptic tries to refute each finding. Each kept finding names item, frame, expected and actual.
3. Fix at the source, as section 7 does, with `run.py change`. That re-check is not a second round. Unfixed findings go in the handoff.

Then write `HOUSE.md`'s handoff report: what changed and the file, each check's result, and what is still open.

## 6. Player

```bash
python tools/beat_review_v2/server.py work/<id>/v2/editorial
```
Run it in the background. It serves `http://localhost:4750`: the player in its default light grey look. `?skin=<name>` picks an optional look from `tools/beat_review_v2/skins/`; the default needs none. Give the user the URL to open in Chrome or Edge (or open the Browser pane if available), give him the handoff, then wait. He watches the real edit with his voice, pauses at a second, presses N and types. Notes save with the picture they were left on, in `work/<id>/notes.jsonl`, which is also taste evidence.

**A page cannot wake a session, so he says go in chat.** Until then, do nothing to the project: a change mid-review moves the picture under him.

He can go back to an earlier round in the player. `review.go_back(project, n)` restores its sources, plan, lock, ownership map and picture, so the next note builds from that version. A note done in a round he went back past reads "undone by go back" and comes to you under `flagged`: ask him, because he may have gone back to get rid of it. He waives a finding there too, by his click only. A review waiver also holds at that composition's 1080p final, on the same frames, and the delivery report lists it under `waived`. It does not hold at 4K60, whose frames differ.

## 7. Note round

Runs when he says go. Change only what he asked for. The `review.` calls are in `tools/beat_review/review.py`, with `project` the path to `$P`:
```bash
python -c "import json,sys; sys.path.insert(0,'tools/beat_review'); import review; print(json.dumps(review.freeze('work/<id>/v2/editorial'),indent=1))"
```

1. **Freeze.** `review.freeze(project)` returns `{notes_rev, notes, flagged}`. `notes` is the one set this round acts on, and a note added after that waits for the next round. `flagged` is notes left on an older picture: ask him about each, never apply one silently. After he explicitly asks to apply flagged notes, call `review.freeze(project, adopt=["<the ids he chose>"])` before editing and use that returned set. Keep their original ids. If the round already rendered, close it first and adopt into the next round.
2. **Map each note to source through the ownership map.** Take the note's frame. `$P/beats.lock.json` gives the beat. In `$P/ownership.json`, the owners whose `frames` hold that frame can affect it. For a scene, confirm its actual `WINDOWS` row before treating it as on screen: an `EXTRA_ROOTS` scene reaches the end for invalidation even after it is hidden. A video note names its own target.

| Owner | Source |
|---|---|
| `scene.sc-x` | Its `own("sc-x", ...)` in `tools_local/scenes.py`, its block in `tools_local/timeline.js`, its rows in `owners.py` |
| `cap.wNNNN-NNNN` | That chunk in `plan.json` `captions.chunks` |
| `hud.<state>` | Its row in `owners.py`. Every later frame shows it |
| Not an owner | Shell: `style.css`, `timeline.js` outside the blocks, `build.py`. Touches every beat |

3. **Make the smallest change that does what he said, in real sources, never generated HTML.** `index.html`, `ownership.json`, `beats.lock.json` and `events.json` are outputs. Do not tidy anything he did not mention.
4. **Keep the copy in step.** A word changed in a graphic must also change that line in `work/<id>/beats.json` copy and its `COPY_BINDS` row in `owners.py`, or the source check reads FAIL. That FAIL is correct. A changed time moves its `plan.json` anchor and its `EVENT_BINDS` row with it, and keeps its `event_id`.
5. **Rule conflicts.** A note that breaks real footage or verified numbers stops and is raised: no synthesized body pixels, and only numbers in `facts.json`. Leave that note undone and say why. Any other rule conflict: his note wins, and it is flagged in the report. A note asking for a full-screen face turns it on for this edit. Set `allow_full_face` true and `allow_full_face_source` to his exact words in `RUN.md`, `beats.json` and `plan.json`. Hard-link `work/<id>/assets/face_full.mp4` into `work/<id>/v2/editorial/assets`, then rebuild those beats. Never set it without his words.
   **Effects from other skills** [Chase, 2026-11-03]. When a note names an effect from `/animate` or `/vfx` ("glass widgets here", "use the head-to-head from animate"), use that skill's real output. Never rebuild a look-alike in ivory's own style. These skills come from the separate Chase Animations pack (github.com/ctskool/chase-animations, set up with its `npm run setup`). If the skill isn't installed in this Claude Code, say so, and leave the note in `not_done` with that reason.
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
     - Move those beats' caption chunks to `position: "fullface"`. At the split's seam they sit on his chin. (Found on the first real orbit, 2026-11-03.)
     - Bind the anchor to the first spoken word in the window, not the cut, or the event check fails. Use `--at` for the landing word.
     - Card numbers (stars, counts) come from `facts.json`, never the effect's built-in defaults.
     - End the HUD strip's run when the effect starts, since it covers the effect on full-frame beats. Chase noted it on the first real orbit, 2026-11-03.
     - Every `/vfx` effect keeps his real pixels (a cut-out, never synthesized), so the real-footage rule holds.
   - **Cost:** a clip the project hasn't used costs a new media plan; on 1030-2 one new clip re-rendered every beat. Tell him the render reach before running.
   - **Record it:** put the skill, effect, vars, command and output path in `RUN.md`. The first real run of each is unproven, so step through those beats by eye before closing the round.
6. **Rebuild.** From `$P`, `python tools_local/build.py`.
   - **Expect a build stop.** `BUILD STOPPED` means the change broke a rule of `tools/beat_render/confine.py`: a position that is not a number, a label, a chained tween, a region that is not one element, an id the shell uses. It writes no `ownership.json`, so `run.py` refuses until it is fixed. Its message names the owner, and `templates/ivory/build_kit/README.md` has the table. Fix the source and build again. Never edit `index.html` to get past it.
   - **Watch for a whole render.** `WHOLE RENDER: scene.sc-x stays in the shell` means a tag or call off confine's short list, and that any change to that scene re-renders every beat. A new line from this change is yours: write it with what is on the list. If his note truly needs it, keep it and tell him the cost in the report.
   - **Watch for a frame gap.** `FRAME GAP: show("#x", t)` means a tween on that element at plain `t` starts after its `show`, so a 60 fps final can flash it for one frame. Give the tween `A(t)`. One from this change is yours to fix, and any other goes in the report.
   - A cut note goes back to section 2's `drops.json`, `cut`, `verify`, `render`, `times` and `prep_source.py`, then re-times the beats after that join. Timing or a window change touches every beat and costs a new media plan. So does adding a video clip the project hasn't used: 1030-2's first round rendered 29 of 29 for one new clip. Tell him before quoting a partial render.
7. **Render what it touched.** `python tools/beat_render/run.py change $P --profile review`, in the background. Same exit codes as section 5. It runs the owner audit, renders every beat with no intact segment, and runs both checks on the stitched picture. On 1 FAIL or 2 refused, fix and run again. A FAIL you cannot fix goes in the report, so he sees it in the player and can waive it.
8. **Close.** `review.close_round(project, done=[note ids], not_done={note id: "why"})` snapshots sources, plan, lock, ownership map and picture, so go back can restore this round. It refuses a project that is not the newest picture, which means `run.py change` has not run since the last edit. List every frozen note in one or the other, and only list as done what this round really did. A note in `not_done`, or in neither, stays open: the player shows it as not done with the reason, it holds Approve, and the next freeze hands it back in `notes`, on any picture. A later round finishes it, or he drops it in the player.
9. **Report each note: done, or not done and why.** Name the beats that changed, what `run.py change` rendered and how long it took, and any flagged rule conflict. Then back to section 6. The player shows what changed. Rounds repeat as often as he wants.

Sound-only notes wait for section 9: put them in `not_done` with that reason, and he drops them in the player when he approves. `$P`'s `sound.json` stays untouched in a note round, even when stale.

## 8. Approval

He approves in the player, and his click is the approval: he watched this exact file. `review.approve(project, picture_sha)` refuses a picture with a FAIL not fixed or waived, with an open note, or that is not the newest picture byte for byte, then writes the record at once (`beat/approvals/<file_sha16>.json`, result `APPROVED`). No second render.
- The same click starts the final (`tools/beat_review/autofinal.py`) when the sound is ready: `sound.json` written for this picture and no sound note open. Otherwise the player says the final starts once the sound is done, and section 9 comes first. Read where it is with `review.approval_status(project)["final"]`.
- Before section 9, two things that make the next video better:
  1. **Library:** `python tools/library.py harvest $P`. It adds this edit's scenes to `templates/ivory/library/` and raises their proven counts. It writes only the library and refuses an unapproved project; report a refusal, never bypass it.
  2. **His notes into rules:** `python tools/taste_from_notes.py digest work/<id>`. Then one agent reads `work/<id>/taste-digest.md`, `templates/ivory/CANDIDATES.md` and the target rule files, and drafts candidates in CANDIDATES.md's format. It merges repeats and counts the videos. Show Chase the list to mark keep or strike. Candidates do nothing until he marks them; only then run `python tools/taste_from_notes.py promote` and show him what moved.
  Then run `python tools/run_state.py metrics <id>` and `python tools/run_state.py report`, and go to section 9.
- Any picture change after approval clears it, and so does a new note on the approved picture. The record stands, so approving that same picture again is instant.
- **The deep check, by hand only:** `approval.start(project, sha, deep=True)` re-renders every beat fresh and compares every frame first, about a whole review render. Use it only when a cached beat is in real doubt. Its results: `reconcile` (differences go to him; only his click settles them, through `review.reconcile`), `failed` (a real difference: show him the frames and treat it as a note round), `blocked` or `error` (read its `why`).

## 9. Sound

`Workflow({scriptPath: "tools/workflows/next/sound-cues.js", args: {root, id, style: "editorial", note: "<his sound note, if any>"}})`
One agent reads the approved plan, `templates/ivory/sound.md` and `sfx/sfx.json`, writes `sound.json` and runs `check-sheet`. It adds no art direction. No music. Then:
```bash
python tools/sound_mix.py check-sheet $P
python tools/sound_mix.py check-mix $P
python tools/sound_mix.py stale $P
```
**He listens in the player before the final.** Once `sound.json` exists, the player shows the cue lane and Sound tab, and the Sound button (key S) plays a listening preview: the picture stream-copied with `sound_mix`'s own mix. It's never a picture and approvals don't read it. A sound note pins a cue, doesn't clear approval, doesn't hold Approve and never enters `freeze`. When he says go, read `review.sound_notes(project)`, revise `sound.json` through `sound-cues.js` with his notes in `note`, re-run the checks below, then `review.close_sound(project, done=[ids], not_done={id: "why"})`. Claude cannot hear, so say what changed and let him listen again. When he says the sound is good, start the final: `python tools/beat_review/autofinal.py start $P` (section 10). It does nothing twice, so it's safe if his click already started it. Sound fixes before that cost no extra final.

`check-sheet` covers palette, special requests, rotation, source share, spacing, events, CTA/proof spans and picture revision. `check-mix` requires 10-26 LU under the voice; over 8 cues per 30 s is a WARN: it "just has to make sense". `stale` lists cues that need review, including moved events. `cues: []` needs `empty_reason`. Sound comes before section 10, because the final freezes `sound.json` with the picture. A sound-only note revises `sound.json` through `sound-cues.js` and costs no render of the review picture. After a final, run section 10's `build` again with the new sheet.

## 10. Final

The final is built fresh from a frozen copy of the approved composition, never from the review picture. `build` refuses without an approval record in `beat/approvals/`. Long job: never two renders at once (`tools/gpu_lock.py` queues them).

**`autofinal.py` does all of this by itself** from his Approve click, or from `python tools/beat_review/autofinal.py start $P` once the sound is good. It writes the swap file below with his click as `authorized_by`, builds 4K30 under `gpu_lock` (1080p30 when there is no `assets/face_half_4k.mp4`), delivers `out/<id>_<style>_final_4k30.mp4`, and runs `check-media`. The player shows each stage, and `work/<id>/final-<sha16>.log` has the output. On an error, read the log, fix it, and run `start` again. The commands below are what it runs, for doing it by hand.

**4K30 is the default final.** Reviews render at 1080p for speed; the edit is a page, so the final renders the same composition at 2160x3840 and text and graphics come out sharp. Prep already wrote `assets/face_half_4k.mp4` (the same frames as `face_half.mp4` at the source's full size), so nothing is re-cut. By hand: write `<work>/swaps-4k30.json` (`<work>` is `work/<id>`) pointing `assets/face_half.mp4` at it, with his approval words in `authorized_by`. YouTube plays and rewards 4K; Instagram and TikTok show 1080p at most, and the same 4K file is fine there.
```bash
# {"swaps": [{"path": "assets/face_half.mp4", "file": "<work>/assets/face_half_4k.mp4", "source": "prep_source.py face_half_4k (same frame map)", "why": "4K30 final", "authorized_by": "<his approval, verbatim>"}]}
python tools/beat_review/final.py build $P --spec 4k30 --workers 6 --swaps <work>/swaps-4k30.json
python tools/deliver.py $P <base>_4k30 --mode final --stitched <file that build printed> --source-swap assets/face_half.mp4
python tools/sound_mix.py check-media out/<base>_4k30.mp4
```
On an 85 s edit the 4K30 build took 11 minutes at 6 workers (1080p30: about 3.5), and delivering it about 10 more. A project prepped before face_half_4k existed: make it with `tools/face_retime.py raw/cut.mp4 --map face_map.json --reuse --crop <metadata face crop> --scale <crop width>x-2 --out assets/face_half_4k.mp4`, never a plain `fps=30` (the swap check refuses frames a tick off). Clips from other skills keep their own size: a /vfx clip stays 1080x1920 and is scaled up. Don't swap in a `/vfx --4k` render: a full-frame 2160x3840 clip inside the composition renders with held frames (about half its frames repeated, found 2026-11-04), while the 1080 clip plays every frame. **1080p30 is the fallback** if a 4K check fails, or if he asks for it:
```bash
python tools/beat_review/final.py build $P --spec 1080p30 --workers 4
python tools/deliver.py $P <base> --mode final --stitched <file that build printed>
python tools/sound_mix.py check-media out/<base>.mp4
```
`deliver.py` takes `$P`, never the bundle: approvals live in `$P`'s store. `build` freezes sources, plan, sound and assets to `work/<id>-final-<rev16>/` and proves the copy rebuilds byte for byte. `deliver.py` refuses a reviewed final without `--stitched`, and refuses a missing or stale sheet. It runs the output check on the delivered, mastered file. `check-media` checks only that file. The delivery manifest links the checks, picture and sheet hashes.
**A new sound sheet after a final.** Run `build` again. A bundle is never changed, so it makes `work/<id>-final-<rev16>-sound-<hash8>/`, the same picture by hard link with the new sheet, cue files and waiver lists, and renders 0 beats. Deliver the file it prints, under a new `<base>`. `deliver.py` refuses a picture from a bundle whose sheet or cue bytes are not `$P`'s, so the old sound cannot go out by accident.
Send him a phone copy of the sounded file and wait for final approval. Sound quality and stressed-word masking stay UNVERIFIED until Chase listens.

**4K60, only if he asks for 60 fps.** Say plainly first: no whole short from a raw has been built this way (4K30 has). It is a derivative revision with its own bundle, and `derivative.json` says exactly what changed. Same cut, audio and plan as approved.
```bash
# Rebuild face_half at 60 fps with ffmpeg from raw/cam_cut.mp4 (metadata.json camera_crops half) or,
# with no CAMERA file, raw/cut.mp4 (face_top_px, face_region). Real pixels only.
# Only when RUN.md has allow_full_face true: rebuild face_full the same way (camera_crops full), scaled to 2160x3840.
# With bottom popout: python tools/popout.py make $P --final writes both popout clips at 2x and work/<id>/swaps-popout.json.
#   Merge its rows into swaps.json and use them instead of face_half (popout pages don't use face_half).
# List each in swaps.json: {"swaps": [{path, file, source, why, authorized_by}]}. A swap needs his words in authorized_by.
python tools/beat_review/final.py build $P --spec 4k60 --workers 6 --swaps swaps.json
python tools/deliver.py $P <base>_4k60 --mode final --stitched <file that build printed> --source-swap <each swapped path, e.g. assets/face_half.mp4>
python tools/sound_mix.py check-media out/<base>_4k60.mp4
```
`--source-swap` lists the same paths as `swaps.json`, so leave it out only if that file lists none. It states what is expected and authorizes nothing. A new sound sheet at 4K60 is a whole 4K render, because rebinding makes the derivative's sheet its own.
- Screen clips and plates keep their preview size. With `allow_full_face` true, full-face punch-ins are real camera pixels scaled up about 1.9x. Tell him what applies.
- **If the render fails, or a check does not pass: say "the 4K60 final cannot be done yet". His approved file stays the 4K30 (or 1080p) final.** Never hand over a guess.

## 11. CapCut

Not part of this release. Do not write a CapCut draft from this skill.
