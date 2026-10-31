# ICSEC 2026 Payload-Link Provenance Addendum

Status: COMPLETE

This append-only addendum freezes binary, source-state, and toolchain provenance for the completed payload-link dataset. It does not modify or duplicate the frozen campaign/N0 evidence.

## Frozen dataset reference

- Dataset: `research/icsec2026/runs/full_20260830_seed20260830_n30/`
- Original inventory: `research/icsec2026/runs/full_20260830_seed20260830_n30/SHA256SUMS.csv`
- Original inventory SHA-256 before provenance work: `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD`

## Board identities and acquisition ranges

- G431 controller: NUCLEO-G431RB; ST-LINK serial `005100243032511537333436`; full internal flash `0x08000000` through `0x0801FFFF` inclusive; 131,072 bytes.
- G474 payload: NUCLEO-G474RE; ST-LINK serial `0041003D3234510F37333934`; full internal flash `0x08000000` through `0x0807FFFF` inclusive; 524,288 bytes.
- Probe selection uses the exact recorded ST-LINK serial. Both serials remain distinct in the current USB enumeration.
- Acquisition policy: OpenOCD SWD attach, halt, memory `dump_image`, resume, shutdown. No program, erase, unprotect, option-byte, or reset command is permitted.

## Read-only flash acquisition

Both captures selected the probe by the exact recorded ST-LINK serial. The OpenOCD target operation was limited to:

```text
init; targets; halt; dump_image {output} <address> <length>; resume; shutdown;
```

No program, erase, unprotect, option-byte, or reset command was issued. Both operations exited zero and produced the exact requested byte count. The CPU was transiently halted for memory acquisition and resumed before debugger shutdown. No readout block was encountered.

| Board | ST-LINK serial | Range | Bytes | Full-flash SHA-256 |
| --- | --- | --- | ---: | --- |
| G431 | `005100243032511537333436` | `0x08000000–0x0801FFFF` | 131,072 | `9D7B9B1439DCA29D434E768237BC78D5BE6737CAF481046C69B90ABA87A3BA1D` |
| G474 | `0041003D3234510F37333934` | `0x08000000–0x0807FFFF` | 524,288 | `0DC52660B6AD976BE217387791C554AD45CAE9ACE1D8C6BF265C3972B521A4E1` |

Acquisition reports, OpenOCD logs, and images are under `flash/`.

## Exact binary comparisons

### G474 payload application

- Frozen dataset binary: `research/icsec2026/runs/full_20260830_seed20260830_n30/firmware/g474_payload_firmware.bin`
- Compared flash range: `0x08000000–0x08002237`
- Byte count: 8,760
- Packaged/captured-region SHA-256: `351E62FCA5389070D393A9EAB973E48C4D8F9F1629483BDDCE063D673243A36C`
- Result: exact byte match; zero differing bytes and zero differing ranges.

This binds the frozen dataset firmware binary to the application bytes acquired from the identified G474. It does not claim the packaged application binary is a full-chip image.

### G431 payload-demo application

- Clean rebuild environment: `core:nucleo_g431rb_payload_demo`
- Compared flash range: `0x08004000–0x08008E33`
- Byte count: 20,020
- Rebuilt/captured-region SHA-256: `7C2C1B646AF312AB6766423D2BC228A5F11CFFB5F9B4BA23521D4610029DFE7F`
- Result: exact byte match; zero differing bytes and zero differing ranges.

### G431 matching bootloader

- Clean rebuild environment: `bootloader:nucleo_g431rb_payload_demo`
- Provisioned application CRC reported during build: `0xE72C1F19`
- Compared flash range: `0x08000000–0x08000FBF`
- Byte count: 4,032
- Rebuilt/captured-region SHA-256: `20FB03F428C980A5D0907E1889AFBA1777B11C6BA5AEA1744F0E716DA1AFA44D`
- Result: exact byte match; zero differing bytes and zero differing ranges.

Comparison JSON and exhaustive difference-range CSVs are under `comparisons/`. Empty difference CSV bodies are retained as evidence of zero ranges.

## Flash bytes outside attributed binary regions

