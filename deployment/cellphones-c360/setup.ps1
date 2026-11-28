
param(
    [ValidateSet("Snapshot", "New", "Update", "Verify")]
    [string]$Mode = "Snapshot",
    [string]$Site = "crm.localhost",
    [string]$Container = "crm-frappe-1",
    [string]$ProjectName = "cellphones-c360-source",
    [switch]$ApplyDepartmentRoles
)

if ($Mode -ne "Snapshot") {
    & (Join-Path $PSScriptRoot "setup-source.ps1") -Mode $Mode -Site $Site -Container $Container -ProjectName $ProjectName -ApplyDepartmentRoles:$ApplyDepartmentRoles
    return
}

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Read MariaDB root password from .env
$envFile = Join-Path $PSScriptRoot ".env"

if (-not (Test-Path $envFile)) {
    throw "Missing .env file. Copy .env.example to .env and configure MYSQL_ROOT_PASSWORD."
}

$passwordLine = Get-Content $envFile |
    Where-Object { $_ -match '^\s*MYSQL_ROOT_PASSWORD=' } |
    Select-Object -Last 1

if (-not $passwordLine) {
    throw "MYSQL_ROOT_PASSWORD is missing in .env."
}

$dbRootPassword = ($passwordLine -split '=', 2)[1].Trim().Trim('"', "'")

if ([string]::IsNullOrWhiteSpace($dbRootPassword) -or $dbRootPassword -eq "CHANGE_ME") {
    throw "Set a valid MYSQL_ROOT_PASSWORD in .env."
}

$env:MYSQL_ROOT_PASSWORD = $dbRootPassword

$projectName = (docker compose config --format json | ConvertFrom-Json).name

if ($LASTEXITCODE -ne 0 -or -not $projectName) {
    throw "Cannot determine Docker Compose project name."
}

$helperName = "$projectName-setup-helper"
function Run-Docker {
    & docker @args

    if ($LASTEXITCODE -ne 0) {
        throw "Docker command failed. Exit code: $LASTEXITCODE"
    }
}

Write-Host "=== CellphoneS C360 Snapshot Setup ==="

# Prevent overwriting an existing snapshot installation
$existing = docker compose ps -a --format json
if ($LASTEXITCODE -ne 0) {
    throw "Cannot inspect Docker Compose."
}
if ($existing) {
    throw "Snapshot containers already exist. Setup is only for a fresh installation."
}

# Check required files
$required = @(
    "frappe-bench-backup.tar.gz",
    "Dockerfile",
    "docker-compose.yml",
    "../../backend/cellphones_c360"
)
foreach ($item in $required) {
    if (-not (Test-Path $item)) {
        throw "Missing: $item"
    }
}

$dbBackup = Get-ChildItem ".\backup\20261122_225223-*-database.sql.gz" | Select-Object -First 1
$publicBackup = Get-ChildItem ".\backup\20261122_225223-*-files.tar" | Select-Object -First 1
$privateBackup = Get-ChildItem ".\backup\20261122_225223-*-private-files.tar" | Select-Object -First 1
$configBackup = Get-ChildItem ".\backup\20261122_225223-*-site_config_backup.json" | Select-Object -First 1

if (-not ($dbBackup -and $publicBackup -and $privateBackup -and $configBackup)) {
    throw "Missing one or more November 22 backup files."
}

# Build the Frappe image before creating the helper container
Write-Host "Building Frappe Docker image..."
Run-Docker compose build frappe

# Start MariaDB and Redis
Write-Host "Starting MariaDB and Redis..."
Run-Docker compose up -d mariadb redis

# Wait for database readiness
Write-Host "Waiting for MariaDB..."
$ready = $false

