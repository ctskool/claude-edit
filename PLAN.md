# claude-edit (shareable repo): plan

Goal: anyone on macOS or Windows clones this repo, opens it in Claude Code, runs one setup command, and can type
`/claude-edit my-video.mp4` (or `/claude-edit-versus take.mkv`) and get shorts out. Built from Chase's working copy in
`C:\Users\Chase\shorts` without moving or changing anything there.

Status: **approved 2026-10-27 with the recommended answers** (Q1 importer, Q2 stills + loops in repo and full videos as
release assets, Q3 MIT with matte.py GPL-3.0, Q4 README credit only, Q5 public repo, created under the **ctskool** GitHub
account at Chase's request; push only after his go). Built; see README, LICENSING-REPORT.md.

---

## 1. Repo layout

```
claude-edit/
  README.md                 what it does, install (Mac + Windows), prompt examples, gallery link
  LICENSE                   MIT for Chase's own code and skills (see section 6)
  THIRD_PARTY.md            what is bundled, what setup downloads, under which licence
  setup.py                  the one command: detect OS/GPU, install/check deps, write config, smoke test
  config/
    config.example.json     machine config (written by setup.py -> config/config.json, git-ignored)
    profile.example.json    brand profile template (your name, handle, colours, fonts) -> config/profile.json
  .claude/
    settings.json           permissions for the tools the skills run (python/ffmpeg/npx), nothing else
    skills/
      claude-edit/          main skill, rewritten for "your" footage, not Chase's folders
      claude-edit-<name>/   ivory rotation frost popout mosaic layers evidence scenes collage wrap tiers cut
      claude-edit-versus/   NEW: Raw vs Claude A/B format (section 4)
      claude-edit-setup/    NEW: "/claude-edit-setup" = run setup.py + ask the brand questions in chat
      hyperframes*, media-use   HyperFrames core skills, pinned to 0.8.184 (Apache-2.0)
  tools/                    Python tools (rawcut, prep_source, transcribe, matte, finish, gates, formats, versus, ...)
    common.py               NEW: loads config, picks encoder / torch device / python for the matte venv
    render.py               NEW: replaces render_one.sh + render_styles.sh (same behaviour, runs everywhere)
    workflows/              recut-plan, recut-build, gauntlet-panel, gate-fix (root passed in, no C:\ paths)
  styles/editorial/         STYLE.md, kits (ivory look); CALIBRATION.md, VISUAL_MENU.md
  templates/editorial/      NEW: the proven 1022-2 ivory project (index.html, plan.json, beats.json, STORYBOARD.md)
                            with media stripped - recut-build adapts THIS instead of work/1022-2
  templates/versus/         NEW: the A/B composition template + music synth
  formats/                  the 10 layout formats (only if Q1 says we may ship them; else an importer, see 6)
  docs/
    index.html              gallery page (GitHub Pages: Settings -> Pages -> /docs)
    media/                  stills (JPG, ~50 KB each) + short looping previews (see Q2)
  examples/prompts.md       prompt cookbook
```

Left out: `_archive/` (saraev, signal), `work/`, `out/`, `reference/` (other creators' videos), `.venv-matte`,
`vendor/` (RVM code + weights), `node_modules`, `research*`, `reports/`, dev-only workflows (crown-robust,
face-retime, split-convert, editorial-rhythm, gauntlet-round) and dev-only tools (face_synth, crown_*, replica/,
score_replica, compare.sh, cutout.sh, face_pipeline.sh, scaffold_styles.sh - the finished-export crown repair path).
Chase's avatar, brand profile and `Videos\` conventions do not ship; they become config the user fills in.

## 2. Setup / doctor: `python setup.py`

One Python 3.10+ script, standard library only, same on both OSes. Steps (each prints OK / FIXED / NEEDS YOU):

| check | Windows | macOS |
|---|---|---|
| OS + arch | `platform` | `platform` (arm64 = Apple Silicon) |
| GPU | `nvidia-smi` -> NVIDIA | Apple Silicon -> MPS; Intel Mac -> CPU |
| ffmpeg / ffprobe | `winget install Gyan.FFmpeg` (asks first) | `brew install ffmpeg` (asks first) |
| encoder | `h264_nvenc` if NVIDIA and ffmpeg has it, else `libx264` | `h264_videotoolbox`, else `libx264` |
| Node 22+ | `winget install OpenJS.NodeJS.LTS` (asks) | `brew install node` (asks) |
| npm deps | `npm ci` (hyperframes 0.8.184 pinned, gsap, fontsource, simple-icons) | same |
| Chrome for HyperFrames | `npx hyperframes doctor` / `npx hyperframes browser` | same |
| Python deps | `pip install -r requirements.txt` into `.venv` (faster-whisper, numpy, opencv-python, pillow, playwright) | same |
| Whisper device | CUDA float16 if available, else CPU int8 | CPU int8 (faster-whisper has no Metal backend) |
| cut-out model | `.venv-matte`: torch cu128 wheels on NVIDIA, CPU wheels otherwise | torch (MPS build) |
| RVM | download PeterL1n/RobustVideoMatting at a pinned commit (zip) + `rvm_mobilenetv3.pth` / `rvm_resnet50.pth` from its v1.0.0 release into `vendor/` (git-ignored), verify SHA-256 | same |
| SFX | copy HyperFrames' bundled Pixabay SFX from `node_modules/hyperframes/dist/skills/media-use/...` into `assets/sfx/` (not committed) | same |
| config | write `config/config.json`: os, gpu, encoder, whisper device, matte device + python path, chrome path, recordings folder | same |
| smoke test | `--smoke`: synth 5 s clip (ffmpeg testsrc + tone) -> encode with the chosen encoder -> 5 s matte -> whisper load -> 5 s HyperFrames render of the ivory template -> finish.py | same |

Flags: `--check` (doctor only, changes nothing), `--yes` (install without asking), `--no-matte` (skip torch, ~2.5 GB),
`--smoke`. Re-running is safe. `/claude-edit-setup` runs it from chat and then asks the brand questions
(name, handle, platform, accent + background colours, three fonts with OFL fallbacks) and writes `config/profile.json`.

## 3. Porting the tools off Chase's machine

- `tools/common.py`: `ROOT` (repo root), `cfg()` (config.json with defaults), `encoder_args(quality)` (nvenc /
  videotoolbox / libx264 with matched quality), `hwaccel_args()` (`cuda` / `videotoolbox` / none, with the existing
  retry-without fallback), `matte_python()`, `torch_device()`, `chrome_path()`.
- `rawcut.py`: `h264_nvenc` -> `encoder_args()`; `-hwaccel cuda` -> `hwaccel_args()`; Whisper device from config.
  Split-composite geometry (seam at 51.9%, 2160x3840) becomes `config.source` fields with Chase's values as the
  documented example; 16:9 camera-only takes (like the A/B take) already work and become the documented default.
- `matte.py`: device = cuda / mps / cpu; fp16 on CUDA, fp32 on MPS/CPU; downsample ratio auto-lowered on CPU; prints
  an honest speed estimate (CPU is slow: minutes per 10 s).
- `transcribe.py`, `prep_source.py`, `formats.py`: same device/encoder helpers; `.venv-matte/Scripts/python.exe` ->
  `matte_python()` (`bin/python` on macOS).
- `.sh` scripts -> Python (`render.py` replaces render_one.sh + render_styles.sh). Nothing left needs bash.
- Workflows: `const S = 'C:\\Users\\Chase\\shorts'` -> `A.root` (the skill passes the repo root); `work/1022-2` reference
  -> `templates/editorial`; donor-frame steps (other creators' reels in `reference/`) become optional: used when the user
  drops their own reference reels in `reference/`, otherwise the director judges against STYLE.md + template snapshots.
- Formats: Chase-specific values (`profile.json`, `.configured`, Chrome paths, `C:/Users/Chase/...`) -> config; the
  pack's own macOS paths come back (VideoToolbox, Apple Vision face boxes stay replaced by OpenCV, which works on both).
- Grep gate before commit: no `C:\Users\Chase`, `chase.h.ai`, `Chase AI`, `Videos\1) Completed` outside docs credits.

**Mac status:** everything above is implemented for macOS but there is no Mac here, so Mac paths ship marked
"untested" in README and setup output until someone runs `python setup.py --smoke` on one.

## 4. New skill: `/claude-edit-versus` (Raw vs Claude)

Generalises `work/1027-ab`. Input: one 16:9 talking-head take in which the speaker says edit instructions out loud
("give me captions", "make it warmer", "put a big title behind my head that says ...", "pull the camera closer",
"bring in some music", "make it quieter", "soften the background", "change the caption font").

1. `rawcut.py session/transcribe/cut/verify/render` -> tight cut (dead space only; the takes the speaker drops stay
   Claude's call through drops.json as today).
2. `tools/versus.py prep <id>`: cam_1080.mp4 (top), cam_raw.mp4 (bottom, same frames), voice.m4a, words.json, and the
   GPU/MPS/CPU cut-out `cam_fg.webm` (needed for title-behind-head and background effects).
3. Claude reads the transcript and writes `edits.json`: one entry per spoken instruction, anchored on the word that
   names the effect (`{op, at_word, t, params, log_label}`), plus caption chunks with key words. Ops in the library:
   `captions, keywords, grade_warm|cool|bw, title_behind, edit_log, sfx_on_change, punch_in, punch_out, music_in,
   music_level, bg_blur, caption_font, zoom_text, lower_third, end_card`; an instruction outside the library gets a
   `custom` op whose GSAP snippet Claude writes (checked with `hyperframes check`).
4. `tools/versus.py build <id>`: fills `templates/versus/index.html` from edits.json (header text, labels, panels,
   edit-log rows backfilled when the log appears, one SFX per edit rotated so no two in a row repeat), short-form-safe
   layout (header below the app tabs, both panels done by y ~1550).
5. `tools/versus.py music <id>`: the numpy synth bed (`make_music.py`, chord set / bpm / seed options) sized to the
   music-in point; level follows `music_level` ops.
6. `tools/render.py` -> finish.py (-14 LUFS / -2 dBTP) -> `out/<id>_versus.mp4` + contact sheet.

Test: rebuild Chase's own 1027-ab take through the new skill and compare with `out/1027-ab_raw-vs-claude_v4.mp4`
(same edits on the same words, +-1 frame); stays local, the take is not committed.

## 5. Docs and gallery

- README: one-paragraph pitch, a 3x4 grid of stills, install for Windows and macOS (4 commands each), what to film
  (16:9 camera take, or a 9:16 split screen + face cam), the menu table, prompt examples, time/GPU expectations
  (renders ~3-8 min on an RTX 5090; CPU cut-outs are much slower), troubleshooting from `setup.py --check`.
- `examples/prompts.md`: `/claude-edit my-video.mp4`, `/claude-edit my-video.mp4 ivory and rotation`,
  `/claude-edit my-video.mp4 ivory + all formats`, `/claude-edit-cut take1.mkv take2.mkv`, `/claude-edit-mosaic ...`,
  `/claude-edit-versus take.mkv`, "redo my brand setup", "polish the rotation version", etc.
- `docs/index.html`: the edit-menu gallery restyled for GitHub Pages: one card per version (still + looping preview +
  what it is + when to use it + its shortcut), plus the Raw vs Claude video. Media plan depends on Q2.

## 6. Licensing (full report goes in `LICENSING-REPORT.md` before anything is public)

| thing | licence | plan |
|---|---|---|
| Chase's skills, tools, styles, templates, versus | his | MIT (or keep "all rights reserved", your call) |
| HyperFrames skills (`hyperframes*`, `media-use`) | Apache-2.0 (heygen-com/hyperframes) | ship copies + LICENSE + NOTICE, pinned to 0.8.184 |
| HyperFrames SFX (`chime.mp3` etc., also in `formats/profile/assets/sfx`) | Pixabay Content Licence (no standalone redistribution) | **not committed**; setup copies them from the installed npm package |
| GSAP | GSAP standard no-charge licence | not committed; installed by npm |
| Fonts (Inter, Inter Tight, Instrument Serif, Newsreader, JetBrains Mono, Space Grotesk, Playfair Display, Caveat) | OFL-1.1 | fine to ship with OFL text; prefer npm @fontsource where possible |
| simple-icons | CC0 | npm |
| Robust Video Matting code + weights | GPL-3.0 | **downloaded at setup, never committed**; `tools/matte.py` (imports it) licensed GPL-3.0 on its own, noted in THIRD_PARTY.md |
| faster-whisper / CTranslate2 / Whisper weights | MIT | pip + downloaded on first use |
| `formats/` (Creator Skill Pack) | **no licence file found** in any format folder or `setup/.pristine` | **needs your answer (Q1)** |
| `styles/editorial` REFERENCE-ANALYSIS + workflow donor lists | names two creators and lists their reel IDs | strip handles + reel IDs from shipped files; never ship `reference/` videos |
| Chase's avatar, face clips, brand | his likeness | avatar out; face clips only per Q2 |

## 7. Order of work after your OK

1. Copy in + scrub (skills, tools, styles, templates; grep gate) and `setup.py` + `common.py`.
2. Port rawcut / matte / transcribe / prep_source / formats / workflows; `render.py`.
3. `versus` skill + `tools/versus.py`; reproduce 1027-ab locally.
4. README, prompts, gallery, LICENSING-REPORT.md, THIRD_PARTY.md.
5. Smoke test here: fresh clone into a temp folder -> `python setup.py --yes --smoke` -> passes on this box.
6. Commit locally in `share/claude-edit`. **No GitHub repo, no push until you say go** (Q5).

## Questions for Chase

- **Q1. Creator Skill Pack (`formats/`)**: where did it come from, and does its licence let you republish it? No licence
  file is in the folders. If yes -> ship all 10 formats. If no / unsure -> ship ivory + cut + versus fully working, and
  the 10 format shortcuts as an importer: `python setup.py --import-pack <path to your copy>` copies the pack in and
  applies our Windows/macOS patches (`_patch.py`). Recommended until you confirm.
- **Q2. Your face in the gallery**: the gallery clips (37 MB in `out/gallery/`) and the Raw vs Claude video are you.
  Options: (a) stills in the repo + MP4s as GitHub Release assets (repo stays small), (b) stills only, (c) no face at
  all (re-render the gallery on a stock/neutral clip later). Recommended (a).
- **Q3. Licence for your own code**: MIT (anyone can reuse, credit kept) or source-available "all rights reserved"?
  Recommended MIT, with `tools/matte.py` GPL-3.0.
- **Q4. Default brand**: the repo ships a neutral default (white/black/one accent, OFL fonts) and the first run asks for
  the user's brand. Should your brand appear anywhere (e.g. "made by Chase AI" credit + link in README)? Recommended yes,
  README credit only.
- **Q5. GitHub**: repo name `claude-edit` under your account, public? (Asked again before the push.)
