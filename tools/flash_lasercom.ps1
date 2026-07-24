param(
    [string]$CoreEnv = "nucleo_g431rb_lasercom",
    [string]$BootloaderEnv = "nucleo_g431rb_lasercom"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Building core before bootloader so the bootloader CRC is current."
Push-Location (Join-Path $RepoRoot "core")
try {
    pio run -e $CoreEnv
}
finally {
    Pop-Location
}

Write-Host "Building bootloader with provisioned core CRC."
Push-Location (Join-Path $RepoRoot "bootloader")
try {
    pio run -e $BootloaderEnv
}
finally {
    Pop-Location
}

Write-Host "Uploading bootloader."
Push-Location (Join-Path $RepoRoot "bootloader")
try {
    pio run -e $BootloaderEnv -t upload
}
finally {
    Pop-Location
}

Write-Host "Uploading core application."
Push-Location (Join-Path $RepoRoot "core")
try {
    pio run -e $CoreEnv -t upload
}
finally {
    Pop-Location
}

Write-Host "LaserCom firmware flashed. Press reset on the board if it does not restart automatically."