for ($i = 0; $i -lt 60; $i++) {
    & docker compose exec -T `
        -e "MYSQL_PWD=$dbRootPassword" `
        mariadb `
        mariadb-admin ping -h 127.0.0.1 -uroot --silent 2>$null | Out-Null

    if ($LASTEXITCODE -eq 0) {
        $ready = $true
        break
    }

    Start-Sleep -Seconds 2
}

if (-not $ready) {
    throw "MariaDB did not become ready."
}

# Initialize database and Frappe database user
Write-Host "Initializing Frappe database..."

$config = Get-Content $configBackup.FullName -Raw | ConvertFrom-Json

$dbName = [string]$config.db_name
$dbPassword = [string]$config.db_password

if ($dbName -notmatch '^[A-Za-z0-9_]+$') {
    throw "Invalid database name."
}

# Escape single quotes and backslashes for SQL string literals
$escapedPassword = $dbPassword.Replace('\', '\\').Replace("'", "''")

$sql = @"
CREATE DATABASE IF NOT EXISTS ``$dbName`` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$dbName'@'%' IDENTIFIED BY '$escapedPassword';
ALTER USER '$dbName'@'%' IDENTIFIED BY '$escapedPassword';
GRANT ALL PRIVILEGES ON ``$dbName``.* TO '$dbName'@'%';
FLUSH PRIVILEGES;
"@

$sql | docker compose exec -T `
    -e "MYSQL_PWD=$dbRootPassword" `
    mariadb `
    mariadb -uroot
if ($LASTEXITCODE -ne 0) {
    throw "Database initialization failed."
}

Write-Host "Database initialized."

# Create a temporary container for Bench restoration
Run-Docker compose run -d --no-deps --name $helperName --entrypoint sleep frappe infinity

try {
    Run-Docker cp ".\frappe-bench-backup.tar.gz" "${helperName}:/home/frappe/bench.tar.gz"

    Run-Docker exec -u root $helperName bash -lc "cd /home/frappe && tar -xzf bench.tar.gz --exclude='frappe-bench/apps/cellphones_c360' --no-same-owner && chown -R frappe:frappe /home/frappe/frappe-bench"

    Run-Docker exec $helperName mkdir -p /home/frappe/frappe-bench/restore-backup

    Run-Docker cp $dbBackup.FullName "${helperName}:/home/frappe/frappe-bench/restore-backup/database.sql.gz"
    Run-Docker cp $publicBackup.FullName "${helperName}:/home/frappe/frappe-bench/restore-backup/files.tar"
    Run-Docker cp $privateBackup.FullName "${helperName}:/home/frappe/frappe-bench/restore-backup/private-files.tar"
    Run-Docker cp $configBackup.FullName "${helperName}:/home/frappe/frappe-bench/restore-backup/site_config_backup.json"

    # Give the Frappe user access to restored backup files
    Run-Docker exec -u root $helperName chown -R frappe:frappe /home/frappe/frappe-bench/restore-backup
    # Build a SQL file compatible with MariaDB 10.8
    $fixSql = @'
import gzip
from pathlib import Path

base = Path("/home/frappe/frappe-bench/restore-backup")
with gzip.open(base / "database.sql.gz", "rt", encoding="utf-8") as src:
    with (base / "compatible.sql").open("w", encoding="utf-8") as dst:
        for line in src:
            if "NOTE_VERBOSITY" not in line:
                dst.write(line)
'@

    $fixSql | docker exec -i $helperName python -
    if ($LASTEXITCODE -ne 0) { throw "SQL compatibility conversion failed." }

    # Restore site configuration and database using Bench
    $restore = @'
set -e
cd /home/frappe/frappe-bench
cp /home/frappe/frappe-bench/restore-backup/site_config_backup.json sites/crm.localhost/site_config.json
bench --site crm.localhost restore \
  /home/frappe/frappe-bench/restore-backup/compatible.sql \
  --with-public-files /home/frappe/frappe-bench/restore-backup/files.tar \
  --with-private-files /home/frappe/frappe-bench/restore-backup/private-files.tar \
  --db-root-username root \
  --db-root-password "$MYSQL_ROOT_PASSWORD"
'@

$restore = $restore -replace "`r`n", "`n"

$restoreFile = Join-Path $env:TEMP "c360-test-restore.sh"

try {
    [System.IO.File]::WriteAllText(
        $restoreFile,
        $restore,
        (New-Object System.Text.UTF8Encoding($false))
    )

    Run-Docker cp $restoreFile "${helperName}:/tmp/c360-restore.sh"

    Run-Docker exec -u frappe `
        -e PYENV_VERSION=3.12.15 `
        -e "MYSQL_ROOT_PASSWORD=$dbRootPassword" `
        -w /home/frappe/frappe-bench `
        $helperName `
        bash /tmp/c360-restore.sh
}
finally {
    Remove-Item $restoreFile -ErrorAction SilentlyContinue
}

    # Remove temporary restore files after successful restoration
    Run-Docker exec -u root $helperName rm -rf /home/frappe/frappe-bench/restore-backup
    Write-Host "Temporary restore files removed."
}
finally {
    docker rm -f $helperName | Out-Null
}

Run-Docker compose up -d --no-deps --force-recreate frappe

Write-Host ""
Write-Host "========================================"
Write-Host " CellphoneS Customer 360 - Setup Done"
Write-Host "========================================"
$portMapping = docker compose port frappe 8000
if ($LASTEXITCODE -ne 0 -or -not $portMapping) {
    throw "Cannot determine Frappe port."
}

$frappePort = ($portMapping | Select-Object -First 1).Trim() -replace '^.*:', ''

Write-Host "Frappe CRM: http://localhost:$frappePort/crm"
Write-Host "Customer API: http://localhost:$frappePort/api/resource/C360%20Customer"
