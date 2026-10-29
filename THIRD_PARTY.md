# Third-party components

## Committed in this repo

| what | where | licence |
|---|---|---|
| HyperFrames agent skills (unmodified) | `.claude/skills/hyperframes*`, `.claude/skills/media-use` | Apache-2.0 ([licenses/Apache-2.0.txt](licenses/Apache-2.0.txt), [NOTICE](NOTICE)) |
| Gallery stills and preview loops (the author's own videos) | `docs/media/` | all rights reserved; shown for demonstration |
| Creator Skill Pack: `business-short-form-reels` (rotation), `glass-explainer-reel` (frost), `explainer-panel-reel` (popout) | `pack/` | redistributed with the pack author's permission; not covered by this repo's MIT licence (see [pack/README.md](pack/README.md)) |
| Playfair Display, Caveat fonts | `pack/*/assets/fonts/` | SIL OFL 1.1 ([licenses/OFL-1.1.txt](licenses/OFL-1.1.txt)) |

Everything else in the repo is the author's work under [MIT](LICENSE), except `tools/matte.py` (GPL-3.0-or-later) and `pack/`.

## Installed or downloaded by `setup.py` (never committed)

| what | from | licence | notes |
|---|---|---|---|
| HyperFrames CLI 0.8.184 | npm | Apache-2.0 | renders every video |
| GSAP 3.13 | npm | GSAP Standard "no charge" licence (https://gsap.com/standard-license) | copied into each project's assets |
| Fonts: Inter, Inter Tight, Instrument Serif, Newsreader, JetBrains Mono, Space Grotesk | npm `@fontsource/*` | SIL OFL 1.1 ([licenses/OFL-1.1.txt](licenses/OFL-1.1.txt)) | copied to `assets/fonts` |
| simple-icons | npm | CC0-1.0 | brand logos; the marks themselves are their owners' trademarks |
| Sound effects (chime, click, whoosh, ...) | the hyperframes npm package (media-use skill) | Pixabay Content License (https://pixabay.com/service/license-summary/) | Pixabay does not allow redistributing the files on their own, so they are copied from your npm install, not committed |
| Robust Video Matting code (commit 53d74c6) + weights v1.0.0 | github.com/PeterL1n/RobustVideoMatting | GPL-3.0 | `vendor/`; SHA-256-checked |
| faster-whisper, CTranslate2 | PyPI | MIT | Whisper model weights (MIT) download on first use |
| PyTorch, torchvision | PyPI / download.pytorch.org | BSD-3-Clause | CUDA wheels include NVIDIA libraries under NVIDIA's licence |
| numpy, opencv-python, pillow, playwright, PyAV | PyPI | BSD / Apache-2.0 / MIT-CMU / Apache-2.0 / BSD | |
| ffmpeg | winget (Gyan build) / Homebrew | LGPL / GPL (build-dependent) | system install, asks first |
| The other 7 Creator Skill Pack layout formats | YOUR copy, imported by `tools/import_formats.py` | the pack's own terms | not in this repo; see README |
