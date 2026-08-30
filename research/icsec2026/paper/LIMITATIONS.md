# Limitations

The evaluation is intentionally narrow and should be read as a payload-link HIL study, not as qualification or broad system validation.

1. **One physical board pair.** All data came from one NUCLEO-G431RB and one NUCLEO-G474RE with fixed firmware, wiring, and host configuration. Cross-device and manufacturing-variation generalization are unknown.
2. **Sequential repeated trials.** The 30 trials per mode were performed sequentially on the same setup. They are repeated measurements, not independent hardware replicates; the exact binomial intervals describe the observed trial outcomes under the analysis convention and are not device-reliability guarantees.
3. **Bounded nominal evidence.** N0 comprises two 65 s windows. Those windows do not establish continuous operation, long-duration stability, or behavior between/across sessions. Absolute counter levels differ because earlier activity preceded the windows; interpretation is restricted to within-window deltas.
4. **No fair C0 comparison.** N0 is a healthy nominal control, not an ablation. There is no evidence for comparative superiority, treatment effect, or improvement over C0.
5. **Host-observed timing only.** Latencies begin at host command-send timestamps and end at host-observed serial markers. They include UART, USB, driver, buffering, scheduling, and timestamping uncertainty. No MCU/host clock synchronization or internal instrumentation was used, so MCU-internal latency and real-time bounds are unknown.
6. **Marker-based outcomes.** Detection and recovery are defined by predefined controller log markers after payload-side command confirmation. Marker occurrence establishes the recorded protocol outcome, not every internal state transition. The absence of `PAYLOAD_LINK_START` is not independent proof that no MCU reset occurred.
7. **Literal health strings.** Any `heartbeat=OK` or `watchdog=OK` text is a literal status field, not an independently instrumented heartbeat or watchdog measurement.
8. **Configured fault models and windows.** SILENT, BAD_CRC, and a 250 ms DELAYED response are the only injected behaviors. Observation windows were 4 s for the fault phase and 3 s for recovery. Other delays, corruption patterns, intermittent faults, concurrency, loads, and recovery horizons were not evaluated.
9. **No environmental testing.** Temperature, vibration, electromagnetic stress, power transients, radiation, and other environmental exposures were not varied or measured.
10. **No qualification evidence.** The package contains no basis for flight qualification, flight readiness, mission assurance, or safety certification.
11. **Subsystem-level scope.** The empirical result concerns one payload communication link and its logged supervision behavior. It does not validate a complete spacecraft, avionics stack, or broadly integrated system.
12. **Descriptive statistics only.** No hypothesis tests, causal estimates, mode comparisons, survival analysis, or dependence model were prespecified or performed. Apparent differences among latency summaries must not be interpreted as statistically established ordering.
13. **Provenance is not performance generalization.** Byte-for-byte agreement between identified board-capture regions and the G431 application/bootloader and G474 application binaries strengthens artifact identity. It does not add trials, device diversity, environmental coverage, or operational qualification.

These limitations define the manuscript’s outer claim boundary. Statements that require evidence beyond this list are classified as Unsupported in `CLAIM_EVIDENCE_MATRIX.md`.
