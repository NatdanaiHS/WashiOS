# ICSEC 2026 Pre-Confirmation-Gated Reframe Freeze

Status: **WORK_REVIEW_REQUIRED**

Verified: `2026-09-03T02:39:00+07:00`

This file records only the verified state frozen immediately before the final confirmation-gated reframing workflow. No reframing has begun. Git history is the record of prior plans and session states.

## Git state

- Branch: `experiment/icsec-extension-20260830`
- Upstream: `origin/experiment/icsec-extension-20260830`
- Pre-freeze HEAD: `402f4568a3742a369f9787172dea30231370b370`
- After `git fetch --prune origin`, local HEAD and the upstream ref were identical (`0` ahead, `0` behind).
- The working tree was clean before this state file was refreshed.
- Freeze tag: `icsec-2026-pre-confirmation-gated-reframe`. The tag's peeled commit is the authoritative final freeze commit; a commit cannot embed its own hash in this file.

## Current manuscript and reviewed PDF

- Canonical source: `research/icsec2026/submission/main.tex`
  - SHA-256: `AA018D5E677D8C6ECAE93DEB33C068B01AC6050B5B57D47F303166BB750007B4`
- Canonical reviewed PDF: `research/icsec2026/submission/main.pdf`
  - SHA-256: `99E4180F4B172C1CC7BABFCF8BE92FCC5442B3868F7AAD1D32A13779849E765D`
  - 68,688 bytes; 5 letter-size pages; unencrypted PDF 1.5.
- Bibliography: `research/icsec2026/submission/references.bib`
  - SHA-256: `B936C7F6AF1E173CEB771D5BB430F3652846B759C494E71B674D3071D387AC00`
- The reviewed manuscript source commit recorded by the submission package is `21129b1795102574dceb023f984c115630b18020`.
- The canonical source and PDF are byte-identical to both reviewed archive checkpoints:
  - `research/icsec2026/archive/manuscripts/pre_final_active_20260902/`
  - `research/icsec2026/archive/manuscripts/submission_candidate_20260902/`
- `research/icsec2026/submission/FINAL_VALIDATION.json`, the submission audits, and visual inspection of all five retained page renders report PASS. No PDF was regenerated during this freeze.

## Frozen empirical evidence used by the manuscript

### Primary G431/G474 campaign and primary N0 windows

- Campaign root: `research/icsec2026/runs/full_20260830_seed20260830_n30/`
- Pre-campaign N0 root: `research/icsec2026/runs/n0_pre_20260830_0205/`
- Post-campaign N0 root: `research/icsec2026/runs/n0_post_20260830_0224/`
- Lock inventory: `research/icsec2026/runs/full_20260830_seed20260830_n30/SHA256SUMS.csv`
  - SHA-256: `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD`
  - 195 rows covering the campaign, both N0 packages, 180 raw serial logs, and packaged firmware.
- Frozen validation records report 90/90 valid planned trials, 30 per mode, with 180 raw logs checked at acquisition time.
- Pre-N0 validation SHA-256: `872BA8EFD5E8F3505C6DEC62AFCAAC59A892D1ED407DDE67E7256B631FBEAA12`; valid 65.0-s window, 13 ONLINE records, `ok` 1835--1955, and zero timeout/CRC/sequence/recovery deltas.
- Post-N0 validation SHA-256: `B3EF1165183D2EEBB0049B11D006A602D2EE36AE5669BD8EA5E92BA091E095F1`; valid 65.0-s window, 13 ONLINE records, `ok` 3049--3169, and zero timeout/CRC/sequence/recovery deltas.
- Current-checkout limitation: an independent read-only check of the 195-row lock inventory found 9 byte-exact files, 185 absent files, and one size mismatch. The absent files are the 180 campaign raw logs, four N0 raw logs, and packaged G474 firmware. The one mismatch is `DATASET_README.md`, whose CRLF checkout form is 4,426 bytes; deterministic CRLF-to-LF normalization produces the inventory's exact 4,368 bytes and SHA-256 `03F9865F836D53725A48040AF56211AF8BD66FBDE8198FF6273229D66651638B`. The lock inventory and retained evidence were not altered. No verified external backup of this original 195-row package is recorded in the current cleanup-freeze records.

