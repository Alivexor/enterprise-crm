$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$Root = Get-CrmRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$VenvPython = Join-Path $Backend ".venv\Scripts\python.exe"
$Runtime = Join-Path $Root ".runtime"
$PidFile = Join-Path $Runtime "processes.txt"

if (-not (Test-Path $VenvPython)) { throw "Backend environment is missing. Run setup-local.cmd or upgrade-existing.cmd first." }
if (-not (Test-Path (Join-Path $Frontend "node_modules"))) { throw "Frontend dependencies are missing. Run setup-local.cmd or upgrade-existing.cmd first." }
if (-not (Test-Path (Join-Path $Backend ".env"))) { throw "backend/.env is missing. Run setup-local.cmd first." }
if (-not (Test-Path (Join-Path $Frontend ".env.local"))) { throw "frontend/.env.local is missing. Run setup-local.cmd first." }

$backendReady = Wait-HttpOk -Url "http://127.0.0.1:8000/api/v1/health/ready" -TimeoutSeconds 1
$frontendReady = Wait-HttpOk -Url "http://127.0.0.1:3000/login" -TimeoutSeconds 1
if ($backendReady -and $frontendReady) {
    Write-Host "Enterprise CRM is already running." -ForegroundColor Green
    Start-Process "http://localhost:3000/login"
    exit 0
}
if (Test-TcpPort -Port 8000) { throw "Port 8000 is already in use by another process." }
if (Test-TcpPort -Port 3000) { throw "Port 3000 is already in use by another process." }

New-Item -ItemType Directory -Force -Path $Runtime | Out-Null
$backendCommand = "Set-Location '$Backend'; & '$VenvPython' -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
$frontendCommand = "Set-Location '$Frontend'; npm run dev"
$workerCommand = "Set-Location '$Backend'; & '$VenvPython' -m app.scripts.run_worker"

$backendProcess = Start-Process powershell -PassThru -ArgumentList "-NoExit", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $backendCommand
Start-Sleep -Seconds 1
$frontendProcess = Start-Process powershell -PassThru -ArgumentList "-NoExit", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $frontendCommand
Start-Sleep -Seconds 1
$workerProcess = Start-Process powershell -PassThru -ArgumentList "-NoExit", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $workerCommand
@($backendProcess.Id, $frontendProcess.Id, $workerProcess.Id) | Set-Content -LiteralPath $PidFile -Encoding ascii

Write-Host "Starting Enterprise CRM..." -ForegroundColor Cyan
$backendOk = Wait-HttpOk -Url "http://127.0.0.1:8000/api/v1/health/ready" -TimeoutSeconds 60
$frontendOk = Wait-HttpOk -Url "http://127.0.0.1:3000/login" -TimeoutSeconds 60
$workerOk = $null -ne (Get-Process -Id $workerProcess.Id -ErrorAction SilentlyContinue)

if (-not $backendOk -or -not $frontendOk -or -not $workerOk) {
    Write-Host "Startup did not become healthy in time." -ForegroundColor Red
    Write-Host "Backend ready: $backendOk | Frontend ready: $frontendOk | Worker running: $workerOk"
    Write-Host "Stopping the process trees started by this launcher..." -ForegroundColor Yellow
    foreach ($processId in @($backendProcess.Id, $frontendProcess.Id, $workerProcess.Id)) {
        if (Get-Process -Id $processId -ErrorAction SilentlyContinue) {
            & taskkill.exe /PID $processId /T /F | Out-Null
        }
    }
    Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
    Write-Host "Check the server-window output above for the exact startup error." -ForegroundColor Yellow
    exit 1
}

Write-Host "Enterprise CRM is ready." -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000"
Write-Host "Backend:  http://localhost:8000"
Write-Host "API docs: http://localhost:8000/docs"
Write-Host "Worker:   background sequences + webhooks"
Start-Process "http://localhost:3000/login"
