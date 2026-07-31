# WashiOS

WashiOS is a deterministic, resource-bounded embedded flight software foundation for small-satellite and mission-critical avionics experiments. It is built around static allocation, retained fault telemetry, task-health supervision, watchdog-enforced recovery, and portable board-support boundaries across STM32 and native host simulation targets.

The primary flight-like reference target is **ST NUCLEO-G431RB / STM32G431RB**. The current portability target is **STM32F411RE**; native host simulation is used for safety-kernel regression tests.

## Project Goals

- Preserve mission-critical fault evidence across warm resets.
- Detect task stalls, corrupted state, and unsafe startup conditions deterministically.
- Maintain a strict **0-byte WashiOS-controlled dynamic heap** discipline.
- Keep core flight logic independent from vendor SDKs through HAL and BSP isolation.
- Provide repeatable host-side SITL tests for safety logic before hardware deployment.

## Architecture

WashiOS is organized as a five-layer architecture:

| Layer | Name | Responsibility |
|---:|---|---|
| 1 | Mission Application | Heartbeat, telemetry, watchdog task, stress task |
| 2 | Core Safety Kernel | Fault log, TMR, CRC, task health, watchdog policy, boot fail-safe |
| 3 | RTOS / Static Tasking | FreeRTOS static task stacks and TCBs |
| 4 | Hardware Abstraction | GPIO, UART, timing, ADC, CAN, I2C, SPI, PWM interfaces |
| 5 | BSP / Silicon | STM32 HAL implementations |

Core code lives under `include/core/` and is intentionally hardware-neutral. Target-specific code is contained under `src/bsp/` and `include/bsp/`.

## Safety Features

### Static Allocation

WashiOS avoids runtime heap allocation in flight-controlled code. FreeRTOS tasks are created through static allocation using `xTaskCreateStatic()`, with task stacks and task control blocks stored in fixed-size objects.

Relevant files:

- `include/rtos_config/WashiTask.hpp`
- `include/rtos_config/FreeRTOSConfig.h`
- `src/main.cpp`

### Retained FaultLog With CRC-32

`FaultLog` stores fault events in retained memory so reset-cause evidence can survive watchdog or software resets.

Protection model:

- Magic signature: `WASHIOS_MAGIC_SIGNATURE = 0x55AA55AA`
- Structure-wide CRC-32 over retained logical fields
- CRC recomputed after `record()` and retained-state initialization
- Recovery rejects cold-boot garbage, bit flips, bad indexes, invalid event types, and CRC mismatch
- Failed recovery scrubs the log through deterministic clean loops

Relevant files:

- `include/core/FaultLog.hpp`
- `include/bsp/CrossPlatformConfig.hpp`
- `include/ldscripts/STM32G431RBTX_FLASH.ld`

### Triple Modular Redundancy

The TMR engine protects critical scalar values by storing three copies and majority-voting on read. Single-copy corruption is repaired and logged. Multi-copy disagreement is treated as unrecoverable and routed into deterministic fault handling.

Relevant file:

- `include/core/TMR.hpp`

### Task Health And Watchdog Gating

`TaskHealthRegistry` tracks registered task check-ins and deadlines. The watchdog refresh path is blocked unless all critical tasks are healthy.

The STM32G4 reference build uses the Independent Watchdog with:

- LSI clock: approximately 32 kHz
- Prescaler: 16
- Reload: 3999
- Timeout: approximately 2 seconds

Relevant files:

- `include/core/TaskHealth.hpp`
- `include/core/Watchdog.hpp`
- `include/core/WatchdogRunner.hpp`
- `src/app/WatchdogTask.hpp`

### Boot Fail-Safe

Startup task creation is guarded. If any critical task fails to start, WashiOS records a `SafeFail` event and enters the deterministic recovery path instead of starting a partially initialized scheduler.

Relevant file:

- `include/core/BootFailSafe.hpp`

