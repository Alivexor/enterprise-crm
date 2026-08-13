$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$Root = Get-CrmRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "backend/.venv is missing. Run setup-local.cmd or upgrade-existing.cmd first."
}
if (-not (Test-Path (Join-Path $Frontend "node_modules"))) {
    throw "frontend/node_modules is missing. Run setup-local.cmd or upgrade-existing.cmd first."
}

Write-Host "[Backend] compile, tests, migrations" -ForegroundColor Cyan
Push-Location $Backend
try {
    & $Python -m compileall -q app migrations tests
    if ($LASTEXITCODE -ne 0) { throw "Backend compile failed." }
    & $Python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw "Backend tests failed." }
    & $Python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw "Alembic upgrade failed." }
    & $Python -m alembic current
    if ($LASTEXITCODE -ne 0) { throw "Alembic current failed." }
    & $Python -m alembic check
    if ($LASTEXITCODE -ne 0) { throw "Alembic model/migration drift check failed." }
    & $Python -m app.scripts.run_worker --once
    if ($LASTEXITCODE -ne 0) { throw "Background worker smoke test failed." }
} finally {
    Pop-Location
}

Write-Host "[Frontend] lint, typecheck, production build" -ForegroundColor Cyan
$nextOutput = Join-Path $Frontend ".next"
if (Test-Path $nextOutput) { Remove-Item -LiteralPath $nextOutput -Recurse -Force }
Push-Location $Frontend
try {
    & npm run lint
    if ($LASTEXITCODE -ne 0) { throw "Frontend lint failed." }
    & npm run typecheck
    if ($LASTEXITCODE -ne 0) { throw "Frontend typecheck failed." }
    & npm run build
    if ($LASTEXITCODE -ne 0) { throw "Frontend production build failed." }
} finally {
    Pop-Location
}

Write-Host "All release checks passed." -ForegroundColor Green
