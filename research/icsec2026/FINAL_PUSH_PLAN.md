# ICSEC 2026 Final Push Plan

Decision date: 2026-09-01 (Asia/Bangkok)

## Current decision

**TODAY: ROOM.** Exact-byte frozen-baseline recovery is complete at synchronized commit `0fbd98f`: two independent copies verify 195/195 dataset rows and 65/65 provenance rows with zero issues. No unresolved scientific question remains from recovery.

The highest-value room milestone is a gated F411-to-F411 physical replication path. It begins with source/pin/VCP feasibility and earns each later checkpoint separately. F411 work is not allowed to delay Friday preparation or alter the frozen submission fallback.

The frozen fallback remains commit `8a47d070c549274c59cdbde2495afa8d353a93b3`, manuscript PDF SHA-256 `992A1C9AA41F4295BF7F97CA081D79A7DE2ABBB4B419B2A0B82144C1B50928DF`. The reviewed primary, G431-B replication, scope-feasibility, and recovery packages also remain unchanged.

## Scientific boundary

The F411 work tests whether the same activation-confirmed UART protocol and supervision semantics can produce interpretable physical observations on another MCU/configuration. It is **cross-configuration, protocol-level physical replication**, not direct replication of G431/G474 timing or binaries.

- Do not pool F411 rows with G431/G474 rows.
- Do not compute a combined success proportion, device-population interval, or reliability estimate.
- Do not infer G431/G474 thresholds, MCU-internal timing, qualification, or population generality.
- Keep the one-pair pilot outside all campaign denominators.
- Treat matching and nonmatching valid outcomes symmetrically. Gate passage depends on evidence validity and semantic equivalence, not on obtaining a preferred result.

Use standalone F411 applications at `0x08000000`; an F411 bootloader port is out of scope. Preserve ST-LINK VCP host control/observation on USART2 PA2/PA3. Use USART1 PA9/PA10 for the physical inter-board link, with TX/RX crossed and common ground.

## Engineering time and complexity stop rule

Allow at most **four focused engineering hours from Checkpoint 1 start through completion of the one inject/restore pilot**:

- Checkpoint 1 feasibility: maximum 60 minutes.
- Controller/payload port plus one-pair bring-up: maximum 120 additional minutes.
- NORMAL and inject/restore pilot: maximum 60 additional minutes.

Stop F411 immediately if any of the following becomes necessary:

- redesigning the common UART, protocol, payload-link controller, fault parser, or host-harness architecture instead of supplying isolated F4 board/UART implementations and narrow build guards;
- changing frame format, CRC/sequence behavior, 115200 8N1, the 500 ms poll cadence, 100 ms deadline, three-consecutive-timeout OFFLINE rule, activation confirmations, NORMAL restoration, or stabilization gates;
- sharing USART2 with the inter-board link, changing Nucleo solder bridges, or losing independent host observation;
- porting the bootloader, altering the frozen G431/G474 implementation, or editing frozen evidence/manuscript paths; or
- exceeding the four-hour pilot budget, even if success appears close.

On a stop, retain code, build logs, and failures as engineering evidence only. Redirect the remaining room time to analysis of the completed evidence, a separate manuscript-extension draft, and Friday scope/export preparation.

## Checkpoint 1 — source/pin/VCP feasibility

Time-box to 60 minutes. Freshly enumerate all four F411 boards by ST-LINK identity and VCP port. Confirm from authoritative board/MCU mappings and the installed PlatformIO board definition that USART2 PA2/PA3 remains the ST-LINK VCP and USART1 PA9/PA10 is independently available on D8/D2 for the link. Build the existing generic F411 target as a toolchain sanity check.

Produce a source-impact and semantic-equivalence record showing that both roles can be implemented through explicit `nucleo_f411re` environments, isolated F4 interrupt-driven UART/ring-buffer code, F4 board initialization, and narrow compile guards. No experimental firmware is flashed in this checkpoint.

**GO** only if both roles have a credible bounded port that preserves every locked semantic without common-architecture refactoring. Otherwise declare **NO-GO** and stop F411.

## Checkpoint 2 — one physical pair bring-up

After Checkpoint 1 GO, assign exactly two boards as F411-P1 controller and payload, record exact identities/ports/pins, and leave the other two boards untouched. Implement the bounded F4 port, add receive-buffer/overflow tests, and require all applicable native/parser/host tests and both role builds to pass.

Flash exact standalone binaries by ST-LINK identity, retain flash logs and hashes, and verify independent host READY/control on both USART2 VCPs plus bidirectional framed traffic on the crossed USART1 link. A pin, VCP, reset, receive-loss, overflow, or build ambiguity is a failed bring-up; preserve it and stop.

## Checkpoint 3 — NORMAL communication

