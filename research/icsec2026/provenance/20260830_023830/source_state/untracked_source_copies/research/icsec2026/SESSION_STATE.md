# ICSEC 2026 Hardware Experiment Session State

Last updated: 2026-08-30T02:42:00+07:00

## Objective

Freeze exact board-flash, rebuild, source-state, and toolchain provenance for the completed dataset without modifying either board or any frozen campaign/N0 artifact.

## Branch and commit

- Branch: `monorepo-migration`
- Starting commit: `ae891a70ca961d247b5fd5ac487271caf2fc881f`
- Current commit: `ae891a70ca961d247b5fd5ac487271caf2fc881f`
- Working tree was verified clean before session files were created.

## Modifications

- Added this authoritative session state file.
- Added `demo-payload/src/HostModeCommandParser.hpp`, implementing bounded line parsing for `MODE NORMAL`, `MODE SILENT`, `MODE BAD_CRC`, and `MODE DELAYED`.
- Modified `demo-payload/src/main.cpp` to receive debug-UART bytes through a non-blocking interrupt-fed ring buffer, apply the existing `PayloadMode`, emit the existing machine-readable `[PAYLOAD] MODE=...` confirmation, preserve button mode cycling, and reject invalid commands explicitly.
- Added the `demo-payload` native test environment and three command-parser test cases.
- Added `research/icsec2026/injector/run_payload_campaign.py`, its pyserial requirement, and four host-side tests.
- Hardened campaign capture so serial-reader exceptions are surfaced, every run requires G431 serial evidence, and any invalid/unconfirmed run stops the campaign after its artifacts are retained.
- Added `run_n0_control.py` with exclusive artifact creation and counter/marker-based N0 validation, plus two native Python tests.
- Added raw-log campaign validation, exact Clopper-Pearson/latency summary generation, and deterministic exclusive SHA-256 inventory tooling with tests.
- Began append-only provenance addendum `research/icsec2026/provenance/20260830_023830/`; no existing dataset file is in its output path.
- G431 firmware and manuscript files have not been modified.

## Hardware / COM configuration

- Controller/OBC: NUCLEO-G431RB
- Simulated payload: NUCLEO-G474RE
- NUCLEO-F411RE: prohibited for this session
- Inter-board UART: G431 PC4 TX -> G474 PC5 RX; G431 PC5 RX <- G474 PC4 TX; common GND; 115200 8N1
- G431 host/debug COM port: `COM8` (USB VID:PID 0483:374E, ST-LINK serial `005100243032511537333436`)
- G474 host/debug COM port: `COM7` (USB VID:PID 0483:374E, ST-LINK serial `0041003D3234510F37333934`)
- pyserial 3.5 is installed in the active Python 3.12 environment.

## Commands executed

