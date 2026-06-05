# WashiOS Flight Software Architecture Blueprint and Technical Reference Manual

Document status: Final handover manifest  
Project context: KNACKSAT-4 satellite flight software architecture  
Software baseline: Post-regression-audit, post-security-hardening, multi-target build verified  
Primary target: ST NUCLEO-G431RB / STM32G431RB  
Portability targets: STM32F411RE, Raspberry Pi Pico RP2040, ESP32 Dev Module  

---

## English Version

## 1. Executive Architectural Summary

### 1.1 Mission Goals

WashiOS is the embedded flight software foundation for the KNACKSAT-4 satellite program. Its mission is to provide a deterministic, resource-bounded, fault-aware execution platform suitable for small-satellite avionics, telemetry generation, health monitoring, and hardware-enforced recovery.

The system has four primary engineering goals:

1. Preserve mission-critical telemetry and fault evidence across reset boundaries.
2. Detect task stalls and corrupted software state before they can become silent mission failures.
3. Maintain strict static allocation discipline, eliminating runtime heap fragmentation from the flight software layer.
4. Demonstrate cross-platform portability across multiple CPU architectures without contaminating core mission logic with silicon-specific dependencies.

The final architecture has been validated across STM32G4, STM32F4, RP2040, and ESP32 build environments. The STM32G4 path is the primary flight-like reference implementation because it includes retained fault memory, FreeRTOS static tasking, telemetry streaming, and hardware Independent Watchdog synchronization.

### 1.2 Five-Layer Decoupled Architecture

WashiOS is organized as a five-layer decoupled architecture. Each layer has a strict ownership boundary and communicates upward or downward through narrow interfaces.

| Layer | Name | Responsibility | Examples |
|---:|---|---|---|
| 1 | Mission Application Layer | Periodic application behavior, telemetry generation, heartbeat activity, stress qualification tasks | `HeartbeatTask`, `TelemetryMockTask`, `WatchdogTask`, `StressTestTask` |
| 2 | Core Safety Kernel Layer | Fault logging, task-health evaluation, watchdog policy, TMR, CRC, reset abstraction | `FaultLog`, `TaskHealthRegistry`, `Watchdog`, `TMR`, telemetry CRC |
| 3 | RTOS and Static Tasking Layer | FreeRTOS integration, static task stacks, static task control blocks, scheduler start policy | `WashiTask`, `vApplicationGetIdleTaskMemory`, `vApplicationGetTimerTaskMemory` |
| 4 | Hardware Abstraction Layer | Stable hardware-neutral contracts for GPIO, UART, timing, and future buses | `IGPIO`, `IUart`, `ITiming`, `IAdc`, `ICanBus`, `II2cBus`, `ISpiBus` |
| 5 | Board Support Package and Silicon Layer | Target-specific register/HAL/Arduino bindings, linker memory sections, reset primitives | `src/bsp/g4`, `src/bsp/f4`, `src/bsp/rp2040`, `src/bsp/esp32` |

This layering ensures that flight behavior is not coupled to a vendor SDK. The application layer speaks only to core services and HAL interfaces. The STM32G4 implementation uses STM32Cube HAL internally, RP2040 and ESP32 use Arduino framework bindings internally, and the core safety kernel remains vendor-neutral.

### 1.3 Platform Isolation Strategy

WashiOS separates platform construction profiles in `platformio.ini`.

The STM32G4 profile builds the production-like FreeRTOS kernel path with:

- STM32Cube HAL.
- Static FreeRTOS allocation.
- Hardware IWDG configuration.
- Retained `.noinit` fault memory.
- USART2 telemetry output.

The STM32F4 profile validates that the same core architecture can cross-compile on another Cortex-M4 target with a separate BSP.

The RP2040 and ESP32 profiles validate architectural portability on a Cortex-M0+ and Xtensa dual-core platform respectively. Their BSP layers provide concrete `GpioDriver` and `UartDriver` implementations while preserving isolation from the central STM32 `src/main.cpp` flight path.

