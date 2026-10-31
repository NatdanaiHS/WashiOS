# Formal-Verification Positioning Lock

Status: `SCIENTIFIC_POSITIONING_APPROVED` (Research Director, 2026-09-08; see `POSITIONING_LOCK_FORMAL_APPROVAL.md`)
Drafted: 2026-09-08 (Asia/Bangkok)
Supersedes on approval: `research/icsec2026/POSITIONING_LOCK.md` (confirmation-gated HIL paper, approved 2026-09-03, never submitted)
Target venue: ICSEC 2026, Final Round Paper Submission 6–25 September 2026 (official `Important Dates` block, rechecked 2026-09-08). 4–6 pages, IEEE two-column, double-anonymous.

The previous manuscript reported host-observed HIL outcomes and explicitly could not claim controller-side timing. This lock replaces the empirical-report framing with a formal-verification framing: model checking of the supervision and boot logic with timed automata, using the already frozen HIL traces only as consistency evidence for the models.

# 1. Research gap

Small-satellite flight software commonly relies on poll/deadline supervision of payload links, task-health-gated hardware watchdogs, and CRC-validated A/B bootloaders. Published evaluations of such stacks (including our own prior HIL work) measure behavior on a bench and report host-observed latencies, which cannot establish worst-case detection, recovery, or fail-safe bounds, nor expose reachable-but-unexercised states. Formal verification with model checking is well established for protocols and RTOS kernels, but we did not find, in the closest work reviewed, a published treatment that (a) verifies the composed payload-link supervisor, task-health watchdog gate, and A/B boot policy of one concrete open flight-software prototype as timed automata, (b) traces every model transition to source lines, and (c) checks the models against byte-preserving hardware traces of the same firmware.

# 2. Proposed solution

Model the WashiOS payload-link supervisor, the task-health/IWDG watchdog gate, and the WashiBoot A/B boot policy as a network of UPPAAL timed automata whose constants are copied from the source (500 ms poll, 100 ms deadline, 3-timeout OFFLINE, 1 ms service loop, 800/1500 ms task deadlines, 100 ms watchdog poll, 2 s IWDG, 3 unconfirmed boot attempts). Verify safety, bounded-response, and liveness properties in TCTL with `verifyta`. Bound the model-to-implementation gap three ways: a transition-to-source-line trace table; replay of the frozen 90-trial campaign, both N0 windows, the 605 s nominal observation, the delay sweep (50–500 ms), the BAD_CRC mechanism traces, and the two F411 pair campaigns against the models' observable event alphabet and bounds; and model-derived scenarios turned into native Unity regression tests.

# 3. Bounded contributions in priority order

1. **Timed-automata models and verified properties** for three interacting safety mechanisms of an actual STM32 flight-software prototype: worst-case fault-onset-to-first-timeout (605 ms) and fault-onset-to-OFFLINE (1609 ms) bounds and a 506 ms recovery bound after restoration, each shown tight to the millisecond; no false OFFLINE under a lossless nominal channel; delay-acceptance boundary; CRC-reject-before-timeout ordering; stall-to-IWDG-reset bound and absence of spurious reset; boot policy never jumps to an unvalidated image, bounded unconfirmed boot loop, inevitability of the safe loop when no slot validates; deadlock freedom of every model with explicit progress properties (every poll resolved, controller always polls again, stall leads to reset, every reset runs the boot policy to completion).
2. **Design findings surfaced by the models** and confirmed in source: (i) the application never sets the boot-confirmation flag, so a `Pending` slot can never become `Confirmed` in flight and the A/B confirmation path is unreachable outside tests; (ii) after any critical task stall the system is fail-safe, not fail-operational: the IWDG reset leads the bootloader to refuse to relaunch the application until the retained fault log is cleared by a cold start; (iii) the effective delay-acceptance boundary is below the nominal 100 ms deadline by the frame serialization time: delays up to 95 ms are provably accepted, delays from 101 ms provably time out, and 96–100 ms is undetermined under the 2 ms jitter assumption, consistent with the observed 90 ms accepted / 100 ms rejected results; (iv) the unconfirmed-boot limit is evaluated on the active slot only, so a fallback into a Pending slot inherits the accumulated boot count and can be launched already over the limit, after which the next warm boot is refused.
3. **Model-to-hardware consistency evidence** reusing the frozen, hash-verified HIL datasets: every observed marker sequence is accepted by the model's observable alphabet, and the recorded intervals are compared at an anchor aligned with the model's clock start, with the residual uncertainty derived from the evidence itself rather than declared. 179 of 180 intervals fall inside the verified bounds and the single exception is reported as unresolved. No new hardware acquisition is required or performed.

# 4. This paper does NOT claim

- verification of the C++ implementation itself (models are hand-derived; the trace table and conformance replay bound, but do not close, the gap);
- correctness of FreeRTOS, the STM32 HAL, the UART driver, or the CRC implementation, which are abstracted as bounded-jitter or ideal components;
- timing under clock drift beyond the stated LSI tolerance assumption, or under ISR latency beyond the stated jitter bound;
- any reliability, availability, or device-population estimate derived from the frozen HIL data (those data serve only as consistency evidence);
- radiation, environmental, or electrical fault tolerance;
- flight qualification, mission assurance, or complete-system validation;
- novelty of timed automata, UPPAAL, or model-based verification of watchdogs and bootloaders in general.

