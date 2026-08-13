$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "common.ps1")

$repoRoot = Get-CrmRoot
$backendDir = Join-Path $repoRoot "backend"
Set-Location -LiteralPath $repoRoot

Write-Host "Enterprise CRM portfolio demo seed" -ForegroundColor Cyan

$python = Join-Path $backendDir ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Backend environment is missing. Run setup-local.cmd or upgrade-existing.cmd first."
}

$backendEnv = Join-Path $backendDir ".env"
if (-not (Test-Path -LiteralPath $backendEnv)) {
    throw "backend\.env is missing. Run setup-local.cmd first."
}

Push-Location -LiteralPath $backendDir
try {
    & $python -m app.scripts.seed_demo
    if ($LASTEXITCODE -ne 0) { throw "Demo seed failed." }
}
finally {
    Pop-Location
}

Write-Host "Demo data is ready. Start the CRM with run-local.cmd." -ForegroundColor Green