The resulting architecture demonstrates that WashiOS is not a board demo. It is a portable embedded operating architecture with a target-specific BSP perimeter and a stable mission-core interior.

---

## 2. Core Safety and Resilience Engine Specifications

### 2.1 Triple Modular Redundancy

The WashiOS core includes a software Triple Modular Redundancy mechanism for protecting critical scalar values against single-event upsets and cosmic-ray-induced bit flips.

The TMR model stores three copies of a protected value:

```text
copy[0] = V
copy[1] = V
copy[2] = V
```

On read, the system performs majority voting:

```text
if copy[0] == copy[1], return copy[0]
if copy[0] == copy[2], repair copy[1], return copy[0]
if copy[1] == copy[2], repair copy[0], return copy[1]
otherwise, declare unrecoverable corruption
```

The safety behavior has two classes:

| Fault class | Detection condition | Recovery behavior |
|---|---|---|
| Single-copy upset | Two copies agree and one differs | The differing copy is rewritten from the majority value; a `TmrCorrection` fault is recorded. |
| Multi-copy corruption | No two copies agree | The value is treated as unrecoverable; a `TmrUnrecoverable` fault is recorded and the deterministic fallback path is entered. |

This design is deterministic and allocation-free. It does not use heap memory, dynamic containers, exceptions, or recovery paths that depend on external services. The correction event is routed through the same `FaultLog` system used by watchdog and stack-fault telemetry.

### 2.2 Fast Nibble-Table CRC-32 Telemetry Verification

WashiOS telemetry frames use a compact fixed-size wire format with a CRC-32 integrity field.

The telemetry wire size is:

```text
TelemetryFrameWireSize = 28 bytes
```

The frame contains:

| Offset | Field | Width |
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

The CRC is computed over the first 24 bytes. The CRC field itself is zeroed before finalization. The implementation uses a 16-entry nibble table instead of a 256-entry byte table. This reduces static read-only data footprint while still providing fast deterministic execution.

The algorithm processes each byte in two 4-bit steps:

```text
crc = crc xor byte
crc = (crc >> 4) xor table[crc & 0x0F]
crc = (crc >> 4) xor table[crc & 0x0F]
```

The polynomial table corresponds to the reflected CRC-32 polynomial representation. The result is bitwise inverted at the end:

```text
final_crc = ~crc
```

This design gives three important flight properties:

1. Fixed execution path per byte.
2. No dynamic memory.
3. Small constant lookup table suitable for flash-constrained microcontrollers.

The optional `WASHIOS_PROFILE_CRC` build mode wraps CRC finalization with a Cortex-M DWT cycle counter so that maximum observed CRC latency can be measured during stress-test firmware runs.

### 2.3 TaskHealthRegistry and Watchdog Synchronization

The `TaskHealthRegistry` is the software health-status board for mission-critical tasks. Each registered task has:

- Task id.
- Deadline in milliseconds.
- Last check-in timestamp.
- Criticality flag.
- Health state.
- Violation report latch.

Heartbeat and telemetry tasks are registered as critical tasks in the STM32G4 flight path. Their nominal deadlines are:

| Task | Task id | Deadline |
|---|---:|---:|
| Heartbeat | 1 | 1500 ms |
| Telemetry | 2 | 800 ms |

The watchdog runner periodically evaluates the registry. If a critical task misses its deadline, the registry emits a `CriticalFailure` result and records `TaskCheckinFailure`. The watchdog layer records `WatchdogTimeout` and `SafeFail`.

The hardware Independent Watchdog is refreshed only when the registry reports that all registered critical tasks are healthy. The final audited implementation wraps the critical-task health iteration in a FreeRTOS critical section, preventing read-after-write races with task check-ins.

The logical gate is:

```text
if all critical tasks are healthy:
    refresh hardware watchdog
else:
    do not refresh hardware watchdog
```

