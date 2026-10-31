# F411 Source, Pin, and VCP Feasibility — 2026-09-01

Decision: **F411_GO for Checkpoint 1 only**

Engineering risk for later port/bring-up: **HIGH**

Decision time: 2026-09-01T20:20:00+07:00
Branch/source checkpoint audited: `experiment/icsec-extension-20260830` at `0fbd98fe367faaeee7da8aa360755bee807f7a36`

This is an engineering feasibility record, not experimental evidence. No F411 firmware was changed, built for an experimental role, flashed, reset, or executed. The firmware already present on the four boards was left untouched. Commit `0fbd98f`, the recovered baseline copies, frozen baseline, reviewed extension packages, and their inventories were not modified.

## 1. Gate scope and time box

The authorized work was Checkpoint 1 in `NEXT_TASK.md`: enumerate the boards, verify pin/VCP separation, build the existing generic F411 environment, audit the smallest role ports, and decide GO/NO-GO. It did not authorize role implementation, flashing, wiring, pair bring-up, or experiment execution.

The first retained feasibility timestamp is 2026-09-01T19:55:45+07:00 and the gate decision is recorded at 20:20:00+07:00, an observed interval of 24 minutes 15 seconds. Preliminary Git/source reading occurred before the first retained timestamp, but the entire checkpoint remained within the 60-minute limit.

## 2. Board identities and host ports

Only two USB ports were available. The four boards were therefore enumerated in two sequential batches. The human assigned names by the mass-storage drive visible in each batch; software then joined that drive to the ST-LINK serial and VCP through the USB parent identity. The ST-LINK serial, not the drive letter or COM number, is the durable identifier.

| Board | Batch | Human mapping during enumeration | Durable ST-LINK serial | VCP observed | PnP state |
|---|---:|---|---|---|---|
| F411-A | 1 | D: | `066BFF495051727187053106` | COM16 | Started |
| F411-B | 1 | E: | `066EFF495051727187053015` | COM11 | Started |
| F411-C | 2 | D: | `0669FF495051727187053226` | COM12 | Started |
| F411-D | 2 | E: | `0663FF495051727187066042` | COM6 | Started |

All four serial identities are unique. Both two-board batches exposed one ST-Link Debug interface, one MBED mass-storage interface, and one STMicroelectronics STLink Virtual COM Port per board using USB VID:PID `0483:374B`. No driver or COM collision was observed in either batch.

Four-board simultaneous attachment was **not tested** because the PC has only two physical USB ports. This does not block the gated plan: Checkpoints 2–6 use one pair, and Checkpoint 7 uses the second pair only after the first pair is frozen and reviewed. A four-board concurrent run is not required. If it is later desired for convenience, a powered hub and a fresh four-device enumeration check are engineering prerequisites, not a scientific prerequisite.

Machine-readable enumeration: `research/icsec2026/extension/evidence/f411_feasibility_20260901/BOARD_ENUMERATION.json`.

## 3. Authoritative pin and VCP mapping

Primary references:

- STMicroelectronics UM1724, *STM32 Nucleo-64 boards (MB1136)*, Table 16 and the USART2/VCP solder-bridge description: <https://www.st.com/resource/en/user_manual/um1724-stlinkv21-in-circuit-debuggerprogrammer-for-stm8-and-stm32-stmicroelectronics.pdf>
- STMicroelectronics STM32F411xC/xE datasheet, alternate-function mapping for PA9/PA10: <https://www.st.com/resource/en/datasheet/stm32f411re.pdf>
- Installed PlatformIO `nucleo_f411re.json`, SHA-256 `560FCA0523A7474E34C2F2623BB2AAB488E7EB3A30145C7FD12A9D3657B10AA8`.

Locked mapping for a later checkpoint:

| Purpose | MCU peripheral | Controller pin/header | Payload pin/header | Wiring/host use |
|---|---|---|---|---|
| Host observation/control | USART2 | PA2 TX / PA3 RX, D1/D0, default ST-LINK VCP | PA2 TX / PA3 RX, D1/D0, default ST-LINK VCP | No external wire; independent USB VCP per board |
| Inter-board payload link | USART1 | PA9 TX / PA10 RX, D8/D2 | PA9 TX / PA10 RX, D8/D2 | Controller D8→payload D2; payload D8→controller D2; common GND |

UM1724 identifies D8 as PA9, D2 as PA10, D1 as PA2/USART2_TX, and D0 as PA3/USART2_RX. The STM32F411 datasheet maps PA9 and PA10 to USART1 TX and RX with AF7. USART1 is therefore electrically separate from the default USART2 ST-LINK VCP. The required pair wiring is three jumper wires and requires no solder-bridge change.

