# Install claude-edit

The editor is a whole folder (tools, templates, fonts, Node packages), not one skill file. The installer puts that folder in one place and adds the `/claude-edit` skill to your Claude Code, so it works from **any folder** you open Claude Code in.

## Quick install

Install the system software in step 1 first. Then:

Windows (PowerShell):

```powershell
irm https://raw.githubusercontent.com/ctskool/claude-edit/main/install.ps1 | iex
```

macOS (Terminal):

```bash
curl -fsSL https://raw.githubusercontent.com/ctskool/claude-edit/main/install.sh | bash
```

What it does, and nothing else:

1. Clones this repo to `~/claude-edit` (set `CLAUDE_EDIT_ROOT` first for another folder; run `install.ps1` or `install.sh` from inside a clone and that clone is used).
2. Builds a Python environment in it, installs the Python and Node packages and the screenshot browser.
3. On an Apple Silicon Mac, adds `mlx-whisper` so transcription runs on the Mac's GPU.
4. Copies the skill to `~/.claude/skills/claude-edit` with a `root.txt` that names the folder from step 1.
5. Runs the doctor and prints anything that needs attention.

Run it again any time to update. It took under two minutes on the author's PC. The transcription model downloads by itself on your first edit. Your edits live in `~/claude-edit/work/`, finals in `~/claude-edit/out/`, and each final is also copied next to your take. To remove it, delete `~/claude-edit` and `~/.claude/skills/claude-edit`.

The Windows installer has been run from a clean state; **the macOS installer and the Mac GPU transcription were written on Windows and have not yet run on a Mac.** If the macOS one fails, the manual steps below do the same job.

You need plain Claude Code. Codex is optional. Windows is tested. **macOS is partly tested** on an Apple Silicon MacBook Air with the manual steps: install, doctor, the test suite, transcription on the CPU, the cut and source prep all run, but no whole edit has run on a Mac yet.

## 1. System software

Python 3.10 or newer (3.12 recommended), Node.js 22 or newer, ffmpeg and ffprobe, git, Chrome or Edge, and Claude Code. Keep at least 25 GB free: raw footage, the transcription model and finals add up. The doctor fails below 5 GB.

### Windows (PowerShell)

```powershell
winget install --exact --id Python.Python.3.12
winget install --exact --id OpenJS.NodeJS.LTS
winget install --exact --id Git.Git
winget install --exact --id Gyan.FFmpeg
irm https://claude.ai/install.ps1 | iex
```

Close and reopen the terminal so PATH refreshes. Edge is enough; install Chrome only if you prefer it.

### macOS (Terminal)

```bash
brew install python@3.12 node ffmpeg-full git
brew link --force ffmpeg-full
brew install --cask google-chrome
curl -fsSL https://claude.ai/install.sh | bash
```

