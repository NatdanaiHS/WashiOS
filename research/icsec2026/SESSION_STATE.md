# ICSEC 2026 Hardware Experiment Session State

Last updated: 2026-08-30T09:53:00+07:00

## Objective

Complete Scientific Review Revision v2 as a compiled 4–6 page, double-anonymous IEEE manuscript centered on activation-confirmed dual-channel HIL fault injection, with statistically valid one-pair language, verified primary-source positioning, audited claims/anonymity, rendered-page QA, and unchanged frozen campaign/provenance artifacts.

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
- Completed the append-only provenance addendum with full user-flash images, exact comparison reports, clean rebuild outputs/logs, frozen source-state bundle, toolchain records, flash-layout inventories, and an independent provenance SHA-256 inventory.
- G431 firmware and manuscript files have not been modified.
- Added `research/icsec2026/paper/` with the locked research questions, contribution boundary, acceptance-risk screening, claim–evidence matrix, evaluation method, results, and limitations.
- Added a deterministic manuscript-table generator that refuses to run unless the frozen campaign summary/validation and both N0 validation files match their approved SHA-256 values.
- Generated machine-readable N0, fault-outcome, and latency tables plus a table provenance record containing input, generator, and output hashes.
- No existing manuscript template was present, so no manuscript file was edited; the new files are evidence-locked section artifacts.
- Added `research/icsec2026/manuscript/main.tex` using the IEEEtran conference class, with an empty author block and no acknowledgments or author-revealing artifact URL.
- Added `references.bib` with seven DOI-verified primary sources covering fault-injection methodology/tooling, HIL fault injection, and the exact binomial interval.
- Added `SUBMISSION_REQUIREMENTS.md`, recording the official submission/schedule URLs, access date, four-to-six-page and double-anonymous requirements, and the official schedule page's conflicting older/later date blocks.
- Compiled `main.pdf` with Tectonic 0.17.0, IEEEtran, IEEEtran bibliography style, and embedded Times-compatible TeX Gyre Termes document fonts.
- Added `ANONYMITY_CLAIM_AUDIT.md` and retained final build, PDF structure, extracted-text, and four-page rendered QA evidence under `research/icsec2026/manuscript/`.
- Revised the anonymous manuscript to Scientific Review v2: removed Clopper–Pearson claims/values and its bibliography entry, retained observed 30/30 counts/proportions, and explicitly states that device-population uncertainty cannot be estimated from one board pair.
- Reframed the title, abstract, contributions, method, discussion, and conclusion around activation-confirmed dual-channel HIL fault injection; evidence locking remains reproducibility support.
- Added a full-width system/protocol figure showing host orchestration, independent OBS C/OBS P channels, injection/restoration confirmations, detector observation, and recovery observation.
- Added verified recent/closest primary work on automotive HIL fault injection and nanosatellite/CubeSat communication testing, plus a bounded related-work comparison table.
- Replaced the interrupting full-width latency float with a single-column table adjacent to RQ3, preserving all frozen median, quartile, IQR, minimum, and maximum values.
- Added `manuscript/SCIENTIFIC_REVIEW_V2.md` and `manuscript/qa/RENDERED_PAGE_QA_V2.md`; updated `ANONYMITY_CLAIM_AUDIT.md`, final build log, PDF structure record, and all four final page renders.
- Final v2 PDF is four letter-size IEEE pages. Build audit found zero overfull boxes, undefined citations/references, or compile errors; visual QA found no clipping, overlap, unreadable label, interrupting conclusion/reference float, or avoidable half-page whitespace.
- Independent final inventory verification resolved all workspace-relative paths and found zero missing, size-mismatched, or hash-mismatched files across 195 frozen dataset rows and 65 frozen provenance rows.
- V2 hashes: `main.tex` `F3181650C86E43848041D1CC27DE08E4DE3E9F65A63F6A5A9F6A5711D3E2EA98`; `references.bib` `952AC1A9B2BDA81A57F001442DE955051F650BB84DB135E1EC1D608198E18A10`; `main.pdf` `992A1C9AA41F4295BF7F97CA081D79A7DE2ABBB4B419B2A0B82144C1B50928DF`.

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
python provenance/.../collect_toolchain.py
python provenance/.../collect_package_lists_utf8.py
python provenance/.../freeze_source_state.py
python provenance/.../analyze_flash_region.py for G431 gap/after-app and G474 after-app regions
python provenance/.../collect_selected_toolchain.py for exact versioned 1.70201.0 compiler directory
python research/icsec2026/injector/create_sha256_inventory.py --output provenance/20260830_023830/PROVENANCE_SHA256SUMS.csv --include provenance/20260830_023830
Independent PowerShell verification of all 65 provenance inventory rows
Independent PowerShell re-verification of all 195 original dataset inventory rows
Get-FileHash for original and provenance inventories
git diff --check
git status --short --branch
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
rg --files research/icsec2026 for manuscript/paper/template and evidence schemas
python research/icsec2026/paper/generate_manuscript_tables.py
python -m py_compile research/icsec2026/paper/generate_manuscript_tables.py
rg acceptance-risk phrases and numeric statements across research/icsec2026/paper
Get-FileHash for the original dataset and provenance inventories
Open official ICSEC 2026 submission and schedule pages and record access-date requirements
Verify seven related-work records against primary papers and publisher/Crossref DOI metadata
Download and version-check Tectonic 0.17.0 in `tmp/pdfs/` for local compilation
tectonic main.tex --keep-logs --keep-intermediates
pdfinfo main.pdf
pdftoppm -png -r 144 main.pdf qa/page
pdfplumber/pypdf page, font, metadata, annotation, attachment, and text extraction checks
Mechanical citation-key, frozen-value projection, risk-phrase, and identity-string audits
Get-FileHash for manuscript deliverables and unchanged dataset/provenance inventories
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
- G431 unattributed `0x08000FC0–0x08003FFF` contains one non-`0xFF` range at `0x08001000–0x08003FFF` (12,288 bytes); it is preserved without attribution. G431 bytes after the emitted application through `0x0801FFFF` are all `0xFF`.
- G474 bytes after the packaged application through `0x0807FFFF` include 30,101 non-`0xFF` bytes in 516 ranges; they are preserved without attribution or runtime interpretation.
- Frozen source state records branch `monorepo-migration`, commit `ae891a70ca961d247b5fd5ac487271caf2fc881f`, binary tracked worktree patch, staged patch, complete porcelain status, tracked path list, and 13 selected untracked experiment source/test copies with hashes. Raw datasets are referenced, not duplicated.
- Toolchain records include PlatformIO Core 6.1.19 (internal Python 3.11.7), `ststm32` 19.6.0, STM32Cube G4 1.6.1, OpenOCD 0.12.0+dev, experiment Python 3.12.10, pip 25.0.1, and pyserial 3.5.
- Both G431 clean build logs selected versioned package `toolchain-gccarmnoneeabi@1.70201.0`; the exact GCC/G++ 7.2.1 and objcopy 2.29.51 executables and package metadata were independently versioned and hashed. A generic installed GCC 12.3.1 directory was recorded but is explicitly not attributed to these builds.
- Initial PlatformIO package-list capture returned three CP1252 Unicode rendering failures. Repeating the unchanged commands with `PYTHONIOENCODING=utf-8` succeeded for core, bootloader, and demo-payload; both failure and successful records are preserved.
- `PROVENANCE_SHA256SUMS.csv` contains 65 addendum artifacts and independently verifies with zero missing, size-mismatched, or hash-mismatched rows.
- Provenance inventory SHA-256 (inventory does not self-list): `84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC`.
- After all provenance work, the original dataset inventory remains SHA-256 `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD`, and all 195 original rows independently re-verify with zero mismatches.
- Evidence-Locked Paper Scope is fixed to three descriptive RQs: nominal N0 behavior, predefined fault detection/recovery outcomes, and host-observed command-to-marker latency distributions.
- `PAPER_DIRECTION.md`, `CLAIM_EVIDENCE_MATRIX.md`, `EVALUATION_METHOD.md`, `RESULTS.md`, and `LIMITATIONS.md` were created under `research/icsec2026/paper/`.
- All manuscript-table rows were regenerated after exact source-hash verification; `TABLE_PROVENANCE.json` records the deterministic derivation and SHA-256 of every generated CSV.
- Acceptance-risk screening explicitly removes C0/comparative-superiority, independent reliability, MCU-internal timing, reset-proof, heartbeat/watchdog, radiation/environmental, flight-qualification, long-duration, and broad integrated-system claims.
- No hardware operation, acquisition, flash readback, protection change, board reflash, campaign run, hypothesis test, or frozen-artifact edit was performed during the paper-scope milestone.
- At the paper-scope checkpoint, the original dataset inventory remains `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD` and the provenance inventory remains `84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC`.
- Independent final re-hashing verified all 195 frozen dataset inventory rows and all 65 provenance inventory rows with zero missing files, size mismatches, or hash mismatches.
- Official submission guidance was rechecked on 2026-08-30: English IEEE two-column regular papers must be 4–6 pages and double anonymous. The later `Important Dates` block lists the second/final-round deadline as 5 September 2026; an older conflicting block remains visible and is documented for final human recheck.
- Anonymous Submission Draft v1 compiles successfully to exactly four letter-size IEEE two-column pages, including references.
- Final PDF visual inspection covered all four 144-dpi page renders; no overlap, clipping, broken table, unreadable label, or unbalanced final reference column remained.
- Final build contains no overfull box, undefined citation/reference, fatal error, or compile error. Three underfull line-breaking notices were visually cleared as non-defects.
- The final PDF embeds TeX Gyre Termes regular/bold/italic/bold-italic document fonts and standard mathematical symbol fonts; no missing glyph was observed.
- PDF `/Author` metadata is absent; no author/affiliation/email/acknowledgment, local username/path, author-revealing URL, external URI annotation, or attachment is present.
- Seven cited keys exactly match seven bibliography entries. Each title/authors/venue/year/pages/DOI and the related-work statement it supports were checked against the primary paper or official publisher metadata.
- Quantitative projection assertions passed for the two N0 rows, three fault-outcome rows, and six latency rows. No frozen value was changed.
- Acceptance-risk scanning found C0 superiority, reset, environmental/radiation, qualification, and complete-system terms only in explicit negations/limitations; no unsupported positive claim was found.
- Draft SHA-256 values: `main.tex` `4311B9AA2AA76CDD91816253307DBAE246AAC4FF2ABE92774B35C4790500EF24`; `references.bib` `AA50FF3F59333E0ACCC0D8E939E359C3FA79FD48A01493321DC84325613F6E87`; `main.pdf` `D44160C1958DB3D771D76A288F204CA62B6A353DD93B08B0415F3C3E71E49430`; requirements `9F3381B12F95CBF0367DB4CCE7CD2CB78BE1C700CD4496718F9C192A8486CFE3`; audit `4FE0BA19F8C1EE4EE472F48C4443EA269219C8819680832CABC4F2D74751847A`.
- The frozen dataset and provenance inventory hashes remain unchanged at `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD` and `84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC`, respectively.

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
- Provenance report: `research/icsec2026/provenance/20260830_023830/PROVENANCE.md`
- Provenance inventory: `research/icsec2026/provenance/20260830_023830/PROVENANCE_SHA256SUMS.csv`
- Provenance inventory SHA-256: `84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC`
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
- Flash captures cover internal user flash only; option bytes, OTP, system ROM, RAM, and peripheral state were not captured.
- Non-`0xFF` bytes outside attributed emitted binary ranges are preserved but their origin and runtime relevance are unknown.
- Debug attachment transiently halted and resumed each CPU; no flash/protection/reset operation occurred, but execution was briefly paused for acquisition.

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
- The dataset supports the reported host-observed proportions and latency distributions under the stated measurement definitions. Frozen interval fields remain unchanged in the source summary but are intentionally excluded from manuscript v2 because one sequential board pair does not justify a device-population sampling model.