```text
Get-Content -Raw <pasted request attachment>
git status --short --branch
Get-Content -Raw research/icsec2026/NEXT_TASK.md
Get-FileHash research/icsec2026/runs/full_20260830_seed20260830_n30/SHA256SUMS.csv
pio device list
Get-Content linker scripts/platformio.ini/OpenOCD helper for memory-map and command audit
python provenance/.../readonly_flash_capture.py for exact-serial G431 full flash
python provenance/.../readonly_flash_capture.py for exact-serial G474 full flash
python provenance/.../compare_binary_region.py for G474 packaged application
python provenance/.../rebuild_capture.py for clean G431 payload-demo application build
python provenance/.../rebuild_capture.py for clean matching G431 bootloader build
python provenance/.../compare_binary_region.py for G431 application and bootloader
Get-Content -Raw research/icsec2026/NEXT_TASK.md
python -m unittest discover -s research/icsec2026/injector -p test_*.py
python -m py_compile research/icsec2026/injector/run_payload_campaign.py research/icsec2026/injector/run_n0_control.py
git diff --check
python research/icsec2026/injector/run_n0_control.py --name n0_pre_20260830_0205 --phase pre --g431-port COM8 --g474-port COM7 --duration-s 65
Get-Content -Raw research/icsec2026/runs/n0_pre_20260830_0205/{manifest.json,validation.json}
Get-FileHash for pre-N0 logs, manifest, and validation
python research/icsec2026/injector/run_payload_campaign.py --campaign full_20260830_seed20260830_n30 --seed 20260830 --g431-port COM8 --g474-port COM7 --repetitions 30
PowerShell manifest/results completion and count check for full_20260830_seed20260830_n30
python research/icsec2026/injector/run_n0_control.py --name n0_post_20260830_0224 --phase post --g431-port COM8 --g474-port COM7 --duration-s 65
Get-Content -Raw research/icsec2026/runs/n0_post_20260830_0224/{manifest.json,validation.json}
Get-FileHash for post-N0 logs, manifest, and validation
python research/icsec2026/injector/summarize_payload_campaign.py --campaign-dir research/icsec2026/runs/full_20260830_seed20260830_n30 --seed 20260830 --expected-per-fault 30
Get-Content/Get-FileHash for campaign validation.json and summary.json
New-Item/Copy-Item exact built firmware into campaign firmware package
python research/icsec2026/injector/create_sha256_inventory.py --repo-root . --output research/icsec2026/runs/full_20260830_seed20260830_n30/SHA256SUMS.csv --include research/icsec2026/runs/n0_pre_20260830_0205 --include research/icsec2026/runs/full_20260830_seed20260830_n30 --include research/icsec2026/runs/n0_post_20260830_0224
Independent PowerShell SHA-256 and size verification of all 195 inventory rows
python -m unittest discover -s research/icsec2026/injector -p test_*.py
git diff --check
git status --short --branch
git rev-parse HEAD
rg --files -g AGENTS.md -g !**/.pio/** -g !**/node_modules/**
rg --files research/icsec2026 demo-payload
Get-Date -Format yyyy-MM-ddTHH:mm:ssK
git status --porcelain=v1
Get-Content -Raw demo-payload/src/main.cpp
Get-Content -Raw demo-payload/platformio.ini
rg -n <payload evidence markers> .
Get-Content -Raw core/src/app/PayloadLinkTask.hpp
Get-Content -Raw core/include/comms/PayloadLinkController.hpp
pio test -d demo-payload -e native
python -m unittest research/icsec2026/injector/test_run_payload_campaign.py
python -m py_compile research/icsec2026/injector/run_payload_campaign.py
pio run -d demo-payload -e nucleo_g474re
python -m pip install -r research/icsec2026/injector/requirements.txt
python research/icsec2026/injector/run_payload_campaign.py --help
git diff --check
Get-FileHash -Algorithm SHA256 demo-payload/.pio/build/nucleo_g474re/firmware.bin
pio device list
pio run -d demo-payload -e nucleo_g474re -t upload
pio run -d demo-payload -e nucleo_g474re -t upload -v
.\tools\flash_payload_responder.ps1
python -c <COM7 four-mode command/confirmation check>
pio device list
python -c <initial dual-console sampler; loop error>
Get-CimInstance Win32_Process -Filter Name=python.exe
Stop-Process -Id 36476
python -c <bounded COM8/COM7 dual-console link check>
python research/icsec2026/injector/run_payload_campaign.py --campaign pilot_20260830_0140_seed431474 --seed 431474 --g431-port COM8 --g474-port COM7
Get-Content -Raw research/icsec2026/runs/pilot_20260830_0140_seed431474/{manifest.json,run_plan.csv,results.csv}
Get-ChildItem/Get-Content/Get-FileHash for all six pilot raw logs
Get-FileHash for pilot manifest, run plan, and results
git diff --check
git status --short --branch
```

## Completed verification

