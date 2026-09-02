# Anonymity, provenance, and claim audit

Candidate status: `WORK_REVIEW_REQUIRED`

## Anonymity: PASS

- LaTeX author and PDF author fields are empty.
- No author name, affiliation, acknowledgment, identifying repository URL, local path, or organization-specific artifact link appears in the manuscript or PDF metadata.
- Hardware product and MCU identifiers are scientific setup details, not author identifiers.

## Provenance: PASS

- Scientific positioning is locked by `research/icsec2026/POSITIONING_LOCK.md`, SHA-256 `120B4C51966DEB4029E63EF32C9EC23C467D5540AD4B492D2517CA0A1CBE44EC`.
- Source evidence was read only. The manuscript references frozen evidence paths and does not copy empirical evidence.
- The 605-s nominal validation and BAD_CRC result hashes match the approved checkpoints.
- F411 Pair-1 and Pair-2 remain separate frozen datasets and are reported without pooling.
- The active candidate is maintained only at `research/icsec2026/submission/{main.tex,references.bib,main.pdf}`; build intermediates are ignored under `submission/build/`.

## Claims: PASS

- The Abstract, Introduction, Related Work, contributions, protocol, Discussion, and Conclusion use the same confirmation-gated methodological claim.
- OBS_C and OBS_P are described as separate same-host channels, not independent observations.
- The primary board-pair scope, 90-trial denominator, per-mode counts, and host-observed latency definitions are unchanged.
- The 605-s observation is separate from the primary trial denominator and from reliability claims.
- BAD_CRC mechanism text follows evaluated source control flow and ordered raw markers; it does not use `offline_before_restore`.
- F411 wording retains two separate 12-row pair datasets and makes no primary-pair replication, pooling, population, or MCU-equivalence claim.
- No controller-internal timing, environmental robustness, flight-qualification, mission-assurance, comparative, or complete-system inference is made.

Overall result: PASS; human scientific review remains required.
