# Next Executable Milestone: Fresh F411 Pair-1 Scientific Pilot

## Authorization and claim boundary

Authorize exactly one completely fresh F411 Pair-1 scientific pilot using the fixed implementation at commit `0ce8a5c`.

- Exclusive evidence package: `research/icsec2026/extension/evidence/f411_pair1_scientific_pilot_20260901/`.
- Pilot run ID: `F411_P1_SCI_PILOT_001_D110`.
- Precondition record ID: `F411_P1_SCI_PILOT_001_D110_PRECHECK`.
- Condition: one 110 ms delayed-response exposure only.

This is one descriptive scientific pilot on one F411-to-F411 configuration. It is not a campaign result, replication count, reliability estimate, population sample, or manuscript result unless a later scientific review explicitly accepts its evidence and wording. Do not pool it with G431/G474, the failed F411 bring-ups, the engineering diagnostic, or any later campaign.

`BRINGUP_001`, `BRINGUP_002`, `ENGDIAG_001`, and `ENGDIAG_001_FIXCHECK` remain separate and unchanged. The bring-ups remain failed engineering attempts; all diagnostic observations remain `scientific_observation=false` and `manuscript_use=NONE`. Do not reinterpret, copy into a scientific denominator, delete, rename, overwrite, or replace them.

## Fixed implementation and hardware

- Controller: F411-A, ST-LINK `066BFF495051727187053106`.
- Payload: F411-B, ST-LINK `066EFF495051727187053015`.
- Leave F411-C and F411-D untouched.
- Host observation/control: independent ST-LINK VCPs on USART2 PA2/PA3.
- Inter-board link: controller D8/PA9 TX to payload D2/PA10 RX, payload D8/PA9 TX to controller D2/PA10 RX, and common GND. No solder change.
- Deployment: standalone applications at `0x08000000`; no bootloader.
- Protocol semantics: 115200 8N1, unchanged frame/CRC/sequence logic, 500 ms poll cadence, 100 ms response deadline, and three consecutive timeouts for OFFLINE.
- Fixed controller ELF SHA-256: `9AA52D103E977A8B18968A0B7F3D69E74361AC5E5FFDFA6B3CBC49A3AD722D78`.
- Fixed controller BIN SHA-256: `8686113C4A83E1600EBE66FB3B3F8795853011B4B0E69D91F9E68EBB3FD8FE68`.
- Payload ELF SHA-256: `0BC0EAAA7830B001CD31F1805C1002275E62FAF8DE6BC8C1AF44ABF5A2005493`.
- Payload BIN SHA-256: `52F145488CAD9D3A9711F77DF1DFB9F76DFEAE6660FE9E1FBD5560AA738BFBBB`.

Do not change firmware, common supervision logic, timing constants, UART mapping, fault behavior, harness validity rules, or pilot condition during this milestone.

## Exact preconditions

All preconditions must pass before sending any delayed-mode command:

1. Reverify the corrected failed-bring-up inventory at SHA-256 `A5C8BF48D7FD0E9CC3A120B890F11CA49FD8DBB6086FD594A321F14C778AC6C9` and the engineering-diagnostic inventory at SHA-256 `98846023F3285F5B9F60C5387E1C54FD6D5EEAA8D5E58A42720795EC9B328DE0`, with zero row issues.
2. Confirm that the only implementation change from commit `600272e` affecting the F411 behavior is the seven-line adapter change in `core/src/bsp/f4/Stm32Timing.cpp`; common protocol, controller/task, and payload parser blobs must match the diagnostic semantic record.
3. Run the required validation suites: core native/SITL/F411 ring 43/43, payload parser 3/3, and extension/legacy host 9/9. Any failure stops the milestone.
4. Clean-build both F411 roles from commit `0ce8a5c`. The resulting BIN/ELF sizes and hashes must exactly reproduce the four fixed hashes above. Any mismatch stops the milestone.
5. Freshly enumerate both boards by durable ST-LINK identity and verify the fixed three-wire connection. Do not rely on historical COM numbers.
6. Create the exclusive package, locked manifest, precondition record, exact attempt ledger, and raw paths before opening the serial ports. Refuse to run if any target path already exists; do not reuse an identifier.
7. Open exact-byte capture on both VCPs before one exact-target flash/verify/reset sequence. Retain complete commands and OpenOCD logs showing `Verified OK` for both fixed ELFs.
8. Require attributable READY markers from both roles, an exact payload-side `MODE=NORMAL` confirmation, controller `PAYLOAD_LINK_START`, and an unambiguous transition to ONLINE.
9. Under precondition ID `F411_P1_SCI_PILOT_001_D110_PRECHECK`, retain one uninterrupted 65 s NORMAL gate: at least 10 controller status records, all ONLINE; strictly increasing `ok`; zero timeout/CRC/sequence/recovery counter deltas; and no rejection, timeout, OFFLINE, recovery, restart, poll-write-failure, UART overflow/error, receive-loss, or reset/fault marker.
10. After that window, require a fresh NORMAL confirmation and a stabilization boundary containing at least three subsequent accepted exchanges, controller ONLINE, unchanged fault/recovery counters, and no unresolved prohibited marker.

