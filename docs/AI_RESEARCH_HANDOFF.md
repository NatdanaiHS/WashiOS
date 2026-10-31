# AI Research Handoff: WashiOS / WashiBoot Project

Generated for another AI agent to understand the current project state and help with research/paper preparation.

Last verified: 2026-07-31

## One-Sentence Summary

This project is a lightweight STM32-based embedded flight-software prototype that combines a fail-safe A/B bootloader, a FreeRTOS runtime safety core, and a demo payload communication link for CubeSat-class or mission-critical embedded systems.

## Repository Layout

The project is organized as a monorepo-style workspace. Use the repository
root rather than a machine-specific absolute path:

```text
<repo-root>
```

Important directories:

```text
bootloader/  WashiBoot fail-safe A/B bootloader
core/        WashiOS-Core FreeRTOS runtime and demos
demo-payload/ G474 hardware-in-the-loop payload responder firmware
docs/        user manual, research handoff, provisioning notes
tools/       PowerShell helper scripts
```

The repository folder name is not part of the build contract. Scripts resolve
paths relative to the repository so the workspace can be moved between
machines.

## Git State

### Repository

Verified baseline on 31 July 2026:

```text
Branch: monorepo-migration
Commit: 8df7062 Fix portable flashing and expand Thai handoff manual
Remote tracking branch: origin/monorepo-migration
```

Automated verification at that baseline plus the documentation/tooling cleanup
records 11/11 WashiBoot native tests, 38/38 core native tests, six core STM32
build environments, three matching WashiBoot builds, and one G474 responder
build. See `docs/DELIVERY_STATUS_TH.md` for exact commands and remaining
handoff limitations.

### Imported Core Snapshot

The `core/` directory was imported from a previous sibling repository. The
historical local checkout path is not required by the current build:

```text
<historical-core-checkout>
```

Previous remote:

```text
https://github.com/NatdanaiHS/WashiOS.git
```

Imported branch:

```text
workspace-bootstrap
```

Imported commit:

```text
4940964 Add payload link demo support
```

### Imported Demo Payload Snapshot

The `demo-payload/` directory was imported from a historical local checkout:

```text
<historical-demo-payload-checkout>
```

It was not a git repository when inspected. It targets `nucleo_g474re` and
acts as the hardware-in-the-loop payload responder for the OBC-side
`nucleo_g431rb_payload_demo` build.

## What This Project Is Trying To Demonstrate

The project is not just a normal STM32 firmware project. It tries to demonstrate a small but coherent safety architecture:

1. Boot-time safety through a bootloader that validates firmware before jumping to it.
2. Runtime safety through task health monitoring, watchdog gating, static FreeRTOS task allocation, and retained fault logs.
3. Communication safety through a payload link demo with CRC, sequence numbers, timeouts, offline detection, and recovery.

The right paper framing is likely:

```text
Lightweight Fault-Tolerant Boot and Runtime Supervision Framework
for STM32-Based CubeSat-Class Embedded Systems
```

Do not overclaim novelty. The current value is mostly integration, validation, and resource-constrained implementation, not a new algorithm.

## High-Level Components

### 1. WashiBoot Bootloader

Location:

```text
bootloader/
```

Purpose:

WashiBoot is the first firmware that runs after reset. It decides whether an application image is safe to boot. It supports A/B application slots, validates firmware integrity with CRC-32, validates the application vector table, tracks boot metadata, and enters a safe beacon loop if no valid firmware is available.

Key files:

```text
src/main.cpp
include/boot/BootPolicy.hpp
include/boot/BootMetadata.hpp
include/boot/Crc32.hpp
include/hal/IFlashMap.hpp
include/hal/IBootPlatform.hpp
include/hal/IBeacon.hpp
src/bsp/g4/Stm32G4FlashMap.cpp
src/bsp/g4/Stm32G4BootPlatform.cpp
src/bsp/g4/Stm32G4Beacon.cpp
bootloader.ld
scripts/provision_slot_crc.py
docs/flight_provisioning.md
test/test_boot_policy/test_main.cpp
```

