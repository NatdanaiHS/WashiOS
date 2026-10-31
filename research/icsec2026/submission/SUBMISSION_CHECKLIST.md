# ICSEC 2026 formal-verification candidate checklist

Status: **READY PENDING THREE HUMAN ACTIONS** (updated 2026-09-21)

Target: Final Round Paper Submission, 6–25 September 2026 (official `Important Dates` block, rechecked
2026-09-08; the older `Conference Schedule` block on the same page conflicts and **must be rechecked by a
human before upload**). 4–6 pages, IEEE two-column, double-anonymous, EDAS.

## Machine-verifiable state (all green as of 2026-09-21)

- [x] `formal/POSITIONING_LOCK_FORMAL.md` approved 2026-09-08, terminology amended and re-approved 2026-09-10, hashed (`A07F7DEB…`).
- [x] UPPAAL 5.0.0 installed and licensed; `formal/tooling/run_verifyta.sh` executed; retained run
      **`formal/results/20260910T072609Z/`** with `SHA256SUMS.csv`.
- [x] `formal/tooling/check_verdicts.py`: **15/15 configurations, 254 verdicts** equal the oracle.
- [x] F4 fixed in the firmware (`resetBootAttempts()` before `activateBootSlot()`,
      `BootPolicy.hpp`), covered by `test_fallback_into_pending_slot_resets_attempt_budget`
      (12/12 boot-policy tests pass; the new test fails without the fix), and re-verified as
      configuration `boot_f4fix`: B8 holds, all other boot properties unchanged, B8c vacuous.
- [x] Conformance table in §IV-C matches `formal/conformance/results/conformance_report.json`
      (0 issues; 179/180 within bounds at the confirmation anchor, 1 unresolved; clock disagreement
      15.38 ms derived from the evidence). 11/11 conformance unit tests pass.
- [x] All `\pending{}` markers closed and the draft macro removed.
- [x] Model-to-source traceability matrix added to the paper (Table I), pinned to the analysed
      revision; `formal/MODEL_CODE_TRACE.md` records the post-fix line numbers.
- [x] Related work: closely related citations resolved through Crossref with abstract-sourced
      "reported" statements; see `REFERENCE_VERIFICATION.md`.
- [x] **Advisor major-revision list applied 2026-09-21** (`REVISION_RESPONSE_20260921.md`): Related Work
      restructured along five verification layers (RTOS semantics, compositional scaling, property
      engineering, model-to-code assurance, hybrid V&V) plus the same-mechanism work, nine Crossref-verified
      references added and seven uncited ones removed; scope table per mechanism (Table I); explicit boot-count
      trace for F4; the 50 ms watchdog-task term defined; which results rest on the jitter abstraction stated;
      property-expressiveness threat and envelope-versus-monitor statement added; abstract and conclusion
      rewritten to the advisor's seven-row table. Space came from the abstract, old Fig. 1, captions and prose;
      no number, table row, property or bound changed and the gate re-verified all of them.
- [x] Self-citation omitted (firmware unreleased); prior campaign described as unpublished; OS name withheld.
- [x] **`\anontrue` is the committed default**, so the default build *is* the double-anonymous review
      artifact. `build/main.pdf` and `submission/main.pdf` are byte-identical.
- [x] Build: **6 pages, 0 overfull boxes**, all six pages rendered and visually inspected 2026-09-21.
- [x] Author blocks (2026-09-21): the review build now carries six **placeholder** blocks
      (`Anonymous Author 1`–`6`, 3+3 rows) instead of an empty `\author{}`, so reviewers see the
      true author count and title-block height. The camera-ready branch gained a second author
      (Natdanai Hirunsirikul, Computer Engineering, Chulalongkorn) and is also laid out 3+3.
      The placeholder block costs about half a column on page 1, which was paid for by removing
      the delay-acceptance figure (old Fig. 3, `fig:band`; its content is fully stated in the
      "Sensitivity to the jitter bound" paragraph), tightening float/caption spacing and
      `\arraystretch` to 0.95, and dropping two clauses in §V-A that Reproducibility already
      states. No claim, number, table or property was changed; the gate re-verified all of them.
