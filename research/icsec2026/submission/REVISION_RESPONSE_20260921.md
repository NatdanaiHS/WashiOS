# Response to the advisor's major-revision list (2026-09-21)

Inputs: `~/Downloads/Major Revision List.pdf` (21 pp., Consensus-generated review with six numbered revisions,
five literature layers and a reference list; `Major Revision List (1).pdf` is a byte-identical duplicate) and
`Major Revision List (2).pdf` (3 pp., Thai seven-row table with suggested text). The review was written against
the 2026-09-08 draft (`build/anon/main.tex`: "fourteen configurations / 240 formulas", "one attempt instead of
three"); items already resolved by the 2026-09-10 revision are marked as such. Build after this response:
`\anontrue` 6 pages, 0 overfull boxes; `\anonfalse` 6 pages, 0 overfull boxes; `verify_manuscript.py` 0 failures,
0 warnings.

| # | Advisor comment | Author action | Where |
|---|---|---|---|
| R1 | "At most 4 launches" vs "one attempt instead of three" is inconsistent; give an explicit trace or truth table of boot-count evolution across active and fallback slots | Inconsistency was fixed on 2026-09-10 (W2): both places say **four**. Added the explicit count trace: every launch increments the count, only confirmation resets it, the limit refuses a Pending active slot with count > 3; fresh Pending slot launched at counts 0–3 and refused at 4 (B3); after k warm resets of a Confirmed slot the fallback launches the Pending slot at count k unchecked and is refused after 4−k launches, one launch once k ≥ 3 (the regression test). Semantics verified in `BootPolicy.hpp` (`bootSlot` → `noteBootAttempt`), `BootMetadata.hpp` (`normalizeConfirmedBoot`, `resetBootAttempts`) and `boot_policy.xml`. | §IV-B F4 |
| R2 | Complete the Listing 1 evidence; define undeclared terms such as the watchdog model's task-side term | Listing 1 was replaced by the line-numbered model-to-source table on 2026-09-10 (Table II) and no author notes remain. The undefined term was the 50 ms `WD_TASK_MS` (WatchdogTask loop delay, `core/src/main.cpp:80`) used in W3's bound 800+100+50+J = 952: the system description now states that the watchdog task wakes every 50 ms and evaluates the registry once 100 ms have elapsed. | §III-A, Table III (W3) |
| R3 | Recast replay as consistency evidence only and align every claim to that standard | Done on 2026-09-10 (REV-02); re-checked: no "validation" language remains in a claim, §IV-C is titled consistency, contribution 3 states "can refute agreement; does not establish conformance". Abstract and Conclusion now use the advisor's wording "non-refuting trace consistency" and the advisor's closing sentence. **Open process item O7**: `POSITIONING_LOCK_FORMAL.md` §3/RQ3 still says "conformance"; needs Research Director sign-off, not a quiet edit. | Abstract, §I, §IV-C, §VI |
| R4 | Justify the RTOS→jitter abstraction; state which properties remain sound | Stated explicitly: Q1, Q7, Q8, W1, W2 and every boot property are written without J; every bounded-response and boundary bound is a closed form in J (Table III), so a larger measured jitter moves a bound without invalidating the proof; no value of J covers a scheduler-induced delay beyond it (blocking, priority inversion), which §V-A excludes from source inspection (no blocking primitives). Related Work now contrasts kernel-level verification (Singh 2021, Lin 2024) with application-level verification above an abstracted kernel. | §III-B, §II, §V-A |
| R5 | Threats: which requirements were directly expressible in UPPAAL's TCTL fragment, which needed observers, whether alternative encodings were cross-checked | New paragraph: fragment is invariants/reachability/leads-to without nesting; of the 44 formulas 34 are invariants, 4 reachability, 6 leads-to; bounded response is an invariant over a clock of the driver template started at the confirmation event (Host / stall injector), i.e. the driver plays the observer role (Vogel 2023); ordering uses Boolean flags; no alternative encoding cross-checked; a mis-stated phase predicate would pass both tightness twins. | §V-A "Property expressiveness" |
| R6 | Separate bug finding from assurance scope; say results hold for the abstracted model under stated assumptions, not radiation/HAL/full stack | Abstract now ends with the boundary sentence; §I names the fourth claim "Assurance limits"; Conclusion closes with the advisor's sentence (does not verify the deployed C++, the RTOS or the HAL). Scope table separates model guarantees from implementation evidence per mechanism. | Abstract, §I, Table I, §VI |
| L1–L5 | Compare across five layers: RTOS semantics, compositional scalability, property patterns, model-to-code, hybrid V&V; plus watchdog-architecture and dual-bank literature | Related Work restructured into exactly those five layers plus a same-mechanism paragraph. Added (Crossref-verified, abstracts logged in `REFERENCE_VERIFICATION.md`): Singh 2021, Jensen 2000, Vogel 2023, Ge 2018, Cho 2025, Pontes 2014, Cutler & Beningo 2022, Asch 2025, Zilio 2023. Watchdog paragraph now contrasts recovery-oriented architectures with the fail-safe gate (F2). Dual-bank update papers (Kachman 2020, Tacchella 2026) resolve on Crossref but were not added for space; listed as candidates. | §II |
| T1 | Compact per-mechanism table: source artifact, abstraction, property family, implementation evidence | Added as Table I (abstraction, implementation evidence; property families via the Q/W/B prefixes; source artifacts remain in Table II). | Table I |
| T2 | Say whether bounds are design-time envelopes or operational monitors | Stated: design-time envelopes; as inequalities over console-observable events they could run as monitors on the debug UART (Zilio 2023, Cho 2025), not done here. | §V-A |
| T3 | Rename "validation" language to "non-refutation consistency" | See R3; wording adopted in Abstract and Conclusion. | — |
| Thai table rows 1–7 | Suggested sentences for motivation, problem, gap, objective, method, results, conclusion | Adopted with two adjustments: the problem sentence is kept verbatim as requested; the gap sentence follows the approved lock ("in the closest work reviewed…") rather than asserting what formal verification "often" does; the results sentence says **four**, not the suggested "three", because the limit of 3 allows four launches (B3) and the 2026-09-10 fix established that number. | Abstract, §VI |

## Space accounting (six-page limit, review build)

Added: five-layer Related Work with nine references (+9 bib entries), scope table, F4 count trace, expressiveness
paragraph, soundness sentences, envelope sentence, longer abstract. Removed or shortened, none affecting a claim or
a gate-checked number: the delay-acceptance figure (old Fig. 3, earlier today) and the payload-template figure
(old Fig. 1; both templates are fully described in §III-B prose); seven uncited references; the contributions list
set inline; captions of Tables II–V; the consistency-method paragraph; F1, F3, F4, sensitivity, reproducibility
and acknowledgment wording; float and caption skips; boot-policy figure at 0.88 scale.

## Not changed, deliberately

- Every count, state-space size, bound, conformance row and property identifier the gate checks.
- Table V (descriptive latency table requested by the Research Director at approval).
- `POSITIONING_LOCK_FORMAL.md` (hash-approved). Its "conformance" wording (O7) and the new gap sentence in the
  abstract should be reconfirmed by the Research Director.
- The advisor's suggested "one attempt instead of three" (see Thai table, row 6).

## Over-claim sweep (2026-09-21, after the revision)

Regex sweep of the typeset branch for novelty/absence words, "verifies the firmware", "hardware confirms",
conformance/validation as our own verdict, guarantee/prove, reliability/population, host-vs-MCU timing and
no-reset claims. Findings and fixes: gap sentence in the abstract rewritten to the sanctioned form ("are not
reported in the cited papers"); "carefully abstracted" → "abstracted"; the two remaining uses of "conforming" as
our own verdict → "consistent"; "Q9 proves acceptance" → "Q9 proves, in the model, acceptance"; the
MCU-time/host-time distinction restored in §III-F; Related Work attributions for Lin 2024, Ge 2018 and
Pontes 2014 narrowed to what their abstracts or titles state; "the recognised limit" → "a recognised limit".
Left as is, deliberately: "no trial recorded a controller restart marker" (an observation, not a no-reset claim);
"defect … fixed in source" (the fix is in the working tree of `BootPolicy.hpp`, not yet committed or tagged —
see SUBMISSION_CHECKLIST item 3).
