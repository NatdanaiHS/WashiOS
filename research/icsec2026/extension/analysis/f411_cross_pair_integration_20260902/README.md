# F411 cross-pair integration package

This is the frozen review package for the 2026-09-02 analysis-only milestone. It contains the provenance-checked, pair-specific synthesis and the bounded manuscript-integration candidate. Pair-1 and Pair-2 remain separate datasets; no combined denominator, pooled statistic, confidence interval, or device-population inference is present.

## Contents

- `synthesis/`: separate pair and pair/condition machine-readable tables, human-readable synthesis, provenance map, reviewed figure, and Friday gap decision.
- `manuscript_candidate/`: candidate source, exact diff from the frozen manuscript source, compiled five-page PDF, build record, and rendered-page/anonymity/claim audits.
- `INTEGRATION_VALIDATION.json`: milestone acceptance checks and immutable-input verification.
- `INTEGRATION_SHA256SUMS.csv`: complete inventory of package files except the inventory itself.

The frozen manuscript remains outside this package and unchanged at SHA-256 `992A1C9AA41F4295BF7F97CA081D79A7DE2ABBB4B419B2A0B82144C1B50928DF`. The authoritative Pair-1 and Pair-2 evidence packages and their backups also remain outside this package and were only read and verified.
