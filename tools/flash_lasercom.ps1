param(
    [string]$CoreEnv = "nucleo_g431rb_lasercom",
    [string]$BootloaderEnv = "nucleo_g431rb_lasercom"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "WashiTools.ps1")
$CoreDirectory = Join-Path $RepoRoot "core"
$BootloaderDirectory = Join-Path $RepoRoot "bootloader"

Write-Host "Building core before bootloader so the bootloader CRC is current."
Push-Location $CoreDirectory
try {
    Invoke-WashiPlatformIO -Arguments @("run", "-e", $CoreEnv)
}
finally {
    Pop-Location
}

Write-Host "Building bootloader with provisioned core CRC."
Push-Location $BootloaderDirectory
try {
    Invoke-WashiPlatformIO -Arguments @("run", "-e", $BootloaderEnv)
}
finally {
    Pop-Location
}

Write-Host "Uploading core application without resetting into the old bootloader."
Invoke-WashiOpenOcdFlash `
    -ProjectDirectory $CoreDirectory `
    -Environment $CoreEnv `
    -ResetConfigNone `
    -NoReset

Write-Host "Uploading bootloader and starting the matched core application."
Invoke-WashiOpenOcdFlash `
    -ProjectDirectory $BootloaderDirectory `
    -Environment $BootloaderEnv `
    -ResetConfigNone

Write-Host "LaserCom firmware flashed and started."