### 2.4 STM32G4 Independent Watchdog Timing

For STM32G431RB, the IWDG uses the Low-Speed Internal oscillator:

```text
LSI ~= 32,000 Hz
Prescaler = 16
Reload = 3999
```

The watchdog counter clock is:

```text
IWDG counter frequency = 32,000 / 16 = 2,000 Hz
```

The reload value counts 4000 ticks:

```text
Timeout = (3999 + 1) / 2000 = 2.000 seconds
```

Therefore a critical task stall produces this recovery sequence:

1. Task stops checking in before its deadline.
2. `TaskHealthRegistry` marks it unhealthy.
3. `Watchdog` stops refreshing the IWDG.
4. IWDG expires after approximately 2000 ms.
5. MCU performs a hardware reset.
6. Retained fault log survives reset.
7. Telemetry task resumes and streams the previous-cycle failure snapshot.

This is a hardware-enforced recovery path. On STM32G4, the safe-fail callback records the fault but does not perform an immediate software reset, allowing the IWDG to remain the final reset authority.

---

## 3. Persistent Fault Tracking and Memory Topology

### 3.1 Retained Fault Memory Purpose

The fault log is designed to survive warm resets caused by software reset requests or hardware watchdog expiration. This is necessary because the most important telemetry is often the telemetry captured immediately before a fault.

If ordinary `.bss` memory were used, startup code would zero the log during reset, destroying the evidence. WashiOS therefore places the production `FaultLog` in a retained memory section using `WASHIOS_RETAINED`.

### 3.2 WASHIOS_RETAINED Macro

`WASHIOS_RETAINED` is defined in the cross-platform memory configuration layer.

| Platform | Retained mapping |
|---|---|
| STM32G4 | `__attribute__((section(".noinit"), aligned(8)))` |
| RP2040 | `__attribute__((section(".uninitialized_data"), aligned(8)))` |
| ESP32 | `__NOINIT_ATTR __attribute__((aligned(8)))` when available; otherwise `.noinit` fallback |
| Native host | Empty macro |

For STM32G4, the linker script explicitly maps `.noinit (NOLOAD)` into SRAM before `.bss`. This means the section is allocated in RAM but is not part of the firmware load image and is not zeroed during startup.

### 3.3 FaultLog Retained Structure

The retained `FaultLog` starts with a fixed 4-byte signature:

```text
WASHIOS_MAGIC_SIGNATURE = 0x55AA55AA
```

The signature is located at the absolute entry boundary of the retained structure, before event storage and index fields.

Conceptual layout:

```text
FaultLog retained block
| offset 0 | magic signature: 0x55AA55AA |
| next     | circular event storage       |
| next     | write index                  |
| next     | stored event count           |
| next     | total event count            |
```

### 3.4 Power-On Noise Rejection

Retained memory is valid after a warm reset only if the RAM contents were actually preserved. After a cold power-on, RAM can contain electrical noise. Random noise can accidentally look like small enum values, so enum-only validation is not sufficient.

The final recovery logic therefore validates in this order:

1. Verify `signature == WASHIOS_MAGIC_SIGNATURE`.
2. Verify ring-buffer indexes are within capacity.
3. Verify `totalCount >= storedCount`.
4. Verify each stored `FaultEventType` is a known enum value.

If any check fails, the log is scrubbed through explicit initialization loops:

```text
entries[i] = zero for every retained slot
writeIndex = 0
storedCount = 0
totalCount = 0
signature = 0x55AA55AA
```

This prevents random cold-boot RAM noise from being transmitted as valid flight telemetry.

### 3.5 Retained Fault Telemetry Flow

The intended warm-reset sequence is:

1. Critical task failure is detected.
2. Faults are recorded into retained `FaultLog`.
3. IWDG causes physical reset.
4. Startup calls `recoverRetainedState()`.
5. Magic signature and structural checks pass.
6. Telemetry task begins streaming the retained latest fault.

