# Rendered-page QA

- Build date: 2026-09-03 (Asia/Bangkok)
- Candidate: `main.pdf`, five US-letter pages, IEEE two-column conference layout
- Rendering: Poppler `pdftoppm`, PNG at 144 dpi, every page inspected after the final source change
- Page 1: anonymous title block, abstract, keywords, problem/gap/solution, locked contribution order, and closest-literature opening are legible; no clipping or collision.
- Page 2: TikZ Figure 1 is at the top and clearly shows topology, same-host OBS_C/OBS_P capture, six event classes, both scoring gates, and the literal invalid/unscored rule. Related-work close, system context, and stage-specific validity rules are legible.
- Page 3: the full-width gap matrix is readable, and the nominal and primary-outcome tables remain sharp and associated with their explanatory text.
- Page 4: latency and pair-separated F411 tables, discussion, validity boundaries, reproducibility, and conclusion are legible without collisions.
- Page 5: all seven emitted references are readable and balanced across the columns; no clipping, broken reference, or unreadable glyph is present.

Result: PASS. The final TeX log contains no overfull horizontal box, unresolved citation, or unresolved reference. Remaining underfull-box and font-substitution notices produce no visible defect.