### Unknown / not supported

- Marker absence does not prove the MCU never reset.
- Literal `heartbeat=OK watchdog=OK` strings do not independently establish heartbeat/watchdog health.
- Host timestamps do not establish MCU-internal timing.
- The dataset does not establish independent-device replication or general behavior outside this setup.
- No C0 ablation claim is supported.

## Provenance interpretation

### Exact matches

- Frozen packaged G474 application equals the identified G474 readback region byte-for-byte.
- Clean rebuilt G431 payload-demo application equals the identified G431 application region byte-for-byte.
- Clean rebuilt matching G431 bootloader equals the identified G431 bootloader region byte-for-byte.
- Both full user-flash images have exact identity, address-range, byte-count, and SHA-256 records.

### Supported linkage

- The G474 dataset binary is directly linked to the acquired G474 application bytes by exact comparison.
- The acquired G431 application and bootloader are linked to the frozen repository/source state and exact selected toolchain by clean rebuild plus exact comparison.
- The provenance addendum references the unchanged original dataset through its original verified inventory.

### Unresolved provenance

- Unattributed flash regions outside emitted binaries remain preserved but unexplained.
- External framework/toolchain trees are not fully vendored; package metadata, versions, paths, build logs, and executable hashes are frozen instead.
- User-flash equality does not describe option bytes, OTP, system ROM, or runtime volatile state.

