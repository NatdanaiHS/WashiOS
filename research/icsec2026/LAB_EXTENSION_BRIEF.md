# ICSEC 2026 Lab Extension Brief

## Frozen boundary

- Source of truth: branch `experiment/icsec-extension-20260830` at `8a47d070c549274c59cdbde2495afa8d353a93b3`, also tagged `icsec-2026-evaluated-state`.
- The frozen 90-trial campaign, its N0 windows, provenance addendum, and manuscript are read-only. The frozen dataset and provenance inventory SHA-256 values are `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD` and `84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC`.
- Store all new material below a separate `research/icsec2026/extension/` evidence root. Every acquisition must identify its source commit, source-tree state, firmware binaries and SHA-256 values, configuration, board/probe identities, wiring, host/ports, seed/plan, raw dual-channel logs, validation, and evidence inventory.
- The existing `SESSION_STATE.md` describes the completed frozen campaign. Its historical branch/commit fields are not the acquisition identity for this extension.

## Inspected mechanism

The controller polls every 500 ms, applies a 100 ms response deadline, and enters `OFFLINE` after three consecutive response timeouts. A CRC-rejected frame increments the CRC-reject counter but does not clear the outstanding response or directly change link state. The pending exchange subsequently times out; repeated CRC-rejected exchanges can therefore accumulate three timeouts and produce `OFFLINE`. A valid response clears the timeout streak and returns/keeps the link `ONLINE`.

## Primary extension milestone: G431-A with G474-A

Use one activation-confirmed, dual-channel evidence package containing these three components:

1. **Extended nominal observation:** request 605 s and accept at least 600 s after payload-side `NORMAL` confirmation and a passed stabilization gate. Require at least 115 periodic controller status records, all `ONLINE`, strictly increasing successful-response counts, zero timeout/CRC/sequence/recovery counter deltas, and no rejection, timeout, offline, recovery, link-restart, or poll-write-failure marker. Interpret only this evaluated window; it is not long-duration, thermal, mission-reliability, or qualification evidence.
2. **Interleaved delay/NC campaign:** five randomized blocks. Each block contains one trial at each configured delay `50, 90, 100, 110, 150, 250, 500 ms` and two `NC` trials, for 35 delay trials and 10 Normal Controls. Constrain the recorded plan so NC trials are not adjacent and no more than four delay trials occur between NC trials. NC keeps the payload in `NORMAL` but otherwise uses the identical 4 s observation and evidence framework. Report per-delay accepted-response, timeout, sequence-rejection, offline, restoration, and recovery observations descriptively; for NC, report every false rejection/timeout/offline/recovery/restart marker. Do not treat sequential trials as independent devices and do not label NC as C0 or an ablation.
3. **Targeted BAD_CRC mechanism check:** retain one short exposure restored immediately after the first confirmed CRC rejection, followed by a passed stabilization gate, and one sustained exposure retained through `PAYLOAD_OFFLINE consecutive=3`, then restored and stabilized. The short exposure must show that a CRC rejection is not itself an immediate OFFLINE transition; the sustained exposure must link OFFLINE to the accumulated timeout streak. These are mechanistic checks, not a new statistical campaign.

Before every trial and before opening the nominal window, require a stabilization gate: a fresh payload-side `NORMAL` confirmation; a defined serial boundary that excludes or separately retains stale pre-gate host data; controller `ONLINE`; at least three subsequent successful exchanges; no increase in fault/recovery counters; and no unresolved transition marker. Do not reset either MCU per trial. On a failed gate, preserve the attempted trial and stop rather than deleting or replacing it.

Precommit the random seed and complete plan before acquisition. Delay activation evidence must confirm the exact requested delay, not merely `DELAYED`. All planned and attempted rows, including invalid or interrupted rows, remain in the evidence package.

## Follow-on priorities

| Decision | Scope |
| --- | --- |
| FIX NOW | Primary milestone readiness, exact-delay activation evidence, stabilization validation, NC handling, raw-log attribution, and the BAD_CRC mechanism check. |
| WORK AROUND | Treat all host-derived intervals as host-observed and use outcome transitions around the 100 ms configuration boundary; do not infer MCU execution latency. |
| SCOPE DOWN | If needed, reduce the primary campaign to three blocks (21 delay trials and 6 NC) while retaining all seven delay values, the 600 s nominal window, and both BAD_CRC exposures. After the primary package passes, replicate only three blocks of `NC, 90, 100, 110 ms` on G431-B using the same G474-A. |
| DROP | Drop G431-B replication if the primary evidence is not frozen; drop oscilloscope work unless primary and replication evidence are already safe; drop F411 work if it requires more than a brief bring-up assessment. |

G431-B is a second physical controller using the same payload simulator, not a second independent board pair. Record its identity and controller firmware hash separately and limit any claim to selected observations reproduced on a second G431 controller with the same G474-A.

Oscilloscope timing is optional and must be time-boxed. Only an endpoint-activation-to-controller-detection interval with explicitly defined GPIO endpoints is admissible. F411 is contingency-only; note whether an existing controller or responder can be brought up with minimal effort, but do not consume core acquisition time on a port.

## Evidence freeze

Reserve the final 20–30 minutes. Stop acquisition, return the payload to confirmed `NORMAL`, validate manifests/results against both raw channels, inventory every extension artifact with SHA-256, re-verify the frozen dataset/provenance inventory hashes, record deviations without removing trials, commit the extension evidence, and make the planned backup.
