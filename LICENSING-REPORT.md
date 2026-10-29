# Licensing report (before going public)

Checked 2026-10-27. Covers every file this repo commits plus everything `setup.py` downloads. Short version: **the repo
as committed is clear to publish**, with four judgment calls for Chase at the bottom.

## Ships in the repo

| item | licence / status | basis |
|---|---|---|
| Chase's tools, skills, workflows, styles, templates, versus, setup | MIT (Chase's choice, Q3) | his own work (built with Claude Code) |
| `tools/matte.py` | GPL-3.0-or-later (SPDX header) | it imports Robust Video Matting (GPL-3.0). Keeping only this file GPL leaves the rest MIT |
| HyperFrames skills: `hyperframes`, `-animation`, `-audio`, `-cli`, `-core`, `-creative`, `-keyframes`, `-registry`, `-studio`, `media-use` | Apache-2.0 | `hyperframes` npm package `license: Apache-2.0`, source github.com/heygen-com/hyperframes. Shipped with `licenses/Apache-2.0.txt` + `NOTICE`. `hyperframes`, `hyperframes-cli` and `media-use` are byte-identical to the copies inside the pinned 0.8.184 npm package. `media-use` was swapped for that npm copy: the one in the working copy was missing script files |
| Gallery stills + 6 s silent preview loops (`docs/media/`, 1.8 MB) | all rights reserved | Chase's own face and video. Approved (Q2: stills + loops in the repo, full videos as release assets). They also show captured screenshots of public pages (Kimi / Moonshot posts and site, GitHub), which is normal editorial use |
| `formats-kit/` (format README, builder brief, per-format defaults, sfx map) | MIT | Chase's own text and settings. It contains no pack code |
| Font licence text (`licenses/OFL-1.1.txt`) | OFL | the font files themselves are installed from npm, not committed |

## Fetched at install (never committed)

| item | licence | how |
|---|---|---|
| Robust Video Matting code (commit 53d74c6) + `rvm_mobilenetv3.pth` / `rvm_resnet50.pth` | GPL-3.0 | `setup.py` downloads the GitHub zip + v1.0.0 release weights into `vendor/` and checks SHA-256 |
| SFX (`chime.mp3`, `whoosh.mp3`, ...; also used by `formats/profile`) | Pixabay Content License | HyperFrames bundles them in its npm package (CREDITS.md). Pixabay forbids redistributing the files on their own, so `setup.py` copies them out of `node_modules`; none are committed |
| GSAP 3.13 | GSAP Standard "no charge" licence | npm; free for commercial use. Copied into each rendered project, as the engines expect |
| Fonts (Inter, Inter Tight, Instrument Serif, Newsreader, JetBrains Mono, Space Grotesk) | OFL-1.1 | npm `@fontsource/*` |
| simple-icons | CC0 (the logos themselves are their owners' trademarks) | npm |
| torch / faster-whisper / numpy / opencv / pillow / playwright / PyAV | BSD / MIT / Apache | PyPI. The CUDA torch wheels bundle NVIDIA libraries under NVIDIA's EULA, which pip installs fetch the normal way |

## Must stay out (and does)

| item | why | what the repo does instead |
|---|---|---|
| **Creator Skill Pack** (`formats/`: the 10 layout formats). **Update 2026-10-29:** the pack's author gave permission to share rotation, frost and popout; they now ship in `pack/` | Its README calls it "client templates" and **there is no licence file** in the pack, any format folder or `setup/.pristine`, so there is no permission to redistribute | `tools/import_formats.py` imports the user's **own copy** and applies the Windows / macOS fixes as 16 regex rules. No pack code is stored in the repo, and `formats/` is git-ignored. Tested here: all 16 rules matched (43 edits), all 10 formats filled, and the result matches the working copy's ports except for intended path / Chrome differences |
| `reference/` (other creators' reels) and their evidence packs / contact sheets | third-party content | not shipped. The workflows treat reference reels as optional and user-supplied (`reference/<style>/`) |
| `_archive/` (saraev, signal styles), `work/`, `out/`, `.venv-matte`, `vendor/` | retired / personal / bulky | not copied |
| Chase's avatar, `formats/profile`, OBS / `Videos\1) Completed` conventions | personal | a first-run brand profile (`config/profile.json`, git-ignored) replaces them; the recordings folder is in `config/config.json` |

## Judgment calls for Chase

1. **The ivory style imitates two named creators.** The `editorial` style, its two component kits and the measured
   targets were reverse-engineered from @nocode.joshua and @michelecottiai reels ("frame-matched replica" at 0.94-0.97
   SSIM). A visual style is not copyrightable, and no frames or assets from their videos ship. Still, I anonymised every
   handle, name and reel ID in the shipped files (now "reference creator A / B", reel IDs `ref-A1` ...). The Nick Saraev
   numbers that remain in CALIBRATION.md are anonymised the same way. Worth knowing before you promote "ivory" publicly:
   people may recognise the look.
2. **`templates/editorial/` is your 1022-2 video's build** (index.html, plan, storyboard, beats about Huashu Motion /
   HyperFrames). It ships as code only, with no media, so the builder has a proven example to adapt. Your words and the
   video's topic are visible in it. Fine if you are OK with that being public.
3. **Gallery clips feature third-party screenshots and logos** (Kimi / Moonshot launch post, pricing, GitHub pages)
   inside your own video. That is normal commentary use; flagging it because the full clips go up as release assets.
4. **Raw vs Claude example script** (`examples/prompts.md`) quotes what you say in the 1027-ab take. It is your own
   words.
