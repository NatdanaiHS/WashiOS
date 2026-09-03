# Requirements and reference audit

Accessed 2026-09-03 (Asia/Bangkok).

The official ICSEC 2026 submission page requires an original English full paper of 4--6 pages inclusive, the official IEEE two-column conference format, and double-anonymous review. The candidate uses `IEEEtran` conference format and omits names, affiliations, acknowledgments, identifying URLs, and PDF-author metadata.

Authoritative requirement sources:

- ICSEC 2026 submission instructions: https://cpe.eng.kps.ku.ac.th/ICSEC2026/submission.php
- IEEE conference templates: https://conferences.ieeeauthorcenter.ieee.org/write-your-paper/authoring-tools-and-templates/

All seven cited publications were checked bibliographically against DOI/Crossref records and publisher metadata. Title, author list, venue, year, volume/issue, pages or article number, and DOI agree with the retained entries. Comparison claims were then checked against the publication text described below.

| Key | Publication text checked | Claim retained in the manuscript |
|---|---|---|
| `arlat1990` | IEEE TSE paper, DOI `10.1109/32.44380`; complete 17-page author-hosted publication recovered through the 2023-11-13 Internet Archive snapshot of https://homepages.laas.fr/arlat/documents/89124/89124.pdf | FARM explicitly separates fault set `F`, functional-exercise/activation domain `A`, readouts `R`, and measures `M`. The paper does not report the endpoint-confirmation gates, five-event record, or byte/hash evidence compared in the matrix. |
| `martinez1999` | Complete 17-page supplied publication, `C:\Users\wachi\Downloads\Experimental_Validation_of_High-Speed_Fault-Tolera.pdf`, SHA-256 `FAD85382F6B5A9AA38A56D55C2C44F58DAC8785E8D49C5F404D2742EF2DD3D7F`; DOI `10.1109/DCFTS.1999.814299` | AFIT distinguishes Activated Injection from Effective Error; `MEE` is asserted only when the selected FTS pin is forced. Non-effective injections, glitches, and invalid sequences are removed before analysis, and detection latency is measured from Effective Error. A separately observed normal-restoration gate before recovery scoring, the exact five-event payload-link chain, and exact-byte/hash evidence are not reported in the paper. |
| `vanderkouwe2014` | Complete author-hosted IEEE HASE paper: https://www.cs.vu.nl/~ast/Publications/Papers/hase-2014.pdf | The input fault load is distinguished from the subset activated during execution as the output fault load. Payload-endpoint and restoration comparisons are marked not applicable because the study analyzes LLVM software-injection distortion and has no commandable payload endpoint or restoration phase. |
| `abboush2022` | Complete publisher PDF: https://www.mdpi.com/1424-8220/22/4/1360 | Programmatically configured real-time HIL signal faults, selected-signal recording, data logging, and fault deactivation followed by return to normal are reported. Separate endpoint confirmation as a detection/recovery scoring gate, the five-event chain, and byte-preserving/hash-frozen evidence are not reported in the paper. |
| `abboush2024` | Complete publisher PDF: https://www.mdpi.com/1424-8220/24/12/3733 | Automated HIL campaigns, configured type/location/time/duration, time-series recording, test reports, fault deactivation, and return to a safe state are reported. Separate endpoint confirmation as a detection/recovery scoring gate, the five-event chain, and byte-preserving/hash-frozen evidence are not reported in the paper. |
| `batista2019` | Complete 10-page supplied Elsevier publication, `C:\Users\wachi\Downloads\1-s2.0-S0094576518302297-main.pdf`, SHA-256 `57FB09A5C10770B3F4BA476DCA159BDCF038804847F0C28EF4A233B1D4BB584B`; DOI `10.1016/j.actaastro.2018.11.011`, PII `S0094576518302297` | FEM separates the WHERE/WHEN/WHAT/HOW fault script from execution, monitors both low interfaces, returns exchanged-message information, and reports transmitted/received values and delays. The detailed result tables are MIL demonstrations; the small HIL set was suspended after interface mismatches. Per-trial detector/recovery eligibility gates, the five-event scoring chain, and exact-byte/hash evidence are not reported in the paper. |
| `conceicao2025` | Complete journal PDF: https://jatm.com.br/jatm/article/download/1379/1044/6370 | The paper reports six MIL/SIL/HIL modules, test reuse, FEM bus-fault injection, a dependability worksheet/database, and test reports. It does not report separate endpoint confirmation as a detection/recovery scoring gate, the five-event chain, or byte-preserving/hash-frozen endpoint evidence. |

Matrix status rule:

- **Reported** means the cited publication explicitly describes the compared element.
- **Not reported in the cited paper** means only that the inspected publication does not describe the element. It is not an inference that the implementation or broader research line lacks it.
- **Not applicable** means the comparison presupposes an endpoint, restoration phase, or scoring object outside the cited study design. It is not a feature-absence claim.

The previously unavailable Martínez and Batista full texts were supplied and verified at the hashes above. `martinez1999` is restored with claims bounded to the full publication, and the Batista comparison no longer relies on abstract-level inference. The unused `piper2015` entry remains removed. No unverified citation remains in the emitted bibliography.
