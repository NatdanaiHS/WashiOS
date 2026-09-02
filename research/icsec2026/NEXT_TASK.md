# Next task: resolve STORY_BLOCK in Related Work

Make only the two scientific-story repairs below in the canonical manuscript. Do not perform a broader rewrite or cosmetic expansion.

## Required repairs

1. Add a concise, literature-verified acknowledgment that prior general HIL and communication-bus fault-injection work already provides signal, subsystem, or multi-point observation and test traceability. Cite the applicable Abboush HIL, Batista/FEM, and Conceição/SATS publications directly. State explicitly that separate or dual-channel observation by itself is not the contribution. Preserve the rule that “not reported in the cited publication” does not mean “does not exist.”
2. Explain in one or two direct sentences that the proposed protocol complements rather than replaces FEM, SATS, and general HIL architectures. Describe it as a validity/scoring layer that can sit around an existing injector and HIL setup: separate payload-side confirmation determines whether detector and recovery observations are eligible to be scored, while the underlying architecture still provides fault delivery, execution, and monitoring.

Place these points in Related Work, or split them between Related Work and the opening of Discussion only if that avoids repetition. Do not create a new section. Keep the wording short and evidence-bounded.

## Preserve without expansion

- Keep the approved gap, solution, contribution hierarchy, and terminology in `POSITIONING_LOCK.md` unchanged. Any proposed change to the gap or contributions requires `SCIENTIFIC_DECISION_REQUIRED`.
- Do not alter verified numerical results, frozen denominators, tables, Figure 1 semantics, experiment interpretation, or evidence boundaries.
- Do not add a new experiment, empirical claim, architecture claim, reliability claim, or anonymous-artifact claim.
- Do not expand the four-page manuscript to fill the six-page allowance. The Introduction already states the gap, the confirmation-gated validity/scoring semantics are clear, the audit workflow is present, and the physical evaluation is interpreted as setup-bounded demonstration rather than device reliability evidence.
- Do not add formalism, a gap matrix, another figure, or another table for these repairs.
- Retain the current concise, restrained prose. Avoid repeating the same complementarity statement in the Introduction, Related Work, Discussion, and Conclusion.

## Verification

After the two repairs, compile the canonical `research/icsec2026/submission/main.pdf` and confirm that:

1. Related Work explicitly acknowledges prior bus fault injection and prior multi-signal or multi-point observation;
2. the claimed methodological distinction remains confirmation-gated trial validity/scoring, not dual-channel monitoring;
3. the paper explicitly says the protocol complements rather than replaces FEM, SATS, and general HIL architectures;
4. every new literature statement is supported by the cited publication;
5. the PDF remains no more than six pages and has no visual regression; and
6. no other scientific or cosmetic change was introduced.