- [x] Anonymity: no identity strings in extracted PDF text, no author in PDF metadata; fonts embedded;
      no links or attachments.
- [x] `formal/tooling/verify_manuscript.py`: **0 failures, 0 warnings** (positioning hash, results
      inventory, oracle, every quoted number, stale-count detection, conformance rows, property
      identifiers, bibliography, anonymity, PDF page count and metadata).
- [x] `FINAL_PDF_SHA256.txt`, `PACKAGE_SHA256SUMS.csv` and `SOURCE_COMMIT.txt` regenerated from the
      current build.
- [x] **Bibliography trap removed 2026-09-21.** A stale `build/references.bib` (2026-09-08, 14 of the
      23 entries) shadowed `submission/references.bib` for any build run *inside* `build/`, so the
      camera-ready variants silently rendered nine citations as `[?]`. The anonymous submission build
      was never affected because it is invoked from `submission/`. The stale copy is deleted and
      `build/main-camera*.tex` now cite `\bibliography{../references}`, so there is one source of
      truth. When rebuilding a variant, run `xelatex; bibtex; xelatex; xelatex` explicitly —
      `latexmk` caches an empty `.bbl` and will hide the fix. Check `[?]` count and reference count
      in any camera PDF before sending it anywhere.
- [x] `paper/verify_candidate.py` retired (early-exit guard).

## Still required before upload

_Item 1 closed 2026-09-10; kept below for the record._

- [x] ~~**1. Positioning-lock sign-off.**~~ **Done 2026-09-10.** Terminology amendment approved by the
      Research Director (repository owner) and classified administrative, on the same footing as the
      2026-09-08 contribution-3 refresh: the claim is narrowed, not widened, and the gap, the three
      contributions and the non-claims are otherwise unchanged, so no new `SCIENTIFIC_DECISION_REQUIRED`
      cycle was opened. Lock amended (contribution 3, RQ3, the non-claim, the outline heading; the
      `formal/conformance/` path and report field names keep their original spelling), dated amendment
      note added, and the approved hash refreshed to `A07F7DEB…` with `FABA6B49…` recorded as superseded.
- [ ] **2. AI-assistance disclosure.** The current Acknowledgment covers translation and grammar only.
      The previously approved wording (archived under `confirmation_gated_final_20260903/`) also
      covers drafting support, literature-search assistance and code/tooling assistance, which is a
      closer description of how this manuscript was produced. Authors must choose the wording that is
      accurate for this paper and confirm it satisfies the ICSEC/IEEE policy.
- [ ] **3. Tag the source commit** and record the tag name in `SOURCE_COMMIT.txt` (currently
      "NOT YET TAGGED"). The working tree also has uncommitted changes that must be committed first.
- [ ] **4. Human scientific review**, and a human recheck of the conflicting date blocks on the ICSEC
      site before upload.

## Camera-ready only (not needed for the review submission)

- [ ] Copyright-notice wording from the chairs or the official template; added without guessing.
      IEEEtran disables `\IEEEpubid` in `conference` mode, so `\IEEEoverridecommandlockouts` is
      required; `build/main-camera-pubid.tex` shows the working incantation with a placeholder.
