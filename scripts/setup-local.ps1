$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$Root = Get-CrmRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$VenvPython = Join-Path $Backend ".venv\Scripts\python.exe"

if ((Test-Path (Join-Path $Backend ".env")) -or (Test-Path (Join-Path $Backend "crm.db"))) {
    Write-Host "Existing Enterprise CRM local state detected." -ForegroundColor Yellow
    Write-Host "Switching to the safe in-place upgrade workflow..." -ForegroundColor DarkGray
    & (Join-Path $PSScriptRoot "upgrade-existing.ps1")
    exit $LASTEXITCODE
}

Require-Command "npm"
$null = Get-PythonLauncher

$createdBackendEnv = $false

Write-Host "[1/7] Preparing backend environment..." -ForegroundColor Cyan
if (-not (Test-Path $VenvPython)) {
    Invoke-SystemPython -Arguments @("-m", "venv", (Join-Path $Backend ".venv"))
}

Write-Host "[2/7] Installing backend dependencies..." -ForegroundColor Cyan
& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }
Push-Location $Backend
try {
    & $VenvPython -m pip install -e ".[dev]"
    if ($LASTEXITCODE -ne 0) { throw "Backend dependency installation failed." }
} finally { Pop-Location }

$BackendEnv = Join-Path $Backend ".env"
if (-not (Test-Path $BackendEnv)) {
    Write-Host "[3/7] Creating safe local backend configuration..." -ForegroundColor Cyan
    $jwtSecret = New-RandomSecret
    $organizationId = [guid]::NewGuid().ToString()
    $adminPassword = New-AdminPassword
    $createdBackendEnv = $true
    $backendEnvContent = @"
DATABASE_URL=sqlite:///./crm.db
ENVIRONMENT=development
DEFAULT_ORGANIZATION_ID=$organizationId
DEFAULT_ORGANIZATION_NAME=Enterprise CRM
ALLOW_SELF_REGISTRATION=false
ATTACHMENT_STORAGE_BACKEND=local
ATTACHMENT_LOCAL_STORAGE_PATH=.attachments
ATTACHMENT_MAX_UPLOAD_BYTES=10485760
IMPORT_EXPORT_MAX_UPLOAD_BYTES=5242880
IMPORT_EXPORT_MAX_ROWS=5000
HTTP_MAX_REQUEST_BYTES=26214400
DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=$adminPassword
DEFAULT_ADMIN_FIRST_NAME=Admin
DEFAULT_ADMIN_LAST_NAME=User
JWT_SECRET=$jwtSecret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_ISSUER=enterprise-crm
JWT_AUDIENCE=enterprise-crm-api
OLLAMA_ENABLED=true
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=gemma3:4b
OLLAMA_TIMEOUT_SECONDS=60
"@
    [System.IO.File]::WriteAllText($BackendEnv, $backendEnvContent, (New-Object System.Text.UTF8Encoding($false)))
} else {
    Write-Host "[3/7] Existing backend/.env kept unchanged." -ForegroundColor DarkGray
}

Write-Host "[4/7] Applying database migrations and idempotent development seed..." -ForegroundColor Cyan
Push-Location $Backend
try {
    & $VenvPython -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw "Alembic migration failed." }
    & $VenvPython -m app.scripts.seed_development
    if ($LASTEXITCODE -ne 0) { throw "Development seed failed." }
} finally { Pop-Location }

Write-Host "[5/7] Installing frontend dependencies..." -ForegroundColor Cyan
Push-Location $Frontend
try {
    & npm ci
    if ($LASTEXITCODE -ne 0) { throw "Frontend dependency installation failed." }
} finally { Pop-Location }

$FrontendEnv = Join-Path $Frontend ".env.local"
if (-not (Test-Path $FrontendEnv)) {
    $frontendEnvContent = @"
NEXT_PUBLIC_API_BASE_URL=/api
BACKEND_API_URL=http://127.0.0.1:8000/api/v1
BACKEND_API_TIMEOUT_MS=10000
AUTH_REFRESH_TOKEN_MAX_AGE_SECONDS=604800
"@
    [System.IO.File]::WriteAllText($FrontendEnv, $frontendEnvContent, (New-Object System.Text.UTF8Encoding($false)))
}

Write-Host "[6/7] Running backend release checks..." -ForegroundColor Cyan
Push-Location $Backend
try {
    & $VenvPython -m compileall -q app migrations tests
    if ($LASTEXITCODE -ne 0) { throw "Backend compile check failed." }
    & $VenvPython -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw "Backend tests failed." }
    & $VenvPython -m alembic check
    if ($LASTEXITCODE -ne 0) { throw "Alembic model/migration check failed." }
} finally { Pop-Location }

Write-Host "[7/7] Setup complete." -ForegroundColor Green
Write-Host ""
if ($createdBackendEnv) {
    Write-Host "Development login:" -ForegroundColor Yellow
    Write-Host "  Email:    admin@example.com"
    Write-Host "  Password: $adminPassword"
    Write-Host ""
}
Write-Host "Next: double-click run-local.cmd" -ForegroundColor Green
