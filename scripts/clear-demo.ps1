$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "common.ps1")

$repoRoot = Get-CrmRoot
$backendDir = Join-Path $repoRoot "backend"
Set-Location -LiteralPath $repoRoot

Write-Host "Enterprise CRM demo cleanup" -ForegroundColor Cyan

$python = Join-Path $backendDir ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Backend environment is missing. Run setup-local.cmd or upgrade-existing.cmd first."
}

Push-Location -LiteralPath $backendDir
try {
    & $python -m app.scripts.clear_demo
    if ($LASTEXITCODE -ne 0) { throw "Demo cleanup failed." }
}
finally {
    Pop-Location
}

Write-Host "Demo records were removed; your non-demo records were preserved." -ForegroundColor Green
