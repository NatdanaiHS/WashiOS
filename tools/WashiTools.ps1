$ErrorActionPreference = "Stop"

function Resolve-WashiPlatformIO {
    $commands = @("pio", "platformio")
    foreach ($name in $commands) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($null -ne $command) {
            return $command.Source
        }
    }

    $candidateRoots = @()
    if (-not [string]::IsNullOrWhiteSpace($env:PLATFORMIO_CORE_DIR)) {
        $candidateRoots += $env:PLATFORMIO_CORE_DIR
    }
    if (-not [string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
        $candidateRoots += (Join-Path $env:USERPROFILE ".platformio")
    }

    foreach ($root in ($candidateRoots | Select-Object -Unique)) {
        foreach ($name in @("pio.exe", "platformio.exe", "pio", "platformio")) {
            $candidate = Join-Path $root (Join-Path "penv" (Join-Path "Scripts" $name))
            if (Test-Path -LiteralPath $candidate -PathType Leaf) {
                return $candidate
            }
            $candidate = Join-Path $root (Join-Path "penv" (Join-Path "bin" $name))
            if (Test-Path -LiteralPath $candidate -PathType Leaf) {
                return $candidate
            }
        }
    }

    throw "PlatformIO Core was not found. Install the PlatformIO VS Code extension or PlatformIO Core, then run this script again."
}

function Invoke-WashiPlatformIO {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    if ([string]::IsNullOrWhiteSpace($script:WashiPlatformIO)) {
        $script:WashiPlatformIO = Resolve-WashiPlatformIO
    }

    & $script:WashiPlatformIO @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "PlatformIO failed with exit code $LASTEXITCODE."
    }
}

function Get-WashiPlatformIOCoreDirectory {
    if ([string]::IsNullOrWhiteSpace($script:WashiPlatformIO)) {
        $script:WashiPlatformIO = Resolve-WashiPlatformIO
    }

    if (-not [string]::IsNullOrWhiteSpace($env:PLATFORMIO_CORE_DIR)) {
        return [System.IO.Path]::GetFullPath($env:PLATFORMIO_CORE_DIR)
    }

    $executableDirectory = Split-Path -Parent ([System.IO.Path]::GetFullPath($script:WashiPlatformIO))
    $virtualEnvironmentDirectory = Split-Path -Parent $executableDirectory
    if ((Split-Path -Leaf $virtualEnvironmentDirectory) -eq "penv") {
        return Split-Path -Parent $virtualEnvironmentDirectory
    }

    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "SilentlyContinue"
        $jsonText = (& $script:WashiPlatformIO system info --json-output 2>$null) -join ""
        $systemInfoExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }

    if ($systemInfoExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($jsonText)) {
        throw "Unable to read the PlatformIO Core directory."
    }

    try {
        $info = $jsonText | ConvertFrom-Json
        return [string]$info.core_dir.value
    }
    catch {
        throw "PlatformIO returned invalid system information: $($_.Exception.Message)"
    }
}

function Resolve-WashiOpenOcd {
    $coreDirectory = Get-WashiPlatformIOCoreDirectory
    $packageDirectory = Join-Path $coreDirectory (Join-Path "packages" "tool-openocd")
    $executableNames = @("openocd.exe", "openocd")

    foreach ($name in $executableNames) {
        $candidate = Join-Path $packageDirectory (Join-Path "bin" $name)
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return @{
                Executable = $candidate
                Scripts = Join-Path $packageDirectory (Join-Path "openocd" "scripts")
            }
        }
    }

    throw "PlatformIO's OpenOCD package was not found. Build the STM32 environment once while connected to the internet, then retry."
}

function Get-WashiStLinkTransport {
    param(
        [Parameter(Mandatory = $true)]
        [string]$OpenOcdScripts
    )

    $stLinkConfig = Join-Path $OpenOcdScripts (Join-Path "interface" "stlink.cfg")
    if (-not (Test-Path -LiteralPath $stLinkConfig -PathType Leaf)) {
        throw "OpenOCD ST-Link configuration was not found: $stLinkConfig"
    }

    $configText = Get-Content -LiteralPath $stLinkConfig -Raw
    if ($configText -match "(?m)^\s*(adapter\s+driver\s+st-link|adapter\s+driver\s+stlink)\s*$") {
        return "swd"
    }
    if ($configText -match "(?m)^\s*(interface|adapter\s+driver)\s+hla\s*$" -or
        $configText -match "(?m)^\s*hla_layout\s+stlink\s*$") {
        return "hla_swd"
    }

    throw "Unsupported OpenOCD ST-Link configuration. Update PlatformIO's tool-openocd package."
}

function Invoke-WashiOpenOcdFlash {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ProjectDirectory,

        [Parameter(Mandatory = $true)]
        [string]$Environment,

        [string]$TargetConfig = "stm32g4x",

        [string]$StLinkSerial,

        [switch]$ResetConfigNone,

        [switch]$NoReset
    )

    $firmware = Join-Path $ProjectDirectory (Join-Path ".pio" (Join-Path "build" (Join-Path $Environment "firmware.elf")))
    if (-not (Test-Path -LiteralPath $firmware -PathType Leaf)) {
        throw "Firmware was not built: $firmware"
    }

    $openOcd = Resolve-WashiOpenOcd
    $transport = Get-WashiStLinkTransport -OpenOcdScripts $openOcd.Scripts
    $firmwareForOpenOcd = ([System.IO.Path]::GetFullPath($firmware)).Replace("\", "/")
    $arguments = @()

    if (-not [string]::IsNullOrWhiteSpace($StLinkSerial)) {
        if ($StLinkSerial -notmatch '^[0-9A-Fa-f]+$') {
            throw "ST-LINK serial must contain only hexadecimal characters."
        }
        $arguments += @("-c", "adapter serial $StLinkSerial")
    }

    if ($ResetConfigNone) {
        $arguments += @("-c", "reset_config none")
    }

    $programCommand = "program {$firmwareForOpenOcd} verify"
    if (-not $NoReset) {
        $programCommand += " reset"
    }
    $programCommand += "; shutdown;"

    $arguments += @(
        "-d2",
        "-s", $openOcd.Scripts,
        "-f", "interface/stlink.cfg",
        "-c", "transport select $transport",
        "-f", "target/$TargetConfig.cfg",
        "-c", $programCommand
    )

    Write-Host "Flashing $Environment with OpenOCD transport '$transport'."
    & $openOcd.Executable @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "OpenOCD flash failed with exit code $LASTEXITCODE."
    }
}
