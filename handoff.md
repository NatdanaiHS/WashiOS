# WashiOS ICSEC 2026 Handoff

Updated: 2026-08-30 (Asia/Bangkok)

## Current decision

The revised v2 manuscript is submission-ready. Scientific scope, statistical language, claim discipline, anonymity, citation closure, IEEE page/layout checks, and rendered-page QA pass. No further hardware acquisition or manuscript revision is authorized unless the submission portal exposes a concrete blocker.

## Repository state

- Source of truth: this repository
- Active branch at handoff: `experiment/icsec-extension-20260830`
- Frozen checkpoint commit before this handoff: `8a47d07` (`icsec: freeze current research and experiment state`)
- Engineering status: `research/icsec2026/SESSION_STATE.md`
- Next operational task: `research/icsec2026/NEXT_TASK.md`
- Anonymous manuscript PDF: `research/icsec2026/manuscript/main.pdf`
- Manuscript source: `research/icsec2026/manuscript/main.tex`
- Scientific v2 review: `research/icsec2026/manuscript/SCIENTIFIC_REVIEW_V2.md`
- Claim/anonymity audit: `research/icsec2026/manuscript/ANONYMITY_CLAIM_AUDIT.md`
- Rendered-page QA: `research/icsec2026/manuscript/qa/RENDERED_PAGE_QA_V2.md`

`SESSION_STATE.md` is authoritative for experiment and evidence status. If its historical branch/commit section differs from Git, use the live Git branch/commit above for repository navigation; do not reinterpret the frozen evidence.

## Locked terminology and scope

- `N0` / `Nominal Control` is the healthy nominal condition.
- `C0` is reserved for a future fair ablation. No C0 experiment exists and no comparative claim is supported.
- The experiment is activation-confirmed dual-channel HIL fault injection for payload-link supervision.
- Software fault injection is not radiation testing.
- Do not claim space-grade, flight-qualified, radiation-tolerant, mission-assured, or complete-system validation.

## Frozen evidence

- Hardware: one NUCLEO-G431RB controller and one NUCLEO-G474RE payload simulator.
- Controls: two valid 65-s N0 windows, one before and one after the campaign.
- Campaign: seed `20260830`; 90 sequential trials; 30 each for `SILENT`, `BAD_CRC`, and `DELAYED`.
- All 90 trials were valid and retained.
- Per mode: activation 30/30, restoration 30/30, predefined detection 30/30, recovery 30/30.
- Timing is host-observed command-to-marker timing and includes UART/USB/OS scheduling effects; it is not MCU-internal latency.
- Trials are repeated observations on one board pair, not independent device replicas. No device-population reliability estimate or confidence interval is supported.
- Frozen dataset inventory SHA-256: `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD`.
- Frozen provenance inventory SHA-256: `84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC`.

## Manuscript checkpoint

- Title: *Activation-Confirmed Dual-Channel HIL Fault Injection for Payload-Link Supervision*
- Format: anonymous IEEE conference paper, 4 US-letter pages.
- PDF SHA-256: `992A1C9AA41F4295BF7F97CA081D79A7DE2ABBB4B419B2A0B82144C1B50928DF`.
- Statistical reporting is descriptive: observed counts/proportions and latency distributions only.
- Clopper-Pearson intervals were intentionally removed from manuscript v2.
- The closest-work claim is bounded to the observation/scoring protocol: independent controller/payload host channels, explicit activation/restoration confirmations, and byte-preserving trial traces.

## Interpretation discipline

### Observed

- Both N0 windows met their predefined criteria.
- Every retained trial contained the required activation, detector, restoration, and recovery evidence.
- Raw logs, validation outputs, firmware, summaries, and inventories are preserved.

### Supported inference

- On the evaluated board pair and fixed setup, each configured payload behavior consistently produced its predefined controller marker and later recovery marker after confirmed NORMAL restoration.

### Unknown / not evaluated

- Cross-device, environmental, and long-duration generalization.
- MCU-internal timing.
- Absolute proof that no MCU reset occurred.
- Electrical, environmental, or radiation-fault equivalence.
- Treatment effect or superiority relative to a fair C0 ablation.

## Next milestone

Freeze and submit the unchanged anonymous PDF through the official ICSEC 2026/EDAS system. The official schedule page contains conflicting date blocks; its current Important Dates block states 5 September 2026, so verify the live EDAS status before final submission. Preserve the paper ID, submission confirmation, and SHA-256 of the exact uploaded PDF.

Do not edit the paper, add review-stage identity, add a copyright notice, collect new data, or change frozen artifacts unless EDAS explicitly rejects the file or the chairs confirm a review-stage requirement.

## Startup instruction for the next AI

Read `research/icsec2026/SESSION_STATE.md`, `research/icsec2026/NEXT_TASK.md`, and the manuscript v2 review/audit files before proposing changes. Treat evidence as frozen, distinguish Observed / Supported inference / Unknown, and prioritize submission correctness over new features or architecture work.
