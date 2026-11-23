# Charcoal, one page (long-form)

What one builder needs to plan, build and render a 16:9 YouTube video in charcoal. Numbers are at 1920x1080; the final is the same page at twice the density (3840x2160, 30 fps). Chase wins every conflict. `TEMPLATE.md` (the look and its open decisions) and `sections.md` (how a scene is written) stay the source; open one when this page does not answer the question.

Every Python line runs from the project root. Every `node tools/...` and `npx hyperframes` line runs from `work/<id>/full`. HyperFrames stays 0.9.13.

## Hard rules (Chase)

1. **Real footage only.** Crop, scale and cut his real pixels. Nothing generated, stretched or extended.
2. **The base is his face and his screen.** [Chase, 2026-11-11: "a lot of this should just be like my face and then the screen"] Two shots with hard cuts: his camera full frame when he talks, his screen full frame with his face in a corner when he shows something.
3. **No face-only stretch over about 12 s without a reason.** [Chase: "people want to see something"] A sentence or two to camera for emphasis is fine. Plan a graphic per idea for the rest.
4. **Never put text over his full-frame face.** [Chase: "That looks terrible"]
5. **No dead space.** [Chase: "so much dead space"] No floating card on an empty stage. No slow push on a screen recording while nothing else changes; a zoom or a soft transition is fine when it has a reason.
6. **A graphic shows something real.** His own screen, a capture, a still of the thing he names. A panel that only repeats his sentence is banned. If his take shows a shot list or a script on screen, build to it.
7. **Verified facts only.** Every figure and quote on screen is in `work/<id>/facts.json` with a source, or in a capture. On-screen words that are not his are listed for him at the storyboard.
8. **No label on his face, no banner, no brand bar, no emoji.** Readable first: headlines 84 px or more, nothing under 24 px.
9. **Images through `codex exec` only**, unless he names another image tool.
10. **He hears the cut before graphics exist, and sees stills before anything renders.** A note should cost him minutes.
11. **The first 30 seconds get the most effort.** [Chase, 2026-11-16: "This first like 30 seconds really needs to kind of like hit them and wow them"; 2026-11-18: the same idea as a short's hook] The opening decides whether a viewer stays, so it is designed graphics that sell what is coming, not b-roll of his screen, and it is the place to be inventive. There is no recipe for it on purpose. So far: very large clean type, one counting number and a table that clears for one figure landed; stamp words and tilted or thrown cut-outs read as corny.

## The flow, and where he is asked

| # | Step | Stop |
|---|---|---|
| 1 | **Intake.** Before the real take, a 10-second test of both files and `new_project.py <id> --check-face --crop W:H:X:Y`: the camera file must be a clean, unmasked shot | Show him `face-check.jpg` |
| 2 | **Cut** (`templates/story.md`, unchanged). Read every RUN-ON line. Then scan every short gap the cut removed for speech-level sound with no word label: that is a dropped word the aligner mislabelled | **He listens in the cut review page (`tools/cut_review`), moves joins by ear and approves; Approve renders `cut.mp4` and `cam_cut.mp4`.** **Rows 3 to 5 are done while he listens** [Chase, 2026-11-12 and 2026-11-13]: the scenes need only the script, so start them the moment the page opens, not when the draft is rendered (`story.md` step 8 has the order) |
| 3 | **Project.** `new_project.py <id> --quick --crop W:H:X:Y --series step:4` as soon as `rawcut.py cut` has run: about half a minute, no face track, and the sections can be written and built. It writes `tools/cut0.json` (the cut the sections are written against). When the draft is rendered: `new_project.py <id> --refresh-media` makes the face track (GPU, about 3 min) for the stills. Then, still during his listen, `render_slices.py work/<id> --rev draft` in the background: it fills the kept browser renders, so his first review render only draws the scenes his cut changed (`build_kit/README.md` "render_slices.py"). After his approval and the render: `new_project.py <id> --refresh-media --keep draft` re-makes the media, writes `tools/retime.json` from what he moved and raises `media_rev`; then `node tools/build.mjs`. Scene times stay as written; a cue on words he cut stops the build and names the phrase | |
| 4 | **Facts and captures.** `facts.json`; `pulls.json` + `capture_docs.mjs` for docs pages; stills of his own screen are frames of `raw/cut.mp4` | |
| 5 | **Plan.** `full/tools/segments.json`: the video as named segments, one idea each, 10 to 40 s. Per segment: face, screen, or a graphic. Write the graphic scenes, build, then `storyboard.py` | **He approves the storyboard by number** |
| 6 | **Pilot.** The intro and first chapter, rendered and in the player first [Chase agreed] | His notes |
| 7 | **The rest**, one section file per chapter | |
| 8 | **Review render** (about 5 min for 16 min of video), player, notes. Change only what he noted; only the slices a note touched render again (under a minute for one graphic) | His notes, by segment |
| 9 | **Final** after his approval in chat: `--res 4k`. Its slices are drawn during his review (see `build_kit/README.md` "Final"), so approval to file is the changed slices plus the join. Frame count, a full decode, a frame from every chapter | Offer the louder copy (about -14 LUFS) beside the original |

## Commands

```bash
python templates/charcoal/build_kit/new_project.py <id> --check-face --crop W:H:X:Y
python templates/charcoal/build_kit/new_project.py <id> --quick --crop W:H:X:Y --series step:4   # while he listens: no face track yet
python templates/charcoal/build_kit/new_project.py <id> --refresh-media [--keep draft]           # the face track; --keep after his approval
node tools/cuecheck.mjs                    # every cue() and at() phrase against the cut's words
python templates/charcoal/build_kit/joins_check.py work/<id>   # every BIG join on a scene change
node tools/build.mjs --sections=00,01          # while writing; --partial while later sections are missing
npx hyperframes snapshot --at 12.5,31          # look at every scene you wrote, mid-reveal and revealed
python templates/charcoal/build_kit/storyboard.py work/<id> --name storyboard-v1
python templates/charcoal/build_kit/render_slices.py work/<id> --rev pilot --partial
python templates/charcoal/build_kit/render_slices.py work/<id> --rev v1 [--dry] [--background]
python templates/charcoal/build_kit/to_player.py work/<id> work/<id>/out/<id>-v1.mp4 --rev v1 [--until <s>]
python templates/charcoal/build_kit/render_slices.py work/<id> --rev final --res 4k
```

Player: serve `work/<id>/v2/editorial` with `tools/beat_review_v2/server.py` (a `.claude/launch.json` entry with its own port) and open `/?skin=wide`. One beat per segment. Approve is off for long-form: his approval is taken in chat.

## What you write

| File | What it is |
|---|---|
| `work/<id>/facts.json`, `pulls.json` | Figures with sources; pages to capture |
| `full/tools/sections/NN-name.mjs` | The scenes of one chapter, with `export const title` (the YouTube chapter name) |
| `full/tools/segments.json` | `[[start, "name"], ...]`, starts on sentence starts of `raw/edit.txt` |
| `work/<id>/storyboard/<name>.json` | The storyboard's rows (format at the top of `storyboard.py`) |
| `full/tools/local.mjs` | A helper only this video needs. Never edit `kit.mjs` or `build.mjs` for one video |
| `work/<id>/RUN.md` | What was decided, his words, what is not his wording |

Generated, never edited: `index.html`, `compositions/`, `faces.json`, `tools/sections.json`, `tools/slices.json`, `tools/clips.json`.

## The scene kit (`full/tools/kit.mjs`)

| Helper | Gives |
|---|---|
| `shots(prefix, end, [[start, "face"], [start, "screen", {face: "pip", crop}], [start, "skip"], ...])` | The base: tiles a stretch with his camera full frame and his screen full frame, hard cuts, and sets the face window for each. `"skip"` leaves a stretch for a graphic scene. Long shots are divided into slices of 22 s at most |
| `fullFace(id, a, b)`, `screenFull(id, a, b, {crop})` | One base shot by hand |
| `scene(id, a, b, {wrap, css, html, tl})` + `face(t, place, dur)` | A designed scene and where the window is. `dur` 0 is a hard cut |
| `screenCard`, `clipTag` | His real screen in a card, or any piece of the cut's footage inside a scene |
| `ruleTitle`, `docs`, `promptCard`, `selector`, the timeline helpers | Chapter card, real docs pull, prompt card, small diagrams (`sections.md`) |

Face window places (x, y, size): `pip` 1512, 582, 360x450 (bottom right, the default over a screen); `pipL` 48, 582 (bottom left); `pipT` 1512, 48 (top right); `right` 1344, 206, 480x600 and `left` 96, 206 (beside a designed scene); `corner` 1566, 538, 258x322; `stag` 1400, 372, 472x590 (large and raised, overlapping a footage card's right edge); `"off"` for full-frame face.

- Every reveal lands on a spoken phrase through `cue("...")`. Every BIG join sits on a scene change within 0.3 s.
- **A scene starts on the join, not on the word** [Chase, 2026-11-13]: write boundaries with `at("phrase", after)`. `joins_check.py` lists any scene that starts a few frames after a join.
- Stills for a graphic go in `full/assets/stills/`. Any image shown larger than its source needs a denser source, or it is soft at 4K.
- A scene that shows his footage inside a graphic uses `clipTag`; the renderer cuts those clips itself.

## Rendering

- **A slice is one scene.** `slices.json` gives each a key from its page, the window place, its length and `video.json` `media_rev`. A slice with a matching file in `work/<id>/slices/nv-1080` or `nv-4k` is re-used, so a timing change earlier in the video re-renders nothing after it. Bump `media_rev` after a re-cut that changes the footage under existing scenes.
- Footage slices never open a browser (GPU decode and encode). **So does a still layout with his footage in it** (`cardPage` + `cardFootage`, `sections.md`): the page is drawn once, the GPU does the rest. On 1113-nod that took the app beats from about 6 min to 1. Every designed slice renders in one HyperFrames call, without the face window; ffmpeg lays the window on. A slice whose window moves during it goes through the browser whole.
- The renderer takes `tools/gpu_lock.py`, so a second render waits. **Full priority by default. `--background` only when he says he is recording** [Chase, 2026-11-20: "I will tell you if I'm recording ... If I don't tell you that, it should never be low priority"]; never tell him recording is safe during a normal render.
- **Never write a file under `full/assets` in place while a render runs.** The render's copy hard-links them.
- No NVIDIA card, or an older project with x264 slices already rendered: `render_slices_x264.py` (same options, `slices/1080` and `4k`; the two stores do not join).

## A timing note after the build

- First, when he reports a rushed join, a stutter or a missing word: measure the source audio in the gap the cut removed at that join (`raw/edl.json` keeps against the source). Restore real footage if it is there. Do not make a pause from a frozen frame or muted sound.
- A change of whole frames at a join: the media (`assets/face.mp4`, `voice.m4a`, `words.json`) are repaired in place of a re-cut, `full/tools/retime.json` gets `[atSecond, addedSeconds]` so later scenes keep their written times, and `full/tools/holds.json` the same in `raw/cut.mp4` times. `build_kit/face_track.py` rebuilds the face track by splice in seconds. This is still a per-video script: start from `work/1110-slop/tools/apply_pauses.py`. A new `rawcut.py cut` loses these repairs.
- A re-cut (`rawcut.py cut`, `verify`, then `tools/cut_review/core.py <raw>` to carry the joins he set by ear, `render`, which re-uses the pieces that did not change): then `new_project.py <id> --refresh-media --keep <label>`. It writes `retime.json` itself when the project has `tools/cut0.json`; a project made before 2026-11-12 needs the row by hand.

## Where things belong

- The look and the helpers: this kit. A change the next video would want is made here, not only in the project's copy.
- One video's content and its one-off helpers: `work/<id>` (`local.mjs`, sections, `RUN.md`).
- A script written in a run folder that a second video would need moves into the kit or `tools/` before the run is closed.

## Proven, and not

Proven 2026-11-11 on `work/kit-proof`, a project scaffolded from this kit holding `work/1110-slop`'s sections and media: all 62 scene pages, `index.html` and all 62 slice keys identical to the approved video's; one footage slice and two designed slices rendered through `render_slices.py` (footage bit-identical to the earlier GPU render, designed slices 49 dB) and joined to 29,359 frames; the pilot path (`--partial`) joined the intro alone; `storyboard.py` took its own stills. The GPU route's 4K output was compared with the approved final at ten designed slices at full size: same picture.

Never yet: a video started from this kit (1110-slop was built first and the kit caught up); a real final delivered by the GPU route; the face-track splice's put-back frames checked against the recording; a render beside a real OBS recording; sound in long-form (asked once per video since 2026-11-22; his answer so far is no, so no cue path has been run).
