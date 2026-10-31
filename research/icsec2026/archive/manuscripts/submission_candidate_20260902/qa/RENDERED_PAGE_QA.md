# Rendered-page QA

- Build date: 2026-09-02 (Asia/Bangkok)
- Candidate: `main.pdf`, five US-letter pages, IEEE two-column conference layout
- Rendering: Poppler `pdftoppm`, PNG, 144 dpi, every page inspected
- Page 1: anonymous title block, abstract, keywords, introduction, and related-work opening are legible; no clipping or collision.
- Page 2: protocol figure, related-work table, source-level BAD_CRC mechanism, and research questions are legible; no clipping or collision.
- Page 3: method, extended nominal method, two-pair F411 method, Table II, and RQ1 result are legible; no clipping or collision.
- Page 4: Tables III--V, BAD_CRC raw-order characterization, latency result, F411 pair-specific result, and limitations are legible; no clipping or collision.
- Page 5: remaining limitations, evidence lock, conclusion, and six references are legible; no clipping or collision.

Result: PASS. No overfull box remains. The remaining underfull-box notices are line-breaking diagnostics and produce no visible defect. Page 5 has intentional unused space after the short reference list; no content is missing.
