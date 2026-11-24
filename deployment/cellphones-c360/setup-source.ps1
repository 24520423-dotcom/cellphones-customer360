param(
    [Parameter(Mandatory)]
    [ValidateSet("New", "Update", "Verify")]
    [string]$Mode,
    [ValidatePattern("^[a-zA-Z0-9][a-zA-Z0-9.-]*$")]
    [string]$Site = "crm.localhost",
    [ValidatePattern("^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")]
    [string]$Container = "crm-frappe-1",
    [ValidatePattern("^[a-z0-9][a-z0-9_-]*$")]
    [string]$ProjectName = "cellphones-c360-source",
    [switch]$ApplyDepartmentRoles
)

$ErrorActionPreference = "Stop"
$bench = "/home/frappe/frappe-bench"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$patch = Join-Path $repo "frappe-crm-native/patches/cellphones-c360.patch"
$rolePatch = Join-Path $repo "frappe-crm-native/patches/department-access.patch"
$release = Join-Path $PSScriptRoot "release.sh"
$releaseText = (Get-Content -LiteralPath $release -Raw -Encoding UTF8) -replace "\r", ""
$encodedRelease = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($releaseText))
$command = "echo $encodedRelease | base64 -d | bash -s --"

function Invoke-Docker {
    & docker @args
    if ($LASTEXITCODE -ne 0) { throw "Docker exited with code $LASTEXITCODE." }
}

if ($Mode -eq "Verify") {
    Invoke-Docker exec -u frappe -w $bench $Container bash -c "$command verify $Site /dev/null"
    return
}

if ($Mode -eq "Update" -and -not $ApplyDepartmentRoles) {
    throw "This release updates site permissions. Use -ApplyDepartmentRoles after the site owner approves the change."
}

$helper = $null
$project = @("compose", "--project-name", $ProjectName)
$setupId = [Guid]::NewGuid().ToString("N")
$releasePatch = "/tmp/c360-release-$setupId.patch"
$releaseRolePatch = "/tmp/c360-department-$setupId.patch"
Push-Location $PSScriptRoot
try {
    if ($Mode -eq "New") {
        if (-not (Test-Path -LiteralPath ".env")) { throw "Copy .env.example to .env and set a private database root password." }
        $passwordLine = Get-Content -LiteralPath ".env" | Where-Object { $_ -match "^\s*MYSQL_ROOT_PASSWORD=" } | Select-Object -Last 1
        if (-not $passwordLine) { throw "MYSQL_ROOT_PASSWORD is missing." }
        $rootPassword = ($passwordLine -split "=", 2)[1].Trim().Trim('"', "'")
        if (-not $rootPassword -or $rootPassword -eq "CHANGE_ME") { throw "Set a private database root password." }
        if ((Invoke-Docker @project ps -a -q) -or
            (Invoke-Docker volume ls -q --filter "label=com.docker.compose.project=$ProjectName")) {
            throw "The chosen Compose project already has containers or volumes. Use Update."
        }
        $admin = Read-Host "New site Administrator password" -AsSecureString
        $env:C360_ADMIN_PASSWORD = [System.Management.Automation.PSCredential]::new("Administrator", $admin).GetNetworkCredential().Password
        $env:C360_DB_ROOT_PASSWORD = $rootPassword
        Invoke-Docker @project build frappe
        Invoke-Docker @project up -d mariadb redis
        $databaseReady = $false
        for ($attempt = 0; $attempt -lt 45; $attempt++) {
            & docker @project exec -T mariadb mariadb-admin ping -h 127.0.0.1 --silent 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) {
                $databaseReady = $true
                break
            }
            Start-Sleep -Seconds 2
        }
        if (-not $databaseReady) { throw "MariaDB did not become ready." }
        $helper = "$ProjectName-setup-$setupId"
        Invoke-Docker @project run --rm -d --no-deps --name $helper --entrypoint sleep frappe infinity
        Invoke-Docker exec -u root $helper chown frappe:frappe $bench "$bench/apps"
        $Container = $helper
        $ApplyDepartmentRoles = $true
    }

    Invoke-Docker cp $patch "${Container}:$releasePatch"
    if ($ApplyDepartmentRoles) {
        Invoke-Docker cp $rolePatch "${Container}:$releaseRolePatch"
    }
    $releaseMode = $Mode.ToLowerInvariant()
    Invoke-Docker exec -u frappe -w $bench -e C360_DB_ROOT_PASSWORD -e C360_ADMIN_PASSWORD $Container bash -c "$command $releaseMode $Site $releasePatch $releaseRolePatch"
    if ($Mode -eq "New") {
        Invoke-Docker @project up -d frappe
    }
} finally {
    if ($helper) {
        & docker stop $helper | Out-Null
    }
    Remove-Item Env:C360_DB_ROOT_PASSWORD, Env:C360_ADMIN_PASSWORD -ErrorAction SilentlyContinue
    Pop-Location
}