## Current blocker

None. SCIENTIFIC_REVIEW_V2_COMPLETE.

## Next engineering action

SCIENTIFIC_REVIEW_V2_COMPLETE. Await review of the v2 checkpoint package; hardware acquisition and frozen evidence remain closed.

## HUMAN ACTION REQUIRED

None at this milestone.

---

## Lab extension session (2026-08-30)

Last updated: 2026-08-30T20:14:00+07:00

- Active branch: `experiment/icsec-extension-20260830`
- Frozen base/current source commit before extension edits: `8a47d070c549274c59cdbde2495afa8d353a93b3`
- Initial working tree: director-owned modified `research/icsec2026/NEXT_TASK.md` and untracked `research/icsec2026/LAB_EXTENSION_BRIEF.md`; no other changes.
- Frozen dataset: `research/icsec2026/runs/full_20260830_seed20260830_n30/`; inventory SHA-256 reverified as `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD`.
- Frozen provenance: `research/icsec2026/provenance/20260830_023830/`; inventory SHA-256 reverified as `84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC`.
- Frozen manuscript: `research/icsec2026/manuscript/`; unchanged.
- Extension objective: primary G431-A/G474-A nominal, interleaved delay/NC, and two-exposure BAD_CRC package under `research/icsec2026/extension/`.
- Readiness finding: frozen G474 responder implements only fixed 250 ms `MODE DELAYED` and cannot confirm an exact requested delay. Minimal extension implementation is in progress to accept `MODE DELAYED <ms>` and emit `MODE=DELAYED delay_ms=<ms>`.
- Modified extension files: `demo-payload/src/HostModeCommandParser.hpp`, `demo-payload/src/main.cpp`, `demo-payload/test/test_host_mode_command/test_main.cpp`, and `core/src/app/PayloadLinkTask.hpp`; new extension harness/tests under `research/icsec2026/extension/`.
- Validation: native command-parser tests pass 3/3 after exact-delay support; extension host tests pass 3/3; legacy injector host tests pass 11/11; core native/SITL tests pass 38/38; G474 responder, G431 payload-demo application, and matched G431 bootloader builds pass.
- Hardware enumeration at 20:05 +07: no ST-LINK virtual COM ports present; COM3/COM4/COM5/COM7 are Bluetooth serial ports. Previously recorded board identities/ports are historical and will not be reused without fresh enumeration.
- Hardware identity intended by methodology: G431-A ST-LINK `005100243032511537333436`; G474-A ST-LINK `0041003D3234510F37333934`; fresh confirmation pending connection.
- Extension G474 firmware: 8,944 bytes, SHA-256 `5581492429080BD58177A37733981ABA12DA6074BA40EAC0157B86E027B479E7`.
- Extension G431 application: 20,256 bytes, SHA-256 `6515796C07D37C19E21B0104B477EA4C6451B66A995EBEF6510725764441E727`.
- Matched G431 bootloader: SHA-256 `FE591BF7292AD0D40F8FEE4AF5779118AE0D0083FF362F5BE9CCB156ADFE619E`.
- Precommitted plan: seed `20260830`, five blocks, 45 rows (35 delay and 10 NC), all seven delays per block, nonadjacent NC, at most four intervening delay trials. Plan SHA-256 `24AD8C20778472BFFC644557D2284D15A481804A1820BDA05A1827D3C88EBBDE`.
- Prepared extension evidence path: `research/icsec2026/extension/evidence/primary_20260830_seed20260830_b5/`.
- Completed experiments: none yet; no hardware was connected or flashed during readiness work.
- Readiness milestone commit: `4a522eb2f1a8abb6b6599964ae4a0cf5e9db2939`; working tree verified clean immediately afterward.
- Current physical blocker: no ST-LINK device or ST-LINK virtual COM port is enumerated. Both intended boards must be connected with the specified UART wiring before exact-identity flashing and acquisition can proceed.

