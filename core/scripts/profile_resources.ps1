param(
    [string]$Environment = "nucleo_g431rb"
)

$ErrorActionPreference = "Stop"

$CoreRoot = Split-Path -Parent $PSScriptRoot
$RepoRoot = Split-Path -Parent $CoreRoot
. (Join-Path $RepoRoot "tools\WashiTools.ps1")

$pio = Resolve-WashiPlatformIO
$platformIoCore = Get-WashiPlatformIOCoreDirectory
$toolchainBin = Join-Path $platformIoCore "packages\toolchain-gccarmnoneeabi\bin"
$objdumpCandidates = @(
    (Join-Path $toolchainBin "arm-none-eabi-objdump.exe"),
    (Join-Path $toolchainBin "arm-none-eabi-objdump")
)
$objdump = $objdumpCandidates |
    Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
    Select-Object -First 1

if ([string]::IsNullOrWhiteSpace($objdump)) {
    throw "ARM objdump was not found under PlatformIO's toolchain package: $toolchainBin"
}

$elf = Join-Path $CoreRoot (Join-Path ".pio\build" (Join-Path $Environment "firmware.elf"))

Push-Location $CoreRoot
try {
    & $pio run -e $Environment -t size | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "PlatformIO size check failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}

if (!(Test-Path -LiteralPath $elf -PathType Leaf)) {
    throw "Expected ELF not found: $elf"
}

$sections = & $objdump -h $elf
if ($LASTEXITCODE -ne 0) {
    throw "objdump failed with exit code $LASTEXITCODE."
}

function Get-SectionSizeBytes {
    param(
        [string[]]$Lines,
        [string]$Name
    )

    foreach ($line in $Lines) {
        if ($line -match "^\s*\d+\s+$([regex]::Escape($Name))\s+([0-9a-fA-F]+)\s+") {
            return [Convert]::ToUInt32($Matches[1], 16)
        }
    }

    return 0
}

$textBytes = Get-SectionSizeBytes $sections ".text"
$dataBytes = Get-SectionSizeBytes $sections ".data"
$bssBytes = Get-SectionSizeBytes $sections ".bss"
$noinitBytes = Get-SectionSizeBytes $sections ".noinit"
$staticRamBytes = $dataBytes + $bssBytes

$freertosConfig = Get-Content (Join-Path $CoreRoot "include\rtos_config\FreeRTOSConfig.h")
$dynamicAllocationDisabled = ($freertosConfig -match "configSUPPORT_DYNAMIC_ALLOCATION\s+0").Count -gt 0
$zeroHeapConfigured = ($freertosConfig -match "configTOTAL_HEAP_SIZE\s+\(\s*\(\s*size_t\s*\)\s*0\s*\)").Count -gt 0
$heapBytes = if ($dynamicAllocationDisabled -and $zeroHeapConfigured) { 0 } else { "CHECK_CONFIG" }

Write-Host ""
Write-Host "WashiOS Resource Profile"
Write-Host "========================"
Write-Host ("Environment              : {0}" -f $Environment)
Write-Host ("Net Flash Footprint      : {0} bytes (.text)" -f $textBytes)
Write-Host ("Net Static RAM Allocation: {0} bytes (.data + .bss)" -f $staticRamBytes)
Write-Host ("  .data                  : {0} bytes" -f $dataBytes)
Write-Host ("  .bss                   : {0} bytes" -f $bssBytes)
Write-Host ("  .noinit retained RAM   : {0} bytes" -f $noinitBytes)
Write-Host ("Dynamic Heap Consumption : {0} bytes" -f $heapBytes)
