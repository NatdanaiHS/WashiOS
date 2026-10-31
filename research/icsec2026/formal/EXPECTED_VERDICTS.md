# Expected verdicts per configuration

`tooling/run_verifyta.sh` verifies every `.q` file against every configuration of its model (14 configurations, 240 formulas). Some formulas are
deliberately expected to be **NOT satisfied**: tightness checks (suffix `T`), scenario-specific formulas run
under the other scenario, reachability checks for the design variant, and the finding-bearing formulas whose
violation is the result. This table is the oracle; a run "passes" when every actual verdict equals the
expected one. `S` = satisfied, `N` = not satisfied, `–` = vacuously satisfied (antecedent unreachable).

## payload_link.q

Formula order as in the file (19 formulas). Configurations: `silent`, `badcrc`, `delayed_50`, `delayed_90`,
`delayed_100`, `delayed_110`, `delayed_250`. Boundary predicates: `ACCEPTS` holds for d ≤ 95;
`TIMES_OUT` holds for d ≥ 101; d = 100 is in the undetermined band.

| # | Id | silent | badcrc | d50 | d90 | d100 | d110 | d250 | Meaning |
|--:|---|---|---|---|---|---|---|---|---|
| 1 | Q0 | S | S | S | S | S | S | S | no deadlock |
| 2 | Q1 | S | S | S | S | S | S | S | no false OFFLINE in nominal |
| 3 | Q2 | S | S | – | – | – | S | S | first timeout ≤ 605 ms |
| 4 | Q2T | **N** | **N** | – | – | – | **N** | **N** | 605 is tight (may occur exactly at 605) |
| 5 | Q3 | S | S | – | – | – | S | S | OFFLINE ≤ 1609 ms |
| 6 | Q3T | **N** | **N** | – | – | – | **N** | **N** | 1609 is tight |
| 7 | Q4 | S | S | S | S | S | S | S | recovery ≤ 506 ms after restoration |
| 8 | Q4T | **N** | **N** | – | – | **N** | **N** | **N** | 506 is tight (vacuous when never OFFLINE) |
| 9 | Q5 | S | S | S | S | S | S | S | Restored leads to ONLINE |
| 10 | Q6 | S | S | S | S | S | S | S | OFFLINE only at threshold |
| 11 | Q7 | – | S | – | – | – | – | – | BAD_CRC: CRC reject before first timeout |
| 12 | Q8 | – | S | – | – | – | – | – | BAD_CRC: CRC reject alone keeps ONLINE |
| 13 | Q9a | – | – | S | S | – | – | – | ACCEPTS: never a timeout |
| 14 | Q9b | – | – | – | – | – | S | S | TIMES_OUT: late frames sequence-rejected |
| 15 | Q9c-1 | **N** | **N** | **N** | **N** | S | **N** | **N** | undetermined band: a timeout is reachable |
| 16 | Q9c-2 | **N** | **N** | **N** | **N** | S | **N** | **N** | undetermined band: no timeout is also reachable |
| 17 | Q10 | S | – | – | – | – | – | – | SILENT: nothing received |
| 18 | Q11a | S | S | S | S | S | S | S | progress: Awaiting leads to Idle (every poll resolved) |
| 19 | Q11b | S | S | S | S | S | S | S | progress: Idle leads to Awaiting (controller always polls again) |

### Jitter sensitivity at the boundary delay (d = 100 ms)

`payload_delayed_100_j0`, `_j1`, `_j5` sweep assumption A1. The expectation was derived analytically
*before* the run, from the model's own predicates: `ACCEPTS` does not involve J, so its edge stays at
d ≤ 95 ms, while `TIMES_OUT` = d + TX_MIN > D + L + J holds for d ≥ 99 + J. Hence d = 100 is decided as a
timeout for J ≤ 1 and undetermined for J ≥ 2, and the undetermined band is 96 to 98 + J ms.

| Configuration | Expected pattern | Meaning |
|---|---|---|
| `payload_delayed_100_j0` | as `delayed_110` (14 S, 5 N) | J = 0: d = 100 decided as a timeout; band 96–98 ms |
| `payload_delayed_100_j1` | as `delayed_110` (14 S, 5 N) | J = 1: d = 100 decided as a timeout; band 96–99 ms |
| `payload_delayed_100_j5` | as `delayed_100` (18 S, 1 N) | J = 5: d = 100 still undetermined; band 96–103 ms |

All three predictions were confirmed by the run on 2026-09-08. The undetermined band at the shipped
constants is therefore a consequence of the conservative 2 ms jitter bound, not a limitation of the model.

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
- Undetermined band (Q9c at d = 100): under a 2 ms jitter bound the model cannot decide a 100 ms delayed
  response; the frozen hardware evidence rejected it in every valid trial on three board pairs. Consistent,
  not proven.
