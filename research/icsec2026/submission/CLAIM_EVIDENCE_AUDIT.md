# Evidence omission and claim-to-evidence audit

## Corrected omissions

- The valid 605.0-s nominal observation is now reported separately from the two primary N0 windows and from the 90-trial denominator. Evidence: `primary_20260830_seed20260830_b5/nominal_validation_002.json`, SHA-256 `3119D5994378E00C7ACE945B0FCB96CBA28C5855CDFEA445CD26570FD52A74FD`. It contains 121 ONLINE records, `ok` 1760--2960, zero timeout/CRC/sequence/recovery deltas, and no prohibited marker.
- The BAD_CRC mechanism check is now reported as two separate mechanistic observations, not new campaign trials. The SHORT raw order is CRC reject then timeout count one, no OFFLINE before restoration. The SUSTAINED raw order is CRC reject, timeout counts one and two, then OFFLINE at consecutive count three; restoration confirmation and recovery follow. Evidence: `bad_crc_results.json` plus `raw/bad_crc/{SHORT,SUSTAINED}/{g431,g474}.log`, SHA-256 of results `F6332F913FFA91432032AA1E5582AE78378F8880FC22D11B921C5B793ADC4E90`. The derived `offline_before_restore` field is not used.

## Source-level trace

Evaluated acquisition revision: `cfd4b1b59d5018f498e5cc083ab27e1d230ae85d` from `FINAL_MANIFEST.json` (SHA-256 `D8424545495CCF2EBA2BF87BE5B68CDA79D3AA41239217140F54D20BD0DCE91E`).

- `core/include/comms/PayloadLinkController.hpp`, Git blob `e2b6c9e9bb4af62afa32daa455479575eebff19a`: 100-ms response deadline; three-timeout OFFLINE threshold. A BadCrc decode result increments `crcRejects` and returns before clearing `awaitingResponse`. Deadline service then increments timeout/consecutive count and sets OFFLINE at threshold. An accepted valid response clears the outstanding request, resets the consecutive count, sets ONLINE, and records recovery when applicable.
- `core/src/app/PayloadLinkTask.hpp`, evaluated Git blob `a76804eb567689588bc3b1459df9a9352ec0d4f4`: emits CRC rejection, timeout, OFFLINE, and recovery markers used in the raw-order trace. Later scope-only GPIO instrumentation does not alter the evaluated controller state machine and is not used as empirical evidence here.

This supports a protocol/control-flow explanation only. It does not establish MCU-internal timing.

## Claim boundaries

- Primary: one G431/G474 pair, 90 sequential valid trials, two 65-s N0 windows.
- Extended nominal: one separate 605-s observation; not a primary trial or reliability estimate.
- BAD_CRC check: two mechanistic observations; not added to the 90-trial denominator.
- F411: two physical pairs under the same fixed F411 configuration, each retained and analyzed as a separate 12-row dataset; no pooling, device-population inference, MCU equivalence, or primary-pair independence claim.
- Scope capture: excluded from timing claims because no machine-readable export and only 12.50 kSa/s at the selected window.

No frozen empirical number was changed. The N0 table was deterministically extended only with fields directly verified in `nominal_validation_002.json`.
