# ICSEC 2026 current frozen candidate

Status: **FROZEN — WORK_REVIEW_REQUIRED**

- Branch: `paper/icsec-confirmation-gated-final`
- Freeze tag: `icsec-2026-confirmation-gated-final`
- Canonical manuscript: `submission/main.tex`
  - SHA-256: `FFAD88E14EE5E3976F77D4C12AE0865697313FDFC7AD14589A54833C596087EC`
- Canonical review PDF: `submission/main.pdf`
  - SHA-256: `7D0467D19CFB19792F73A98566712DBCF384D25BF501DC562A7BB5C6D0F9D2D4`
  - Five US-letter pages

The tag's commit is the authoritative repository snapshot. `submission/` is the only active
manuscript directory; Git history is the archive for earlier manuscript text.

## Use these files

- Submission PDF: `submission/main.pdf`
- Manuscript source: `submission/main.tex`
- Bibliography: `submission/references.bib`
- Final submission checks and hashes: `submission/`

- Scientific positioning authority: `POSITIONING_LOCK.md`
- Completed task record: `NEXT_TASK.md`
- Synthetic scorer validation: `synthetic_scorer_validation/`
- Reproducible candidate verifier: `paper/verify_candidate.py`

The synthetic directory contains exactly five derived mutations from BAD_CRC trial `R005_P02`,
their expected and actual scorer outputs, automated assertions, and source/derived hashes. These
are control-flow checks only and are excluded from all empirical denominators.

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

## Verify the frozen candidate

From the repository root:

```powershell
python research/icsec2026/paper/verify_candidate.py
python research/icsec2026/synthetic_scorer_validation/trace_replay.py
```

The candidate verifier checks empirical values and denominators, positioning, bibliography, PDF
text and page count, canonical-path hygiene, synthetic scorer assertions, and submission hashes.
The replay script writes only derived files inside `synthetic_scorer_validation/` and verifies that
the referenced empirical sources remain unchanged.

## Rebuild without overwriting the reviewed PDF prematurely

Write temporary LaTeX products only to the ignored `submission/build/` directory. Replace
`submission/main.pdf` only after page-count, textual, and rendered-page checks pass, then refresh
`FINAL_PDF_SHA256.txt` and `PACKAGE_SHA256SUMS.csv`.

After any future source change, verify the page count, bibliography, anonymity, rendered pages,
package inventory, and protected-file hashes before replacing the canonical PDF.
