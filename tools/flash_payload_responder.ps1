param(
    [string]$PayloadEnv = "nucleo_g474re"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$PayloadDirectory = Join-Path $RepoRoot "demo-payload"
. (Join-Path $PSScriptRoot "WashiTools.ps1")

Write-Host "Building demo payload responder for the G474 payload board."
Push-Location $PayloadDirectory
try {
    Invoke-WashiPlatformIO -Arguments @("run", "-e", $PayloadEnv)
}
finally {
    Pop-Location
}

Write-Host "Uploading demo payload responder to the G474 payload board."
Invoke-WashiOpenOcdFlash `
    -ProjectDirectory $PayloadDirectory `
    -Environment $PayloadEnv

Write-Host "Demo payload responder flashed."
