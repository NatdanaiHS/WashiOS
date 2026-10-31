# Formal verification package (model checking)

Status: `POSITIONING APPROVED 2026-09-08; MODELS VERIFIED (UPPAAL 5.0.0, 240 verdicts = oracle); conformance 0 issues`
Created: 2026-09-08 on branch `paper/icsec-formal-verification`

This directory holds the material for the re-scoped ICSEC 2026 paper: UPPAAL timed-automata models of
three WashiOS/WashiBoot safety mechanisms, their TCTL queries, a model-to-source trace, and a
conformance replay that checks the frozen hardware evidence against the models. It replaces the
confirmation-gated HIL evaluation paper as the active research direction; that manuscript is archived
under `../archive/manuscripts/confirmation_gated_final_20260903/` and was never submitted.

## Files

| Path | Purpose |
|---|---|
| `POSITIONING_LOCK_FORMAL.md` (+ `_APPROVAL.md`) | Approved research gap, contributions, non-claims, RQs, outline, with the approved hash. |
| `models/payload_link.xml` + `.q` | Controller / Payload / Host network; RQ1 properties Q0–Q10. |
| `models/watchdog_gating.xml` + `.q` | Two critical tasks, supervisor, IWDG, stall injector; RQ2 properties W1–W6. |
| `models/boot_policy.xml` + `.q` | A/B slot policy with retained metadata, resets, cold starts; RQ2 properties B1–B8. |
| `MODEL_CODE_TRACE.md` | Every constant and transition tied to a source line; abstraction assumptions A1–A6. |
| `conformance/check_frozen_traces.py` | Replays `results.csv`, N0 validations, the extension delay sweep, BAD_CRC traces, and F411 pairs against the model alphabet and bounds. Read-only; writes `conformance/results/`. |
| `conformance/test_check_frozen_traces.py` | Unit tests for the replay (run with `python3 -m unittest discover -s research/icsec2026/formal/conformance -p 'test_*.py'`). |
| `tooling/run_verifyta.sh` | Batch-verifies all model configurations into an exclusive `results/<stamp>/` with a SHA-256 inventory. |
| `tooling/INSTALL.md` | JDK + UPPAAL installation and licence notes. |
| `tooling/verify_manuscript.py` | Checks `submission/main.tex` against the approved lock hash, the retained results, the oracle, the conformance report, property-identifier definitions, and bibliography/anonymity rules. Replaces `paper/verify_candidate.py`. |
| `tooling/draw_automata.py`, `figures/*.{svg,png}` | Hand-laid-out drawings of the three automata networks for reading and slides; the XML files remain the verified artifacts. Every label is drawn on an opaque plate above the edges, so no line can strike through text, and the script exits non-zero listing any two labels whose plates intersect. |
| `EXPECTED_VERDICTS.md` | Per-configuration oracle explaining which formulas are meant to be NOT satisfied (tightness, scenario, findings). |
| `tooling/check_verdicts.py` | Compares a `results/<stamp>/` directory against the oracle; exit 0 only on a full match. |
| `results/20260908T074838Z/` | Retained `verifyta` outputs, instantiated models, `SUMMARY.txt`, `SHA256SUMS.csv`. |

## Verification status

`tooling/run_verifyta.sh` → `results/20260908T074838Z/` (UPPAAL 5.0.0 rev. 714BA9DB36F49691): 14 configurations,
240 formulas, every verdict equal to `EXPECTED_VERDICTS.md` (`tooling/check_verdicts.py` reports 11/11). Largest state space 12,547 symbolic states (`boot_design`).

Configurations include a jitter sensitivity sweep (`payload_delayed_100_j{0,1,5}`) whose expected verdicts
were derived analytically before the run and confirmed by it; see `EXPECTED_VERDICTS.md`. The conformance
replay compares intervals at the confirmation anchor, which matches the model's clock start, and quantifies
its residual uncertainty from the evidence rather than declaring a slack.

Remaining tasks before the manuscript is submittable:

2. `payload_link.xml`: the `Payload.Responding` self-loop on `poll?` is documented as unreachable under A5;
   confirm with an `E<>` query before deleting it or leaving it.
3. Approve `POSITIONING_LOCK_FORMAL.md`; then close the manuscript `\pending{}` items that are not verdicts
   (related-work citations, self-citation wording, artifact statement).

Closed on 2026-09-08: licence activated; element order in the `Host` template; clock reads moved out of
functions; location references removed from guards; instance renamed (`B = Boot()`); unbounded counters
replaced by saturating ones (UPPAAL ints are 16-bit); bounded-response queries made strict with tightness
twins; boundary predicates `ACCEPTS`/`TIMES_OUT` introduced; boot model instrumented for F4.

## Rules

- Frozen evidence under `../runs/`, `../provenance/`, `../extension/evidence/`, `../extension/analysis/`,
  and `../archive/` is read-only. This package only reads from it.
- No verification result is typed into any document without a retained `verifyta` output.
- Conformance numbers come only from `conformance/results/*.json` produced by the checker.
- Model constants must equal the source constants listed in `MODEL_CODE_TRACE.md`; if firmware changes,
  the trace table, the models, and the checker constants change together.
