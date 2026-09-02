# Next task: six-page confirmation-gated manuscript rewrite

Rewrite the canonical ICSEC 2026 manuscript as one consolidated task. The paper must tell the locked confirmation-gated experimental-protocol story while preserving the verified empirical record.

## Authority and immutable positioning

1. Read `research/icsec2026/POSITIONING_LOCK.md` and `research/icsec2026/POSITIONING_LOCK_APPROVAL.md` completely before editing.
2. Verify that `POSITIONING_LOCK.md` has SHA-256 `120B4C51966DEB4029E63EF32C9EC23C467D5540AD4B492D2517CA0A1CBE44EC`. Treat that version as the scientific-positioning authority.
3. All manuscript changes must remain consistent with the locked gap, solution, three bounded contributions, non-claims, evidence roles, title, and six-page story.
4. Do not change or broaden the research gap or contribution hierarchy. If such a change appears necessary, stop before editing it and report `SCIENTIFIC_DECISION_REQUIRED` with the exact conflict and supporting evidence.
5. Use conservative literature language: “among the closest published studies reviewed,” “we did not find,” and “not reported in the cited publication.” In all gap-matrix reasoning, `not reported` does not mean `does not exist`.
6. Prefer “separate payload-side observation/confirmation” over “independent confirmation.” OBS_C and OBS_P are separate observation channels collected on the same host; do not imply stronger host or statistical independence.

## Canonical base and write scope

- Rewrite from `research/icsec2026/submission/main.tex`, the current five-page evidence-safe manuscript. Its pre-rewrite SHA-256 is `AA018D5E677D8C6ECAE93DEB33C068B01AC6050B5B57D47F303166BB750007B4`.
- Use `research/icsec2026/submission/references.bib` as the canonical bibliography and compile the canonical output in place as `research/icsec2026/submission/main.pdf`. The pre-rewrite PDF SHA-256 is `99E4180F4B172C1CC7BABFCF8BE92FCC5442B3868F7AAD1D32A13779849E765D`.
- Do not use the eight-page AI-generated review draft, files under `research/icsec2026/archive/manuscripts/`, or manuscript snapshots under `research/icsec2026/extension/analysis/` as rewrite bases.
- Keep all manuscript work in the existing `research/icsec2026/submission/` tree. Do not create a duplicate manuscript tree, alternate final package, or numbered files such as `final_v2.pdf`.
- Do not alter frozen evidence, campaign records, raw traces, hashes, firmware history, or positioning-lock files. Do not authorize or run new hardware or new experiments.

## Scientific rewrite requirements

Use the locked title: **Confirmation-Gated HIL Fault-Injection Trials for Auditable Payload-Link Supervision**.

Rebuild the Title, Abstract, Introduction, Related Work, contribution hierarchy, methodology framing, Discussion, and Conclusion around this narrow methodological claim: an injection request is not activation evidence; controller detection becomes scoreable only after separate payload-side observation/confirmation of the injected endpoint condition; recovery becomes scoreable only after separate payload-side confirmation that the payload returned to NORMAL; requested, activated, detected, restored, and recovered remain distinguishable; and byte-preserving endpoint traces plus hash-verified frozen summaries support auditability.

WashiOS, the firmware, the G431/G474 boards, and the F411 boards are system and evaluation context only. Do not frame the paper as a WashiOS architecture contribution, a new CubeSat HIL framework, a new fault injector, or a reliability study. Do not claim “first,” “unique,” “no prior work,” “state-of-the-art,” “superior,” complete-system validation, flight qualification, population generality, MCU-family equivalence, or comparative advantage unless independently proven and separately approved.

State the three contributions in the locked priority order:

1. the confirmation-gated scoring protocol and distinct event classes;
2. the byte-preserving, hash-verified evidence workflow; and
3. the setup-bounded descriptive evaluation using the primary G431/G474 campaign, separate 605-s nominal observation, two BAD_CRC mechanism observations, and two separate F411 pair campaigns.

Formalization is permitted only where it materially clarifies trial validity or scoring semantics. A compact definition, predicate, or event-order relation is acceptable; decorative notation, theorem-like presentation without analytical value, and redundant algorithms are not. Make explicit that missing activation or restoration confirmation makes the affected trial invalid and unscored rather than a detector or recovery failure.

## Required Figure 1

Replace the existing Figure 1 with one legible TikZ figure that combines:

- the minimal topology: controller, payload endpoint, fault-injection control, separate OBS_C and OBS_P observation channels, and their same-host trace capture; and
- the event sequence: `requested -> confirmed activated -> detected -> restore request -> confirmed restored -> recovered`.

Show the two scoring gates directly: detection is scoreable only after confirmed activation, and recovery is scoreable only after confirmed restoration. Include the exact rule **“no confirmation => trial invalid/unscored.”** The figure must remain readable in the IEEE two-column format. Do not add redundant algorithm, timing, or state-machine figures merely to make the paper appear more technical.

## Related-work and gap verification

Rework Related Work around the closest verified publications in the positioning lock, including at least FARM/Arlat, Abboush HIL, Batista/FEM, and Conceição/SATS. AFIT and the injection-fidelity study may remain where they sharpen the comparison.