Acquire one predefined 65 s NORMAL window on F411-P1 with exact-byte dual logs. Require at least 10 ONLINE status records, a strictly increasing successful-response counter, zero timeout/CRC/sequence/recovery counter deltas, and no rejection, OFFLINE, recovery, restart, overflow, or poll-write-failure marker.

If the window fails or requires a reset/retry, preserve it and stop. Do not replace the window.

## Checkpoint 4 — one inject/restore pilot

Run one retained 110 ms delayed-response pilot, separate from the later campaign. Require a passed pre-gate, exact payload-side `DELAYED 110` activation confirmation, attributable controller evidence showing either an accepted response or the timeout/rejection path, confirmed NORMAL restoration, any applicable recovery marker, and a passed post-stabilization gate in exact-byte dual logs.

The pilot passes on an unambiguous, semantically valid observation regardless of whether its outcome matches G431/G474. Any activation, serial, reset, attribution, restoration, recovery, or stabilization ambiguity is a failed pilot; preserve it and stop without retry.

## Checkpoint 5 — small predefined F411-P1 campaign

Only after the pilot passes, freeze a seeded three-block plan before acquisition. Each block contains one NC and one each of 90, 100, and 110 ms: 12 observations total. The pilot is not counted. Lock firmware hashes, identities, harness version, conditions, order, validity rules, and the no-replacement rule before row 1.

Execute every row in order with exact activation, dual logs, confirmed restoration, and stabilization. Preserve all attempts and all scientifically valid outcomes. Stop the campaign on the first invalid row; do not omit, replace, or rerun it. A valid outcome that differs from G431/G474 is not an invalid row and does not authorize changing the plan.

## Checkpoint 6 — freeze and scientific review

Before touching the second pair, freeze F411-P1 source state, exact binaries/hashes, board identities, wiring, plans, all raw logs, ledger, validation, descriptive summary, deviations/failures, and a complete SHA-256 inventory. Make and independently verify an exact-copy backup, and reverify the frozen baseline plus all reviewed extension inventory hashes.

Scientific review must confirm semantic equivalence, complete attempt accounting, outcome-neutral validation, correct cross-configuration wording, and no pooled inference. A partial or invalid P1 package stops the path.

## Checkpoint 7 — second independent F411 pair

Only after Checkpoint 6 passes, assign the two untouched boards as F411-P2 controller and payload. Use the same role binaries, wiring, host harness, validity rules, and exact 12-row campaign plan/order, changing only recorded physical identities and ports. Require a fresh readiness check and the same 65 s NORMAL gate before the campaign.

Preserve every attempt and stop on the first invalid row without replacement. Freeze, inventory, back up, independently verify, and separately review F411-P2. Keep P1 and P2 denominators separate from each other and from G431/G474.

## Paper inclusion rule

The following are **supporting/Future Work evidence only** and are not worth adding to the ICSEC paper: source feasibility, successful builds, pin/VCP checks, one-pair bring-up, NORMAL alone, the single pilot, a partial/invalid campaign, or one complete F411 pair without the second pair.

F411 becomes eligible for the paper only if both physical pairs complete the identical campaign with valid frozen packages, semantic review passes, and the resulting comparison materially strengthens the configuration-boundary discussion without displacing the core activation-confirmed contribution. Report pair-specific descriptive outcomes and configuration differences; do not pool counts. If the two pairs or configurations diverge, the result may be included only as an explicit boundary/limitation result. Otherwise retain it as supporting evidence and use the frozen manuscript fallback.

## Friday reserved for G431/G474 scope timing

Friday's full lab session is reserved for the only remaining high-value G431/G474 milestone: a new precommitted five-trace 110 ms quantitative scope campaign using the locked G474 endpoint-start and G431 first-timeout GPIO edges.

Before Friday, prepare verified removable storage or supported Hantek PC export, prove on a dummy capture that a native waveform and screenshot can be saved and reopened, retain the existing five-trace definitions, prepare exact evidence directories/scripts/checklists, and reserve at least 90 minutes for acquisition plus freeze. On Friday, use G431-B/G474-A and the Hantek only after fresh identity, firmware, probe, settings, and export checks.

If native export cannot be demonstrated, do not start the quantitative campaign. Non-destructive export of internal S001 may be retained as feasibility support but cannot become a timing datum. Do not spend Friday on extra serial repetitions, 500 ms scheduling changes, F411 work, or a wider condition grid.

## Global fallback rule

No F411 or scope result enters the manuscript until its complete package passes independent inventory verification and scientific review. Any stop or failure leaves the frozen submission and reviewed evidence checkpoints unchanged. If time threatens manuscript quality, freeze the extension as supporting evidence and return to the frozen paper.
