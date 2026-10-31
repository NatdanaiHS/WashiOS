# Scientific Review Revision v2

Review date: 2026-08-30 (Asia/Bangkok)

Overall status: **PASS — V2 CHECKPOINT COMPLETE**

## Statistical decision

The v1 Clopper–Pearson interval was removed from the abstract, method, results, tables, and bibliography. Sequential trials on one physical board pair do not supply the independent Bernoulli sampling model needed for an unconditional device-population interval. V2 therefore reports the frozen observations directly: 30/30 valid trials per mode contained the predefined detector marker and 30/30 contained the recovery marker after confirmed restoration, for an observed proportion of 1.0.

No interval, hypothesis test, mode ranking, or reliability estimate is reported. The manuscript states that population-level uncertainty cannot be estimated from the single board pair. The frozen source summary remains unchanged; its interval fields are simply outside the v2 manuscript claim set.

## Novelty and positioning decision

The title and contribution framing now center on **activation-confirmed dual-channel HIL fault injection**. The empirical construct distinguishes five events: request, payload-confirmed activation, controller detection, payload-confirmed restoration, and controller recovery. Evidence locking remains a reproducibility mechanism rather than the sole novelty claim.

Recent and directly adjacent primary work was added:

- Abboush, Knieke, and Rausch, 2024, real-time HIL/virtual fault testing for automotive software, DOI `10.3390/s24123733`.
- Batista *et al.*, 2019, nanosatellite communication-bus failure emulation in MIL/HIL, DOI `10.1016/j.actaastro.2018.11.011`.
- Conceição and Mattiello-Francisco, 2025, systematic CubeSat interoperability testing across modeled and physical stages, DOI `10.1590/jatm.v17.1379`.

The closest-work gap is stated conservatively. V2 does not claim to introduce nanosatellite bus fault injection. It claims and evaluates a specific observation/scoring protocol using independent host channels, explicit mode confirmations after injection and restoration, and byte-preserving per-trial traces.

## Construct-validity decision

Figure 1 separates host orchestration, controller observation (OBS C), payload observation (OBS P), the physical UART, and the accepted injection-to-recovery sequence. A new construct-validity subsection defines the intervention as confirmed endpoint behavior and the response as a predefined controller marker in the permitted phase.

The manuscript explicitly limits these constructs:

- endpoint silence, bad CRC, and delay are not treated as electrical, environmental, or radiation-fault equivalents;
- markers do not expose every controller internal transition;
- host timestamps include UART, USB, driver, operating-system, scheduling, and timestamping effects;
- fixed windows, seeded order, and separated raw channels improve within-setup traceability but do not create hardware replication.

## Evidence traceability

All reported quantitative values were checked against the frozen generated tables:

| Manuscript content | Frozen table | Rows | Result |
|---|---|---:|---|
| RQ1 / Table II | `n0_controls.csv` | 2 | Exact projection |
| RQ2 / Table III | `fault_outcomes.csv` | 3 | Exact projection excluding interval fields |
| RQ3 / Table IV | `latency_summary.csv` | 6 | Exact median, Q1, Q3, IQR, minimum, and maximum values |

The original campaign summary hash remains `124554F98A93639B4C2C8C18A708DC14A1D5673823A4CD2F84DB0F563083E1CA`. No experimental file, table source, test, trial classification, or statistical output was altered.

## Layout decision

- Figure 1 is a compact full-width figure at the top of page 2, before the system/method discussion it supports.
- The selected-related-work table appears with the related-work discussion.
- N0 and outcome tables appear on page 3 adjacent to RQ1/RQ2.
- The latency table appears at the top of page 4 immediately before the continuing RQ3/discussion text.
- Conclusion and references flow continuously in the right column of page 4; no full-width float interrupts them.
- The final four pages contain no clipping, collision, unreadable label, or avoidable half-page whitespace.

## Final scientific disposition

The v2 manuscript is scientifically bounded to the frozen one-pair campaign. It supports a reproducible empirical demonstration of activation-confirmed payload-link supervision under the three configured behaviors. It does not support C0 comparison, independent reliability, MCU-internal timing, reset proof, environmental/radiation robustness, flight qualification, mission assurance, or complete-system validation.

