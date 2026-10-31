# Part B handoff: on-target tests and camera-ready rewrite (2026-11-01)

Branch `lab/hw-tests-B`. Camera-ready deadline 2026-11-05 (IEEE PDF eXpress). Reviews:
`../submission/EMAIL_REVIEW.md`; plan and earlier findings E1-E4: `../submission/CAMERA_READY_PLAN_20261018.md`.

## State

| Item | Status |
|---|---|
| B1-B6 on hardware | done, evidence in `runs/` (9 closed runs, each with `INVENTORY.sha256`) |
| Retained-RAM defect F5 | found on hardware, fixed in commit `96a78a2`, re-verified (B3, B4) |
| Manuscript | rewritten: `../draft-camera-ready/manuscript/main.tex` (the authors' `washi.tex` was identical to it before the rewrite); `references.bib` unchanged |
| Manuscript gate | `verify_manuscript.py`: 0 failures, 5 warnings (merged verdict-table rows, R085 status-window check, camera-ready mode). Now checks every Table V (`tab:hw`) row against the closed runs, including the post-F5 `shared-retained` runs, requires exactly one run per pattern, and fails on a missing, stale or over-long PDF (falls back to `pdfinfo` without `pypdf`) |
| **PDF** | built with `latexmk -xelatex` into `manuscript/build/`: **6 pages**, no overfull boxes. The first build ran to 7 pages; prose was tightened and table columns rebalanced, no result removed |
| Push | this branch on origin |

## Results (numbers as in the manuscript; sources in brackets)

- **B1, J:** poll period 500.03-500.57 ms (n=1319), 500.08-500.40 ms in the 132 periods containing a status report. J=2 ms holds with margin. [`runs/*B1B2B5*/analysis_B1_B2_B5.json`]
- **B2, E1:** the status write blocks the link task 9.67-9.84 ms but delays no poll by more than 0.40 ms. The host-observed slip comes from the campaign's serial reader (`read(64)`, 50 ms timeout): with that reader, intervals spanning a status report read 496.5-553.0 ms on the host and 498.1-501.2 ms on the MCU; stamp lag varies over 0-63.8 ms. [`analysis/injector_latency_B6.json`, `analysis/host_vs_mcu_B1.json`]
- **B5, round trip:** poll to accepted frame 6.01-8.02 ms (n=1320), **F411 payload**.
- **B6:** MCU-timed recovery 159.0-503.5 ms, first timeout 113.6-593.5 ms (n=15, F411 payload), within 516/603. R085's 522.8 ms host interval is attributed to reader lag.
- **B3 (pre-F5 layout):** stall to WATCHDOG_TIMEOUT 801.4-801.8 ms (link, n=24), 1091.9-1092.4 ms (heartbeat, n=23); IWDG reset follows; **the app was relaunched 47/47** (F5).
- **B3 (shared layout):** safe loop (PriorCriticalFault) 20/20, also after a further warm reset.
- **B4:** policy mode matches the model on both bootloaders; F4 pre-fix 3/2/1 launches for k=1/2/3, fixed 4/4/4. System mode matches only after the F5 fix.

## Deviations to keep stated (already in the manuscript)

- Payload board was an F411RE, not the G474 of the frozen campaign: affects B5 and B6 only.
- Stalls injected at one phase (10 s after boot).
- After the F5 fix, cold starts were emulated over SWD (retained signatures invalidated), not by removing power.
- Lab-only (not for the paper): the analyzer's CH5/CH6 leads were swapped in Setup A; runs record it as channel map `A_ch5ch6_swapped`.

## Reproduce / check

```bash
git config core.autocrlf false     # Windows: required, or older frozen evidence fails its hashes
python research/icsec2026/draft-camera-ready/tooling/verify_manuscript.py --tex research/icsec2026/draft-camera-ready/manuscript/main.tex --max-pages 6
cd research/icsec2026/lab-partB/runs && for d in */; do (cd "$d" && sha256sum -c --quiet <(awk '{print tolower($1)"  "$2}' INVENTORY.sha256) && echo "OK $d"); done
```

Lab procedure: `RUNBOOK.md`. Tools: `labtool.py` (runs, capture, analysis), `bootfault.py` (B4 over SWD;
`build-prefix` recreates the pre-F4-fix bootloader worktree outside the repo), `stallcheck.py` (B3 after F5),
`host_vs_mcu.py`, `injector_latency.py`.

## Open

1. ~~Build the PDF and fit the page limit~~ done 2026-11-01 (6 pages).
2. Final read of the manuscript by the authors.
3. IEEE PDF eXpress, copyright form, submission by 2026-11-05.
