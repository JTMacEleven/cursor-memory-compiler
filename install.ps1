param(
    [string]$Target = ".",
    [string]$KbSubdir = ""
)

$ErrorActionPreference = "Stop"
$Source = $PSScriptRoot
$Target = Resolve-Path $Target

if ($KbSubdir) {
    $KbRoot = Join-Path $Target $KbSubdir
    New-Item -ItemType Directory -Force -Path $KbRoot | Out-Null
} else {
    $KbRoot = $Target
}

Write-Host "Installing cursor-memory-compiler into: $KbRoot"

$dirs = @("hooks", "scripts", "daily", "knowledge", "knowledge\concepts", "knowledge\connections", "knowledge\qa", "reports")
foreach ($d in $dirs) {
    New-Item -ItemType Directory -Force -Path (Join-Path $KbRoot $d) | Out-Null
}

$files = @("AGENTS.md", "howToUse.md", "pyproject.toml", ".gitignore")
foreach ($f in $files) {
    Copy-Item (Join-Path $Source $f) (Join-Path $KbRoot $f) -Force
}

Copy-Item (Join-Path $Source "hooks\*") (Join-Path $KbRoot "hooks") -Recurse -Force
Copy-Item (Join-Path $Source "scripts\*") (Join-Path $KbRoot "scripts") -Recurse -Force

foreach ($kf in @("index.md", "log.md")) {
    $dest = Join-Path $KbRoot "knowledge\$kf"
    if (-not (Test-Path $dest)) {
        Copy-Item (Join-Path $Source "knowledge\$kf") $dest -Force
    }
}

# Cursor config at workspace root (where hooks must live)
$cursorDir = Join-Path $Target ".cursor"
$rulesDir = Join-Path $cursorDir "rules"
New-Item -ItemType Directory -Force -Path $rulesDir | Out-Null

if ($KbSubdir) {
    # Nested KB: wrapper script + hooks.json at workspace root
    $hooksDir = Join-Path $cursorDir "hooks"
    New-Item -ItemType Directory -Force -Path $hooksDir | Out-Null

    @"
param([Parameter(Mandatory=`$true)][string]`$HookScript)
`$vaultRoot = Join-Path `$PSScriptRoot "..\..\$KbSubdir" | Resolve-Path
Set-Location `$vaultRoot
python -m uv run python "hooks/`$HookScript"
"@ | Set-Content (Join-Path $hooksDir "run-hook.ps1") -Encoding UTF8

    @"
{
  "version": 1,
  "hooks": {
    "sessionStart": [{ "command": "powershell -NoProfile -ExecutionPolicy Bypass -File .cursor/hooks/run-hook.ps1 -HookScript session-start.py", "timeout": 15 }],
    "sessionEnd": [{ "command": "powershell -NoProfile -ExecutionPolicy Bypass -File .cursor/hooks/run-hook.ps1 -HookScript session-end.py", "timeout": 10 }],
    "preCompact": [{ "command": "powershell -NoProfile -ExecutionPolicy Bypass -File .cursor/hooks/run-hook.ps1 -HookScript pre-compact.py", "timeout": 10 }],
    "stop": [{ "command": "powershell -NoProfile -ExecutionPolicy Bypass -File .cursor/hooks/run-hook.ps1 -HookScript stop-memory.py", "loop_limit": 1, "timeout": 5 }]
  }
}
"@ | Set-Content (Join-Path $cursorDir "hooks.json") -Encoding UTF8

    $ruleContent = Get-Content (Join-Path $Source ".cursor\rules\knowledge-base.mdc") -Raw
    $ruleContent = $ruleContent -replace '\[AGENTS\.md\]\(AGENTS\.md\)', "[AGENTS.md]($KbSubdir/AGENTS.md)"
    $ruleContent = $ruleContent -replace 'knowledge/', "$KbSubdir/knowledge/"
    $ruleContent = $ruleContent -replace 'daily/', "$KbSubdir/daily/"
    $ruleContent = $ruleContent -replace 'scripts/', "$KbSubdir/scripts/"
    $ruleContent | Set-Content (Join-Path $rulesDir "knowledge-base.mdc") -Encoding UTF8
} else {
    Copy-Item (Join-Path $Source ".cursor\hooks.json") (Join-Path $cursorDir "hooks.json") -Force
    Copy-Item (Join-Path $Source ".cursor\rules\knowledge-base.mdc") (Join-Path $rulesDir "knowledge-base.mdc") -Force
}

Set-Location $KbRoot
python -m pip install uv -q 2>$null
python -m uv sync

Write-Host "Done. Open $Target in Cursor and check Settings -> Hooks."
