# Model-to-Source Trace

Every model transition, constant, and abstraction is tied to the source it represents. Line numbers are
for branch `paper/icsec-formal-verification` at its creation (based on
`paper/icsec-confirmation-gated-final` commit `cf8fa9b`). Re-verify with `grep -n` before citing.

**These line numbers describe the analysed revision, before the F4 fix.** The fix (`resetBootAttempts()` before `activateBootSlot()` on the fallback path, verified as configuration `boot_f4fix`) adds `resetBootAttempts()` to `BootMetadata.hpp` and eight lines to `BootPolicy.hpp::run()`, so in a fixed tree the fallback block is at `BootPolicy.hpp:94-99` and `isPendingBootAttemptLimitExceeded()` at `:132`. Findings F1-F4 and every model constant refer to the pre-fix revision.

## Constants

| Model constant | Value | Source |
|---|---:|---|
| `POLL_MS` | 500 | `core/include/comms/PayloadLinkController.hpp:32` |
| `DEADLINE_MS` | 100 | `core/include/comms/PayloadLinkController.hpp:33` |
| `OFFLINE_N` | 3 | `core/include/comms/PayloadLinkController.hpp:34` |
| `LOOP_MS` | 1 | `core/src/app/PayloadLinkTask.hpp:17` |
| `PL_PERIOD_MS` (health check-in) | 100 | `core/src/app/PayloadLinkTask.hpp:18`, `:175-176` |
| `HB_PERIOD_MS` | 500 | `core/src/app/HeartbeatTask.hpp:44` |
| `HB_DEADLINE_MS` | 1500 | `core/src/main.cpp:74`, registered `:252-253` |
| `PL_DEADLINE_MS` | 800 | `core/src/main.cpp:75` (`TelemetryDeadlineMs`; `PayloadLinkTaskId = TelemetryTaskId`, `:65-67`), registered `:256-257` |
| `WD_POLL_MS` | 100 | `core/src/main.cpp:79`, `WatchdogRunner.hpp` `runOnce()` |
| `WD_TASK_MS` | 50 | `core/src/main.cpp:80`, `core/src/app/WatchdogTask.hpp:28` |
| `IWDG_NOMINAL_MS` / `IWDG_MIN_MS` / `IWDG_MAX_MS` | 2000 / 1882 / 2170 | `core/src/main.cpp:433-434` (prescaler 16, reload 3999); DS12589 Rev 6 Table 44 (f_LSI 29.5–34 kHz) |
| `MAX_UNCONFIRMED` | 3 | `bootloader/include/boot/BootPolicy.hpp:16` |
| `DELAY_MS` default | 250 | `demo-payload/src/main.cpp:15` (`DefaultDelayedResponseMs`) |
| `TX_MIN_MS`/`TX_MAX_MS` | 3/4 | derived: 32-byte frame (`PayloadProtocol.hpp:12`) at 115200 8N1 = 2.78 ms plus decode/encode |
| `EXPOSURE_MS`/`RECOVERY_MS` | 4000/3000 | `research/icsec2026/injector/run_payload_campaign.py:488-489` defaults used by the frozen campaign |

## Payload-link model (`models/payload_link.xml`)

| Model element | Source behavior |
|---|---|
| `Controller.Idle → Awaiting` on `xPoll >= POLL_MS`, `poll!` | `preparePoll()` `PayloadLinkController.hpp:53-73`; deadline and next poll anchored at send time `:69-70` |
| `Awaiting` invariant `xResp <= DEADLINE + LOOP + JITTER` | timeout is evaluated in `service()` once per loop iteration `PayloadLinkTask.hpp:44-50` |
| `Awaiting → Idle` on `resp_ok?`, `onAccept()` | `acceptResponse()` Ok path `:108-118`: clears awaiting, zeroes consecutive, sets Online, counts recovery if was Offline |
| `Awaiting → Awaiting` on `resp_badcrc?` | `acceptResponse()` BadCrc branch `:84-90` increments `crcRejects` only; awaiting untouched |
| `Awaiting → Idle` on `xResp >= DEADLINE`, `onTimeout()` | `service()` `:36-51`: `awaitingResponse=false`, `timeouts++`, `consecutive++` (saturating at 255 `:42-45`), Offline at threshold `:46-49` |
| `Idle → Idle` on `resp_ok?`, `seqRejects++` | `acceptResponse()` `:99-102`: `!awaitingResponse || frame.sequence != expectedSequence` |
| receive-before-service ordering | `Run()` loop order `receiveFrames`, `serviceController`, `sendPoll` `PayloadLinkTask.hpp:45-47` |
| Marker `PAYLOAD_TIMEOUT` / `PAYLOAD_OFFLINE` | `serviceController()` `:127-145`, `logTimeout()` `:259`, `logOffline()` `:268` |
| Marker `PAYLOAD_RECOVERED` / `PAYLOAD_ACCEPTED` / `PAYLOAD_REJECT` | `receiveFrames()` `:88-125`, `logRecovery()` `:235`, `logAccepted()` `:224`, `logRejection()` `:244` |
| `Payload.Ready → Responding` on `poll?` when `mode != SILENT` | `handleRequest()` `demo-payload/src/main.cpp:298-345`: SILENT returns at `:318-321` |
| `Responding` delay `DELAY_MS` for DELAYED | `HAL_Delay(delayedResponseMs)` `:328` |
| `resp_badcrc!` for BAD_CRC | CRC byte flipped after encoding `:340-343` |
| Mode captured at request time (`pending = mode`) | `currentMode` read inside `handleRequest()`; host command applies mode before `logMode()` (`:240-248`) |
| `Host.Nominal → Faulted` only when `link == ONLINE` | harness precondition observation and payload confirmation gate `run_payload_campaign.py:391-409` |

