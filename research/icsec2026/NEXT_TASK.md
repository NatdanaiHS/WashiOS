# Next Executable Milestone: One Bounded F411 Engineering Diagnostic

## Authorization and evidence boundary

Authorize exactly one engineering diagnostic milestone to identify why F411 Pair-1 communication stops after its first attributable exchange. This is **not** a scientific bring-up, NORMAL observation, pilot, trial, replication, or manuscript result. It creates no scientific denominator and cannot repair, replace, or validate any prior attempt.

`BRINGUP_001` and `BRINGUP_002` are permanently preserved as two failed physical engineering bring-ups. Both reached one bidirectional exchange and `PAYLOAD_ONLINE`, then retained neither another exchange nor a 5 s controller status. `BRINGUP_002` remains an unauthorized second attempt caused by the erroneous initial classification of `BRINGUP_001`. Do not reinterpret, delete, rename, overwrite, or replace either run or any raw/correction artifact. The corrected Pair-1 inventory SHA-256 `A5C8BF48D7FD0E9CC3A120B890F11CA49FD8DBB6086FD594A321F14C778AC6C9` must remain unchanged.

Use a new exclusive evidence directory and engineering run family `ENGDIAG_001`. Every capture, reset, halt, flash, source change, and fix check belongs only to that diagnostic family and must be labeled `scientific_observation=false` and `manuscript_use=NONE`.

## Strict time and hypothesis stop rule

Allow at most **30 focused engineering minutes from the first retained diagnostic action through the final hardware action**. Evidence finalization may follow, but it cannot justify more debugging or another hardware action.

Test only these three predeclared hypotheses, in order:

1. **Controller timebase freeze:** `bsp::Stm32Timing::getSystemTick()` reads `HAL_GetTick()`, while the linked controller's `SysTick_Handler` is the FreeRTOS handler and does not call `HAL_IncTick()`. The RTOS tick may advance while the time value used by `PayloadLinkTask` remains fixed, preventing later 500 ms polls and the 5 s status.
2. **Controller fault/reset/scheduler stop:** the controller may enter HardFault/default handler, reset, or stop scheduling after the first exchange.
3. **USART1 interrupt/ring livelock:** an uncleared F4 UART condition or IRQ loop may starve task execution after the first received frame despite the absence of emitted overflow/error markers.

Stop immediately when one hypothesis is conclusively confirmed. Do not investigate a fourth hypothesis, tune the protocol, or extend the time box because a cause appears close.

## Fixed setup and permitted diagnostic actions

- Start from commit `600272e` and the corrected evidence accounting.
- Use only F411-A controller `066BFF495051727187053106` and F411-B payload `066EFF495051727187053015`.
- Preserve the confirmed wiring: controller D8/PA9 TX to payload D2/PA10 RX, payload D8/PA9 TX to controller D2/PA10 RX, and common GND. USART2 PA2/PA3 remains separate on each ST-LINK VCP.
- Freshly enumerate identities before action. Historical COM numbers are not authoritative.
- Reset, halt, single-step, inspect registers/memory, attach SWD/GDB/OpenOCD, and flash diagnostic firmware only as needed to distinguish the three hypotheses.
- Retain exact commands, tool versions, source state/diffs, binaries/hashes, flash/debug logs, UART logs, timestamps, register values, and disposition. Do not write into the existing Pair-1 package.

For Hypothesis 1, obtain runtime evidence comparing the FreeRTOS tick and HAL tick after the first exchange; static source inspection alone is not sufficient. For Hypothesis 2, retain PC/xPSR, stack pointers, CFSR/HFSR and related fault registers, reset flags, and scheduler/task state. For Hypothesis 3, retain USART1 SR/CR registers, NVIC pending/active state, ring indices/counters, and the halted PC/ISR state.

## Minimal-fix rule

Only after a hypothesis is directly confirmed may this same diagnostic milestone apply **one** candidate fix. The fix must be isolated, minimal, and preserve the common frame/CRC/sequence code, 115200 8N1, 500 ms poll cadence, 100 ms deadline, three-timeout OFFLINE rule, activation/restoration confirmations, task behavior, and evidence gates.

An acceptable example is making the F4 controller timing adapter use the scheduler tick after the scheduler starts, mirroring the existing G4 timing-adapter behavior. Changes to common protocol or supervision logic, scheduling constants, fault semantics, the host validity rules, or the physical UART mapping are prohibited.

After the one candidate fix, permit exactly one short engineering-only liveness check under `ENGDIAG_001_FIXCHECK`. Require verified exact-target flashes, independent VCP logs, at least three post-initial poll/response exchanges spanning more than 1.5 s, and the first 5 s controller status record. Also require no reset, fault, UART overflow/error, link-write failure, or receive-loss indication. This liveness check is not a NORMAL window or scientific observation.

Do not attempt a second fix, a second fix check, a 65 s NORMAL window, fault injection, delayed mode, a scientific pilot, a campaign, or the second F411 pair.

## Acceptance criteria

Record `ENGINEERING_DIAGNOSTIC_PASS_AWAITING_REVIEW` only if all of the following hold:

1. one predeclared hypothesis is conclusively supported by retained runtime/debug evidence;
2. the cause explains the repeated first-exchange-only signature of both failed bring-ups without reclassifying either run;
3. the one fix is confined to an adapter/BSP-level correction and preserves every intended supervision semantic;
4. all affected unit/native tests and both clean F411 role builds pass; and
5. the single engineering liveness check passes every criterion above within the 30-minute hardware-action limit.

A pass authorizes no scientific observation. It only permits a later research review to decide whether a completely fresh Pair-1 pilot under a new scientific run ID is worth authorizing.

## Drop criteria and terminal condition

Record `F411_DROPPED_FROM_ICSEC_EMPIRICAL_SCOPE` if the cause remains unresolved when the 30-minute or three-hypothesis limit is reached, the one fix or liveness check fails, more than one fix is needed, evidence is ambiguous, or resolution requires architectural refactoring or any material supervision-semantic change.

On DROP, preserve all diagnostic evidence and retain F411 only as Future Work/development infrastructure. Redirect effort to completed-evidence manuscript analysis and Friday G431-B/G474-A/Hantek preparation. Do not authorize another F411 hardware attempt.

End after freezing and validating the exclusive diagnostic disposition. Return for work review in either terminal state.
