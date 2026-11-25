# eval_run.ps1 : one evaluation run = prepare folder, open claude, then grade and record after /exit.
# usage: powershell -ExecutionPolicy Bypass -File C:\AI_Tools\eval_run.ps1 -Id T02 -Run 1
param(
  [Parameter(Mandatory=$true)][string]$Id,
  [Parameter(Mandatory=$true)][int]$Run,
  [string]$Structure = 'baseline',
  [string]$Root = 'C:\baseline',
  [string]$Python = 'python',
  [string]$Notes = '',
  [int]$Quality = 0,
  [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$src  = "C:\AI_Tools\eval_set\$Id"
$priv = "C:\eval_private\$Id"
$add  = "C:\AI_Tools\eval_add.py"
$d    = Join-Path (Join-Path $Root $Id) ("run" + $Run)
if (-not (Test-Path "$src\prompt.txt")) { throw "missing $src\prompt.txt" }
if (-not (Test-Path "$priv\grade.py")) { throw "missing $priv\grade.py" }
if (-not (Test-Path $add)) { throw "missing $add (install eval_add.py first)" }

Set-Location C:\
if (Test-Path $d) {
  $ans = Read-Host "Run folder exists: $d . Delete and redo? (y/N)"
  if ($ans -ne 'y') { Write-Host 'aborted'; exit 1 }
  Remove-Item $d -Recurse -Force
}
New-Item -ItemType Directory -Force $d | Out-Null
Copy-Item "$src\*" $d -Recurse
Set-Location $d
Get-Content .\prompt.txt -Raw -Encoding UTF8 | Set-Clipboard
Write-Host '--- clipboard check: Korean text must look right ---'
Get-Clipboard | Select-Object -First 3
$go = Read-Host 'Start claude? (Enter = yes, n = abort)'
if ($go -eq 'n') { Write-Host 'aborted'; exit 1 }
Write-Host "RUN $Id run$Run : paste with Ctrl+V, keep manual mode, choose option 2 on plan screens, type /exit when done."
claude

Set-Location $d
Write-Host '--- grading ---'
& $Python "$priv\grade.py" $d
$code = $LASTEXITCODE
Write-Host "grade exit code: $code"
if ($code -ne 0 -and $code -ne 1) { Write-Host "WARNING: exit code $code is not a normal pass/fail. Check python and grade.py before recording."; }
$ok = if ($code -eq 0) { 1 } else { 0 }

Write-Host '--- files added (NEW) or changed (MOD) compared with the input ---'
Get-ChildItem $d -Recurse -File -Force |
  Where-Object { $_.FullName -notmatch '\\(\.claude|__pycache__|\.pytest_cache)\\' } |
  ForEach-Object {
    $rel = $_.FullName.Substring($d.Length + 1)
    $s = Join-Path $src $rel
    if (-not (Test-Path $s)) { "NEW  $rel" }
    elseif ((Get-FileHash $s).Hash -ne (Get-FileHash $_.FullName).Hash) { "MOD  $rel" }
  }

$list = @($add, '--auto', $d, '--task', $Id, '--structure', $Structure, '--run', "$Run", '--success', "$ok")
if ($Quality -ge 1) { $list += @('--quality', "$Quality") }
if ($Notes) { $list += @('--notes', $Notes) }
if ($DryRun) { $list += '--dry-run' }
Write-Host '--- recording ---'
& $Python @list
Set-Location C:\
