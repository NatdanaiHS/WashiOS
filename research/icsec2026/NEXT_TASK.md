# Next Executable Milestone: Identical F411 Pair-2 Campaign

## Scientific decision and authorization

The frozen F411 Pair-1 campaign supports a bounded descriptive protocol-level result for one physical F411 controller/payload pair: 12/12 predefined rows were valid; all three Normal Controls were clean; all three 90 ms rows accepted delayed responses without fault transitions; and all three 100 ms plus all three 110 ms rows produced the recorded timeout/sequence-rejection/OFFLINE pattern followed by confirmed restoration and recovery. This is sequential within-pair evidence only. It is not a reliability estimate, device-population evidence, or an extension of the G431/G474 denominator.

Authorize exactly one identical predefined campaign on the untouched second physical F411 pair. Its scientific value is to test whether the Pair-1 protocol-level pattern is reproduced on an independent controller/payload pair under the same implementation and procedure. Outcome agreement is not required for validity. Pair-2 is a separate physical-pair dataset and must never be pooled statistically with Pair-1, the F411 pilot, the engineering diagnostic, or any G431/G474 package.

The Pair-1 source and backup package at `research/icsec2026/extension/evidence/f411_pair1_campaign_20260901_seed20260901_b3/` are frozen exactly as reviewed: 12 planned, 12 attempted once, 12 valid, zero invalid, zero retries or replacements; 95/95 inventory rows; inventory SHA-256 `797F908BCFC5EB5450302360501016DCB23188996C15194D9CF91C8BE619C2BC`. Do not reinterpret, edit, regenerate, rename, append to, or change its denominator.

This document authorizes Pair-2 acquisition, freeze, and backup only. It authorizes no Pair-3, adaptive experiment, manuscript claim, or additional F411 hardware observation.

## Fixed Pair-2 package, hardware, and implementation

- Exclusive package: `research/icsec2026/extension/evidence/f411_pair2_campaign_20260901_seed20260901_b3/`.
- Campaign ID: `F411_P2_CAMPAIGN_20260901_B3`.
- Pre-campaign gate ID: `F411_P2_CAMPAIGN_20260901_B3_PRECHECK`.
- Controller: untouched F411-C, ST-LINK `0669FF495051727187053226`.
- Payload: untouched F411-D, ST-LINK `0663FF495051727187066042`.
- F411-A and F411-B must not be flashed, reset, or observed during Pair-2 acquisition.
- Fixed controller ELF/BIN SHA-256: `9AA52D103E977A8B18968A0B7F3D69E74361AC5E5FFDFA6B3CBC49A3AD722D78` / `8686113C4A83E1600EBE66FB3B3F8795853011B4B0E69D91F9E68EBB3FD8FE68`.
- Fixed payload ELF/BIN SHA-256: `0BC0EAAA7830B001CD31F1805C1002275E62FAF8DE6BC8C1AF44ABF5A2005493` / `52F145488CAD9D3A9711F77DF1DFB9F76DFEAE6660FE9E1FBD5560AA738BFBBB`.
- Deployment: standalone at `0x08000000`, no bootloader.
- Host channels: independent ST-LINK VCPs on USART2 PA2/PA3; freshly enumerate ports because historical COM numbers are not authoritative.
- Inter-board link: controller D8/PA9 TX to payload D2/PA10 RX, payload D8/PA9 TX to controller D2/PA10 RX, and common GND; no D0/D1 wire and no solder change.
- Protocol and supervision semantics: 115200 8N1; unchanged frame, CRC, and sequence handling; 500 ms poll cadence; 100 ms response deadline; OFFLINE after three consecutive timeouts; exact activation/restoration confirmation; four-second exposure; no reset between rows.
- Use the same Pair-1 campaign acquisition and validation logic, validity rules, stabilization rules, and evidence schema. The only permitted configuration changes are Pair-2 campaign/run identifiers, exclusive paths, the two physical board identities, and freshly enumerated VCP ports. Record and review the exact configuration-only diff before hardware action. Substantive firmware, protocol, timing, harness, validator, or acceptance-rule changes cancel this authorization and redirect to manuscript integration and Friday gap analysis.