The installed Nucleo board definition selects STM32F411RET6, 100 MHz, 512 KiB flash, 128 KiB RAM, onboard/default ST-LINK, and `st_nucleo_f4`. Explicit later role environments must use `board = nucleo_f411re`, not the generic board's default serial upload path.

## 4. Existing build environments and toolchain sanity

Existing F411 environment: `core/platformio.ini` has only `genericSTM32F411RE`. It builds the generic controller/telemetry composition, not the payload-supervision controller role. `demo-payload/platformio.ini` has no F411 environment.

The required sanity command completed successfully without source changes:

`C:\Users\wachi\.platformio\penv\Scripts\platformio.exe run -d C:\WashiOS\core -e genericSTM32F411RE`

- PlatformIO Core 6.1.19; ST STM32 platform 19.6.0.
- STM32CubeF4 1.28.1; GCC ARM 7.2.1.
- Result: SUCCESS in 19.666 s.
- RAM: 7,748/131,072 bytes (5.9%); flash: 15,404/524,288 bytes (2.9%).
- `firmware.bin`: 15,832 bytes, SHA-256 `B5524BD395023202D096FEF374820F1C0637717CC75698AA27E1E8208AAB9E5A`.
- `firmware.elf`: 155,072 bytes, SHA-256 `F723A3A1BF9EFB1B334C77A97FFB9B2CC3603228BCBC21BBC55C28234933BFBB`.

These binaries are toolchain-sanity artifacts only and were not flashed. Machine-readable build record: `research/icsec2026/extension/evidence/f411_feasibility_20260901/TOOLCHAIN_SANITY.json`.

## 5. Exact source gaps

| Area | Current state | Required bounded change |
|---|---|---|
| Controller environment | Only generic F411 environment exists. The experimental controller composition is guarded by `WASHIOS_PAYLOAD_DEMO && STM32G431xx`. | Add an explicit standalone `nucleo_f411re_payload_controller` environment and a narrow F411 role define. Keep default link origin `0x08000000`; do not add a bootloader. |
| Controller host UART | F4 `main.cpp` initializes USART2 PA2/PA3. Current `Stm32Uart` uses blocking HAL TX/RX and `available()` always returns zero. | Keep USART2 for VCP. Supply an isolated F4 interrupt-driven/bounded UART implementation where receive is needed; retain bounded blocking TX only where it cannot affect supervision timing. |
| Controller link UART | No F411 USART1 PA9/PA10 link initialization or IRQ receive path exists. | Add isolated F411 USART1 AF7 board initialization, IRQ dispatch, bounded RX ring, explicit overflow count/marker, and instantiate the unchanged `PayloadLinkTask`. |
| Common controller semantics | `PayloadLinkController` already owns frame/CRC/sequence processing and constants 500 ms, 100 ms, and three consecutive timeouts. `PayloadLinkTask` consumes at most 64 received bytes per cycle through nonblocking `available()`. | Reuse unchanged. Do not refactor the common controller/task/protocol. Only widen the composition guard to the explicit F411 role. |
| Payload environment | `demo-payload` has G474 and native environments only. | Add explicit standalone `nucleo_f411re_payload` environment with F4-only source selection. |
| Payload board code | `demo-payload/src/main.cpp` hard-includes G4 HAL, uses G4 UART/FIFO/status-register details, G474 pins, and a G474 READY marker. | Add an isolated F411 board/main implementation for USART2 PA2/PA3 host and USART1 PA9/PA10 link. Reuse the command parser and common wire protocol; use F4 SR/DR IRQ semantics and bounded rings with explicit overflow counters. |
| Payload control/parser | Fixed-capacity parser already supports exact `NORMAL`, `SILENT`, `BAD_CRC`, and `DELAYED n` commands. | Reuse unchanged. Preserve exact activation confirmation and NORMAL restoration markers, changing only the board/config identity field. |
| Host harness | Primary primitives accept ports and parse common markers, but wrappers, filenames, firmware assumptions, READY string, and board labels are G431/G474-specific; replication wrapper assumes a G431 bootloader/application flow. | Add a separate F411 wrapper using the proven capture/gate/trial primitives. Use standalone binaries, ST-LINK serial-bound roles, F411 READY identities, pair-specific paths, and overflow markers as prohibited validity events. Do not change reviewed G431/G474 evidence or rerun it. |

## 6. Smallest planned file set for Checkpoint 2

This is a plan only; none of these changes was made in Checkpoint 1.

