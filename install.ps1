# Installs /claude-edit for every folder on this Windows PC, or updates it. Safe to run again.
#
#   irm https://raw.githubusercontent.com/ctskool/claude-edit/main/install.ps1 | iex
#
# It puts the editor in ~/claude-edit (set CLAUDE_EDIT_ROOT first to choose another folder; run from inside a clone and
# that clone is used), builds its Python and Node environments there, and copies the skill into ~/.claude/skills so
# /claude-edit works wherever Claude Code is opened. It installs no system software: it tells you what is missing.
$ErrorActionPreference = 'Stop'
$repo = 'https://github.com/ctskool/claude-edit.git'
if ($env:CLAUDE_EDIT_REPO) { $repo = $env:CLAUDE_EDIT_REPO }   # a fork, or a local clone when testing

function Step($text) { Write-Host "`n== $text" -ForegroundColor Cyan }
function Run($what, [scriptblock]$block) {
    & $block
    if ($LASTEXITCODE -ne 0) { throw "$what failed (exit code $LASTEXITCODE)" }
}

$missing = @()
foreach ($need in @(
        @('git', 'winget install --exact --id Git.Git'),
        @('node', 'winget install --exact --id OpenJS.NodeJS.LTS'),
        @('ffmpeg', 'winget install --exact --id Gyan.FFmpeg'),
        @('claude', 'irm https://claude.ai/install.ps1 | iex'))) {
    if (-not (Get-Command $need[0] -ErrorAction SilentlyContinue)) { $missing += ('  {0,-8} {1}' -f $need[0], $need[1]) }
}
$py = $null
foreach ($try in @(@('py', '-3.12'), @('py', '-3'), @('python'))) {
    if (-not (Get-Command $try[0] -ErrorAction SilentlyContinue)) { continue }
    $rest = @($try | Select-Object -Skip 1)
    try { & $try[0] @rest -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>$null } catch { $LASTEXITCODE = 1 }
    if ($LASTEXITCODE -eq 0) { $py = $try; break }
}
if (-not $py) { $missing += '  python   winget install --exact --id Python.Python.3.12' }
if ($missing) {
    Write-Host "`nInstall these first, open a new terminal, and run this again:" -ForegroundColor Yellow
    $missing | ForEach-Object { Write-Host $_ }
    throw 'missing system software'
}

$here = $null
if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot 'tools/doctor.py'))) { $here = $PSScriptRoot }
if ($here) { $root = $here } elseif ($env:CLAUDE_EDIT_ROOT) { $root = $env:CLAUDE_EDIT_ROOT } else { $root = Join-Path $HOME 'claude-edit' }

if ($here) {
    Step "Using this clone: $root"
} elseif (Test-Path (Join-Path $root '.git')) {
    Step "Updating $root"
    Run 'git pull' { git -C $root pull --ff-only }
} else {
    Step "Cloning into $root"
    Run 'git clone' { git clone $repo $root }
}
$root = (Resolve-Path $root).Path
Set-Location $root

Step 'Python environment'
$venvPy = Join-Path $root '.venv/Scripts/python.exe'
if (-not (Test-Path $venvPy)) {
    $rest = @($py | Select-Object -Skip 1)
    Run 'python -m venv' { & $py[0] @rest -m venv .venv }
}
Run 'pip' { & $venvPy -m pip install --quiet --upgrade pip }
Run 'pip install' { & $venvPy -m pip install --quiet -r requirements.txt }

Step 'Node packages'
Run 'npm ci' { npm ci --no-audit --no-fund }

Step 'Browser for screenshots'
Run 'playwright install' { & $venvPy -m playwright install chromium }

Step 'The skill, for every folder'
$skill = Join-Path $HOME '.claude/skills/claude-edit'
if ((Test-Path $skill) -and -not (Test-Path (Join-Path $skill 'root.txt'))) {
    $keep = "$skill.before-" + (Get-Date -Format 'yyyyMMdd-HHmmss')
    Move-Item $skill $keep
    Write-Host "A claude-edit skill this installer did not make was already there; it is kept at $keep"
} elseif (Test-Path $skill) {
    Remove-Item -Recurse -Force $skill
}
New-Item -ItemType Directory -Force (Split-Path $skill) | Out-Null
Copy-Item -Recurse (Join-Path $root '.claude/skills/claude-edit') $skill
[IO.File]::WriteAllText((Join-Path $skill 'root.txt'), ($root -replace '\\', '/'))
Write-Host "$skill -> $root"

Step 'Check'
& $venvPy tools/doctor.py --brief
$doctor = $LASTEXITCODE

Write-Host ''
if ($doctor -ne 0) {
    Write-Host "Installed, but the check found a FAIL. See: `"$venvPy`" `"$root\tools\doctor.py`" --fix-hints" -ForegroundColor Yellow
} else {
    Write-Host 'Installed. Open Claude Code in any folder and type:' -ForegroundColor Green
    Write-Host '  /claude-edit "C:/path/to/your/take.mkv"'
}
Write-Host "The editor and your edits live in $root (edits under work\). Run this installer again to update."
Write-Host 'The transcription model (about 1.6 GB, 3 GB with an NVIDIA card) downloads by itself on the first edit.'
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    Write-Host 'NVIDIA card found. For fast transcription, once:'
    Write-Host "  `"$venvPy`" -m pip install nvidia-cublas-cu12 `"nvidia-cudnn-cu12>=9,<10`""
}
