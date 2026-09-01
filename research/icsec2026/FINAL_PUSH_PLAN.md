# ICSEC 2026 Final Push Decision

Decision date: 2026-09-01 (Asia/Bangkok)

## Decision

**Go to the lab today.** The first and only authorized milestone is recovery of the exact frozen-baseline bytes from the original lab machine or media. Do not run, flash, reset, or reconfigure any board during that milestone.

This is an evidence-integrity decision, not a request for more experimental rows. The frozen manuscript remains the submission fallback at commit `8a47d070c549274c59cdbde2495afa8d353a93b3`, with `main.pdf` SHA-256 `992A1C9AA41F4295BF7F97CA081D79A7DE2ABBB4B419B2A0B82144C1B50928DF`. No final-push failure may modify that commit, the frozen manuscript, its inventories, or its claims.

## Completed-evidence basis

- The primary G431-A/G474-A extension is complete and valid within its stated scope: 24 valid retained rows, six valid normal controls, three valid observations at each retained delay, and two valid BAD_CRC exposures. `R002_B1_D500` remains invalid evidence because the blocking 500 ms payload behavior starved NORMAL-command processing; it must not be repaired, replaced, or moved into a valid denominator.
- The G431-B/G474-A replication is complete: 12/12 valid observations reproduced the selected 90/100/110 ms and normal-control outcome pattern on a second G431 controller. Because G474-A was shared, this is second-controller reproduction, not an independent board-pair or population result.
- The Hantek work produced one serial-valid feasibility attempt but zero quantitative traces. The internal Wave(Binary) slot and human-observed clean edges do not support a timing estimate.
- The extension packages and their backups verify completely. In contrast, the recovered checkout is missing 185/195 frozen-dataset artifacts and 10/65 frozen-provenance artifacts. The unchanged inventories identify the required exact bytes; reruns cannot restore them.
- The frozen four-page manuscript is unchanged from the evaluated baseline. Its one-pair claims remain a safe fallback even if every proposed extension below fails.

## Highest-value remaining G431/G474 milestone

The only remaining G431/G474 hardware milestone with material scientific value is a **new, precommitted five-trace quantitative scope campaign at 110 ms**, using the already locked G474 endpoint-start and G431 first-timeout GPIO definitions and preserving native machine-readable traces, screenshots, exact scope settings, paired serial evidence, and every attempted capture.

Do **not** run it today. More serial repetitions, more G431-A/G431-B swapping, or export of S001 alone would not solve the shared-G474 replication limit or produce the missing quantitative construct. With only one G474-A, an independent G431/G474 pair is impossible. Reserve the quantitative scope campaign for Friday, and only pass its readiness gate described below.

## F411 decision

An F411 port is worth **one bounded, outcome-neutral pilot after the frozen recovery checkpoint passes**. It is not a direct G431/G474 replication and must be reported, if successful, only as protocol-level cross-platform reproduction. Counts must remain separate from all G431/G474 counts.

The port must use standalone applications at `0x08000000`; an F411 bootloader port is not part of this push. Keep ST-LINK VCP host control/observation on USART2 PA2/PA3. Use USART1 PA9/PA10 for the inter-board link, with TX/RX crossed and common ground. The six available jumper wires are sufficient for two pairs, one pair at a time or concurrently.

### F411 Gate 1: software semantics

Time-box the controller and payload role ports to three focused engineering hours after baseline recovery.

Pass only if:

- explicit `nucleo_f411re` controller and payload environments build reproducibly;
- F4 interrupt-driven receive and bounded ring buffers preserve nonblocking behavior on both host and payload-link UART paths;
- existing host/parser/native tests pass, with added tests for F4 receive buffering and overflow handling;
- the wire protocol, CRC/sequence handling, 115200 8N1 link, 500 ms poll cadence, 100 ms deadline, three-timeout OFFLINE rule, fault activation confirmations, NORMAL restoration, and stabilization gates remain unchanged; and
- the port does not require edits to the frozen dataset, provenance, manuscript, or reviewed extension evidence.