- G431 `0x08000FC0–0x08003FFF`: 12,352 bytes total. Bytes `0x08001000–0x08003FFF` form one 12,288-byte non-`0xFF` range. These bytes are preserved but not attributed to either emitted rebuild binary.
- G431 `0x08008E34–0x0801FFFF`: 94,668 bytes, all `0xFF`.
- G474 `0x08002238–0x0807FFFF`: 515,528 bytes, including 30,101 non-`0xFF` bytes in 516 contiguous ranges. These bytes are preserved but not attributed to the packaged application.

Exact region hashes and non-`0xFF` range inventories are under `flash_layout/`. No interpretation of the unattributed bytes as active, inactive, historical, or erased content is made.

## Frozen source state

- Branch: `monorepo-migration`
- Commit: `ae891a70ca961d247b5fd5ac487271caf2fc881f`
- `source_state/tracked_worktree.patch`: binary-capable patch for tracked worktree changes relative to the commit.
- `source_state/staged.patch`: staged diff (retained even when empty).
- `source_state/git_status_porcelain_v1.txt`: complete file-level status including untracked paths.
- `source_state/tracked_files.txt`: tracked path list.
- `source_state/untracked_source_copies/`: 13 selected experiment firmware/harness source and test files copied with repository-relative paths.
- `source_state/untracked_source_inventory.csv`: byte counts and SHA-256 values for those copies.

Raw campaign/N0 data is referenced by its existing path and original inventory SHA-256; it is not duplicated in this addendum.

## Toolchain and dependency provenance

- PlatformIO Core: 6.1.19, using its internal Python 3.11.7.
- Platform: `ststm32` 19.6.0.
- STM32Cube G4 framework: `framework-stm32cubeg4` 1.6.1.
- Both clean G431 build logs selected `toolchain-gccarmnoneeabi` 1.70201.0.
- Exact selected compiler: GNU Arm Embedded GCC/G++ 7.2.1, 2017-q4-major.
- Exact selected objcopy: GNU binutils 2.29.51.20171128.
- OpenOCD: xPack 0.12.0+dev-02228-ge5888bda3-dirty, build timestamp 2025-10-04-22:44.
- Experiment Python: CPython 3.12.10; pip 25.0.1; pyserial 3.5.
- Git: 2.55.0.windows.3; PowerShell: 7.6.4.

`toolchain/selected_build_toolchain_1.70201.0.json` contains version output, package metadata, and executable hashes for the actual selected compiler tools. A generic installed GCC 12.3.1 directory is also recorded by the broad host inventory, but the build logs show it was not selected for these rebuilds.

The first three PlatformIO package-list commands encountered a CP1252 Unicode rendering failure after beginning output. The unchanged commands were repeated with `PYTHONIOENCODING=utf-8`; all three then exited zero and their full outputs are retained in `toolchain/package_lists_utf8.json`.

## Exact matches

- G474 packaged application binary equals the acquired G474 application region byte-for-byte.
- Clean rebuilt G431 payload-demo application equals the acquired G431 application region byte-for-byte.
- Clean rebuilt matching G431 bootloader equals the acquired G431 bootloader region byte-for-byte.
- Full user-flash captures have exact board identity, range, byte-count, and SHA-256 records.

## Supported linkage

- The dataset’s packaged G474 application is directly linked to the identified G474 readback by an exact byte comparison.
- The identified G431’s application and matching bootloader are linked to the frozen repository state and recorded toolchain by clean rebuilds followed by exact byte comparisons.
- The original dataset remains referenced by its immutable inventory rather than being repackaged or rewritten.

## Unresolved provenance / limitations

- The full-flash images cover internal user flash only. Option bytes, OTP, system ROM, RAM, and peripheral state were not captured.
- Unattributed non-`0xFF` regions outside emitted application/bootloader binaries are preserved and inventoried but their origin or runtime relevance is unknown.
- The source bundle freezes the working source state and selected untracked experiment files; it does not vendor the complete external PlatformIO/framework/toolchain directory trees. Package metadata, versions, paths, and executable hashes are provided instead.
- Debug attachment transiently halted and resumed each CPU. No flash/protection/reset command was used, but this is not a claim that runtime execution was never paused during provenance capture.

## Inventory

`PROVENANCE_SHA256SUMS.csv` is generated after all other addendum files and therefore does not list itself. Its independent SHA-256 and verification result are recorded in `research/icsec2026/SESSION_STATE.md`.
