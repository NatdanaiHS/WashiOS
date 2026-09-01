# Friday oscilloscope gap decision

Decision: **NO-GO** for a new quantitative 110 ms G431-B/G474-A oscilloscope campaign.

Native waveform export has not been proven. The retained `S001_D110` capture exists only in Hantek DSO4254C internal Wave(Binary) slot No.1, with a phone photo available as supporting evidence; no CSV/native waveform was transferred to the evidence computer. Its 12.50 kSa/s acquisition at the selected 20 ms/div window is feasibility-only and is not microsecond-resolution MCU execution timing. Therefore the mandatory pre-acquisition export gate fails, irrespective of remaining time, and no new acquisition is authorized.

Exact incremental value had the gate passed: a precommitted set of at least five machine-readable traces could have bounded the host-marker timing discussion with endpoint-edge-to-controller-marker observations at 110 ms. Because export proof is absent, that value cannot be obtained with provenance-complete data.

Friday fallback: if access remains and the oscilloscope still retains slot No.1, only a non-destructive export of the already retained S001 waveform may be attempted as feasibility support. Do not acquire a new trace, change F411 hardware, estimate an interval from the screen/photo, or treat S001 as quantitative timing evidence. Reserve at least 30 minutes after any export attempt for hashing, provenance, backup, and freeze.
