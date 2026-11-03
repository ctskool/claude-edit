# Beat review: rounds and the approval check

`review.py` is what the player and a note round call. `project` is always a path to `v2/editorial`. Plan: `reports/2026-10-31-moves-plan-page/PLAN-V2-BEAT-REVIEW.md`, Workstream D. Results: `stage1/phase3-rounds.md`.

## A note round

```python
import review
frozen = review.freeze(project)        # the one set for this round. The first freeze also snapshots round 0
# make the edits in real sources, run tools_local/build.py, then run.py change
review.close_round(project, done=[ids], not_done={id: why})   # snapshots this round. Refuses if the project is not the newest picture
```

A word changed in a graphic must change `beats.json` copy, `owners.py` and `plan.json` too, or the build or the source check stops it. That is correct.

| Call | What it does |
|---|---|
| `state(project)` | Everything the player shows. Reads only |
| `add_note(project, {text, frame, scope, picture_sha})` | Appends to `notes.jsonl`, bound to that picture. 12 ms measured. The still comes from a background ffmpeg, decoded by frame number |
| `freeze(project, adopt=())` | Open notes on the newest picture, plus any an earlier round left undone. Older or undone notes come back as `flagged`. After Chase asks to apply specific flagged ids, `freeze(project, adopt=[ids])` includes them under their original ids. A resumed freeze after rendering returns the existing set |
| `close_round(project, done, not_done)` | Round number, parent, changed beats. `done` is the frozen ids this round did, `not_done` maps the rest to why. A frozen note in neither stays open too |
| `drop_note(project, id)` | Chase's click only. No round owes it any more. It stays in `notes.jsonl` |
| `go_back(project, n)` | Restores sources, plan, lock, map and the picture. After it, `run.py change` renders 0 and stitches the same file. What was here stays in `rounds/left-*.json` |
| `waive(project, finding_id, why)` | Chase's click only. Findings with no frames cannot be waived |
| `approve(project, picture_sha)` | Starts the check in its own process. Refuses an open note |
| `approval_status(project)` | `none`, `running`, `reconcile`, `blocked`, `error`, `failed` or `approved` |
| `reconcile(project, picture_sha, why)` | Chase's click only, on regions the method could not call. Refuses an open note |
| `native_beat(project, beat_id)` | One beat at the final profile, in `work/<id>/beat-native`. No sound. Waits for the render |
| `sound_view(project)` | `sound.json` cues at `t`, file-stem names, linear gain converted to dB, full sheet/media identity, and stale revision/event markers. Missing sheet returns no cues |
| `sound_notes(project)` | All open sound notes, including older pictures and sheets |
| `close_sound(project, done=[ids], not_done={id: why})` | Records only named open sound-note outcomes in `sound_rounds.json`. An omitted note stays open unchanged. An undone note stays open with its reason. No picture round or snapshot |
| `sound_preview(project, picture_sha, sheet_identity)` | Builds or reuses a listening derivative using `sound_mix.mix` for voice plus cues and ffmpeg video stream copy. The server calls this in a background thread |

## Where things live

```
work/<id>/
  notes.jsonl  waivers.json  dropped_notes.json     beside fixture.json. A new file in v2/editorial stales the build
  sound_rounds.json           sound-note outcomes, independent of the picture head
  beat/rounds/NNNN.json         one round: manifest of every file, the picture's entry, its notes
  beat/rounds/blobs/<sha256>    file bytes, real copies, shared between rounds
  beat/stills/<file16>/N.jpg
  beat/sound-preview/<picture16>-<sound-identity16>.mp4  listening only; never a picture entry
  beat/approvals/<file16>.json  the record, written once
  beat/approvals/active.json    which picture is approved now. Any picture change clears it
  beat/approvals/regions-<file16>/  crops: approved, fresh, difference at 4x
  beat-fresh/<file16>/          the fresh render's file and checks. Its segments are removed after
  beat-native/                  native beats
```

## A note's state

A note closes only because a round named it in `done`, or Chase dropped it, and only while that round is on the head's line. After `go_back`, what later rounds did reads `undone`, and is flagged, not offered. What a round left undone stays open on every later picture and holds approval. A new note on the approved picture clears the approval. The record stands, so approving again costs no render. A note during the check stops it at the end: `reconcile` refuses, and a clean check writes its record without approving.

Frozen notes stay open when a new picture arrives, until a round answers them. Closing a round with any open note clears approval. A nonempty `done` or `not_done` without a frozen set is refused, even if the picture has not changed.

### Sound in the player

The Sound tab follows Rounds. Each cue shows its time, short name, event, gain in dB and any stale marker, using the same revision and event comparisons as `sound_mix.stale`. The lane directly below the beat strip seeks to `round(t * fps)`; crowded names become ticks with titles. A missing sheet says cues arrive after picture approval. A zero gain displays −∞ dB.

Sound (or **S**) toggles voice only / with cues. The first request shows building progress; failures show the reason and allow retry. Switching preserves position and play/pause. “Listening preview” identifies the sounded media. The preview uses the exact picture's compressed video stream, without a video encode or frame-count change, and audio from the final's own `sound_mix.mix` code. A sheet or cue-byte change selects another file. No mastering or final approval is implied by listening here.

`loaded`, note `picture_sha`, approve, reconcile and all picture checks always refer to the real picture. A preview never enters `current.json`, `last_attempt.json`, stitched pictures, changes, picture rounds, final builds or delivery. It lives only under `beat/sound-preview/`. Inputs that move during a build refuse publication. The dark theme is the default; the appearance select and offline font fallbacks still work.

