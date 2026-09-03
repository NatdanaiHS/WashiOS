# Rendered-page QA

- Build date: 2026-09-03 (Asia/Bangkok)
- Candidate: `main.pdf`, five US-letter pages, IEEE two-column conference layout
- Rendering: Poppler `pdftoppm`, PNG at 144 dpi, every page inspected after the final source change
- Page 1: anonymous title block, abstract, keywords, problem/gap/solution, one central methodological contribution, and the opening closest-literature comparison are legible; no clipping or collision.
- Page 2: TikZ Figure 1 clearly shows the host-orchestrated topology, unobstructed same-host OBS_C/OBS_P paths, six sequence nodes, both scoring-eligibility gates, and the two stage-specific unscored cases. Related Work and the opening protocol text remain legible.
- Page 3: the full-width gap matrix is readable. The trust-boundary clarification, scoring semantics, and observation/audit model remain sharp and associated with their explanatory text.
- Page 4: nominal, primary, latency, and pair-separated F411 tables are legible. Discussion and validity boundaries begin without collision.
- Page 5: the continuation of the validity boundaries, reproducibility, conclusion, and all seven emitted references are readable; no clipping, broken reference, or unreadable glyph is present.

Result: PASS. The final TeX log contains no overfull horizontal box, unresolved citation, or unresolved reference. Remaining underfull-box and font-substitution notices produce no visible defect.
