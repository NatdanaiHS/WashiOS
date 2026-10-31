# draft-camera-ready: re-modelled payload link (2026-10-18)

Working copy of `../formal/` for the ICSEC 2026 camera-ready revision (reviews in
`../submission/EMAIL_REVIEW.md`, plan in `../submission/CAMERA_READY_PLAN_20261018.md`). `../formal/`,
its retained results and the submitted manuscript are **unchanged**. Nothing here is yet cited by `main.tex`.

## What changed against `formal/`

| File | Change |
|---|---|
| `models/payload_link.xml` | A2 re-derived as a round trip from the poll stamp: `Payload` gains a `Decoding` location (mode read at decode, 2–9 ms), response 2–4 ms later, `HAL_Delay(d)` overrun 0–1 ms; `Controller` gains `Pickup` (frame consumed within L+J at the next loop pass). New assumption A7: optional `Status` template blocks the link task for ≤ `SLIP_MS` once per 5000 ms; controller actions are guarded by `!blocked` and its invariants extended by `slack`. New placeholders `SLIP_SELECT`, `STATUS_INSTANCE`. |
| `models/payload_link.q` | Comments only (bound values, placeholder list). Formulas unchanged. |
| `models/watchdog_gating.*`, `models/boot_policy.*` | Unchanged copies. |
| `tooling/run_verifyta.sh` | Writes to `draft-camera-ready/results/<stamp>/`. Payload configurations: SLIP 0 for silent, badcrc, d50/90/100/110/150/250, d100 at J ∈ {0,1,5}; SLIP 60 for silent, badcrc, d90/110/250. 21 configurations, 368 formulas. |
| `tooling/check_verdicts.py` | New oracle, **predicted before any run**; see `EXPECTED_VERDICTS.md`. |
| `EXPECTED_VERDICTS.md`, `MODEL_CODE_TRACE.md` | Payload section rewritten; A1 note, A2 and A7 entries; new constants with source lines. |
| `conformance/check_frozen_traces.py` (+ tests, 13 pass) | Draft bounds at SLIP 0 and 60; slip-aware delay predicates; 15.4 ms reattributed to the monotonic clock; measures status slip, host read residual and steady-state period from the raw 605 s nominal logs. Report: `conformance/results/conformance_report.json`. |
| `conformance/check_status_windows.py` (+ 4 tests) | Item 1: for every primary trial whose raw log is supplied from the backup, verifies the log against the frozen inventory and reports whether a `PAYLOAD_STATUS` report fell inside its detection and recovery windows. Not yet run: the raw logs are on the Windows lab PC. |
| `code_conformance/` | Item 2: the real firmware headers checked against the model's properties with plain `g++`. See `code_conformance/README.md`. Current run `results/20261018T075550Z/`: all pass. F4 is reproduced on the pre-fix code and absent after the fix. |
| `tooling/verify_manuscript.py` | Item 3: ported gate. Reads draft results, models, conformance and code-conformance runs. Takes `--tex` and `--max-pages`. Checks the SLIP 0/60 bounds, the 85/86/99/159 ms band edges, `599+2J`, the 368/21 counts, the new timebase and uncertainty numbers, and that 0.235 / 498.83 are gone. Numbers are matched as whole tokens against typeset text (TikZ and comments stripped). Against the submitted `main.tex` it reports 31 expected failures, the to-do list for the rewrite. |
| `tooling/draw_automata.py` | Unmodified copy; still draws from `formal/`. |
| `manuscript/main.tex`, `references.bib` | Item 4: camera-ready rewrite (copy; `submission/main.tex` untouched). `\anonfalse`. **6 pages**, 0 overfull, gate `tooling/verify_manuscript.py --tex manuscript/main.tex --max-pages 6`: 0 failures (5 expected warnings: merged verdict-table rows, which were checked by hand against the outputs; R085 pending; camera-ready mode). Contents: new bounds and band, round trip and status slip, corrected uncertainty and timebase, Code-level conformance subsection, updated F3/F4, replay at both bounds. Reviewer 3: TCTL forms, tightness twin, Pending/Confirmed, IWDG/LSI, committed locations, confirmation anchor and falsification floor defined at first use; Fig. 1 at full scale with larger labels. To fit: abstract, Related Work, F1–F4, Discussion and tables compressed, no result removed. Review-only wording sits behind `\ifanon` (prototype name, artifact sentence). The 7-page version is in the session scratchpad only. |

## Bounds (verified 2026-10-18, run 20261018T073529Z)

| | no status report in the window (SLIP 0) | any window (SLIP 60) | submitted |
|---|---:|---:|---:|
| first timeout after confirmed onset | 603 ms | 663 ms | 605 ms |
| OFFLINE | 1607 ms | 1667 ms | 1609 ms |
| ONLINE after confirmed restoration | 516 ms | 576 ms | 506 ms |
| delay accepted / timed out / band | ≤ 85 / ≥ 100 / 86–99 ms | ≤ 85 / ≥ 160 / 86–159 ms | ≤ 95 / ≥ 101 / 96–100 ms |

## Replay against frozen evidence (run 2026-10-18, read-only, 0 issues)

- Primary campaign, confirmation anchor: 179/180 within the SLIP-0 bounds; **180/180 within the bounds that
  hold in every window**. The exception is still R085_P02 (BAD_CRC recovery 522.8 ms): 6.8 ms over 516,
  inside 576. Whether a status report fell inside its window needs the raw log from the external backup.
- Delay sweep: 100 ms is now a decided timeout (hardware: timed out in every valid trial, CONFORMS); 90 ms
  moves into the band (hardware: accepted, consistent). F411 pairs: same verdicts, 0 issues.
- Raw 605 s nominal logs: status-report slip 10.0–54.5 ms (median 30.4, n = 241); control windows
  −15.4..9.4 ms; per-stamp host read residual p99 5.2 ms, max 8.6 ms; steady-state median period
  495.85 ms, so the MCU time base runs ≥ 0.84 % fast against the host (the submitted 0.235 % used a mean
  that includes the status slips).

## Status: verified 2026-10-18

Licence re-activated 2026-10-18. Run `results/20261018T073529Z/` (UPPAAL 5.0.0 rev. 714BA9DB, 21
configurations, 368 formulas, SHA-256 inventory in the directory). Against the pre-declared oracle, 19/21
matched on the first comparison. The two mismatches (Q4T in the d = 90 band, with and without the status
block) were a prediction error: the recovery bound holds but is not attained there (worst case 513 / 573 ms
against 516 / 576). The probe that shows this is in `results/20261018T073529Z_q4t_probe/`, and the
oracle correction is recorded with its reason in `tooling/check_verdicts.py` and `EXPECTED_VERDICTS.md`.
After the correction, 21/21 configurations match.

Every closed-form bound in the table above is confirmed by its tightness twin: it holds as a strict
inequality and fails with `>=`, so it is attained in the timeout-mode configurations. The watchdog and
boot verdicts are unchanged from `formal/`. Largest exploration: 73 520 states (`payload_delayed_90_status`,
max "States explored" over its formulas; this metric differs from the per-configuration state counts in the
submitted Table IV).

Re-run:

```bash
research/icsec2026/draft-camera-ready/tooling/run_verifyta.sh
python3 research/icsec2026/draft-camera-ready/tooling/check_verdicts.py
```
