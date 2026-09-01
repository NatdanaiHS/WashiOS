# Repository cleanup report

## Disposition

**ACTIVE PATH-ONLY CLEANUP - CANONICAL SUBMISSION ESTABLISHED**

The FINAL_PASS package is now the sole active manuscript package at
`research/icsec2026/submission/`. Five older manuscript trees were moved intact to
`research/icsec2026/archive/manuscripts/`. No file was deleted.

## Protected-byte result

- Pre-move verification: 906/906 protected repository rows matched size and SHA-256.
- Immutable freeze package: 7/7 rows matched.
- External verified backups: 472/472 rows matched and remained read-only.
- Relocations: 122 files, including 121 protected files; every post-move byte count and SHA-256
  equals its pre-move value.
- Deletions: 0.
- Canonical PDF SHA-256:
  `99E4180F4B172C1CC7BABFCF8BE92FCC5442B3868F7AAD1D32A13779849E765D`.

The active relocation map is `PATH_RELOCATION.csv`. Exact duplicates retained in archives or
immutable analysis snapshots are classified in `DUPLICATE_DISPOSITION.csv`.

## Manuscript verification

The canonical `submission/main.tex` was rebuilt in a temporary directory with Tectonic 0.17.0.
The build completed with bibliography resolution, no fatal error, and five letter-size pages.
All five rendered pages were visually checked with no clipping, overlap, or unreadable content.
The frozen tracked `submission/main.pdf` was not overwritten.

## Retained pre-existing bookkeeping conflict

`POST_CLEANUP_VALIDATION.json` reports four historical table-provenance hash mismatches: the
table generator plus `n0_controls.csv`, `fault_outcomes.csv`, and `latency_summary.csv`. Those
four current bytes are exactly the bytes recorded by the immutable pre-cleanup protected-file
manifest, so the conflict predates and is independent of this path-only cleanup. Neither the
historical `TABLE_PROVENANCE.json` nor the protected files were rewritten to hide the conflict.

## Canonical use

- Submit: `research/icsec2026/submission/main.pdf`
- Edit only if a later manuscript revision is authorized: `research/icsec2026/submission/main.tex`
- Historical manuscript material: `research/icsec2026/archive/manuscripts/`
- Empirical evidence and analysis: unchanged at their existing `runs/`, `extension/evidence/`,
  `extension/analysis/`, and `provenance/` paths.
