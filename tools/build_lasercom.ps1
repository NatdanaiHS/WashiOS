param(
    [string]$CoreEnv = "nucleo_g431rb_lasercom",
    [string]$BootloaderEnv = "nucleo_g431rb_lasercom"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Building WashiOS-Core environment: $CoreEnv"
Push-Location (Join-Path $RepoRoot "core")
try {
    pio run -e $CoreEnv
}
finally {
    Pop-Location
}

Write-Host "Building WashiBoot environment: $BootloaderEnv"
Push-Location (Join-Path $RepoRoot "bootloader")
try {
    pio run -e $BootloaderEnv
}
finally {
    Pop-Location
}

Write-Host "LaserCom build complete."
