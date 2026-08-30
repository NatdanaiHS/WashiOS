# Goal

Freeze exact binary, source-state, and toolchain provenance for the completed dataset without modifying either board or any acquired evidence.

# Why

The experiment and statistics pass review, but the package contains only the G474 firmware binary. The exact G431 application/bootloader state and the uncommitted source state are not yet independently reproducible.

# Acceptance Criteria

- Read-only flash acquisition identifies each board by recorded ST-LINK serial and preserves exact G431 and G474 flash images with address ranges, byte counts, and SHA-256 values.
- The G474 programmed application bytes are compared with the packaged `g474_payload_firmware.bin`; match or mismatch is recorded, never assumed.
- A rebuild-only comparison is attempted for the G431 application and matching bootloader; exact matches or all differing regions are recorded without flashing.
- The source state is frozen with commit ID, tracked diff, untracked experiment source/test files, and SHA-256 inventory; raw datasets are referenced rather than duplicated.
- PlatformIO, platform/framework, Python, dependency, and compiler versions required to interpret or rebuild the package are recorded.
- Existing campaign/N0 artifacts and `SHA256SUMS.csv` remain unchanged; provenance is stored as an append-only addendum with its own inventory.

# Evidence Required

- `research/icsec2026/provenance/<timestamp>/PROVENANCE.md`
- Read-only board flash images and comparison reports
- Frozen source-state bundle or patch plus file inventory
- Toolchain/dependency version record
- `PROVENANCE_SHA256SUMS.csv`
- Updated `research/icsec2026/SESSION_STATE.md` distinguishing exact matches, supported linkage, and unresolved provenance

# Stop / Scope-Down Rule

If probe identity is ambiguous, readout protection is encountered, or any operation requests erase/program/unprotect, stop immediately. Do not flash, reset protection, overwrite the original dataset inventory, rerun the campaign, or infer that a rebuilt image equals the acquired image without a byte comparison.