### Acquisition update (2026-08-30T20:45:00+07:00)

- Fresh enumeration mapped G431-A ST-LINK `005100243032511537333436` to COM8 and G474-A ST-LINK `0041003D3234510F37333934` to COM9.
- Exact-serial OpenOCD flashes verified G474 application `5581492429080BD58177A37733981ABA12DA6074BA40EAC0157B86E027B479E7`, G431 application `6515796C07D37C19E21B0104B477EA4C6451B66A995EBEF6510725764441E727`, and matched G431 bootloader `FE591BF7292AD0D40F8FEE4AF5779118AE0D0083FF362F5BE9CCB156ADFE619E`.
- Retained preflight `PREFLIGHT_FLASH_CHECK` passed exact 90 ms activation, G431 accepted-response instrumentation, confirmed NORMAL restoration, and stabilization. A prior invocation failed before serial open because pyserial was absent; that software-only failure is retained in the manifest.
- `NOMINAL_001` retained as invalid: G431 captured the full stable interval, but G474 capture ended with `ClearCommError` and final NORMAL write failure. No campaign row followed this attempt.
- Retained post-failure serial-reopen diagnostic passed. `NOMINAL_002` then passed: 605.0 s, 121 ONLINE status records, strictly increasing `ok`, zero timeout/CRC/sequence/recovery deltas, and zero prohibited markers. Evidence: `research/icsec2026/extension/evidence/primary_20260830_seed20260830_b5/nominal_validation_002.json` and `raw/nominal/NOMINAL_002/`.
- Campaign `R001_B1_D110` completed valid with exact 110 ms activation, one accepted-response marker, two timeout markers, one sequence rejection, OFFLINE, confirmed NORMAL restoration, and passed post-stabilization.
- Campaign stopped at retained `R002_B1_D500`: exact 500 ms activation succeeded, then the blocking payload response handler continuously drained queued poll requests and starved host-command processing. NORMAL restore was sent but never confirmed; controller remained OFFLINE. No row after R002 was started.
- Evidence: `research/icsec2026/extension/evidence/primary_20260830_seed20260830_b5/campaign_results.json`, `raw/campaign/R001_B1_D110/`, and `raw/campaign/R002_B1_D500/`.
- Scientific conflict: the implemented 500 ms condition cannot meet the mandated restoration/stabilization methodology without changing payload scheduling behavior (for example, servicing at most one link frame before returning to host commands) or changing the condition set. Acquisition is stopped pending Research Director direction; the invalid attempt will not be deleted or replaced.
- Research review decision: scope down to blocks 1-3 and serviceable delays 50, 90, 100, 110, 150, and 250 ms; retain R002 invalid without retry; omit unstarted R011/R021 500 ms rows; carry valid R001; run all other original rows through R027 and both BAD_CRC exposures without changing firmware.
- Append-only amended plan: `research/icsec2026/extension/evidence/primary_20260830_seed20260830_b5/amended_execution_plan.csv`, SHA-256 `3556D9902DD28DCA8FB86D504AFD5FF3A6C49CC01C49AB6B4FF476E92AFCF0CF`; linked original plan SHA-256 `24AD8C20778472BFFC644557D2284D15A481804A1820BDA05A1827D3C88EBBDE`.
- R002 locked raw hashes reverified: G431 `08022AE828B5AF1715BF9991FBCF8DF2B9D399263B90B64F131F2720D732EDF3`; G474 `3062DA9486CE630E4821D075464766DFDFE863576288C3C4469F7F6A1F7E130D`.