Stop and defer F411 to Future Work if the gate misses the time box, requires changing an experimental semantic, or cannot produce separate reliable host and link UARTs. Preserve all source changes and test failures on the extension branch; do not describe the attempt as evidence.

### F411 Gate 2: one-pair pilot

Before flashing, record exact board identities, role assignment, pin map, standalone deployment difference, firmware hashes, and a seeded three-block plan containing one NC and one each of 90, 100, and 110 ms per block (12 observations total). Use two F411 boards only.

Pass only if readiness, a 65 s nominal window, and all 12 precommitted observations are valid under exact activation, restoration, dual-log, and stabilization rules. The gate is **outcome-neutral**: matching the G431/G474 pattern is not an acceptance criterion, and a scientifically contrary but valid result must be retained as such. Any serial-integrity failure, reset ambiguity, unconfirmed activation/restoration, failed stabilization, or omitted/replaced row stops expansion. Preserve every attempt and freeze a clearly labeled failed or partial pilot; do not retry to obtain a preferred pattern.

### F411 Gate 3: second physical pair

Only after Gate 2 passes, assign the two untouched F411 boards as a second controller/payload pair and execute the same already locked plan without tuning conditions after seeing pair-one outcomes. Preserve all attempts. Freeze, inventory, independently verify, and back up each pair separately before any manuscript decision.

Even if both pairs pass, the supported result is bounded cross-platform reproduction on two F411 pairs. Do not pool observations, infer an MCU timing threshold, or claim G431/G474 device-population generalization.

## Friday contingency

Friday is reserved in this order:

1. If exact frozen recovery has not passed, spend the visit only on locating and verifying the original bytes. Do not substitute reruns.
2. If recovery has passed, authorize the five-trace 110 ms scope campaign only if, before acquisition, a USB/storage or supported PC export path has successfully saved and reopened a dummy native waveform and screenshot, at least 90 minutes remain for acquisition plus evidence freeze, and the endpoint definitions and five-row plan remain unchanged.
3. If that readiness gate fails, attempt only non-destructive export of the existing internal S001 Wave(Binary) record. Retain it as feasibility evidence; it does not reduce the requirement for five new valid traces and does not support a quantitative claim.

Stop the scope campaign on the first invalid acquisition, any loss of activation/restoration/stabilization evidence, any inability to save a native trace, or insufficient time to freeze and back up every attempt. Preserve the failure and retain the zero-trace feasibility conclusion rather than replacing a row.

## Explicit deferrals

Defer to Future Work:

- the 500 ms condition under altered payload scheduling;
- additional G431-A/G431-B serial repetitions or a larger delay grid;
- independent-pair or device-population claims until another G474-class payload board exists;
- F411 bootloader equivalence, binary/configuration replication, broader fault matrices, or pooled cross-platform counts;
- MCU-internal timing, long-duration, environmental, qualification, and reliability claims; and
- any quantitative scope claim if Friday's native-export and five-trace gates do not pass.

## Fallback checkpoints and global stop rule

1. **Submission fallback:** frozen commit `8a47d070c549274c59cdbde2495afa8d353a93b3` and the unchanged four-page manuscript PDF.
2. **Reviewed extension fallback:** the complete primary, G431-B replication, and scope-feasibility packages with inventory hashes `8B4CB2AB87CD317905AA4A219B81E99E2E459DC3EEF386D14286297476177C0B`, `F13EBB7FEB42FB3F67E56A8503CB6D70A5F630F2C864A16B22D5BF4D9D19CCE9`, and `519E7E142DFAFEA4736CA74D945B3197D106714F9B6B1A6B45C75309EC4B1B0E`.
3. **Recovery checkpoint:** a new exclusive exact-byte copy must verify 195/195 frozen-dataset rows and 65/65 frozen-provenance rows against the existing inventories, with a second verified copy. Inventories must not be regenerated.

No F411 or scope result enters the manuscript unless its complete precommitted package passes independent inventory verification and a separate scientific review. If any gate fails or time threatens manuscript quality, stop the extension, preserve the negative/partial evidence outside the frozen paths, and submit from the frozen fallback.
