# Install claude-edit

`/claude-edit` is a project skill: it lives in this repo's `.claude/skills/claude-edit/` and runs the tools beside it. Clone the whole repo and open Claude Code inside it. Copying only `SKILL.md` into a global skills folder will not work.

You need plain Claude Code. Codex is optional. Windows is tested. **macOS is partly tested** on an Apple Silicon MacBook Air: install, doctor, the test suite, transcription, the cut and source prep all run, but no whole edit has run on a Mac yet.

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

## 2. Clone and install

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

HyperFrames is pinned to exactly 0.8.184, because the renderer uses its internal API. Don't upgrade it on its own.

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

Today's template, ivory, is vertical, so record a vertical (9:16) take: your screen in the top half and your face cam in the bottom half. This is how Chase records in OBS. A separate full-quality camera file named `CAMERA-<same timestamp>.mkv` next to the take is optional; with it, the face clips come from the clean camera. A take that is just your face (no split) works too: tell Claude at intake.

From the repo folder, with the Python environment selected:

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

Claude cuts the take, sends you a phone-size copy, and **stops for your one-minute cut listen**. After you answer, it builds the whole first edit and opens the review player at `http://localhost:4750`. Open that in Chrome or Edge, pause where you want a change, press **N** and type the note. When you've left your notes, tell Claude "go" in the chat.

Run only one render at a time on a machine.

### Running workflows without a Workflow host

The build steps are written as workflow scripts in `tools/workflows/next/`. If your Claude Code has no `Workflow` tool, the skill tells Claude to run each workflow's phases as ordinary subagents, with the same prompts and checks. These files are not standalone Node programs: don't run them with `node`.

## Optional extras

| Extra | What it adds | Setup |
|---|---|---|
| Codex | Generated scene images, and a second-model reviewer in the defects round | `npm install -g @openai/codex`, then sign in. Without it, no beat is a generated image and two Claude reviewers run instead |
| Word alignment | Tighter word timings than Whisper's | `python -m pip install torch "transformers>=5.13,<6"`. Slow on a CPU. Without it the tools keep Whisper's timings and say so |
| Popout bottom | Your cut-out rising out of the bottom card instead of a plain split | NVIDIA GPU, `python -m pip install torch torchvision`, then [Robust Video Matting](https://github.com/PeterL1n/RobustVideoMatting) (GPL-3.0, from its own GitHub) into `vendor/RobustVideoMatting` and its `rvm_resnet50.pth` into `vendor/rvm-weights/`. Untested on a Mac |
| `/animate` and `/vfx` effects | A note can call an animation or an effect on your own shot | Install the separate [Chase Animations](https://github.com/ctskool/chase-animations) pack with its `npm run setup`. Without it, Claude says the effect isn't installed and leaves that note open |
| Reference sound stems | Measuring the sound in a reference reel | Demucs. Without it, use `python tools/reference.py measure ... --no-sound` |

## If something breaks

- `python tools/doctor.py --fix-hints` first.
- `CLAUDE_EDIT_ROOT` points the tools at a different checkout. You rarely need it: `tools/paths.py` finds the folder above `tools/`.
- Paths with spaces are fine: quote them.