## Telemetry Frame

WashiOS telemetry uses a fixed 28-byte wire frame with CRC-32 over the first 24 bytes.

| Offset | Field | Size |
|---:|---|---:|
| 0 | Sync byte 0 | 1 byte |
| 1 | Sync byte 1 | 1 byte |
| 2 | Version | 1 byte |
| 3 | Frame size | 1 byte |
| 4 | Sequence number | 4 bytes |
| 8 | Uptime milliseconds | 4 bytes |
| 12 | Task health mask | 4 bytes |
| 16 | Fault event count | 4 bytes |
| 20 | Latest fault type | 1 byte |
| 21 | Latest fault task id | 1 byte |
| 22 | Reserved | 2 bytes |
| 24 | CRC-32 | 4 bytes |

Relevant file:

- `include/core/Telemetry.hpp`

## Supported PlatformIO Environments

| Environment | Target | Purpose |
|---|---|---|
| `nucleo_g431rb` | STM32G431RB | Primary flight-like STM32G4 build |
| `nucleo_g431rb_slot_b` | STM32G431RB | Slot B linker-layout validation |
| `nucleo_g431rb_stress` | STM32G431RB | Stress/profiling build with CRC profiling |
| `nucleo_g431rb_lasercom` | STM32G431RB | GPIO optical telemetry demo |
| `nucleo_g431rb_payload_demo` | STM32G431RB | UART payload-supervision demo |
| `genericSTM32F411RE` | STM32F411RE | STM32F4 portability build |
| `native` | Host | Unity SITL test environment |

## Build And Test

Install PlatformIO first, then run commands from the repository root.

Run the native SITL regression suite:

```powershell
pio test -e native
```

Build all firmware targets:

```powershell
pio run -e genericSTM32F411RE -e nucleo_g431rb -e nucleo_g431rb_stress
```

Clean all firmware target outputs:

```powershell
pio run -t clean -e genericSTM32F411RE -e nucleo_g431rb -e nucleo_g431rb_stress
```

## Verification Status

Current verified baseline:

- Native SITL: **38/38 tests passed**
- Core firmware builds: **6/6 STM32 environments passed**
- WashiOS-controlled heap usage: **0 bytes**

This baseline was re-verified on 31 July 2026. The repository-level delivery
status also records the 11/11 WashiBoot tests, three matching bootloader
builds, and the demo-payload responder build.

The SITL suite covers:

- HAL mock behavior
- TMR repair and unrecoverable fallback
- Retained `FaultLog` wrapping, garbage rejection, and CRC bit-flip rejection
- Watchdog critical and non-critical timeout behavior
- Selective starvation of one critical task
- Atomic task health summary evaluation
- Boot fail-safe task startup rejection path
- Telemetry packing and CRC validation

## Repository Layout

```text
include/
  bsp/              Cross-platform retained-memory and BSP headers
  core/             Safety kernel: FaultLog, TMR, CRC, telemetry, watchdog
  hal/              Hardware-neutral interface contracts
  rtos_config/      FreeRTOS configuration and static task wrapper
src/
  app/              Flight application tasks
  bsp/              Target-specific BSP implementations
  core/             Optional profiling implementation
  stress/           Stress/profiling task
test/
  mocks/            Host-side HAL and runtime mocks
  test_sitl/        Unity SITL regression suite
lib/
  FreeRTOS/         Integrated FreeRTOS source subset
scripts/            PlatformIO build guard scripts
```

## Development Rules

- Keep flight code deterministic and allocation-free.
- Do not introduce dynamic containers or runtime heap allocation into core flight paths.
- Keep target-specific SDK details inside BSP layers.
- Add native SITL tests for new safety behavior.
- Run `pio test -e native` and all firmware builds before delivery.
- Treat retained memory, watchdog refresh, and boot fail-safe paths as mission-critical.

## License

No explicit license file is currently included. Add a license before publishing this repository publicly.
