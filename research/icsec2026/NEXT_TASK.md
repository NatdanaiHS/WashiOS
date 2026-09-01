# Next Executable Milestone: F411 Pair-1 Bring-up and Pilot

## Decision and boundary

Checkpoint 1 passed `F411_GO`. The feasibility inventory independently verifies 4/4 rows, the recorded generic F411 BIN/ELF artifacts reverify exactly, all four boards have unique ST-LINK identities and observed VCPs, and the locked USART2-host/USART1-link mapping requires no solder change. Engineering risk remains HIGH.

Implement and test only one physical F411-to-F411 pair through one NORMAL window and one retained 110 ms inject/restore pilot. Do not start the predefined campaign, freeze/review checkpoint, or second-pair work in this milestone. The pilot is not a campaign row and must never enter a campaign denominator.

Allow at most 180 focused engineering minutes for this milestone: at most 120 minutes for role implementation, tests, clean builds, flashing, and physical bring-up, followed by at most 60 minutes for the NORMAL window and inject/restore pilot. The global four-focused-hour budget from Checkpoint 1 through pilot remains controlling.

## Fixed hardware assignment and wiring

- Controller F411-P1-C: F411-A, ST-LINK `066BFF495051727187053106`.
- Payload F411-P1-P: F411-B, ST-LINK `066EFF495051727187053015`.
- Leave F411-C `0669FF495051727187053226` and F411-D `0663FF495051727187066042` untouched.
- Freshly enumerate P1 by durable ST-LINK identity; do not trust historical COM numbers.
- Keep each board's USART2 PA2/PA3 on its independent ST-LINK VCP for host observation/control.
- Wire controller D8/PA9 TX to payload D2/PA10 RX, payload D8/PA9 TX to controller D2/PA10 RX, and one common GND. Use exactly three jumpers and make no solder-bridge change.

## Authorized implementation

Use standalone applications linked at `0x08000000`; do not port or use a bootloader.

- Add explicit `nucleo_f411re` controller and payload role environments.
- Supply isolated F4 USART2/USART1 board initialization and interrupt-driven, fixed-capacity receive rings where receive is required. Overflow must be counted and emitted as a prohibited validity marker; no receive path used by supervision may block.
- Reuse the common frame, CRC, sequence, `PayloadLinkController`, task, and payload command parser semantics unchanged. Permit only narrow role/source-selection guards needed to compose the F411 roles.
- Add deterministic tests for ring empty/single/wrap/full behavior, overflow without overwrite, RX/error interrupt clearing/recovery, and bounded task consumption.
- Add a separate F411 Pair-1 harness/config that reuses the proven exact-byte dual capture, activation, restoration, and stabilization primitives. Do not edit reviewed G431/G474 evidence or its results.

Record pre/post hashes or an equivalent diff proof for the common protocol, supervision controller, task constants, and command parser so semantic preservation is auditable.

## Bring-up acceptance criteria

All criteria must pass before NORMAL acquisition:

1. All applicable existing core native/SITL, payload-parser, and extension/legacy host tests pass together with the new F4 UART tests.
2. Both role environments build from clean outputs. Retain commands, tool versions, maps, exact BIN/ELF hashes, sizes, and proof that both applications begin at `0x08000000`.
3. Common protocol, controller, parser, 115200 8N1, 500 ms poll cadence, 100 ms response deadline, three-timeout OFFLINE rule, activation confirmation, restoration, and stabilization semantics are unchanged.
4. Flash and verify each role by its exact ST-LINK identity; retain complete flash logs. A wrong-target or unverifiable flash is a failure.
5. Both USART2 VCPs provide independent, attributable READY/control or observation records, and the crossed USART1 link carries bidirectional framed traffic.
6. There is no reset ambiguity, UART receive loss, ring overflow, host/link UART sharing, solder change, or pin conflict.

If any criterion fails, retain all build/flash/log evidence and stop without NORMAL or fault injection.

## NORMAL acceptance criteria

Acquire exactly one predefined 65 s NORMAL observation with exact-byte controller and payload logs. Pass only if:

- the payload confirms NORMAL and the controller reaches ONLINE before the observation boundary;
- at least 10 controller status records are present and all are ONLINE;
- the successful-response counter increases strictly;
- timeout, CRC, sequence, and recovery counter deltas are all zero; and
- there is no rejection, timeout, OFFLINE, recovery, restart, poll-write-failure, receive-loss, or overflow marker.

Any failed serial capture, reset, prohibited marker, counter change, or acceptance ambiguity makes the retained NORMAL attempt invalid and ends the milestone. Do not reset and retry or replace the observation.

## One inject/restore pilot

Only after NORMAL passes, execute exactly one retained 110 ms delayed-response pilot with the same four-second exposure framework used by the reviewed extension. Require:

1. a passed pre-stabilization gate: fresh payload NORMAL confirmation, controller ONLINE, at least three subsequent successful exchanges, zero fault/recovery counter deltas, and no unresolved prohibited marker;
2. an exact payload-side `DELAYED 110` activation confirmation before scoring controller evidence;
3. attributable controller evidence for an unambiguous terminal supervision outcome—either accepted response before the deadline or the timeout/rejection/OFFLINE path—without inferring an outcome from marker absence;
4. one NORMAL restore command only after the retained exposure/target condition, exact payload-side NORMAL restoration confirmation, and any required controller recovery marker; and
5. a passed post-stabilization gate with exact-byte dual logs and no reset, receive-loss, overflow, or serial-integrity ambiguity.

The pilot passes on any scientifically valid outcome, including one that differs from G431/G474. Matching the earlier 110 ms result is not an acceptance criterion. Preserve exact marker order and do not cite a derived field that conflicts with ordered raw evidence or harness control flow.

On any activation, attribution, serial, reset, restoration, recovery, stabilization, receive-loss, or overflow failure, retain the invalid pilot and stop. Do not retry, replace, change the delay, tune the deadline, or alter the implementation after seeing the outcome.

## Evidence and terminal condition

Use a new exclusive Pair-1 bring-up/pilot evidence directory. Retain source state, semantic-diff proof, board identities/ports, wiring, test/build records, exact binaries and hashes, flash verification, raw exact-byte dual logs, readable renderings, NORMAL validation, pilot validation, attempt accounting, deviations/failures, elapsed engineering time, and final board state.

Stop immediately if work requires common architectural refactoring, a bootloader, shared VCP/link UART, solder changes, blocking supervision receive, any material supervision-semantic change, edits to frozen evidence/manuscript paths, or more than the authorized time. Preserve partial work as engineering evidence and redirect to manuscript/evidence analysis and Friday scope/export preparation.

End after recording `PAIR1_PILOT_PASS` or `PAIR1_PILOT_FAIL` and the complete evidence disposition. A pass does not authorize the 12-row Pair-1 campaign; return for scientific review.