The intended cold-boot sequence is:

1. Startup calls `recoverRetainedState()`.
2. Magic signature is absent or corrupted.
3. Fault log is scrubbed and re-signed.
4. Telemetry begins with an empty fault database.

---

## 4. Minimum Hardware Requirements and Profiling Matrix

### 4.1 Final Production Footprint Matrix

The following metrics were refreshed from PlatformIO size reports after final security hardening. Heap consumption refers to WashiOS-controlled runtime heap allocation. The STM32 FreeRTOS profiles are configured for static allocation only, with dynamic allocation disabled.

| Target architecture | PlatformIO environment | Board | `.text` bytes | `.data` bytes | `.bss` bytes | Static RAM `.data + .bss` | WashiOS heap consumption |
|---|---|---|---:|---:|---:|---:|---:|
| STM32G4 / Cortex-M4F | `nucleo_g431rb` | NUCLEO-G431RB | 16,236 | 148 | 9,232 | 9,380 | 0 |
| STM32F4 / Cortex-M4F | `genericSTM32F411RE` | STM32F411RE | 14,232 | 1,200 | 8,088 | 9,288 | 0 |
| RP2040 / Cortex-M0+ | `raspberrypi_pico` | Raspberry Pi Pico | 75,202 | 0 | 38,956 | 38,956 | 0 |
| ESP32 / Xtensa dual-core | `esp32_dev` | ESP32 Dev Module | 199,433 | 71,068 | 4,973 | 76,041 | 0 |

### 4.2 Interpretation of Metrics

The STM32 targets are the smallest because the firmware uses STM32Cube HAL and a directly integrated FreeRTOS source tree with static allocation. The RP2040 and ESP32 images include Arduino framework overhead. Their larger `.text` and `.data` footprints reflect framework startup, serial support, and board-package runtime scaffolding, not an expansion of the WashiOS core safety model.

The `.data + .bss` column is the minimum static RAM pressure before runtime stack-depth safety margin. For custom PCB production, RAM capacity must exceed this value with sufficient margin for:

- Interrupt stack.
- FreeRTOS task stacks.
- Peripheral driver state.
- DMA or communication buffers.
- Future payload interface expansion.
- Radiation-event diagnostic expansion.

### 4.3 Minimum Hardware Specification for Custom PCB

The recommended minimum production microcontroller specification is:

| Requirement | Minimum | Recommended production margin |
|---|---:|---:|
| CPU class | 32-bit MCU | ARM Cortex-M4F or better |
| Clock frequency | 64 MHz | 100 MHz or higher |
| Flash | 128 KB | 256 KB or higher |
| SRAM | 32 KB | 64 KB or higher |
| Retained / no-init RAM support | Required | Dedicated linker-managed retained section |
| Hardware watchdog | Required | Independent oscillator watchdog preferred |
| UART | 1 TX channel minimum | Full duplex command and telemetry UART |
| GPIO | LED/status and interrupt-capable pins | Multiple EXTI lines with conflict validation |
| RTOS support | Static allocation capable | FreeRTOS static task and timer allocation |
| CRC support | Software acceptable | Hardware CRC optional |
| Debug | SWD/JTAG or equivalent | SWD/JTAG plus production recovery boot mode |

The STM32G431RB remains a strong minimum reference because it satisfies:

- 170 MHz Cortex-M4F execution.
- 128 KB flash.
- 32 KB SRAM.
- Independent watchdog with LSI oscillator.
- USART2 telemetry.
- Linker-managed `.noinit` retained memory.

For a custom production PCB, the preferred margin is at least 256 KB flash and 64 KB RAM to allow:

1. Additional payload drivers.
2. Real command uplink handling.
3. Expanded telemetry dictionaries.
4. Redundant sensor interfaces.
5. Larger retained fault history.
6. On-orbit diagnostic modes.

### 4.4 Final Verification Status

