# Recovery Command and Tool Record

All source discovery and verification operations were read-only. Output paths were created exclusively and were never reused.

## Tools

- Windows 11 Home Single Language
- PowerShell 7.6.4
- Git 2.55.0.windows.3
- bsdtar 3.8.4
- SHA-256 through PowerShell `Get-FileHash`

## Executed sequence

1. `Get-FileHash -Algorithm SHA256 C:/Users/wachi/Documents/WashiOS_EVIDENCE_TRANSFER_20260901.zip`
2. Open the ZIP central directory with `.NET System.IO.Compression.ZipFile` and confirm 270 file entries totaling 1,663,907 bytes.
3. Create exclusive source directory `C:/WashiOS-baseline-recovery/source_transfer_20260901_5BC8B2B1` and run `Expand-Archive` once.
4. Verify every extracted file listed in `TRANSFER_FILE_INVENTORY.csv` with `Get-Item` and `Get-FileHash`.
5. Verify all 195 dataset and 65 provenance rows against the unchanged extracted inventories.
6. Failed attempt 1: create an exclusive primary directory, export tracked paths with `git archive --format=tar`, extract with `tar -xf`, and copy the 195 ignored recovered artifacts with `Copy-Item`. Independent verification detected and retained 28 mismatches.
7. Failed attempt 2: create a new exclusive primary directory, stream every tracked path with `git cat-file blob`, and copy the 195 ignored recovered artifacts. Independent verification detected and retained 35 row mismatches plus two inventory-file hash mismatches.
8. Passing attempt 3: create a third exclusive primary directory. For each inventory row, select the raw frozen Git blob only when its SHA-256 equals the inventory; otherwise select the exact recovered original. Copy both unchanged inventories from the verified transfer. Verify every copied row independently.
9. Create the exclusive secondary directory with `Copy-Item -Recurse` from the passing primary copy and independently verify every row against both unchanged inventories.
10. Reverify all 269 source-transfer inventory rows after all copy operations to confirm the extracted source did not change.

Per-file sources, expected/actual sizes, hashes, and validity are retained in `PRIMARY_COPY_LEDGER.csv` and `SECONDARY_VERIFICATION_LEDGER.csv`. Failed-attempt details are retained in the two mismatch ledgers.