- Repository is on branch `monorepo-migration` at starting commit `ae891a70ca961d247b5fd5ac487271caf2fc881f`.
- Working tree was clean at task start.
- `demo-payload/src/main.cpp` and `demo-payload/platformio.ini` exist.
- No repository `AGENTS.md` was found by the initial search.
- No fair C0 ablation configuration exists; `C0` is reserved for a future fair ablation and must not label the current healthy baseline.
- Command parser native tests: 3/3 passed.
- Harness tests: 4/4 passed, covering deterministic plan reproduction, complete fault membership and bounded offsets, CSV/raw-log creation with exclusive run directories, and fault-specific detection rules.
- Repeating the same seed produces an identical in-memory run plan in the tested Python runtime.
- Modified G474 firmware built successfully for `nucleo_g474re`.
- Built firmware binary: 8,760 bytes; SHA-256 `351E62FCA5389070D393A9EAB973E48C4D8F9F1629483BDDCE063D673243A36C`.
- Raw log records contain host UTC time, exact received bytes as hexadecimal, and an escaped readable rendering. Existing campaign/run directories are opened exclusively and are never reused.
- Harness activation requires the G474 `[PAYLOAD] MODE=<fault>` confirmation; a sent command alone is insufficient.
- DELAYED classification uses the actually inspected controller behavior: a 250 ms payload response exceeds the 100 ms G431 deadline, so the accepted detector markers are G431 `PAYLOAD_TIMEOUT` or `PAYLOAD_OFFLINE`. BAD_CRC requires the explicit CRC rejection marker and does not require OFFLINE.
- With only the G474 connected, its virtual serial interface was identified as `COM7`.
- The direct PlatformIO upload target failed before programming because PlatformIO selected obsolete OpenOCD transport `hla_swd`; this failure did not alter experiment data.
- Repository script `tools/flash_payload_responder.ps1` selected compatible `swd`, identified STM32G47/G48xx flash, completed programming, reported `Verified OK`, and reset the target.
- On-hardware host command verification on COM7 observed exact confirmations for SILENT, BAD_CRC, DELAYED, and NORMAL. The final commanded mode was NORMAL.
- With both permitted boards connected, the newly enumerated G431 virtual serial interface was identified as `COM8`.
- A first ad hoc sampler contained an unbounded-comprehension error and was terminated by exact PID after its command line was verified; it produced no usable evidence and no campaign directory.
- A corrected six-second dual-console check observed G431 `[OBC] PAYLOAD_STATUS state=ONLINE ...` on COM8 and G474 `[PAYLOAD] MODE=NORMAL` on COM7.
- Automated campaign `pilot_20260830_0140_seed431474` completed all three randomized faults with manifest status `COMPLETE` and no invalid runs.
- Seed 431474 produced order SILENT, DELAYED, BAD_CRC with pre-injection offsets 0.312 s, 1.047 s, and 0.505 s respectively.
- All three activations were confirmed by the corresponding G474 `[PAYLOAD] MODE=...` raw log line.
- SILENT detection: first G431 `PAYLOAD_TIMEOUT consecutive=1`, host latency 578 ms from command send; OFFLINE and later RECOVERED were observed.
- DELAYED detection: first G431 `PAYLOAD_TIMEOUT consecutive=1`, host latency 344 ms from command send; late `PAYLOAD_REJECT reason=SEQUENCE`, OFFLINE, and later RECOVERED were also observed.
- BAD_CRC detection: first G431 `PAYLOAD_REJECT reason=CRC`, host latency 78 ms from command send. In this actual four-second run the controller subsequently timed out, entered OFFLINE, and later emitted RECOVERED; OFFLINE was observed but was not required for BAD_CRC activation or detection classification.
- Host-measured restore-command-to-`PAYLOAD_RECOVERED` intervals were 438 ms (SILENT), 234 ms (DELAYED), and 531 ms (BAD_CRC). These are host serial timestamps and should be treated as host-observed timing, not MCU-internal timing.
- No post-injection `PAYLOAD_LINK_START` marker was observed in any pilot run. This is recorded only as marker absence and is not proof that no MCU reset occurred.
- Raw logs were inspected against `results.csv`; the reported markers and times agree with the preserved records.
- The literal `heartbeat=OK watchdog=OK` text appears in G431 logs but has not been interpreted as independently measured state.
- Research direction approved seed 20260830, 30 trials per fault, and dedicated pre/post N0 controls.
- N0 validation tooling requires at least 60 seconds, at least 10 ONLINE status records, strictly increasing `ok`, zero deltas for timeout/CRC/sequence/recovery counters, and absence of all prohibited transition/restart markers.
- Current host test suite passes 6/6 after harness hardening and N0 tooling addition.
- Pre-campaign N0 `n0_pre_20260830_0205` completed a 65.0-second validated window.
- Pre-N0 contained 13 `PAYLOAD_STATUS state=ONLINE` records; `ok` increased strictly from 1835 to 1955.
- Pre-N0 deltas were timeout=0, crc=0, seq=0, recovery=0, with no prohibited transition or post-start link-start marker.
- Post-processing/inventory host test suite passes 11/11.
- Full campaign `full_20260830_seed20260830_n30` completed all 90 planned trials with seed 20260830; manifest status is `COMPLETE`, results contain 90 rows, and the preliminary invalid count is zero.
- Post-campaign N0 `n0_post_20260830_0224` completed a 65.0-second validated window.
- Post-N0 contained 13 `PAYLOAD_STATUS state=ONLINE` records; `ok` increased strictly from 3049 to 3169.
- Post-N0 deltas were timeout=0, crc=0, seq=0, recovery=0, with no prohibited transition or post-start link-start marker.
- Machine validation checked 90 result rows against all 180 campaign raw logs and found zero issues.
- All modes had 30 valid, 0 invalid, 30/30 activation confirmations, 30/30 restoration confirmations, 30/30 detections, 30/30 OFFLINE observations, 30/30 recovery observations, and 0/30 post-injection restart markers.
- For each 30/30 detection and recovery proportion, the two-sided 95% Clopper-Pearson interval is `[0.884296692, 1.0]`.
- Host-observed detection latency (median, IQR, min, max; milliseconds): SILENT `(383.0, 196.25, 125.0, 578.0)`; BAD_CRC `(359.5, 293.0, 78.0, 531.0)`; DELAYED `(406.0, 215.0, 156.0, 610.0)`.
- Host-observed restore-command-to-recovery latency (median, IQR, min, max; milliseconds): SILENT `(297.0, 230.75, 78.0, 516.0)`; BAD_CRC `(359.0, 303.5, 47.0, 531.0)`; DELAYED `(296.5, 238.25, 94.0, 531.0)`.
- The packaged firmware is 8,760 bytes with SHA-256 `351E62FCA5389070D393A9EAB973E48C4D8F9F1629483BDDCE063D673243A36C`, matching the image built and flashed earlier.
- `SHA256SUMS.csv` inventories 195 artifacts: 180 campaign raw logs, four pre-N0 files, four post-N0 files, and seven additional campaign/package files including firmware.
- An independent re-hash verified all 195 recorded sizes and SHA-256 values with zero mismatches.
- Final host-side suite passes 11/11; `git diff --check` reports no whitespace errors (only existing line-ending notices).
- Provenance review approved. The frozen dataset inventory SHA-256 was rechecked before provenance work as `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD`.
- Current USB enumeration still uniquely maps G431 ST-LINK serial `005100243032511537333436` to COM8 and G474 ST-LINK serial `0041003D3234510F37333934` to COM7.
- Linker/device definitions establish full-flash acquisition ranges: G431 `0x08000000` + `0x20000` bytes; G474 `0x08000000` + `0x80000` bytes.
- The readback helper rejects operations containing program, erase, unprotect, option, or reset; its only target operations are attach/init, halt, `dump_image`, resume, and shutdown.
- Read-only G431 full-flash capture completed for exact ST-LINK serial `005100243032511537333436`: 131,072 bytes, range `0x08000000–0x0801FFFF`, SHA-256 `9D7B9B1439DCA29D434E768237BC78D5BE6737CAF481046C69B90ABA87A3BA1D`.
- Read-only G474 full-flash capture completed for exact ST-LINK serial `0041003D3234510F37333934`: 524,288 bytes, range `0x08000000–0x0807FFFF`, SHA-256 `0DC52660B6AD976BE217387791C554AD45CAE9ACE1D8C6BF265C3972B521A4E1`.
- Both OpenOCD operations exited 0 after `dump_image`; no program, erase, unprotect, option-byte, or reset command was issued. The target was halted for memory acquisition and resumed before shutdown.
- The captured G474 application region `0x08000000–0x08002237` exactly matches the frozen packaged 8,760-byte binary; both SHA-256 values are `351E62FCA5389070D393A9EAB973E48C4D8F9F1629483BDDCE063D673243A36C`.
- The G474 full flash contains preserved non-`0xFF` content outside the packaged application region; therefore the packaged binary is linked exactly to the programmed application region but is not represented as a full-chip image.
- Clean rebuild-only G431 payload-demo application: 20,020 bytes, SHA-256 `7C2C1B646AF312AB6766423D2BC228A5F11CFFB5F9B4BA23521D4610029DFE7F`.
- Captured G431 application region `0x08004000–0x08008E33` exactly matches that rebuild; zero differing bytes/ranges.
- Clean rebuild-only matching G431 bootloader: 4,032 bytes, SHA-256 `20FB03F428C980A5D0907E1889AFBA1777B11C6BA5AEA1744F0E716DA1AFA44D`.
- Captured G431 bootloader region `0x08000000–0x08000FBF` exactly matches that rebuild; zero differing bytes/ranges.

