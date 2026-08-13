$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$Root = Get-CrmRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$VenvPython = Join-Path $Backend ".venv\Scripts\python.exe"

Require-Command "npm"
$null = Get-PythonLauncher

if ((Test-TcpPort -Port 8000) -or (Test-TcpPort -Port 3000)) {
    throw "Port 8000 or 3000 is currently in use. Close the running CRM first (use stop-local.cmd when applicable), then run this upgrade again."
}

Write-Host "Enterprise CRM in-place upgrade" -ForegroundColor Cyan
Write-Host "This preserves your local .env files, SQLite database, and attachments." -ForegroundColor DarkGray

Write-Host "[1/8] Backing up local configuration/database..." -ForegroundColor Cyan
$backup = New-LocalBackup -Root $Root
Write-Host "Backup: $backup" -ForegroundColor DarkGray

Write-Host "[2/8] Preparing Python environment..." -ForegroundColor Cyan
if (-not (Test-Path $VenvPython)) {
    Invoke-SystemPython -Arguments @("-m", "venv", (Join-Path $Backend ".venv"))
}
& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }
Push-Location $Backend
try {
    & $VenvPython -m pip install -e ".[dev]"
    if ($LASTEXITCODE -ne 0) { throw "Backend dependency sync failed." }
} finally { Pop-Location }

Write-Host "[3/8] Upgrading local environment files without replacing existing values..." -ForegroundColor Cyan
$BackendEnv = Join-Path $Backend ".env"
if (Test-Path $BackendEnv) {
    $duplicates = @(Normalize-EnvFile -Path $BackendEnv)
    if ($duplicates.Count -gt 0) {
        Write-Host "Removed duplicate backend env keys while preserving their effective (last) values: $($duplicates -join ' , ')" -ForegroundColor DarkGray
    }

    # V3.0.1: migrate only the previous bundled default model. Custom user-selected models are preserved.
    $envLines = @(Get-Content -LiteralPath $BackendEnv)
    $migratedOllamaModel = $false
    for ($i = 0; $i -lt $envLines.Count; $i++) {
        if ($envLines[$i] -match '^\s*OLLAMA_MODEL\s*=\s*qwen3:4b\s*$') {
            $envLines[$i] = "OLLAMA_MODEL=gemma3:4b"
            $migratedOllamaModel = $true
        }
    }
    if ($migratedOllamaModel) {
        Write-Utf8NoBom -Path $BackendEnv -Content (($envLines -join "`r`n") + "`r`n")
        Write-Host "Updated the previous bundled Ollama default from qwen3:4b to gemma3:4b. Custom model selections are preserved." -ForegroundColor DarkGray
    }
}
if (-not (Test-Path $BackendEnv)) {
    $jwtSecret = New-RandomSecret
    $adminPassword = New-AdminPassword
    $organizationId = [guid]::NewGuid().ToString()
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
    Write-Utf8NoBom -Path $BackendEnv -Content ($backendEnvContent + "`r`n")
    Write-Host "Created backend/.env with a new development admin credential." -ForegroundColor Yellow
    Write-Host "  Email: admin@example.com"
    Write-Host "  Password: $adminPassword"
} else {
    $generatedAdminPassword = New-AdminPassword
    $backendDefaults = [ordered]@{
        DATABASE_URL = "sqlite:///./crm.db"
        ENVIRONMENT = "development"
        DEFAULT_ORGANIZATION_ID = ([guid]::NewGuid().ToString())
        DEFAULT_ORGANIZATION_NAME = "Enterprise CRM"
        ALLOW_SELF_REGISTRATION = "false"
        ATTACHMENT_STORAGE_BACKEND = "local"
        ATTACHMENT_LOCAL_STORAGE_PATH = ".attachments"
        ATTACHMENT_MAX_UPLOAD_BYTES = "10485760"
        IMPORT_EXPORT_MAX_UPLOAD_BYTES = "5242880"
        IMPORT_EXPORT_MAX_ROWS = "5000"
        HTTP_MAX_REQUEST_BYTES = "26214400"
        DEFAULT_ADMIN_EMAIL = "admin@example.com"
        DEFAULT_ADMIN_PASSWORD = $generatedAdminPassword
        DEFAULT_ADMIN_FIRST_NAME = "Admin"
        DEFAULT_ADMIN_LAST_NAME = "User"
        JWT_SECRET = (New-RandomSecret)
        JWT_ALGORITHM = "HS256"
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES = "15"
        JWT_REFRESH_TOKEN_EXPIRE_DAYS = "7"
        JWT_ISSUER = "enterprise-crm"
        JWT_AUDIENCE = "enterprise-crm-api"
        OLLAMA_ENABLED = "true"
        OLLAMA_BASE_URL = "http://127.0.0.1:11434"
        OLLAMA_MODEL = "gemma3:4b"
        OLLAMA_TIMEOUT_SECONDS = "60"
    }
    $added = @(Add-MissingEnvEntries -Path $BackendEnv -Entries $backendDefaults)
    if ($added.Count -gt 0) {
        Write-Host "Added $($added.Count) missing backend setting(s); existing values were preserved." -ForegroundColor DarkGray
        if ($added -match '^DEFAULT_ADMIN_PASSWORD=') {
            Write-Host "A missing local admin password setting was generated: $generatedAdminPassword" -ForegroundColor Yellow
        }
    }
}

