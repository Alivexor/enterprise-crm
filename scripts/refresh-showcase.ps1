$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "common.ps1")

$repoRoot = Get-CrmRoot
$backendDir = Join-Path $repoRoot "backend"
Set-Location -LiteralPath $repoRoot

Write-Host "Enterprise CRM showcase refresh" -ForegroundColor Cyan
Write-Host "This removes only Demo data and creates a dense portfolio dataset." -ForegroundColor DarkGray

$python = Join-Path $backendDir ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Backend environment is missing. Run upgrade-existing.cmd first."
}

$backendEnv = Join-Path $backendDir ".env"
if (-not (Test-Path -LiteralPath $backendEnv)) {
    throw "backend\.env is missing."
}

Push-Location -LiteralPath $backendDir
try {
    Write-Host "[1/2] Removing previous showcase records..." -ForegroundColor Yellow
    & $python -m app.scripts.clear_demo
    if ($LASTEXITCODE -ne 0) { throw "Previous demo cleanup failed." }

    Write-Host "[2/2] Creating rich showcase records..." -ForegroundColor Yellow
    & $python -m app.scripts.seed_demo
    if ($LASTEXITCODE -ne 0) { throw "Showcase demo seed failed." }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Showcase workspace is ready." -ForegroundColor Green
Write-Host "Start the CRM with run-local.cmd and sign in with your normal admin account." -ForegroundColor Green