### Scope-down completion (2026-08-30T21:09:00+07:00)

- Pre-acquisition reviewed-plan commit: `cfd4b1b59d5018f498e5cc083ab27e1d230ae85d`.
- Exceptional recovery: one exact-serial G474-A-only reset; OpenOCD exit 0, payload READY/NORMAL confirmed, G431 `PAYLOAD_RECOVERED recoveries=2` observed, no G431 link-start marker, and stabilization passed with `ok` 3018→3028 and zero counter deltas. G431-A was not reset.
- Continuation completed all 23 amended planned rows in original relative order with zero invalid rows or serial failures. Together with carried R001, the valid campaign contains 24 rows: three observations at each serviceable delay 50/90/100/110/150/250 ms and six NC observations.
- Delay outcomes: 50 and 90 ms had accepted delayed responses in 3/3 with no timeout/sequence rejection/OFFLINE; 100, 110, 150, and 250 ms had timeout, sequence rejection, and OFFLINE in 3/3, followed by confirmed restoration and recovery in 3/3. These are descriptive observations on one board pair.
- All six NC rows had zero false CRC/sequence rejection, timeout, OFFLINE, recovery, restart, or poll-write-failure markers.
- SHORT BAD_CRC: confirmed CRC rejection, then timeout consecutive=1, no OFFLINE, confirmed NORMAL restoration, and passed stabilization.
- SUSTAINED BAD_CRC: confirmed CRC rejection → timeout consecutive=1 → timeout consecutive=2 → OFFLINE consecutive=3, followed by confirmed NORMAL, recovery, and passed stabilization.
- Final accounting: 45 original-plan rows; 25 attempted; 24 valid; one invalid retained R002; 20 review-removed rows (R011/R021 plus blocks 4–5). R002 was not retried and is excluded from valid denominators.
- Machine validation: `final_validation.json` valid=true, zero failures, zero raw-log format failures; nominal, recovery, campaign, BAD_CRC, plan, firmware, R002, partial-inventory, and frozen-inventory checks all pass.
- Frozen dataset/provenance hashes remain `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD` and `84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC`.
- Final evidence path: `research/icsec2026/extension/evidence/primary_20260830_seed20260830_b5/`.
- Last confirmed payload state: NORMAL with passed post-SUSTAINED stabilization gate.
- Complete extension inventory: 88 artifacts, independently verified with zero missing, size, or hash mismatches. `EXTENSION_SHA256SUMS.csv` SHA-256 `8B4CB2AB87CD317905AA4A219B81E99E2E459DC3EEF386D14286297476177C0B` (inventory excludes itself).
- Final host validation: extension tests 4/4 and legacy injector tests 11/11 pass; `git diff --check` reports no whitespace errors.
- Remaining actions: commit frozen extension evidence, exact-copy backup, and independent backup verification. No further acquisition is authorized for this milestone.
- Frozen extension evidence commit: `fa20d3805b4aa3744b7e64f627e2c2426ba0d231`.
- Exact-copy backup completed at `C:/WashiOS-extension-backup/primary_20260830_seed20260830_b5`. The copied inventory SHA-256 equals the source (`8B4CB2AB87CD317905AA4A219B81E99E2E459DC3EEF386D14286297476177C0B`), and all 88 copied rows independently verify with zero missing, size, or hash mismatches.
- Primary reviewed scope-down milestone is scientifically complete. No unresolved scientific question blocks this evidence package; the invalid 500 ms attempt and initial nominal serial failure remain explicit retained limitations.
- Next action: WORK_REVIEW_REQUIRED. Do not begin G431-B, oscilloscope, F411, or manuscript work in this milestone.
- Unresolved uncertainty: remaining lab-access time was not supplied; acquisition will use the five-block plan unless the director-defined time rule forces the three-block scope-down.
- Evidence-readiness finding: the 4 s trial window is shorter than the controller's 5 s aggregate status period. Minimal extension-only G431 instrumentation now emits `PAYLOAD_ACCEPTED seq=<n> mode=<n>` after each accepted response so accepted responses are directly attributable without inferring success from marker absence.
- Next action: finish host tests and both firmware builds, precommit the seeded plan, then request only the physical board connection needed for flashing/acquisition.