### Extended nominal observation and BAD_CRC mechanism evidence

- Package root: `research/icsec2026/extension/evidence/primary_20260830_seed20260830_b5/`
- Lock inventory: `EXTENSION_SHA256SUMS.csv`
  - SHA-256: `8B4CB2AB87CD317905AA4A219B81E99E2E459DC3EEF386D14286297476177C0B`
  - Current source check: 88/88 rows byte-exact; zero missing, size, or hash issues.
- Final manifest: `FINAL_MANIFEST.json`
  - SHA-256: `D8424545495CCF2EBA2BF87BE5B68CDA79D3AA41239217140F54D20BD0DCE91E`
- Extended nominal record: `nominal_validation_002.json`
  - SHA-256: `3119D5994378E00C7ACE945B0FCB96CBA28C5855CDFEA445CD26570FD52A74FD`
  - Valid 605.0-s observation, 121 ONLINE records, `ok` 1760--2960, zero timeout/CRC/sequence/recovery deltas, and no prohibited marker.
- BAD_CRC result record: `bad_crc_results.json`
  - SHA-256: `F6332F913FFA91432032AA1E5582AE78378F8880FC22D11B921C5B793ADC4E90`
  - The locked raw records under `raw/bad_crc/SHORT/` and `raw/bad_crc/SUSTAINED/` support the paper's separate short and sustained mechanism observations; they are not part of the 90-trial denominator.
- Evaluated acquisition revision: `cfd4b1b59d5018f498e5cc083ab27e1d230ae85d`.
- Mechanism source evidence:
  - `core/include/comms/PayloadLinkController.hpp`, Git blob `e2b6c9e9bb4af62afa32daa455479575eebff19a`
  - `core/src/app/PayloadLinkTask.hpp`, Git blob `a76804eb567689588bc3b1459df9a9352ec0d4f4`

### F411 Pair-1

- Package root: `research/icsec2026/extension/evidence/f411_pair1_campaign_20260901_seed20260901_b3/`
- Lock inventory: `F411_PAIR1_CAMPAIGN_SHA256SUMS.csv`
  - SHA-256: `797F908BCFC5EB5450302360501016DCB23188996C15194D9CF91C8BE619C2BC`
  - Current source check: 95/95 rows byte-exact; zero missing, size, or hash issues.
- `final_validation.json` and `independent_validation.json` both report 12/12 valid predefined rows, zero invalid rows, and no raw-record validation failure.
- This is a separate pair-specific dataset and is not pooled with Pair-2 or the primary G431/G474 campaign.

### F411 Pair-2

- Package root: `research/icsec2026/extension/evidence/f411_pair2_campaign_20260901_seed20260901_b3/`
- Lock inventory: `F411_PAIR2_CAMPAIGN_SHA256SUMS.csv`
  - SHA-256: `481F56C98647D037CFAA5698BDEF61C0D918D42954A646E36C7479EA8203588E`
  - Current source check: 81/81 rows byte-exact; zero missing, size, or hash issues.
- `final_validation.json` and `independent_validation.json` both report 12/12 valid predefined rows, zero invalid rows, and no raw-record validation failure.
- This is a separate pair-specific dataset and is not pooled with Pair-1 or the primary G431/G474 campaign.

## External verified backups

Existing verification records identify these relevant external backups:

- `C:/WashiOS-extension-backup/primary_20260830_seed20260830_b5/`
- `C:/WashiOS-extension-backup/f411_pair1_campaign_20260901_seed20260901_b3/`
- `C:/WashiOS-extension-backup/f411_pair2_campaign_20260901_seed20260901_b3/`

`research/icsec2026/cleanup_freeze_20260902/VALIDATION.json` records PASS for the protected repository and external-backup manifests. The external backup files were not copied, renamed, moved, deleted, regenerated, modified, or re-inventoried during this freeze.

## Freeze boundary

- No empirical evidence file was copied, renamed, moved, deleted, regenerated, or modified.
- No backup copy was created inside the repository.
- No external verified backup was modified.
- The next workflow may reframe the manuscript only after review of this freeze, especially the incomplete current-checkout materialization of the original 195-row primary campaign package.
- Stop condition: **WORK_REVIEW_REQUIRED**.
