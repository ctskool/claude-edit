# Charcoal build kit: reference

`templates/charcoal/CARD.md` is the page a builder works from: the rules, the flow, the commands. This file says what each script in the kit does and what is worth knowing about it. Read a section here when the card does not answer the question.

HyperFrames stays 0.9.13. Every Python and `capture_docs.mjs` line runs from the project root; every `node tools/...` and `npx hyperframes` line runs from `work/<id>/full`.

## What is in the kit

| File | Does |
|---|---|
| `new_project.py` | Scaffolds `work/<id>/full` from the spine's output; `--check-face`; `--refresh-media` after a re-cut |
| `tools/kit.mjs`, `tools/build.mjs` | The look, the scene helpers, the build. Copied into each project |
| `tools/local.mjs` | Empty: a project's own one-off helpers go in its copy |
| `tools/make_clips.py` | Cuts the clips designed scenes show (`clipTag`). The renderers run it |
| `capture_docs.mjs` | Real docs-page captures with measured sentences |
| `storyboard.py` | The stills storyboard he approves graphics from |
| `render_slices.py` | The renderer: slices on the GPU, joined by stream copy |
| `render_slices_x264.py` | The same in software. For a machine with no NVIDIA card, and for projects with x264 slices already rendered (`work/1110-slop`'s final) |
| `facewin_assets.mjs` | Draws the face window's ring and mask stills the renderers lay on with ffmpeg |
| `face_track.py` | Builds `assets/face.mp4` on the GPU and repairs it by splice |
| `to_player.py` | Loads a render into the review player |
| `examples/` | Two approved section files from 1109-fable (another video's facts: read, never copy) |

## new_project.py

The spine has run (`templates/story.md`), so `work/<id>/raw` holds `cut.mp4`, `cut_words.json`, `edl.json`, `edit.txt` and, with a clean CAMERA file, `cam_cut.mp4`.

```bash
python templates/charcoal/build_kit/new_project.py <id> --check-face --crop W:H:X:Y
python templates/charcoal/build_kit/new_project.py <id> --crop W:H:X:Y --series step:4 [--docs-site platform.claude.com/docs]
```

- `--check-face` writes `work/<id>/face-check.jpg`, the window as the video will show it, and stops. Black in the corners means the camera file has a mask baked in, and the crop cannot go wider than that mask; say so to Chase before building. The crop is a 4:5 rectangle of his real pixels: `1440:1800:1200:173` on 1109-fable (masked camera), `1728:2160:1056:0` on 1110-slop (clean camera, full height).
- The real run makes `work/<id>/full`: a copy of `tools/`, `hyperframes.json`, `package.json`, the fonts, `assets/face.mp4` (960x1200, 30 fps), `assets/voice.m4a` (the cut's audio, copied), `assets/words.json`, and `tools/video.json`, this video's settings. A ten-minute face clip takes a few minutes. It refuses to run on a project that already exists.
- `--series label:count` feeds `ruleTitle`'s kicker (`// step 02 of 4`).
- `--quick` [Chase, 2026-11-13] is the first run for a video whose cut he is still listening to: it needs only `cut_words.json` and `edl.json` (no rendered picture), takes about half a minute (a stand-in voice track is encoded from `edit.wav`), and leaves out the face track. Sections can be written and built at once. `--refresh-media` then makes the face track when `raw/cut.mp4` exists (no `--keep` needed the first time), and again with `--keep draft` on his approved cut.
- The face track is built on the GPU (`face_track.build_base`) when NVENC is there: 2 min 48 s for a 12.5-minute cut, against about 7 in software. The file is larger (1.0 GB against 0.3). Without NVENC, or if the GPU route fails, it falls back to x264 by itself.
- `joins_check.py work/<id>` (after a full build) lists every BIG join no scene change covers and exits 1 if there is one. `tools/cuecheck.mjs` (from `full/`) checks every `cue()` and `at()` phrase in the sections against the cut's words and prints the words near a miss.
- `video.json` `face.ring` (optional) is the face window's box-shadow, for a video with its own look (1113-nod: a pink edge). The build, the slice keys and both renderers read it; the default is unchanged.

## Captures

```bash
node templates/charcoal/build_kit/capture_docs.mjs work/<id>            # every pull in work/<id>/pulls.json
node templates/charcoal/build_kit/capture_docs.mjs work/<id> r03-half   # only these ids
```

Each pull gets the article column at 3x with every sentence's line boxes, and the lifted excerpt at 5x for the 4K final. A sentence the page does not have is reported MISSING and the run exits 1: fix `pulls.json`. Proven on platform.claude.com/docs only. Other pages (a site he shows, a local page) were captured per video so far; stills of his own screen are frames of `raw/cut.mp4`.

## The build

```bash
node tools/build.mjs --sections=00,01     # while working on a part
node tools/build.mjs --partial            # a pilot: the sections written so far
node tools/build.mjs                      # the whole video: stops on a gap, an overlap, or a last scene that misses the cut's end
npx hyperframes check --json > check.json
npx hyperframes snapshot --at 12.5,31
```

A full build writes, besides the page: `tools/sections.json` (the chapters), `tools/slices.json` (one slice per scene: `key`, `frame0`, `frames`, and `ff` for a footage slice or `pg` for a designed one), `tools/clips.json` and `faces.json`. `--range=a,b`, `--reel=id,id` and `--no-voice` are what the renderer calls; you do not.

One frame rule everywhere: a scene that starts at t is first seen on frame ceil(t x 30).

A slice's key is made from its scene page, the window place it uses (by value), its length, `video.json` `media_rev` and `STAGE_REV` in `build.mjs`. Bump `media_rev` when the footage under existing scenes changed; bump `STAGE_REV` only when `build.mjs` changes what every frame looks like.

## storyboard.py

```bash
python templates/charcoal/build_kit/storyboard.py work/<id> --name storyboard-v1
```

Reads `work/<id>/storyboard/storyboard-v1.json` (format at the top of the script: per row a title, the seconds to take stills at, what he says, what is on screen, which words are not his) and writes one self-contained `storyboard-v1.html`. The stills are snapshots of the built page, not a render, so a row costs seconds. Number the rows; he answers by number.

## render_slices.py

```bash
python templates/charcoal/build_kit/render_slices.py work/<id> --rev v1                  # 1080p review render
python templates/charcoal/build_kit/render_slices.py work/<id> --rev pilot --partial     # only the first sections exist
python templates/charcoal/build_kit/render_slices.py work/<id> --rev final --res 4k
```

- It runs a full build, cuts any clips designed scenes need, renders every slice whose key has no file in `work/<id>/slices/nv-1080` (or `nv-4k`), and joins all slices by stream copy under the voice into `work/<id>/out/<id>-<rev>.mp4`, with `-chapters.txt` beside it.
- Three routes. **Footage** (his camera or screen, window still): decoded and encoded on the GPU, no browser. A footage slice with a `card` (`cardFootage` in `kit.mjs`) is the same route with one more layer: `card_assets.mjs` draws the scene's page and the card's rounded mask once (`slices/_cards`), and ffmpeg lays his cropped footage into the card and the face window on top. **Reel**: every designed slice whose window does not move, rendered back to back in one HyperFrames call without the window, then cut per slice by ffmpeg, which lays the window on. **Page**: a slice whose window moves or fades during it, through the browser whole.
- Measured on a copy of 1110-slop (16:18, 62 slices, 2026-11-11): everything from nothing in 5 min at 1080p and under 9 min at 4K; one changed graphic 46 s. `reports/2026-11-11-render-speed/part-2-gpu.md` has the method and the encoder choices. Do not edit the ffmpeg or NVENC arguments: every slice must carry the same header or the join breaks.
- **Kept browser renders** [Chase, 2026-11-20]. Each reel's browser render is kept in `slices/nv-<res>/reels/` and indexed in `pages.json` by the scene's `pkey` (its page and length only: no face window, no `media_rev` unless the scene shows clips of the cut). A designed slice whose full key is new but whose page is kept skips the browser: ffmpeg cuts it from the kept reel and lays the window on ("from kept browser renders" in the first line). So a re-cut, a moved window or a new ring re-renders only the scenes whose page changed. Proven on a copy of 1119-neon: `media_rev` raised, the whole video rendered again in 134 s instead of 771 s, every frame identical. Kept reels no scene of the current build uses are deleted at the end of a full run (a 4K reel is several GB).
- **Render the draft during his cut listen.** Once the scenes are written on the draft and the draft's face track exists (`--refresh-media`), run `render_slices.py work/<id> --rev draft` in the background at full priority. After his approval (`--refresh-media --keep draft`, build), the first review render draws only the scenes his cut changed. Never shown to him: the draft render only fills the cache.
- `--dry` lists what would render. `--background` only when he says he is recording (never by default, [Chase] 2026-11-20): idle priority and one ffmpeg job (a normal render cost a 60 fps capture 13% of its frames). `--no-reel` renders designed slices one by one. `--no-gpu-decode` forces software decode.
- It takes `tools/gpu_lock.py` (a second render or a transcription waits its turn) and starts `tools/qos_watch.py` (Windows otherwise parks Chrome's workers on the efficiency cores, 2-3x slower).
- A GPU decode that stalls is killed after 25 s and the slice is built with software decode; the output format is the same.
- **Never write a file under `full/assets` in place while it runs.** Its working copy (`work/<id>/w1`) hard-links them. Write `x.new`, then replace, after the render.

`render_slices_x264.py` takes the same `--rev`, `--res`, `--dry`; its slices live in `slices/1080` and `slices/4k` and do not join with the GPU ones.

## to_player.py

```bash
python templates/charcoal/build_kit/to_player.py work/<id> work/<id>/out/<id>-v1.mp4 --rev v1 [--until 128.72]
```

Then serve `work/<id>/v2/editorial` with `tools/beat_review_v2/server.py` (a `.claude/launch.json` entry with its own port, like `beat-review-v2-1110-slop`) and open `http://localhost:<port>/?skin=wide`. With `full/tools/segments.json` present the player shows one beat per segment; `--sentences` gives one per sentence. He pauses, presses N and types; notes land in `work/<id>/notes.jsonl`, bound to the word under the playhead. This load is a stand-in: Approve is off, and his approval is taken in chat.

## face_track.py and timing repairs

- `face_track.py base` builds the face track once per cut on the GPU (`assets/face.cut.mp4`, about 3 min for 16 min). `splice` makes `assets/face.mp4` from it and a list of repairs in seconds: whole seconds the repairs do not touch are copied, the rest is encoded again from the camera footage itself.
- A repair after the build (frames put back or trimmed at a join) must change `assets/face.mp4`, `voice.m4a`, `words.json`, add a row to `tools/retime.json` (`[atSecond, addedSeconds]` on the timeline the sections were written against, in whole frames) and the same in `tools/holds.json` in `raw/cut.mp4` times. This is still a per-video script: `work/1110-slop/tools/apply_pauses.py` is the one to start from, with its face block replaced by:

```python
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "templates" / "charcoal" / "build_kit"))
import face_track
base = A / "face.cut.mp4"
if not base.exists() or "--rebuild-face" in sys.argv:
    face_track.build_base("../raw/cam_cut.mp4", crop, base)
face_track.splice(base, "../raw/cam_cut.mp4", crop, [dict(at=o["at"], n=o["n"], src=o.get("src"), cam=CAM) for o in OPS], A / "face.mp4")
```

- Known gap: the splice's put-back frames have been checked against the base track, not yet against the recording. The old full rebuild in that script shows the camera 1/60 s late on every third frame.
- A re-cut instead (`rawcut.py cut`, `verify`, `render`): `new_project.py <id> --refresh-media --keep <label>` re-makes face, voice and words and keeps the old ones. With `tools/cut0.json` in the project (written by a first run since 2026-11-12) it also writes `retime.json` from the two cuts and raises `media_rev`; without it, add the `retime.json` row and bump `media_rev` by hand. The same command brings a project started on the cut review page's draft onto his approved cut. A new cut loses any repairs made by script.

## Final

```bash
python templates/charcoal/build_kit/render_slices.py work/<id> --rev final --res 4k
```

**Draw the 4K slices during his review** [Chase, 2026-11-20: "we should always do that"]. As soon as a review version is in the player, start `render_slices.py work/<id> --rev 4k-<rev> --res 4k` in the background at full priority. Slices are cached by key, so:
- a scene he leaves alone is drawn at 4K once and re-used by the final;
- a scene he changes gets a new key; only its 4K drawing is wasted;
- a note round comes first: if the 4K run still holds `gpu_lock` when his notes are ready, stop it, render his review version, then start the 4K run again (it skips every slice already in `slices/nv-4k`);
- on his approval, run the command below: it draws only what changed since the last 4K pass and joins. The `4k-<rev>` file is never sent; delete it after the final.
Why: 1119-neon's final drew 25,000 designed frames at 4K in the browser, 31 min after his approval (browser capture 1,708 s of 1,831 s).

The same page at twice the density, 3840x2160 at 30 fps. Before sending: the joined frame count matches, `ffmpeg -v error -i <file> -f null -` decodes the whole file with no output, and a frame from every chapter has been looked at. Any image shown larger than its source needs a denser source first, or it is soft at 4K.

## Proven, and not

- 2026-11-09, on a throwaway project holding 1109-fable's 13 sections: all 72 scene files, `index.html` and `faces.json` byte for byte the same as that video's own build; `face.mp4` frame-identical; `capture_docs.mjs` re-captured two pulls with identical geometry; `--check-face` showed the circle mask and refused a crop that is not 4:5.
- 2026-11-11, on `work/kit-proof` (scaffolded from this kit, holding 1110-slop's sections and media, its one video-only helper moved to `tools/local.mjs`): all 62 scene pages, `index.html`, `faces.json`, `sections.json` and all 62 slice keys identical to the approved video's. One footage slice and two designed slices rendered through `render_slices.py`: the footage slice bit-identical to the earlier GPU render, the designed ones at 49 dB; joined to 29,359 frames. `--partial` with only the intro present: the plain build refused, the pilot joined 3,472 frames. `storyboard.py` wrote a page from a two-row file and took its own stills.
- The GPU route's 4K output against the approved 4K final, ten designed slices at full size: same picture (face box, ring, shadow, text).

- 2026-11-13, on `work/kit-check-1113` (1113-nod's approved cut and sections, on the kit's own `at()`, `joinNear()`, `cardPage()` and `cardFootage()`): `--quick` with no rendered picture in 33 s; build, `cuecheck.mjs` and `joins_check.py` clean with all 72 scenes on the same frames as the delivered video; `--refresh-media` made the first face track on the GPU in 2 min 48 s (22,621 frames); a full 1080p render from nothing in 193 s, and every one of its 22,621 frames against the delivered v3: 57.2 dB average, 50.8 dB lowest. 1113-nod itself was the first video started from this kit and the first final delivered by the GPU route (4K, 287 s), with the card route.

Never yet: `--quick` during a real cut listen; a draft render re-used after a real cut approval; `--refresh-media --keep draft` after he moves joins on a quick project; the card route in `render_slices_x264.py` (it does not have it); a card over the charcoal stage (the ASCII strip drifts, so the page is not a still); a real final delivered by the GPU route; `--refresh-media` on a real changed cut; a page other than platform.claude.com/docs through `capture_docs.mjs`; sound; the splice's put-back frames against the recording; a render beside a real OBS recording; a designed scene that shows a clip (`clipTag`) rendered at 4K through the reel.
