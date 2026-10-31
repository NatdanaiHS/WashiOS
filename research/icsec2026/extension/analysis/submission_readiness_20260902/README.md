# ICSEC 2026 consolidated submission-readiness package

Status: `SUBMISSION_READY`

The five-page candidate at `research/icsec2026/extension/submission_candidate_20260902/main.pdf` passes the evidence-omission, source-trace, reference, requirements, claim-boundary, anonymity, provenance, deterministic-value, build, and rendered-page audits.

## Issue disposition

| Authorized issue | Disposition | Evidence |
|---|---|---|
| Stale whole-study one-pair statement | FIXED | Primary is one G431/G474 pair; extension is two F411 physical pairs under one configuration. |
| Cross-configuration headings | FIXED | Both headings now say two-pair F411. |
| Valid 605-s nominal observation omitted | FIXED | Added as a separate observation, never as a primary N0/trial or reliability estimate. |
| BAD_CRC to OFFLINE underexplained | FIXED | Added evaluated-source control flow and SHORT/SUSTAINED raw marker order. |
| References not reverified for final submission | VERIFIED | Six existing DOI records match Crossref; no new or AI-manuscript citation imported. |
| Venue/template/anonymity/page constraint | VERIFIED | Official ICSEC/IEEE sources; five pages; anonymous IEEE conference build. |

No frozen empirical number changed. Table II gained one row that is a direct deterministic projection of the hash-verified 605-s validation JSON. No figure required regeneration because no plotted datum or diagram semantics changed. Tables III--V retain the prior verified projections.

The first validator execution failed only during path resolution and is retained in `FAILED_VALIDATOR_ATTEMPT.json`; it did not read or alter evidence. The corrected validator result is `FINAL_VALIDATION.json` with status `PASS`.
