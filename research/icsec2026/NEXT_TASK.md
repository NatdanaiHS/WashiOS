# Next Executable Milestone: Predefined F411 Pair-1 Campaign

## Authorization and scientific value

Authorize one small predefined campaign on the fixed F411 Pair-1 configuration. The valid fresh pilot shows that the activation/restoration construct is operational; this campaign now tests within-configuration reproducibility at the selected 90/100/110 ms boundary and under interleaved Normal Controls. It is the minimum useful Pair-1 evidence gate before any independent second-pair decision.

This campaign remains sequential evidence from one physical F411 controller/payload pair. It is not a device sample, reliability estimate, independent replication, or G431/G474 campaign extension. Do not pool its rows with the original G431/G474 data, the G431-B replication, the fresh pilot, the failed F411 bring-ups, or the engineering diagnostic. No manuscript inclusion or second-pair work is authorized here.

## Fixed package, hardware, and implementation

- Exclusive package: `research/icsec2026/extension/evidence/f411_pair1_campaign_20260901_seed20260901_b3/`.
- Campaign ID: `F411_P1_CAMPAIGN_20260901_B3`.
- Pre-campaign gate ID: `F411_P1_CAMPAIGN_20260901_B3_PRECHECK`.
- Controller: F411-A, ST-LINK `066BFF495051727187053106`.
- Payload: F411-B, ST-LINK `066EFF495051727187053015`.
- Leave F411-C and F411-D untouched.
- Fixed controller ELF/BIN SHA-256: `9AA52D103E977A8B18968A0B7F3D69E74361AC5E5FFDFA6B3CBC49A3AD722D78` / `8686113C4A83E1600EBE66FB3B3F8795853011B4B0E69D91F9E68EBB3FD8FE68`.
- Fixed payload ELF/BIN SHA-256: `0BC0EAAA7830B001CD31F1805C1002275E62FAF8DE6BC8C1AF44ABF5A2005493` / `52F145488CAD9D3A9711F77DF1DFB9F76DFEAE6660FE9E1FBD5560AA738BFBBB`.
- Deployment: standalone at `0x08000000`, no bootloader.
- Host channels: independent ST-LINK VCPs on USART2 PA2/PA3.
- Link: controller D8/PA9 TX to payload D2/PA10 RX, payload D8/PA9 TX to controller D2/PA10 RX, and common GND; no D0/D1 wire or solder change.
- Locked semantics: 115200 8N1, unchanged frame/CRC/sequence handling, 500 ms poll cadence, 100 ms response deadline, three consecutive timeouts for OFFLINE, exact activation/restoration confirmation, four-second row exposure, and unchanged stabilization gates.

Do not change firmware, timing, protocol, link mapping, harness validity rules, conditions, exposure, block count, order, or analysis after the plan is locked or after any hardware observation.

## Fixed design and denominator

Seed: `20260901`.

Ordering method: within each block, sort `NC`, `D090`, `D100`, and `D110` by ascending SHA-256 of the UTF-8 string `20260901|B<block>|<condition>`. The exact table below is authoritative if any implementation disagrees.

| Row | Run ID | Block | Condition |
|---:|---|---:|---|
| 1 | `F411P1_C01_B1_NC` | 1 | NC |
| 2 | `F411P1_C02_B1_D110` | 1 | DELAYED 110 ms |
| 3 | `F411P1_C03_B1_D090` | 1 | DELAYED 90 ms |
| 4 | `F411P1_C04_B1_D100` | 1 | DELAYED 100 ms |
| 5 | `F411P1_C05_B2_D090` | 2 | DELAYED 90 ms |
| 6 | `F411P1_C06_B2_NC` | 2 | NC |
| 7 | `F411P1_C07_B2_D100` | 2 | DELAYED 100 ms |
| 8 | `F411P1_C08_B2_D110` | 2 | DELAYED 110 ms |
| 9 | `F411P1_C09_B3_D100` | 3 | DELAYED 100 ms |
| 10 | `F411P1_C10_B3_D110` | 3 | DELAYED 110 ms |
| 11 | `F411P1_C11_B3_NC` | 3 | NC |
| 12 | `F411P1_C12_B3_D090` | 3 | DELAYED 90 ms |

