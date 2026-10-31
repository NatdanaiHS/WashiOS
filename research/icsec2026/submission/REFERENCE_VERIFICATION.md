# Reference verification (formal-verification manuscript)

Date: 2026-09-08; extended 2026-09-21 for the advisor's major-revision list. Every entry in `references.bib` was resolved through the Crossref REST API
(`https://api.crossref.org/works/<DOI>`) for title, author list, venue, volume/issue/pages, and year. The
"reported" statements in Related Work were written from each paper's abstract, obtained from the sources
named below. Statements about what a paper does *not* report are phrased "not reported in the cited paper"
and refer to the abstract and, where fetched, the publisher landing page; they are not claims about the full
text beyond those sources.

| Key | DOI (Crossref resolved) | Abstract source | What the Related Work text attributes to it |
|---|---|---|---|
| alur1994 | 10.1016/0304-3975(94)90010-8 | classic; Crossref metadata only | theory of timed automata |
| larsen1997 | 10.1007/s100090050010 | Crossref metadata only | UPPAAL tool description |
| behrmann2004 | 10.1007/978-3-540-30080-9_7 | Crossref metadata only | UPPAAL tutorial |
| bengtsson2004 | 10.1007/978-3-540-27755-2_3 | Crossref metadata only | timed-automata semantics, algorithms, tools |
| clarke2018 | (book, no DOI) | publisher catalogue | model checking textbook |
| alencar2014 | 10.1007/s40313-013-0085-3 | Springer landing page | UPPAAL on ITASAT communication-module software; exposed requirement-completeness problems |
| luo2013 | 10.1109/COMPSACW.2013.56 | OpenAlex abstract | SpaceWire link interface as UPPAAL timed automata; CTL requirements; link initialization within scheduled time; disconnection-error timing |
| lin2024 | 10.1007/978-981-96-0617-7_12 | Springer landing page | FreeRTOS Cortex-M4 port model; model checking finds errors; assertion failures reproduced on STM32F429I-DISC1 |
| pan2014 | 10.1016/j.entcs.2014.12.004 | Semantic Scholar abstract | CAN arbitration/transmission/fault confinement in UPPAAL; 11 properties; violations from starvation and bus-off |
| johansson2020 | 10.1109/IECON43393.2020.9254494 | Semantic Scholar abstract; workflow claim verified 3-0 | heartbeat-based failure detection and role selection modelled and validated in UPPAAL |
| ahmed2018 | 10.1109/ICM.2018.8704088 | Semantic Scholar abstract; workflow claim verified 3-0 | AUTOSAR Watchdog Manager verified against specification by symbolic execution of C code |
| cook2020 | 10.1007/s10703-020-00344-2 | Crossref abstract | CBMC proof of memory safety of AWS initial boot code (journal version of the CAV 2018 paper) |
| vasudevan2024 | 10.23919/DATE58400.2024.10546576 | Semantic Scholar abstract; workflow claim verified 3-0 | UPPAAL analysis of Zynq-7000 secure-boot loader code; CVE exposed with four properties |
| yuan2021 | 10.1145/3487212.3487347 | Semantic Scholar abstract | RIOT bootloader (ARM IoT) functional correctness and memory safety in F*/Low* |
| larsen2005 | 10.1145/1086228.1086283 | OpenAlex abstract | UPPAAL-TRON online black-box conformance testing; industrial case study |
| waszniowski2009 | 10.1016/j.jss.2009.04.042 | Crossref metadata only (no abstract retrievable) | cited at title level only: a timed-automata case study of a distributed fault-tolerant system |
| gan2014 | 10.1016/j.scico.2013.03.005 | Crossref metadata only (no abstract retrievable) | cited at title level only: symbolic model checking of satellite onboard software |
| st2021ds12589 | (no DOI; vendor document DS12589 Rev 6, Oct 2021) | local copy of the datasheet PDF, Table 44 p. 105 and Table 79 p. 150 | LSI 29.5–34 kHz over VDD 1.62–3.6 V and −40..125 °C (31.04–32.96 kHz at 3.0 V, 30 °C); IWDG /16 reload 0xFFF max 2048 ms at 32 kHz; one LSI period phasing uncertainty |
| arlat1990 | 10.1109/32.44380 | carried over from archived paper (full-text verified there) | fault-injection methodology |
| martinez1999 | 10.1109/DCFTS.1999.814299 | carried over (full-text verified there) | physical fault injection validation |
| batista2019 | 10.1016/j.actaastro.2018.11.011 | carried over (full-text verified there) | nanosatellite communication-bus fault injection |
| singh2021 | 10.1145/3412841.3442053 | OpenAlex abstract | formal-methods-based conformance testing of a safety-critical ARINC 653 RTOS with UPPAAL |
| jensen2000 | 10.1007/3-540-45352-0_4 | Crossref metadata; full title from Semantic Scholar (no abstract retrievable) | cited at title level only: compositionality and abstraction for scaling UPPAAL |
| vogel2023 | 10.1016/j.infsof.2022.107100 | Semantic Scholar abstract | UPPAAL supports only a restricted, non-nested subset of TCTL; richer patterns need timed observer automata, which the catalogue provides |
| cho2025 | 10.1109/ACCESS.2025.3608215 | OpenAlex abstract | verified translation of UPPAAL timed automata into executable code combined with runtime monitoring |
| ge2018 | 10.1007/s10009-017-0475-0 | Crossref metadata only (no abstract retrievable) | cited at title level only: integrated formal verification of safety-critical software |
| pontes2014 | 10.1007/s10664-012-9215-y | Crossref metadata only (no abstract retrievable) | cited at title level only: model checking combined with the CoFI (conformance and fault injection) methodology for space embedded software |
| cutler2022 | 10.2514/1.I011025 | OpenAlex abstract | nanosatellite watchdog with separate clock and power domains; recovers restart-curable faults; deployed on several missions |
| asch2025 | 10.1109/LES.2024.3467332 | OpenAlex abstract | software-defined watchdogs as eager deadlines for delayed or missing signals |
| zilio2023 | 10.1016/j.robot.2022.104301 | Semantic Scholar abstract | formal model executed in place of the implementation with runtime verification and monitoring |