Memory map on STM32G431RB:

```text
Bootloader: 0x08000000, 16 KiB
Slot A:     0x08004000, 56 KiB
Slot B:     0x08012000, 56 KiB
RAM:        0x20000000, 32 KiB
```

Boot flow:

1. `HAL_Init()` is called.
2. The beacon GPIO is initialized.
3. `BootPolicy` is created with the flash map, platform jump implementation, beacon, retained boot metadata, retained fault log, expected CRC, and provisioned image length.
4. `BootPolicy::run()` recovers retained fault state and boot metadata.
5. It normalizes a confirmed boot flag if the application previously marked the boot successful.
6. It rejects booting if retained fault recovery is corrupt, if a pending image exceeds the boot attempt limit, or if a prior critical fault is recorded.
7. It checks the active slot first.
8. If the active slot fails, it checks the fallback slot.
9. A bootable slot must have a bootable state, valid vector table, provisioned expected CRC, and matching runtime CRC.
10. If a slot is valid, the bootloader records a boot attempt, disables/deinitializes hardware, sets VTOR/MSP, and jumps to the application reset handler.
11. If no slot is valid, it records `SafeFail` and enters the beacon safe loop.

Boot metadata:

```text
signature
checksum
boot_count
confirmed_flag
expected_firmware_crc32
metadata_version
active_slot
slot_a_crc32
slot_b_crc32
slot_a_state
slot_b_state
last_boot_slot
last_fail_reason
```

Important constants:

```text
WASHIOS_MAGIC_SIGNATURE = 0x55AA55AA
BootMetadataConfirmed   = 0xA5A55A5A
BootMetadataCurrentVersion = 2
MaxUnconfirmedBootAttempts = 3
```

Firmware slot states:

```text
Empty
Valid
Pending
Confirmed
Bad
```

Current bootloader limitations:

1. Metadata is currently retained in `.noinit` RAM, so it can survive warm resets but not a full power loss.
2. CRC-32 detects accidental corruption but does not provide authenticity. It does not prevent malicious firmware replacement.
3. There is no cryptographic signature verification yet.
4. There is no anti-rollback counter yet.
5. There is no complete OTA update pipeline yet.
6. Slot provisioning is development-oriented: a pre-build script reads a prebuilt WashiOS-Core ELF and injects compile-time CRC defaults.

Provisioning script:

```text
scripts/provision_slot_crc.py
```

What it does:

1. Locates the configured Slot A ELF from WashiOS-Core.
2. Uses `objcopy` to convert it to binary.
3. Checks that the image fits in Slot A.
4. Validates the vector table against Slot A base and RAM range.
5. Computes CRC-32 over the actual application binary length.
6. Injects `WASHIBOOT_DEFAULT_EXPECTED_CRC32` and `WASHIBOOT_DEFAULT_SLOT_A_CRC_LENGTH` into the bootloader build.

Bootloader tests currently cover:

1. Legacy metadata migration.
2. Corrupt metadata initialization.
3. Adoption of provisioned Slot A default CRC.
4. Successful Slot A boot.
5. Provisioned image-length CRC behavior.
6. Confirmed-slot boot count handling.
7. Pending-slot boot loop limit.
8. Stale Slot A CRC adopting the default provisioned image CRC.
9. Fallback from Slot A to Slot B on CRC failure.
10. Fallback from Slot A to Slot B on invalid vector table.
11. Safe fail when both slots fail.

### 2. WashiOS-Core

Location:

```text
core/
```

Purpose:

WashiOS-Core is the application firmware. It is a lightweight FreeRTOS-based safety core for STM32 targets. It focuses on deterministic behavior, static allocation, retained fault telemetry, task health monitoring, watchdog-enforced recovery, and hardware abstraction.

Main PlatformIO environments:

```text
genericSTM32F411RE
nucleo_g431rb
nucleo_g431rb_slot_b
nucleo_g431rb_stress
nucleo_g431rb_lasercom
nucleo_g431rb_payload_demo
native
```

Important directories:

```text
include/core
include/hal
include/bsp
include/comms
include/rtos_config
src/app
src/bsp
src/stress
test/test_sitl
```

Core safety mechanisms:

1. `FaultLog`
   - Stores fault events in retained `.noinit` RAM.
   - Uses a magic signature and CRC-32 checksum.
   - Can reject cold-start garbage or corrupted retained state.
   - Records faults such as watchdog timeout, task check-in failure, stack overflow, TMR correction, TMR unrecoverable, assert failure, and safe fail.

2. `TaskHealthRegistry`
   - Registers tasks with deadlines.
   - Tracks check-ins.
   - Distinguishes critical and non-critical failures.
   - Produces a health mask for telemetry.

3. `Watchdog`
   - Polls task health.
   - Records `TaskCheckinFailure`, `WatchdogTimeout`, and `SafeFail` on critical failure.
   - Refreshes the hardware watchdog only when all critical tasks are healthy.

4. `WatchdogRunner`
   - Periodically invokes watchdog polling.

5. `WashiTask`
   - Static allocation wrapper for FreeRTOS tasks.
   - Owns each task's `StaticTask_t` and stack buffer.
   - Avoids dynamic task allocation in flight-controlled code.

6. `BootFailSafe`
   - Detects failure to start critical tasks before scheduler start.
   - Records `SafeFail` and requests reset instead of running a partial system.

7. `Telemetry`
   - Fixed 28-byte frame.
   - Contains sync bytes, version, sequence, uptime, task health mask, fault count, latest fault type/task id, and CRC-32.

8. `TMR`
   - Triple modular redundancy wrapper for critical scalar values.
   - Repairs one corrupted copy.
   - Logs unrecoverable disagreement and triggers reset outside test mode.

Startup flow in `src/main.cpp`:

1. Initialize HAL and system clock.
2. Initialize GPIO.
3. Initialize UART(s).
4. Initialize timing source.
5. Initialize heartbeat LED and optional laser TX pin.
6. Recover retained fault log.
7. Register task health entries.
8. Configure tasks.
9. Initialize hardware independent watchdog on STM32G4.
10. Start static FreeRTOS tasks.
11. If task creation fails, record safe fail and reset.
12. Start the scheduler.
13. If scheduler returns unexpectedly, record safe fail and reset.

Core application tasks:

```text
HeartbeatTask
TelemetryMockTask
WatchdogTask
PayloadLinkTask
LaserTelemetryTask
StressTestTask
```

### 3. Demo Payload Link

The payload demo now has two parts:

```text
core/          OBC-side payload supervisor firmware for NUCLEO-G431RB
demo-payload/  Payload responder firmware for NUCLEO-G474RE
```

The OBC-side functionality is implemented inside `core/` as the PlatformIO environment:

```text
nucleo_g431rb_payload_demo
```

The responder-side functionality is implemented inside `demo-payload/` as:

```text
nucleo_g474re
```

Purpose:

The demo payload link shows how the OBC-side firmware can supervise a payload connection using a small deterministic protocol. It validates framing, CRC, sequence numbers, timeouts, offline detection, and recovery.

Files added or heavily involved:

```text
include/comms/PayloadProtocol.hpp
include/comms/PayloadLinkController.hpp
src/app/PayloadLinkTask.hpp
include/core/FixedTextWriter.hpp
include/core/TaskHealthReporter.hpp
include/bsp/g4/Stm32G4BoardUart.hpp
src/bsp/g4/Stm32G4BoardUart.cpp
src/bsp/g4/Stm32G4Uart.cpp
include/bsp/g4/Stm32G4Uart.hpp
src/main.cpp
test/test_sitl/test_main.cpp
```

Payload UART mapping on STM32G431RB:

```text
USART1: payload TX/RX on PC4/PC5
USART2: debug console TX on PA2
```

UART details:

1. Common baud rate is 115200.
2. USART1 supports interrupt receive.
3. A 128-byte software receive ring buffer is used for USART1.
4. UART operation timeout is bounded to 10 ms in the G4 UART wrapper.

Payload wire protocol:

```text
Frame size: 32 bytes
Sync0:      0x57
Sync1:      0x50
Version:    1
CRC offset: 28
Payload:    16 bytes
```

Message types:

```text
PollRequest       = 0x01
TelemetryResponse = 0x81
```

Telemetry response fields:

```text
uptimeMs
sampleCounter
simulatedSensorMilliunits
mode
```

Payload modes:

```text
Normal
Silent
BadCrc
Delayed
```

Payload link controller behavior:

```text
Poll period:          500 ms
Response timeout:     100 ms
Offline threshold:    3 consecutive timeouts
Initial state:        Starting
Nominal state:        Online
Failure state:        Offline
```

`PayloadLinkTask` behavior:

1. Runs every 1 ms.
2. Reads up to 64 payload UART bytes per cycle.
3. Decodes fixed-size payload frames.
4. Sends poll requests when the controller allows it.
5. Checks in to the task health registry every 100 ms.
6. Prints status to debug UART every 5 seconds.
7. Logs transitions such as online, timeout, offline, recovered, rejected frame, and poll write failure.

Important design point:

Payload offline status does not automatically make the whole OBC firmware unhealthy. The `PayloadLinkTask` keeps checking in as long as the task itself is alive. This separates "payload link health" from "OBC task health".

Payload tests currently cover:

1. Known request vector and round trip.
2. Telemetry response round trip.
3. Invalid size, sync, version, type, length, and CRC rejection.
4. Decoder fragmentation and resynchronization.
5. Link offline transition after timeouts.
6. Rejection of stale sequence.
7. Recovery back to online.
8. CRC rejection statistics.
9. Payload offline not making the running task unhealthy.

### 4. Demo Payload Responder Board

Location:

```text
demo-payload/
```

Purpose:

This is the firmware for a second NUCLEO-G474RE board that behaves like a
simulated payload. It receives OBC poll requests over USART1, validates the
shared payload protocol, and sends telemetry responses back to the OBC.

Key files:

```text
demo-payload/platformio.ini
demo-payload/src/main.cpp
demo-payload/docs/experiment-results.md
demo-payload/docs/presentation-script.md
```

Target:

```text
NUCLEO-G474RE / STM32G474RE
```

Wiring:

```text
G431 OBC PC4 / USART1_TX  ->  G474 payload PC5 / USART1_RX
G431 OBC PC5 / USART1_RX  ->  G474 payload PC4 / USART1_TX
G431 GND                  ->  G474 GND
```

The responder imports protocol headers from `../core/include/comms` and
`../core/include/core` so the OBC and payload use the same frame format.

Responder modes:

```text
NORMAL   valid telemetry response
SILENT   receive polls but send no response
BAD_CRC  corrupt the response CRC
DELAYED  wait 250 ms before responding, exceeding the OBC 100 ms deadline
```

The G474 user button cycles:

```text
NORMAL -> SILENT -> BAD_CRC -> DELAYED -> NORMAL
```

The G474 user LED toggles for every valid poll request.

### 5. LaserCom / Optical Telemetry Demo

WashiOS-Core also contains a laser communication demo environment:

```text
nucleo_g431rb_lasercom
```

Related files:

```text
include/comms/LaserPdmTx.hpp
include/comms/FsoFrame.hpp
src/app/LaserTelemetryTask.hpp
src/main.cpp
```

Purpose:

This part demonstrates a simple optical/laser telemetry transmitter using a GPIO-driven pulse-duration modulation scheme.

Laser PDM timing:

```text
Short pulse: 2000 us
Long pulse:  4000 us
Gap:         2000 us
```

Laser transmit pin on STM32G4:

```text
PA6
```

`LaserTelemetryTask` can send either:

1. A fixed ASCII test message when `WASHIOS_LASERCOM_ASCII_TEST` is enabled.
2. A serialized WashiOS telemetry frame wrapped in an FSO frame.

FSO frame:

```text
Sync0:        0xAA
Sync1:        0x55
Type:         0x03
Max payload:  64 bytes
CRC:          CRC-8
```

This is useful as a demo communication path, but it is not yet a robust optical communication stack.

