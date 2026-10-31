# Rendered-page QA

- Build date: 2026-09-03 (Asia/Bangkok)
- Candidate: `main.pdf`, six US-letter pages, IEEE two-column conference layout
- Rendering: Poppler `pdftoppm`, PNG at 140 dpi, every page inspected after the final source change
- Page 1: anonymous title block, abstract, keywords, problem/gap/solution, one central methodological contribution, and the opening closest-literature comparison are legible; no clipping or collision.
- Page 2: TikZ Figure 1 clearly shows the host-orchestrated topology, unobstructed same-host OBS_C/OBS_P paths, six sequence nodes, both scoring-eligibility gates, and the two stage-specific unscored cases. The expanded thematic Related Work and opening protocol text remain legible.
- Page 3: the full-width selected-work matrix is readable. The complete-trial validity indicator is centered as Equation (1) with its number flush right; the stage-specific semantics and trust-boundary clarification remain sharp and associated with their explanatory text.
- Page 4: nominal, primary, latency, and pair-separated F411 tables are legible; no table content moved or overflowed unexpectedly.
- Page 5: validity boundaries, reproducibility, conclusion, the anonymous AI acknowledgment, and the beginning of References are readable without collision.
- Page 6: all ten emitted scientific references are readable in balanced columns; the remaining white space reflects the bibliography length and no clipped or orphaned content.

Result: PASS. The final TeX build contains no overfull horizontal box, unresolved citation, or unresolved reference. The remaining underfull-box warnings produce no visible defect.

## Addendum 2026-09-22 (formal-verification manuscript, acknowledgment addition and advisor revision)

- Change: acknowledgment gains a hardware/technical-support sentence behind `\ifanon` (name withheld in the
  review build, INSTED named in the camera-ready build); `\arraystretch` lowered from 0.95 to 0.92 because the
  extra sentence otherwise pushed references [22]–[23] onto a seventh page.
- Build: TeX Live 2026 `latexmk -xelatex`, 6 pages, 0 overfull boxes, 0 unresolved citations, 23 references.
- Rendering: Poppler `pdftoppm` at 72 dpi, all six pages inspected. Tables I–V remain legible after the
  row-spacing change; page 6 holds Discussion, Reproducibility, Conclusion, Acknowledgment and the full
  reference list in balanced columns with no clipping.
- Gate: `formal/tooling/verify_manuscript.py` 0 failures, 0 warnings (anonymous build).

Result: PASS.

Second build of 2026-09-22 (advisor's revision list): AI-use disclosure made explicit about what the tools were
not used for; spelling normalized to American English throughout (behavior, catalog, modeling, emphasize, analyzed, recognized, serialization) at the owner's request; one sentence on the uneven
empirical support across the three mechanisms added to Threats to validity; the Reproducibility paragraph
condensed by one clause to pay for it; the placeholder "City, Country" line removed from the six anonymous
author blocks to recover two lines on page 1. Still 6 pages, 0 overfull boxes, 0 unresolved citations, 23
references; page 6 re-rendered and inspected (Discussion, Reproducibility, Conclusion, Acknowledgment and
references intact, columns balanced). Gate: 0 failures, 0 warnings. Third build: the owner asked for the original two-row, six-block camera-ready author
layout, so the grouped block was reverted and six lines were recovered instead by five prose trims applied to
both builds (no claim or number changed; gate 0 failures). Review build: 6 pages, 0 overfull, pages 5-6
re-rendered and inspected. Named build (`build/main-camera*.tex`, `\anonfalse`, `\contribfalse`): 6 pages,
0 overfull, pages 1 and 6 rendered and inspected (two author rows aligned, KMUTNB block intact, references
complete).

## Addendum 2026-09-23 (A4 page size)

- Trigger: the submission portal rejected `main.pdf` with "The page size is US letter size (8.5 by 11
  inches) ... but only A4 size (210 x 297 mm) is allowed."
- Cause: `IEEEtran` defaults to `letterpaper`; the preamble passed no paper option. Fix: one option,
  `\documentclass[conference,a4paper]{IEEEtran}` (also applied to `build/main-camera*.tex`). IEEEtran keeps the
  same text block for both sizes, so only the margins move.
- Build: TeX Live 2026 `latexmk -xelatex`, page size 595.28 x 841.89 pt (A4), 6 pages, 0 overfull boxes.
  `pdftotext` output of the old and new PDF differs only in whitespace.
- Rendering: Poppler `pdftoppm`, first and last page inspected; title block, columns and balanced references
  unchanged. `FINAL_PDF_SHA256.txt` and `PACKAGE_SHA256SUMS.csv` refreshed for `main.pdf`, `main.tex` and this file.
- Gate: `formal/tooling/verify_manuscript.py` 0 failures (pypdf warning only).

Result: PASS.
