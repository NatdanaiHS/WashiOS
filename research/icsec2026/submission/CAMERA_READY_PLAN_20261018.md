# Camera-ready plan: response to ICSEC 2026 final-round reviews (2026-10-18)

Input: `EMAIL_REVIEW.md` (paper #1571357468, accepted; camera-ready due 2026-11-05, IEEE PDF eXpress).
Reviewer 1 left every field empty. Constraint: no hardware until further notice, so this plan separates
what can be fixed from code, models and frozen evidence (Part A) from what needs the boards (Part B).

Every evidence number below was recomputed from files in this checkout; scripts are described inline so
they can be re-run and retained before any number goes into `main.tex`.

## 1. Adjudication of the reviewer comments

| # | Comment | Verdict | Evidence | Action |
|---|---|---|---|---|
| R2.1 | J = 2 ms is assumed, not measured; all bounds depend on it | **Fair, and worse than the reviewer knows** | §III-B and §V-A say "assumed, not measured". Frozen nominal logs show the assumption is violated once every 5 s (finding E1 below) | A1, A2, B1 |
| R2.2 | One interval exceeds its bound by 17 ms, unexplained; is J big enough? | **Fair; partly explainable now** | §IV-C reports R085_P02 (BAD_CRC recovery, 522.8 ms vs 506 ms) as unresolved. E1, E2, E3 give three candidate mechanisms the paper does not mention | A1, A3, A4, B1, B2 |
| R2.3 | Narrow the model–code gap for at least one mechanism | **Fair; feasible without hardware** | §V-A: "a code-level check of the header-only controller ... is future work" | A5 |
| R3.1 | Simplified models, not the actual firmware | **Already conceded** (abstract last sentence, §I "Assurance limits", §V-A). A5 gives a concrete partial answer | — | A5 |
| R3.2 | Hardware validation only for the payload link; watchdog and boot need experiments | **Fair, already conceded** in Table I and the last sentence of §V-A | Table I: watchdog "no stall in the frozen traces", boot "no trace evidence" | A5 (native/host-side), B3, B4 |
| R3.3 | Explain technical terms; make figures easier to read | **Fair** | Fig. 1 is drawn at `scale=0.84` with `\scriptsize` labels; terms used before or without definition include TCTL fragment, leads-to, tightness twin, Pending/Confirmed, IWDG/LSI, confirmation anchor, falsification floor | A6 |
| R3.4 | More detail on timing assumptions and the 17 ms difference | **Fair** (same as R2.2) | — | A1–A4 |

## 2. New findings from the frozen evidence (no hardware used)

**E1. The 2 ms jitter assumption does not hold for the poll period that contains the 5 s status report.**
In `extension/evidence/primary_20260830_seed20260830_b5/raw/nominal/NOMINAL_00{1,2}/g431.log`
(the 605 s observation, about 1220 consecutive accepted polls each), host-stamped intervals between
consecutive `PAYLOAD_ACCEPTED` lines cluster at 491–500 ms. The interval that contains a
`[OBC] PAYLOAD_STATUS` line (emitted every `StatusPeriodMs = 5000`, `PayloadLinkTask.hpp:20`) is
instead 508–557 ms. The following polls keep the shifted phase: over the five periods spanning a status
line the schedule slips about +25 to +55 ms. A host-side read delay cannot shift every later line, so the
poll itself left late on the MCU. This follows from `nextPollMs = nowMs + PollPeriodMs`
(`PayloadLinkController.hpp`, the anchoring the paper already models). The G431-B replication logs
(`replication_g431b_20260830_seed20260830_b3/raw/*/*/g431.log`) show the same pattern on a second board.
- Effect on the model: one period in ten is about P + 25..55 ms, not P + J. The first-timeout and OFFLINE
  bounds (Q2, Q3) and the recovery bound (Q4) are sound only for windows that contain no status report.
- Cause not established. A blocking 115200-baud write of a ~110-byte line takes ~9.5 ms, less than the
  observed slip. Note also that `HAL_UART_Transmit` uses `HAL_GetTick()` for its timeout, which is frozen
  after the scheduler starts, so the "10 ms UART timeout" in §V-A is not enforced on the G4. Root cause
  needs B1.

**E2. The response-time constant T_tx ∈ [3,4] ms covers one frame, but the modeled interval is a round
trip.** `MODEL_CODE_TRACE.md` A2 derives T_tx from a single 32-byte frame (2.78 ms) plus decode work.
In the model the Payload clock starts at the poll send, so T_tx must cover: poll serialization (2.78 ms,
blocking `writeBuffer` after `preparePoll` has stamped `nowMs`), the responder's main loop
(`HAL_Delay(1)`, so up to ~2 ms before `serviceLink()` runs, `demo-payload/src/main.cpp`), response
serialization (2.78 ms), and the controller's next receive pass (up to L + J). That gives roughly
6–10 ms, not 3–4. The responder can also be held up by its own blocking debug writes, e.g. `logMode()`
right at the confirmation instant. The recovery bound P + J + T_tx^max and the Q9 delay boundary both use
T_tx, so both move by several ms.

**E3. The observation path adds a systematic offset the paper does not account for.** The recovery
endpoint is the host stamp at the end of `[OBC] PAYLOAD_RECOVERED ...`, which is written *after*
`[OBC] PAYLOAD_ACCEPTED ...` (`PayloadLinkTask.hpp` `receiveFrames`). That is about 75 bytes, or 6.5 ms
at 115200, after the internal event, before USB/VCP latency. The anchor `[PAYLOAD] MODE=NORMAL` is
about 23 bytes (2 ms) after the assignment, which shortens the interval. Net offset is about +4.5 ms
before any USB latency.

**E4. The paper's uncertainty argument attributes the 15.4 ms disagreement to the wrong clock.** Every
command-anchored latency in `runs/.../results.csv` is a whole number of ms, and adjacent distinct values
are 14–16 ms apart (47, 78, 94, 109, 125, 140 ...). They come from `time.monotonic()`
(`injector/run_payload_campaign.py:448,456`), which on Windows ticks at ~15.6 ms. The wall-clock
`datetime.now()` stamps that the confirmation anchor uses have sub-ms resolution (522.800, 505.418,
9.999 ms). So the 15.4 ms disagreement measures the *monotonic* tick, not wall-clock granularity. §III-F
("bounds the wall-clock granularity at 15.4 ms") and §IV-C ("larger than the 15.4 ms clock
disagreement") rest on this misattribution, and so does the code comment in
`check_frozen_traces.py`. The 17 ms excess is therefore *less* explainable by timestamp granularity
than the paper suggests. Confirm the Python version and OS in `provenance/` before rewording.

**Is R085 explained?** Not proven. E2 + E3 account for roughly 7–11 ms of the 17 ms. If a status report
fell inside R085's recovery period, E1 alone would cover it, since a +25–55 ms slip exceeds 17 ms.
The primary raw logs that would show that are not in this checkout (external backup,
`extension/recovery/recovery_20260901/`). Retrieving `R085_P02`'s `g431.log` from the backup would
settle it without new hardware: look for a `PAYLOAD_STATUS` line between the NORMAL confirmation and
`PAYLOAD_RECOVERED`. None of the 42 recoveries in the extension raw logs has a status line in its
window, and their maximum is 462 ms, which fits the hypothesis but does not test it.

## Part A: fixes that need no hardware

- **A0 (do first). Pull `R085_P02` (and `R047_P02`, 505 ms, the runner-up) raw logs from the verified
  backup**, read-only, and check for a status line in the recovery window. Record the result in a new
  exclusively named analysis directory, never under `runs/`.
- **A1. Revise the model's timing assumptions**, keeping the models and trace consistent
  (`models/payload_link.xml`, `MODEL_CODE_TRACE.md`, `check_frozen_traces.py` constants, Table III):
  - Re-derive T_tx as a round trip from source (E2), with the line numbers in the trace.
  - Model the status-report period explicitly: either a separate per-period delay `S` that applies to
    at most one period in every 10, or report bounds for "no status report in window" plus a worst-case
    variant with `J_status` set to the evidence maximum (about 60 ms, labeled host-observed). The bounds
    are already closed forms in J (§III-B), so this is a parameter change plus a re-run.
  - Re-run `tooling/run_verifyta.sh` into a new `results/<stamp>/`, update `EXPECTED_VERDICTS.md`, and
    re-check with `check_verdicts.py`. Every number the gate checks will change, so update
    `verify_manuscript.py` expectations together with `main.tex`.
- **A2. Add an evidence-derived jitter paragraph** answering R2. This is *not* "measured on target": it
  is host-observed and covers per-period scheduling only. From the 605 s observation: steady periods
  491–500 ms (spread within host noise, consistent with a small J), one period in ten +25–55 ms aligned
  with the status report, and the 0.235 % clock-rate result already in the paper. State that this
  bounds the per-period delay from above and shows J = 2 ms is violated periodically, and that MCU-side
  measurement is B1. Retain the analysis script and its output under a new analysis directory with a
  hash inventory.
- **A3. Fix the uncertainty reasoning (E4).** Rewrite §III-F and the §IV-C sentence. The wall-clock
  stamps are fine-grained; the 15.4 ms figure is the monotonic tick. The 50 ms falsification floor must
  be re-justified, e.g. from E1 (largest observed schedule slip) plus E3, or reduced. Update the
  `check_frozen_traces.py` docstring and comment and add a unit test, without touching frozen data.
- **A4. Re-explain the 17 ms in §IV-C** with E1–E3 as candidate mechanisms, each with its size and
  source line. If A0 finds a status line in the window, report it as explained by E1, and say so in
  the abstract; otherwise keep "unresolved" and list the mechanisms. Add the console-serialization
  offset (E3) to the replay as a stated, source-derived term, not a fitted one.
- **A5. Narrow the model–code gap without hardware (R2.3, R3.1, partly R3.2).** All three mechanisms
  have pure-logic C++ cores that already build natively:
  - *Payload link:* a native test that drives the real `PayloadLinkController` + `PayloadLinkTask`
    receive/service/poll order over a simulated ms clock, sweeping every fault-onset phase 0–499 ms,
    T_tx and per-period delays in the modeled range, asserting the Q2/Q3/Q4 bounds and the Q9
    boundary. With integer-ms time this is exhaustive over the phase space for the stated parameters.
    It is the cheapest "code conforms to the model" evidence.
  - *Boot policy:* enumerate every retained state (active slot, slot states, boot count 0–255,
    confirmed flag, retained fault, metadata corruption, image validity) through the real `BootPolicy`
    with the existing injected interfaces, and check B1, B2, B3, B6 and B8 (with the F4 fix) on each
    state and its successors. This is explicit-state model checking of the actual code and answers
    "watchdog and boot need more testing" at the implementation level.
  - *Watchdog gate:* simulate `TaskHealthRegistry` + `Watchdog` + `WatchdogRunner` over ms time with a
    stall at every phase, asserting W2 and W3 (952/1652 ms).
  - Needs native tests first (repo rule). Report these as native/host-level conformance checks, not
    hardware evidence.
- **A6. Readability (R3.3).** Enlarge Fig. 1 (drop `scale=0.84`, labels `\footnotesize`). Add a
  one-line gloss at first use for TCTL and its UPPAAL fragment, leads-to (`-->`), tightness twin,
  Pending/Confirmed, IWDG/LSI, confirmation anchor, falsification floor. Consider restoring one of the
  payload-link figures removed for space (`formal/figures/payload_link.svg`).
- **A7. Process.** Commit the F4 fix in `BootPolicy.hpp` and its regression test (still uncommitted;
  SUBMISSION_CHECKLIST item 3); the paper says "fixed in source". Then: de-anonymize (`\anonfalse`),
  rebuild, run `verify_manuscript.py`, IEEE PDF eXpress, refresh the hashes. Ask the chairs whether
  camera-ready allows a seventh page: the manuscript is already at 6 pages, and A1–A6 add text.

## Part B: hardware tests to run when the boards are back

Put each in a new exclusively named evidence directory with its own inventory. Never reuse a run name.

- **B1. Measure J on target (Reviewer 2's explicit request).** Toggle a GPIO at the poll send instant in
  `sendPoll()` (and optionally at the top of each `PayloadLinkTask` loop) in a scope-instrumented build.
  Capture with a logic analyzer or a scope that can export (the last scope attempt failed on export:
  bring a USB stick and check that ≥1 MSa/s CSV export works *before* the lab session). Record ≥ 10 min
  so it covers ≥ 120 status reports. Report the distribution of poll-to-poll period in MCU time, with
  status-report periods shown separately. This replaces the J assumption with a measured bound and
  confirms or refutes E1.
- **B2. Root-cause the status-report slip (E1).** Same instrumentation, plus edges around
  `reportStatus()` / `writeLine()`. Check whether the delay is the blocking console write, preemption,
  or something else. If fixable, a design fix (e.g. a non-blocking console write) can be re-verified
  with J = measured, like F4.
- **B3. Watchdog stall injection (Reviewer 3).** A test build with a define-gated command that stalls
  the payload-link task (and separately the heartbeat). Measure stall → `WATCHDOG_TIMEOUT` record →
  IWDG reset with a GPIO edge and the reset pin on the scope; compare with W3 (952/1652 ms) and W5/W6
  (+ IWDG max 2170 ms). Then confirm B6/F2: after the reset the bootloader enters the PA5 beacon and
  does not relaunch until a power cycle. About 10 trials per task is enough for consistency evidence.
- **B4. Boot-policy fault injection (Reviewer 3).** Using flash writes via OpenOCD between resets:
  (a) corrupt slot A's CRC → fallback to B; (b) corrupt both → safe-loop beacon (B4);
  (c) stage slot B as Pending and warm-reset repeatedly → launched at most 4 times, then refused (B3);
  (d) the F4 scenario: k warm resets of Confirmed A, then corrupt A with Pending B staged. On the
  pre-fix bootloader B gets 4 − k launches; on the fixed bootloader it gets 4. That gives hardware
  evidence for the defect and the fix. Read retained `BootMetadata` over SWD after each step.
- **B5. Re-measure the round-trip response time (E2).** GPIO edges at controller poll send and at
  controller frame acceptance give T_tx directly in MCU time, replacing the derived [3,4] ms.
- **B6. Re-run a small recovery campaign with MCU-side timing** (scope-build GPIO at confirmation
  receipt on the payload and at recovery on the controller), so recovery intervals no longer depend on
  host stamps. This is the direct test of whether anything like R085's 523 ms recurs and why.

## Rules reminder

Frozen trees (`runs/`, `provenance/`, `extension/evidence/`, `extension/analysis/`, `archive/`) stay
read-only. Firmware changes to protocol constants (500/100/3, frame, baud) are off limits; GPIO
instrumentation behind `ICSEC_SCOPE_INSTRUMENTATION` is fine. Any new number in `main.tex` needs a
retained output first.
