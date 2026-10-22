# Expected verdicts per configuration

`tooling/run_verifyta.sh` verifies every `.q` file against every configuration of its model (21 configurations, 2 × 11 + 3 × 14 + 16 × 19 = 368 formulas). Some formulas are
deliberately expected to be **NOT satisfied**: tightness checks (suffix `T`), scenario-specific formulas run
under the other scenario, reachability checks for the design variant, and the finding-bearing formulas whose
violation is the result. This table is the oracle; a run "passes" when every actual verdict equals the
expected one. `S` = satisfied, `N` = not satisfied, `–` = vacuously satisfied (antecedent unreachable).

## payload_link.q (DRAFT-CAMERA-READY, predicted 2026-10-18 before any run)

Formula order as in the file (19 formulas). The draft model replaces the one-frame serialization window
[3,4] ms by a round trip from the poll stamp (decode 2..9 ms, then response 2..4 ms, plus 0..1 ms of
`HAL_Delay` overrun in DELAYED and a pickup within L+J), captures the payload mode at decode time, and adds
an optional status-report block of at most SLIP ms per 5000 ms (assumption A7). Configurations run with
SLIP 0 (no status report in the window; `Status` template absent) and, suffix `_status`, SLIP 60.

Boundary predicates: `ACCEPTS` = d + 14 < 100, i.e. d ≤ 85. `TIMES_OUT` = d + 4 > 103 + SLIP, i.e.
d ≥ 100 at SLIP 0 and d ≥ 160 at SLIP 60. Undetermined band: 86–99 ms (SLIP 0), 86–159 ms (SLIP 60).

Closed-form bounds (SLIP 0 / SLIP 60): first timeout P+J−DECODE_MIN+D+L+J+SLIP = **603 / 663**;
OFFLINE 3(P+J)−DECODE_MIN+D+L+J+SLIP = **1607 / 1667**; recovery
P+J−DECODE_MIN+DECODE_MAX+RESP_MAX+L+J+SLIP = **516 / 576** ms.

Four patterns (verdict strings in Q-order):

| Pattern | String | Configurations |
|---|---|---|
| timeout mode (bounds tight) | `SSSNSNSNSSSSSSNNSSS` (14 S, 5 N) | silent, badcrc, d100, d110, d150, d250, d100_j0, d100_j1, silent_status, badcrc_status, d250_status |
| accepted (d ≤ 85) | `SSSSSSSSSSSSSSNNSSS` (17 S, 2 N) | d50 |
| band | `SSSSSSSNSSSSSSSSSSS` (18 S, 1 N) | d100_j5 |
| band, recovery bound not attained | `SSSSSSSSSSSSSSSSSSS` (19 S) | d90, d90_status (**corrected after the run**, see below) |
| band created by the status block | `SSSSSSSNSSSSSSSNSSS` (17 S, 2 N) | d110_status |

Changes against the submitted model, all predicted: d = 100 ms moves from the band to a decided timeout
(the hardware rejected 100 ms in every valid trial); d = 90 ms moves from "accepted" into the band (the
hardware accepted it in every valid trial: consistent, not proven); with the status block a 110 ms
response can be accepted when the block covers the deadline check (Q9c-1 holds), but a single block per
5 s cannot rescue every poll of a 1326 ms exposure (Q9c-2 fails).

### Outcome of run `results/20261018T073529Z/` (2026-10-18)

19 of 21 configurations matched the prediction. The two mismatches were the same formula: Q4T was
predicted N for `payload_delayed_90` and `payload_delayed_90_status` and is S. The probe in
`results/20261018T073529Z_q4t_probe/` locates the worst-case recovery at 513 ms (573 ms with the status
block), against 516 ms (576) in SILENT, where the bound is attained. Cause: at d = 90 the link is OFFLINE at
restoration only if the delayed response arrived after the earliest deadline check (100 ms), which needs a
decode later than 100 − 90 − 1 − 4 = 5 ms after the poll; restoration cannot precede that decode, so the
worst case is 516 − (5 − 2) = 513 ms. Q4 holds in every configuration; it is tight only in timeout modes.
This was a prediction error, not a model error. The oracle was corrected with the reason recorded in
`tooling/check_verdicts.py`. The original prediction for both rows was `SSSSSSSNSSSSSSSSSSS`.

### Jitter sensitivity at d = 100 ms (SLIP 0)

`TIMES_OUT` = 104 > 101 + J holds for J ≤ 2. Predicted: `_j0`, `_j1` timeout pattern; `_j5` band pattern.
The band no longer collapses with J alone: its lower edge (86 ms) is set by the round-trip window, not by J.

