# Scientific Review Revision v2 — Anonymity, Claim, Citation, and PDF Audit

Audit date: 2026-08-30 (Asia/Bangkok)

Overall status: **PASS**

## Deliverable and format audit

| Check | Result | Evidence |
|---|---|---|
| Compiled PDF | PASS | `research/icsec2026/manuscript/main.pdf` |
| Page limit and geometry | PASS | 4 letter-size pages (612 × 792 pt), including references |
| IEEE format | PASS | `IEEEtran` conference class, two columns, no global spacing or margin override |
| Build diagnostics | PASS | No overfull box, undefined citation/reference, fatal error, emergency stop, or LaTeX error |
| Citation closure | PASS | Six cited keys exactly equal six bibliography entries; no unused entry |
| Visual integrity | PASS | All four final 144-dpi renders inspected; no overlap, clipping, broken float, unreadable label, or avoidable half-page whitespace |

The final log contains three underfull line-breaking notices. Visual inspection confirms that they do not create overflow, collision, missing content, or an unreadable line.

## Double-anonymity and PDF-structure audit

| Potential leak | Result | Detail |
|---|---|---|
| Author identity block | PASS | Empty `\author{}`; no names, affiliations, addresses, email, ORCID, or acknowledgment |
| Project/institution identity | PASS | No local project name or submitting institution in manuscript text |
| Author-revealing artifact location | PASS | No repository URL or local path in PDF |
| First-person self-citation | PASS | None identified; all related work is discussed in third person |
| PDF author metadata | PASS | `/Author` absent |
| Local username/path | PASS | Extracted-text scan found no `WashiOS`, `wachi`, drive path, or local username |
| External URI annotation | PASS | None; 21 annotations are internal document links |
| Embedded attachment | PASS | None |

The PDF uses embedded TeX Gyre Termes regular/bold/italic/bold-italic document fonts and embedded mathematical symbol fonts. Its metadata contains only title, keywords, creator, producer, and creation date.

## Statistical and quantitative claim audit

| Claim group | Frozen evidence | Result |
|---|---|---|
| Two 65-s N0 windows and Table II | `paper/tables/n0_controls.csv`, SHA-256 `E02BC3729FBF0CE26C4395938712E3A9E2C6FAE6DC796DDC69E677A719005B03` | PASS |
| 90 valid trials, 30/30 per-mode outcomes, Table III | `paper/tables/fault_outcomes.csv`, SHA-256 `C3773C171029F56CAAA1669D7537A40CCE4B71973A2A7CE04FAEEB6DD49EEF98` | PASS |
| Six host-observed latency rows, Table IV | `paper/tables/latency_summary.csv`, SHA-256 `AA177409EF7D91064EE32EF1DEE6F60DA77AAA4E5E52714E4B93B8AA297486C6` | PASS |
| Deterministic table projection | `paper/tables/TABLE_PROVENANCE.json`, SHA-256 `383315929940D0E32002E06DC3748573210EA5B2214D32AD5C9BF10BE9D81C7D` | PASS |

Clopper–Pearson language, interval values, and the bibliography entry were removed from the manuscript. The paper retains the observed 30/30 counts and proportion 1.0, explicitly identifies sequential observations on one board pair, and states that device-population uncertainty cannot be estimated from that setup. No post-hoc test or between-mode ranking was added.

## Claim-boundary audit

| Excluded claim | Result | Treatment |
|---|---|---|
| C0 comparison or superiority | PASS | N0 is labeled nominal, not comparative; no C0 experiment is claimed |
| Independent reliability/device population | PASS | Results remain setup-bounded; 30/30 is descriptive only |
| MCU-internal timing | PASS | Every latency quantity is labeled host-observed and includes serial/USB/host effects |
| Independent reset proof | PASS | Link-start absence is explicitly not reset proof |
| Heartbeat/watchdog health | PASS | Literal strings are explicitly excluded as independent measurements |
| Radiation/environmental robustness | PASS | Appears only as an untested limitation |
| Flight qualification/mission assurance | PASS | Explicitly unsupported |
| Broad integrated-system validation | PASS | Empirical boundary remains the payload link |

## Related-work verification

Six primary papers are cited and six bibliography entries are present. Metadata and the manuscript use were checked against publisher/primary records for IEEE DOI `10.1109/32.44380`, IEEE DOI `10.1109/EDCC.2015.14`, *Sensors* DOIs `10.3390/s22041360` and `10.3390/s24123733`, *Acta Astronautica* DOI `10.1016/j.actaastro.2018.11.011`, and *Journal of Aerospace Technology and Management* DOI `10.1590/jatm.v17.1379`.

The closest-work statement is bounded: prior nanosatellite work already establishes communication-bus fault injection and staged interoperability testing. The claimed distinction is the evaluated protocol construct—independent controller/payload host observations, explicit activation/restoration gates, and byte-preserving per-trial traces—not first-ever nanosatellite fault injection.

## Final hashes

- `main.tex`: `F3181650C86E43848041D1CC27DE08E4DE3E9F65A63F6A5A9F6A5711D3E2EA98`
- `references.bib`: `952AC1A9B2BDA81A57F001442DE955051F650BB84DB135E1EC1D608198E18A10`
- `main.pdf`: `992A1C9AA41F4295BF7F97CA081D79A7DE2ABBB4B419B2A0B82144C1B50928DF`
- Frozen dataset inventory: `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD`
- Frozen provenance inventory: `84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC`

Independent final re-verification resolved all workspace-relative inventory paths and found zero missing files, size mismatches, or SHA-256 mismatches across all 195 dataset rows and all 65 provenance rows.
