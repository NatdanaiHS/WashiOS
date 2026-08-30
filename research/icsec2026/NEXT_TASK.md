# Goal

Reproduce the selected supervision-boundary observations on the second physical controller G431-B using the same G474-A payload simulator, after the primary G431-A/G474-A scope-down package has passed work review.

# Why

The primary package is scientifically accepted: nominal, six-delay/NC, BAD_CRC, accounting, provenance, inventory, and backup gates pass. The highest-value remaining hardware task is a bounded second-controller check at 90, 100, and 110 ms. This can support only the statement that selected observations were reproduced on a second physical G431 controller using the same payload simulator; it is not an independent second board pair or a device-population estimate.

The primary sustained BAD_CRC field `offline_before_restore=false` is a non-blocking derived-field ambiguity and must not be cited. The accepted mechanism statement rests on the ordered raw markers and harness control flow that waited for `PAYLOAD_OFFLINE consecutive=3` before issuing restore. Do not modify the frozen primary package.

# Experimental Conditions

- Use G431-B as controller and the same G474-A as payload. Freshly enumerate and record both ST-LINK identities and host ports; do not infer G431-B identity from port number.
- Use controller firmware/configuration identical to the reviewed primary campaign where scientifically appropriate. Record G431-B application and bootloader binaries/hashes separately and retain the unchanged G474-A firmware hash.
- Store replication evidence in a new exclusive extension directory. Do not modify the frozen baseline or `primary_20260830_seed20260830_b5`.
- Precommit a seeded three-block plan before acquisition. Each block contains one NC and one trial at each of `90, 100, 110 ms`, for 12 observations total. Randomize within blocks while retaining exact identifiers and order.
- Use the same dual-channel exact-byte logging, exact delay/NC activation confirmations, 4 s observation window, restoration confirmation, and full pre/post stabilization gate as the primary campaign.
- Do not use routine per-trial resets and do not run 500 ms, BAD_CRC, G431-A reacquisition, oscilloscope, F411, or manuscript work in this milestone.

# Acceptance Criteria

- All 12 planned observations are retained with attributable raw logs, activation confirmation, validity status, confirmed `NORMAL` restoration, and passed post-stabilization; no failed or inconvenient row is deleted or replaced.
- The three NC observations quantify every false rejection/timeout/OFFLINE/recovery/restart/poll-write-failure marker.
- The three observations at each of 90, 100, and 110 ms report accepted response, timeout, sequence rejection, OFFLINE, restoration, and recovery descriptively. A reproduction claim is allowed only for outcomes actually observed on both controllers.
- Board identity, source commit/state, wiring, firmware/configuration hashes, seed/plan, raw logs, results, deviations, and measurement definitions are complete and internally consistent.
- Validation and inventory checks pass, the reviewed primary package and frozen baseline hashes remain unchanged, and the separate replication package is committed and backed up.

# Evidence Required

- G431-B/G474-A identity and port record, wiring/configuration record, source-state record, exact firmware binaries/hashes, and precommitted plan/seed
- Exact-byte plus readable G431-B and G474-A logs for every attempted NC and delay observation
- Per-observation results and stabilization records, descriptive cross-controller comparison, validation, deviations, and complete SHA-256 inventory
- Replication evidence commit, independent frozen-primary/baseline recheck, and verified backup record

# Stop / Scope-Down Rule

If remaining hardware access cannot accommodate all 12 observations plus a 20–30 minute evidence freeze, DROP this replication before acquisition rather than reduce it post hoc. If identity, serial integrity, activation, restoration, or stabilization fails, preserve the attempt and stop for review. Do not change payload scheduling, firmware semantics, or the condition set to rescue an unexpected outcome.
