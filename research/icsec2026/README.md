# ICSEC 2026 canonical entry points

## Use these files

- Submission PDF: `submission/main.pdf`
- Manuscript source: `submission/main.tex`
- Bibliography: `submission/references.bib`
- Final submission checks and hashes: `submission/`

`submission/` is the only active manuscript directory. The frozen submission PDF has SHA-256
`99E4180F4B172C1CC7BABFCF8BE92FCC5442B3868F7AAD1D32A13779849E765D`.

## Evidence and provenance

- Primary frozen campaigns: `runs/full_20260830_seed20260830_n30/`,
  `runs/n0_pre_20260830_0205/`, and `runs/n0_post_20260830_0224/`
- Reviewed extension evidence: `extension/evidence/`
- Reviewed extension analysis: `extension/analysis/`
- Primary provenance: `provenance/20260830_023830/`
- Pre-cleanup protected-file freeze and hashes: `cleanup_freeze_20260902/`
- Post-cleanup relocation and duplicate records: `cleanup/`

Empirical evidence, provenance packages, failed experiments, and external verified backups were
not deleted or content-modified during cleanup.

## Historical files

Old manuscript builds and candidates are under `archive/manuscripts/`. They are retained for
history and provenance only; do not submit or edit them. Manuscript snapshots inside
`extension/analysis/` are also immutable provenance snapshots, not active manuscript sources.

## Rebuild without overwriting the frozen PDF

Copy `submission/main.tex` and `submission/references.bib` to a temporary directory, then run
Tectonic there. Do not build in `submission/`, because `submission/main.pdf` is the frozen,
reviewed five-page file.

After any future source change, verify the page count, bibliography, anonymity, rendered pages,
package inventory, and protected-file hashes before replacing the canonical PDF.