The final software baseline has passed:

- STM32G4 production build.
- STM32G4 stress/profiling build.
- STM32F4 portability build.
- RP2040 portability build.
- ESP32 portability build.
- Native SITL suite with 19/19 tests passing.

The architecture is therefore considered ready for handover into custom PCB integration and hardware-in-the-loop validation.

---

# คู่มือภาษาไทย

# พิมพ์เขียวสถาปัตยกรรมซอฟต์แวร์การบิน WashiOS และคู่มืออ้างอิงทางเทคนิค

สถานะเอกสาร: เอกสารส่งมอบขั้นสุดท้าย  
บริบทโครงการ: สถาปัตยกรรมซอฟต์แวร์การบินสำหรับดาวเทียม KNACKSAT-4  
ฐานซอฟต์แวร์: ผ่านการตรวจ Regression Audit และการเสริมความปลอดภัยขั้นสุดท้ายแล้ว  
เป้าหมายหลัก: ST NUCLEO-G431RB / STM32G431RB  
เป้าหมายการพอร์ต: STM32F411RE, Raspberry Pi Pico RP2040, ESP32 Dev Module  

---

## 1. สรุปสถาปัตยกรรมระดับผู้บริหาร

### 1.1 เป้าหมายภารกิจ

WashiOS คือฐานซอฟต์แวร์ฝังตัวสำหรับโครงการดาวเทียม KNACKSAT-4 มีเป้าหมายเพื่อเป็นแพลตฟอร์มการทำงานที่กำหนดเวลาได้ชัดเจน ใช้ทรัพยากรแบบมีขอบเขต ตรวจจับความผิดปกติได้ และสามารถกู้คืนระบบด้วยกลไกฮาร์ดแวร์เมื่อซอฟต์แวร์เข้าสู่สถานะไม่ปลอดภัย

เป้าหมายหลักของระบบมี 4 ข้อ:

1. รักษาข้อมูลความผิดปกติและเทเลเมทรีสำคัญให้คงอยู่ข้ามการรีเซ็ต
2. ตรวจจับงานที่หยุดตอบสนองหรือสถานะซอฟต์แวร์ที่เสียหายก่อนกลายเป็นความล้มเหลวแบบเงียบ
3. ใช้หน่วยความจำแบบ static allocation เท่านั้น เพื่อตัดความเสี่ยงจาก heap fragmentation
4. แสดงความสามารถในการพอร์ตข้ามสถาปัตยกรรม CPU โดยไม่ผูก mission logic เข้ากับ vendor SDK

ระบบรุ่นสุดท้ายผ่านการตรวจบน STM32G4, STM32F4, RP2040 และ ESP32 โดยเส้นทาง STM32G4 เป็น reference implementation หลัก เพราะรวม retained fault memory, FreeRTOS static tasking, telemetry streaming และ hardware watchdog synchronization ไว้ครบถ้วน

### 1.2 สถาปัตยกรรมแบบแยกชั้น 5 ระดับ

WashiOS ใช้สถาปัตยกรรมแบบแยกชั้น 5 ระดับ แต่ละชั้นมีขอบเขตความรับผิดชอบชัดเจนและสื่อสารกันผ่าน interface ที่แคบและเสถียร

| ชั้น | ชื่อ | หน้าที่ | ตัวอย่าง |
|---:|---|---|---|
| 1 | Mission Application Layer | พฤติกรรมของ application, telemetry, heartbeat, stress task | `HeartbeatTask`, `TelemetryMockTask`, `WatchdogTask`, `StressTestTask` |
| 2 | Core Safety Kernel Layer | fault log, task health, watchdog policy, TMR, CRC, reset abstraction | `FaultLog`, `TaskHealthRegistry`, `Watchdog`, `TMR` |
| 3 | RTOS and Static Tasking Layer | FreeRTOS, static stacks, static TCB, scheduler policy | `WashiTask`, idle/timer memory hooks |
| 4 | Hardware Abstraction Layer | interface กลางสำหรับ GPIO, UART, timing และ bus อื่น | `IGPIO`, `IUart`, `ITiming` |
| 5 | BSP and Silicon Layer | driver เฉพาะชิป, linker section, reset primitive | `src/bsp/g4`, `src/bsp/f4`, `src/bsp/rp2040`, `src/bsp/esp32` |

