# Prepare Canteen CMS for IIS (no Activate.ps1 needed).
# Usage:  .\deploy\iis\prepare_iis.ps1
#         .\deploy\iis\prepare_iis.ps1 -VirtualPath /cms
#         .\deploy\iis\prepare_iis.ps1 -UseGlobalPython   # skip venv (if always locked)

param(
    [string]$VirtualPath = '/cms',
    [switch]$UseGlobalPython,
    [string]$AppPoolName = 'CanteenCMS'
)

$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $Root
Write-Host "Project: $Root" -ForegroundColor Cyan

function Stop-IisWorkers {
    Write-Host 'Stopping IIS app pool (releases locked venv files)...' -ForegroundColor Yellow
    try {
        Import-Module WebAdministration -ErrorAction Stop
        if (Test-Path "IIS:\AppPools\$AppPoolName") {
            Stop-WebAppPool -Name $AppPoolName -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
    } catch {
        Write-Host '  (WebAdministration not available — stop IIS pool manually in IIS Manager)' -ForegroundColor DarkYellow
    }
    Get-Process -Name 'w3wp', 'python' -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -like "$Root*" } |
        Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

function Start-IisWorkers {
    try {
        Import-Module WebAdministration -ErrorAction SilentlyContinue
        if (Test-Path "IIS:\AppPools\$AppPoolName") {
            Start-WebAppPool -Name $AppPoolName -ErrorAction SilentlyContinue
        }
    } catch { }
}

function Test-PythonHasDjango([string]$PythonExe) {
    if (-not (Test-Path $PythonExe)) { return $false }
    $out = & $PythonExe -c "import django; print(django.VERSION)" 2>&1
    return $LASTEXITCODE -eq 0
}

function Install-Requirements([string]$PythonExe) {
    Write-Host "pip install -> $PythonExe" -ForegroundColor DarkGray
    & $PythonExe -m pip install --upgrade pip 2>&1 | Where-Object { $_ -notmatch 'WARNING: Cache entry' }
    & $PythonExe -m pip install -r requirements.txt 2>&1 | Where-Object { $_ -notmatch 'WARNING: Cache entry' }
    return $LASTEXITCODE -eq 0
}

# --- Stop IIS so venv files are not locked ---
Stop-IisWorkers

# --- Resolve Python for IIS ---
$venvPython = Join-Path $Root 'venv\Scripts\python.exe'
$globalPython = (py -3 -c "import sys; print(sys.executable)" 2>$null).Trim()

$iisPython = $null

if ($UseGlobalPython) {
    $iisPython = $globalPython
    Write-Host "Using global Python (-UseGlobalPython): $iisPython" -ForegroundColor Yellow
    Install-Requirements $iisPython | Out-Null
} else {
    if (-not (Test-Path $venvPython)) {
        Write-Host 'Creating venv...' -ForegroundColor Yellow
        py -3 -m venv venv 2>&1 | Out-Null
    }
    if (Test-Path $venvPython) {
        $venvOk = Install-Requirements $venvPython
        if (-not $venvOk) {
            Write-Host 'venv pip failed (often IIS lock). Retrying after stop...' -ForegroundColor Yellow
            Stop-IisWorkers
            $venvOk = Install-Requirements $venvPython
        }
        if ((Test-PythonHasDjango $venvPython)) {
            $iisPython = $venvPython
            Write-Host "IIS Python: venv" -ForegroundColor Green
        }
    }
    if (-not $iisPython) {
        $iisPython = $globalPython
        Write-Host "IIS Python: global (venv unavailable): $iisPython" -ForegroundColor Yellow
        Install-Requirements $iisPython | Out-Null
        if (-not (Test-PythonHasDjango $iisPython)) {
            Write-Host 'ERROR: Django not installed. Run: py -3 -m pip install -r requirements.txt' -ForegroundColor Red
            exit 1
        }
    }
}

Write-Host "Python for IIS: $iisPython" -ForegroundColor Green

# --- Folders ---
@('logs', 'media', 'staticfiles') | ForEach-Object {
    $p = Join-Path $Root $_
    if (-not (Test-Path $p)) { New-Item -ItemType Directory -Path $p | Out-Null }
}

if (-not (Test-Path (Join-Path $Root '.env'))) {
    Copy-Item (Join-Path $Root '.env.example') (Join-Path $Root '.env')
    Write-Host 'Created .env from .env.example' -ForegroundColor Yellow
}

# --- Django publish ---
& $iisPython manage.py publish
if ($LASTEXITCODE -ne 0) {
    Write-Host 'publish failed.' -ForegroundColor Red
    exit 1
}

# --- web.config (UTF-8 without BOM — BOM breaks IIS) ---
& (Join-Path $PSScriptRoot 'Write-WebConfig.ps1') -Root $Root -PythonExe $iisPython -VirtualPath $VirtualPath
Write-Host "Wrote web.config (no BOM)" -ForegroundColor Green

Start-IisWorkers

Write-Host ''
Write-Host 'Prep complete.' -ForegroundColor Green
Write-Host "  Browse: http://localhost$VirtualPath/dashboard/"
Write-Host '  .env:   deploy/iis/env_iis_snippet.txt'
