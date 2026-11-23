Read this when he approves in the player, or when sound or the final is the next step. It holds sections 8, 9 and 10, moved here unchanged from `SKILL.md`. The by-hand final (4K30 by hand, 1080p30, a new sound sheet after a final, 4K60) is in `final-by-hand.md`.

## 8. Approval

He approves in the player, and his click is the approval: he watched this exact file. `review.approve(project, picture_sha)` refuses a picture with a FAIL not fixed or waived, with an open note, or that is not the newest picture byte for byte, then writes the record at once (`beat/approvals/<file_sha16>.json`, result `APPROVED`). No second render (Chase, 2026-11-04: "once I've done the final approval on the editor, just it should go right into the 4K build").
- The same click starts the final (`tools/beat_review/autofinal.py`) when the sound is ready: `sound.json` written for this picture and no sound note open. Otherwise the player says the final starts once the sound is done, and section 9 comes first. Read where it is with `review.approval_status(project)["final"]`.
- Before section 9, two things that make the next video better:
  1. **Library:** `python tools/library.py harvest $P`. It adds this edit's scenes to `templates/ivory/library/` and raises their proven counts. It writes only the library and refuses an unapproved project; report a refusal, never bypass it.
  2. **His notes into rules:** `python tools/taste_from_notes.py digest work/<id>`. Then one agent reads `work/<id>/taste-digest.md`, `templates/ivory/CANDIDATES.md` and the target rule files, and drafts candidates in CANDIDATES.md's format. It merges repeats and counts the videos. Show Chase the list to mark keep or strike. Candidates do nothing until he marks them; only then run `python tools/taste_from_notes.py promote` and show him what moved.
  Then run `python tools/run_state.py metrics <id>` and `python tools/run_state.py report`, and go to section 9.
- Any picture change after approval clears it, and so does a new note on the approved picture. The record stands, so approving that same picture again is instant.
- **The deep check, by hand only:** `approval.start(project, sha, deep=True)` re-renders every beat fresh and compares every frame first, about a whole review render. Use it only when a cached beat is in real doubt. Its results: `reconcile` (differences go to him; only his click settles them, through `review.reconcile`), `failed` (a real difference: show him the frames and treat it as a note round), `blocked` or `error` (read its `why`).

## 9. Sound

`Workflow({scriptPath: "tools/workflows/next/sound-cues.js", args: {id, style: "editorial", note: "<his sound note, if any>"}})`
One agent reads the approved plan, `templates/ivory/sound.md` and `templates/ivory/sfx/sfx.json`, writes `sound.json` and runs `check-sheet`. It adds no art direction. No music. Then:
```bash
python tools/sound_mix.py check-sheet $P
python tools/sound_mix.py check-mix $P
python tools/sound_mix.py stale $P
```
**He listens in the player before the final.** Once `sound.json` exists, the player shows the cue lane and Sound tab, and the Sound button (key S) plays a listening preview: the picture stream-copied with `sound_mix`'s own mix. A sheet he has not heard yet switches the player to "Sound: with cues" by itself [Chase, 2026-11-18: clicking over from voice only after sound was added "is not a very good user experience"]; turning it off by hand sticks until the next new sheet. It's never a picture and approvals don't read it. A sound note pins a cue, doesn't clear approval, doesn't hold Approve and never enters `freeze`. When he says go, read `review.sound_notes(project)`, revise `sound.json` through `sound-cues.js` with his notes in `note`, re-run the checks below, then `review.close_sound(project, done=[ids], not_done={id: "why"})`. Claude cannot hear, so say what changed and let him listen again. When he says the sound is good, start the final: `python tools/beat_review/autofinal.py start $P` (section 10). It does nothing twice, so it's safe if his click already started it. Sound fixes before that cost no extra final.

`check-sheet` covers palette, special requests, rotation, source share, spacing, events, CTA/proof spans and picture revision. `check-mix` requires 10-26 LU under the voice; over 8 cues per 30 s is a WARN: it "just has to make sense". `stale` lists cues that need review, including moved events. `cues: []` needs `empty_reason`. Sound comes before section 10, because the final freezes `sound.json` with the picture. A sound-only note revises `sound.json` through `sound-cues.js` and costs no render of the review picture. After a final, run section 10's `build` again with the new sheet (`final-by-hand.md`, "A new sound sheet after a final").

## 10. Final

The final is built fresh from a frozen copy of the approved composition, never from the review picture. `build` refuses without an approval record in `beat/approvals/`. Long job: never two renders at once (`tools/gpu_lock.py` queues them).

**`autofinal.py` does all of this by itself** from his Approve click, or from `python tools/beat_review/autofinal.py start $P` once the sound is good. It writes the swap file (shown in `final-by-hand.md`) with his click as `authorized_by`, builds 4K30 under `gpu_lock` (1080p30 when there is no `assets/face_half_4k.mp4`), delivers `out/<id>_<style>_final_4k30.mp4`, and runs `check-media`. The player shows each stage, and `work/<id>/final-<sha16>.log` has the output. On an error, read the log, fix it, and run `start` again. The commands it runs, for doing it by hand, are in `final-by-hand.md`.

**4K30 is the default final.** 1080p30 is the fallback if a 4K check fails, or if he asks for it; 4K60 only if he asks for 60 fps. All three by hand: `final-by-hand.md`.

Send him a phone copy of the sounded file and wait for final approval. Sound quality and stressed-word masking stay UNVERIFIED until Chase listens.