## Evidence locations

- Session state: `research/icsec2026/SESSION_STATE.md`
- Campaign harness: `research/icsec2026/injector/run_payload_campaign.py`
- Dataset guide: `research/icsec2026/runs/full_20260830_seed20260830_n30/DATASET_README.md`
- Dataset guide SHA-256: `03F9865F836D53725A48040AF56211AF8BD66FBDE8198FF6273229D66651638B`
- Completed pilot: `research/icsec2026/runs/pilot_20260830_0140_seed431474/`
- Valid pre-N0: `research/icsec2026/runs/n0_pre_20260830_0205/`
- Full campaign: `research/icsec2026/runs/full_20260830_seed20260830_n30/`
- Valid post-N0: `research/icsec2026/runs/n0_post_20260830_0224/`
- Post-N0 hashes: G431 `65E9D27B36BFAECB846212D320038671D398F472BBB2ECE486429969A0F0E795`; G474 `86DE062DAB326A4D15375B55481DBEE4A607069ED586D348D612EA1244ED1311`; manifest `5681822B48FD8B210BE10F3575F932D7D6FA0A311831B5BFC735AB4EED527031`; validation `B3EF1165183D2EEBB0049B11D006A602D2EE36AE5669BD8EA5E92BA091E095F1`.
- Full campaign manifest SHA-256: `10D966EE6F43BB70EAAFA713723F9C56EEDA51757E605BEB80A8578E0ABEE67F`
- Full campaign plan SHA-256: `08BCBDD505DA95460ABFADE719411409501DE7B6F40BE648B30CB4E986F051B7`
- Full campaign results SHA-256: `770FB1FEF5BFD6B529906B35CBA67D9BAC2887DED241EA38D8CB914A157478CE`
- Full campaign validation SHA-256: `D06426EE043D32B032FA3267E7A8DDAB0AD345FD1F69807E93E9F47507BA84EB`
- Full campaign summary SHA-256: `124554F98A93639B4C2C8C18A708DC14A1D5673823A4CD2F84DB0F563083E1CA`
- SHA-256 inventory: `research/icsec2026/runs/full_20260830_seed20260830_n30/SHA256SUMS.csv`
- Inventory file SHA-256 (the inventory does not self-list): `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD`
- Provenance addendum (in progress): `research/icsec2026/provenance/20260830_023830/`
- G431 full flash: `research/icsec2026/provenance/20260830_023830/flash/g431_full_flash_0x08000000_0x20000.bin`
- G474 full flash: `research/icsec2026/provenance/20260830_023830/flash/g474_full_flash_0x08000000_0x80000.bin`
- Pre-N0 hashes: G431 `E6E89E51487EB1D7CE1D8CEF6B3BE75FD1BD48726BA8873C875E7E5C1BB527FF`; G474 `C67B72C2775689C0B0A1B7E672B23DD63F68400BBB4858264D17AC848870457A`; manifest `626E1F38687DF0514B14152B0D04CADA71A303CC43EC55A39F1BBEF7DAC88CC4`; validation `872BA8EFD5E8F3505C6DEC62AFCAAC59A892D1ED407DDE67E7256B631FBEAA12`.
- Pilot manifest SHA-256: `8C95290EC0BD3C1A647F5789678987F978753AFD56F3C7BDA6F07FBA66EA191F`
- Pilot run plan SHA-256: `A2F407916441F00747AFB54A8A053463F585D6B36A46E6CC95718BE54434DBCD`
- Pilot results SHA-256: `114816EAE253DE4F5724C65FA8B70C1F51546226E4A1B5CDD12FC848F407538B`
- Raw log SHA-256 values:
  - R001_P01 G431: `F1BF33A665CDFFAE2302F51B6708C1CF1C49CB71DD8A13C89AE1D108B0E56AC9`
  - R001_P01 G474: `74F4AF034107FFC0FFA2FD1DF5BA93940050CF71EF0DA61D52B45F17B6A28559`
  - R002_P03 G431: `D6869338ECDE939D3E9F936BA1302229A45AF0315554215B724B95DCE139A94E`
  - R002_P03 G474: `DD23A3F3A5F147D03022F3BD784661EE50C973E5AAFDD6017AFD7629A1F35037`
  - R003_P02 G431: `C1DE9CC9F74723C01C8EFA947AE0B6F5D83F70D63CA054850F2A417C32940DA7`
  - R003_P02 G474: `901A7506FB1BC33B2599838683F11FD577F621298628BE0E79E5A5A1D5407B03`
