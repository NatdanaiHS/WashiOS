# WashiOS FlightStack

WashiOS FlightStack is a single-repository workspace for the WashiOS embedded flight-software prototype.

It contains:

```text
bootloader/  WashiBoot fail-safe A/B bootloader
core/        WashiOS-Core FreeRTOS safety runtime and demos
demo-payload/ Hardware-in-the-loop payload responder for the G474 payload board
docs/        Thai user manual, research handoff, provisioning notes
tools/       Convenience PowerShell scripts for lab use
```

The current main OBC target board is:

```text
ST NUCLEO-G431RB / STM32G431RB
```

The demo payload responder target board is:

```text
ST NUCLEO-G474RE / STM32G474RE
```

## What This Project Does

This project demonstrates a lightweight safety-oriented STM32 firmware stack:

1. `bootloader/` validates the application image before booting it.
2. `core/` runs the FreeRTOS application with task-health supervision, retained fault logging, and watchdog gating.
3. `core/` contains OBC-side demo modes for UART payload supervision and GPIO-driven laser communication.
4. `demo-payload/` runs on a second board and replies to the OBC payload-link polls.

## Repository Structure

```text
.
  README.md
  bootloader/
    platformio.ini
    bootloader.ld
    include/
    src/
    scripts/
    test/
  core/
    platformio.ini
    include/
    src/
    lib/
    scripts/
    test/
  demo-payload/
    platformio.ini
    src/
    docs/
  docs/
    WashiOS_User_Manual_TH.md
    AI_RESEARCH_HANDOFF.md
    flight_provisioning.md
  tools/
    build_lasercom.ps1
    flash_lasercom.ps1
    build_payload_demo.ps1
    flash_payload_demo.ps1
    build_payload_responder.ps1
    flash_payload_responder.ps1
    test_native.ps1
```

The PowerShell helpers are self-contained with respect to PlatformIO paths and
OpenOCD ST-Link transport selection. They locate `pio`/`platformio` from `PATH`
or the user's PlatformIO installation, locate the matching OpenOCD package, and
select either modern `swd` or legacy `hla_swd` from the installed ST-Link
configuration. Do not edit PlatformIO's installed `platform.py` when moving the
repository to another machine.

On Windows, the `flash_*.cmd` launchers also bypass per-machine PowerShell
execution-policy differences. For example:

```bat
tools\flash_payload_demo.cmd
```

## Quick Start: Laser Communication Demo

From the repository root:

```powershell
.\tools\build_lasercom.ps1
.\tools\flash_lasercom.cmd
```

Manual build commands:

```powershell
cd core
pio run -e nucleo_g431rb_lasercom

cd ..\bootloader
pio run -e nucleo_g431rb_lasercom
```

Use `tools\flash_lasercom.cmd` for programming. The helper deliberately writes
the core without resetting, then writes and starts the matching CRC-provisioned
bootloader. Directly uploading the bootloader before the core can start a
mismatched image between programming steps.

The laser communication demo uses:

```text
PA6  Laser TX GPIO
PA5  Heartbeat LED / bootloader safe-loop beacon
```

Do not connect a laser diode directly to PA6. Use a laser driver, transistor, or module with a suitable 3.3 V logic input.

## Quick Start: Native Tests

```powershell
.\tools\test_native.ps1
```

Manual commands:

```powershell
cd bootloader
pio test -e native

cd ..\core
pio test -e native
```

## Quick Start: Payload UART Demo

There are two parts:

```text
core/          OBC-side payload supervisor on NUCLEO-G431RB
demo-payload/  Payload responder firmware on NUCLEO-G474RE
```

From the repository root:

```powershell
.\tools\build_payload_demo.ps1
.\tools\flash_payload_demo.cmd
.\tools\build_payload_responder.ps1
.\tools\flash_payload_responder.cmd
```

The payload UART demo uses:

```text
USART1 PC4/PC5  Payload link
USART2 PA2      Debug console
Baud rate       115200
```

Wire the two boards:

```text
G431 OBC PC4 / USART1_TX  ->  G474 payload PC5 / USART1_RX
G431 OBC PC5 / USART1_RX  ->  G474 payload PC4 / USART1_TX
G431 GND                  ->  G474 GND
```

Do not connect the boards' 3V3 or 5V rails together when both boards are powered from USB.

## Build Rule To Remember

Build the matching `core/` environment before building the bootloader.

The bootloader build reads the core firmware ELF, validates its vector table, computes its CRC-32, and embeds that CRC into the bootloader image.

Example for LaserCom:

```powershell
cd core
pio run -e nucleo_g431rb_lasercom

cd ..\bootloader
pio run -e nucleo_g431rb_lasercom
```

If the core firmware changes, rebuild the bootloader so the provisioned CRC stays in sync.

## Documentation

Start here:

```text
docs/WashiOS_User_Manual_TH.md
```

Research/paper handoff:

```text
docs/AI_RESEARCH_HANDOFF.md
```

Delivery readiness and the verified baseline:

```text
docs/DELIVERY_STATUS_TH.md
```

Internship presentation order and speaker notes:

```text
docs/PRESENTATION_GUIDE_TH.md
```

Bootloader provisioning notes:

```text
docs/flight_provisioning.md
```
