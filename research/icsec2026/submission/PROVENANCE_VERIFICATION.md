# Provenance verification

Result: **PASS**

- Active branch: `paper/icsec-confirmation-gated-final`.
- The approved positioning lock matches SHA-256 `7637F3D3FC53622A382C29C6B1BFD7EE952558F4961358FF347870EB756CC586`.
- The rewrite began from canonical `submission/main.tex` SHA-256 `AA018D5E677D8C6ECAE93DEB33C068B01AC6050B5B57D47F303166BB750007B4` and canonical `submission/main.pdf` SHA-256 `99E4180F4B172C1CC7BABFCF8BE92FCC5442B3868F7AAD1D32A13779849E765D`.
- The evaluated controller sources are Git blobs `e2b6c9e9bb4af62afa32daa455479575eebff19a` (`PayloadLinkController.hpp`) and `a76804eb567689588bc3b1459df9a9352ec0d4f4` (`PayloadLinkTask.hpp`).
- The campaign runner supporting Figure 1's transitions is Git blob `68625847689bfe7906833bc1ade8dc9f8169625e`; exact line ranges are recorded in `CLAIM_EVIDENCE_AUDIT.md`.
- Protected G474 and F411 payload sources and the shared host-command parser match their cleanup-freeze hashes. Their exact assignment-before-confirmation locations and the confirmation trust boundary are recorded in `CLAIM_EVIDENCE_AUDIT.md`.
- Primary 605-s nominal validation SHA-256 remains `3119D5994378E00C7ACE945B0FCB96CBA28C5855CDFEA445CD26570FD52A74FD`.
- BAD_CRC result SHA-256 remains `F6332F913FFA91432032AA1E5582AE78378F8880FC22D11B921C5B793ADC4E90`; all four endpoint logs were inspected in timestamp order.
- F411 Pair-1 and Pair-2 source/backup inventories remain separate with zero recorded issues; no evidence or firmware history was modified.
- The separate five-case synthetic scorer validation passes all assertions and reports all referenced empirical source hashes unchanged; it is not part of any HIL denominator.
- Tectonic 0.17.0 produced the canonical candidate locally without Docker. The latest build log is retained under the ignored build directory, and only `main.pdf` remains at the canonical review path.

Candidate status: `WORK_REVIEW_REQUIRED`.
