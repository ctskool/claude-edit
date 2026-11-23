---
name: claude-edit
description: A video editor for talking-head videos. Takes your raw take through the spine and a cut listen to a whole first edit in the ivory template, a review render and a player where you leave notes at exact seconds. Claude changes only what you noted, you approve, then sound and the final. Shorts in several looks, and 16:9 long-form.
argument-hint: "<raw takes> [template] [notes]"
disable-model-invocation: true
---

# /claude-edit

Chase Hannegan built this editor on his own videos. In this skill and every rule file, **Chase (he, his) means the person running it: the user.** A `[Chase]` tag records where a rule came from, and a dated quote is his note on one of his own videos. `status.md` says what is proven.

Run it for: $ARGUMENTS

Project root: resolve once at intake with `python -c "from tools.paths import project_root; print(project_root().as_posix())"`. Store that result as `root` and change the working directory to it. `CLAUDE_EDIT_ROOT` overrides the checkout location. Run `python tools/doctor.py --fix-hints` before a new installation's first edit. Use Python and native tool argv arrays for file operations, quote every path in a shell command, and detect executables with Python `shutil.which`. Template: `ivory` is the only template for shorts (the layout and the kit), and tools call it `editorial`. What changes from short to short is the **look** laid over it: charcoal, neo-brutalist, collage, blueprint, sky and the recolours (section 1, "Look"). A 16:9 long-form video uses the `charcoal` template: the Long-form section below.
**One agent builds a short** [Chase, 2026-11-10]: it plans and builds from the one-page card `templates/ivory/LIGHT.md` and `templates/ivory/build_kit/README.md`. Open a full rule file (`templates/HOUSE.md`, `layout.md`, `captions.md`, `STYLE.md`) only when the card does not answer the question, and log it in `RUN.md`. The older multi-agent pipeline was retired on 2026-11-12 and does not ship. Chase wins every conflict.
Workflow hosting: `Workflow(...)` (the sound step) is not a built-in plain Claude Code command. If this session has no Workflow host, read the workflow file and run its phases through native Claude Code subagents: each `agent` is one fresh subagent; keep the prompt, schema, result fields and every check and retry gate. Do not run the file with plain Node.
Trial ideas stay off. Open decisions stay open: keep current behaviour and flag them.

**The flow.** Raw in, spine and one-minute cut listen, whole edit in ivory, review render, player, notes, he says go in chat, note round, repeat, approval, sound, final. He reacts to his own edit. There is no pick list before the build.

`P=work/<id>/v2/editorial` below. Every Python line runs from the project root.

**This file is the router.** Sections 1 and 2 run on every video. Sections 3 to 10 are a short's stages: each says what happens and names the side file in this folder that holds its steps. Read a side file when the run reaches it, not before. "Section N" in any of these files means that numbered section, here and in its side file. "Read next" at the end lists every side file and when to read it.

## 1. Intake and state