### G431-B replication readiness (2026-08-30T21:23:04+07:00)

- Research review passed the primary scope-down milestone and authorized the bounded G431-B/G474-A replication in the current `NEXT_TASK.md`.
- Active branch: `experiment/icsec-extension-20260830`; readiness starting commit: `45080a894fb6e18b178ac818e1ad03ae9024fdc6`; frozen base `8a47d070c549274c59cdbde2495afa8d353a93b3` remains an ancestor.
- Initial working tree contained only the Research Director's modified `research/icsec2026/NEXT_TASK.md`; this change is preserved.
- Frozen dataset inventory reverified as `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD`; frozen provenance inventory reverified as `84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC`; reviewed primary inventory reverified as `8B4CB2AB87CD317905AA4A219B81E99E2E459DC3EEF386D14286297476177C0B`.
- The primary sustained BAD_CRC derived field `offline_before_restore=false` is prohibited from citation. The accepted evidence is the ordered raw marker sequence and harness control flow that waited for `PAYLOAD_OFFLINE consecutive=3` before restore.
- Added `research/icsec2026/extension/run_g431b_replication.py` and its host tests. It reuses the primary exact-byte dual-channel capture, exact activation confirmation, four-second observation, restoration, and stabilization implementations; no firmware semantics were changed.
- Replication host suite passes 6/6 including the four existing primary tests. Python compilation and `git diff --check` pass.
- Precommitted exclusive evidence package: `research/icsec2026/extension/evidence/replication_g431b_20260830_seed20260830_b3/`.
- Precommitted plan seed: `20260830`; 3 randomized blocks; one NC and one each of 90/100/110 ms per block; 12 rows; plan SHA-256 `D631AC024CA033EA47FA340921549D56FA845A79784599D14938225015E6A901`.
- Firmware candidates are unchanged and hash-identical to the reviewed primary: G431 application `6515796C07D37C19E21B0104B477EA4C6451B66A995EBEF6510725764441E727`; G431 bootloader `FE591BF7292AD0D40F8FEE4AF5779118AE0D0083FF362F5BE9CCB156ADFE619E`; G474 payload `5581492429080BD58177A37733981ABA12DA6074BA40EAC0157B86E027B479E7`.
- Current fresh enumeration still identifies G431-A ST-LINK `005100243032511537333436` on COM8 and G474-A ST-LINK `0041003D3234510F37333934` on COM9. G431-B is not connected, so no replication acquisition has started.
- Hardware identity/configuration: pending fresh enumeration of G431-B after the physical swap; G474-A remains exact serial `0041003D3234510F37333934`; prescribed UART wiring remains G431 PC4 TX to G474 PC5 RX, G431 PC5 RX from G474 PC4 TX, common GND, 115200 8N1.
- Completed replication experiments: none. Evidence currently contains only the locked plan/configuration/manifest; no observation row has been attempted.
- Remaining time: not supplied. Per `NEXT_TASK.md`, acquisition will not start unless all 12 observations plus evidence freeze can be completed.
- Next action: commit replication readiness, then physically replace G431-A with G431-B while retaining G474-A and the same UART wiring; freshly enumerate exact identities/ports before exact-target flashing.

