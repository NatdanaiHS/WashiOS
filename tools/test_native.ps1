$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Running bootloader native tests."
Push-Location (Join-Path $RepoRoot "bootloader")
try {
    pio test -e native
}
finally {
    Pop-Location
}

Write-Host "Running core native tests."
Push-Location (Join-Path $RepoRoot "core")
try {
    pio test -e native
}
finally {
    Pop-Location
}

Write-Host "Native tests complete."