- Takes: raw OBS `.mkv` files at the paths supplied in $ARGUMENTS; resolve each to an absolute path. If no path was supplied, ask for the take path. Confirm which by frame grabs and a quick transcript. A finished export is not handled here yet: say so.
- Template: ivory for a vertical short. A widescreen long-form video for YouTube is `charcoal`: go to the Long-form section after the cut listen. Any other name, stop and say only those two exist here. Everything left is notes.
- Look: `ivory` unless he names another shipped look in words ("charcoal", "the dark one", "collage", "the Vox one"). `ls templates/ivory/build_kit/looks` is the list; any other name, say which looks exist. `collage` is a whole aesthetic with its own images and motion, not a recolour: its `LOOK.md` says what a scene writes for it. `blueprint` [Chase, 2026-11-19] is different again: the whole short as one engineering drawing the camera travels across, hand-built on its own engine after the cut is approved, not through `build.py`; its `LOOK.md` says how. `sky` [Chase, 2026-11-19] is the same kind: the pixel Claude guide acting the short out on a pixel sky, hand-built on its own engine; its `LOOK.md` says how. **Both are still reviewed in the player** [Chase, 2026-11-22]: notes by beat, rounds and his Approve click starting the 4K final, through `tools/look_player.py` (each `LOOK.md`, "Review in the player"); sections 6 to 8 hold for them, with the spec's `player` command in place of `run.py`, and section 9 does not apply (their few cues are in the review picture). Record `look` and `look_source` (his words, or `default`) in `RUN.md` and `plan.json`, and read that look's `LOOK.md` after the card. A reference video is not a look name: that is the Reference line below.
- Full-face: read `templates/<name>/template.json`. `allow_full_face = template.full_face OR Chase's request for this edit`. A missing file, a missing field or anything but the Boolean `true` reads false. Ivory reads false.
- His request counts only when he asks in words for a full-screen face on this edit. Skipping a page or running straight through grants nothing.
- Bottom: `split`, unless he asks for popout in words ("popout", "the pop out version"). Then the template's `template.json` must have a `popout` block. If it doesn't, say this template has no popout yet. Record `bottom` and `bottom_source` (his exact words, or `default`) in `RUN.md`. Popout needs the clean camera from section 2. Rules: `templates/HOUSE.md` "Popout bottom".
- Reference: only when he names one in words or hands over a video ("like this reel"). Ask once, before the spine: "The whole look, or specific things you liked?" Then read `reference-look.md`: what to record, what each answer means, and the rules that hold either way.
- Hooks: when he asks for hooks 1, 2 and 3 of one short, each extra hook gets its own opener graphic on its words, a different colour look for the whole video from the standard set, and a different caption font, all on hook 1's body [Chase, 2026-11-16]. It runs after hook 1 is approved and only when he asks. Read `hook-variants.md`. **The three-aesthetic test he asked for** [Chase, 2026-11-17] (charcoal, neo-brutalist and collage versions of one take) was delivered on 2026-11-18 and is how a short is remade in another kit look: `hook-variants.md` "The three-aesthetic test".
- `allow_full_face_source` is `template`, or his exact words when they turned it on. Resolve both here and record both in `RUN.md`, `beats.json` and `plan.json`. If either changes before the build, re-run the plan. After the build, a note turns it on as section 7 says.
- Codex: the skill assumes plain Claude Code. Run `codex --version` once. Only exit 0 sets `codex = true`; anything else is false. With Codex, scene images can be generated and Sol is the defects-round reviewer; without it, no beat is a scene and the reviewer is a Claude subagent (`short-review.md`). Record `codex` in `RUN.md`.
- Hard-link each take into `work/<id>/keep/` with `ln` until he says done. If that fails, flag it.
- Root: `root` is this project folder as an absolute path. Pass it to the sound workflow (section 9), which cannot find it itself. On a new machine, run `python tools/doctor.py` first and stop on any FAIL. `INSTALL.md` says how to fix each one.
- State lives in `work/<id>/run.json`. Start a run with `python tools/run_state.py init <id> --model "<model>" --template ivory` (add `--codex` when `codex` is true, and `--reference <slug>` when he named one). At every stage boundary run `start <id> <stage>` before the work and `done <id> <stage> --note "<result>"` after checking its output. Use `wait` while waiting on Chase and `fail` for a failure. A resumed or compacted session runs `python tools/run_state.py status <id>` first and checks the real outputs before carrying on. Stages: intake, spine, cut_listen, research, facts_assets_beats, direction, plan_check, build, review_render, defects, player, note_round_N, approval, sound, final. The names come from the archived pipeline. A run has no `research` or `plan_check` work and plans in one step, and the tool has no skip: such a stage stays `pending` and `status` may name it as next.
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
- Camera [Chase, 2026-11-10]: he may record with the camera hidden in OBS (screen only in the take) and the face only in the CAMERA file. `session` then syncs by the mic audio both files carry (`audio match`, should be 0.9+) and `prep_source.py` centres the face crops on his face found in the camera. A `motion match` line under 0.5 on a take with no face means the CAMERA file has no audio: stop and tell him the Source Record filter's Different Audio (Mic/Aux) is off. A CAMERA file at a different frame rate than the take is refused: the filter's Framerate must equal the canvas rate.
- Keep the wrong-to-right list in `$R/corrections.json`. No tool reads it yet, so pass each pair as `--fix`.
- Run the full read-through in `story.md`, with its fresh reader, before `render`.
- Read every `RUN-ON` line `cut` prints and listen to that second before `render`: it means he may still be speaking when the join lands (`story.md` step 7). `NUMBER` lines point at the usual cause.
- **Stop for the cut listen, in the cut review page** (standing step since 2026-11-12: Chase, "the cut review replaces it"; `story.md` steps 8 and 9). After `cut` and `verify`, and before `render`: start `tools/cut_review/server.py $R`, send him the link with the cut report from `story.md`, and wait. It looks like CapCut: his camera on top, one row of clips below. He trims by ear and approves there; his Approve click runs `render` for both files. Run `tools/cut_review/core.py $R --video` in the background right after `session` so the picture is ready. **While he listens, keep working** [Chase, 2026-11-12]: the page renders the machine's cut as a draft in the background, and you prepare everything that stores no time (facts, assets, the plan). **Long-form: the scenes and the storyboard are finished during his listen** [Chase, 2026-11-13], starting the moment the page opens with `new_project.py --quick`, not when the draft is rendered. `story.md` step 8 has the order and the rules. Nothing made from the draft goes to him as approved, and nothing that reads `cut.mp4` or stores a time is final until he approves. If he asks for the old way, a small phone copy of `$R/cut.mp4` after `render` still works.
- **Nothing runs while he listens.** Research takes minutes and waits for his answer.

