# Format library

The claude-edit skill has two menus:

- **Style** = the visual skin of the split-screen layout (`styles/`: `editorial` = menu name `ivory`).
- **Format** = the layout itself and what moves (this folder, `formats/`).

A format is one of the Creator Skill Pack's reel skills, imported from your own copy of the pack by
`python tools/import_formats.py <pack>/skills`, filled with your brand from `config/profile.json` and patched to run on
Windows and macOS. Every format reads the same prepped video (the contract below), so one recording can be rendered as
several kinds of edit and compared side by side.

| menu name | key | folder | what it looks like | how it runs |
|---|---|---|---|---|
| `rotation` | `business` | `business-short-form-reels/` | face full screen / split / full-screen animation rotation; glass pills, real interfaces | HyperFrames, reel engine |
| `popout` | `panel` | `explainer-panel-reel/` | you in a rounded panel at the bottom (head pops above it), headings + diagrams above | HyperFrames, its own 06_crops / 07_captions |
| `layers` | `depth` | `depth-ui-reel/` | full frame the whole time; real interfaces BEHIND your head (cut-out), cards on the chest | HyperFrames |
| `wrap` | `fitted` | `fitted-stacked-captions/` | caption layer: one big accent anchor word, the others fitted around its letters | headless Chrome + ffmpeg |
| `frost` | `glass` | `glass-explainer-reel/` | the panel layout with graphics on rectangular glass cards | HyperFrames |
| `evidence` | `essay` | `visual-essay-reel/` | dark frame, you cut out low (wide shot), an evidence wall of real posts / charts | HyperFrames |
| `scenes` | `backdrop` | `cutout-backdrop-reel/` | you cut out over one full-screen image per idea, hard cuts every 1.5-3 s | `cutout_reel.py` (PIL + ffmpeg) |
| `mosaic` | `grid` | `cutout-grid-reel/` | you cut out in the centre over a 2x2 image grid that changes together | `grid_reel.py` (PIL + ffmpeg) |
| `collage` | `cluster` | `image-cluster-reel/` | you low, 1-3 images above your head changing every 3-5 s, tiny captions | `cluster_reel.py` (headless Chrome + ffmpeg) |
| `tiers` | `ranking` | `ranking-format/` | tier list S-F; item cards pop when named and drop into their tier | HyperFrames, `rank_engine.py` from `plan.json` |

**Screenshots of the thing being talked about: yes, capture them.** When the video names a repo, skill, product page,
pricing page, blog post or doc, builders capture it live with `tools/capture_shots.py` (Playwright, DPR 2, light + dark,
element crops, per-shot box JSON) into `work/<id>/shared/shots/` and list the URL in ASSETS.md. The source is chosen per
asset (routing table in `.claude/skills/claude-edit/SKILL.md`, "Pick the source per asset").

**Other people's images (backdrop / grid / collage):** the pack's `fetch_images.py` scrapes image search. Do not use it
unless you decide that is fine for you; by default the image formats use your real assets only (page screenshots, logos,
stills/clips of your own recording) or images you supply.

## How to run one

```bash
python tools/formats.py media  <id>                 # once per video: shared media (cut-outs, crops, 16:9 camera cut)
python tools/formats.py new    <id> <format>        # scaffold work/<id>/formats/<format>/
# write work/<id>/formats/<format>/build.py with the format's engine (its SKILL.md + examples/) - the creative step,
# one builder agent per format briefed from formats/BUILDER_BRIEF.md
python tools/formats.py render <id> <format> --draft   # then without --draft for the final -> out/<id>_fmt-<format>.mp4
python tools/formats.py gallery <id>                # out/<id>-formats.html: every version side by side
```

Read the format's own `SKILL.md` for its design rules before writing `build.py`. Ignore its "Step 0 setup gate", its
transcribe / cut / crop / scaffold / render steps and its shell scripts: the claude-edit pipeline and `tools/formats.py`
do those. What still applies: the look, the layout numbers, the engine API, the caption rules and the review checklist.

## The contract (what a format may read from `work/<id>/`)

Written by `tools/rawcut.py` + `tools/prep_source.py` (+ the `recut-plan` workflow for the content plan):

| file | what |
|---|---|
| `raw/cut.mp4` | tight cut, carries the voice |
| `raw/cam_cut.mp4` | clean camera on exactly the same frames (only with a separate camera recording, see rawcut.py) |
| `raw/cut_words.json`, `raw/cuts.json`, `raw/edl.json`, `raw/edit.wav` | cut-clock words, joins (`big` = visible jump), keeps, verified audio |
| `words.json` | `[{i, text, start, end}]` |
| `assets/face_full.mp4`, `face_half.mp4`, `face_wide.mp4` | 30 fps camera crops |
| `assets/voice.m4a`, `metadata.json`, `face_map.json` | voice, camera geometry, frame map |
| `facts.json`, `ASSETS.md`, `shared/`, `beats.json` | verified facts, screenshots/clips/logos, style-agnostic content plan (read only) |

`tools/formats.py media` adds `work/<id>/formats/_media/`: `cam_full.mp4` + `cam_fg.webm` (cut-out), `cam_top.mp4`
(9:8 face with the voice), `cut16x9.mp4` (camera, 30 fps, with the voice), `words_sew.json` (`[[s, e, word]]`) and
`media.json` (duration, face geometry, the big jump cuts).

## Known engine quirks (work around them in build.py)

- Whisper splits decimals ("5" ".5") - `tools/formats.py` joins them in every words file it writes.
- business `reel_engine` and depth `captions()` strip "." from words ("5.5" -> "55"); depth `counter()` rounds to whole
  numbers; depth `camera()` hard-codes transform-origin 50% 38%; business split scenes hidden under a face window trip
  `content_overlap` in check (filler scenes fix it).
- panel / glass headings and the ranking title sit at y ~190 (pack default), inside the band a phone app's top bar can
  cover - move them to ~y 290+.
- Framing: a camera framed tight for split screen leaves little room in the full-frame formats (the pack's chin / chest
  caption spots land on the mouth). Measure the head box from stills; for full-frame formats frame wider (chin ~60%
  down the frame).
- Captions stay verbatim (what you say); the facts rules apply to graphics only.

## Brand

`config/profile.json` -> `formats/profile/profile.json` (+ `formats/profile/assets/fonts`, `assets/sfx`, `sfx_map.json`).
Per-format answers live in `formats-kit/pack-defaults.json`; override any of them under `"skills"` in
`config/profile.json`. After a change: `python tools/import_formats.py --refill`.

## Port fixes

`tools/import_formats.py` applies them as pattern rules every time you import (see its docstring): local GSAP instead
of the CDN, the cut-out through `tools/matte.py` (CUDA / Apple MPS / CPU) instead of `hyperframes remove-background`,
Windows font fallbacks, Windows-safe file:// URLs, `shutil.rmtree` instead of `rm -rf`, Chrome found on any OS, OpenCV
face boxes for ranking (no Swift), the business engine at 30 fps. Everything runs with `PYTHONUTF8=1`. The pack's zsh
scripts and `npx hyperframes@latest init` are not used.
