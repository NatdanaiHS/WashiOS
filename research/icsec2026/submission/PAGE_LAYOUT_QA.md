# Rendered-page QA

- Build date: 2026-09-03 (Asia/Bangkok)
- Candidate: `main.pdf`, four US-letter pages, IEEE two-column conference layout
- Rendering: Poppler `pdftoppm`, PNG at 144 dpi, every page inspected after the final source change
- Page 1: anonymous title block, abstract, keywords, problem/gap/solution, locked contribution order, and closest-literature opening are legible; no clipping or collision.
- Page 2: TikZ Figure 1 is at the top and clearly shows topology, same-host OBS_C/OBS_P capture, six event classes, both scoring gates, and the literal invalid/unscored rule. Related-work close, system context, validity predicates, and audit model are legible.
- Page 3: all four tables are sharp and readable; primary, nominal, BAD_CRC, and pair-separated F411 results remain visually associated with their explanatory text.
- Page 4: discussion, validity boundaries, reproducibility, conclusion, and five emitted references are legible; no clipping, collision, broken reference, or unreadable glyph.

Result: PASS. The final TeX log contains no overfull horizontal box, unresolved citation, or unresolved reference. Remaining underfull-box and font-substitution notices produce no visible defect.