## watchdog_gating.q

11 formulas. Configurations: `watchdog_nostall` (SCENARIO 0), `watchdog_stall` (SCENARIO 1).

| # | Id | nostall | stall | Meaning |
|--:|---|---|---|---|
| 1 | Q0 | S | S | no deadlock |
| 2 | W1a | S | **N** | never reset (only meaningful without stall) |
| 3 | W1b | S | **N** | never a critical failure (only meaningful without stall) |
| 4 | W2 | S | S | no IWDG refresh after a critical failure |
| 5 | W3-HB | – | S | heartbeat stall detected ≤ 1652 ms |
| 6 | W3-PL | – | S | payload-link stall detected ≤ 952 ms |
| 7 | W3T | – | **N** | 952 is tight |
| 8 | W5 | – | S | stall leads to reset |
| 9 | W6-PL | – | S | payload-link stall to reset ≤ 952 + 2170 ms |
| 10 | W6-HB | – | S | heartbeat stall to reset ≤ 1652 + 2170 ms |
| 11 | W7 | S | S | reset only after a recorded critical failure |

## boot_policy.q

14 formulas. Configurations: `boot_shipped` (APP_CONFIRMS 0, FALLBACK_RESETS 0), `boot_design` (APP_CONFIRMS 1, FALLBACK_RESETS 0), `boot_f4fix` (APP_CONFIRMS 0, FALLBACK_RESETS 1 -- the F4 fix: `resetBootAttempts()` before `activateBootSlot()` on the fallback path, `BootPolicy.hpp:86-92`).

| # | Id | shipped | design | f4fix | Meaning |
|--:|---|---|---|---|---|
| 1 | Q0 | S | S | S | no deadlock |
| 2 | B1 | S | S | S | never launch an unvalidated image |
| 3 | B2 | S | S | S | never launch a non-bootable slot state |
| 4 | B3 | S | S | S | Pending slot launched ≤ 4 times in a row |
| 5 | B4 | S | S | S | both images bad at boot ⇒ safe loop |
| 6 | B5a | S | S | S | safe loop reachable |
| 7 | B5b | S | S | S | safe loop recorded |
| 8 | B6 | S | S | S | retained critical fault ⇒ no relaunch before cold start (finding F2) |
| 9 | B7 | S | **N** | S | Pending never becomes Confirmed (finding F1 in shipped) |
| 10 | B7r | **N** | S | **N** | confirmation reachable only in the design variant |
| 11 | B8 | **N** | **N** | S | unconfirmed-boot limit never bypassed — violated via fallback (finding F4); holds once the fallback resets the budget |
| 12 | B8b | S | S | S | the bypass exists only on the fallback path |
| 13 | B8c | S | **N** | S | after an over-limit fallback launch the next warm boot is refused (design variant may confirm instead); **vacuous** under the fix, where no over-limit launch occurs |
| 14 | B9 | S | S | S | progress: every reset runs the policy to AppRunning or SafeLoop |

## Deadlock freedom and progress

`A[] not deadlock` (Q0) holds in every configuration: no reachable state of any model blocks all discrete
transitions forever. Because the environment automata of the boot model always have an enabled edge, Q0
alone would be weak there; the leads-to properties Q11a/Q11b (payload link), W5 (watchdog), and B9 (boot)
state the intended progress explicitly. These are properties of the models. Task-level blocking in the
firmware is excluded by construction, not by the models: the flight code uses no semaphores, queues,
mutexes, event groups, or task notifications (verified with `git grep` over `core/`, `bootloader/`,
`demo-payload/` excluding the vendored FreeRTOS sources on 2026-09-08); it blocks only in `vTaskDelay`,
non-blocking `taskENTER_CRITICAL` sections, and HAL UART calls with a 10 ms timeout.

## Findings carried by NOT-satisfied verdicts

- **F1** (B7/B7r): the shipped application never confirms a boot; the A/B confirmation path is unreachable.
- **F4** (B8): `isPendingBootAttemptLimitExceeded()` is evaluated for the active slot only; when the active slot
  fails validation and the fallback slot is Pending, the fallback launch inherits `boot_count` accumulated by
  the previous slot and may be launched already over the limit. B8c shows the next warm boot is then refused,
  so a Pending fallback image effectively gets one attempt instead of three.
- Undetermined band (Q9c): 86–99 ms between status reports, 86–159 ms when a status report falls in the
  window. The frozen sweep (90 ms accepted, 100 ms and above timed out in every valid trial) is consistent
  with both, not proven by either.
