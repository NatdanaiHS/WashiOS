# Goal

**SCOPE DOWN.** Complete and freeze the minimum valid G431-A/G474-A extension package using the passed `NOMINAL_002`, three blocks of the six serviceable delays `50, 90, 100, 110, 150, 250 ms` with interleaved NC, and the two-exposure BAD_CRC mechanism check. Preserve `R002_B1_D500` permanently as invalid evidence; do not retry, replace, delete, or include it in a valid-condition denominator.

# Why

At 500 ms, the current payload firmware blocks for one full controller poll period while answering a request, and its link service continues draining newly queued polls before returning to host-command service. The sent `NORMAL` command is therefore starved and never confirmed, so restoration and stabilization are not achievable under the required protocol. Fixing the scheduler would change payload behavior and firmware identity, requiring a fresh internally consistent campaign. Removing 500 ms retains below/near/above-boundary coverage through 250 ms and preserves the higher-value 100 ms boundary question without mixing firmware semantics.

# Experimental Conditions

- Keep the original plan, `R001_B1_D110`, `R002_B1_D500`, both R002 raw logs, and the existing results/partial inventory immutable. Their verified R002 log SHA-256 values are G431 `08022AE828B5AF1715BF9991FBCF8DF2B9D399263B90B64F131F2720D732EDF3` and G474 `3062DA9486CE630E4821D075464766DFDFE863576288C3C4469F7F6A1F7E130D`.
- Before resuming, create an append-only amended execution plan derived mechanically from the original order: retain blocks 1–3, omit only every unstarted 500 ms row, and do not reorder or renumber any retained row. Record the amended plan and its SHA-256 before acquisition.
- Count valid `R001_B1_D110` toward block 1. Retain invalid R002 in the attempt ledger but exclude it from all valid-condition summaries. Continue with the remaining original rows through block 3, skipping `R011_B2_D500` and `R021_B3_D500` as predeclared scope removals.
- Recover from the R002 starvation with one documented payload-only reset if required; this is an exceptional recovery action, not a per-trial reset. Do not reset G431-A. Reopen capture as needed, reconfirm the same board identities and unchanged firmware hashes, obtain fresh payload-side `NORMAL`, observe controller recovery/`ONLINE`, and pass the full stabilization gate before the next retained row.
- Use the unchanged 4 s observation framework. Each completed block contains one trial at `50, 90, 100, 110, 150, 250 ms` and two NC trials, preserving the original relative order and NC spacing.
- After three complete blocks, run BAD_CRC once with restoration immediately after the first confirmed CRC rejection and once held through `PAYLOAD_OFFLINE consecutive=3`, with confirmed restoration and stabilization after each.
- Do not change or rebuild firmware for this continuation. Do not alter the frozen dataset, provenance, or manuscript.

# Acceptance Criteria

- `NOMINAL_002` remains the accepted nominal observation: 605.0 s, 121 `ONLINE` status records, strictly increasing `ok`, zero timeout/CRC/sequence/recovery deltas, and no prohibited marker.
- Three complete amended blocks yield 3 valid observations at each of `50, 90, 100, 110, 150, 250 ms` and 6 valid NC observations. Every retained trial has exact activation confirmation, attributable raw logs, confirmed `NORMAL` restoration, and passed post-stabilization.
- All NC false rejection/timeout/offline/recovery/restart markers are quantified. Delay outcomes are reported descriptively as accepted response, timeout, sequence rejection, OFFLINE, restoration, and recovery observations; no device-population or MCU-latency inference is made.
- R002 remains visibly invalid with reason `NORMAL_RESTORE_NOT_CONFIRMED`; the final accounting distinguishes original-plan rows, attempted rows, valid rows, invalid rows, and rows removed by the scope decision.
- The short BAD_CRC exposure shows CRC rejection without immediate OFFLINE and returns to stable `ONLINE`; the sustained exposure reaches OFFLINE only at the three-timeout accumulation and then confirms restoration/recovery.
- Machine validation passes for amended-plan/results/raw-log consistency, serial health, stabilization, unchanged firmware attribution, and evidence hashes.
- The frozen dataset and provenance inventory hashes remain `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD` and `84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC`.

# Evidence Required

- Append-only decision/amendment record linking the original plan hash to the amended three-block, six-delay execution plan and stating why 500 ms was removed
- Preserved R002 result, both raw logs, verified hashes, starvation-cause record, and any exceptional payload-reset/recovery record
- Exact-byte plus readable dual-channel logs and stabilization evidence for every resumed, attempted, or completed observation
- Results ledger and descriptive summary that retain invalid/dropped rows without replacement and separate them from valid denominators
- BAD_CRC mechanism trace, final validation, complete extension SHA-256 inventory, extension evidence commit, frozen-inventory recheck, and backup record

# Stop / Scope-Down Rule

Do not fix the payload scheduler or reacquire R002 tonight. If the exceptional payload recovery cannot reach a clean stabilization gate, or if any retained condition at or below 250 ms cannot confirm restoration/stabilization, preserve the attempt and stop for review. Do not shorten below three complete blocks or omit either BAD_CRC exposure and still call the milestone complete. Stop acquisition with 20–30 minutes remaining for validation, hashes, commit, and backup; drop G431-B replication, oscilloscope, F411, and manuscript work for this session.
