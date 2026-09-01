# Anonymity, provenance, and claim audit

## Anonymity: PASS

- LaTeX author and PDF author fields are empty.
- No author name, affiliation, acknowledgment, identifying repository URL, local path, or organization-specific artifact link appears in the manuscript or PDF metadata.
- Hardware product and MCU identifiers are scientific setup details, not author identifiers.

## Provenance: PASS

- `main`, `origin/main`, and `icsec-2026-evaluated-state` resolve to frozen commit `8a47d070c549274c59cdbde2495afa8d353a93b3`.
- The original submission-safe frozen PDF remains SHA-256 `992A1C9AA41F4295BF7F97CA081D79A7DE2ABBB4B419B2A0B82144C1B50928DF`.
- Source evidence was read only. The consolidated candidate is extension-branch output and does not replace frozen evidence.
- The 605-s nominal validation, BAD_CRC results, and primary final-manifest hashes match their recorded checkpoints.
- Pair-1 and Pair-2 remain separate frozen datasets and are projected from the verified cross-pair synthesis package without pooling.

## Claims: PASS

- Primary board-pair scope, denominator, mode counts, latency definitions, and frozen numbers are unchanged.
- The 605-s observation is explicitly separate from the primary N0 windows, trial denominator, and reliability claims.
- BAD_CRC explanation uses evaluated source control flow and ordered raw markers; it does not use the known-limited `offline_before_restore` derived field.
- F411 wording says two physical pairs under one fixed configuration and retains separate denominators.
- Scope evidence is excluded from timing claims.
- No device-population, independence, MCU-equivalence, internal-timing, environmental, or mission-assurance inference is made.

Overall result: PASS.
