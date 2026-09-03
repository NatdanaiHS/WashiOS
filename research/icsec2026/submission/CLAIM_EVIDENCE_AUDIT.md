# Evidence omission and claim-to-evidence audit

## Corrected omissions

- The valid 605.0-s nominal observation is now reported separately from the two primary N0 windows and from the 90-trial denominator. Evidence: `primary_20260830_seed20260830_b5/nominal_validation_002.json`, SHA-256 `3119D5994378E00C7ACE945B0FCB96CBA28C5855CDFEA445CD26570FD52A74FD`. It contains 121 ONLINE records, `ok` 1760--2960, zero timeout/CRC/sequence/recovery deltas, and no prohibited marker.
- The BAD_CRC mechanism check is now reported as two separate mechanistic observations, not new campaign trials. The SHORT raw order is CRC reject then timeout count one, no OFFLINE before restoration. The SUSTAINED raw order is CRC reject, timeout counts one and two, then OFFLINE at consecutive count three; restoration confirmation and recovery follow. Evidence: `bad_crc_results.json` plus `raw/bad_crc/{SHORT,SUSTAINED}/{g431,g474}.log`, SHA-256 of results `F6332F913FFA91432032AA1E5582AE78378F8880FC22D11B921C5B793ADC4E90`. The derived `offline_before_restore` field is not used.

## Source-level trace

Evaluated acquisition revision: `cfd4b1b59d5018f498e5cc083ab27e1d230ae85d` from `FINAL_MANIFEST.json` (SHA-256 `D8424545495CCF2EBA2BF87BE5B68CDA79D3AA41239217140F54D20BD0DCE91E`).

- `core/include/comms/PayloadLinkController.hpp`, Git blob `e2b6c9e9bb4af62afa32daa455479575eebff19a`: lines 33--34 define the 100-ms response deadline and three-timeout OFFLINE threshold; lines 36--50 increment the timeout streak and set OFFLINE at the threshold; lines 75--103 reject invalid CRC/sequence responses without clearing the outstanding request; and lines 110--119 clear the request and streak, set ONLINE, and count recovery after an accepted response from OFFLINE.
- `core/src/app/PayloadLinkTask.hpp`, evaluated Git blob `a76804eb567689588bc3b1459df9a9352ec0d4f4`: lines 75--104 route decoded frames to the controller and emit rejection/recovery consequences; lines 108--125 emit timeout or OFFLINE after controller service; lines 209--249 define the recovery, rejection, timeout, and OFFLINE marker text. Later scope-only GPIO instrumentation does not alter the evaluated controller state machine and is not used as empirical evidence here.

## Figure 1 protocol-transition trace

Figure 1 is an experimental protocol/topology figure, not a reconstructed controller state machine. Every event transition is supported by the frozen campaign runner `research/icsec2026/injector/run_payload_campaign.py`, Git blob `68625847689bfe7906833bc1ade8dc9f8169625e`:

- requested -> activation confirmed: lines 391--404 send the selected mode and require the matching payload confirmation; lines 400--404 record missing confirmation as `FAULT_ACTIVATION_NOT_CONFIRMED` or retain the confirmation time;
- activation confirmed -> detected: lines 406--409 establish the controller-observation phase, and lines 431--449 select the predefined post-request detector marker and its host-observed interval;
- detected -> restore request: lines 411--414 send NORMAL and retain the restore-command host time after the fixed observation phase;
- restore requested -> restoration confirmed: lines 415--421 require the payload's NORMAL confirmation and otherwise record `NORMAL_RESTORE_NOT_CONFIRMED`;
- restoration confirmed -> recovered: lines 423--457 observe the post-restore controller stream, select a recovery marker only after the restore request, and populate recovery timing only when restoration confirmation exists; and
- stage-specific eligibility: lines 400--404 make missing activation an invalid trial condition, lines 443--449 retain an observed detection independently of restoration, lines 454--457 populate recovery timing only with restoration confirmation, and lines 460--467 preserve the stricter complete-trial outcome rule.

The same runner lines 134--180 define concurrent serial capture, lines 321--326 define command-send capture, lines 329--336 match payload mode confirmations, and lines 531--540 record the exact-byte log format and measurement definitions. Because capture is concurrent and detector selection covers all events after the request (line 431), a detector marker can be received while activation confirmation is still being awaited. Figure 1's arrows therefore denote validation/scoring stages, not a claim that all raw host timestamps have the same strict order. No unverified internal transition is drawn.

This supports a protocol/control-flow explanation only. It does not establish MCU-internal timing.

## Payload-confirmation causal ordering and trust boundary

- In the protected G474 payload source `demo-payload/src/main.cpp` (SHA-256 `FB83C6AEFDB6A2488648B56E9AE1CFBF5FC87AEF6312915CCF7FA2C803C50EE5`), lines 240--248 parse into local selected values, assign `currentMode` and `delayedResponseMs`, and only then call `logMode()`. Lines 197--208 construct the confirmation from those assigned values and transmit it. The main loop calls `serviceHostCommands()` before `serviceLink()` at lines 451--452.
- The protected F411 payload source `demo-payload/src/f411_main.cpp` (SHA-256 `0275FD31799420707E2AE87411497D7C50018E0E8ABF7F957030B000C7E974BD`) uses the same assignment-before-confirmation order at lines 142--150 and calls command service before link service at lines 309--310. `demo-payload/src/HostModeCommandParser.hpp` (SHA-256 `23460BCDC2E6B77CDF3FAB9CFF0542C8987BE1A59DB6CEE3B3EB6FE0804DFFBE`) returns `ModeSelected` only after selecting the parsed mode.
- The primary-run frozen worktree patch independently records `currentMode = selectedMode` before `logMode()` in `provenance/20260830_023830/source_state/tracked_worktree.patch`, lines 95--102. Thus the confirmation establishes a software causal boundary for scorer eligibility. It is not an independent physical measurement of UART behavior.
- Consistent with that boundary, a controller marker received before matching activation confirmation is outside the eligible interval and is ignored. The retained synthetic replay records this as `DETECTOR_BEFORE_ACTIVATION_IGNORED` and produces an eligible `NOT_DETECTED` result after activation is confirmed; it does not classify the marker as ambiguous or invalidate the trial.

## Claim boundaries

- Primary: one G431/G474 pair, 90 sequential valid trials, two 65-s N0 windows.
- Extended nominal: one separate 605-s observation; not a primary trial or reliability estimate.
- BAD_CRC check: two mechanistic observations; not added to the 90-trial denominator.
- F411: two physical pairs under the same fixed F411 configuration, each retained and analyzed as a separate 12-row dataset; no pooling, device-population inference, MCU equivalence, or primary-pair independence claim.
- Scope capture: excluded from timing claims because no machine-readable export and only 12.50 kSa/s at the selected window.

No frozen empirical number was changed. The N0 table was deterministically extended only with fields directly verified in `nominal_validation_002.json`.
