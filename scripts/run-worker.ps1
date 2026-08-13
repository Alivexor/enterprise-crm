$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot "common.ps1")
$repoRoot = Get-CrmRoot
$backendDir = Join-Path $repoRoot "backend"
$python = Join-Path $backendDir ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Backend virtual environment is missing. Run upgrade-existing.cmd first." }
Set-Location $backendDir
& $python -m app.scripts.run_worker
if ($LASTEXITCODE -ne 0) { throw "CRM worker exited with code $LASTEXITCODE" }