## What Was Actually Implemented

### Bootloader Work

Implemented or extended:

1. A/B slot boot policy.
2. Boot metadata version 2.
3. Per-slot CRC fields.
4. Per-slot state fields.
5. Active slot tracking.
6. Last boot slot and last fail reason tracking.
7. Legacy metadata migration.
8. Pending-slot boot attempt limit.
9. Fallback slot selection.
10. Default Slot A CRC adoption from provisioning.
11. Pre-build Slot A provisioning script.
12. Flight provisioning notes.
13. Unit tests for boot policy behavior.

### Core Work

Implemented or extended:

1. Shifted application memory map for bootloader-compatible Slot A.
2. Slot B linker script support.
3. Retained fault log compatibility with bootloader expectations.
4. Firmware health monitor logic.
5. Task health reporter helper.
6. Fixed-size text writer helper.
7. G4 board UART initialization helpers.
8. Interrupt-driven USART1 receive buffer.
9. Payload demo environment.
10. Payload protocol and link controller.
11. Payload link FreeRTOS task.
12. LaserCom task/test improvements.
13. SITL tests for payload protocol/link and communication framing.

### Demo Payload Work

Implemented OBC-side payload link demo:

1. Fixed-size payload frame.
2. Poll-response protocol.
3. CRC validation.
4. Sequence validation.
5. Timeout handling.
6. Offline state after repeated timeouts.
7. Recovery when responses become valid again.
8. Debug UART status messages.
9. Unit tests for protocol, decoder, and link state machine.

## Existing Research/Paper Value

The current project has practical engineering value because it integrates boot-time safety, runtime safety, and communication-link supervision on a constrained STM32 platform.

However, as of now, it is probably not enough for a strong conference paper if presented only as "we built a bootloader and firmware demo." The current contribution is mostly an engineering integration prototype.

It can become paper-worthy if the work is framed and evaluated as:

```text
A lightweight, measurable, fault-injection-tested safety architecture
for STM32-based CubeSat-class embedded systems.
```

The most defensible contribution is:

1. A minimal A/B bootloader with deterministic fallback behavior.
2. A lightweight FreeRTOS runtime supervision layer with retained fault evidence.
3. A payload communication fault-handling demo integrated into the same health-supervised runtime.
4. A reproducible fault-injection and measurement campaign showing detection/recovery behavior.

## Comparison Baselines To Research

The next AI agent should compare this project against:

1. MCUboot
   - Boot slots, image validation, image confirmation, rollback.
   - Official docs: https://docs.mcuboot.com/design.html

2. NASA core Flight System (cFS)
   - Mature flight software framework.
   - Useful contrast: this project is much lighter and MCU-focused.
   - Official docs: https://etd.gsfc.nasa.gov/capabilities/core-flight-system/

3. NASA F Prime
   - Component-based flight software framework.
   - Useful contrast: framework maturity vs resource-constrained minimal implementation.
   - Official docs: https://nasa.github.io/fprime/

4. CubeSat bootloader papers
   - Especially robust bootloader / dual-bank / OTA / rollback papers.

5. CubeSat flight software case studies
   - FreeRTOS, modular architecture, onboard computer constraints, validation.

6. Nanosatellite communication software testing papers
   - Interoperability faults, malformed frames, timeout behavior, protocol testing.

7. Fault injection for CubeSat software
   - Validate CRC mismatch, invalid vector table, corrupted metadata, task starvation, payload timeout, and communication errors.

## Suggested Research Questions

Potential paper research questions:

1. How much boot-time overhead does CRC-based firmware validation add on an STM32G431RB?
2. Can a minimal A/B bootloader deterministically recover from corrupted application images and invalid vector tables?
3. What is the resource overhead of adding retained fault logging, task health monitoring, and watchdog gating to a FreeRTOS application?
4. Can payload communication faults be isolated from core OBC task health while still being reported as link-level faults?
5. How many realistic fault scenarios can the integrated boot/runtime/payload safety architecture detect and recover from?

## Experiments Needed Before Paper Submission

