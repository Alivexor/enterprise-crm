Set-StrictMode -Version Latest

function Get-CrmRoot {
    return (Split-Path -Parent $PSScriptRoot)
}

function Get-PythonLauncher {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @{ Command = "py"; Prefix = @("-3") }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @{ Command = "python"; Prefix = @() }
    }
    throw "Python 3.11+ was not found. Install Python and make sure 'py' or 'python' is available in PATH."
}

function Invoke-SystemPython {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    $launcher = Get-PythonLauncher
    $allArgs = @($launcher.Prefix) + $Arguments
    & $launcher.Command @allArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code $LASTEXITCODE."
    }
}

function Require-Command {
    param([Parameter(Mandatory = $true)][string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "'$Name' was not found in PATH. Install it and run this script again."
    }
}

function Test-TcpPort {
    param(
        [string]$HostName = "127.0.0.1",
        [Parameter(Mandatory = $true)][int]$Port,
        [int]$TimeoutMs = 350
    )
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $async = $client.BeginConnect($HostName, $Port, $null, $null)
        if (-not $async.AsyncWaitHandle.WaitOne($TimeoutMs, $false)) {
            return $false
        }
        $client.EndConnect($async)
        return $true
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

function Wait-HttpOk {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [int]$TimeoutSeconds = 60
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
                return $true
            }
        } catch {
            Start-Sleep -Milliseconds 750
        }
    }
    return $false
}

function New-RandomSecret {
    param([int]$Bytes = 48)
    $buffer = New-Object byte[] $Bytes
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $rng.GetBytes($buffer)
    } finally {
        $rng.Dispose()
    }
    return [Convert]::ToBase64String($buffer)
}

function New-AdminPassword {
    $value = (New-RandomSecret -Bytes 18).Replace("/", "A").Replace("+", "B").Replace("=", "C")
    return "$value!a1"
}

function Get-EnvKeys {
    param([Parameter(Mandatory = $true)][string]$Path)
    $keys = @{}
    if (-not (Test-Path $Path)) { return $keys }
    foreach ($line in Get-Content -LiteralPath $Path) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=') {
            $keys[$Matches[1]] = $true
        }
    }
    return $keys
}

function Add-MissingEnvEntries {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][System.Collections.Specialized.OrderedDictionary]$Entries
    )
    $keys = Get-EnvKeys -Path $Path
    $missing = @()
    foreach ($entry in $Entries.GetEnumerator()) {
        if (-not $keys.ContainsKey([string]$entry.Key)) {
            $missing += "$($entry.Key)=$($entry.Value)"
        }
    }
    if ($missing.Count -gt 0) {
        $existingContent = [System.IO.File]::ReadAllText($Path)
        if ($existingContent.Length -gt 0 -and -not $existingContent.EndsWith("`n")) {
            $existingContent += "`r`n"
        }
        $appendBlock = "`r`n# Added automatically by the Enterprise CRM upgrade script`r`n" + ($missing -join "`r`n") + "`r`n"
        Write-Utf8NoBom -Path $Path -Content ($existingContent + $appendBlock)
    }
    return $missing
}


function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )
    [System.IO.File]::WriteAllText($Path, $Content, (New-Object System.Text.UTF8Encoding($false)))
}

function Normalize-EnvFile {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path $Path)) { return @() }
    $lines = @(Get-Content -LiteralPath $Path)
    $lastIndex = @{}
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=') {
            $lastIndex[$Matches[1]] = $i
        }
    }
    $duplicates = @{}
    $seen = @{}
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=') {
            $key = $Matches[1]
            if ($seen.ContainsKey($key)) { $duplicates[$key] = $true }
            $seen[$key] = $true
        }
    }
    if ($duplicates.Count -eq 0) { return @() }
    $output = @()
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=') {
            $key = $Matches[1]
            if ($lastIndex[$key] -ne $i) { continue }
        }
        $output += $lines[$i]
    }
    Write-Utf8NoBom -Path $Path -Content (($output -join "`r`n") + "`r`n")
    return @($duplicates.Keys)
}

function New-LocalBackup {
    param([Parameter(Mandatory = $true)][string]$Root)
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backup = Join-Path $Root ".upgrade-backups\$stamp"
    New-Item -ItemType Directory -Force -Path $backup | Out-Null

    $candidates = @(
        @{ Source = (Join-Path $Root "backend\.env"); Destination = "backend.env" },
        @{ Source = (Join-Path $Root "frontend\.env.local"); Destination = "frontend.env.local" },
        @{ Source = (Join-Path $Root "backend\crm.db"); Destination = "crm.db" }
    )
    foreach ($item in $candidates) {
        if (Test-Path $item.Source) {
            Copy-Item -LiteralPath $item.Source -Destination (Join-Path $backup $item.Destination) -Force
        }
    }
    return $backup
}
