$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "WashiTools.ps1")

Write-Host "Running bootloader native tests."
Push-Location (Join-Path $RepoRoot "bootloader")
try {
    Invoke-WashiPlatformIO -Arguments @("test", "-e", "native")
}
finally {
    Pop-Location
}

Write-Host "Running core native tests."
Push-Location (Join-Path $RepoRoot "core")
try {
    Invoke-WashiPlatformIO -Arguments @("test", "-e", "native")
}
finally {
    Pop-Location
}

Write-Host "Native tests complete."
