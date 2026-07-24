param(
    [string]$PayloadEnv = "nucleo_g474re"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Uploading demo payload responder to the G474 payload board."
Push-Location (Join-Path $RepoRoot "demo-payload")
try {
    pio run -e $PayloadEnv -t upload
}
finally {
    Pop-Location
}

Write-Host "Demo payload responder flashed."
