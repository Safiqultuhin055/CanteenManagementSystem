# Quick IIS / Django diagnostics. Run from project root:
#   powershell -ExecutionPolicy Bypass -File .\deploy\iis\diagnose_iis.ps1

$ErrorActionPreference = 'Continue'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $Root

Write-Host "=== Canteen CMS IIS diagnose ===" -ForegroundColor Cyan
Write-Host "Project: $Root"

$py = Join-Path $Root 'venv\Scripts\python.exe'
if (-not (Test-Path $py)) {
    Write-Host 'FAIL: venv missing. Run prepare_iis.ps1 first.' -ForegroundColor Red
    exit 1
}

Write-Host "`n[1] Python + Django"
& $py --version
& $py manage.py check

Write-Host "`n[2] web.config"
$wc = Join-Path $Root 'web.config'
if (Test-Path $wc) { Get-Content $wc | Select-String 'processPath|FORCE_SCRIPT_NAME' }
else { Write-Host 'FAIL: web.config not found' -ForegroundColor Red }

Write-Host "`n[3] HttpPlatformHandler (IIS module)"
try {
    Import-Module WebAdministration -ErrorAction Stop
    $hp = Get-WebGlobalModule -Name 'httpPlatformHandler' -ErrorAction SilentlyContinue
    if ($hp) { Write-Host 'OK: httpPlatformHandler installed' -ForegroundColor Green }
    else { Write-Host 'MISSING: Install HttpPlatformHandler (IIS download)' -ForegroundColor Red }
} catch {
    Write-Host 'Could not query IIS modules (run as Admin?):' $_.Exception.Message -ForegroundColor Yellow
}

Write-Host "`n[4] Recent logs"
@('logs\iis_stdout*.log', 'logs\iis_boot.log', 'logs\django.log') | ForEach-Object {
    Get-ChildItem (Join-Path $Root $_) -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | ForEach-Object {
        Write-Host "--- $($_.Name) ---"
        Get-Content $_.FullName -Tail 15
    }
}

Write-Host "`n[5] URLs to try"
Write-Host '  http://localhost/cms/'
Write-Host '  http://localhost/cms/dashboard/'
Write-Host '  http://localhost/cms/users/login/'
