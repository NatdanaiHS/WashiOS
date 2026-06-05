param(
    [string]$Environment = "nucleo_g431rb",
    [uint32]$MeasuredCrcMaxCycles = 0,
    [uint32]$MeasuredCrcBytes = 0,
    [uint32]$CpuHz = 170000000
)

$ErrorActionPreference = "Stop"

$pio = "C:\Users\wachi\.platformio\penv\Scripts\pio.exe"
$objdump = "C:\Users\wachi\.platformio\packages\toolchain-gccarmnoneeabi\bin\arm-none-eabi-objdump.exe"
$elf = ".pio\build\$Environment\firmware.elf"

& $pio run -e $Environment -t size | Out-Host

if (!(Test-Path $elf)) {
    throw "Expected ELF not found: $elf"
}

$sections = & $objdump -h $elf

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

$freertosConfig = Get-Content "include\rtos_config\FreeRTOSConfig.h"
$dynamicAllocationDisabled = ($freertosConfig -match "configSUPPORT_DYNAMIC_ALLOCATION\s+0").Count -gt 0
$zeroHeapConfigured = ($freertosConfig -match "configTOTAL_HEAP_SIZE\s+\(\s*\(\s*size_t\s*\)\s*0\s*\)").Count -gt 0
$heapBytes = if ($dynamicAllocationDisabled -and $zeroHeapConfigured) { 0 } else { "CHECK_CONFIG" }

$crcLatency = "No runtime CRC cycle sample supplied"
if ($MeasuredCrcMaxCycles -gt 0 -and $CpuHz -gt 0) {
    $latencyUs = ($MeasuredCrcMaxCycles * 1000000.0) / $CpuHz
    $crcLatency = ("{0} cycles over {1} bytes = {2:N3} us @ {3:N0} Hz" -f `
        $MeasuredCrcMaxCycles, $MeasuredCrcBytes, $latencyUs, $CpuHz)
}

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
Write-Host ("CRC-32 Max Latency       : {0}" -f $crcLatency)
