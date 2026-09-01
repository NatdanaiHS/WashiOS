# Frozen-Baseline Recovery Record

Status: **PASS**

The original-PC transfer ZIP was hashed before extraction and matched the supplied SHA-256 exactly. Its extracted source remained read-only during reconciliation and independently verified against its 269-row transfer inventory both before and after copying.

The recovered source contains every byte required by the unchanged frozen inventories. The final primary and secondary copies each pass all 195 dataset rows and all 65 provenance rows with zero missing files, zero size mismatches, and zero SHA-256 mismatches.

## Verified external paths

- Source extraction: `C:/WashiOS-baseline-recovery/source_transfer_20260901_5BC8B2B1/WashiOS_EVIDENCE_TRANSFER_20260901`
- Primary verified copy: `C:/WashiOS-baseline-recovery/primary_recovered_baseline_20260901_attempt3_verified`
- Secondary verified copy: `C:/WashiOS-baseline-recovery/secondary_recovered_baseline_20260901_verified`

Each final copy contains 262 files totaling 1,559,372 bytes: 260 inventory-listed artifacts plus the two unchanged inventory files.

## Byte-source reconciliation

- 30 tracked inventory rows exactly match their raw blob at frozen commit `8a47d070c549274c59cdbde2495afa8d353a93b3`.
- 35 tracked inventory rows require the recovered original clean-working-tree byte sequence to match the frozen inventory.
- 195 ignored raw logs/binaries/ELFs require the recovered original bytes.
- The two unchanged inventory files were copied from the verified source transfer because their recorded inventory-file hashes identify the original CRLF working-tree bytes.

This mixed line-ending result explains why two staging methods failed. Both failed directories and their complete ledgers are retained. No failed file was replaced in place or hidden; the passing copy uses a third exclusive path.

## Boundaries

- No board or oscilloscope was connected, commanded, flashed, reset, or sampled.
- No frozen dataset, provenance, manuscript, or reviewed extension evidence path was changed.
- No inventory was regenerated.
- This milestone restores exact frozen bytes; it adds no experimental observation or scientific claim.

See `RECOVERY_RECORD.json` for machine-readable counts, hashes, tools, and paths, and `COMMAND_LOG.md` for the executed copy/verification sequence.
