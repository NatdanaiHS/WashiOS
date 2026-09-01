# F411 cross-pair descriptive synthesis

## Allowed claim

Under the identical predefined protocol and fixed F411 implementation, the same condition-level supervision pattern was observed on each of two separate physical F411 controller/payload pairs.

Pair-1 and Pair-2 remain separate 12-row datasets. Each pair has three observations per condition; no row, counter, or proportion is pooled across pairs.

## Pair-specific result

| Physical pair | Valid | NC clean | 90 ms accepted without fault | 100 ms timeout/SEQ/OFFLINE -> restore/recover | 110 ms timeout/SEQ/OFFLINE -> restore/recover |
|---|---:|---:|---:|---:|---:|
| Pair-1 | 12/12 | 3/3 | 3/3 | 3/3 | 3/3 |
| Pair-2 | 12/12 | 3/3 | 3/3 | 3/3 | 3/3 |

For each pair separately, D100 and D110 contained zero accepted mode-3 responses. Each three-row D100 or D110 condition retained six explicit timeout-transition markers, three explicit sequence-rejection markers, three OFFLINE observations, three confirmed NORMAL restorations, and three recoveries. The corresponding cumulative status-counter deltas were timeout 24, sequence 24, CRC 0, and recovery 3 per condition per pair; cumulative deltas are not explicit marker counts.

## Boundary and provenance observations

Post-activation mode-0 accepts are retained as boundary/pipeline observations, not delayed-mode accepts: four Pair-1 rows and three Pair-2 rows. Each was followed by attributable condition-specific evidence. Both master controller logs end with a partial `[OBC] PAYLOAD_AC` record after the final complete ONLINE status and outside scored/stabilization boundaries. Pair-2's first backup copy command safely copied zero files; the verified corrective copy matched all 81 inventory rows. None of these observations invalidated a scientific row.

## Configuration and interpretation boundary

The two F411 campaigns used the same fixed F411 controller/payload implementation, firmware hashes, UART protocol, 500 ms poll cadence, 100 ms response deadline, three-timeout OFFLINE rule, exact confirmation gates, four-second exposures, seed, order, and validity rules. They used separate physical controller/payload pairs. This is cross-configuration, protocol-level physical replication relative to the G431/G474 study: it does not establish G431/G474 binary or timing replication, MCU-family equivalence, reliability, qualification, or device-population generality.

## Prohibited interpretations

- Do not combine the two 12-row denominators or report 24/24.
- Do not calculate a combined proportion, confidence interval, or population test.
- Do not treat sequential rows as independent devices.
- Do not count mode-0 boundary accepts as delayed-mode responses.
- Do not infer MCU execution timing from host timestamps.