# 5. Locked research questions

- **RQ1 — Payload-link supervision:** Under a lossless channel, what worst-case bounds does the design guarantee for fault-onset-to-first-timeout, fault-onset-to-OFFLINE, and restoration-to-recovery for SILENT, BAD_CRC, and DELAYED(d) payload behavior, and for which d is a delayed response accepted?
- **RQ2 — Watchdog gating and boot policy:** Does a critical task stall always lead to an IWDG reset within a bound with no refresh after detection, can a healthy system ever be reset spuriously, and does the boot policy guarantee that only a validated image is launched, that unconfirmed boot loops are bounded, and that a safe loop is reached when no image validates?
- **RQ3 — Consistency:** Are all frozen hardware marker sequences accepted by the models, and do all host-observed intervals fall within the verified bounds plus the declared host-overhead slack?

# 6. Verification and evidence plan

| Artifact | Path | Tool | Status |
|---|---|---|---|
| Payload-link model + queries | `formal/models/payload_link.xml`, `.q` | UPPAAL 5.0.0 `verifyta` | verified 2026-09-08: 10 configurations × 19 formulas, all verdicts equal the oracle |
| Watchdog-gating model + queries | `formal/models/watchdog_gating.xml`, `.q` | UPPAAL 5.0.0 `verifyta` | verified 2026-09-08: 2 × 11 formulas, all equal the oracle |
| Boot-policy model + queries | `formal/models/boot_policy.xml`, `.q` | UPPAAL 5.0.0 `verifyta` | verified 2026-09-08: 2 × 14 formulas, all equal the oracle |
| Expected-verdict oracle | `formal/EXPECTED_VERDICTS.md`, `formal/tooling/check_verdicts.py` | Python 3 | 11/14 configurations match, 240 verdicts |
| Model-to-source trace | `formal/MODEL_CODE_TRACE.md` | manual, line-numbered | drafted; F4 rows added |
| Conformance replay | `formal/conformance/check_frozen_traces.py` | Python 3 stdlib | run 2026-09-08: 0 issues, 179/180 intervals within bounds, 1 unresolved; 11/11 tests pass |
| Manuscript gate | `formal/tooling/verify_manuscript.py` | Python 3 | 0 failures, 0 warnings |
| Verification run records | `formal/results/20260908T074838Z/` | `formal/tooling/run_verifyta.sh` | retained; `SHA256SUMS.csv` SHA-256 `94A784D84C292E42280CD031218007F132504C83F2110A7D08019AC0F35CA15E` |

Every reported verdict in the manuscript must come from a retained `verifyta` output with its SHA-256 recorded in `formal/results/`. Every conformance number must come from the retained JSON report of `check_frozen_traces.py`. No verdict may be typed from analytical expectation.

# 7. Proposed title

**Timed-Automata Verification of Payload-Link Supervision, Watchdog Gating, and A/B Boot Policy in STM32 Flight Software**

(Terminology amended 2026-09-10 at the Research Director's request, in response to reviewer item REV-02: "conformance" replaced by "consistency" where it names contribution 3, RQ3, the non-claim and the outline heading, because offline replay of recorded traces cannot establish conformance in the testing sense. The claim is thereby narrowed, not widened; the evidence, the gap, the three contributions and the non-claims are otherwise unchanged. The `formal/conformance/` artifact path and the report's field names keep their original spelling.)

(Title amended 2026-09-08 at the Research Director's request: "prototype" dropped from the title, kept in the body; formalism named instead of "model checking". Gap, contributions, and non-claims unchanged.)

# 8. Six-page outline

1. **Problem and claim boundary.** Bench evaluation cannot give worst-case bounds or reach unexercised states; state the three mechanisms, the three RQs, the three contributions, and the non-claims.
2. **Related work and system.** Timed automata and UPPAAL; model checking of watchdogs, bootloaders, and communication supervision; prior HIL evaluation of this stack. Minimal description of the controller, watchdog gate, and boot policy with the source constants.
3. **Models.** Automata networks, abstractions (1 ms loop as jitter bound, frame serialization as a delay interval, FreeRTOS as bounded wakeup jitter, LSI tolerance), and the properties in TCTL.
4. **Verification results.** Verdicts, bounds, deadlock freedom and progress, state-space sizes, and the four design findings with their source references.
5. **Consistency with frozen hardware traces.** One paragraph on the confirmation-gated acquisition protocol (credited as method, not claimed as contribution); a descriptive table of host-observed medians, IQRs, and maxima per mode next to the verified bounds (no interval or reliability inference); alphabet acceptance and bound compliance for the primary campaign, N0 windows, 605 s observation, delay sweep, BAD_CRC traces, and F411 pairs; the 90/100 ms boundary.
6. **Discussion, threats to validity, reproducibility, conclusion.** Model-code gap, abstraction assumptions, what the models do not cover, artifact package.

# 9. Decision gate

Approved 2026-09-08 with two additions requested at approval: explicit progress properties (Q11, B9) and the descriptive latency table in the conformance section. Approval of this lock authorizes: creating the formal package, archiving the unsubmitted confirmation-gated manuscript, drafting the new manuscript, and running `verifyta` and the conformance replay. It does not authorize new hardware acquisition, edits to any frozen evidence path, or manuscript claims that are not backed by retained tool output.
