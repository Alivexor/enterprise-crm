$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$Root = Get-CrmRoot
$PidFile = Join-Path $Root ".runtime\processes.txt"

$pids = if (Test-Path $PidFile) {
    Get-Content -LiteralPath $PidFile | Where-Object { $_ -match '^\d+$' }
} else {
    @()
}

# Also support a CRM instance started from the project directory without the
# launcher PID file. Never stop an unrelated process that merely uses a port.
function Test-IsCrmProcess {
    param([Parameter(Mandatory = $true)][int]$ProcessId)

    $currentId = $ProcessId
    for ($depth = 0; $depth -lt 6 -and $currentId -gt 0; $depth++) {
        $current = Get-CimInstance Win32_Process -Filter "ProcessId = $currentId" -ErrorAction SilentlyContinue
        if ($null -eq $current) { return $false }
        if ($current.CommandLine -and $current.CommandLine.Contains($Root)) { return $true }
        $currentId = $current.ParentProcessId
    }
    return $false
}

foreach ($port in 8000, 3000) {
    foreach ($connection in Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
        if (Test-IsCrmProcess -ProcessId $connection.OwningProcess) {
            $pids += [string]$connection.OwningProcess
        }
    }
}

$pids = @($pids | Select-Object -Unique)
if ($pids.Count -eq 0) {
    Write-Host "No running Enterprise CRM process was found." -ForegroundColor Yellow
    exit 0
}

foreach ($pidValue in $pids) {
    $pidNumber = [int]$pidValue
    $process = Get-Process -Id $pidNumber -ErrorAction SilentlyContinue
    if ($null -ne $process) {
        Write-Host "Stopping process tree $pidNumber..." -ForegroundColor Cyan
        & taskkill.exe /PID $pidNumber /T /F | Out-Null
    }
}
Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
Write-Host "Enterprise CRM local processes stopped." -ForegroundColor Green