Fixed planned denominator: 12 rows—three NC and three observations at each delay. The previously reviewed pilot is excluded. Report planned, attempted, valid, invalid, and not-attempted-after-stop counts for the campaign and separately for every condition. Condition summaries use only valid rows but must always show the full accounting; do not compute population confidence intervals or reliability estimates.

## Pre-acquisition lock and readiness

Before opening serial ports or acting on hardware:

1. Create the exclusive package, manifest, exact 12-row plan, attempt ledger, conditions, validity rules, and raw paths. Refuse any pre-existing run/package path.
2. Record hashes for the plan and all acquisition/validation code. Commit the locked plan and harness before acquisition; record the clean acquisition source state.
3. Reverify 48/48 rows in both source and backup of the reviewed fresh-pilot package and its inventory SHA-256 `B8B2DB1679A21747B80DB9209E7249C755C30CF8C62464E425906951E24295D1`.
4. Reverify the corrected failed-bring-up and diagnostic inventories unchanged at `A5C8BF48D7FD0E9CC3A120B890F11CA49FD8DBB6086FD594A321F14C778AC6C9` and `98846023F3285F5B9F60C5387E1C54FD6D5EEAA8D5E58A42720795EC9B328DE0`.
5. Reverify the frozen dataset/provenance and all reviewed G431/G474 extension inventory-file hashes unchanged.
6. Run all required existing tests plus campaign-harness tests, and clean-build both role images. The four firmware hashes must reproduce exactly.
7. Freshly enumerate the two fixed boards by ST-LINK identity and obtain human confirmation of the exact three-wire link. Historical COM numbers are not authoritative.
8. Do not start unless enough uninterrupted time remains to execute all 12 rows and freeze, inventory, and back up every artifact. Reserve at least 90 minutes before the hard stop.

After those checks, open one continuous exact-byte capture on both VCPs before a single exact-target flash/verify/reset sequence. Retain the continuous master logs across readiness, every row, every inter-row stabilization interval, and final state. Require both READY markers, payload NORMAL, controller link start, and ONLINE.

Under `F411_P1_CAMPAIGN_20260901_B3_PRECHECK`, retain one uninterrupted 65 s NORMAL readiness window: at least 10 status records, all ONLINE; strictly increasing `ok`; zero timeout/CRC/sequence/recovery counter deltas; and no rejection, timeout, OFFLINE, recovery, restart, poll-write-failure, UART overflow/error, receive-loss, reset/fault, or serial-integrity marker. Failure stops before row 1 without reset or retry.

## Per-row stabilization and procedure

Before every row:

1. Send one fresh `MODE NORMAL` command and require exact payload-side NORMAL confirmation.
2. Lock a new serial boundary after confirmation.
3. Require controller ONLINE, at least three subsequent accepted exchanges, and two subsequent controller status records with strictly increasing `ok` and zero timeout/CRC/sequence/recovery deltas between them.
4. Require no unresolved rejection, timeout, OFFLINE, recovery, restart, poll-write-failure, UART overflow/error, receive-loss, reset/fault, or serial-integrity marker after the boundary.

For a delayed row:

1. Send exactly one `MODE DELAYED <90|100|110>` command matching the plan and require exact payload-side `MODE=DELAYED delay_ms=<value>` confirmation before scoring.
2. Observe for exactly four seconds and retain all accepted-response, timeout, rejection, OFFLINE, counter, and other markers. Classify only explicit attributable evidence; never infer an outcome from marker absence.
3. Send one NORMAL restore after the retained exposure/target condition and require exact payload-side NORMAL confirmation.
4. If the controller entered OFFLINE, require an attributable recovery marker. If it remained ONLINE, do not require or infer recovery.

For an NC row:

1. Keep the payload in confirmed NORMAL at the activation-equivalent boundary.
2. Observe the identical four-second window without injecting a fault.
3. Retain and report every accepted exchange and every false rejection, timeout, OFFLINE, recovery, restart, write-failure, overflow/error, receive-loss, or reset/fault marker. NC is a healthy control, not C0 or an ablation.
4. Send and confirm one final NORMAL command at the same restoration-equivalent boundary used by delayed rows.

After every row, require post-stabilization: controller ONLINE; at least three subsequent accepted exchanges; two subsequent status records with strictly increasing `ok`; zero timeout/CRC/sequence/recovery deltas between the two records; and no unresolved prohibited marker after the post-restore baseline. Evaluate counter deltas from locked boundaries, not absolute cumulative counter values.

Do not reset either MCU between rows. Do not reflash, change ports, reopen capture, or alter the plan after row 1 starts.

## Validity and outcome rules

A row is valid only when its planned identity/condition/order is exact and all capture, activation/control, exposure, restoration-equivalent, applicable recovery, raw-integrity, and pre/post-stabilization requirements pass.

Invalidity is limited to methodological or evidence-integrity failures, including wrong/unconfirmed condition; wrong order or identity; serial/capture/harness failure; reset ambiguity; UART overflow/error or receive loss; wrong-target/unverified firmware; ambiguous attribution; unconfirmed NORMAL restoration; missing required recovery; failed stabilization; duplicate/reused path; or malformed/missing raw evidence.

An unexpected scientific outcome is **not** invalid. In particular:

- a delayed response may be accepted or may produce timeout/rejection/OFFLINE at any tested delay;
- repeated cumulative timeout/sequence increments during the four-second exposure remain valid if boundaries and raw evidence are clear; and
- an NC false marker is a valid adverse control outcome if capture, condition, restoration, and stabilization remain valid.

Preserve and report such outcomes without tuning or replacement.

## Campaign acceptance criteria

Record `F411_P1_CAMPAIGN_COMPLETE_AWAITING_REVIEW` only if:

- all 12 planned rows were attempted exactly once in the locked order;
- all 12 rows are methodologically valid;
- all three NC rows and all three rows at every delay have complete outcome accounting;
- source state, firmware, identities, wiring, capture, and semantics remained fixed throughout;
- final payload state is confirmed NORMAL and final controller state is ONLINE with a passed stabilization gate; and
- the complete evidence package, inventory, and backup independently verify.

No particular 90/100/110 ms outcome pattern is required for campaign validity. Report condition-specific descriptive counts for accepted delayed response, timeout, sequence/CRC rejection, OFFLINE, restoration, recovery, and NC false markers. Keep Pair-1 counts separate from every other package.

## First-invalid stop and other stop rules

On the first invalid row or failed inter-row gate:

- retain the invalid attempt and exact reason;
- stop immediately before the next row;
- mark every remaining planned row `NOT_ATTEMPTED_AFTER_STOP`;
- do not reset/retry, replace, reorder, append rows, create a new campaign ID, or modify firmware/harness/conditions; and
- record `F411_P1_CAMPAIGN_STOPPED_INVALID_AWAITING_REVIEW`.

Also stop if continuous capture is lost, a board identity/port/wiring changes, less than 30 minutes remains for evidence freeze/backup, or any prior inventory changes. Preserve all partial evidence. A partial campaign cannot authorize second-pair work or manuscript use.

## Evidence and terminal requirements

Retain the locked manifest/plan and hashes, acquisition source state, full attempt ledger including unattempted rows, exact identities/wiring, test/build/map records, exact firmware copies/hashes, flash logs, continuous exact-byte dual logs, immutable row-boundary ledger, per-row readable views and machine validations, all counter/marker observations, deviations/failures, descriptive condition summary, final states, process/port-close status, and a complete SHA-256 inventory excluding itself.

Independently verify every source inventory row, make an exact-copy backup, independently verify every backup row, and reverify all prior inventory-file hashes unchanged. Then stop for scientific review. Completion does not authorize manuscript inclusion, a second F411 pair, or any additional F411 observation.
