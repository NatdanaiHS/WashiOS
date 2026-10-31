# Results

All statements below are descriptive observations from the frozen artifacts. Table-source paths and hashes are embedded in the machine-readable CSV files and consolidated in `tables/TABLE_PROVENANCE.json`.

## RQ1: nominal windows

Both predefined N0 windows satisfied the validation rule. Each lasted 65.0 s and contained 13 ONLINE status records. The `ok` counter increased strictly from 1835 to 1955 in the pre-campaign window and from 3049 to 3169 in the post-campaign window. Within each window, timeout, CRC, sequence, and recovery counter deltas were zero, and the prohibited-marker list was empty.

| Phase | Duration (s) | ONLINE records | `ok` first→last | timeout Δ | CRC Δ | sequence Δ | recovery Δ | Prohibited markers | Valid |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Pre | 65.0 | 13 | 1835→1955 | 0 | 0 | 0 | 0 | 0 | Yes |
| Post | 65.0 | 13 | 3049→3169 | 0 | 0 | 0 | 0 | 0 | Yes |

Authoritative source: `research/icsec2026/paper/tables/n0_controls.csv`, deterministically projected from the pre/post N0 validation JSON files. The different absolute counter levels reflect prior activity; only within-window deltas are evaluated.

## RQ2: predefined fault outcomes

Machine validation checked 90 plan rows, 90 result rows, and all 180 raw log files, reporting zero issues and zero invalid rows (`research/icsec2026/runs/full_20260830_seed20260830_n30/validation.json`, SHA-256 `D06426EE043D32B032FA3267E7A8DDAB0AD345FD1F69807E93E9F47507BA84EB`). For each mode, all 30 planned trials had confirmed activation and confirmed NORMAL restoration. The predefined detector marker and subsequent recovery marker were each observed in 30/30 valid trials. For each 30/30 observed proportion, the two-sided 95% Clopper–Pearson exact interval was [0.884296692, 1.0].

| Mode | Valid / planned | Invalid | Activation confirmed | Detection observed (exact 95% CI) | OFFLINE observed | Restoration confirmed | Recovery observed (exact 95% CI) | Restart marker observed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SILENT | 30/30 | 0 | 30/30 | 30/30 [0.884296692, 1.0] | 30/30 | 30/30 | 30/30 [0.884296692, 1.0] | 0/30 |
| BAD_CRC | 30/30 | 0 | 30/30 | 30/30 [0.884296692, 1.0] | 30/30 | 30/30 | 30/30 [0.884296692, 1.0] | 0/30 |
| DELAYED | 30/30 | 0 | 30/30 | 30/30 [0.884296692, 1.0] | 30/30 | 30/30 | 30/30 [0.884296692, 1.0] | 0/30 |

Authoritative source: `research/icsec2026/paper/tables/fault_outcomes.csv`, projected from frozen `research/icsec2026/runs/full_20260830_seed20260830_n30/summary.json`. OFFLINE is a secondary observation and is not the BAD_CRC detection criterion. The zero restart-marker counts describe absence of that log marker only and do not prove absence of MCU resets.

## RQ3: host-observed latency distributions

### Command-to-detector-marker latency

| Mode | n | Median (ms) | IQR (ms) | Q1 (ms) | Q3 (ms) | Min (ms) | Max (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|
| SILENT | 30 | 383.0 | 196.25 | 288.75 | 485.0 | 125.0 | 578.0 |
| BAD_CRC | 30 | 359.5 | 293.0 | 171.25 | 464.25 | 78.0 | 531.0 |
| DELAYED | 30 | 406.0 | 215.0 | 297.0 | 512.0 | 156.0 | 610.0 |

### Restore-command-to-recovery-marker latency

| Mode | n | Median (ms) | IQR (ms) | Q1 (ms) | Q3 (ms) | Min (ms) | Max (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|
| SILENT | 30 | 297.0 | 230.75 | 144.25 | 375.0 | 78.0 | 516.0 |
| BAD_CRC | 30 | 359.0 | 303.5 | 113.75 | 417.25 | 47.0 | 531.0 |
| DELAYED | 30 | 296.5 | 238.25 | 187.25 | 425.5 | 94.0 | 531.0 |

Authoritative source: the six rows of `research/icsec2026/paper/tables/latency_summary.csv`, projected from frozen `research/icsec2026/runs/full_20260830_seed20260830_n30/summary.json`. These are host-observed command-to-marker distributions; no between-mode hypothesis test or comparative ranking is asserted.

## Evidence-bounded interpretation

For this board pair, firmware, wiring, host, and configured timing, every retained injected behavior produced its predefined controller detector evidence and was followed by a logged recovery after confirmed NORMAL restoration. The two N0 records support nominal behavior only during their observed windows. These results do not establish independent-device reliability or performance beyond the tested setup.
