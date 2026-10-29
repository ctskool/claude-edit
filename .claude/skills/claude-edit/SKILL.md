---
name: claude-edit
description: Recut a talking-head recording (a split-screen short with screen recording on top and face cam below, a plain 16:9 or 9:16 camera take, or raw takes it tight-cuts first) into one or more motion-graphics shorts in different looks from the edit menu (ivory = default, rotation, frost, popout, cut, versus), transcript-synced and rendered with HyperFrames. Use when the user says "/claude-edit", "edit this video", "recut this short", "make motion graphics versions of this video", "give me 3 versions of this reel", "do this one in ivory and rotation", or hands over a recording and asks for an edit.
argument-hint: <video or raw takes> [menu names, e.g. "ivory and rotation"]
---

# Claude Edit

One recording in, N differently-designed shorts out. Each style is a folder of rules (`styles/<name>/STYLE.md`), each
format a layout engine (`formats/`), and each video is data (`work/<id>/beats.json`), so the same content plan is rendered
through every version for A/B posting.

Everything below runs from the repo root (the folder that holds this `.claude/`). Paths are relative to it; pass the
absolute repo root as `root` to the workflows. Commands are the same on Windows and macOS (`python` = whatever Python 3.10+
is on PATH; every tool re-runs itself in the repo's `.venv`).

## -1. First run
If `config/config.json` is missing, run `python setup.py` (or the `/claude-edit-setup` skill) before anything else and
fix what it reports. If `config/profile.json` still says "Your Brand", ask the user for their brand (name, handle,
platform, accent + background colour, fonts) once, write it, and carry on - the ivory style keeps its own palette; the
brand drives the layout formats and any end card / handle on screen. Never guess the user's brand.

## 0. Intake (ask only what you can't infer)
- Source: EITHER raw takes (step 0b: one or more recordings of one short, false starts and all) OR a finished / already
  cut video (skip 0b). Layout: a portrait split-screen (screen recording on top, face cam below) or a camera take
  (landscape = auto `--layout camera`). A finished export with burned-in captions in the face half: `--face-top 0.575`
  and check with frame grabs that no caption remnants reach the top edge of the face crop (raise it a little if they do).
- Which versions, by MENU NAME (the internal key on the right is what folders, tools and workflow args use):
  | menu name | internal key | what it is | needs |
  |---|---|---|---|
  | `ivory` (DEFAULT) | `editorial` | split screen, ivory + clay graphics on top; house rules in `styles/editorial/STYLE.md` | - |
  | `rotation` | `business` | face / split / full-screen animation rotation | bundled |
  | `frost` | `glass` | panel layout with frosted glass cards | bundled + cut-out |
  | `popout` | `panel` | you in a rounded panel at the bottom, head popping above it | bundled + cut-out |
  | `cut` | - | only the tight cut of raw takes (step 0b) | - |
  | `versus` | - | Raw vs Claude A/B: the speaker asks for edits out loud; see `/claude-edit-versus` | cut-out |
  "all formats" = rotation, frost and popout. Examples: "/claude-edit <video>" = ivory only;
  "/claude-edit <video> frost and rotation"; "/claude-edit <video> ivory + all formats".
  Shortcuts: `/claude-edit-<menu name> <video>` is this skill limited to one version (`.claude/skills/claude-edit-<name>/`).
  Gallery of what each looks like: `docs/index.html`.
- "bundled" formats (rotation, frost, popout) ship in `pack/` and `setup.py` installs them into `formats/`; if they are
  missing, run `python tools/import_formats.py`. Other layouts (mosaic, layers, evidence, scenes, collage, wrap, tiers) are
  not in this repo yet: if asked for one, say so and offer the closest of the four.
- "cut-out" = `tools/matte.py` (Robust Video Matting). NVIDIA: ~40 s per 50 s of 1080p; Apple Silicon: slower (MPS);
  CPU only: minutes per 10 s - say so before starting a cut-out version on a CPU machine.
- Any URLs / repos / products mentioned that need real screenshots.
- Time budget for a ~50 s short on a fast GPU box: prep ~5 min, recut-plan ~1 h, recut-build ~2-3 h, renders ~3-8 min
  per version, each polish round ~2-3 h. First automated builds land ~6.5/10 on the panel; plan 1-2 polish rounds on the
  versions the user will post.

Pick an id for the video (short, filesystem-safe, e.g. `kimi-launch`); everything for it lives in `work/<id>/`.

## 0b. Raw takes -> tight cut (`tools/rawcut.py`; skip for an already-cut video)
Raw recordings are usually in `recordings_dir` from config/config.json (OBS names files by start time). One short = one
or more take files: confirm which by frame grabs + a quick transcript, never by date alone.
```bash
R=work/<id>/raw
python tools/rawcut.py session $R "<take1.mkv>" "<take2.mkv>" ...   # in recording order
python tools/rawcut.py transcribe $R          # script per take + hints (fillers, repeats, restart?)
# write $R/drops.json: {"words": [[i, j], ...], "secs": [[a, b], ...]} - failed takes, false starts, asides; keep the LAST
# complete take of each line. A "restart?" hint can be a deliberate rhetorical repeat - read it. {} when nothing to drop.
python tools/rawcut.py cut $R                 # read the EDIT as a script
python tools/rawcut.py verify $R              # must say 0 issue(s); fix drops.json and repeat until it does
python tools/rawcut.py render $R              # $R/cut.mp4, frame-exact (NVENC / VideoToolbox / x264 per config)
python tools/rawcut.py times $R               # BIG joins = visible face-cam jumps
```
Separate clean camera (optional): if the recorder also writes the camera on its own (OBS Source Record filter, files named
`CAMERA-<YYYY-MM-DD hh-mm-ss>.mkv` next to each take), `session` pairs it (timestamp within 5 s), measures the frame lag
from face motion, and `render` also writes `$R/cam_cut.mp4` on exactly the same frames; prep_source.py then crops the
face from it at full resolution. Without one, the face comes from the take itself.
Then step 1 with `"$R/cut.mp4"` (split take: `--face-top 0.52` if the seam is at ~52%; measure it from a frame).
`--min-cut 0.3` (default) leaves short pauses uncut, so only real jumps remain; every BIG join must get a full-graphic
takeover or a face punch-in in beats.json (pass the `times` output to the planner as `jumpcuts`).

## 1. Prep (scripts)
```bash
python tools/prep_source.py "<video>" work/<id>            # face_half / face_full / face_wide, voice.m4a, transcript.json
python tools/make_words.py work/<id>/transcript.json work/<id>/words.json --fix "11 Labs=ElevenLabs"
```
`--layout auto` (default): landscape = camera take (all three face clips are centre crops), portrait = split screen (face
cam below `--face-top`). `make_words.py` writes the flat `[{i,text,start,end}]` words (hyphenated words re-joined; each
--fix merges misheard words into the right name, keeping timings). Names Whisper keeps mishearing go in `glossary` in
config/profile.json.

### Face layout: SPLIT SCREEN in the ivory style
Ivory keeps the face cam in the bottom half (`assets/face_half.mp4`) and full-face beats use the plain crop
`assets/face_full.mp4` (`data-media-start = data-start`). No person cut-out in ivory: the look lives in the top half and
the captions. Cut-out formats get theirs from `tools/formats.py media` (step "Formats").

## 2-3. Facts, assets, content plan (one workflow): `tools/workflows/recut-plan.js`
Right after prep: `Workflow({scriptPath: "tools/workflows/recut-plan.js", args: {root: "<abs repo root>", id, source:
"<abs video path>", hints: [repo/site URLs you can see or hear], jumpcuts: [BIG join times, if any]}})`. It runs:
researcher (live-web verified facts with sources and dates -> `facts.json`, what the screen part shows by time) -> asset
wrangler (capture_shots.py light+dark plates, 3-6 clips of the user's own screen recording, logos, `ASSETS.md` with CSS-px
regions) -> planner (`beats.json`) -> independent checker -> one revision. Rules it enforces, if you do any of it by hand:
- `beats.json` is style-agnostic: `id, start, end, words:[i0,i1], say, shape, anchor:{word,t,what}, copy, assets,
  layout_hint, hint_why, emphasis?` (complete example: `templates/editorial/beats.json`).
- Beats break on phrase boundaries, 1.1-3 s each; every spoken list item gets its own beat; the first frame is on-topic.
- Only verified facts or the transcript go on screen - never invent numbers (a stat needs a source URL and a date).
- Every beat gets a `layout_hint` from what is being said (no quota - each switch must be earned by the line):
  `face` = opinion/emphasis, direct address, rhetorical question, payoff, CTA, or covering a jump cut;
  `takeover` = the visual IS the point (name reveal, A vs B, list of 3+, big number, before-after, demo clip);
  `split` = explaining / pointing at what's on screen, setup and connective lines. `hint_why` quotes the trigger. Cut on
  the stressed word, no two switches within ~1.2 s; if one hint holds past ~8 s, look for a line that earns a break.
  Mark `emphasis` on the strongest face/takeover beats and the payoff line.
- Every beat also gets a `visual: {type, why}` picked from what the line MEANS by `styles/VISUAL_MENU.md` (real_shot,
  own_clip, number, compare, diagram, list, scene, face, text; proof beats illustration). Abstract / metaphor lines may get
  a generated `scene` (2-3 per short) only if the user has an image generator they want used; real text/logos overlaid.
- Screenshots: `python tools/capture_shots.py work/<id>/shared/shots work/<id>/shots.spec.json` (DPR 2, light+dark,
  element crops, per-shot box JSON; spec format in `templates/editorial/shots.spec.json`). Crop huge full-page captures.
  Never screenshot Google/search UIs - rebuild them.
- **Pick the source per asset (be smart, not uniform):**
  | the beat needs | source | tool |
  |---|---|---|
  | what the user actually showed / did on screen | a still or clip of their recording | ffmpeg on `raw/cut.mp4` (screen = the part above the face cam) |
  | a public page: GitHub repo / README section, docs, blog, pricing | live capture, light + dark | `capture_shots.py` |
  | a post behind a sign-in (X, Threads, LinkedIn) | read it in the signed-in in-app browser (`mcp__Claude_Browser__*`, if available: text incl. emoji alts, time, avatar, media URLs, stats), then rebuild it crisp | `tools/post_card.py` spec -> PNG + box JSON in `shared/posts/` |
  | another signed-in page (a dashboard) | in-app browser screenshot / zoom, CROPPED to the content | in-app browser |
  | a number / claim with no good page | a built graphic, labelled with its source | the style kit |
  `capture_shots.py` marks a sign-in wall (`"login_wall": true` + a WALL line): never keep that plate, re-route it. Never
  show anything of the signed-in user's own account (sidebar, notifications, handle) or anything in profile `never_show`,
  never interact (like / follow / reply). Drop or crop a post's media when it carries numbers facts.json rules out.
  Record every source URL in ASSETS.md.
- Logos `node_modules/simple-icons/icons/<slug>.svg`; fonts / sfx / gsap from `assets/` (setup.py fills it).

## 4. Build (one workflow, parallel per style): `tools/workflows/recut-build.js`
`Workflow({scriptPath: "tools/workflows/recut-build.js", args: {root: "<abs repo root>", id, styles: ["editorial"]}})`
Per style: director writes plan.json + STORYBOARD.md against the measured targets (`styles/<style>/REFERENCE-ANALYSIS.md`,
`styles/CALIBRATION.md`) -> independent plan check -> builder adapts the PROVEN template `templates/<style>` (8+ critic
rounds of fixes; its media are not shipped, so it never renders as-is) and the measured kits in `styles/*/kit/` to the new
content, with lint + motionlint + snapshot QA -> independent art director -> apply. Reference reels are optional: put 2-4
reels whose editing the user wants matched in `reference/<style>/` (and `python tools/evidence.py <reel> reference/<style>/evidence/<name>`).

## 4b. Panel rounds until SHIP: `tools/workflows/gauntlet-panel.js`
Render (step 5), then `Workflow({scriptPath: "tools/workflows/gauntlet-panel.js", args: {root, video: id, prev: "vN",
next: "vN+1", styles, notes: {style: "context"}}})`. Per style: 3 independent critics on the ENCODED MP4 (fidelity /
motion+sync / first-time phone viewer) -> lead director merges + ranks -> one skeptic per P0/P1 verifies it against the
frames (refuted findings are dropped) -> fixer -> independent regression check (+ one re-fix). Record the panel mean in
`out/<id>-scores.json`; repeat render + round until the panel says SHIP (critic scores are noisy +-0.5, so judge trends).
Gate failures only (frozen stretches, static band over the target): `tools/workflows/gate-fix.js`
`args: {root, items: [{id, style, tag: "vN"}]}` - one agent per project adds on-word motion through each frozen window.

## 5. Render (sequential - never in parallel)
```bash
python tools/render.py styles <id> work/<id>/v2 <vN> editorial      # ~3-8 min per style on a fast GPU box
python tools/render.py one work/<id>/v2/editorial <id>_editorial_<vN> --quality looks --pack editorial   # one by hand
```
Per style: render, finish.py (two-pass loudnorm to -14 LUFS / -2.0 dBTP + 2 fps contact sheet), gates.py with the
style's static-band targets, the critic evidence pack (`out/evidence/<id>_<style>_<vN>/`), a phone copy under 30 MB
(`out/preview/<id>_<style>_<vN>_preview.mp4` - send THAT to the user's phone), and `out/<id>-review.html`. Never run two
renders at once.

## 6. Review before handing over
Watch the contact sheet + spot frames at every beat anchor: captions in sync and never over the mouth, nothing clipped,
face never absent > 3.5 s, no static stretch > 1.5 s, real assets correct. Fix and re-render only what needs it.

## Style packs
| style | look |
|---|---|
| `editorial` = menu `ivory` | ivory #EEEEE7 + clay, serif headline with italic clay word, rebuilt white UI cards, mono caption chips on the seam, progress HUD; face cam split |
To add a style: copy a STYLE.md, change the numbers (palette, type, layout px, motion, captions, banned list), add 3-6
reference frames, and a `templates/<style>` project once one has been built and polished.

## Formats: the other menu
Styles change the skin of the split-screen layout. FORMATS change the layout itself - installed from the
Creator Skill Pack copy in `pack/` into `formats/` (brand from `config/profile.json`; read `formats/README.md` after import). No image
search for other people's pictures without the user's OK; screenshots of whatever the video names (repo, product, pricing, docs page) are always fair game via `capture_shots.py`.
`python tools/formats.py list` shows them. Same prepped video, same facts/assets/beats as the styles:
```bash
python tools/formats.py media  <id>                 # once: cut-outs, crops, 16:9 30 fps camera cut
python tools/formats.py new    <id> <format>        # scaffold work/<id>/formats/<format>/
# the creative step: one builder agent per format IN PARALLEL (Agent tool, general-purpose, background), each briefed
# from formats/BUILDER_BRIEF.md with its fields filled in; builders snapshot/sheet only and never render
python tools/formats.py render <id> <format> [--draft]   # -> out/<id>_fmt-<format>.mp4 (YOU render, one at a time)
python tools/formats.py gallery <id>                # out/<id>-formats.html: the cut, every style, every format side by side
```
Framing: a camera framed tight for split screen leaves the head filling most of a full-frame format - measure the head
box from stills before placing captions (the pack defaults land on the mouth).
