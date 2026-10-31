# Evaluation Method

## Experimental scope and setup

The evaluation used one NUCLEO-G431RB as the controller and one NUCLEO-G474RE as the simulated payload. The boards communicated over the payload UART at 115200 8N1 with a common ground. Separate host serial channels captured controller and payload-simulator output. Each captured record contains an ISO-8601 UTC host timestamp, the exact received bytes in hexadecimal, and an escaped readable rendering.

The empirical scope is the payload-link supervision behavior visible at those serial interfaces. Boot and runtime mechanisms describe architectural context only. Exact application/bootloader rebuild-to-readback matches establish firmware provenance but are not treated as additional performance experiments.

## Nominal controls

A predefined N0 (Nominal Control) window was captured before the campaign and another after it. Each window was configured for 65 s. A window was valid only if it contained at least 10 controller status records, all records reported ONLINE, the `ok` counter increased strictly, timeout/CRC/sequence/recovery counter deltas were zero, and no prohibited transition, rejection, recovery, or post-start link-start marker appeared. N0 is a healthy control and is not a C0 ablation or comparative baseline.

## Fault conditions and trial protocol

The campaign used seed 20260830 to construct a fixed order of 90 sequential trials: 30 SILENT, 30 BAD_CRC, and 30 DELAYED. The order and pre-injection offsets were recorded in `run_plan.csv`. All trials used the same physical board pair and were executed sequentially; the 30 observations per mode are not independent hardware replicates.

For each trial, the harness:

1. commanded NORMAL and observed the precondition;
2. waited the seeded pre-injection offset;
3. sent the selected fault-mode command;
4. required the matching G474 `[PAYLOAD] MODE=<fault>` confirmation;
5. observed controller output for the configured 4 s fault window;
6. sent `MODE NORMAL` and required the G474 NORMAL confirmation; and
7. observed controller output for the configured 3 s recovery window before finalizing the trial.

The injected modes were:

- **SILENT:** the payload simulator withheld its response. The predefined detector was the first controller `PAYLOAD_TIMEOUT` or `PAYLOAD_OFFLINE` marker after injection.
- **BAD_CRC:** the payload simulator returned a response with an invalid CRC. The predefined detector was the first controller `PAYLOAD_REJECT reason=CRC` marker after injection.
- **DELAYED:** the payload simulator delayed its response by 250 ms, exceeding the inspected 100 ms controller deadline. The predefined detector was the first controller `PAYLOAD_TIMEOUT` or `PAYLOAD_OFFLINE` marker after injection.

OFFLINE occurrence was retained as a secondary descriptive field and was not required to classify BAD_CRC detection. A recovery outcome required a controller `PAYLOAD_RECOVERED` marker after the NORMAL restore command and a confirmed G474 NORMAL restoration. A post-injection `PAYLOAD_LINK_START` field recorded only marker presence or absence; it was not an independent reset measurement.

## Trial validity and artifact validation

A trial was valid when `invalid_reason` was empty and both G474 activation and NORMAL-restoration confirmations were present. The frozen validator checked the 90 planned rows, 90 result rows, and all 180 controller/payload raw logs; it reported zero issues and zero invalid rows. All campaign and N0 artifacts are covered by the frozen dataset SHA-256 inventory.

## Outcome measures

RQ1 uses N0 validity, duration, ONLINE status count, first/last `ok`, strict monotonicity, within-window error/recovery counter deltas, and prohibited-marker count.

RQ2 reports planned, valid, and invalid trials; activation and restoration confirmations; and observed detector, OFFLINE, recovery, and restart-marker counts by mode. Detection and recovery proportions use valid trials for the corresponding mode as denominator.

RQ3 uses two explicitly host-observed intervals:

- **command-to-detector-marker latency:** host timestamp of the first predefined controller detector marker minus the host timestamp when the injection command was sent;
- **restore-command-to-recovery-marker latency:** host timestamp of the controller `PAYLOAD_RECOVERED` marker minus the host timestamp when `MODE NORMAL` was sent.

These intervals include UART transmission, USB transport, host-driver buffering, scheduling, and timestamping effects. No MCU/host clock synchronization was performed, so the measures are not MCU-internal timing.

## Statistical treatment

Analysis is descriptive. For each mode, the paper reports counts, observed proportions, and two-sided 95% Clopper–Pearson exact binomial intervals for detection and recovery. Latency is reported as n, median, inclusive-linear Q1 and Q3, IQR (Q3−Q1), minimum, and maximum. No hypothesis tests, model comparisons, between-mode significance claims, or independence assumptions are used.

## Reproducible table derivation

`generate_manuscript_tables.py` verifies the frozen SHA-256 values of `summary.json`, campaign `validation.json`, and both N0 `validation.json` files before projecting their fields into:

- `tables/n0_controls.csv`;
- `tables/fault_outcomes.csv`; and
- `tables/latency_summary.csv`.

`tables/TABLE_PROVENANCE.json` records the generator hash and every input/output hash. The generator does not recompute inferential results; it deterministically projects the already frozen validated summaries.

## Frozen source locators

| Purpose | Path | SHA-256 |
|---|---|---|
| Campaign design/timing | `research/icsec2026/runs/full_20260830_seed20260830_n30/manifest.json` | `10D966EE6F43BB70EAAFA713723F9C56EEDA51757E605BEB80A8578E0ABEE67F` |
| Seeded plan | `research/icsec2026/runs/full_20260830_seed20260830_n30/run_plan.csv` | `08BCBDD505DA95460ABFADE719411409501DE7B6F40BE648B30CB4E986F051B7` |
| Per-trial results | `research/icsec2026/runs/full_20260830_seed20260830_n30/results.csv` | `770FB1FEF5BFD6B529906B35CBA67D9BAC2887DED241EA38D8CB914A157478CE` |
| Campaign validation | `research/icsec2026/runs/full_20260830_seed20260830_n30/validation.json` | `D06426EE043D32B032FA3267E7A8DDAB0AD345FD1F69807E93E9F47507BA84EB` |
| Campaign summary | `research/icsec2026/runs/full_20260830_seed20260830_n30/summary.json` | `124554F98A93639B4C2C8C18A708DC14A1D5673823A4CD2F84DB0F563083E1CA` |
| Pre-N0 validation | `research/icsec2026/runs/n0_pre_20260830_0205/validation.json` | `872BA8EFD5E8F3505C6DEC62AFCAAC59A892D1ED407DDE67E7256B631FBEAA12` |
| Post-N0 validation | `research/icsec2026/runs/n0_post_20260830_0224/validation.json` | `B3EF1165183D2EEBB0049B11D006A602D2EE36AE5669BD8EA5E92BA091E095F1` |