### G431-B replication acquisition and freeze (2026-08-30T21:33:50+07:00)

- Fresh USB-parent enumeration identified G431-B as ST-LINK `0029002B3032511537333436` on COM10 and independently reconfirmed the same G474-A as ST-LINK `0041003D3234510F37333934` on COM9. Identity was not inferred from port number.
- Exact-target OpenOCD flashing verified G431-B application `6515796C07D37C19E21B0104B477EA4C6451B66A995EBEF6510725764441E727` at `0x08004000` and bootloader `FE591BF7292AD0D40F8FEE4AF5779118AE0D0083FF362F5BE9CCB156ADFE619E` at `0x08000000`; raw flash logs are retained. G474-A firmware was unchanged at `5581492429080BD58177A37733981ABA12DA6074BA40EAC0157B86E027B479E7`.
- Acquisition source commit: `2da2d11194307afac974b58aa6e780d456ff53fa`; source status at acquisition was clean. No routine per-trial MCU reset was performed.
- Readiness gate passed: fresh G474 NORMAL, G431-B ONLINE, `ok` 30 to 40, zero timeout/CRC/sequence/recovery deltas, and no prohibited marker.
- The exact precommitted plan SHA-256 `D631AC024CA033EA47FA340921549D56FA845A79784599D14938225015E6A901` completed in order: 12 attempted, 12 valid, zero invalid, zero omitted, zero replacement.
- All three NC observations had zero false CRC/sequence rejection, timeout, OFFLINE, recovery, restart, or poll-write-failure markers.
- At 90 ms, all three G431-B observations had accepted delayed responses and no timeout, sequence rejection, OFFLINE, or recovery; all three restored and stabilized.
- At 100 ms and 110 ms, all three observations at each delay had timeout, sequence rejection, and OFFLINE, followed by confirmed NORMAL restoration, recovery, and passed stabilization; no delayed response was accepted.
- Cross-controller comparison matches the reviewed G431-A all/none outcome pattern for accepted response, timeout, sequence rejection, OFFLINE, restoration, and recovery at 90/100/110 ms. The supported claim is only selected-observation reproduction on a second physical G431 controller using the same G474-A, not an independent board pair or population estimate.
- Final payload state: fresh NORMAL confirmation after the final valid post-stabilization gate. No serial-integrity, activation, restoration, stabilization, or unexpected-outcome failure occurred.
- Machine validation: `final_validation.json` valid=true, zero failures and zero raw-log failures. Exact-byte plus readable G431-B/G474-A logs exist for every row.
- Evidence path: `research/icsec2026/extension/evidence/replication_g431b_20260830_seed20260830_b3/`.
- Complete replication inventory: 42 artifacts, independently verified with zero missing, size, or SHA-256 mismatches; inventory SHA-256 `F13EBB7FEB42FB3F67E56A8503CB6D70A5F630F2C864A16B22D5BF4D9D19CCE9` (inventory excludes itself).
- Frozen dataset, frozen provenance, and reviewed primary inventory hashes remain unchanged at `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD`, `84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC`, and `8B4CB2AB87CD317905AA4A219B81E99E2E459DC3EEF386D14286297476177C0B`.
- Completed experiments: the entire authorized 12-observation replication milestone. Unresolved uncertainty: none blocks this package; shared G474-A and sequential-controller limits remain explicit.
- Remaining time: not supplied. Next action: commit the frozen replication evidence, make the planned exact-copy backup, independently verify every copied inventory row, then stop for work review.