After his answer, prepare the source and corrected words, then begin section 3:
```bash
python tools/prep_source.py $R/cut.mp4 work/<id> --face-top 0.52
# a face-only take, a camera file rotated against the take, or full-face on: read "Source prep cases" in short-build.md before this line
python tools/make_words.py work/<id>/transcript.json work/<id>/words.json --fix "wrong=right"
```

## 3. Facts and plan

One agent, no Workflow, no subagents. Work from `templates/ivory/LIGHT.md`: facts for what will appear on screen, plates, then `beats.json` and `$P/plan.json`, then the self-check before building. Steps: `short-build.md`.

## 4. First edit: the whole video in ivory

The pilot look comes first, and it is a stop. Then the same agent builds in the real kit (`python templates/ivory/build_kit/new_project.py <id>`, then `python tools_local/build.py` from `$P`), runs the kit README's QA in its order, and looks at a snapshot of every scene before spending a render. With `bottom` popout, `python tools/popout.py make $P` follows a passing build. Steps: `short-build.md`. The whole look from a reference: `reference-look.md`.

## 5. Review render

Long job: run it in the background, and never two renders at once.
```bash
python tools/beat_render/run.py draft $P --profile review
```
Then one defects-only round on this picture, which Chase does not see: `python tools/beat_check/jumps.py $P`, your own look at the frames around every layout switch, and one fresh reviewer, never zero. Fix at the source once, then write `HOUSE.md`'s handoff report. Exit codes, the reviewer's brief and who reviews: `short-review.md`.

## 6. Player

```bash
python -B tools/beat_review_v2/server.py work/<id>/v2/editorial
```
Run it in the background. It serves `http://localhost:4750`. Set `PORT` when another video's player holds that port; 4744 and 4745 are refused. Open it in the Browser pane, give him the handoff, then wait. Going back a round and waivers: `short-review.md`.

## 7. Note round

