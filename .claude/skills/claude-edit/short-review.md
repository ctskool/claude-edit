Read this when the build has passed its QA and the first review render is next. It holds sections 5 and 6, moved here from `SKILL.md` unchanged except for the player's server line (the v2 page, which recent runs use).

## 5. Review render

Long job: run it in the background, and never two renders at once.
```bash
python tools/beat_render/run.py draft $P --profile review
```
Every beat at the review profile, voice only, stitched, with both checks on the stitched picture. Exit 0 means both checks finished and neither failed. The status then reads UNVERIFIED at best, because the review bed's loudness is not measured until delivery. Exit 1 is a FAIL, 2 refused with nothing rendered, 3 missing references or a check that did not finish. `beat/current.json` moves only if both checks ran to the end and neither failed. Any other picture goes in `beat/last_attempt.json`.
- A refusal or a failed owner audit means a source problem. Fix it in `$P/tools_local`, `python tools_local/build.py` from `$P`, then run again.
- A FAIL: fix the source, as section 7 does, and run `run.py change`. Read `findings` from `review.state(project)`. Only Chase can waive a finding, by clicking it in the player. Claude never writes a waiver, and says what the frames show so he can decide.

**One defects-only round, on this picture.** Chase does not see this round. No gauntlet.

**One fresh reviewer, never zero.** On 1106-1 every real defect the automated checks passed was found here. Cut contact sheets from the stitched picture, one frame a second, and look at them yourself. Give one fresh subagent the sheets, the picture's path, the transcript, the layout-switch times, and `LIGHT.md`'s defect list with its never-report line. It sees rendered frames only: no source, no plan. Ask for full-size frames only where a sheet raises a doubt; a brief that stepped all 17 switches took 12 minutes. **Who reviews:** with `codex` true (intake checked it), Sol: `codex exec -m gpt-6.1-sol --sandbox read-only --skip-git-repo-check -i <sheet> -`, one `-i` per sheet, brief on stdin, fallback model gpt-5.6-sol. With `codex` false, one Claude subagent started with `model: "sonnet"`; never let it inherit the session's model. Neither choice has been measured against the other yet, so if a reviewer comes back with nothing on a first render, look harder at the sheets yourself before trusting it. A sheet at one frame a second cannot show a one-frame snap: on the cold test Sol reported nothing and the builder then found one. So before the reviewer, run `python tools/beat_check/jumps.py $P` and look at every frame it names; a JOIN line is a defect. Then pull the frame before and the two frames after every layout switch at full size and look at them yourself, whatever the reviewer says: a caption on the wrong side of a switch and a card that opens empty were both found there and nowhere else. Refute what you can on full-size frames, then fix at the source once, as step 3 below says. A FAIL from the re-render gets fixed too, and that is not a second round.

Then fix at the source, as section 7 does, with `run.py change`. That re-check is not a second round. Unfixed findings go in the handoff.

Then write `HOUSE.md`'s handoff report: what changed and the file, each check's result, and what is still open.

## 6. Player

```bash
python -B tools/beat_review_v2/server.py work/<id>/v2/editorial
```
Run it in the background. It serves `http://localhost:4750`: the same player, notes, rounds and approval as `tools/beat_review/`, in the look he picked on 2026-11-02. Set `PORT` when another video's player holds 4750 (`.claude/launch.json` has one entry per recent video, 4750 to 4757); 4744 and 4745 are refused. Open it in the Browser pane, give him the handoff, then wait. He watches the real edit with his voice, pauses at a second, presses N and types. Notes save with the picture they were left on, in `work/<id>/notes.jsonl`, which is also taste evidence.

**A page cannot wake a session, so he says go in chat.** Until then, do nothing to the project: a change mid-review moves the picture under him.

He can go back to an earlier round in the player. `review.go_back(project, n)` restores its sources, plan, lock, ownership map and picture, so the next note builds from that version. A note done in a round he went back past reads "undone by go back" and comes to you under `flagged`: ask him, because he may have gone back to get rid of it. He waives a finding there too, by his click only. A review waiver also holds at that composition's 1080p final, on the same frames, and the delivery report lists it under `waived`. It does not hold at 4K60, whose frames differ.
