# WashiOS

WashiOS is the current implementation workspace for the KNACKSAT-4 K4-Core foundation: a reusable Core OS + Hardware Abstraction Layer framework for satellite-class embedded software.

This repository is not the final KNACKSAT-4 flight application. Its job is to become the standard platform underneath future mission logic: deterministic RTOS services, hardware-neutral HAL contracts, board-specific drivers, software-in-the-loop mocks, hardware-in-the-loop tests, and resilience patterns for space-grade firmware.

The deeper architecture source is `KNACKSAT4_Master_Blueprint.md`. This README is the execution roadmap from the current repo state.

## Current State Vs Blueprint

### Already In Place

- PlatformIO project targeting `genericSTM32F411RE` with the STM32Cube framework.
- Native PlatformIO environment for host-side SITL tests.
- Vendored FreeRTOS kernel under `lib/FreeRTOS`.
- Static-only FreeRTOS configuration:
  - `configSUPPORT_STATIC_ALLOCATION` is enabled.
  - `configSUPPORT_DYNAMIC_ALLOCATION` is disabled.
  - `configTOTAL_HEAP_SIZE` is `0`.
- `rtos_config::WashiTask<StackDepth>` wraps `xTaskCreateStatic()` so application tasks own their task control block and stack.
- Demo tasks exist:
  - `HeartbeatTask` toggles the PA5 LED every 1000 ms and reports health.
  - `TelemetryMockTask` emits fixed-size telemetry frames every 500 ms and reports health.
- Strict C++ build flags disable exceptions and RTTI.
- HAL interface headers exist for GPIO, I2C, SPI, UART, timing, ADC, CAN, and PWM.
- GPIO includes a hardware-neutral interrupt registration contract using a fixed callback pointer and opaque context.
- CAN, ADC, and PWM include small hardware-neutral status/state types for diagnostics and mock simulation.
- Core safety-service headers exist under `include/core`.
- `TMR<T>` provides majority voting, one-copy repair, and fault logging.
- Static `FaultLog` records TMR, watchdog, task health, stack overflow, assert, and safe-fail events.
- `TaskHealthRegistry` and `Watchdog` provide host-testable liveness monitoring and safe-fail callback behavior.
- `WatchdogRunner` periodically invokes the watchdog monitor from an active runtime loop.
- SITL runtime tests register heartbeat and telemetry task IDs, execute periodic check-ins, and verify watchdog safe-fail behavior.
- `HeartbeatTask` and `TelemetryMockTask` expose health check-in hooks for target-side integration.
- `TelemetryFrame` defines a fixed-size K4 telemetry packet with sync bytes, sequence, uptime, task health, fault summary, and CRC-32.
- The telemetry pipeline serializes frames into deterministic little-endian wire bytes and validates corruption through CRC.
- SITL telemetry writes real serialized frames into a fixed-size mock UART transport buffer.
- `WatchdogTask` provides a FreeRTOS `WashiTask` wrapper for running the watchdog monitor on target.
- `src/main.cpp` now statically wires the production `FaultLog`, `TaskHealthRegistry`, `Watchdog`, `WatchdogRunner`, `WatchdogTask`, heartbeat task, and telemetry task.
- Target startup registers heartbeat and telemetry task IDs before launching the scheduler.
- STM32 system clock configuration initializes the HSI PLL for a 100 MHz SYSCLK target.
- STM32 BSP drivers exist for GPIO, timing, UART, and system reset.
- `Stm32Timing` uses HAL milliseconds and the Cortex-M4 DWT cycle counter for microsecond delays.
- `Stm32Gpio` drives the PA5 onboard LED through the `IGPIO` interface.
- `Stm32Uart` binds telemetry transport to USART2 for future host serial inspection.
- `HeartbeatTask` now toggles the PA5 LED while still reporting task health.
- The target watchdog safe-fail callback records a critical fault and requests a CMSIS software reset through the BSP reset path.
- The STM32 stack-overflow hook records a fault event before requesting reset.
- Fixed-storage mock HAL drivers exist under `test/mocks`.
- Native Unity SITL tests exist under `test/test_sitl`.
- Hard-float compiler and linker flags are configured for the STM32F411RE Cortex-M4F FPU.

### Still Missing From The Blueprint

- Persistent or retained fault storage across resets.
- Independent hardware-watchdog reset control beyond the current CMSIS software reset path.
- Hardware-in-the-loop test plan across STM32 first, then ESP32 or Pi Pico later.
- Stress test procedure using an external host such as Raspberry Pi 4.
- Profiling for stack, `.bss`, `.data`, `.text`, and CPU idle time.
- Minimum hardware requirements document for the board team.
- FreeRTOS source version and local modification notes.