Runs when he says go. Change only what he asked for. In order: `review.freeze(project)`; map each note to its source through the ownership map; the smallest change in real sources, never generated HTML; keep the `beats.json` copy in step; `python tools_local/build.py` from `$P`, reading any `BUILD STOPPED`, `WHOLE RENDER` or `FRAME GAP` line; `python tools/beat_render/run.py change $P --profile review`; `review.close_round(...)`; report each note done, or not done and why; back to section 6. All nine steps: `short-notes.md`. A note that names an effect from `/animate` or `/vfx`: `effects-bridge.md` first.

## 8. Approval

He approves in the player, and his click is the approval: he watched this exact file. The same click starts the final when the sound is ready. Before section 9, harvest the library and digest his notes into candidate rules, then run the metrics. Any picture change after approval clears it. Steps, and the deep check that is by hand only: `short-finish.md`.

## 9. Sound

`tools/workflows/next/sound-cues.js` writes `sound.json`, then `check-sheet`, `check-mix` and `stale`. No music. He listens in the player before the final. Claude cannot hear, so say what changed and let him listen again. When he says the sound is good, start the final: `python tools/beat_review/autofinal.py start $P`. Steps: `short-finish.md`.

## 10. Final

**4K30 is the default final.** `autofinal.py` does all of it by itself, from his Approve click or from `start`: it builds fresh from a frozen copy of the approved composition under `gpu_lock`, delivers `out/<id>_<style>_final_4k30.mp4` and runs `check-media` (1080p30 when there is no `assets/face_half_4k.mp4`). Send him a phone copy of the sounded file and wait for final approval. Steps: `short-finish.md`. By hand, 1080p30, a project prepped before `face_half_4k.mp4`, a new sound sheet after a final, and 4K60: `final-by-hand.md`.

## Long-form (charcoal)

A widescreen (16:9) YouTube video: his screen take plus the camera file, minutes long. Built by hand by one agent from one page, **`templates/charcoal/CARD.md`**: his long-form rules, the stops, every command, the scene kit and how rendering works. Read it right after the cut listen, and `templates/charcoal/sections.md` before writing a scene. Sections 3 to 10 above do not apply, and `run.py`, `sound.json` and the Approve click do not know this template.

- Sections 1 and 2 as written: intake, spine, the cut listen. `prep_source.py` is not used. Before a real take, check a 10-second test of the camera file with `new_project.py <id> --check-face`: it must be a clean, unmasked shot.
- **The cut listen takes his timing notes too** [Chase, 2026-11-11]: he hears the tight cut before any graphic exists, in the cut review page, where he fixes most of them himself. After the cut, scan the short gaps it removed for speech with no word label (a dropped word the aligner mislabelled).
- **The base is his camera full frame and his screen full frame with his face in a corner** [Chase, 2026-11-11]; a designed graphic per idea, of something real. No face-only stretch over about 12 s without a reason. Never text over his full-frame face.
- **He approves a stills storyboard before anything renders** (`build_kit/storyboard.py`), then a pilot of the intro and first chapter in the player, before the rest is written.
- Rendering is by slice on the GPU: `python templates/charcoal/build_kit/render_slices.py work/<id> --rev v1`, about 5 minutes for a 16-minute video and under a minute after a note on one graphic. Full priority by default; `--background` (idle priority, about twice as slow) only when he says he is recording [Chase, 2026-11-20]. The player shows one beat per named segment (`to_player.py`); change only what he notes.
- His approval is in chat. The final is `render_slices.py work/<id> --rev final --res 4k`; check it as the card says. Its 4K slices are drawn in the background while he reviews each version (`templates/charcoal/build_kit/README.md` "Final"), never only after approval. **Sound is asked once per video** [Chase, 2026-11-22: "case-by-case... for me right now, it tends to be no"]: at the storyboard stop, ask whether this video gets sound cues, and record the answer in `RUN.md`. No answer means no: voice only is a complete final and nothing waits on sound. When he says yes, put the cues in the player, never a side file.
- For the upload: `out/<id>-<rev>-chapters.txt`, captions with `tools/words_srt.py`, titles with `/yt-package`.
- A helper only this video needs goes in the project's `tools/local.mjs`. A script written in the run folder that the next video would need moves into the kit before the run is closed.

