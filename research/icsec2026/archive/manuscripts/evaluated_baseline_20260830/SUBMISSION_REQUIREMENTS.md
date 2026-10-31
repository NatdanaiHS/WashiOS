# ICSEC 2026 Submission Requirements

Accessed: 2026-08-30 (Asia/Bangkok)

## Official sources

- Submission guideline: <https://cpe.eng.kps.ku.ac.th/ICSEC2026/submission.php>
- Schedule / Important Dates: <https://cpe.eng.kps.ku.ac.th/ICSEC2026/schedule.php>
- IEEE conference templates linked by ICSEC: <https://www.ieee.org/conferences/publishing/templates.html>

## Requirements applied to Anonymous Submission Draft v1

| Requirement | Official basis | Draft action |
|---|---|---|
| English regular paper | Submission guideline, regular-paper section | Manuscript is in English. |
| 4–6 pages inclusive of figures, tables, appendices, etc. | Submission guideline | `main.pdf` must be 4–6 pages including references. |
| Standard IEEE two-column conference format | Submission guideline | `\documentclass[conference]{IEEEtran}`; no global font, margin, or spacing override. |
| Official IEEE conference template | Submission guideline | IEEEtran conference class supplied through the TeX bundle. |
| Double-anonymous review | Submission guideline | No author names, affiliations, acknowledgments, author-revealing URLs, company/project identity, or first-person self-citation. |
| Self-citations in third person | Submission guideline | No identified self-citation is present in v1; all related work is written in third person. |
| No author-revealing artifact URL | Submission guideline | The PDF describes the evidence package without a repository URL. |
| No author-revealing acknowledgment | Submission guideline | No acknowledgment section is present. |
| No IEEE spacing/font alterations | Submission guideline | Only standard section/table commands and local IEEE-compatible table font sizing are used. |
| Exclusive submission and IEEE authorship/plagiarism policies | Submission guideline | Procedural author responsibility; not mechanically verifiable from the draft. |

## Deadline interpretation

The current `Important Dates` block on the official schedule page lists **Second (Final) Round Paper Submission: 5 Aug – 5 Sep 2026**. Therefore the draft records **5 September 2026** as the final-round deadline.

The same page also contains an earlier `Conference Schedule` block listing **26 May – 2 July 2026** for a final round. This conflicts with the later `Important Dates` block. The 5 September date is used because it is the currently presented Important Dates schedule and matches the approved research decision. Authors should recheck the live site and EDAS before submission.

## PDF Express note

The page displays PDF eXpress preparation text, including a first-page copyright-notice instruction, while a nearby sentence stating that all submissions must be PDF is struck through. This v1 is an anonymous review draft and does not add a copyright notice without a confirmed review-stage requirement. PDF eXpress/copyright requirements should be rechecked at final upload or camera-ready preparation.

## Local compile implementation

- Engine: Tectonic 0.17.0
- Template class: IEEEtran conference class from the standard TeX bundle resolved by Tectonic
- Bibliography style: IEEEtran
- Build transcript: `build.log`
- Rendered QA pages: `qa/page-*.png`
- PDF structural metadata capture: `qa/pdfinfo.txt`
