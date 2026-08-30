# Goal

Attempt one time-boxed oscilloscope milestone on G431-B/G474-A: measure the hardware-observed interval from payload endpoint delayed-behavior start to the controller's first timeout-detection marker for the reproduced 110 ms condition.

# Why

The primary and second-controller packages are scientifically accepted, frozen, and independently backed up. Hardware timing is now the only approved stretch task with material scientific value: it can improve attribution beyond host serial timestamps. The admissible quantity is an endpoint-behavior-start-to-controller-timeout-marker interval, not MCU execution latency, command-to-detection latency, qualification evidence, or a general timing bound.

# Experimental Conditions

- Keep the frozen baseline, reviewed primary package, and reviewed G431-B replication package read-only. Use a new exclusive instrumented source commit, firmware set, and evidence directory.
- Use G431-B and the same G474-A. Record exact board identities, wiring, probe channels, ground reference, GPIO pins, voltage scale, probe attenuation, coupling, trigger, timebase, sample rate/memory depth, and oscilloscope identity/settings.
- Define one unambiguous G474 GPIO edge as the start of delayed endpoint behavior for a decoded poll, and one unambiguous G431 GPIO edge as the first controller timeout-detection event for that same supervision exchange. Marker code must not change the 100 ms deadline, 500 ms poll period, UART protocol, delay scheduling, or link state logic.
- Use delay 110 ms only. Require exact payload-side activation confirmation, dual-channel serial logs, confirmed `NORMAL` restoration, and full stabilization for every attempted capture.
- Acquire at least five valid, individually retained traces. Preserve every attempted trace; do not replace inconvenient measurements. Optional UART scope channels may be observed only if they do not delay or destabilize the two required GPIO channels.
- Human involvement is expected for safe probe placement, scope triggering, and saving native waveform/screenshot data. Codex may prepare instrumentation and evidence handling but must not infer measurements from a screen description alone.

# Acceptance Criteria

- At least five traces contain both predefined GPIO edges with sufficient resolution and an attributable same-exchange relationship; every trace links to exact firmware/configuration, scope settings, and serial activation/restoration/stabilization evidence.
- Per-trace endpoint-to-timeout intervals are extracted from preserved scope data and summarized descriptively with count, median, minimum, and maximum; resolution/uncertainty is stated from the actual acquisition settings.
- The result is labeled only as the hardware-observed G474 endpoint-behavior-start to G431 timeout-marker interval under this instrumented 110 ms setup.
- Instrumented firmware hashes, source state, raw scope exports/screenshots, serial logs, result table, deviations, validation, and SHA-256 inventory are complete. The separate package is committed and backed up, and all prior inventories reverify unchanged.

# Evidence Required

- Endpoint definitions and pin/channel map, oscilloscope identity/settings, wiring/probe record, source commit/state, exact instrumented firmware binaries/hashes, and measurement protocol
- Native scope waveform exports plus screenshots for every attempted capture, paired exact-byte G431-B/G474-A serial logs, activation/restoration confirmations, and stabilization records
- Per-trace timing ledger, descriptive summary, uncertainty/resolution note, validation, complete SHA-256 inventory, evidence commit, and verified backup
- Independent recheck of frozen dataset, provenance, primary-extension, and G431-B replication inventories

# Stop / Scope-Down Rule

Time-box instrumentation bring-up to 20 minutes. If two clean and scientifically interpretable GPIO edges cannot be produced within that time, or if fewer than 40 minutes remain before the required evidence freeze, DROP oscilloscope acquisition and preserve only a clearly labeled feasibility record. Do not change endpoint definitions after observing results, do not substitute host timestamps, and do not begin F411, manuscript, or additional fault work in this milestone.