- G474 firmware image: `demo-payload/.pio/build/nucleo_g474re/firmware.bin`
- Command parser tests: `demo-payload/test/test_host_mode_command/test_main.cpp`
- Harness tests: `research/icsec2026/injector/test_run_payload_campaign.py`

## Unresolved uncertainty

- Timing uses host receipt timestamps and includes serial/OS scheduling uncertainty; no MCU clock synchronization was performed.
- Absence of `PAYLOAD_LINK_START` is not absolute reset evidence.
- No fair C0 ablation configuration was created or evaluated; the current healthy condition must be labeled N0 / Nominal Control.
- Results are sequential repeated trials on one physical board pair, not independent hardware replicates; cross-device, environmental, and long-duration generalization remain unknown.

## Deviations and anomalies

- No deviation, invalid trial, serial loss, harness error, or scope reduction occurred during the approved pre-N0, 90-trial campaign, or post-N0 sequence.
- Earlier in the session, direct PlatformIO upload selected incompatible `hla_swd`; the repository flash helper selected `swd` and verified the programmed image. This preceded the dataset sequence.
- Earlier in the session, one ad hoc link sampler had an unbounded loop and was terminated by verified PID. It produced no campaign artifact and preceded pre-N0.

## Interpretation

### Observed

- Both 65-second N0 controls met all acceptance criteria.
- All 90 seeded randomized trials were valid and retained; all activations, detections, restorations, and recoveries were observed in the logs.
- OFFLINE occurred in every trial under the configured four-second observation duration, including BAD_CRC, though OFFLINE was not required for BAD_CRC detection.
- No post-injection `PAYLOAD_LINK_START` marker appeared.

### Supported inference

- For this board pair, firmware, wiring, host, and experiment timing, each injected payload behavior consistently produced its predefined G431 log detector evidence and a later logged recovery after confirmed NORMAL restoration.
- The pre/post N0 logs support nominal stability during the two observed control windows.
- The dataset supports the reported host-observed proportions, exact intervals, and latency distributions under the stated measurement definitions.

### Unknown / not supported

- Marker absence does not prove the MCU never reset.
- Literal `heartbeat=OK watchdog=OK` strings do not independently establish heartbeat/watchdog health.
- Host timestamps do not establish MCU-internal timing.
- The dataset does not establish independent-device replication or general behavior outside this setup.
- No C0 ablation claim is supported.

## Current blocker

None. Full flash captures and binary comparisons completed without readout protection or ambiguous probe selection.

## Next engineering action

Freeze exact source state and toolchain/dependency versions, then finalize the provenance interpretation and independent inventory.

## HUMAN ACTION REQUIRED

None at this milestone.