The project needs more experimental evidence. Suggested experiments:

### Bootloader Experiments

1. Valid Slot A boots.
2. Slot A CRC mismatch falls back to Slot B.
3. Slot A invalid vector table falls back to Slot B.
4. Both slots invalid enters safe loop.
5. Corrupt boot metadata is detected and reinitialized.
6. Legacy boot metadata migrates to current metadata.
7. Pending image boot count exceeds 3 attempts and is rejected.
8. Measure boot time with and without CRC validation.
9. Measure CRC time versus firmware image size.

### Runtime Core Experiments

1. All tasks healthy: watchdog is refreshed.
2. Heartbeat task starvation: task health failure is detected.
3. Telemetry/PayloadLink task starvation: fault is logged and reset path is triggered.
4. Stack overflow hook records a fault and resets.
5. Retained fault log survives warm reset.
6. Corrupted retained fault log is rejected.
7. Measure RAM/flash overhead of safety mechanisms.
8. Measure watchdog reaction time after task failure.

### Demo Payload Experiments

1. Normal payload response keeps link online.
2. CRC-corrupted response is rejected.
3. Wrong sequence response is rejected.
4. Missing response causes timeout.
5. Three consecutive timeouts move link offline.
6. Valid later response moves link from offline to online/recovered.
7. Payload offline does not kill OBC task health.
8. Measure detection time and recovery time.

### LaserCom Experiments

1. Validate pulse timing for 0 and 1 bits.
2. Validate sync pulse generation.
3. Validate FSO frame construction and CRC-8.
4. Measure transmit time per telemetry frame.
5. Optional: test with photodiode receiver or oscilloscope.

## Metrics To Collect

Minimum useful metrics:

```text
Bootloader flash usage
Bootloader RAM usage
Application flash usage
Application RAM usage
Boot time to application jump
CRC verification time
Watchdog reaction time
Fault log record time
Payload offline detection time
Payload recovery time
Payload frame rejection counts
Laser frame transmit time
```

If possible, also collect:

```text
Power cycles tested
Warm resets tested
Long-run soak test duration
Number of injected faults
Number of detected faults
Number of successful recoveries
False positive count
False negative count
```

## Important Limitations To Be Honest About

The paper should openly state:

1. CRC-32 is an integrity check, not a security mechanism.
2. There is no signed firmware validation yet.
3. There is no anti-rollback mechanism yet.
4. Boot metadata is not yet persisted in flash across power loss.
5. The current update/provisioning flow is development-oriented.
6. The payload demo is an OBC-side link supervision demo, not a full payload subsystem.
7. LaserCom is a simple demo transmitter, not a complete optical communications system.
8. More hardware-in-the-loop or FlatSat testing is needed for a stronger paper.

## Recommended Paper Positioning

Recommended title direction:

```text
Lightweight Boot and Runtime Fault Supervision for STM32-Based CubeSat-Class Firmware
```

Recommended contribution statement:

```text
This work presents a compact embedded firmware prototype that integrates
CRC-validated A/B boot selection, retained fault telemetry, health-gated
watchdog refresh, and payload-link fault supervision on an STM32G431RB
development board. The system is evaluated through unit tests and proposed
fault-injection scenarios targeting boot corruption, task starvation, and
payload communication failures.
```

Avoid claiming:

```text
New bootloader algorithm
Full secure boot
Production-ready CubeSat flight software
Replacement for cFS/F Prime/MCUboot
Complete payload subsystem
Complete optical communication stack
```

Claim instead:

```text
Lightweight integrated prototype
Resource-constrained safety architecture
Educational/research testbed
Fault-injection-ready framework
Boot-time plus runtime plus link-level fault supervision
```

## Suggested Related Work List

Research should include papers and docs around:

1. Robust CubeSat bootloader with OTA and rollback.
2. MCUboot design and image confirmation/rollback.
3. NASA cFS and F Prime as mature flight software frameworks.
4. CubeSat flight software case studies using FreeRTOS.
5. Fault injection platforms for CubeSat software.
6. Nanosatellite communication software interoperability testing.
7. Runtime verification and autonomous fault recovery in CubeSats.
8. Secure firmware update surveys for constrained IoT/CubeSat systems.

