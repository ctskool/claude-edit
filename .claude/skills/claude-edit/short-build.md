Read this when the cut listen is answered and the run is a short. It holds the source prep cases from section 2 and the steps of sections 3 and 4.

## Source prep cases (end of section 2)

After his answer, prepare the source and corrected words, then begin section 3:
```bash
python tools/prep_source.py $R/cut.mp4 work/<id> --face-top 0.52
# a face-only take (no screen above the face): python tools/prep_source.py $R/cut.mp4 work/<id> --no-camera --face-top 0.15 --face-bottom 0.63
#   pick the head-and-shoulders window from a frame grab; a camera file rotated against the take also needs --no-camera
#   with full-face on, look at one frame of assets/face_full.mp4 too: on a face-only take prep cuts it from the same head-and-shoulders
#   window, a tight close-up. For his whole shot, remake it from the whole frame with the same frame map (real pixels, scale only):
#   python tools/face_retime.py $R/cut.mp4 --map work/<id>/face_map.json --reuse --proxy-crop <the face_half crop, W:H:X:Y> --crop <W:H:0:0 of the source> --scale 1080x1920 --out work/<id>/assets/face_full.mp4
#   then look at one frame of assets/face_half.mp4: 0.52 on a face-only take crops to his chest (cold test, 2026-11-10)
python tools/make_words.py work/<id>/transcript.json work/<id>/words.json --fix "wrong=right"
```

## 3. Facts and plan

One agent, no Workflow, no subagents. Work from `templates/ivory/LIGHT.md`.
1. **Facts.** Decide what will appear on screen, then verify only that. Every number, name, price and quote on a graphic gets a `work/<id>/facts.json` entry with source and date. A spoken claim nothing supports stays in the caption, and the graphic shows the neutral thing it is about.
2. **Plates.** Capture only the pages the video needs: write `work/<id>/shots.spec.json` and run `python tools/capture_cache.py work/<id>/shared/shots work/<id>/shots.spec.json`. His own clips go in `shared/clips`. Measure crops on the capture, never by guess.
3. **Plan.** Write `work/<id>/beats.json` and `$P/plan.json` directly (fields: the kit README). Snap every beat edge to a 30 fps frame. Put each BIG join on its frame in the face clip, read from `face_map.json`, not on the cut's own time: on 1106-1 two joins sat one frame apart and failed as double cuts. `beats.json` carries `allow_full_face`, its source, `cta_start` and each beat's `copy`.
   **The hook gets the most effort** [Chase, 2026-11-17 and 2026-11-18]. The first beat decides whether a scroller stays, so it is the one place to spend real design and motion effort and be inventive. Ask what single picture would make someone with no context stop, then build that, not the nearest card from the library. There is no recipe for it on purpose. Body beats can stay simple. The house limits still hold.
4. **Self-check before building.** Nothing else checks the plan, so do not skip a line:
   - Would the hook's first second stop a cold scroller? If it is only fine, it is not done.
   - Every BIG join is covered, on its face-clip frame.
   - No scene's window crosses a beat edge. A picture that holds across two lines is one beat.
   - No top panel only repeats his words.
   - Every payoff (a number, a name, the last row of a list) is on screen at least one second: land it a stressed word earlier if the cut is close.
   - Every line of the intake notes is honoured, one by one.
   Put anything unresolved in `RUN.md`.

## 4. First edit: the whole video in ivory

**Pilot look first** [Chase, 2026-11-10]. Before building the whole video, write only the hook's and the first step's scenes, build, and take six to eight stills across them with `npx hyperframes snapshot --at <times>`. Run the kit's QA on the pilot as well, geometry included: a new look's overflows show up here first. Send him the sheet with one line on how the rest will follow it, and wait. What he says is intake notes for the rest. Skip it only when he says to run straight through; record `pilot` and his words in `RUN.md`. Events with no scene yet read UNVERIFIED in the source check until the rest is built, which is expected.

The same agent builds, in the real kit:
```bash
python templates/ivory/build_kit/new_project.py <id>     # add --full-face only with allow_full_face true
# write $P/tools_local/scenes.py, timeline.js, owners.py, and style.css only for a new component
cd $P ; python tools_local/build.py
```
Then the kit README's QA, in its order: owner audit, `conform.py --all` (exit 3 with no FAIL line), `npx hyperframes lint`, `motionlint.py`, and `python tools/beat_check/geometry.py $P` (advisory). Then `npx hyperframes snapshot --at <one time per scene>` and look at every frame before spending a render.
- Bind each beat's anchor and every `beats.json` copy line. A full-face beat has no scene: bind its anchor to its chip as `present`. An element that is up on the switch frame, one frame ahead of its word, takes `lead_frames` 1 in its bind. Do not move it a frame later, which leaves an empty panel.
- Reuse a proven scene from `templates/ivory/library/INDEX.md` before writing a new one.
- With `codex` true, scene images go through `codex exec`: generate each missing `shared/scenes/<beat>.png` through Codex's built-in image tool, and record prompts and dimensions in `ASSETS.md`. Without it, no scene beats.
- The popout paragraph and the `build.py` stop, whole-render and frame-gap lines (section 7, step 6) apply as written.

**A look from a reference** (by hand; only when he asked for the whole look at intake). `reference-look.md`.

**Popout.** With `bottom` popout in `RUN.md`, after a passing build and before section 5:
```bash
python tools/popout.py make $P          # about 3 min: measure his head, crop the camera, cut-out, assets/popout.json
```
Read its line and any WARN. A flicker warning means look at the cut-out by eye, and use split for this video if the edge halos or flickers. Then set `"bottom": "popout"` and `"bottom_source"` in `$P/plan.json` and run `python $P/tools_local/build.py`. With `bottom` split, the build is byte for byte what it was before popout existed. A later note that switches the bottom does the same steps, and it re-renders every beat. A switch after sound leaves `sound.json` on the old picture, and the player then plays voice only. Popout moves no event, so run `python tools/sound_mix.py rebind $P --why "<the switch>"`, then `check-sheet`. Chase hit this on 2026-11-02.

**Reading the build result.** Read the owner audit, which must start PASS, and every `WHOLE RENDER` row. Each row states its rebuild reach and cost; put it in `RUN.md`. An audit that is not PASS is a source problem: fix it in `tools_local` and build again. Read the source check, the actual pre-render `conform.py --all` exit code and summary: exit 3 is expected without a render, with no FAIL lines; every FAIL must be fixed before section 5. Exit 4 means the page was not measured and stops the stage.