ผลลัพธ์คือ application logic ไม่พึ่งพา vendor SDK โดยตรง STM32G4 ใช้ STM32Cube HAL ภายใน BSP, RP2040 และ ESP32 ใช้ Arduino framework ภายใน BSP ส่วน core safety kernel ยังคงเป็นโค้ดกลางที่ไม่ขึ้นกับ silicon

---

## 2. สเปกระบบความปลอดภัยและการกู้คืน

### 2.1 Triple Modular Redundancy

WashiOS มีระบบ Triple Modular Redundancy หรือ TMR เพื่อป้องกันตัวแปรสำคัญจาก bit flip ที่เกิดจากรังสีคอสมิกหรือ single-event upset

ระบบเก็บค่าหนึ่งค่าเป็น 3 สำเนา:

```text
copy[0] = V
copy[1] = V
copy[2] = V
```

เมื่ออ่านค่า ระบบใช้ majority voting:

```text
ถ้า copy[0] == copy[1] ให้คืนค่า copy[0]
ถ้า copy[0] == copy[2] ให้ซ่อม copy[1] แล้วคืนค่า copy[0]
ถ้า copy[1] == copy[2] ให้ซ่อม copy[0] แล้วคืนค่า copy[1]
ถ้าไม่มีคู่ใดตรงกัน ให้ประกาศว่า unrecoverable
```

| ประเภทความผิดปกติ | เงื่อนไขตรวจพบ | พฤติกรรมกู้คืน |
|---|---|---|
| สำเนาเดียวเสีย | มี 2 สำเนาตรงกันและ 1 สำเนาต่าง | ซ่อมสำเนาที่ต่างและบันทึก `TmrCorrection` |
| หลายสำเนาเสีย | ไม่มี 2 สำเนาที่ตรงกัน | บันทึก `TmrUnrecoverable` และเข้าสู่ fallback path |

ระบบนี้ทำงานแบบ deterministic และไม่ใช้ heap memory, container, exception หรือ recovery path ที่ต้องพึ่งบริการภายนอก

### 2.2 Fast Nibble-Table CRC-32

Telemetry frame ของ WashiOS มีขนาดคงที่ 28 bytes และมี CRC-32 สำหรับตรวจสอบความถูกต้อง

โครงสร้างเฟรม:

| Offset | Field | ขนาด |
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

CRC คำนวณจาก 24 bytes แรก โดยตั้งค่า field CRC เป็นศูนย์ก่อน finalization

ระบบใช้ตาราง 16 entries แบบ nibble table แทนตาราง 256 entries เพื่อลด footprint ใน flash และยังคงเวลา execution ที่แน่นอน

หลักการคำนวณต่อ byte:

```text
crc = crc xor byte
crc = (crc >> 4) xor table[crc & 0x0F]
crc = (crc >> 4) xor table[crc & 0x0F]
```

คุณสมบัติสำคัญ:

1. เส้นทางการประมวลผลคงที่ต่อ byte
2. ไม่ใช้ dynamic memory
3. ตาราง lookup มีขนาดเล็ก เหมาะกับ microcontroller ที่มี flash จำกัด

### 2.3 TaskHealthRegistry และ Watchdog

`TaskHealthRegistry` เป็นกระดานสถานะสุขภาพของ task สำคัญ แต่ละ task มี:

- task id
- deadline
- เวลา check-in ล่าสุด
- critical flag
- health state
- latch สำหรับรายงาน violation

บน STM32G4 task สำคัญคือ:

| Task | Task id | Deadline |
|---|---:|---:|
| Heartbeat | 1 | 1500 ms |
| Telemetry | 2 | 800 ms |

ถ้า task critical ไม่ check-in ภายใน deadline ระบบจะ:

1. บันทึก `TaskCheckinFailure`
2. บันทึก `WatchdogTimeout`
3. บันทึก `SafeFail`
4. หยุด feed hardware watchdog
5. ปล่อยให้ IWDG reset MCU

การอ่านสถานะ critical task ถูกครอบด้วย FreeRTOS critical section แล้ว เพื่อป้องกัน data race ระหว่าง watchdog task กับ task ที่กำลัง check-in

### 2.4 การคำนวณ IWDG บน STM32G4

ค่า watchdog:

```text
LSI ~= 32,000 Hz
Prescaler = 16
Reload = 3999
```

ความถี่ counter:

```text
32,000 / 16 = 2,000 Hz
```

เวลา timeout:

```text
(3999 + 1) / 2000 = 2.000 seconds
```

ดังนั้นถ้า task critical หยุดตอบสนอง ระบบจะไม่ refresh IWDG และ MCU จะถูก reset โดยฮาร์ดแวร์หลังประมาณ 2 วินาที

---

## 3. Persistent Fault Tracking และ Memory Topology

### 3.1 เหตุผลของ Retained Fault Memory

Fault log ต้องอยู่รอดข้าม warm reset เพราะข้อมูลที่สำคัญที่สุดมักเกิดขึ้นก่อน reset เพียงเล็กน้อย ถ้าใช้ `.bss` ปกติ startup code จะล้างข้อมูลทิ้งทั้งหมด WashiOS จึงใช้ `WASHIOS_RETAINED` เพื่อวาง log ไว้ใน memory section ที่ไม่ถูก zero-initialize

### 3.2 WASHIOS_RETAINED

| Platform | Mapping |
|---|---|
| STM32G4 | `.noinit`, aligned 8 |
| RP2040 | `.uninitialized_data`, aligned 8 |
| ESP32 | `__NOINIT_ATTR` หรือ `.noinit`, aligned 8 |
| Native host | ว่าง |

บน STM32G4 linker script กำหนด `.noinit (NOLOAD)` ใน SRAM ก่อน `.bss` ทำให้ข้อมูลใน section นี้ไม่ถูกโหลดใหม่และไม่ถูกล้างระหว่าง reset

### 3.3 WASHIOS_MAGIC_SIGNATURE

`FaultLog` มี signature 4 bytes ที่ตำแหน่งเริ่มต้นของ retained structure:

```text
WASHIOS_MAGIC_SIGNATURE = 0x55AA55AA
```

layout เชิงแนวคิด:

```text
FaultLog retained block
| offset 0 | magic signature |
| next     | fault entries   |
| next     | write index     |
| next     | stored count    |
| next     | total count     |
```

### 3.4 การกรอง RAM Noise ตอน Cold Boot

หลัง cold boot, RAM อาจมีค่าขยะจากไฟฟ้า หากตรวจเฉพาะ enum อาจเกิด false positive ได้ เพราะ enum มีค่าขนาดเล็ก ระบบจึงตรวจตามลำดับ:

1. signature ต้องเท่ากับ `0x55AA55AA`
2. index ต้องอยู่ในขอบเขต capacity
3. `totalCount >= storedCount`
4. event type ทุกตัวต้องเป็น enum ที่รู้จัก

ถ้าตรวจไม่ผ่าน ระบบจะล้าง log ด้วย loop ที่ชัดเจน:

```text
entries ทั้งหมด = 0
writeIndex = 0
storedCount = 0
totalCount = 0
signature = 0x55AA55AA
```

ผลคือ cold-boot RAM noise จะไม่ถูกส่งเป็น telemetry จริง

---

## 4. Minimum Hardware Requirements และ Profiling Matrix