$FrontendEnv = Join-Path $Frontend ".env.local"
if (Test-Path $FrontendEnv) { $null = Normalize-EnvFile -Path $FrontendEnv }
if (-not (Test-Path $FrontendEnv)) {
    $frontendEnvContent = @"
NEXT_PUBLIC_API_BASE_URL=/api
BACKEND_API_URL=http://127.0.0.1:8000/api/v1
BACKEND_API_TIMEOUT_MS=10000
AUTH_REFRESH_TOKEN_MAX_AGE_SECONDS=604800
"@
    Write-Utf8NoBom -Path $FrontendEnv -Content ($frontendEnvContent + "`r`n")
} else {
    $frontendDefaults = [ordered]@{
        NEXT_PUBLIC_API_BASE_URL = "/api"
        BACKEND_API_URL = "http://127.0.0.1:8000/api/v1"
        BACKEND_API_TIMEOUT_MS = "10000"
        AUTH_REFRESH_TOKEN_MAX_AGE_SECONDS = "604800"
    }
    $null = Add-MissingEnvEntries -Path $FrontendEnv -Entries $frontendDefaults
}

Write-Host "[4/8] Applying migrations and seed..." -ForegroundColor Cyan
Push-Location $Backend
try {
    & $VenvPython -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw "Database migration failed. Your pre-upgrade backup is at $backup" }
    & $VenvPython -m app.scripts.seed_development
    if ($LASTEXITCODE -ne 0) { throw "Development seed failed." }
} finally { Pop-Location }

Write-Host "[5/8] Synchronizing frontend dependencies..." -ForegroundColor Cyan
$nextOutput = Join-Path $Frontend ".next"
if (Test-Path $nextOutput) {
    Remove-Item -LiteralPath $nextOutput -Recurse -Force
}
Push-Location $Frontend
try {
    & npm ci
    if ($LASTEXITCODE -ne 0) { throw "Frontend dependency sync failed." }
} finally { Pop-Location }

Write-Host "[6/8] Validating backend..." -ForegroundColor Cyan
Push-Location $Backend
try {
    & $VenvPython -m compileall -q app migrations tests
    if ($LASTEXITCODE -ne 0) { throw "Backend compile failed." }
    & $VenvPython -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw "Backend tests failed." }
    & $VenvPython -m alembic current
    if ($LASTEXITCODE -ne 0) { throw "Alembic current failed." }
    & $VenvPython -m alembic check
    if ($LASTEXITCODE -ne 0) { throw "Alembic drift check failed." }
    & $VenvPython -m app.scripts.run_worker --once
    if ($LASTEXITCODE -ne 0) { throw "Background worker smoke test failed." }
} finally { Pop-Location }

Write-Host "[7/8] Validating frontend..." -ForegroundColor Cyan
Push-Location $Frontend
try {
    & npm run lint
    if ($LASTEXITCODE -ne 0) { throw "Frontend lint failed." }
    & npm run typecheck
    if ($LASTEXITCODE -ne 0) { throw "Frontend typecheck failed." }
    & npm run build
    if ($LASTEXITCODE -ne 0) { throw "Frontend production build failed." }
} finally { Pop-Location }

Write-Host "[8/8] Upgrade and validation complete." -ForegroundColor Green
Write-Host "Your previous local state backup is available at:" -ForegroundColor DarkGray
Write-Host "  $backup"
Write-Host ""
Write-Host "Next: double-click run-local.cmd" -ForegroundColor Green
