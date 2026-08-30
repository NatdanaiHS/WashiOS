# Evidence-Locked Paper Direction

## Scope decision

The paper is an evaluation of payload-link supervision using a reproducible hardware-in-the-loop (HIL) fault-injection method. The empirical unit is a sequential trial on one fixed NUCLEO-G431RB controller and NUCLEO-G474RE payload-simulator pair. Boot and runtime mechanisms may explain the architecture, but are not co-equal empirically validated contributions.

No additional hardware acquisition, campaign extension, C0 construction, or hypothesis testing is in scope. The frozen evidence is the two N0 windows, the 90-trial campaign, its validation and summary, and the completed provenance addendum.

## Locked research questions

- **RQ1 — Nominal windows:** What payload-link status and counter behavior was observed during the predefined pre- and post-campaign N0 windows?
- **RQ2 — Predefined outcomes:** For each injected mode (SILENT, BAD_CRC, DELAYED), in how many valid sequential trials were activation, the mode-specific detector marker, NORMAL restoration, and the recovery marker observed?
- **RQ3 — Host-observed timing:** What are the distributions of command-to-detector-marker and restore-command-to-recovery-marker latency for each injected mode, using host serial timestamps?

These questions are descriptive. They do not ask whether one design is superior to another, whether outcomes generalize to independent devices, or whether the measured intervals represent MCU-internal execution time.

## Contribution boundary

1. A reproducible dual-serial HIL procedure that confirms commanded payload behavior on the payload simulator before classifying controller observations.
2. An evidence-locked description of nominal-window behavior and predefined fault detection/recovery outcomes for one board pair under the frozen protocol.
3. A traceable artifact package connecting manuscript tables to hash-verified frozen summaries and connecting the evaluated firmware images to board readbacks.

The third contribution is reproducibility/provenance support. Byte-for-byte firmware agreement does not expand the empirical claims beyond the board pair and protocol that produced the dataset.

## Claim rules

- **Observed:** Directly represented in frozen logs, validation JSON, summary JSON, or exact binary-comparison reports.
- **Supported inference:** A bounded interpretation explicitly restricted to this board pair, firmware, wiring, host, observation windows, and timing definitions.
- **Unsupported:** Any statement requiring an unperformed comparison, independent-device replication, MCU clock measurement, reset instrumentation, environmental testing, or qualification evidence.

Use “observed proportion” rather than “reliability,” “command-to-detector-marker latency” rather than “detection time,” and “restore-command-to-recovery-marker latency” rather than “recovery time” unless the host-observed basis is stated in the same sentence or caption.

## Acceptance-risk screening

| Candidate framing | Risk | Disposition | Evidence-locked replacement |
|---|---:|---|---|
| “The proposed system outperforms a baseline.” | Critical | Remove | No fair C0 or comparative baseline was evaluated. |
| “Thirty independent experiments per fault.” | Critical | Remove | Thirty sequential repeated trials per fault on one board pair. |
| “100% reliable detection and recovery.” | Critical | Remove | Detection and recovery markers were each observed in 30/30 valid trials per mode; exact 95% CI [0.884296692, 1.0]. |
| “Sub-millisecond/millisecond MCU response.” | Critical | Remove | Report host-observed command-to-marker distributions only. |
| “No controller resets occurred.” | High | Remove | No post-injection `PAYLOAD_LINK_START` marker was observed; marker absence is not reset proof. |
| “Watchdog and heartbeat remained healthy.” | High | Remove | Do not interpret literal status strings as independent measurements. |
| “Fault-tolerant under radiation/environmental stress.” | Critical | Remove | No environmental or radiation experiment was performed. |
| “Flight-qualified/flight-ready.” | Critical | Remove | Qualification is outside the evidence. |
| “Validated integrated spacecraft/avionics system.” | Critical | Remove | Scope is the payload-link HIL setup, not a broadly integrated system. |
| “The method is reproducible from the package.” | Moderate | Qualify | The package records the seeded protocol, raw logs, validation, table derivation, source state, toolchain, and exact evaluated binary linkage. Reproduction on other hardware remains untested. |

## Evidence registry

| ID | Frozen artifact | SHA-256 | Primary use |
|---|---|---|---|
| E-SUM | `research/icsec2026/runs/full_20260830_seed20260830_n30/summary.json` | `124554F98A93639B4C2C8C18A708DC14A1D5673823A4CD2F84DB0F563083E1CA` | Counts, exact intervals, latency summaries |
| E-VAL | `research/icsec2026/runs/full_20260830_seed20260830_n30/validation.json` | `D06426EE043D32B032FA3267E7A8DDAB0AD345FD1F69807E93E9F47507BA84EB` | Structural/raw-log validation |
| E-PRE | `research/icsec2026/runs/n0_pre_20260830_0205/validation.json` | `872BA8EFD5E8F3505C6DEC62AFCAAC59A892D1ED407DDE67E7256B631FBEAA12` | Pre-N0 results |
| E-POST | `research/icsec2026/runs/n0_post_20260830_0224/validation.json` | `B3EF1165183D2EEBB0049B11D006A602D2EE36AE5669BD8EA5E92BA091E095F1` | Post-N0 results |
| E-INV | `research/icsec2026/runs/full_20260830_seed20260830_n30/SHA256SUMS.csv` | `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD` | Frozen dataset inventory |
| E-PROV | `research/icsec2026/provenance/20260830_023830/PROVENANCE_SHA256SUMS.csv` | `84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC` | Provenance inventory |
| E-TABLE | `research/icsec2026/paper/tables/TABLE_PROVENANCE.json` | Generated outside frozen evidence | Table input/output hashes and derivation |

## Manuscript assembly rule

The method, results, and limitations sections may be assembled from the companion files in this directory. Quantitative tables must be imported from `tables/*.csv`; hand transcription is not authoritative. There was no existing manuscript template in `research/icsec2026`, so this milestone produces evidence-locked section artifacts only.