A cue's Note button opens scope `sound`. N or Note with Sound selected chooses the nearest cue to the playhead (earlier sheet row wins ties). Shift N remains Whole video. Sound notes pin frame/time, zero-based `cue_index`, `cue_time`, `cue_name`, real `picture_sha` and full `sheet_identity` (the canonical hash of `sound_mix.sound_identity`, including cue bytes). They use the same `notes.jsonl` and Chase-only Drop action as picture notes. They never clear or hold picture approval, enter freeze's `notes` or `flagged`, or count in `close_round`. They do not block final or delivery. Older-picture and older-sheet notes remain open and labelled, including when left `not_done`. Old frame/video JSONL rows need no migration. Sound outcomes persist independently of picture go-back.

### Player HTTP API

All routes are local. Media supports byte ranges. Existing picture routes and click-origin requirements are unchanged.

| Route | Request / response |
|---|---|
| `GET /api/state` | Existing state plus `sound: {present, identity, cues, stale?, error?}` and `sound_preview: null` or the current job (`running`, `done` with URL, or `failed` with error). Cues include `index`, `name`, `gain_db`, `stale` and the original sheet fields |
| `POST /api/sound-preview` | `{picture_sha, sheet_identity}` for the newest picture/current sheet. Starts or reuses a background listening job; does no work on the request thread. A failed job may be retried |
| `GET /media/sound-preview/<picture16>-<identity16>.mp4` | Serves a completed listening job only, never arbitrary paths |
| `POST /api/notes` | Existing `{text, frame, scope, picture_sha}` plus `cue_index` and `sheet_identity` for `scope: "sound"`. Cue time/name are taken from the identified sheet by the server. A changed sheet refuses the note |
| `POST /api/sound/close` | `{done: [ids], not_done: {id: "why"}}`, equivalent to `close_sound`. Refuses unknown, picture, closed or simultaneously done/undone ids and blank reasons |
| `POST /api/drop_note` | `{id}`, including a sound note; requires the page's own Origin |

Tests: `python tools/tests/test_beat_sound.py` uses temporary projects, real ffmpeg media, Chrome when available, and a final/delivery integration. For manual testing, use a copy of the fixture on `PORT=4745`; do not use the approved project or its live server.

## Waivers

`tools/beat_check/output.py` reads `waivers.json` and the rows of `fixture.json` that name frames. A waiver names a check, its exact frames and why. A waived finding no longer fails its check and is listed under `waived` in every report. One from `waive` also names the segments its frames sit in, so an edit to those beats brings the finding back. O4 waivers also name composition and profile, so they hold for a final of that exact composition on the same frames when only the profile changes. A 4K60 derivative is a new composition and frame grid; the review waiver cannot clear a finding there. `final.py` freezes both waiver files into the bundle by hash.

Waivable: `O4.flash`, `O4.double_cut`, `O5.sample`, `O5.clip`, and any `source.*` finding with a frame. `state` honours a click at once, and the output check applies both sample and clip waivers. A clicked sample waiver belongs to the exact rendered file; matching composition or segment keys never carries it to another render. All flash rows are retained, including those past the first twelve. `conform.py` does not read waivers, so a waived source FAIL leaves the picture in `last_attempt.json`, and it can still be approved. Not waivable: `binding`, `O1`, `O2`, `O3`, join problems, `O6`, and anything with no frames.

After a final freezes, changed review waiver files select a new immutable bundle revision on the next `final.py build`, sharing the existing picture segments. No code writes a waiver for Chase: only his player click does. Final-only findings still have no click route; they must be fixed or brought to Chase as an unresolved workflow decision.

Sound identity is `sound.json` plus the hash of every cue file it names. A sound revision copies those cue files, replacing links before writing, and leaves the earlier bundle intact. Missing sheets or cues refuse, and delivery checks both the project's identity against its bundle and the frozen inputs during delivery. The revision suffix hashes that identity and the home waiver hashes, not just the sheet.

## The approval check

```
python tools/beat_review/approval.py check <project> --picture <sha256>     what approve starts
python tools/beat_review/approval.py compare <a.mp4> <b.mp4> --out rows.json
python tools/beat_review/qualify_approval.py plant <copy's v2/editorial>     test only
python tools/beat_review/qualify_approval.py measure ...                     writes the limits
```

Every beat renders fresh at the complete review profile, in a store of its own, through `run.py draft --store`. The fresh file is compared to the approved one, every frame, paired by decoded frame number. Three measures decide: worst 48 px luma window, worst 24 px luma window and worst 48 px chroma window, all sliding. PSNR is reported and never decides.

Three zones, from `stage1/phase3-approval-qualification.json`: under `pass_under` passes, over `fail_over` is a real difference and stops, and between them the regions go to Chase. With no qualification, or if noise and defects overlapped, nothing passes by itself. `qualify_approval.py widen` adds comparisons to that evidence and sets the limits again, by the same rule and the same check against the plants. New approval comparisons record the fresh file hash, store and whether `--reuse-fresh` was used. Widen preserves that provenance and labels older comparisons without it as unknown, never automatically as another whole fresh render.

A `FAIL` record is written once, so that file cannot be approved. To repair a wrong cache, re-render the beats its regions name, then stitch, which makes a new file:

```
python tools/beat_render/run.py draft <project> --profile review --force --only b16,b38
python tools/beat_render/run.py stitch <project> --profile review
```

Tests: `python tools/tests/test_beat_review.py`.