## Watchdog-gating model (`models/watchdog_gating.xml`)

| Model element | Source behavior |
|---|---|
| `Task(id)` check-in sets `healthy[id] = true` and resets `since[id]` | `TaskHealthRegistry::checkIn()` `core/include/core/TaskHealth.hpp:69-80` |
| `Supervisor` expiry edges `since[id] > DEADLINE[id]` | `evaluate()` `:96-104` (`deltaMs > deadlineMs`) |
| `criticalFailed` set once | `newlyReportedFailure` and `violationReported` `:106-115`; `Watchdog::poll()` records `WatchdogTimeout` and `SafeFail` `core/include/core/Watchdog.hpp:42-58` |
| `kick!` only on the edge where both clocks are within deadline and both flags healthy | `Watchdog.hpp:61-65` (`areAllCriticalTasksHealthy()`), `TaskHealth.hpp:179-197` |
| Safe-fail callback does not reset on G431 | `targetSafeFail()` `core/src/main.cpp:81-93` (`requestSystemReset()` only under `!STM32G431xx`) |
| Watchdog poll cadence | `WatchdogRunner::runOnce()` (`>= periodMs`), called every 50 ms by `WatchdogTask` |
| IWDG expiry → reset | hardware; configured `Board_IWDG_Init()` `core/src/main.cpp:433-435` |
| Both modelled tasks are critical | `registerTask(..., critical = true, ...)` `core/src/main.cpp:252-258` (verify flag values before citing) |

## Boot-policy model (`models/boot_policy.xml`)

| Model element | Source behavior |
|---|---|
| `Start → SafeLoop` when `metadataCorrupt` | `run()` `BootPolicy.hpp:47-57`: `RetainedStateRecoveryStatus::Corrupt` → `safeFail(DetailFaultLogRecoveryFailed)` |
| `normalizeConfirmed()` | `normalizeConfirmedBoot()` `BootMetadata.hpp:243-258` |
| `loopLimit()` | `isPendingBootAttemptLimitExceeded()` `BootPolicy.hpp:126-131` → `safeFail(DetailBootLoopLimit)` `:64-67` |
| `retainedCriticalFault` → `SafeLoop` | `hasPriorCriticalFault()` `:233-251` (TaskCheckinFailure or WatchdogTimeout) → `safeFail(DetailPriorCriticalFault)` `:70-73` |
| `slotBootable()` | `isSlotBootable()` `:159-193`: bootable state, vector table, provisioned CRC, CRC match (default-CRC adoption `:178-183` abstracted into `imageOf`) |
| `launch()` increments `bootCount` | `bootSlot()` `:220-229` → `noteBootAttempt()` `BootMetadata.hpp:261-266` |
| fallback activates other slot | `activateBootSlot()` `BootMetadata.hpp:274-278`, `run()` `:86-92` |
| `SafeLoop` never exits on warm reset | `Stm32G4Beacon::enterSafeLoop()` `bootloader/src/bsp/g4/Stm32G4Beacon.cpp:37-45` (infinite loop; only a hardware reset restarts `main()`, which re-reads the same retained state) |
| `coldStart` scrubs retained state | `.noinit` SRAM has no defined content after power loss; `FaultLog` recovery rejects garbage (`FaultLog.hpp:87-`, `:252-272`) and `recoverBootMetadata()` reinitializes (`BootMetadata.hpp:208-224`) |
| `App` never sets `confirmedFlag` (APP_CONFIRMS = 0) | no reference to `BootMetadata`, `confirmed_flag`, or `BootMetadataConfirmed` anywhere under `core/` (verified 2026-09-08 with `git grep`) |