## Phase 1 Implementation Notes

Phase 1 now establishes the architecture and software-in-the-loop foundation.

- `platformio.ini` has separate STM32 and native environments.
- The STM32 environment keeps the Cortex-M4F hard-float flags.
- The native environment builds host-side tests without STM32 HAL.
- `include/hal/*.hpp` remains chip-neutral and does not include STM32 headers.
- Mock drivers use fixed arrays, counters, and function pointers rather than dynamic allocation.
- SITL tests prove HAL-driven logic can execute through interfaces only.

## Phase 2 Implementation Notes

Phase 2 now establishes the Core OS safety-service foundation.

- `include/core/FaultLog.hpp` implements a fixed-capacity ring fault log.
- `include/core/TMR.hpp` implements allocation-free Triple Modular Redundancy with automatic one-copy scrubbing.
- `include/core/TaskHealth.hpp` implements a fixed-capacity task health registry using numeric task IDs.
- `include/core/Watchdog.hpp` implements a hardware-neutral watchdog monitor driven by `hal::ITiming`.
- `include/core/WatchdogRunner.hpp` adds periodic poll scheduling for the watchdog monitor.
- `test/mocks/SitlRuntime.hpp` runs heartbeat, telemetry, and watchdog services together in native SITL.
- SITL tests cover TMR clean reads, injected copy corruption, unrecoverable TMR disagreement, watchdog critical timeout, non-critical timeout, and fault-log wraparound.
- SITL tests also cover nominal runtime operation and a stalled telemetry task triggering safe-fail.
- The watchdog task wrapper is instantiated in target startup using placeholder timing until the BSP exists.

## Telemetry Pipeline Notes

Roadmap Item 3 is implemented in native SITL.

- `include/core/Telemetry.hpp` owns the fixed-size packed frame definition and CRC-32 helpers.
- Frame sync bytes are `0x4B 0x34` for K4.
- The wire frame is 28 bytes and uses explicit little-endian serialization.
- The frame includes sequence number, uptime, task health bitmask, fault-event count, latest fault type, latest fault task ID, and trailing CRC-32.
- `TelemetryMockTask` can assemble and transmit real frames when configured with timing, task health, fault log, and `IUart` transport dependencies.
- `test/mocks/SitlRuntime.hpp` routes telemetry into `MockUart` so host tests can inspect emitted packets.
- SITL tests cover nominal packing, CRC validation, bit-flip corruption detection, and runtime frame emission.

## Stage 1 STM32 BSP Notes

Stage 1 STM32 BSP and board wiring are implemented for `genericSTM32F411RE`.

- `include/bsp/Stm32Gpio.hpp` and `src/bsp/Stm32Gpio.cpp` implement the `IGPIO` contract with STM32Cube HAL calls.
- `include/bsp/Stm32Timing.hpp` and `src/bsp/Stm32Timing.cpp` implement the `ITiming` contract with HAL ticks and DWT-backed microsecond delays.
- `include/bsp/Stm32Uart.hpp` and `src/bsp/Stm32Uart.cpp` implement the `IUart` contract for blocking UART transport.
- `src/bsp/SystemReset.cpp` owns the STM32 reset primitive used by fatal core paths.
- `src/main.cpp` configures clocks, GPIOA, USART2, PA5 heartbeat LED, task registration, watchdog startup, and telemetry dependency injection.
- Vendor headers remain contained in BSP implementation files and the STM32 target entry point.

## Next Work Roadmap

### 1. Add Retained Fault Storage

The current target fault log is RAM-resident only.

First targets:

- Decide retained RAM or flash-backed fault storage.
- Preserve latest fault records across reset when possible.
- Include reset/fault summary in telemetry after boot.

### 2. Validate Hardware-In-The-Loop On STM32

The firmware now compiles with real STM32 BSP drivers. The next validation step is hardware.

First targets:

- Flash the `genericSTM32F411RE` build to the board.
- Confirm PA5 heartbeat LED toggles at the expected cadence.
- Confirm USART2 emits valid 28-byte telemetry frames.
- Verify watchdog reset behavior with a deliberate missed check-in test build.

### 3. Create The Cross-Board Plan

The blueprint asks for proof that the same logic can run across boards. Do this in stages.

Recommended order:

1. STM32F411RE only, with real GPIO and UART.
2. STM32 HIL test driven by a host computer or Raspberry Pi.
3. Add a second platform after the STM32 path is stable, preferably ESP32 or Pi Pico.
4. Demonstrate that application logic uses HAL interfaces and does not change when the board target changes.

