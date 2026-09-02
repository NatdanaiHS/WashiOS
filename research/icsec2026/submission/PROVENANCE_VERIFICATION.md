# Provenance verification

Result: **PASS**

- Active branch: `paper/icsec-confirmation-gated-final`.
- The approved positioning lock matches SHA-256 `120B4C51966DEB4029E63EF32C9EC23C467D5540AD4B492D2517CA0A1CBE44EC`.
- The rewrite began from canonical `submission/main.tex` SHA-256 `AA018D5E677D8C6ECAE93DEB33C068B01AC6050B5B57D47F303166BB750007B4` and canonical `submission/main.pdf` SHA-256 `99E4180F4B172C1CC7BABFCF8BE92FCC5442B3868F7AAD1D32A13779849E765D`.
- The evaluated controller sources are Git blobs `e2b6c9e9bb4af62afa32daa455479575eebff19a` (`PayloadLinkController.hpp`) and `a76804eb567689588bc3b1459df9a9352ec0d4f4` (`PayloadLinkTask.hpp`).
- The campaign runner supporting Figure 1's transitions is Git blob `68625847689bfe7906833bc1ade8dc9f8169625e`; exact line ranges are recorded in `CLAIM_EVIDENCE_AUDIT.md`.
- Primary 605-s nominal validation SHA-256 remains `3119D5994378E00C7ACE945B0FCB96CBA28C5855CDFEA445CD26570FD52A74FD`.
- BAD_CRC result SHA-256 remains `F6332F913FFA91432032AA1E5582AE78378F8880FC22D11B921C5B793ADC4E90`; all four endpoint logs were inspected in timestamp order.
- F411 Pair-1 and Pair-2 source/backup inventories remain separate with zero recorded issues; no evidence or firmware history was modified.
- Tectonic 0.17.0 produced the candidate in the ignored build directory. Only the verified PDF is promoted to the canonical review path.

Candidate status: `WORK_REVIEW_REQUIRED`.