Potential references already identified in discussion:

```text
Sobreira et al., 2026,
"Case Study: A Robust Bootloader System with Support for Over-the-Air Firmware Updates in CubeSat Payloads"
DOI: 10.1109/LATS70329.2026.11480316

Wu and Xin, 2026,
"Porting NASA cFS Flight Software Framework to Safety Microcontroller TMS570 with FreeRTOS"
DOI: 10.3390/electronics15051020

Eshaq et al., 2025,
"CubeSat Flight Software: Insights and a Case Study"
DOI: 10.2514/1.A35882

Conceicao and Mattiello-Francisco, 2025,
"Systematic testing approach for communicating software embedded in nanosatellites focusing on interoperability faults"

Molina et al., 2023,
"Cubedate: Securing Software Updates in Orbit for Low-Power Payloads Hosted on CubeSats"
DOI: 10.23919/PEMWN58813.2023.10304910
```

The next agent should verify all bibliographic metadata before using citations in a paper.

## Build/Validation Notes

Known useful commands from the monorepo root:

```text
.\tools\test_native.ps1
.\tools\build_lasercom.ps1
.\tools\flash_lasercom.ps1
.\tools\build_payload_demo.ps1
.\tools\flash_payload_demo.ps1
.\tools\build_payload_responder.ps1
.\tools\flash_payload_responder.ps1
```

Known useful PlatformIO commands:

```text
cd core
pio test -e native
pio run -e nucleo_g431rb_payload_demo
pio run -e nucleo_g431rb_lasercom
pio run -e nucleo_g431rb

cd ../bootloader
pio test -e native
pio run -e nucleo_g431rb_lasercom

cd ../demo-payload
pio run -e nucleo_g474re
```

For bootloader provisioning, build the corresponding WashiOS-Core firmware first because the bootloader pre-build script reads the application ELF and computes its CRC.

Example conceptual flow:

```text
1. From `core/`, build WashiOS-Core env nucleo_g431rb_payload_demo.
2. From `bootloader/`, build Bootloader env nucleo_g431rb_payload_demo.
3. Bootloader script reads the core ELF, validates Slot A vector table, computes CRC, and injects build defines.
4. Upload the application image to Slot A without resetting.
5. Upload the matching bootloader last, then reset once.
6. From `demo-payload/`, build and upload env nucleo_g474re to the G474 payload board.
```

## Handoff Guidance For The Next AI Agent

The next AI agent should:

1. Treat the project as an applied embedded systems research prototype.
2. First build a related-work table comparing WashiBoot/WashiOS with MCUboot, cFS, F Prime, CubeSat bootloader papers, and CubeSat fault-injection/testing papers.
3. Then propose a clear experiment matrix.
4. Then help draft paper sections:
   - Introduction
   - Related Work
   - System Architecture
   - Bootloader Design
   - Runtime Safety Core
   - Payload Link Demo
   - Evaluation Methodology
   - Results
   - Limitations
   - Future Work
5. Avoid overclaiming security or flight readiness.
6. Emphasize measurable behavior, reproducibility, and small-MCU resource constraints.

## Plain-Language Explanation

This project builds firmware that tries to behave safely when something goes wrong.

The bootloader checks whether the main firmware looks valid before starting it. If the first firmware slot looks broken, it can try another slot. If nothing is valid, it stops in a visible safe loop.

The main firmware runs several FreeRTOS tasks. Each important task must periodically report that it is still alive. The watchdog is refreshed only when the important tasks are healthy. If a task gets stuck, the system records the fault and resets instead of silently continuing.

The payload demo sends poll messages to an external payload and checks the replies. It can detect bad CRCs, wrong sequence numbers, missing replies, offline payload state, and recovery back to online state.

The research value is not that any single mechanism is completely new. The value is the compact integration of boot safety, runtime safety, and payload-link supervision on a small STM32 platform, plus the potential to validate it with systematic fault injection and resource measurements.
