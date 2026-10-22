# Next task: approve the formal-verification positioning, then verify the models

Status: `SCIENTIFIC_POSITIONING_APPROVED` (2026-09-08) — manuscript completion in progress
Opened: 2026-09-08 (Asia/Bangkok), branch `paper/icsec-formal-verification`

The confirmation-gated HIL manuscript (positioning approved 2026-09-03) was **not submitted**. The
Research Director decided to change the paper's scope to formal verification with model checking. The
old manuscript and its audits are archived byte-exact under
`archive/manuscripts/confirmation_gated_final_20260903/` (PDF SHA-256
`597A288326CEE460A40139CDF478E4BEF5F17F1574C089C976371A0170E195AF`). `submission/` now holds the new
draft.

## Decision record

`formal/POSITIONING_LOCK_FORMAL.md` was approved on 2026-09-08 (`formal/POSITIONING_LOCK_FORMAL_APPROVAL.md`).
Two additions were requested and executed: progress properties Q11/B9 (verified, 240 verdicts) and the
descriptive latency table in the conformance section. Venue: ICSEC 2026 final round, 6–25 September 2026.

## Work already done on this branch (no hardware touched, no frozen evidence changed)

- `formal/models/{payload_link,watchdog_gating,boot_policy}.xml` + `.q`: UPPAAL models and TCTL
  queries built from source constants and **verified with UPPAAL 5.0.0** on 2026-09-08:
  `formal/results/20260908T074838Z/`, 14 configurations, 240 verdicts, all equal to
  `formal/EXPECTED_VERDICTS.md` (`tooling/check_verdicts.py` 11/11). Verified inclusive bounds: first
  timeout 605 ms, OFFLINE 1609 ms, recovery 506 ms, stall detection 952/1652 ms, each tight.
  Findings: F1 (Pending never confirmed), F2 (fail-safe after stall), F3 (delay boundary 95/101 ms with an
  undetermined 96–100 ms band), F4 (fallback bypasses the unconfirmed-boot limit).
- `formal/MODEL_CODE_TRACE.md`: every constant and transition tied to a source line; assumptions A1–A6.
- `formal/conformance/check_frozen_traces.py`: replay of frozen evidence against the model alphabet and
  bounds. Executed: **0 issues** across 90 primary trials, both N0 windows, the 605 s nominal window,
  the 50–500 ms delay sweep, both BAD_CRC traces, and both F411 pair campaigns. Report and 6 passing
  unit tests retained under `formal/conformance/`.
- `submission/main.tex`: full draft with red `\pending{}` markers where verifyta output is required.
  `references.bib` extended with five formal-methods entries (to be verified).
- `submission/SUBMISSION_CHECKLIST.md`: replaced for the new paper.

## After approval, in order

1. (done) LSI tolerance sourced from DS12589 Rev 6; optional: decide whether to keep the unreachable
   `Payload.Responding` self-loop (see `formal/README.md`).
2. (mostly done) Related-work citations added and Crossref-verified 2026-09-08; self-citation omitted.
   Artifact statement and LSI citation closed 2026-09-08; no `\pending{}` markers remain.
3. Build into `submission/build/`, run page/anonymity/render QA, promote `main.pdf`, write the new
   hash records, tag the source.
4. (done) `paper/verify_candidate.py` retired; `formal/tooling/verify_manuscript.py` is the verifier.

## Stop / scope-down rules

- No new hardware acquisition is authorized by this task.
- No edit to `runs/`, `provenance/`, `extension/evidence/`, `extension/analysis/`, or `archive/`.
- No verdict enters any document without a retained `verifyta` output file.
- If the watchdog or boot models cannot be made to terminate under `verifyta` within reasonable
  bounds, drop that case study to future work rather than weakening properties silently; record the
  decision here.