## Verified bounds (inclusive) and their derivation

| Bound | Value | Derivation from source constants |
|---|---:|---|
| first timeout after confirmed fault onset | 605 ms | poll may be up to `POLL+J` after the previous poll (`nextPollMs` anchored at the actual send, `PayloadLinkController.hpp:70`), then deadline `D` evaluated once per `LOOP` with jitter `J`: `P+J+D+L+J` |
| OFFLINE after confirmed fault onset | 1609 ms | three polls each up to `P+J`, then `D+L+J`: `3(P+J)+D+L+J` |
| ONLINE after confirmed restoration | 506 ms | next poll up to `P+J`, response serialization up to `TX_MAX`: `P+J+TX_MAX` |
| stall detection (payload-link task) | 952 ms | `deadline 800` strict-greater test at a poll instant, next poll up to `WD_POLL+WD_TASK+J = 152` later |
| stall detection (heartbeat) | 1652 ms | `1500 + 152` |
| stall to IWDG reset | detection + 2170 ms | no refresh after detection (W2) plus the slow-LSI IWDG period bound (A3, datasheet-derived) |

Tightness: each `T` query in the `.q` files replaces `>` by `>=` and is NOT satisfied, i.e. the event can occur exactly at the bound.

## Finding F4: fallback bypasses the unconfirmed-boot limit

| Model element | Source behavior |
|---|---|
| `loopLimit()` evaluated once on `active` in `Recovered` | `run()` `BootPolicy.hpp:64-67` calls `isPendingBootAttemptLimitExceeded()` which reads `firmwareSlotState(metadata, activeBootSlot())` and `metadata.boot_count` (`:126-131`) |
| fallback edge `active = 1 - active, launch(active, true)` with no second limit check | `run()` `:86-92`: `activateBootSlot()` then `bootSlot()`; `activateBootSlot()` (`BootMetadata.hpp:274-278`) changes `active_slot` only and leaves `boot_count` |
| `bootCount` accumulates while a Confirmed slot runs | `noteBootAttempt()` increments on every launch (`:261-266`); only `normalizeConfirmedBoot()` (`:243-258`) resets it, and the application never sets the flag (F1) |
| B8c: next warm boot after the over-limit fallback launch is refused | `run()` `:64-67` on the now-active Pending slot with the inherited count |

## Abstractions and assumptions

- **A1 (jitter).** FreeRTOS wakeups and UART ISR latency are bounded by `JITTER_MS = 2` ms. Justification: 1 kHz tick, three tasks, no long critical sections in the modelled paths. Not measured. Sensitivity: the
  first-timeout bound is 601 + 2J ms; the delay-acceptance edge at 95 ms does not depend on J, while the
  timeout edge is 99 + J, so the undetermined band is 96 to 98 + J ms. Verified at J ∈ {0, 1, 2, 5} ms
  (`payload_delayed_100_j*`); for J ≤ 1 ms the model decides d = 100 ms as a timeout.
- **A2 (serialization).** A 32-byte frame completes 3–4 ms after the sender begins transmission. Justification: 320 bit-times at 115200 baud = 2.78 ms plus decode/encode work under 1 ms.
- **A3 (LSI tolerance).** IWDG period lies in [1882, 2170] ms around the 2000 ms nominal. Source: STM32G431 datasheet DS12589 Rev 6 (Oct 2021), Table 44, f_LSI = 29.5–34 kHz over VDD 1.62–3.6 V and −40..125 °C; period = 4000·16/f_LSI; Table 79 note 2 adds at most one LSI period (34 µs) of APB/LSI phasing uncertainty, absorbed by the ceiling.
- **A4 (lossless channel).** No UART byte loss or corruption other than the injected BAD_CRC. The frozen N0 and 605 s observations showed zero CRC or sequence rejects, supporting this for the bench setup only.
- **A5 (single outstanding response).** `DELAY_MS < POLL_MS`; a delayed response never overlaps the next poll. The 500 ms sweep condition in the extension package (invalid restoration) is outside the model.
- **A6 (boot CRC).** CRC-32 and vector-table checks are abstracted to a boolean image validity chosen by the environment; CRC collision is not modelled.
