# Goal

Complete and freeze the primary G431-A/G474-A lab-extension evidence package defined in `LAB_EXTENSION_BRIEF.md`: one at-least-600-s nominal window, one interleaved variable-delay/NC campaign, and the two-exposure BAD_CRC mechanism check.

# Why

This closes the highest-value evidence gaps: bounded nominal observation, false-marker controls under the trial framework, state isolation, behavior around the inspected 100 ms supervision deadline, and the actual accumulated-timeout path from CRC rejection to OFFLINE.

# Experimental Conditions

- Use G431-A as controller and G474-A as the payload simulator; record exact board/probe identities, wiring, source commit/state, configuration, firmware hashes, host/port mapping, and raw dual-channel serial evidence.
- Keep the frozen dataset, provenance, and manuscript unchanged; place all outputs under the separate extension evidence root.
- Nominal: request 605 s, accept at least 600 s, payload confirmed `NORMAL`, and stabilization gate passed before the window.
- Main campaign: five randomized blocks; each block has delays `50, 90, 100, 110, 150, 250, 500 ms` once and NC twice. Use a precommitted seed, nonadjacent NC placement, no gap longer than four delay trials between NC trials, and the same 4 s observation framework for every condition.
- BAD_CRC: one exposure restored immediately after the first confirmed CRC rejection and one exposure held through `PAYLOAD_OFFLINE consecutive=3`.
- Require the full stabilization gate before each observation; do not perform routine per-trial MCU resets.

# Acceptance Criteria

- The nominal window is at least 600 s with at least 115 status records, all `ONLINE`, strictly increasing successful-response counts, zero timeout/CRC/sequence/recovery deltas, and zero prohibited markers.
- Every delay and NC trial has exact payload-side condition confirmation, attributable raw logs, retained validity status, confirmed `NORMAL` restoration, and a passed post-trial stabilization gate.
- The campaign retains 5 observations per delay and 10 NC observations, with all false detector/offline/recovery/restart markers in NC quantified; no attempted or inconvenient trial is deleted or replaced.
- The short BAD_CRC exposure shows CRC rejection without immediate OFFLINE and returns to stable `ONLINE`; the sustained exposure shows OFFLINE only at the three-timeout accumulation and then confirmed restoration/recovery.
- Machine validation passes for plan/results/raw-log consistency, serial capture health, stabilization evidence, and measurement definitions. Claims remain descriptive and setup-bounded.
- The frozen dataset and provenance inventory hashes still equal `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD` and `84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC`.

# Evidence Required

- Exclusive extension directory with manifest, precommitted plan/seed, configuration, commands, source-state record, board identities, firmware binaries/hashes, and deviations
- Exact-byte plus readable raw logs from G431-A and G474-A for the nominal window and every attempted NC, delay, and BAD_CRC observation
- Per-observation results, stabilization records, nominal validation, campaign validation, BAD_CRC mechanism trace, descriptive summary, and SHA-256 inventory
- Final validation record, extension evidence commit, frozen-inventory recheck, and backup record

# Stop / Scope-Down Rule

If activation confirmation, serial integrity, or stabilization fails, preserve the attempt and stop; choose FIX NOW only for a bounded correction that does not threaten the freeze window. If time requires scope reduction, use three blocks while retaining the 600 s nominal window, all seven delay values, six NC trials, and both BAD_CRC exposures. Stop all acquisition with 20–30 minutes remaining for validation, hashes, commit, and backup; do not start G431-B, oscilloscope, F411, or manuscript work before this milestone is safe.
