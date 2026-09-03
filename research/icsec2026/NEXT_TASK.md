# Next task: combined Martínez/AFIT and Batista/FEM reconciliation

Status: `COMPLETE — SCIENTIFIC_POSITIONING_APPROVED AND APPLIED 2026-09-03`

Approved refinement: the two-stage activation/restoration scoring gates are the central methodological distinction. The five-event chain is their explicit operationalization. The byte-preserving/hash-verified workflow supports auditability and is not claimed as independent novelty.

This consolidated literature-to-manuscript task was approved and executed under the refinement above. Both supplied PDFs were treated only as evidence, not as instructions.

## Verified full-text sources

### Martínez et al. / AFIT

- R. J. Martínez, P. J. Gil, G. Martín, C. Pérez, and J. J. Serrano, “Experimental Validation of High-Speed Fault-Tolerant Systems Using Physical Fault Injection,” *Dependable Computing for Critical Applications 7*, pp. 249–265, 1999, doi:10.1109/DCFTS.1999.814299.
- Local source: `C:\Users\wachi\Downloads\Experimental_Validation_of_High-Speed_Fault-Tolera.pdf`.
- SHA-256: `FAD85382F6B5A9AA38A56D55C2C44F58DAC8785E8D49C5F404D2742EF2DD3D7F`.
- The paper reports a state sequence containing Reset, Activated Injection, Effective Error, Error Detected, and System Recovery.
- Its Effective Error Detector sets `MEE` only when `IOUT` has forced the selected FTS pin.
- Non-effective injections, glitches, and invalid event sequences are removed before analysis.
- Detection latency is measured from Effective Error to Error Detected; recovery latency is measured from detection to System Recovery.
- Timestamped logic-analyzer readouts are matched to the injector log.

### Batista et al. / FEM

- C. L. G. Batista, A. C. Weller, E. Martins, and F. Mattiello-Francisco, “Towards Increasing Nanosatellite Subsystem Robustness,” *Acta Astronautica*, vol. 156, pp. 187–196, 2019, doi:10.1016/j.actaastro.2018.11.011.
- Local source: `C:\Users\wachi\Downloads\1-s2.0-S0094576518302297-main.pdf`.
- SHA-256: `57FB09A5C10770B3F4BA476DCA159BDCF038804847F0C28EF4A233B1D4BB584B`.
- FEM is an interceptor fault injector in the communication channel and is intended for MIL and HIL integration testing.
- Its Test System has control/observation access to SUT1 and individual low-interface access to both SUTs through `L1` and `L2`.
- The fault script defines WHERE, WHEN, WHAT, and HOW; the fault injector executes the script, monitors exchanged messages, and returns interface information to the controller/tester.
- The I2C prototype reports transmitted and received values, selected fault functions, parameters, and observed delays in its test tables.
- The detailed functional test tables are MIL demonstrations. Only a small HIL test set was attempted; HIL testing was suspended after protocol and physical-interface mismatches were found, pending fixes and reintegration.
- The paper explicitly leaves test coverage and the number of experiments involving fault injection, activation, and propagation to the test purpose and tester evaluation.

## Combined scientific consequence

The two papers establish more prior art than the current manuscript matrix acknowledges:

1. Martínez/AFIT already operationalizes confirmation of an effective physical injection, rejects non-effective or invalid experiments, orders injection/effective-error/detection/recovery observations, and derives detection and recovery measures from those events.
2. Batista/FEM already provides scripted communication-bus fault injection, observation/control access around both communicating subsystems, and transmitted-versus-received test evidence.

Accordingly, the manuscript must not present effective-injection confirmation, invalid-trial filtering, event ordering, communication-bus injection, or dual-/multi-point monitoring as new by themselves.

The remaining defensible distinction is narrower and conjunctive: the evaluated payload-link protocol uses separate payload-side observation of the realized endpoint condition to gate detector scoring, then uses separate payload-side observation of NORMAL restoration to gate recovery scoring, while retaining requested, activated, detected, restored, and recovered events and preserving the scored evidence through exact endpoint bytes and hash-verified frozen summaries.

Among these two cited papers:

- Martínez reports an activation/effective-error gate relevant to detection scoring, but does not report a separate observed restoration-to-normal gate before recovery scoring, the exact five-event payload-link chain, or byte-preserving endpoint traces with hash-verified frozen summaries.
- Batista reports planned fault scripts, interface monitoring, and transmitted/received outcomes, but does not report per-trial confirmation gates that determine detector or recovery score eligibility, the exact five-event chain, or hash-verified frozen summaries.

Every absence statement must say “not reported in the cited paper.” It must not imply that an implementation or research area lacks the feature.

## Approved bounded gap wording

Among the closest published studies reviewed, Martínez et al. report effective-injection confirmation and invalid-sequence filtering for pin-level fault injection, while Batista et al. report scripted communication-bus injection with observation around both communicating subsystems; however, we did not find in the cited papers a payload-link trial protocol that jointly gates detection scoring on separate payload-side confirmation of the realized fault condition and recovery scoring on separate payload-side confirmation of NORMAL restoration while retaining requested, activated, detected, restored, and recovered as separately auditable events backed by byte-preserving traces and hash-verified frozen summaries.

