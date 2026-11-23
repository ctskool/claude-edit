#!/usr/bin/env bash
# Installs /claude-edit for every folder on this Mac (or Linux), or updates it. Safe to run again.
#
#   curl -fsSL https://raw.githubusercontent.com/ctskool/claude-edit/main/install.sh | bash
#
# It puts the editor in ~/claude-edit (set CLAUDE_EDIT_ROOT first to choose another folder; run from inside a clone and
# that clone is used), builds its Python and Node environments there, and copies the skill into ~/.claude/skills so
# /claude-edit works wherever Claude Code is opened. It installs no system software: it tells you what is missing.
# Written on a Windows PC: this script and the Apple GPU transcription it sets up have not yet run on a Mac (2026-11-23).
set -euo pipefail
repo=${CLAUDE_EDIT_REPO:-https://github.com/ctskool/claude-edit.git}   # a fork, or a local clone when testing
step() { printf '\n== %s\n' "$1"; }

missing=()
need() { command -v "$1" >/dev/null 2>&1 || missing+=("  $1    $2"); }
need git 'brew install git'
need node 'brew install node'
need ffmpeg 'brew install ffmpeg-full && brew link --force ffmpeg-full'
need claude 'curl -fsSL https://claude.ai/install.sh | bash'
py=
for try in python3.12 python3.13 python3.11 python3.10 python3; do
  if command -v "$try" >/dev/null 2>&1 && "$try" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then py=$try; break; fi
done
[ -n "$py" ] || missing+=('  python    brew install python@3.12')
if [ ${#missing[@]} -gt 0 ]; then
  printf '\nInstall these first, open a new terminal, and run this again:\n'
  printf '%s\n' "${missing[@]}"
  exit 1
fi

here=
src=${BASH_SOURCE[0]:-}
if [ -n "$src" ] && [ -f "$(dirname "$src")/tools/doctor.py" ]; then here=$(cd "$(dirname "$src")" && pwd); fi
root=${here:-${CLAUDE_EDIT_ROOT:-$HOME/claude-edit}}

if [ -n "$here" ]; then
  step "Using this clone: $root"
elif [ -d "$root/.git" ]; then
  step "Updating $root"; git -C "$root" pull --ff-only
else
  step "Cloning into $root"; git clone "$repo" "$root"
fi
root=$(cd "$root" && pwd)
cd "$root"

step 'Python environment'
[ -x .venv/bin/python ] || "$py" -m venv .venv
vpy="$root/.venv/bin/python"
"$vpy" -m pip install --quiet --upgrade pip
"$vpy" -m pip install --quiet -r requirements.txt

if [ "$(uname -s)" = Darwin ] && [ "$(uname -m)" = arm64 ]; then
  step 'Apple Silicon: Whisper on the Mac GPU (mlx-whisper)'
  "$vpy" -m pip install --quiet mlx-whisper || echo 'mlx-whisper did not install; transcription stays on the CPU (slower, same words)'
fi

step 'Node packages'
npm ci --no-audit --no-fund

step 'Browser for screenshots'
"$vpy" -m playwright install chromium

step 'The skill, for every folder'
skill="$HOME/.claude/skills/claude-edit"
if [ -e "$skill" ] && [ ! -f "$skill/root.txt" ]; then
  keep="$skill.before-$(date +%Y%m%d-%H%M%S)"; mv "$skill" "$keep"
  echo "A claude-edit skill this installer did not make was already there; it is kept at $keep"
elif [ -e "$skill" ]; then
  rm -rf "$skill"
fi
mkdir -p "$(dirname "$skill")"
cp -R "$root/.claude/skills/claude-edit" "$skill"
printf '%s' "$root" > "$skill/root.txt"
echo "$skill -> $root"

step 'Check'
doctor=0
"$vpy" tools/doctor.py --brief || doctor=$?

echo
if [ "$doctor" -ne 0 ]; then
  echo "Installed, but the check found a FAIL. See: \"$vpy\" \"$root/tools/doctor.py\" --fix-hints"
else
  echo 'Installed. Open Claude Code in any folder and type:'
  echo '  /claude-edit "/path/to/your/take.mov"'
fi
echo "The editor and your edits live in $root (edits under work/). Run this installer again to update."
echo 'The transcription model (a few GB) downloads by itself on the first edit.'