## Fixed design, denominator, and order

Use the identical Pair-1 seed `20260901`, three-block design, condition counts, and order. The table is authoritative; do not rerandomize.

| Row | Run ID | Block | Condition |
|---:|---|---:|---|
| 1 | `F411P2_C01_B1_NC` | 1 | NC |
| 2 | `F411P2_C02_B1_D110` | 1 | DELAYED 110 ms |
| 3 | `F411P2_C03_B1_D090` | 1 | DELAYED 90 ms |
| 4 | `F411P2_C04_B1_D100` | 1 | DELAYED 100 ms |
| 5 | `F411P2_C05_B2_D090` | 2 | DELAYED 90 ms |
| 6 | `F411P2_C06_B2_NC` | 2 | NC |
| 7 | `F411P2_C07_B2_D100` | 2 | DELAYED 100 ms |
| 8 | `F411P2_C08_B2_D110` | 2 | DELAYED 110 ms |
| 9 | `F411P2_C09_B3_D100` | 3 | DELAYED 100 ms |
| 10 | `F411P2_C10_B3_D110` | 3 | DELAYED 110 ms |
| 11 | `F411P2_C11_B3_NC` | 3 | NC |
| 12 | `F411P2_C12_B3_D090` | 3 | DELAYED 90 ms |

The fixed Pair-2 denominator is 12 rows: three NC and three observations at each of 90, 100, and 110 ms. Each planned row may be attempted at most once. Report Pair-2 planned, attempted, valid, invalid, and not-attempted-after-stop counts overall and by condition. Do not replace, retry, reorder, append, change delays, alter exposure, or adapt after seeing any outcome.

## Checkpoint A — lock and readiness before hardware action

Before opening a serial port, flashing, resetting, or sending a command:

1. Independently reverify the frozen Pair-1 source and exact-copy backup against all 95 inventory rows and the inventory hash above. Any mismatch stops Pair-2.
2. Reverify all previously frozen baseline, G431/G474 extension, F411 pilot, failed-bring-up, and engineering-diagnostic inventory-file hashes unchanged.
3. Create the exclusive Pair-2 package, locked manifest, exact plan, full attempt ledger, conditions, validity rules, and raw paths. Refuse any reused package or run path.
4. Record hashes of the Pair-1 and Pair-2 plan/configuration plus acquisition/validation code. Demonstrate that the Pair-2 execution path differs from the reviewed Pair-1 path only in the permitted identifiers, paths, physical identities, and ports. Commit the lock before acquisition and record a clean, synchronized source state.
5. Run the same required tests and campaign-harness tests and clean-build both roles. Require the four fixed firmware hashes above exactly.
6. Freshly enumerate F411-C and F411-D by durable ST-LINK identity and obtain human confirmation of the exact three-wire crossed link, correct roles, no D0/D1 wire, and no solder change.
7. Do not start unless at least 90 uninterrupted minutes remain for all 12 rows plus freeze and backup. Reserve at least 30 minutes for evidence finalization.

Failure of any item stops without hardware acquisition and redirects to manuscript integration and Friday gap analysis. Do not substitute Pair-1 boards or change roles.

## Checkpoint B — continuous capture and 65 s NORMAL gate

Open one continuous exact-byte capture on both Pair-2 VCPs before one exact-target flash/verify/reset sequence. Retain continuous master logs through readiness, every row, all inter-row stabilization, and final state. Require both READY markers, payload NORMAL, controller link start, and ONLINE.

Under `F411_P2_CAMPAIGN_20260901_B3_PRECHECK`, retain one uninterrupted 65 s NORMAL window with:

- at least 10 controller status records, all ONLINE;
- strictly increasing `ok`;
- zero timeout/CRC/sequence/recovery counter deltas; and
- no rejection, timeout, OFFLINE, recovery, restart, poll-write-failure, UART overflow/error, receive-loss, reset/fault, serial-integrity, or ambiguous-attribution marker.

Failure stops before row 1. Preserve the failed readiness evidence; do not reset, retry, change firmware, create a replacement campaign, or fall back to Pair-1.

## Checkpoint C — identical per-row procedure

Before every row:

1. Send one fresh `MODE NORMAL` and require exact payload-side NORMAL confirmation.
2. Lock a new serial boundary after confirmation.
3. Require controller ONLINE, at least three subsequent accepted exchanges, and two subsequent controller status records with strictly increasing `ok` and zero timeout/CRC/sequence/recovery deltas between them.
4. Require no unresolved prohibited marker after the boundary.

For each delayed row, send exactly one planned `MODE DELAYED <90|100|110>`, require exact payload-side activation confirmation before scoring, observe for exactly four seconds, and retain every accepted response, counter, timeout, rejection, OFFLINE, and other marker. Then send one NORMAL restore and require exact payload-side NORMAL confirmation. Require an attributable recovery marker if the controller entered OFFLINE; if it remained ONLINE, do not require or infer recovery.

For each NC row, keep the payload in confirmed NORMAL at the activation-equivalent boundary, observe the identical four-second window without fault injection, retain all healthy and adverse markers, then send and confirm one final NORMAL command at the same restoration-equivalent boundary.

After every row, require controller ONLINE, at least three subsequent accepted exchanges, and two subsequent status records with strictly increasing `ok`, zero timeout/CRC/sequence/recovery deltas between the two records, and no unresolved prohibited marker after the post-restore boundary. Evaluate deltas at locked boundaries, not from absolute cumulative values.

Do not reset, reflash, change ports, reopen capture, or alter the plan between rows.

## Validity, acceptance, and stop rules

A row is valid only if its planned identity, condition, and order are exact and continuous capture, activation/control, four-second exposure, restoration-equivalent confirmation, applicable recovery, raw integrity, and pre/post-stabilization all pass. Methodological invalidity includes wrong or unconfirmed condition; wrong order/identity; capture or harness failure; reset ambiguity; UART overflow/error or receive loss; wrong-target or unverified firmware; ambiguous attribution; unconfirmed restoration; missing required recovery; failed stabilization; duplicate path; or malformed/missing raw evidence.

An unexpected scientific outcome is valid evidence. Pair-2 need not reproduce Pair-1: a delayed response may be accepted or fault at any delay, and an NC may contain a valid adverse outcome. Preserve and report differences without tuning, exclusion, or replacement. Do not use Pair-1 outcomes as Pair-2 acceptance criteria.

Record `F411_P2_CAMPAIGN_COMPLETE_AWAITING_REVIEW` only if all 12 planned rows were attempted exactly once in order and all 12 are methodologically valid; all condition outcomes are completely accounted; implementation, identities, wiring, capture, and semantics remained fixed; final payload NORMAL and controller ONLINE stabilization pass; and the complete source package and exact-copy backup independently verify.

At the first invalid row or failed inter-row gate:

- retain the attempt and exact invalidity reason;
- stop before the next row;
- mark all remaining planned rows `NOT_ATTEMPTED_AFTER_STOP`;
- do not retry, replace, reorder, append, reset, reflash, tune, or create a new campaign ID; and
- record `F411_P2_CAMPAIGN_STOPPED_INVALID_AWAITING_REVIEW`.

Also stop if continuous capture is lost, identity/port/wiring changes, a prior inventory changes, or fewer than 30 minutes remain for freeze and backup. Preserve all partial evidence. After either complete or stopped disposition, end F411 hardware work and proceed to scientific review, manuscript integration, and Friday gap analysis; no further F411 campaign is authorized.

## Evidence and terminal requirements

Retain the locked manifest and plan/hashes, source state, full attempt ledger including unattempted rows, exact board identities and wiring confirmation, tests/build/map records, exact firmware copies/hashes and flash logs, continuous exact-byte dual logs, immutable row boundaries, per-row readable views and machine validations, every counter/marker observation, deviations/failures, Pair-2-only condition summary, final state, process/port-close status, and a complete SHA-256 inventory excluding itself.

Independently verify every source inventory row, create an exact-copy backup, independently verify every backup row, and reverify all prior inventory hashes unchanged. Keep Pair-2 summaries and denominator separate. Any later cross-pair review may compare Pair-1 and Pair-2 descriptively as two physical-pair datasets, but must not pool rows, estimate population reliability, or imply device-population generalization. Then stop for scientific review.