A compact gap matrix may replace the current adjacent-work table only if every cell is checked directly against the cited publication. Each “not reported” cell must say “not reported in the cited publication” or “not reported in the cited publications,” carry the supporting citation, and make no inference beyond that publication. Do not copy unverified assertions from the eight-page review draft. Keep the matrix only if it remains readable within the six-page limit and contributes more than equivalent prose.

## Evidence and Results constraints

Preserve every verified numerical result in the current evidence-safe manuscript unless direct repository evidence proves an error. If an error is found, do not silently reinterpret or replace it: identify the exact source, explain the minimal correction, verify all affected statements, and report the change. Do not create a new empirical claim.

Keep the empirical roles and denominators fixed:

- the primary G431/G474 campaign is one physical pair with 90 sequential trials, 30 per SILENT, BAD_CRC, and DELAYED mode;
- the 605-s nominal observation is separate and duration-bounded, not a reliability estimate or a primary fault-trial denominator;
- the SHORT and SUSTAINED BAD_CRC records are two mechanism observations, not additions to the 90-trial denominator; and
- the two F411 campaigns are separate 12-row pair-specific datasets and must not be pooled or presented as independent replication of the G431/G474 setup.

Retain existing factual Results, denominators, descriptive host-observed timing limits, and stated validity boundaries. Improve organization or wording only when the resulting statement remains traceable to frozen evidence. Do not infer controller-internal timing from host serial timestamps. Do not convert counts into reliability, population, environmental-robustness, or mission-assurance claims.

Use BAD_CRC state-machine or threshold material only after direct verification against the evaluated controller source and frozen ordered traces. At minimum, check the evaluated `core/src/app/PayloadLinkTask.hpp` Git blob `a76804eb567689588bc3b1459df9a9352ec0d4f4`, `research/icsec2026/extension/evidence/primary_20260830_seed20260830_b5/bad_crc_results.json`, and its four `raw/bad_crc/{SHORT,SUSTAINED}/{g431,g474}.log` files. Do not use the known-limited `offline_before_restore` derived field as evidence.

## Six-page structure

Fit the complete IEEE manuscript, including references, within six pages maximum:

1. Page 1: problem, scope boundary, gap, solution, and three contributions.
2. Page 2: closest literature, minimal system context, and the new topology/event-gating Figure 1.
3. Page 3: confirmation-gated protocol, validity/scoring semantics, observation model, and audit workflow.
4. Page 4: primary G431/G474 evidence, 605-s nominal observation, and bounded BAD_CRC characterization.
5. Page 5: pair-separated F411 extension, discussion, and threats/limitations.
6. Page 6: reproducibility, conclusion, and verified references.

This allocation may be adjusted for legibility, but the narrative order, contribution hierarchy, and six-page maximum are binding.

## Mandatory writing constraints

- Write in concise, natural academic English appropriate for an IEEE conference paper.
- Prefer short, direct sentences. Remove unnecessary introductory phrases, rhetorical flourishes, and repeated explanations.
- Each paragraph should make one clear point and advance the argument.
- Do not inflate significance. Use bounded verbs such as “shows,” “observes,” “supports,” “demonstrates,” and “reports” only when directly supported by evidence.
- Avoid AI-like phrases such as “it is important to note,” “it is worth mentioning,” “in today’s rapidly evolving,” “comprehensive,” “robust,” “novel,” “significant,” “crucial,” or “promising” unless technically necessary and supported.
- Do not restate the same limitation or contribution in multiple sections unless needed for interpretation.
- Preserve the terminology already established in `POSITIONING_LOCK.md`; do not invent new terminology for stylistic variety.
- Prefer concrete statements over abstract claims. State what was done, observed, or measured.
- Do not add filler transitions merely to improve flow.
- Keep the tone restrained and human-written, similar to a careful engineering researcher rather than promotional scientific prose.
- After rewriting, perform a prose-compression pass: remove every sentence that does not add technical information, reasoning, evidence, or necessary context.
- Preserve all verified facts and numerical results while shortening wording wherever possible.

## Artifact and anonymity rules

Do not claim that an anonymous artifact, repository, DOI, or review package exists unless an actual reviewer-accessible anonymous artifact has been created and verified. If none exists, use only supportable reproducibility language about retained traces, hashes, and frozen summaries. Do not upload or publish anything externally as part of this task.

## Completion checks

Before declaring the rewrite complete:

1. compile the canonical PDF successfully and confirm it is no more than six pages including references;
2. render and visually inspect every page for clipping, collisions, illegible table text, broken references, and Figure 1 readability;
3. verify every numerical statement against the frozen evidence and confirm that no denominator was pooled, expanded, or reinterpreted;
4. verify every gap-matrix cell directly against its cited publication and preserve the strict `not reported` rule;
5. confirm the Abstract, Introduction, Related Work, contributions, Methodology, Discussion, and Conclusion all express the same confirmation-gated story and non-claims;
6. confirm the manuscript uses “demonstrates” rather than claiming independent or comparative method validation;
7. confirm there is no unsupported anonymous-artifact claim, no new experiment, and no new empirical claim;
8. confirm the active repository contains only the canonical manuscript tree and no duplicate or numbered final PDFs; and
9. report the final PDF page count, files changed, verification performed, and any evidence-backed numerical correction. If the locked gap or contributions would need to change, report `SCIENTIFIC_DECISION_REQUIRED` instead of completing the rewrite.