### 4. Profile And Produce Hardware Requirements

The final framework output should guide the hardware team.

Collect:

- Flash usage from `.text`.
- RAM usage from `.bss` and `.data`.
- Per-task stack high-water marks.
- Idle-time or CPU-load estimate.
- Required peripherals: GPIO, UART, I2C, SPI, timers, watchdog, and optional CAN/ADC/PWM.
- Minimum RAM and flash recommendation with margin.
- Known timing assumptions and clock requirements.

Deliver this as a hardware requirements document once the STM32 BSP, watchdog, telemetry, and profiling hooks exist.

## Blueprint Timeline, Adjusted For This Repo

### Phase 1, Weeks 1-2: Architecture And Interfaces

Status: implemented as a foundation.

Done:

- PlatformIO project exists.
- HAL interface headers exist.
- GPIO interrupt contract exists.
- Static FreeRTOS foundation exists.
- Strict C++ safety flags are configured.
- Mock HAL drivers exist.
- Software-in-the-loop tests exist.

### Phase 2, Weeks 3-5: Core OS And TMR

Status: implemented as a host-testable foundation.

Done:

- Add task health registry.
- Add watchdog monitor.
- Add watchdog runner and FreeRTOS task wrapper.
- Add `TMR<T>`.
- Add TMR correction and fault counters.
- Add basic fault reporting.
- Add SITL runtime simulation for nominal and stalled-task behavior.
- Add fixed-size telemetry frame, CRC-32, serialization, and SITL transport tests.

Remaining:

- Add retained fault storage and hardware watchdog reset behavior.

### Phase 3, Weeks 6-8: Cross-Platform HIL

Status: blocked until STM32 BSP exists.

Next:

- Implement STM32 BSP first.
- Prove real GPIO heartbeat and UART telemetry.
- Add host-driven HIL tests.
- Add ESP32 or Pi Pico only after STM32 behavior is stable.

### Phase 4, Weeks 9-10: Stress Test And Hardware Handover

Status: future milestone.

Next:

- Stress test UART/I2C/SPI paths.
- Measure RAM, flash, stacks, and CPU idle time.
- Write minimum hardware requirements for the board team.
- Record limitations and accepted risks.

## Build And Test

Build STM32 firmware:

```powershell
pio run -e genericSTM32F411RE
```

Run native SITL tests:

```powershell
pio test -e native
```

Or with the known local PlatformIO executable:

```powershell
C:\Users\wachi\.platformio\penv\Scripts\pio.exe run -e genericSTM32F411RE
C:\Users\wachi\.platformio\penv\Scripts\pio.exe test -e native
```

STM32 artifacts are generated under `.pio/build/genericSTM32F411RE/`.

## Project Map

```text
WashiOS/
  KNACKSAT4_Master_Blueprint.md   Blueprint and long-term architecture source
  README.md                       Current execution roadmap
  platformio.ini                  STM32 and native SITL PlatformIO config
  scripts/
    hard_float_link.py            Adds hard-float linker flags for STM32
    strict_cpp_flags.py           Adds no-exceptions, no-RTTI, and warning flags for C++
  src/
    main.cpp                      STM32 startup, task creation, RTOS hooks
    app/                          Current demo tasks
    bsp/                          STM32 HAL-backed BSP driver implementations
  include/
    bsp/                          STM32 BSP driver interfaces
    core/                         Hardware-neutral Core OS safety services
    core/Telemetry.hpp            Fixed-size telemetry frame and CRC helpers
    hal/                          Hardware-neutral C++ HAL interfaces
    rtos_config/                  FreeRTOS config and WashiTask wrapper
  test/
    mocks/                        Fixed-storage HAL mocks for SITL
    mocks/SitlRuntime.hpp         Host runtime simulation for app task and watchdog loops
    test_sitl/                    Native Unity SITL test skeleton
  lib/
    FreeRTOS/                     Vendored FreeRTOS kernel
```

## Working Rules

- HAL interfaces define what hardware must do; BSP drivers define how a specific chip does it.
- Application logic should depend on `include/hal` interfaces, not STM32 HAL directly.
- `src/main.cpp` and future BSP files may include STM32 headers; `include/hal/*.hpp` must not.
- Static memory allocation is the default rule.
- C++ exceptions and RTTI are disabled.
- Timeouts are mandatory for bus operations.
- SITL mocks must use fixed storage, not heap allocation.
- Faults should be recorded before halt or reset whenever possible.
- The main success criterion is not a single mission demo. It is a reusable, testable, portable software standard for KNACKSAT-4 and future satellites.