1. Edit `core/platformio.ini` to add an explicit Nucleo F411 controller-role environment.
2. Add `core/include/bsp/f4/Stm32F411InterruptUart.hpp` and `core/src/bsp/f4/Stm32F411InterruptUart.cpp` for fixed-capacity RX, IRQ/error handling, and overflow accounting.
3. Add `core/include/bsp/f4/Stm32F411BoardUart.hpp` and `core/src/bsp/f4/Stm32F411BoardUart.cpp` for USART2 VCP plus USART1 PA9/PA10 initialization; make only a narrow role-selection edit in `core/src/main.cpp`.
4. Edit `demo-payload/platformio.ini` and add an F4-selected payload source under `demo-payload/src/f4/`, reusing `HostModeCommandParser.hpp` and common protocol headers unchanged.
5. Add native tests for F4 ring/overflow behavior; retain all existing core and payload-parser tests.
6. Add a separate F411 pair harness/config under `research/icsec2026/extension/`; do not generalize or edit frozen run evidence.

If implementation reveals that these changes require a common UART/protocol/controller/parser architecture refactor, the FINAL_PUSH_PLAN stop condition applies and this GO must be revoked.

## 7. Semantic equivalence lock

| Construct | Locked behavior | F411 preservation mechanism | Verification required before bring-up |
|---|---|---|---|
| Frame/protocol | Existing fixed frame, CRC, and sequence rules | Reuse common protocol and `PayloadLinkController` unchanged | Existing native tests plus cross-role build inspection |
| Link format | 115200 8N1 | USART1 AF7 on PA9/PA10 in both roles | Initialization inspection and loop/link traffic check |
| Poll cadence | 500 ms | Existing `PollPeriodMs = 500` | Unit tests and retained timestamps |
| Response deadline | 100 ms | Existing `ResponseTimeoutMs = 100` | Unit tests and pilot marker ordering |
| OFFLINE rule | Three consecutive timeouts | Existing `OfflineThreshold = 3` | Unit tests and later valid raw evidence |
| Fault activation | Exact payload-side confirmation before exposure | Reuse parser modes and confirmation markers | Harness activation gate |
| NORMAL restoration | Exact payload confirmation; never infer from send | Reuse parser/markers | Restore gate in both logs |
| Inter-trial stabilization | ONLINE/counter/forbidden-marker gate | Reuse proven harness primitives with F411 identities | Pre/post gate records |
| Deployment | Standalone application at `0x08000000` | Nucleo environments; no bootloader | Link map and flash-address check |
| Evidence boundary | Pair-specific exact-byte dual logs; no pooling | Separate F411 paths/ledgers/inventories | Independent validation and review |

The F411 hardware watchdog behavior is not assumed identical to the G431 build and must not be represented as such. It is outside the locked UART supervision construct unless a later implementation conflict shows otherwise.

## 8. Required tests and later hardware checks

Before any flash, Checkpoint 2 must require:

- ring empty/single/wrap/full behavior;
- deterministic overflow counting without memory overwrite;
- RX/error IRQ clearing and recovery;
- bounded task consumption and no blocking receive path;
- both explicit role builds from clean outputs;
- all applicable existing native/parser/host tests;
- exact linker origin and binary hashes;
- static confirmation that common protocol/controller/parser files are unchanged.

Later physical bring-up must verify, without ambiguity:

- roles selected by durable ST-LINK serial, never COM number alone;
- independent READY/control on both USART2 VCPs;
- crossed USART1 PA9/PA10 plus common ground;
- bidirectional framed traffic at 115200 8N1;
- no reset ambiguity, UART receive loss, overflow, or host/link sharing;
- all fault confirmations, restoration, and stabilization gates before any retained pilot.

## 9. Gate decision

**F411_GO** is justified because:

- the board and MCU mappings provide independent USART2 VCP and USART1 link paths without solder changes;
- all four boards have unique durable ST-LINK identities and individually enumerate a VCP;
- two independent physical F411↔F411 pairs are technically feasible and may be used sequentially as required by the gated plan;
- the common protocol, CRC/sequence, timeout/OFFLINE controller, task, and payload command parser can remain unchanged;
- the missing code is confined to explicit environments, isolated F4 board/UART implementations, narrow composition guards, tests, and a separate harness wrapper; and
- the existing F411 toolchain target builds successfully.

Risk remains **HIGH** because neither experimental role currently exists on F411, current F4 receive is blocking/nonfunctional for `available()`, the payload is G4-register-specific, overflow tests do not yet exist, and the later port/bring-up has a strict 120-minute budget. GO means only that the port is credible and bounded; it does not predict successful bring-up or authorize Checkpoint 2.

No experimental result, direct G431/G474 comparison, timing claim, pooled denominator, or population claim is supported by this checkpoint.