### 4.1 ตาราง Footprint ขั้นสุดท้าย

ตัวเลขต่อไปนี้มาจาก PlatformIO size report หลังการ hardening ขั้นสุดท้าย

| Target architecture | Environment | Board | `.text` bytes | `.data` bytes | `.bss` bytes | Static RAM `.data + .bss` | WashiOS heap |
|---|---|---|---:|---:|---:|---:|---:|
| STM32G4 / Cortex-M4F | `nucleo_g431rb` | NUCLEO-G431RB | 16,236 | 148 | 9,232 | 9,380 | 0 |
| STM32F4 / Cortex-M4F | `genericSTM32F411RE` | STM32F411RE | 14,232 | 1,200 | 8,088 | 9,288 | 0 |
| RP2040 / Cortex-M0+ | `raspberrypi_pico` | Raspberry Pi Pico | 75,202 | 0 | 38,956 | 38,956 | 0 |
| ESP32 / Xtensa dual-core | `esp32_dev` | ESP32 Dev Module | 199,433 | 71,068 | 4,973 | 76,041 | 0 |

### 4.2 การตีความตัวเลข

STM32 มี footprint ต่ำที่สุดเพราะใช้ STM32Cube HAL และ FreeRTOS source ที่ผนวกโดยตรง ส่วน RP2040 และ ESP32 มี footprint สูงขึ้นเนื่องจาก framework overhead ของ Arduino/Mbed และ ESP-IDF/FreeRTOS runtime ไม่ใช่เพราะ WashiOS core ขยายตัวมากขึ้น

ค่า `.data + .bss` คือแรงกดดัน RAM แบบ static ขั้นต่ำก่อนคำนึงถึง margin สำหรับ interrupt stack, task stack, DMA, driver state และ payload interface ในอนาคต

### 4.3 Minimum Hardware Specification สำหรับ Custom PCB

| Requirement | ขั้นต่ำ | แนะนำสำหรับ production |
|---|---:|---:|
| CPU | 32-bit MCU | ARM Cortex-M4F หรือสูงกว่า |
| Clock | 64 MHz | 100 MHz ขึ้นไป |
| Flash | 128 KB | 256 KB ขึ้นไป |
| SRAM | 32 KB | 64 KB ขึ้นไป |
| Retained RAM | จำเป็น | มี linker-managed retained section |
| Hardware watchdog | จำเป็น | independent oscillator watchdog |
| UART | TX อย่างน้อย 1 ช่อง | full duplex command/telemetry |
| GPIO | status LED และ interrupt pins | หลาย EXTI lines พร้อม conflict validation |
| RTOS | static allocation capable | FreeRTOS static task/timer allocation |
| CRC | software CRC ได้ | hardware CRC เป็น optional |
| Debug | SWD/JTAG หรือเทียบเท่า | SWD/JTAG พร้อม recovery boot mode |

STM32G431RB เหมาะเป็น production reference เพราะมี:

- Cortex-M4F 170 MHz
- Flash 128 KB
- SRAM 32 KB
- IWDG พร้อม LSI oscillator
- USART2 telemetry
- `.noinit` retained memory ผ่าน linker script

สำหรับ custom PCB แนะนำให้เผื่ออย่างน้อย 256 KB flash และ 64 KB RAM เพื่อรองรับ payload driver, command uplink, telemetry dictionary, sensor redundancy, retained log ที่ใหญ่ขึ้น และ diagnostic mode บนวงโคจร

### 4.4 สถานะ Verification ขั้นสุดท้าย

ซอฟต์แวร์ baseline ขั้นสุดท้ายผ่าน:

- STM32G4 production build
- STM32G4 stress/profiling build
- STM32F4 portability build
- RP2040 portability build
- ESP32 portability build
- Native SITL 19/19 tests

สถาปัตยกรรม WashiOS พร้อมส่งมอบเข้าสู่ขั้น custom PCB integration และ hardware-in-the-loop validation
