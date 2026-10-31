# Payload-Link Quantitative Hardware Dataset

## Dataset identity

- Campaign: `full_20260830_seed20260830_n30`
- Fixed seed: `20260830`
- Hardware: NUCLEO-G431RB controller plus NUCLEO-G474RE simulated payload
- Firmware source commit: `ae891a70ca961d247b5fd5ac487271caf2fc881f`, with the uncommitted session modifications recorded in `research/icsec2026/SESSION_STATE.md`
- Design: 30 randomized trials each of SILENT, BAD_CRC, and DELAYED; 90 trials total
- Controls: dedicated 65-second pre-campaign and post-campaign N0 / Nominal Control windows
- Timing basis: host serial receipt timestamps; no MCU/host clock synchronization

## Contents

- `manifest.json`: campaign parameters, state history, timing definitions, and completion status
- `run_plan.csv`: immutable seeded randomized run order and pre-injection offsets
- `results.csv`: per-trial activation, detection, offline, restoration, recovery, restart-marker, outcome, and validity fields
- `raw/<run_id>/g431.log`: exact-hex plus readable G431 serial records with host timestamps
- `raw/<run_id>/g474.log`: exact-hex plus readable G474 serial records with host timestamps
- `validation.json`: machine validation of plan/results structure and all 180 raw logs
- `summary.json`: valid/invalid counts, exact 95% binomial intervals, and latency distributions
- `firmware/g474_payload_firmware.bin`: exact G474 image used for acquisition
- `SHA256SUMS.csv`: deterministic inventory for firmware, campaign artifacts/raw logs, and both N0 packages

The pre-N0 package is `research/icsec2026/runs/n0_pre_20260830_0205/`. The post-N0 package is `research/icsec2026/runs/n0_post_20260830_0224/`.

## Observed

- Both N0 windows lasted 65.0 seconds and contained 13 ONLINE status records with strictly increasing `ok`.
- Within each N0 window, timeout, CRC, sequence, and recovery counter deltas were zero, and no timeout, offline, rejection, recovery, or post-start link-start marker appeared.
- The campaign completed 90/90 planned trials with 30 trials per fault mode, zero invalid trials, and all G474 activation and NORMAL restoration confirmations present.
- Detection was observed in 30/30 valid trials for each mode. The two-sided 95% Clopper-Pearson interval is 0.884296692 to 1.0 for each 30/30 proportion.
- Recovery was observed in 30/30 valid trials for each mode, with the same exact interval.
- OFFLINE was observed in 30/30 trials for every mode under the configured four-second fault observation period.
- No post-injection `PAYLOAD_LINK_START` marker was observed in any trial.
- Host-observed detection latency summaries in milliseconds were:
  - SILENT: median 383.0, IQR 196.25, minimum 125.0, maximum 578.0
  - BAD_CRC: median 359.5, IQR 293.0, minimum 78.0, maximum 531.0
  - DELAYED: median 406.0, IQR 215.0, minimum 156.0, maximum 610.0
- Host-observed restoration-command-to-recovery latency summaries in milliseconds were:
  - SILENT: median 297.0, IQR 230.75, minimum 78.0, maximum 516.0
  - BAD_CRC: median 359.0, IQR 303.5, minimum 47.0, maximum 531.0
  - DELAYED: median 296.5, IQR 238.25, minimum 94.0, maximum 531.0

## Supported inference

- For this board pair, firmware image, wiring, host, and configured timing, all three injected payload behaviors consistently produced their predefined G431 log detector evidence and returned to a logged recovered state after confirmed NORMAL restoration.
- The dedicated N0 windows support nominal link stability during the two observed 65-second control periods.
- The raw evidence and validation support reporting observed detection/recovery proportions and host-observed latency distributions for this experiment.

## Unknown / not supported

- Absence of `PAYLOAD_LINK_START` is not absolute proof that the controller MCU never reset.
- Literal `heartbeat=OK watchdog=OK` strings are not independent heartbeat/watchdog measurements.
- Host-observed latency includes UART transmission, USB, driver, thread scheduling, and timestamping uncertainty; it is not MCU-internal latency.
- This single G431/G474 pair does not establish cross-device, environmental, or long-duration generalization.
- Trials are repeated sequential measurements on one setup; no claim of independent hardware replicates is supported.
- No fair C0 ablation exists in the repository, and none was created or evaluated. N0 denotes the healthy nominal control only.