Notes:

- `alencar2014`: Crossref lists the online date as 2013 and the journal issue as vol. 25 no. 1 (2014); the
  print year is used.
- `lin2024`: the LNCS volume number was not returned by Crossref and is omitted rather than guessed.
- Removed from the bibliography on 2026-09-08 because no longer cited: `abboush2022`, `abboush2024`,
  `blanc2009`, `conceicao2025`, `hsueh1997`, `short2008`, `vanderkouwe2014` (all retained in the archived
  manuscript's bibliography).
- `waszniowski2009` and `gan2014` were added on 2026-09-08 after a review noted their absence. No abstract
  was retrievable from Crossref, OpenAlex, Semantic Scholar or the publisher pages during these sessions, so
  the Related Work text characterises them only at the level of their titles and attributes no specific
  finding to them. Their bibliographic metadata is Crossref-resolved.
- Candidates found by the literature search and still not cited, with reasons:
  Gluck and Holzmann 2002 (10.1109/AERO.2002.1036832, SPIN flight software) for the same reason; the
  TELFOR 2025 inter-satellite TDM paper (10.1109/TELFOR67910.2025.11314273) because its subject is a
  federated-learning testbed, not link supervision.
- 2026-09-21 (advisor major-revision list, five-layer Related Work): nine entries added, all Crossref-resolved
  on that date with the abstract sources given above. Print years follow the existing convention: `ge2018`
  (Crossref online 2017, print vol. 20 no. 4, 2018), `pontes2014` (online 2012, print vol. 19 no. 1, 2014),
  `vogel2023` and `zilio2023` (online 2022, print volumes 154 and 159, 2023); the advisor's list cites the
  online years. Where no abstract was retrievable (`jensen2000`, `ge2018`, `pontes2014`) the text attributes
  nothing beyond the title.
- Removed on 2026-09-21 because no longer cited after the restructure, to fund the layer-specific references
  inside the six-page limit: `clarke2018` (textbook), `waszniowski2009` and `gan2014` (title-level citations only),
  `bengtsson2004` (third UPPAAL tutorial), `martinez1999` (third fault-injection reference), `luo2013`,
  `yuan2021`. All remain in git history and in the archived manuscript's bibliography.
- Not added from the advisor's list, with reasons: entries without a resolvable identifier or venue
  ("Form Methods Syst Des DOI 10.1007/s10703-010-0103-z" with no authors, "Hakimipour 2011", "Xu, W., & D.
  (2021)", "Tao 2021", "Wu 2024"); and, for space, one representative per layer was kept (Yoon 2017, Zhang 2024,
  Larsen 1995, Foughali 2023, Kim 2025, McColl 2024, Cornejo 2022, Franca 2025, Kachman 2020, Tacchella 2026,
  Grobelna 2025, Silva 2016, Kartal 2016 all resolve on Crossref and can be added if a page is gained).

## 2026-09-22: DOI check of the advisor's "PAPER-FINAL-IEEE-APPROVED" reference list

The advisor's list attaches a DOI to every entry. Each was resolved through the Crossref REST API on
2026-09-22 and compared with the Crossref-resolved DOI already recorded above and in `references.bib`.

- Matching the bibliography (5): `alur1994`, `larsen1997`, `behrmann2004`, `arlat1990`, `zilio2023`.
- Not resolvable on Crossref (9): the DOIs given for `singh2021`, `vogel2023` (year 2023 in the suffix; the
  real article is `j.infsof.2022.107100`), `cho2025` (placeholder `ACCESS.2025.xxxxx`), `batista2019`,
  `pan2014`, `johansson2020`, `cutler2022`, `asch2025`, `vasudevan2024`.
- Resolving to a different, unrelated paper (8): `lin2024` (a vulnerability-detection GNN paper),
  `alencar2014` (power-quality classification), `jensen2000` (probabilistic hybrid automata), `ge2018`
  (parametric timed automata decidability), `larsen2005` (synchronous data-flow), `pontes2014` (a guest
  editorial), `ahmed2018` (a system-on-chip architecture), `cook2020` (hyperproperty monitoring).
- The datasheet (`st2021ds12589`) has no DOI; the advisor's list gives the vendor URL instead, which is
  the correct form for a vendor document.

Conclusion: the bibliography keeps the 22 Crossref-resolved DOIs recorded above (all 22 re-resolved to
the cited titles on 2026-09-22); none of the advisor's differing DOIs was adopted. `IEEEtran.bst` does
not typeset the `doi` field, so the DOIs are held in `references.bib` for the record; printing them as a
`note` adds about twelve lines to the reference list and pushes the paper to seven pages, so they are
not printed in the six-page submission build.

## 2026-09-23: full sweep of `references.bib` (owner: "it seems like some doi are wrong")

Three independent passes:

1. Crossref, field by field (title, author surnames, container, volume, issue, pages, print/online years) for all
   22 DOIs, plus a `doi.org` redirect check. Every DOI resolves (HTTP 302 to the publisher record) and every title
   matches the cited paper.
2. OpenAlex for all 22 DOIs: every record's title and first author match. Year differences reported by OpenAlex are
   online-first years (`alencar2014`, `ge2018`, `pontes2014`, `vogel2023`, `zilio2023`, `asch2025`, `batista2019`);
   the bibliography's convention is the print year.
3. Publisher pages, DBLP and author copies through the deep-research workflow (108 agents, 3-vote adversarial
   verification). Ten entries received 3-0 verified claims (`behrmann2004`, `singh2021`, `lin2024`, `jensen2000`,
   `vogel2023`, `cook2020`, `pan2014`, `johansson2020`, `vasudevan2024`, `larsen2005`); the other thirteen produced no
   surviving claim in that run and rest on passes 1 and 2.

**No wrong DOI was found.** Corrections applied to `references.bib`:

| Key | Change | Evidence |
|---|---|---|
| `cook2020` | year 2020 → 2021 (vol. 57 no. 1 is the July 2021 print issue; 2020 was online-first) | Crossref `journal-issue.published-print` 2021-07; Springer article page |
| `zilio2023` | author `Silvano {Dal Zilio}` so the surname renders "S. Dal Zilio", not "S. D. Zilio" | Elsevier record, OpenAlex |
| `lin2024` | added `volume = {15394}` (LNCS) | Springer chapter and book pages |
| `jensen2000` | added `volume = {1926}` (LNCS); subtitle kept (Springer page and DBLP show it; Crossref drops it) | Springer chapter page, DBLP conf/ftrtft/JensenLS00 |
| `behrmann2004`, `larsen1997` | tool name written "Uppaal" as in the published titles | Springer pages, Crossref |
| `johansson2020` | second author `R{\aa}gberger` as printed in the paper | author copy at es.mdu.se |

`larsen2005` keeps its subtitle "An industrial case study": ACM and Crossref store it as a subtitle field. Key names
(`cook2020`) are unchanged; they are identifiers, not metadata.