- [x] **2026-09-22:** the camera-ready build (`\anonfalse`, six named author blocks in two rows, the original
      layout) fits **6 pages, 0 overfull boxes**. The six lines it had spilled were recovered by five prose trims
      that apply to both builds and change no claim or number: Related Work opener, one redundant sentence in
      III-F on confirmation gating, the monitoring sentence in Property expressiveness, the Reproducibility
      list, and the Conclusion's last sentence. With `\contribtrue` (author contributions, funding, conflicts)
      the named build is still about eight lines longer and would need a further trim or an extra-page allowance.
      Earlier record: the camera-ready build (`\anonfalse`, six named authors) also fits **6 pages, 0 overfull boxes**
      as of 2026-09-21, so no post-acceptance trim or extra-page allowance is needed. Two author-block
      changes bought the space: the redundant `Faculty of Engineering` line was dropped from all six
      blocks, and the KMUTNB department and university names carry explicit line breaks so that three
      blocks fit per row (without them IEEEtran rewraps the rows to 3+2+1 and the block grows taller).
      Verify with `sed 's/^\\anontrue$/\\anonfalse/'` on a copy; do not flip the committed default.
      **Do not cut Table IV** — the descriptive latency table was requested by the Research Director
      at approval. If a future edit overruns again, the cheapest candidates are prose in §V-A and the
      Fig. 1/Fig. 2 captions; Fig. 3 has already been spent.

## Build

`tectonic` is no longer installed and is no longer used. Build with TeX Live 2026:

```
cd research/icsec2026/submission && latexmk -xelatex -outdir=build main.tex
```

`verify_manuscript.py` reads `build/main.pdf`, so always build into `build/` before running the gate.
`pypdf` is required for the gate's PDF checks.

Do not upload or externally publish this candidate until every item above is checked.

## 2026-09-22 advisor revision (PAPER-FINAL-IEEE-APPROVED.md)

- [x] Spelling: source spell-checked (pyspellchecker over de-TeX'd body); only domain words flagged, no
      misspelling found. Spelling normalized to American English throughout at the owner's request
      (behaviour→behavior, catalogue→catalog, modelling→modeling, emphasise→emphasize, analysed→analyzed,
      recognised→recognized, serialisation→serialization); cited titles in `references.bib` are untouched.
- [x] AI-use disclosure reworded to state what the tools were not used for.
- [x] Acknowledgment of INSTED (camera-ready branch); withheld-name sentence in the review branch.
- [x] Author contributions, funding and conflict-of-interest statements added behind `\ifcontrib` (default off;
      the gate fails if it is on together with `\anontrue`).
- [x] Evidence-asymmetry point added to Threats to validity (one sentence; the advisor's paragraph-length
      version does not fit).
- [x] Reference DOIs: all 22 Crossref-resolved DOIs already in `references.bib` re-resolved on 2026-09-22; 17 of
      the advisor's 22 DOIs do not resolve or resolve to unrelated papers and were not adopted
      (REFERENCE_VERIFICATION.md). `IEEEtran.bst` does not print DOIs; printing them as notes costs ~12 lines
      and a seventh page, so they are not printed.
- [ ] Not added, for the reasons given: Section III-H (anchor timeline figure; III-F already states the anchors,
      and the figure's "14.8 ms granularity" and "5–20 ms" command-to-confirmation figures have no source in the
      conformance record — the recorded values are 15.4 ms max and 4.4 ms median disagreement); Table VI (jitter
      sensitivity: Table III already gives every bound as a closed form in J, and the advisor's table marks Q3,
      Q4 and W3 as J-independent although each contains J, and gives the band as [97, 100+J] against the
      verified 96 to 98+J); Table VII (F4 before/after: its code excerpts are not the repository's code and its
      "zero attempts" outcome contradicts the regression test's one attempt); Table VIII (audit trail: two of its
      four source anchors are wrong — the deadline constant is at PayloadLinkController.hpp:33, not :38, and no
      `BootConfirmed` enum exists at BootPolicy.hpp:16–20). Table II already carries the F-tags and Table III the
      properties. Any of these needs an equal cut elsewhere to stay within six pages.

## 2026-09-23 reference sweep

- [x] All 22 DOIs re-verified through Crossref, OpenAlex and publisher pages (deep-research workflow); none wrong.
      Metadata corrections: `cook2020` print year 2021, `zilio2023` surname "Dal Zilio", LNCS volumes for `lin2024`
      (15394) and `jensen2000` (1926), "Uppaal" capitalization in two titles, "Rågberger" diacritic. Details in
      REFERENCE_VERIFICATION.md. Rebuilt: review and both camera variants 6 pages, 0 overfull, gate 0 failures.
