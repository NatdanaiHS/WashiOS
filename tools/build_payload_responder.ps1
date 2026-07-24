param(
    [string]$PayloadEnv = "nucleo_g474re"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Building demo payload responder environment: $PayloadEnv"
Push-Location (Join-Path $RepoRoot "demo-payload")
try {
    pio run -e $PayloadEnv
}
finally {
    Pop-Location
}

Write-Host "Demo payload responder build complete."
