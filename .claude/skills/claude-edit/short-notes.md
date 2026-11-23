Read this when he says go on his notes. It holds section 7, moved here unchanged from `SKILL.md`. The `/animate` and `/vfx` part of step 5 is in `effects-bridge.md`.

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
   **Effects from other skills.** When a note names an effect from `/animate` or `/vfx`, read `effects-bridge.md` before changing anything for it.
6. **Rebuild.** From `$P`, `python tools_local/build.py`.
   - **Expect a build stop.** `BUILD STOPPED` means the change broke a rule of `tools/beat_render/confine.py`: a position that is not a number, a label, a chained tween, a region that is not one element, an id the shell uses. It writes no `ownership.json`, so `run.py` refuses until it is fixed. Its message names the owner, and `templates/ivory/build_kit/README.md` has the table. Fix the source and build again. Never edit `index.html` to get past it.
   - **Watch for a whole render.** `WHOLE RENDER: scene.sc-x stays in the shell` means a tag or call off confine's short list, and that any change to that scene re-renders every beat. A new line from this change is yours: write it with what is on the list. If his note truly needs it, keep it and tell him the cost in the report.
   - **Watch for a frame gap.** `FRAME GAP: show("#x", t)` means a tween on that element at plain `t` starts after its `show`, so a 60 fps final can flash it for one frame. Give the tween `A(t)`. One from this change is yours to fix, and any other goes in the report.
   - A cut note goes back to section 2's `drops.json`, `cut`, `verify`, `render`, `times` and `prep_source.py`, then re-times the beats after that join. Timing or a window change touches every beat and costs a new media plan. So does adding a video clip the project hasn't used: 1030-2's first round rendered 29 of 29 for one new clip. Tell him before quoting a partial render.
7. **Render what it touched.** `python tools/beat_render/run.py change $P --profile review`, in the background. Same exit codes as section 5. It waits its turn in `tools/gpu_lock.py`'s queue behind any other render (another session's, a 4K final), so several sessions can ask at once; a `gpu_lock: waiting for ...` line means it is queued, not stuck. It runs the owner audit, renders every beat with no intact segment, and runs both checks on the stitched picture. On 1 FAIL or 2 refused, fix and run again. A FAIL you cannot fix goes in the report, so he sees it in the player and can waive it.
8. **Close.** `review.close_round(project, done=[note ids], not_done={note id: "why"})` snapshots sources, plan, lock, ownership map and picture, so go back can restore this round. It refuses a project that is not the newest picture, which means `run.py change` has not run since the last edit. List every frozen note in one or the other, and only list as done what this round really did. A note in `not_done`, or in neither, stays open: the player shows it as not done with the reason, it holds Approve, and the next freeze hands it back in `notes`, on any picture. A later round finishes it, or he drops it in the player.
9. **Report each note: done, or not done and why.** Name the beats that changed, what `run.py change` rendered and how long it took, and any flagged rule conflict. Then back to section 6. The player shows what changed. Rounds repeat as often as he wants.

Sound-only notes wait for section 9: put them in `not_done` with that reason, and he drops them in the player when he approves. `$P`'s `sound.json` stays untouched in a note round, even when stale.
