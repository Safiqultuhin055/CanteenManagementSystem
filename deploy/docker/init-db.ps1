# Initialize CanteenManagementDB on shared SQL Server (default 192.168.153.248)
param(
    [string]$SqlHost = "192.168.153.248",
    [string]$SqlUser = "sa",
    [string]$SqlPassword = "@Mis#Dev",
    [string]$SqlContainer = "deploy-sqlserver-1"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$DbRoot = Join-Path $Root "database"
$DockerSql = Join-Path $PSScriptRoot "01_create_database_docker.sql"

function Get-SqlCmdRunner {
    param([string]$Container)
    $running = docker ps --format "{{.Names}}" | Select-String -Pattern "^$([regex]::Escape($Container))$" -Quiet
    if ($running) {
        return @{ Mode = "exec"; Container = $Container }
    }
    return @{ Mode = "run" }
}

function Invoke-RemoteSqlQuery {
    param([string]$Query)
    $runner = Get-SqlCmdRunner -Container $SqlContainer
    if ($runner.Mode -eq "exec") {
        docker exec $runner.Container /opt/mssql-tools18/bin/sqlcmd `
            -S $SqlHost -U $SqlUser -P $SqlPassword -C -h -1 -W -Q $Query
    } else {
        docker run --rm mcr.microsoft.com/mssql/server:2022-latest `
            /opt/mssql-tools18/bin/sqlcmd -S $SqlHost -U $SqlUser -P $SqlPassword -C -h -1 -W -Q $Query
    }
}

function Test-CmsDatabaseReady {
    $query = "SET NOCOUNT ON; IF DB_ID(N'CanteenManagementDB') IS NULL SELECT 0 ELSE IF OBJECT_ID(N'dbo.users', N'U') IS NULL SELECT 0 ELSE SELECT 1"
    $out = Invoke-RemoteSqlQuery -Query $query 2>$null
    return ($out -match '^\s*1\s*$')
}

function Invoke-SqlFile {
    param(
        [string]$Path,
        [switch]$Optional
    )
    if (-not (Test-Path $Path)) {
        Write-Warning "Skip missing: $Path"
        return
    }
    $leaf = Split-Path $Path -Leaf
    Write-Host "  -> $leaf" -ForegroundColor Gray
    $runner = Get-SqlCmdRunner -Container $SqlContainer
    if ($runner.Mode -eq "exec") {
        $remote = "/tmp/cms-$leaf"
        docker cp $Path "$($runner.Container):$remote" | Out-Null
        docker exec $runner.Container /opt/mssql-tools18/bin/sqlcmd `
            -S $SqlHost -U $SqlUser -P $SqlPassword -C -I -x -b -i $remote
    } else {
        $mount = ($Path -replace '\\', '/')
        docker run --rm -v "${DbRoot}:/db:ro" -v "${PSScriptRoot}:/boot:ro" mcr.microsoft.com/mssql/server:2022-latest `
            /opt/mssql-tools18/bin/sqlcmd -S $SqlHost -U $SqlUser -P $SqlPassword -C -I -x -b -i "/boot/$leaf"
    }
    if ($LASTEXITCODE -ne 0) {
        if ($Optional) {
            Write-Warning "Optional script failed (continuing): $Path"
        } else {
            throw "SQL failed: $Path"
        }
    }
}

if (Test-CmsDatabaseReady) {
    Write-Host "CanteenManagementDB on $SqlHost already initialized - skipping SQL scripts." -ForegroundColor Green
    exit 0
}

Write-Host "=== Initializing CanteenManagementDB on $SqlHost ===" -ForegroundColor Cyan

Invoke-SqlFile $DockerSql

$scripts = @(
    "02_security_users_tables.sql",
    "03_employee_tables.sql",
    "04_food_inventory_tables.sql",
    "05_balance_credit_tables.sql",
    "06_sales_pos_tables.sql",
    "06b_employee_request_tables.sql",
    "07_system_monitoring_tables.sql",
    "08_indexes.sql",
    "09_seed_data.sql",
    "13_menu_permissions_and_help.sql",
    "Speed_data.sql",
    "10_stored_procedures_part1.sql",
    "10_stored_procedures_part2.sql",
    "10_stored_procedures_part3.sql",
    "11_views.sql",
    "11_views_part2.sql",
    "12_sample_transactions.sql",
    "14_fix_menu_urls.sql",
    "15_settings_menu_children.sql",
    "16_user_permissions.sql",
    "17_menu_permissions_complete.sql",
    "18_user_menu_grants.sql",
    "19_receipt_pos_settings.sql",
    "20_menu_item_image_path.sql",
    "21_report_submenus.sql"
)

$optionalScripts = @(
    "Speed_data.sql",
    "12_sample_transactions.sql"
)

foreach ($name in $scripts) {
    $path = Join-Path $DbRoot $name
    if ($optionalScripts -contains $name) {
        Invoke-SqlFile $path -Optional
    } else {
        Invoke-SqlFile $path
    }
}

Write-Host "Database initialized on $SqlHost." -ForegroundColor Green
