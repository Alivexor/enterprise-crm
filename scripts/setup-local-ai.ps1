$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $Here "common.ps1")
$RepoRoot = Get-CrmRoot
$BackendEnv = Join-Path $RepoRoot "backend\.env"

Write-Host "Enterprise CRM V3 - Local AI setup" -ForegroundColor Cyan
Write-Host "This uses Ollama on your own computer. No paid AI API key is required." -ForegroundColor DarkGray

$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if ($null -eq $ollama) {
    Write-Host "Ollama was not found on PATH." -ForegroundColor Yellow
    Write-Host "Install Ollama from its official website, reopen this window, then run setup-local-ai.cmd again." -ForegroundColor Yellow
    exit 2
}

Write-Host "[1/3] Checking Ollama..." -ForegroundColor Cyan
& ollama --version
if ($LASTEXITCODE -ne 0) { throw "Ollama is installed but could not be executed." }

Write-Host "[2/3] Checking the default local model gemma3:4b..." -ForegroundColor Cyan
$installedModels = (& ollama list 2>$null | Out-String)
if ($LASTEXITCODE -ne 0) { throw "Ollama is installed but the local model list could not be read." }
if ($installedModels -match '(?m)^gemma3:4b\s') {
    Write-Host "gemma3:4b is already installed; skipping download." -ForegroundColor DarkGray
} else {
    Write-Host "gemma3:4b was not found locally; downloading it now..." -ForegroundColor Cyan
    & ollama pull gemma3:4b
    if ($LASTEXITCODE -ne 0) { throw "The model download failed. Check Ollama/network access and retry." }
}

Write-Host "[3/3] Updating local CRM AI settings if they are missing..." -ForegroundColor Cyan
if (-not (Test-Path $BackendEnv)) {
    Write-Host "backend/.env does not exist yet. Run setup-local.cmd or upgrade-existing.cmd first." -ForegroundColor Yellow
    exit 3
}
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
}

$entries = [ordered]@{
    OLLAMA_ENABLED = "true"
    OLLAMA_BASE_URL = "http://127.0.0.1:11434"
    OLLAMA_MODEL = "gemma3:4b"
    OLLAMA_TIMEOUT_SECONDS = "60"
}
$null = Add-MissingEnvEntries -Path $BackendEnv -Entries $entries

Write-Host "Local AI is ready." -ForegroundColor Green
Write-Host "Start the CRM with run-local.cmd and open Intelligence -> Intelligence center." -ForegroundColor Green
