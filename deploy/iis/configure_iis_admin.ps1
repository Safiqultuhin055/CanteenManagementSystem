# Run as Administrator (right-click PowerShell -> Run as administrator):
#   cd "E:\Python Project\CanteenManagementSystem"
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\deploy\iis\configure_iis_admin.ps1

#Requires -RunAsAdministrator

param(
    [string]$SiteName = 'Default Web Site',
    [string]$AppName = 'cms',
    [string]$AppPoolName = 'CanteenCMS',
    [int]$Port = 80
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $Root

Write-Host "=== Configure IIS for Canteen CMS ===" -ForegroundColor Cyan
Write-Host "Project: $Root"
Write-Host "URL: http://localhost/$AppName/"

# 1) Ensure IIS + HttpPlatformHandler
$w3svc = Get-Service W3SVC -ErrorAction SilentlyContinue
if (-not $w3svc) {
    Write-Host 'IIS not installed. Enable: Windows Features -> Internet Information Services' -ForegroundColor Red
    exit 1
}
if ($w3svc.Status -ne 'Running') {
    Write-Host 'Starting W3SVC...'
    Start-Service W3SVC
}

Import-Module WebAdministration -ErrorAction Stop
$hp = Get-WebGlobalModule -Name 'httpPlatformHandler' -ErrorAction SilentlyContinue
if (-not $hp) {
    Write-Host ''
    Write-Host 'MISSING: HttpPlatformHandler' -ForegroundColor Red
    Write-Host 'Download and install:' -ForegroundColor Yellow
    Write-Host '  https://www.iis.net/downloads/microsoft/httpplatformhandler'
    Write-Host 'Then re-run this script.'
    exit 1
}
Write-Host 'OK: HttpPlatformHandler' -ForegroundColor Green

# 2) App pool (No Managed Code)
if (-not (Test-Path "IIS:\AppPools\$AppPoolName")) {
    Write-Host "Creating app pool $AppPoolName..."
    New-WebAppPool -Name $AppPoolName | Out-Null
}
Set-ItemProperty "IIS:\AppPools\$AppPoolName" -Name managedRuntimeVersion -Value ''
Set-ItemProperty "IIS:\AppPools\$AppPoolName" -Name processModel.identityType -Value 4  # ApplicationPoolIdentity
Write-Host "OK: App pool $AppPoolName (No Managed Code)" -ForegroundColor Green

# 3) Application under Default Web Site
$appPath = "IIS:\Sites\$SiteName\$AppName"
$physicalPath = $Root
if (Test-Path $appPath) {
    Write-Host "Updating existing application /$AppName..."
    Set-ItemProperty $appPath -Name physicalPath -Value $physicalPath
    Set-ItemProperty $appPath -Name applicationPool -Value $AppPoolName
} else {
    Write-Host "Creating application /$AppName..."
    New-WebApplication -Name $AppName -Site $SiteName -PhysicalPath $physicalPath -ApplicationPool $AppPoolName | Out-Null
}

# 4) Folder permissions
Write-Host 'Setting folder permissions...'
$poolSid = 'IIS AppPool\' + $AppPoolName
icacls $Root /grant 'IIS_IUSRS:(OI)(CI)RX' /T /C /Q 2>$null | Out-Null
icacls (Join-Path $Root 'media') /grant ('{0}:(OI)(CI)M' -f $poolSid) /T /C /Q 2>$null | Out-Null
icacls (Join-Path $Root 'logs') /grant ('{0}:(OI)(CI)M' -f $poolSid) /T /C /Q 2>$null | Out-Null
Write-Host 'OK: Permissions' -ForegroundColor Green

# 5) Django prep (no admin needed but run here)
Write-Host ''
Write-Host 'Running Django IIS prep...' -ForegroundColor Cyan
& (Join-Path $PSScriptRoot 'prepare_iis.ps1') -VirtualPath "/$AppName"

# 6) Recycle pool
Restart-WebAppPool -Name $AppPoolName
Write-Host ''
Write-Host '=== IIS configuration complete ===' -ForegroundColor Green
Write-Host "Open: http://localhost/$AppName/dashboard/"
Write-Host "Login: http://localhost/$AppName/users/login/"
Write-Host "TV:    http://localhost/$AppName/distribution/display/"
Write-Host ''
Write-Host 'YOU must still edit .env (see deploy/iis/env_iis_snippet.txt)' -ForegroundColor Yellow