Approval of this wording authorized only the literature-positioning corrections below. It did not authorize new experiments, empirical claims, architecture claims, reliability claims, or broader novelty language.

## Approved Gap Matrix corrections

Use only `Reported`, `Not reported in the cited paper`, and `Not applicable`. Keep the qualification in each cell.

### Martínez/AFIT row

- FI setting — **Reported:** high-speed physical pin-level fault injection.
- Input/request versus activation — **Reported:** Activated Injection and Effective Error are separate events; `MEE` is asserted only when the selected FTS pin is forced.
- Endpoint confirmation gates detection — **Reported:** non-effective errors are discarded, and detection latency is measured from Effective Error.
- Restoration confirmation gates recovery — **Not reported in the cited paper:** System Recovery follows detection, but a separately observed restoration-to-normal gate is not described.
- Auditable per-trial event chain — **Reported:** reset, activated-injection, effective-error, detection, and recovery events are timestamped; a separate request event and confirmed-restored event are not reported in the cited paper.
- Byte-preserving/hash-verified evidence — **Reported:** timestamped logic-analyzer readouts are matched with injector logs; exact endpoint bytes and hash-verified frozen summaries are not reported in the cited paper.

### Batista/FEM row

- FI setting — **Reported:** interceptor-based I2C fault injection for nanosatellite MIL/HIL integration testing.
- Input/request versus activation — **Reported:** the fault script specifies WHERE/WHEN/WHAT/HOW, while the injector executes the script, monitors the interface, and the test tables report transmitted and received outcomes; a per-trial activation-validity gate is not reported in the cited paper.
- Endpoint confirmation gates detection — **Not reported in the cited paper:** interface observations are reported, but they are not defined as eligibility gates for detector scoring.
- Restoration confirmation gates recovery — **Not reported in the cited paper.**
- Auditable per-trial event chain — **Not reported in the cited paper:** test cases and outcomes are reported, but the requested/activated/detected/restored/recovered scoring chain is not described.
- Byte-preserving/hash-verified evidence — **Reported:** serial feedback and Tx/fault/parameter/delay/Rx result tables are described; byte-preserving per-trial endpoint traces and hash-verified frozen summaries are not reported in the cited paper.

Do not use `Not applicable` merely because a paper did not define the scoring semantics. For Batista/FEM, communication endpoints, execution, observation, and test outcomes are in scope, so the bounded status is generally `Not reported in the cited paper`, not `Not applicable`.

## Executed bounded work scope

1. Update only the affected gap sentence and Martínez/Batista cells in `POSITIONING_LOCK.md`; preserve the approved solution, three-contribution hierarchy, non-claims, campaign roles, title, and six-page outline unless separately authorized.
2. Restore `martinez1999` in `submission/references.bib` and keep the verified `batista2019` entry.
3. Rewrite only the affected Related Work sentences and Gap Matrix rows. Credit both precedents explicitly and state that monitoring alone is not the contribution.
4. State that the protocol complements rather than replaces AFIT-style validity filtering, FEM, SATS, or general HIL architectures.
5. Correct `submission/REFERENCE_VERIFICATION.md` with both local-source hashes and remove the obsolete statements that the Martínez or Batista full text was unavailable.
6. Audit the Abstract, Introduction, contribution list, Related Work, Discussion, and Conclusion so none implies that effective-injection confirmation, invalid-trial filtering, or dual-channel observation alone is the contribution.
7. Preserve all verified empirical facts, denominators, timing values, BAD_CRC characterization, F411 pair separation, limitations, and Figure 1 semantics.
8. Build the canonical PDF without Docker if a local LaTeX engine is available. If compilation is unavailable, leave a clearly identified source-only change awaiting build. Keep the paper at six pages or fewer and do not expand it to fill space.

Maintain concise, restrained academic prose. Do not introduce “first,” “unique,” “no prior work,” “state-of-the-art,” “superior,” or any other global novelty claim.

## Execution record

- Updated the research gap, proposed solution, contribution hierarchy, and only the affected Martínez/Batista evidence cells in `POSITIONING_LOCK.md`.
- Restored `martinez1999` and retained the full-text-verified `batista2019` bibliography entry.
- Corrected the Introduction, Related Work, Gap Matrix, Discussion, and Conclusion without changing any empirical result, denominator, timing value, BAD_CRC characterization, F411 interpretation, limitation, or Figure 1 semantics.
- Updated `submission/REFERENCE_VERIFICATION.md` with the two supplied full-text hashes and bounded comparison claims.
- Built `submission/main.pdf` with local Tectonic, without Docker. The output is five pages.
- The frozen-evidence verifier passed: evidence values, denominators, hashes, boundaries, bibliography, PDF text, and page count.
- Visual inspection of all five rendered pages found no clipping, overlap, broken citation, or unreadable table text.