The precondition record is retained gate evidence, not a campaign row. If any precondition fails, preserve the failure, issue no delayed command, and stop without reset, retry, replacement, or new run ID.

## Pilot procedure and acceptance criteria

After every precondition passes, execute `F411_P1_SCI_PILOT_001_D110` exactly once:

1. Send exactly one `MODE DELAYED 110` command and require exact payload-side `MODE=DELAYED delay_ms=110` confirmation before scoring controller evidence.
2. Use the unchanged four-second exposure framework and exact-byte dual-channel capture.
3. Require an attributable controller outcome for the activated condition. A valid outcome may be either:
   - an accepted delayed response with its exact sequence/mode marker and no inferred event from marker absence; or
   - the ordered timeout/rejection/OFFLINE path actually present in the raw log.
4. Treat outcome validity independently of whether the result matches G431/G474 or the earlier F411 engineering behavior. An unexpected but valid outcome must be preserved and reported, not retried or tuned.
5. After the retained exposure/target condition, send exactly one `MODE NORMAL` restore command. Require exact payload-side NORMAL confirmation.
6. If the controller entered OFFLINE, require an attributable `PAYLOAD_RECOVERED` marker. If it remained ONLINE, do not require or infer recovery.
7. Require post-stabilization: controller ONLINE, at least three subsequent accepted exchanges, stable fault/recovery counters after the new baseline boundary, and no unresolved restart, poll-write-failure, UART overflow/error, receive-loss, reset/fault, activation, or restoration ambiguity.

The pilot is valid only if activation, controller outcome, restoration, applicable recovery, exact log integrity, and both stabilization boundaries are all unambiguous. Do not use absence-only reasoning to classify acceptance, detection, OFFLINE, or recovery.

## Evidence requirements

Retain in the exclusive package:

- locked manifest, run/precondition IDs, attempt ledger, protocol/condition record, source commit/state, semantic-diff proof, and explicit references to—but no modification of—the prior failed/diagnostic packages;
- exact board identities, fresh ports, wiring confirmation, deployment address, toolchain versions, test logs, clean-build logs, maps, exact BIN/ELF copies and hashes;
- exact-target flash commands and complete verification logs;
- controller and payload exact-byte raw logs plus readable renderings covering flash/reset through final post-stabilization;
- machine-readable precondition, activation, exposure, outcome, restoration, recovery, and post-stabilization validations with exact host-time boundaries;
- all observed markers and counter deltas, prohibited-marker checks, deviations, failures, final payload/controller state, and process/port-close status;
- final disposition and a complete SHA-256 inventory that excludes itself, followed by an independent full-row verification and an exact-copy backup verification.

Reverify the frozen baseline, reviewed primary, G431-B replication, scope-feasibility, recovery, corrected failed-bring-up, and engineering-diagnostic inventory-file hashes unchanged before final disposition.

## Stop rule and terminal condition

There is exactly one scientific pilot attempt. On any precondition, serial, flash, activation, attribution, restoration, recovery, stabilization, reset, overflow/error, evidence-path, or inventory failure:

- preserve every artifact under the assigned ID;
- mark the precondition or pilot invalid with the exact reason;
- do not reset and retry, replace the run, create another ID, change firmware/harness/settings, or begin a campaign; and
- record `F411_P1_SCI_PILOT_FAIL`, drop F411 from the current ICSEC empirical extension, and retain it only as Future Work/development infrastructure.

If the pilot passes, record `F411_P1_SCI_PILOT_PASS_AWAITING_REVIEW`, freeze/inventory/back up the package, and stop. A pass does not authorize a Pair-1 campaign, manuscript inclusion, or second-pair work. Return for scientific review.