## Stops: where Chase is asked something

1. Intake: with a reference, ask the one question before the spine.
2. The cut listen in the cut review page (section 2). Prepare on the draft while he listens; nothing made from it is shown as approved until he answers.
3. The pilot look (section 4). Skip it only when he says to run straight through.
4. The player (section 6): give him the handoff, then wait until he says go in chat.
5. In a note round (section 7): ask him about each flagged note, raise a note that breaks real footage or verified numbers, and tell him the render reach before a change that re-renders every beat.
6. Approval (section 8) is his click in the player. Then show him the candidate rules to mark keep or strike.
7. Sound (section 9): he listens in the player and says when the sound is good.
8. The final (section 10): send the phone copy and wait for final approval.
   Long-form has its own stops, in `templates/charcoal/CARD.md`: the face check, the cut listen with timing notes, the storyboard, the pilot, notes by segment, approval in chat.
9. Only when they apply: "Keep this look for next time?" once after approval (`reference-look.md`); 4K60 is said plainly first (`final-by-hand.md`).

## Hard rules, every template

Chase wins every conflict. `templates/HOUSE.md` "Non-negotiables" is the full list for footage and facts, and each template's files add their own. These hold on every run:
- **Real footage and verified numbers.** A note that breaks real footage or verified numbers stops and is raised: no synthesized body pixels, and only numbers in `facts.json`. Leave that note undone and say why. Any other rule conflict: his note wins, and it is flagged in the report.
- **Full-screen face** only by the template or his words, as intake says. Never set it without his words.
- **Renders.** Long job: run it in the background, and never two renders at once.
- **While he reviews.** **A page cannot wake a session, so he says go in chat.** Until then, do nothing to the project: a change mid-review moves the picture under him.
- **Notes.** Change only what he asked for, in real sources, never generated HTML.
- **Findings.** Only Chase can waive a finding, by clicking it in the player. Claude never writes a waiver, and says what the frames show so he can decide.
- **Generated images.** Images go through `codex exec`. Without Codex, no generated images at all (`templates/HOUSE.md`), so no beat is a scene.

## Read next

| Read | When |
|---|---|
| `templates/story.md` | Before the spine, every run |
| `templates/ivory/LIGHT.md`, then `templates/ivory/build_kit/README.md` | Every short, before section 3 |
| `templates/ivory/build_kit/looks/<name>/LOOK.md` | The short's `look` is not `ivory`: after the card |
| `short-build.md` | The cut listen is answered and the run is a short: prep cases, sections 3 and 4 |
| `short-review.md` | The build passed its QA: sections 5 and 6 |
| `short-notes.md` | He says go on his notes: section 7 |
| `short-finish.md` | He approves, or sound or the final is next: sections 8, 9 and 10 |
| `effects-bridge.md` | A note names an effect from `/animate` or `/vfx` |
| `reference-look.md` | He names a reference in words or hands over a video |
| `hook-variants.md` | He asks for hooks 1, 2 and 3 (more than one hook) of the same short |
| `final-by-hand.md` | `autofinal.py` failed or cannot be used, a 4K check fails, he asks for 1080p or 60 fps, or the sound sheet changes after a final |
| `templates/charcoal/CARD.md`, then `templates/charcoal/sections.md` | A 16:9 long-form video, after the cut listen |
| `status.md` | You need to know whether a stage or tool is proven before relying on it. A run never needs it |
| A full rule file (`templates/HOUSE.md`, `templates/ivory/layout.md`, `templates/ivory/captions.md`, `styles/editorial/STYLE.md`) | The card does not answer the question. Log it in `RUN.md` |
