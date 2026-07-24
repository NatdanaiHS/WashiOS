param(
    [string]$PayloadEnv = "nucleo_g474re"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "WashiTools.ps1")

Write-Host "Building demo payload responder environment: $PayloadEnv"
Push-Location (Join-Path $RepoRoot "demo-payload")
try {
    Invoke-WashiPlatformIO -Arguments @("run", "-e", $PayloadEnv)
}
finally {
    Pop-Location
}

Write-Host "Demo payload responder build complete."