Install [Homebrew](https://brew.sh/) first if you don't have it. Use `ffmpeg-full`, not `ffmpeg`: Homebrew's plain `ffmpeg` has no `drawtext` filter, and the final delivery's contact sheet needs it. If you already have plain `ffmpeg`, run `brew unlink ffmpeg` before the `brew link` line. Apple Silicon has no CUDA, so transcription runs on the CPU (slower, same result). [Claude Code setup reference](https://code.claude.com/docs/en/setup).

## 2. Clone and install by hand

Skip this if you used the quick install. Done this way, `/claude-edit` works when Claude Code is opened inside the clone; run `install.ps1` or `install.sh` from the clone afterwards to make it work everywhere.

### Windows

```powershell
git clone https://github.com/ctskool/claude-edit.git
cd claude-edit
py -3.12 -m venv .venv
$env:Path = (Join-Path (Get-Location) '.venv/Scripts') + ';' + $env:Path
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
npm ci
python -m playwright install chromium
```

The `$env:Path` line selects the project's Python without changing PowerShell's execution policy. Run it again in each new terminal before `claude`.

### macOS

```bash
git clone https://github.com/ctskool/claude-edit.git
cd claude-edit
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
npm ci
python -m playwright install chromium
```

Run `source .venv/bin/activate` again in each new terminal.

HyperFrames is pinned to exactly 0.9.13, because the renderer uses its internal API. Don't upgrade it on its own.

## 3. One-time downloads

**Transcription model.** The tools try faster-whisper `large-v3` on an NVIDIA GPU and fall back to `large-v3-turbo` on the CPU. Fetch the CPU model once (a few GB):

```text
python -c "from faster_whisper import WhisperModel; WhisperModel('large-v3-turbo', device='cpu', compute_type='int8')"
```

On Windows with an NVIDIA card, add the CUDA libraries for the faster path:

```powershell
python -m pip install nvidia-cublas-cu12 "nvidia-cudnn-cu12>=9,<10"
python -c "import sys; sys.path.insert(0,'tools'); from asr import load_whisper; load_whisper('large-v3')"
```

Never install the NVIDIA wheels on a Mac.

On an Apple Silicon Mac, the fast path is `mlx-whisper` instead (the quick install adds it):

```bash
python -m pip install mlx-whisper
```

The tools then transcribe on the Mac's GPU by themselves and say so; if a call fails they redo it on the CPU. `CLAUDE_EDIT_ASR=cpu` turns it off. Not yet run on a Mac.

**Two pencil sounds.** Two sounds in the palette are from Pixabay, whose licence lets you use them in videos but not pass the files on. So they don't ship; this downloads them from Pixabay and cuts their slices on your machine:

```text
python tools/fetch_sounds.py
```

Every other sound ships in `templates/ivory/sfx/`.

## 4. Check

```text
python tools/doctor.py
python tools/doctor.py --fix-hints
```

Each line is PASS, WARN or FAIL, with the Windows and macOS command that fixes it. Exit 1 means a FAIL: fix those before an edit. WARNs are usually optional features (Codex, word alignment, popout, the pencil sounds before step 3). The doctor installs nothing, downloads nothing and renders nothing. A PASS is a preflight, not proof that a whole edit will work.

## 5. Your first edit

For a short, record a vertical (9:16) take: your screen in the top half and your face cam in the bottom half. This is how Chase records in OBS. It is built in the ivory look unless you name another ("in charcoal", "the collage one"); the README lists them. For a 16:9 long-form video, hand over the screen recording and say it is long-form. A separate full-quality camera file named `CAMERA-<same timestamp>.mkv` next to the take is optional; with it, the face clips come from the clean camera. A take that is just your face (no split) works too: tell Claude at intake.

From any folder after the quick install (after a manual install: from the repo folder, with its Python environment selected):

```text
claude
```

Then, in Claude Code:

```text
/claude-edit "C:/Users/you/Videos/take.mkv"
```

or on a Mac:

```text
/claude-edit "/Users/you/Movies/take.mov"
```

Claude cuts the take and **stops for your cut listen**: it opens the cut review page, a simple timeline where you hear the tight cut, drag any join that sounds wrong, and click Approve. After that it builds the whole first edit and opens the review player at `http://localhost:4750`. Open that in Chrome or Edge, pause where you want a change, press **N** and type the note. When you've left your notes, tell Claude "go" in the chat.

Run only one render at a time on a machine.

A test suite ships too. It is optional: `python -m pip install pytest`, then `python -m pytest tools/tests -q` (about eight minutes; tests that need the author's own edits skip).

## Optional extras

| Extra | What it adds | Setup |
|---|---|---|
| Codex | Generated scene images, and a second-model reviewer in the defects round | `npm install -g @openai/codex`, then sign in. Without it, no beat is a generated image and two Claude reviewers run instead |
| Word alignment | Tighter word timings than Whisper's | `python -m pip install torch "transformers>=5.13,<6"`. Slow on a CPU. Without it the tools keep Whisper's timings and say so |
| Popout bottom | Your cut-out rising out of the bottom card instead of a plain split | NVIDIA GPU, `python -m pip install torch torchvision`, then [Robust Video Matting](https://github.com/PeterL1n/RobustVideoMatting) (GPL-3.0, from its own GitHub) into `vendor/RobustVideoMatting` and its `rvm_resnet50.pth` into `vendor/rvm-weights/`. Untested on a Mac |
| `/animate` and `/vfx` effects | A note can call an animation or an effect on your own shot | Install the separate [Chase Animations](https://github.com/ctskool/chase-animations) pack with its `npm run setup`. Without it, Claude says the effect isn't installed and leaves that note open |
| Long-form (16:9) on the GPU | The fast slice renderer for the `charcoal` template | An NVIDIA card with NVENC. Without it `render_slices.py` hands over to the software renderer by itself; nothing to install |
| Reference sound stems | Measuring the sound in a reference reel | Demucs. Without it, use `python tools/reference.py measure ... --no-sound` |

## If something breaks

- `python tools/doctor.py --fix-hints` first.
- `CLAUDE_EDIT_ROOT` points the tools at a different checkout. You rarely need it: `tools/paths.py` finds the folder above `tools/`.
- Paths with spaces are fine: quote them.
