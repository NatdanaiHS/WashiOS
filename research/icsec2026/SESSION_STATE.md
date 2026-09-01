# ICSEC 2026 Hardware Experiment Session State

Last updated: 2026-09-01T19:38:55+07:00

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
- Frozen replication evidence commit: `0f77fec1eb35e482fa27e932d3b22224edd6607c`.
- Exact-copy backup completed at `C:/WashiOS-extension-backup/replication_g431b_20260830_seed20260830_b3`. Source and backup inventory SHA-256 values both equal `F13EBB7FEB42FB3F67E56A8503CB6D70A5F630F2C864A16B22D5BF4D9D19CCE9`; all 42 inventoried rows independently verify with zero missing, size, or hash mismatches (43 total files including the inventory).
- Replication milestone is scientifically complete. Next action: WORK_REVIEW_REQUIRED; do not begin oscilloscope, F411, manuscript, or additional acquisition work under this milestone.

### Oscilloscope stretch readiness (2026-08-30T21:45:45+07:00)

- Research review passed the G431-B/G474-A replication milestone and authorized only the time-boxed 110 ms oscilloscope stretch in the current `NEXT_TASK.md`.
- Active branch: `experiment/icsec-extension-20260830`; starting commit `14ec248df36be885cb58f50458a74861e81ecca6`; frozen base remains an ancestor. Initial worktree contained only the Research Director's modified `research/icsec2026/NEXT_TASK.md`.
- Frozen dataset, provenance, primary-extension, and replication inventory hashes reverified unchanged as `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD`, `84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC`, `8B4CB2AB87CD317905AA4A219B81E99E2E459DC3EEF386D14286297476177C0B`, and `F13EBB7FEB42FB3F67E56A8503CB6D70A5F630F2C864A16B22D5BF4D9D19CCE9`.
- Endpoint definitions are locked before observation: CH1 is G474-A PA8 / NUCLEO D7 rising immediately before the configured 110 ms delay after a valid decoded poll; CH2 is G431-B PA8 / NUCLEO D7 rising immediately after `PayloadLinkController::service()` increments the first timeout count and before timeout serial logging. CH1 remains high for the delay; a valid same-exchange CH2 edge must occur within that CH1 high pulse. Poll period remains 500 ms.
- Instrumentation only adds GPIO writes and separate build environments. It does not change the 100 ms deadline, 500 ms poll cadence, UART protocol, delayed-response scheduling, link-state logic, or serial markers.
- Core native/SITL tests pass 38/38; payload parser tests pass 3/3; instrumented G474, G431 application, and matched bootloader builds pass.
- Instrumented firmware hashes: G474 payload `9718A3B7080162235E27D6A2A8333DFF6F631C667D50E0AB90DC53749CEE917D` (8,980 bytes); G431-B application `9F5B0041A7939468ED20736E0FDA2659FF90A106CC9C08610C0272CBE0FABC0A` (20,344 bytes); matched G431-B bootloader `7C36C0CBDEFECB31ABBD857B15E2AA28D7CBBDF5FBF5B4629666B13F23F716F2` (4,032 bytes).
- Exclusive evidence package: `research/icsec2026/extension/evidence/scope_g431b_g474a_110ms_20260830/`; precommitted five-trace plan SHA-256 `F5145A7732882F6BA8450356E0C1FDD9D0074015D69244B552B65BBA82F59B5F`.
- Scope bring-up time box started during instrumentation work and remains within the 20-minute limit at this checkpoint. No scope acquisition or serial capture has started.
- Hardware identities remain G431-B ST-LINK `0029002B3032511537333436` on COM10 and G474-A ST-LINK `0041003D3234510F37333934` on COM9, pending fresh recheck before flashing.
- Remaining time: not supplied. The milestone will be dropped if both clean edges are not established within the bring-up box or if fewer than 40 minutes remain before evidence freeze.
- Next action: commit the locked instrumentation/protocol, flash exact instrumented targets, validate serial behavior, then request human probe placement and scope settings/capture only.

### Oscilloscope feasibility outcome (2026-08-30T22:31:13+07:00)

- Exact identities reverified before flashing: G431-B `0029002B3032511537333436` / COM10 and G474-A `0041003D3234510F37333934` / COM9. All three instrumented images were exact-target flashed and OpenOCD-verified; raw flash logs are retained.
- Human setup: Hantek DSO4254C; CH1 G474-A D7/PA8, CH2 G431-B D7/PA8, shared ground, 10X probes, DC coupling, 1 V/div both channels, 20 ms/div, CH1 rising trigger at 1.64 V, SINGLE mode, 32K memory, actual 12.50 kSa/s (80 us sample interval). Both channels were initially LOW.
- S001_D110 completed with exact 110 ms activation, attributable dual serial logs, confirmed NORMAL restoration, and passed pre/post stabilization. Serial outcome matched the prior 110 ms observations: timeout, sequence rejection, OFFLINE, then recovery.
- Human reported CH1 rising first and CH2 rising while CH1 remained high, with both edges apparently clean and attributable to one pulse. The scope saved Wave(Binary) to internal slot No.1.
- No USB drive was available, so no native waveform, CSV, or scope screenshot entered the evidence package. No interval was extracted or manually estimated; the internal record and human observation are feasibility support only, not machine-readable timing evidence.
- Under the hard lab-stop constraint and `NEXT_TASK.md` stop rule, quantitative acquisition was dropped after S001. S002-S005 were not attempted; accounting is 5 planned, 1 attempted/serial-valid, 0 valid timing traces, 4 dropped unattempted. No row was replaced or retried.
- Last confirmed payload state: NORMAL with passed post-S001 stabilization gate.
- Prior frozen dataset, provenance, primary-extension, and G431-B replication inventories remain unchanged.
- Completed experiment: bounded GPIO-edge feasibility only. Unresolved uncertainty: the internal Wave(Binary) record is not independently verifiable unless later exported; no quantitative timing claim is supported.
- Next action: freeze, inventory, commit, and back up this clearly labeled feasibility package; no additional hardware acquisition is authorized under the hard lab stop.
- Feasibility package inventory contains 19 artifacts and independently verifies with zero missing, size, or SHA-256 mismatches. `SCOPE_FEASIBILITY_SHA256SUMS.csv` SHA-256 is `519E7E142DFAFEA4736CA74D945B3197D106714F9B6B1A6B45C75309EC4B1B0E` (inventory excludes itself).
- Frozen feasibility evidence commit: `d7205914745688a781d8aed5199eb5306965216e`.
- Exact-copy backup completed at `C:/WashiOS-extension-backup/scope_g431b_g474a_110ms_20260830`; all 19 inventory rows independently verify with zero issues (20 total files including inventory), and source/backup inventory hashes both equal `519E7E142DFAFEA4736CA74D945B3197D106714F9B6B1A6B45C75309EC4B1B0E`.
- Oscilloscope stretch is complete as a dropped quantitative milestone with retained feasibility evidence only. Next action: WORK_REVIEW_REQUIRED.

### Final lab closeout (2026-08-30T22:37:09+07:00)

- Lab access ended by explicit human direction. No new experiment, serial command, flash, reset, or acquisition was started during closeout.
- Active branch before final closeout commit: `experiment/icsec-extension-20260830` at `8c736c30ebc3abacd73354f81dd2ac170000014f`; frozen base `8a47d070c549274c59cdbde2495afa8d353a93b3` remains an ancestor.
- Independent final source and backup verification: primary 88/88 rows, G431-B replication 42/42 rows, and scope feasibility 19/19 rows; zero missing files, size mismatches, or SHA-256 mismatches in every source and backup.
- Frozen dataset, provenance, reviewed primary, reviewed replication, and scope-feasibility inventory hashes remain respectively `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD`, `84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC`, `8B4CB2AB87CD317905AA4A219B81E99E2E459DC3EEF386D14286297476177C0B`, `F13EBB7FEB42FB3F67E56A8503CB6D70A5F630F2C864A16B22D5BF4D9D19CCE9`, and `519E7E142DFAFEA4736CA74D945B3197D106714F9B6B1A6B45C75309EC4B1B0E`.
- Invalid/incomplete evidence preservation rechecked: both NOMINAL_001 raw logs, both R002_B1_D500 raw logs, both S001_D110 serial logs, the internal-scope-only feasibility disposition, and all four dropped-unattempted S002-S005 ledger rows remain present. Nothing was replaced or silently removed.
- Final controller/payload state from the last hardware operation: G474-A confirmed `NORMAL`; G431-B passed post-S001 stabilization and was ONLINE. No Python acquisition process or OpenOCD process remains active and no COM port is held by the experiment tooling.
- Instrumented firmware remains installed on G431-B and G474-A; this is recorded by exact hashes and does not prevent safe power removal.
- Hardware disconnect status: safe after final repository commit/push attempt; remove scope probe tips/grounds, then USB power/cables and inter-board UART wiring without pressing reset.

### Recovery checkpoint (2026-09-01T15:51:37+07:00)

- Recovery was read-only with respect to hardware and experiment execution: no board communication, flash, reset, build, or acquisition occurred. `NEXT_TASK.md` was not changed.
- Starting branch/HEAD: `experiment/icsec-extension-20260830` at `06f1ab7fa7dffb3d0a6d5b30216e4d3713d1f80e`; upstream was the same commit after fetch and the starting worktree was clean.
- `main`, `origin/main`, and `icsec-2026-evaluated-state` still resolve to frozen commit `8a47d070c549274c59cdbde2495afa8d353a93b3`, which remains an ancestor of the extension branch. No Git diff from the frozen commit to extension HEAD affects the frozen dataset, frozen provenance package, or manuscript paths.
- Current extension source and exact-copy backup inventories independently verify: primary 88/88 rows, G431-B replication 42/42 rows, and scope feasibility 19/19 rows, all with zero missing, size, or SHA-256 issues. Their inventory-file hashes remain `8B4CB2AB87CD317905AA4A219B81E99E2E459DC3EEF386D14286297476177C0B`, `F13EBB7FEB42FB3F67E56A8503CB6D70A5F630F2C864A16B22D5BF4D9D19CCE9`, and `519E7E142DFAFEA4736CA74D945B3197D106714F9B6B1A6B45C75309EC4B1B0E`.
- Recovery integrity finding: the frozen inventory files retain hashes `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD` and `84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC`, but the current checkout contains only 10/195 inventoried frozen-dataset paths and 55/65 inventoried frozen-provenance paths. Missing files are ignored raw logs/binaries/ELFs: 185 dataset artifacts and 10 provenance artifacts. They were not stored in the frozen Git tree, and the known extension backup does not contain a frozen-baseline backup. Among present paths, one dataset text file and 27 provenance text files differ bytewise only because the checkout uses CRLF; all match their frozen hashes after LF normalization and their canonical LF blobs remain in Git.
- Exact Aug 30 recovery accounting: one valid extended nominal (`NOMINAL_002`); `NOMINAL_001` invalid retained; primary campaign 25 attempted/24 valid/1 invalid retained/20 review-removed; valid rows include six NC and three each at 50/90/100/110/150/250 ms; two valid BAD_CRC exposures; G431-B replication 12/12 valid including three NC and three each at 90/100/110 ms; scope 5 planned/1 serial-valid feasibility attempt/0 timing traces/4 dropped-unattempted.
- The sustained BAD_CRC result is recoverable only through the ordered raw marker sequence and control flow that waited for OFFLINE before restore; the derived `offline_before_restore=false` field remains prohibited from citation.
- Read-only F411 assessment: USART2 PA2/PA3 is the default ST-LINK VCP host channel; USART1 PA9/PA10 is the smallest separate payload-link choice. Four healthy boards can technically form two independent F411-to-F411 pairs, but both roles require F4 interrupt-UART/role ports and any result would be protocol-level cross-platform replication, not direct G431/G474 replication. Overall engineering risk is HIGH. No F411 firmware was modified.
- Recovery report and complete evidence-path accounting: `research/icsec2026/CURRENT_STATE_20260901.md`.
- Unresolved uncertainty requiring immediate attention: locate the exact original missing frozen artifacts and verify them against the existing inventories before relying on the frozen baseline package as locally complete. Do not regenerate inventories or substitute reruns.
- Next action: await Research Director review and a new `NEXT_TASK.md`; no new experiment is authorized by this checkpoint.

### Exact-byte frozen-baseline recovery (2026-09-01T19:38:55+07:00)

- Authorized scope was recovery/hash verification only under `NEXT_TASK.md`, `FINAL_PUSH_PLAN.md`, and `LAB_EXTENSION_BRIEF.md`. No board or oscilloscope was connected, commanded, flashed, reset, or sampled; no firmware was built or modified.
- Starting branch/HEAD: `experiment/icsec-extension-20260830` at `34c3ba76ad8fd0b73c57bc1a0bc31f3f0e23bf6e`; starting upstream was `06f1ab7fa7dffb3d0a6d5b30216e4d3713d1f80e` (local ahead 1). Frozen `main`, `origin/main`, and `icsec-2026-evaluated-state` remained `8a47d070c549274c59cdbde2495afa8d353a93b3`.
- Research Director inputs present at milestone start: modified `research/icsec2026/NEXT_TASK.md` and untracked `research/icsec2026/FINAL_PUSH_PLAN.md`; both were preserved. New recovery records are under `research/icsec2026/extension/recovery/recovery_20260901/`.
- Original-PC transfer ZIP: `C:/Users/wachi/Documents/WashiOS_EVIDENCE_TRANSFER_20260901.zip`, 391,219 bytes, SHA-256 `5BC8B2B14CCDFA597AF93A5C40E2A246B3ED6A88508121F4A7A8A2B94D45F462`; the supplied hash was verified before extraction.
- Exclusive read-only source extraction: `C:/WashiOS-baseline-recovery/source_transfer_20260901_5BC8B2B1/WashiOS_EVIDENCE_TRANSFER_20260901`; 270 files, 1,663,907 bytes. Its 269-row transfer inventory SHA-256 is `422760C42F0B8D5BA535E37A58F87136A1A59591601BE3AB01B396D6BB17171C`; zero issues before copying and zero issues after all copies.
- The extracted source independently verified all 195 frozen dataset rows and 65 frozen provenance rows with zero missing, size, or SHA-256 issues. Inventory hashes are unchanged at `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD` and `84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC`.
- Two invalid staging attempts are retained transparently. Attempt 1 (`C:/WashiOS-baseline-recovery/primary_recovered_baseline_20260901`) used Git archive export and produced 28 CRLF-related row mismatches; its ledger has SHA-256 `1DA9AE064F1994AFB70AC077DCB09DCEC5EABA37F0C59EAFEE176588A8F86C7E`. Attempt 2 (`C:/WashiOS-baseline-recovery/primary_recovered_baseline_20260901_attempt2`) used raw Git blobs for all tracked files and produced 35 row mismatches plus two inventory-file hash mismatches; its ledger has SHA-256 `A43A3322A6C1AB9C8172B34146295E96F12E231882777C7EE1DF3A1BFF6DE545`.
- Reconciliation finding: the unchanged inventories require mixed original working-tree byte sequences. Of 260 inventory rows, 30 tracked rows match their raw frozen Git blob, 35 tracked rows require the recovered original clean-working-tree representation, and 195 ignored logs/binaries/ELFs require recovered original bytes. The two inventory files also require the verified recovered-source bytes. This is resolved in the final copies and does not alter any inventory.
- Primary verified copy: `C:/WashiOS-baseline-recovery/primary_recovered_baseline_20260901_attempt3_verified`; 262 files, 1,559,372 bytes; dataset 195/195 and provenance 65/65 exact, with zero missing, size, or SHA-256 issues. Per-row source/copy ledger SHA-256: `3B8A94F9F3DDF5D036C0EA4E99E4DDB2694023260B426801348F4016CABDD091`.
- Secondary independently verified copy: `C:/WashiOS-baseline-recovery/secondary_recovered_baseline_20260901_verified`; 262 files, 1,559,372 bytes; dataset 195/195 and provenance 65/65 exact, with zero missing, size, or SHA-256 issues. Verification-ledger SHA-256: `12304CEA4DE64EF3432F84C237CB4BFD2CB3930141D9C53B5DB878EF87CE7837`.
- Recovery record inventory: nine rows, zero issues; `research/icsec2026/extension/recovery/recovery_20260901/RECOVERY_SHA256SUMS.csv` SHA-256 `BA40B30A7EFEA2F6E438A4B5482D8074AC5D6B834C55118DCF17B42C4BC056C1` (inventory excludes itself).
- Frozen dataset, frozen provenance, frozen manuscript, and reviewed primary/replication/scope extension evidence paths were not modified. No inventory was regenerated and no rerun or rebuild was substituted for original evidence.
- Completed milestone: exact-byte frozen-baseline recovery with two independently verified external copies. Unresolved provenance issue: none. Remaining time: not applicable; no further milestone is authorized before research review.
- Next action: validate the recovery record against the external copies, commit the coherent recovery checkpoint, synchronize the extension branch if permitted by the final-push workflow, then stop with `WORK_REVIEW_REQUIRED`.

### F411 source/pin/VCP feasibility gate (2026-09-01T20:22:41+07:00)

- Authorized scope was Checkpoint 1 in the Research Director's current `NEXT_TASK.md` under `FINAL_PUSH_PLAN.md`: board/VCP enumeration, authoritative pin audit, existing generic build, source-impact/semantic audit, and one GO/NO-GO decision only. No F411 experimental-role source was modified, no board was flashed or reset, no UART wiring was installed, and no physical experiment was run. Pre-existing firmware on all four F411 boards was left untouched.
- Starting branch/source checkpoint: `experiment/icsec-extension-20260830` at synchronized commit `0fbd98fe367faaeee7da8aa360755bee807f7a36`; frozen `main`, `origin/main`, and evaluated tag remained `8a47d070c549274c59cdbde2495afa8d353a93b3`. The Research Director's uncommitted `NEXT_TASK.md` and `FINAL_PUSH_PLAN.md` updates were preserved as milestone inputs.
- Due to two available USB ports, enumeration used two sequential batches. Durable identities and observed VCPs were F411-A `066BFF495051727187053106` / COM16, F411-B `066EFF495051727187053015` / COM11, F411-C `0669FF495051727187053226` / COM12, and F411-D `0663FF495051727187066042` / COM6. All serials were unique; each board exposed an ST-LINK VCP with no conflict in its two-board batch. COM and drive letters are non-durable. Four-board simultaneous attachment was not tested and is not required by the sequential gated plan.
- Locked later pin map: USART2 PA2/PA3 through the default ST-LINK VCP for independent host observation/control; USART1 PA9/PA10 AF7 exposed on D8/D2 for the crossed inter-board link plus common ground. Authoritative ST UM1724, the STM32F411 datasheet, and installed PlatformIO board definitions support the mapping; no solder change is required.
- Existing `genericSTM32F411RE` toolchain sanity build passed with PlatformIO 6.1.19 / ST STM32 19.6.0 in 19.666 s. It used 7,748 bytes RAM and 15,404 bytes flash. Unflashed sanity artifacts: BIN SHA-256 `B5524BD395023202D096FEF374820F1C0637717CC75698AA27E1E8208AAB9E5A`; ELF SHA-256 `F723A3A1BF9EFB1B334C77A97FFB9B2CC3603228BCBC21BBC55C28234933BFBB`.
- Source audit result: the common protocol, CRC/sequence controller, 500 ms poll, 100 ms deadline, three-timeout OFFLINE rule, task, and payload fault parser can remain unchanged. Missing work is bounded to explicit standalone Nucleo role environments, isolated F4 USART2/USART1 board and interrupt-ring implementations, narrow composition/source-selection guards, buffer/overflow tests, and a separate F411 harness wrapper. Current F4 receive is blocking and reports `available() == 0`; current payload board code is G4-specific.
- Gate decision: `F411_GO` for Checkpoint 1 only; later engineering risk HIGH. This does not authorize Checkpoint 2, does not predict successful bring-up, and supports no experimental, timing, pooled, or population claim. Any later result is bounded protocol-level cross-configuration evidence with pair-specific accounting.
- Report: `research/icsec2026/extension/F411_FEASIBILITY_20260901.md`. Machine-readable evidence: `research/icsec2026/extension/evidence/f411_feasibility_20260901/`. Its four-row inventory independently verified with zero issues; inventory SHA-256 `540D3E46D206B9CE29806E291F8328D3B8C4F43F7A58471931AA3BEFB8A8930C` (inventory excludes itself).
- Frozen dataset, frozen provenance, reviewed primary, G431-B replication, scope-feasibility, and recovery inventory-file hashes reverified unchanged as `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD`, `84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC`, `8B4CB2AB87CD317905AA4A219B81E99E2E459DC3EEF386D14286297476177C0B`, `F13EBB7FEB42FB3F67E56A8503CB6D70A5F630F2C864A16B22D5BF4D9D19CCE9`, `519E7E142DFAFEA4736CA74D945B3197D106714F9B6B1A6B45C75309EC4B1B0E`, and `BA40B30A7EFEA2F6E438A4B5482D8074AC5D6B834C55118DCF17B42C4BC056C1`.
- Modified/new milestone records: Research Director inputs `research/icsec2026/NEXT_TASK.md` and `research/icsec2026/FINAL_PUSH_PLAN.md`; agent records `research/icsec2026/extension/F411_FEASIBILITY_20260901.md`, `research/icsec2026/extension/evidence/f411_feasibility_20260901/*`, and this session entry. Remaining time: Checkpoint 1 complete within its 60-minute time box. Next action: freeze/commit/synchronize this checkpoint and stop with `WORK_REVIEW_REQUIRED`; do not implement or flash Checkpoint 2 before research review.

### F411 Pair-1 software gate (2026-09-01T20:51:36+07:00)

- Research review authorized only F411 Pair-1 implementation/bring-up, one 65 s NORMAL window, and one retained 110 ms pilot. Starting branch/HEAD was `experiment/icsec-extension-20260830` at synchronized `0fdac83844c4f6247598146e32a522529a412607`; frozen base and recovery checkpoint remain ancestors. The Research Director's updated `NEXT_TASK.md` was the only initial worktree change.
- Focused implementation began at the first retained timestamp 2026-09-01T20:33:18+07:00. Role implementation commit `8d6728fbbd35ec96ab539f914e7b0fbd70b53a1d` is pushed to origin. No board was flashed/reset and no UART wiring or physical experiment occurred during the software gate.
- Added explicit standalone F411 controller and payload environments, isolated PA2/PA3 USART2 host plus PA9/PA10 USART1 link initialization, interrupt-driven fixed-capacity receive rings, explicit overflow/error markers, deterministic ring tests, and a separate Pair-1 harness. Common protocol, controller, task, and parser blobs are exactly unchanged from `0fdac83`.
- Validation: core native/SITL/F411 ring 43/43 passed, payload parser 3/3 passed, extension/legacy host 9/9 passed. Existing G431 controller and G474 payload builds also passed after the narrow source-selection changes.
- Clean F411 role builds passed reproducibly and both vector tables begin at `0x08000000`. Controller BIN `F83B425A57CC31D4E81EC8D145CAE77C1AC81957A17A13161267EFDDE7ACB146` (19,820 bytes), ELF `14878B899FBCED958CF507FBF62E10F39A95CBE90A4C33A8C938396305D93452` (158,152 bytes). Payload BIN `52F145488CAD9D3A9711F77DF1DFB9F76DFEAE6660FE9E1FBD5560AA738BFBBB` (8,152 bytes), ELF `0BC0EAAA7830B001CD31F1805C1002275E62FAF8DE6BC8C1AF44ABF5A2005493` (143,396 bytes).
- Exclusive evidence path: `research/icsec2026/extension/evidence/f411_pair1_20260901/`, currently status `SOFTWARE_GATE_PASSED_AWAITING_PHYSICAL_BRINGUP`. F411-C and F411-D remained the last physically connected batch and were not accessed. Fixed P1 identities remain F411-A controller `066BFF495051727187053106` and F411-B payload `066EFF495051727187053015`.
- Elapsed implementation/test/build interval from the first retained milestone timestamp is approximately 18 minutes, within the 120-minute implementation/bring-up allowance; global recorded feasibility plus this interval is approximately 42 minutes. Next action requires a human to disconnect C/D, connect A/B, and install exactly the three locked jumpers before software can freshly enumerate and flash by durable identity.

### F411 Pair-1 failed bring-up disposition (2026-09-01T21:12:55+07:00)

- Human connected fixed Pair-1 with exactly three jumpers: F411-A D8/PA9 TX to F411-B D2/PA10 RX, F411-B D8/PA9 TX to F411-A D2/PA10 RX, and common GND; no solder change. Fresh enumeration was F411-A controller `066BFF495051727187053106` / COM16 and F411-B payload `066EFF495051727187053015` / COM11. F411-C/D were absent and untouched.
- `BRINGUP_001` is retained as a pre-attempt harness abort caused by an already-existing empty exclusive directory. COM ports were opened then closed; capture, flash, reset, and hardware observation did not start. It is not a scientific or physical attempt and was not deleted or overwritten. Harness correction commit `a8e736b` records the distinct next identifier before physical action.
- `BRINGUP_002` is the single physical bring-up attempt. Exact standalone payload ELF `0BC0EAAA7830B001CD31F1805C1002275E62FAF8DE6BC8C1AF44ABF5A2005493` and controller ELF `14878B899FBCED958CF507FBF62E10F39A95CBE90A4C33A8C938396305D93452` were flashed by their exact ST-LINK serials. Both OpenOCD commands exited zero and retained `Verified OK` records.
- Exact-byte dual logs retain payload READY/NORMAL/LINK_ACTIVE and controller READY/PAYLOAD_LINK_START/PAYLOAD_ACCEPTED seq=0 mode=0/PAYLOAD_ONLINE. This proves independent VCP observation and one attributable bidirectional framed exchange on the crossed USART1 link. Zero UART overflow/error or link-write-failure markers were observed.
- Bring-up failed because no controller 5 s status record or subsequent link exchange appeared during the retained window after the initial ONLINE transition. Controller runtime/reset state is ambiguous. This violates the no-reset-ambiguity acceptance criterion; the raw evidence is not classified as a valid bring-up.
- Stop rule enforced: no 65 s NORMAL observation and no 110 ms pilot were attempted; there was no reset, retry, replacement, delay change, or post-outcome implementation tuning. Terminal disposition is `PAIR1_PILOT_FAIL`, with zero scientific observations and no campaign denominator.
- Last exact payload-side mode confirmation is NORMAL at 2026-09-01T14:10:33.928438+00:00. Final controller runtime state is unresolved after the initial ONLINE transition. Exact role firmware remains installed; no experiment Python or OpenOCD process remains and no COM port is held by the harness.
- Evidence path: `research/icsec2026/extension/evidence/f411_pair1_20260901/`. It includes source/semantic proof, test/build logs, exact binaries, identity/wiring record, both retained bring-up dispositions, flash logs, exact-byte/readable dual logs, validations, and final disposition.
- Frozen dataset, frozen provenance, primary, G431-B replication, scope-feasibility, and recovery inventory hashes remain unchanged. Focused Pair-1 milestone elapsed time from first retained implementation timestamp to terminal decision was approximately 38 minutes; global recorded feasibility plus Pair-1 time was approximately 62 minutes, within budget.
- Unresolved engineering uncertainty: root cause of controller runtime cessation after the first exchange. Under the reviewed no-retry rule it was not debugged on hardware in this milestone. Next action: inventory, commit, synchronize, and stop with `WORK_REVIEW_REQUIRED`; do not run NORMAL, pilot, campaign, or second-pair work.
- Final Pair-1 package inventory contains 33 rows and independently verifies with zero missing, size, or SHA-256 mismatches; `PAIR1_SHA256SUMS.csv` SHA-256 is `AC00A0C93083FBB553408B2EE20DC283D9002B67F853D472B28D3067E2145A3F` (inventory excludes itself; 34 total package files, 390,356 bytes). Evidence-integrity problem: none.

### F411 Pair-1 accounting correction (2026-09-01T21:16:52+07:00)

- Recovery inspection of the committed raw package disproved the immediately preceding derived accounting: `BRINGUP_001` was a physical bring-up, not an empty-directory pre-attempt abort. Its controller/payload UART logs and both OpenOCD flash logs predate the later `pre_attempt_abort.json`; programming completed with `Verified OK`, both roles emitted READY, and one exchange reached `PAYLOAD_ACCEPTED` and `PAYLOAD_ONLINE`.
- Correct accounting is two physical bring-up attempts, both invalid; zero valid bring-ups, zero NORMAL attempts, zero pilot attempts, and zero scientific observations. `BRINGUP_002` occurred because the first attempt was incorrectly reconstructed as a nonphysical abort, and therefore violated the reviewed no-retry rule. No additional hardware operation or experiment was performed after discovery.
- Both attempts show the same bounded engineering pattern: one attributable bidirectional exchange followed by no retained 5 s controller status and no subsequent link exchange. This is not scientific evidence and does not authorize a protocol-level replication claim.
- The original raw UART and OpenOCD logs remain byte-for-byte intact. `raw/bringup/BRINGUP_001/pre_attempt_abort.json` is retained but is factually incorrect and superseded. The singular `bringup_validation.json` contains only `BRINGUP_002`; any original per-run validation for `BRINGUP_001` was not retained and may have been overwritten. Consequently, the first attempt's exact programmed ELF hash cannot be independently proven from its retained OpenOCD output alone, although successful programming and verification are directly recorded.
- Additive correction records: `research/icsec2026/extension/evidence/f411_pair1_20260901/ACCOUNTING_CORRECTION_20260901.json`, `bringup_001_reconstructed_validation.json`, and `FINAL_CORRECTED_DISPOSITION.json`. The prior manifest, ledger, disposition, validation, and inventory remain preserved as the committed historical checkpoint and are explicitly superseded where inconsistent.
- Active branch/commit at discovery: `experiment/icsec-extension-20260830` / `403e09cb361142040bc41e2b2621f6e377a3e7af`, synchronized with origin before the additive correction. No Python acquisition or OpenOCD process was active.
- Next action: create a supplemental full-package inventory covering the correction addenda, validate both old and supplemental inventories, commit and synchronize the correction, then stop with `WORK_REVIEW_REQUIRED`.
- Verification completed: the original 33-row inventory still verifies with zero missing, size, or SHA-256 issues and retains SHA-256 `AC00A0C93083FBB553408B2EE20DC283D9002B67F853D472B28D3067E2145A3F`. Supplemental `PAIR1_CORRECTED_SHA256SUMS.csv` covers 38 package files with zero issues and has SHA-256 `A5C8BF48D7FD0E9CC3A120B890F11CA49FD8DBB6086FD594A321F14C778AC6C9` (inventory excludes itself). All 14 package JSON files parse successfully.

### F411 bounded engineering diagnostic (2026-09-01T21:33:51+07:00)

- Research review authorized one engineering-only `ENGDIAG_001` under the current `NEXT_TASK.md`: 30 focused hardware-action minutes, the three predeclared hypotheses in order, stop on conclusive confirmation, at most one minimal fix, and exactly one liveness check. This milestone creates no scientific observation or manuscript result.
- Starting branch/commit was `experiment/icsec-extension-20260830` / synchronized `600272edf9460191cbb7c7c6080ce503ffad1f17`; the only starting worktree change was the Research Director's updated `NEXT_TASK.md`. The corrected prior Pair-1 inventory remained byte-identical at SHA-256 `A5C8BF48D7FD0E9CC3A120B890F11CA49FD8DBB6086FD594A321F14C778AC6C9`.
- Fresh enumeration unambiguously identified F411-A controller `066BFF495051727187053106` on COM16 and F411-B payload `066EFF495051727187053015` on COM11. The existing three-jumper D8/PA9-to-D2/PA10 crossed USART1 wiring and common ground were unchanged; board roles were unchanged.
- Hypothesis 1 was conclusively confirmed by a non-resetting exact-serial SWD runtime probe after the retained first-exchange-only state. Over a 2 s resume interval, FreeRTOS `xTickCount` advanced 629922→631961 (delta 2039) while HAL `uwTick` remained 0→0. Scheduler-suspended was zero, CPU mode was Thread, and CFSR/HFSR were zero. Per the stop rule, Hypotheses 2 and 3 were not tested.
- Cause: F411 `Stm32Timing::getSystemTick()` used the frozen HAL tick after FreeRTOS replaced `SysTick_Handler`, so the initial time-zero poll ran but later 500 ms polls and the 5 s status never became due even though the scheduler continued. This directly explains both preserved failed bring-up signatures without reclassifying either.
- Applied exactly one adapter-only fix in `core/src/bsp/f4/Stm32Timing.cpp`: use `xTaskGetTickCount()` after the scheduler starts and retain `HAL_GetTick()` before scheduler start, mirroring the existing G4 adapter. Common protocol, supervision controller/task, parser, 115200 8N1, 500 ms poll, 100 ms deadline, three-timeout OFFLINE rule, evidence gates, and UART mapping are unchanged.
- Validation passed: core native/SITL/F411 ring 43/43, payload parser 3/3, extension/legacy host 9/9, and both clean F411 role builds. Fixed controller ELF SHA-256 is `9AA52D103E977A8B18968A0B7F3D69E74361AC5E5FFDFA6B3CBC49A3AD722D78`; unchanged payload ELF SHA-256 is `0BC0EAAA7830B001CD31F1805C1002275E62FAF8DE6BC8C1AF44ABF5A2005493`.
- The only liveness check, `ENGDIAG_001_FIXCHECK`, exact-target flashed and verified both identities. It retained 12 accepted exchanges, including 11 post-initial exchanges spanning 4.993306 s, and the first 5 s status `ONLINE polls=10 ok=10 timeout=0 crc=0 seq=0 recovery=0 heartbeat=OK watchdog=OK`. No reset/fault, UART overflow/error, link-write-failure, or receive-loss indication was retained.
- Final hardware action ended at 2026-09-01T21:33:51.524365+07:00, 205.839974 s after the retained diagnostic start and within the 1800 s limit. No NORMAL window, delayed mode, fault injection, scientific pilot, campaign, or second-pair action occurred. Final controller state was running the fixed diagnostic firmware with ONLINE/continued exchanges observed; payload was running unchanged firmware with NORMAL confirmed.
- Terminal condition: `ENGINEERING_DIAGNOSTIC_PASS_AWAITING_REVIEW`. Evidence root: `research/icsec2026/extension/evidence/f411_engdiag_20260901/`. Next action is evidence inventory, commit/synchronization, and `WORK_REVIEW_REQUIRED`; no fresh scientific Pair-1 work is authorized.
- Final diagnostic inventory contains 30 rows and independently verifies with zero missing, size, or SHA-256 mismatches; `ENGDIAG_SHA256SUMS.csv` SHA-256 is `98846023F3285F5B9F60C5387E1C54FD6D5EEAA8D5E58A42720795EC9B328DE0` (inventory excludes itself; 31 total package files). The package-local `.gitattributes` records all package paths as exact-byte binary data. All nine diagnostic JSON files parse, both exact-byte UART logs pass format validation, no experiment process remains, and the corrected prior Pair-1 inventory still verifies 38/38 unchanged.

### Fresh F411 Pair-1 scientific pilot readiness (2026-09-01T21:52:00+07:00)

- Research review authorized exactly one fresh scientific pilot `F411_P1_SCI_PILOT_001_D110` with retained precondition `F411_P1_SCI_PILOT_001_D110_PRECHECK`, one 110 ms delayed-response exposure, no retry/replacement, and no campaign denominator. Failed bring-ups and engineering diagnostic observations remain separate and unchanged.
- Starting branch/commit was synchronized `experiment/icsec-extension-20260830` / `0ce8a5cfe12b0dc72df5e8baeee1f8f3bdf19612`; only the Research Director's new `NEXT_TASK.md` was initially modified. Frozen `main` and `origin/main` remained `8a47d070c549274c59cdbde2495afa8d353a93b3`.
- Corrected failed-bring-up inventory reverified 38/38 with SHA-256 `A5C8BF48D7FD0E9CC3A120B890F11CA49FD8DBB6086FD594A321F14C778AC6C9`; engineering diagnostic inventory reverified 30/30 with SHA-256 `98846023F3285F5B9F60C5387E1C54FD6D5EEAA8D5E58A42720795EC9B328DE0`; both had zero issues.
- Firmware behavior diff from `600272e` to `0ce8a5c` is only `core/src/bsp/f4/Stm32Timing.cpp`; the four common semantic Git blobs match the diagnostic record. No firmware source was modified in this milestone.
- Required suites pass: core native/SITL/F411 ring 43/43, payload parser 3/3, extension/legacy host 9/9, and focused continuous scientific-harness validation 3/3. One initial test-fixture constructor error (three test errors, no hardware action) is retained in `development_test_history.json`.
- Clean role builds exactly reproduce the fixed hashes and sizes: controller BIN `8686113C4A83E1600EBE66FB3B3F8795853011B4B0E69D91F9E68EBB3FD8FE68` / 19,832 bytes and ELF `9AA52D103E977A8B18968A0B7F3D69E74361AC5E5FFDFA6B3CBC49A3AD722D78` / 158,152 bytes; payload BIN `52F145488CAD9D3A9711F77DF1DFB9F76DFEAE6660FE9E1FBD5560AA738BFBBB` / 8,152 bytes and ELF `0BC0EAAA7830B001CD31F1805C1002275E62FAF8DE6BC8C1AF44ABF5A2005493` / 143,396 bytes.
- Added a host-only continuous-capture orchestrator that refuses reused IDs/paths and holds both VCP captures across exact-target flashing, the 65 s NORMAL precondition, fresh stabilization, the single activation/exposure/restore, and final stabilization. It does not alter firmware or harness validity rules.
- Fresh USB enumeration unambiguously identified F411-A `066BFF495051727187053106` / COM16 and F411-B `066EFF495051727187053015` / COM11; F411-C/D were absent. Serial ports were not opened and no reset/flash/hardware action occurred during readiness.
- Exclusive locked package: `research/icsec2026/extension/evidence/f411_pair1_scientific_pilot_20260901/`. Its preacquisition inventory verifies 28/28 rows with zero issues; `PREACQUISITION_SHA256SUMS.csv` SHA-256 is `0123BCDA3590BF6151A12DF6A0BD1A71FC80F383EB838D44BD38D6B89EBC217D` (inventory excludes itself).
- Next action requires human physical confirmation of the unchanged exact three-wire A/B link before the one flash/verify/reset and scientific acquisition sequence. No delayed command has been sent.

### Fresh F411 Pair-1 scientific pilot outcome (2026-09-01T22:14:52+07:00)

- Human identity confirmation established F411-A controller `066BFF495051727187053106` / COM16 and F411-B payload `066EFF495051727187053015` / COM11. The exact three-wire link was confirmed as A D8/PA9 to B D2/PA10, B D8/PA9 to A D2/PA10, and GND to GND, with no D0/D1 wiring. Disconnect/reconnect of A for identity confirmation occurred before capture and is retained as a pre-capture power cycle.
- Acquisition source was synchronized commit `6bfd5ae4ed2eb71171988a56ca8087127d42cad5` on `experiment/icsec-extension-20260830`. Exact firmware hashes were controller ELF `9AA52D103E977A8B18968A0B7F3D69E74361AC5E5FFDFA6B3CBC49A3AD722D78`, controller BIN `8686113C4A83E1600EBE66FB3B3F8795853011B4B0E69D91F9E68EBB3FD8FE68`, payload ELF `0BC0EAAA7830B001CD31F1805C1002275E62FAF8DE6BC8C1AF44ABF5A2005493`, and payload BIN `52F145488CAD9D3A9711F77DF1DFB9F76DFEAE6660FE9E1FBD5560AA738BFBBB`. Both exact-target flashes exited zero and retained `Verified OK`.
- Exactly one scientific acquisition invocation was performed. No retry, replacement, post-outcome firmware change, setting change, or second delayed command occurred. The attempt is not a campaign denominator.
- Precondition `F411_P1_SCI_PILOT_001_D110_PRECHECK` is valid: 65.0 s monotonic NORMAL window; 13/13 status records ONLINE; `ok` increased strictly from 10 to 130; timeout, CRC, sequence, and recovery deltas were all zero; no prohibited marker occurred. Fresh NORMAL confirmation and pre-pilot stabilization passed.
- Pilot `F411_P1_SCI_PILOT_001_D110` is valid with one exact 110 ms activation confirmation, 4.0 s exposure, one NORMAL restore, confirmed recovery, and passed post-stabilization. Ordered raw markers were timeout consecutive=1, sequence rejection, timeout consecutive=2, OFFLINE consecutive=3, then restore and recovery.
- Unexpected retained outcome: the first post-restore status reported cumulative `timeout=8`, `crc=0`, `seq=8`, `recovery=1`, rather than only the explicitly logged transition markers. This remains descriptive evidence and was not tuned or rerun.
- Continuous capture retained two controller timeout markers before controller flash/READY while the payload was flashed first. They precede all scientific boundaries and are excluded from scoring. It also retained one partial final record (`[OBC] PAYLOAD_ACCE`) after the last validated status while ports were closing; it is outside every scored boundary and is not counted as an exchange.
- The original `precondition_validation.json` wrote `normal_window_end_host_time` after stabilization rather than at the NORMAL-window boundary. The original is preserved; additive `precondition_boundary_correction.json` records the exact retained post-window host boundary. This has no effect on the monotonic 65.0 s gate or raw status selection.
- Independent raw validation passed: controller 191 records, payload 6 records, zero raw-format/render failures, exactly one activation, and confirmed OFFLINE/recovery. Final payload state is NORMAL; final controller state is ONLINE with stable counters. Both serial ports are closed, no acquisition/OpenOCD process remains, and no hardware action followed the run.
- Evidence root: `research/icsec2026/extension/evidence/f411_pair1_scientific_pilot_20260901/`. Final disposition is `F411_P1_SCI_PILOT_PASS_AWAITING_REVIEW`; `final_validation.json` reports valid=true with zero failures.
- Final inventory contains 48 rows with zero missing, size, or SHA-256 issues (49 files including the inventory). `SCIENTIFIC_PILOT_SHA256SUMS.csv` SHA-256 is `B8B2DB1679A21747B80DB9209E7249C755C30CF8C62464E425906951E24295D1`.
- Exact-copy backup: `C:/WashiOS-extension-backup/f411_pair1_scientific_pilot_20260901`; all 48 inventory rows independently match size and SHA-256, with 49 total files and the same inventory hash `B8B2DB1679A21747B80DB9209E7249C755C30CF8C62464E425906951E24295D1`.
- Prior corrected failed-bring-up and engineering-diagnostic packages remain unchanged at inventory hashes `A5C8BF48D7FD0E9CC3A120B890F11CA49FD8DBB6086FD594A321F14C778AC6C9` and `98846023F3285F5B9F60C5387E1C54FD6D5EEAA8D5E58A42720795EC9B328DE0`. Frozen and reviewed baseline/extension inventories were reverified unchanged before acquisition.
- Modified/new milestone files are the locked pilot package, `research/icsec2026/extension/run_f411_scientific_pilot.py`, `research/icsec2026/extension/validate_f411_scientific_pilot.py`, `research/icsec2026/extension/test_f411_scientific_pilot.py`, the Research Director's `NEXT_TASK.md`, and this session entry. Remaining time: milestone complete; no additional hardware experiment is authorized. Next action: commit, synchronize, and stop with `WORK_REVIEW_REQUIRED`.

### Predefined F411 Pair-1 campaign readiness (2026-09-01T22:37:55+07:00)

- Research review authorized only campaign `F411_P1_CAMPAIGN_20260901_B3`: 12 sequential rows in the exact predefined seed-20260901 order, comprising three NC and three each at 90/100/110 ms. The reviewed pilot, corrected failed bring-ups, and engineering diagnostic remain separate and excluded from this denominator.
- Starting branch/HEAD was synchronized `experiment/icsec-extension-20260830` / `66b17036bfdaf4053448c2920a4737b0ebf23708`; the only starting worktree change was the Research Director's updated `NEXT_TASK.md`. Frozen `main` and `origin/main` remained `8a47d070c549274c59cdbde2495afa8d353a93b3`.
- Reviewed pilot source and backup independently reverified 48/48 rows each with inventory SHA-256 `B8B2DB1679A21747B80DB9209E7249C755C30CF8C62464E425906951E24295D1`. Corrected failed-bring-up and diagnostic inventories reverified 38/38 and 30/30 at `A5C8BF48D7FD0E9CC3A120B890F11CA49FD8DBB6086FD594A321F14C778AC6C9` and `98846023F3285F5B9F60C5387E1C54FD6D5EEAA8D5E58A42720795EC9B328DE0`. Frozen/reviewed G431/G474 and recovery inventory-file hashes remain unchanged.
- Exclusive campaign package `research/icsec2026/extension/evidence/f411_pair1_campaign_20260901_seed20260901_b3/` was created once. Plan SHA-256 is `88EDD7D47C40354D1C9DF8B0F7EC9A083198B4A6E5CBF4D453E947AD9B88BF45`; the attempt ledger is pristine with 12 PLANNED rows and no acquisition path exists.
- Added a campaign-only continuous-capture harness, focused tests, and independent validator. Harness/test/validator SHA-256 values are `B6E3E244053E43C639AFF091FA0DF2880C8CAA7B8D5F16B5AF8A716A91A8F8AF`, `90B98F389C05C95C040D7C0210DB0FAF6936AC77F1C4661B90E42C2E8E136009`, and `C23EC424B42ECF186F79D66750CF2D059921D3E54CF533D1E6219426DADD2468`. The harness enforces exact order/condition, one attempt per row, continuous master logs, first-invalid stop, no reset/reflash between rows, and full remaining-row accounting.
- Required tests pass: core native/SITL/F411 ring 43/43, payload parser 3/3, and combined extension/legacy/pilot/campaign host suite 16/16. Both roles clean-build successfully and exactly reproduce the reviewed fixed hashes: controller ELF/BIN `9AA52D...2D78` / `868611...FE68`; payload ELF/BIN `0BC0EA...5493` / `52F145...BBB`. Both images remain standalone at `0x08000000`; no firmware source or semantics changed.
- No serial port was opened, board flashed/reset, command sent, or observation started during readiness. Next actions are preacquisition inventory/commit, fresh exact-identity enumeration, and human confirmation of the exact three-wire link plus at least 90 uninterrupted minutes before the hard stop.
- Preacquisition inventory contains 32 rows with zero missing, size, or SHA-256 issues (33 package files including the inventory). `PREACQUISITION_SHA256SUMS.csv` SHA-256 is `F82C38B2017204D723F74223051CEEF64D3F354005999C7C7C3A6BCFCED1B2FC`. The package-local `.gitattributes` marks all package paths binary so exact evidence bytes are not line-ending normalized.

### Predefined F411 Pair-1 campaign acquisition and freeze (2026-09-01T22:55:14+07:00)

- Fresh enumeration identified fixed F411-A controller `066BFF495051727187053106` / COM16 and F411-B payload `066EFF495051727187053015` / COM11; F411-C/D were absent. The human confirmed the unchanged crossed D8/PA9-to-D2/PA10 link, common GND, no D0/D1 wire, both boards powered/connected, no confirmation-time reset/power cycle, and at least 90 uninterrupted minutes.
- Acquisition source was clean synchronized commit `623c783f489a8e9f5de58b9bf66b863f1e33cb54`. Exactly one campaign invocation opened continuous dual capture, performed one exact-target flash/verify/reset sequence, and executed the authoritative plan. There was no retry, replacement, port reopen, intermediate reset/reflash, condition/order/denominator change, or second-pair action.
- Precheck `F411_P1_CAMPAIGN_20260901_B3_PRECHECK` passed: 65.0 s monotonic NORMAL window, 13 ONLINE statuses, `ok` 10→130 strictly increasing, zero timeout/CRC/sequence/recovery deltas, zero prohibited markers, both READY markers, link start/active, ONLINE, and one `Verified OK` flash record per exact identity.
- Campaign accounting is 12 planned, 12 attempted exactly once in order, 12 valid, zero invalid, and zero not attempted. All 12 pre-stabilization and 12 post-stabilization gates passed; all 12 restorations were confirmed. No row was replaced or excluded.
- All three NC rows retained nine accepted mode=0 responses each and zero false timeout, rejection, OFFLINE, recovery, restart, poll-write-failure, overflow/error, receive-loss, or reset/fault markers.
- All three D090 rows retained accepted delayed responses (seven mode=3 accepts per row), zero timeout/rejection/OFFLINE, confirmed restoration, and zero recovery requirement. All three D100 and all three D110 rows retained two explicit timeout-transition markers, one sequence rejection, OFFLINE, confirmed NORMAL restoration, recovery, and passed stabilization; no mode=3 response was accepted in those six rows.
- Cumulative counter accounting is separately retained: every D100/D110 row changed timeout by 8, sequence by 8, CRC by 0, and recovery by 1 between the final pre-gate status and first post-gate status; NC and D090 deltas were all zero. Explicit transition-marker counts must not be conflated with cumulative counter deltas.
- Boundary observations retained transparently: four delayed rows (`C03`, `C05`, `C07`, `C10`) contain one accepted mode=0 response after exact delayed activation confirmation, followed by the attributable condition-specific markers above. One partial final controller record `[OBC] PAYLOAD_AC` occurred after the final complete ONLINE status and row-12 validation while ports were closing; it is outside every scored/stabilization boundary and is not counted.
- Independent validation passed with 660 controller and 36 payload exact-byte records, zero raw-format/render failures, 12 row validations, exact activation confirmations 3/3 per delay, and all four firmware hashes exact. UTC exposure labels span 3.999907–4.000644 s around the fixed monotonic 4.0 s sleep and are not MCU timing.
- Provenance correction: the 32-row preacquisition inventory included the intentionally mutable `attempt_ledger.json`, producing one expected post-run mismatch. Its exact original 12-PLANNED content is preserved as `locked_attempt_ledger.json` and matches the preinventory SHA; the exact final 12-valid content is preserved as `final_attempt_ledger.json`. The other 31 preinventory rows remain unchanged, no raw/scientific evidence was changed, and there is no data loss.
- Final payload state is confirmed NORMAL at 2026-09-01T15:49:01.527250+00:00. Final complete controller status is ONLINE at 2026-09-01T15:49:07.294141+00:00 with stable post-row counters. Both ports are closed and no Python/OpenOCD process remains.
- Evidence root: `research/icsec2026/extension/evidence/f411_pair1_campaign_20260901_seed20260901_b3/`. Complete inventory contains 95 rows with zero issues (96 files including inventory); `F411_PAIR1_CAMPAIGN_SHA256SUMS.csv` SHA-256 is `797F908BCFC5EB5450302360501016DCB23188996C15194D9CF91C8BE619C2BC`.
- Exact-copy backup: `C:/WashiOS-extension-backup/f411_pair1_campaign_20260901_seed20260901_b3`; all 95 rows independently match size and SHA-256, with the same inventory hash and 96 total files. Prior pilot, failed-bring-up, diagnostic, frozen baseline, and reviewed G431/G474 inventory hashes remain unchanged.
- Terminal disposition is `F411_P1_CAMPAIGN_COMPLETE_AWAITING_REVIEW`. This evidence remains one sequential fixed F411 pair and authorizes neither manuscript inclusion nor second-pair work. Next action: commit, synchronize, and stop with `WORK_REVIEW_REQUIRED`.

### Predefined F411 Pair-2 campaign readiness (2026-09-01T23:12:10+07:00)

- Research review authorized exactly one separate Pair-2 campaign `F411_P2_CAMPAIGN_20260901_B3`, using untouched F411-C controller ST-LINK `0669FF495051727187053226` and untouched F411-D payload ST-LINK `0663FF495051727187066042`. Pair-1 remains frozen and is not part of the Pair-2 denominator.
- Starting branch/HEAD was synchronized `experiment/icsec-extension-20260830` / `043d2e4b67e50d8910d0aa64da385500d364adab`; the only initial worktree change was the Research Director's updated `NEXT_TASK.md`. `main` and `origin/main` remain frozen at `8a47d070c549274c59cdbde2495afa8d353a93b3`.
- Pair-1 source and exact-copy backup independently reverified 95/95 rows with zero issues and inventory SHA-256 `797F908BCFC5EB5450302360501016DCB23188996C15194D9CF91C8BE619C2BC`. Prior reviewed extension/F411 packages reverified row-wise where retained, and frozen dataset/provenance inventory-file hashes remain exact.
- Created exclusive Pair-2 package `research/icsec2026/extension/evidence/f411_pair2_campaign_20260901_seed20260901_b3/` with 12 pristine PLANNED ledger rows and the exact authorized order. Pair-2 plan SHA-256 is `7C8A60145CDAFB04BC6F1553B42D401FC35532B64B587D90D62942D4947E103F`.
- The reviewed acquisition/validation engine was configuration-extracted without changing protocol, timing, stabilization, validity, stop, or analysis definitions. The Pair-2 profile changes only permitted IDs, paths, C/D identities, artifact labels, and later fresh ports. Focused tests confirm Pair-2 uses the identical shared `acquire`, `stabilization`, and `outcome_summary` function objects; the refactored validator still validates frozen Pair-1 with zero failures.
- Required tests pass: core 43/43, payload 3/3, and host 18/18. Clean builds exactly reproduce controller ELF/BIN `9AA52D...2D78` / `868611...FE68` and payload ELF/BIN `0BC0EA...5493` / `52F145...BBB`.
- No serial port has been opened, no board has been flashed/reset/observed, and no command has been sent for Pair-2. F411-A/B remain connected from Pair-1 and must be disconnected before C/D enumeration; this physical swap requires human action. Fresh C/D VCP mapping, exact three-wire confirmation, and at least 90 uninterrupted minutes remain pending.
- Human action replaced A/B with Pair-2 and reported the exact crossed three-wire link with no D0/D1 wiring. Read-only software enumeration independently matched F411-C `0669FF495051727187053226` to COM12 and F411-D `0663FF495051727187066042` to COM6; A/B and other ST-LINK VCPs were absent. Both boards remain powered. No VCP was opened and no Pair-2 flash/reset/command occurred. The required explicit confirmation of at least 90 uninterrupted minutes remains pending.
- The human subsequently confirmed at least 90 uninterrupted minutes with both Pair-2 boards still powered, the wiring unchanged, and no reset/disconnect/jumper change. All human and identity gates now pass. Next action is to seal the pre-acquisition inventory, commit/synchronize the exact lock, recheck identity without opening VCPs, and invoke the campaign exactly once.

### Predefined F411 Pair-2 campaign acquisition and freeze (2026-09-01T23:54:10+07:00)

- The final acquisition lock was clean and synchronized at `eb3c15a2396eb80e327ebf8cd142f1f4298430e2`. The 22-row pre-acquisition inventory verified with zero issues at SHA-256 `DE4894ED6056B23E1A7E9A191931B754F3098D9D1B82DFD8456D7650B4A1E9BA`. Pair-1 source and backup reverified 95/95 before acquisition.
- Exactly one Pair-2 invocation used F411-C controller `0669FF495051727187053226` / COM12 and F411-D payload `0663FF495051727187066042` / COM6. It opened one continuous dual capture, performed one exact-target flash/verify/reset sequence, and exited zero. There was no retry, replacement, port reopen, intermediate reset/reflash, order/condition/denominator change, or Pair-1 action.
- Precheck `F411_P2_CAMPAIGN_20260901_B3_PRECHECK` passed: 65.0 s monotonic NORMAL window, 13 ONLINE statuses, strictly increasing `ok` 10→130, zero timeout/CRC/sequence/recovery deltas, zero prohibited markers, both READY/link markers, and exact-target flash verification.
- Campaign accounting is 12 planned, 12 attempted exactly once in fixed order, 12 valid, zero invalid, and zero not attempted. All pre/post stabilizations and all restoration-equivalent confirmations passed.
- All three NC rows retained nine mode-0 accepts and zero adverse markers. All three D090 rows retained accepted delayed responses (7, 7, and 8 mode-3 accepts) without timeout/rejection/OFFLINE. Every D100 and D110 row retained two explicit timeout-transition markers, one explicit sequence rejection, OFFLINE, confirmed NORMAL restoration, recovery, and passed stabilization; none accepted mode-3 responses.
- Boundary evidence is retained: one mode-0 accept occurred in each of C02 D110, C05 D090, and C10 D110 after exact delayed confirmation, followed by attributable condition-specific markers. Every D100/D110 row has cumulative status-boundary deltas timeout=8, seq=8, crc=0, recovery=1; these are not the explicit marker counts. One final partial `[OBC] PAYLOAD_AC` record occurred after the final complete ONLINE status and row-12 validation during port close and is not counted.
- Independent validation passed with 657 controller and 36 payload exact-byte records and zero raw format/render failures. Host timestamp exposure labels span 4.000259–4.001148 s around the fixed monotonic 4.0 s exposure and are not MCU execution timing.
- Final payload NORMAL is confirmed at `2026-09-01T16:52:26.291557+00:00`; final complete controller status is ONLINE at `2026-09-01T16:52:31.969730+00:00`. Both ports are closed and no Python/OpenOCD process remains.
- All prior inventory-file hashes remain unchanged after acquisition, including Pair-1 source and backup `797F908...C2BC` 95/95. The only expected preinventory mismatch is mutable `attempt_ledger.json`; pristine and final ledger copies are separately retained. Next action is final package inventory, exact-copy backup, independent verification, commit/push, and `WORK_REVIEW_REQUIRED`.
- Final Pair-2 inventory contains 81 rows with zero issues (82 package files including the inventory); `F411_PAIR2_CAMPAIGN_SHA256SUMS.csv` SHA-256 is `481F56C98647D037CFAA5698BDEF61C0D918D42954A646E36C7479EA8203588E`. Exact-copy backup `C:/WashiOS-extension-backup/f411_pair2_campaign_20260901_seed20260901_b3` independently verifies all 81 rows with the same inventory hash and 82 files.
- The first backup copy command safely copied zero files because `-LiteralPath` did not expand a wildcard. The empty exclusive target was verified, then populated using explicit child-item objects; source and backup subsequently matched 81/81. This routine backup-tooling failure is retained in `F411_PAIR2_CAMPAIGN_BACKUP_COMPLETION.json` and did not modify or lose evidence.
- Terminal disposition is `F411_P2_CAMPAIGN_COMPLETE_AWAITING_REVIEW`. Pair-2 remains separate from Pair-1 and every prior package. No further F411 campaign or manuscript action is authorized by this milestone. Next action is final commit/synchronization and `WORK_REVIEW_REQUIRED`.

### F411 cross-pair descriptive synthesis and manuscript candidate (2026-09-02T00:18:52+07:00)

- This was an analysis-only milestone. No serial port was opened; no board was powered, reset, flashed, rewired, commanded, or observed. F411 hardware work remains closed.
- Starting state was synchronized branch `experiment/icsec-extension-20260830` at `883f7b5ba48bda5766ba7590a4c6ac39712fdb93`, with only the Research Director's updated `NEXT_TASK.md` modified. `main` and `origin/main` remained frozen at `8a47d070c549274c59cdbde2495afa8d353a93b3`.
- Pair-1 source and exact-copy backup independently reverified 95/95 rows each with zero missing, size, or SHA-256 issues; inventory SHA-256 remains `797F908BCFC5EB5450302360501016DCB23188996C15194D9CF91C8BE619C2BC`. Pair-2 source and backup independently reverified 81/81 rows each with zero issues; inventory SHA-256 remains `481F56C98647D037CFAA5698BDEF61C0D918D42954A646E36C7479EA8203588E`.
- The deterministic generator and focused tests produced separate pair and pair/condition tables, provenance mapping, and a reviewed figure. Pair-1 and Pair-2 each remain 12/12 valid with their own denominators: NC 3/3 clean, D090 3/3 accepted without fault transition, and D100 plus D110 each 3/3 with timeout/sequence-rejection/OFFLINE followed by confirmed NORMAL restoration and recovery. No row, counter, or proportion was pooled.
- Boundary evidence remains explicit: four Pair-1 and three Pair-2 post-activation mode-0 accepts are retained as boundary/pipeline observations, both final partial controller records remain outside scored boundaries, and Pair-2's safely failed zero-file backup attempt remains disclosed. Explicit transition-marker counts and cumulative status-counter deltas are separate fields.
- Two schema-only generator attempts failed before producing scientific outputs and are retained at `research/icsec2026/extension/analysis/f411_cross_pair_synthesis_20260902/` and `_r2/`. A complete `_r3/` output is retained with a figure-QA failure for a clipped colorbar label. The corrected, visually reviewed synthesis is `_r4/`; no source evidence changed.
- The manuscript candidate at `research/icsec2026/extension/manuscript_candidate_f411_20260902/` builds successfully to five pages. Rendered inspection of every page and anonymity/claim audits pass. Candidate PDF SHA-256 is `2E3E684431608396122F018BE45A17BA7F05FAD92F1E017934FC9F624395A3F5`. The original frozen manuscript PDF remains unchanged at `992A1C9AA41F4295BF7F97CA081D79A7DE2ABBB4B419B2A0B82144C1B50928DF`.
- Friday quantitative scope acquisition is `NO-GO` because native waveform export was not proven before acquisition. The only allowed fallback is non-destructive export of the already retained S001 internal-memory waveform as feasibility support; no new trace or screen-derived interval is authorized.
- Final review package: `research/icsec2026/extension/analysis/f411_cross_pair_integration_20260902/`. Its inventory contains 31 rows plus the inventory file, zero verification issues, and SHA-256 `4C0D6FC2AF25228AB3080677D5C14C58DB83029D9041D04610E93F22C3D4BA15`. Exact-copy backup `C:/WashiOS-extension-backup/f411_cross_pair_integration_20260902` independently verifies 31/31 rows with the same inventory hash and 32 files.
- Modified/new milestone files are the Research Director's `NEXT_TASK.md`, synthesis generator/tests and retained generation attempts, final synthesis, manuscript candidate/audits, integration package, and this factual session entry. Validation status: acceptance checks pass; unresolved scientific uncertainty is limited to Research Director acceptance of manuscript inclusion and the unexported S001 feasibility trace. Remaining time: milestone complete. Next action: commit, synchronize, and stop with `WORK_REVIEW_REQUIRED`.

### Accepted F411 manuscript claim correction and promotion (2026-09-02T00:48:29+07:00)

- This was manuscript/analysis work only. No serial port was opened and no board was powered, reset, flashed, rewired, commanded, or observed.
- Starting branch/HEAD was synchronized `experiment/icsec-extension-20260830` / `112459b7dd97ff225259bc9bedba4f7ed5bd4397`; the only starting change was the Research Director's updated `NEXT_TASK.md`. `main`, `origin/main`, and `icsec-2026-evaluated-state` remain `8a47d070c549274c59cdbde2495afa8d353a93b3`.
- A new corrected candidate was created at `research/icsec2026/extension/manuscript_candidate_f411_20260902_corrected/`; the prior candidate and reviewed integration package remain unchanged. Relative to the prior candidate, `main.tex` contains exactly two authorized phrase replacements: the introduction and Discussion now state two separate physical F411 controller/payload pairs under one fixed F411 implementation. Machine validation reports two replacements, zero other source changes, and zero numerical or table changes.
- The corrected manuscript rebuilt successfully to five pages. All five final 144-dpi renders were visually inspected with no clipping, collision, unreadable table, broken reference, or anonymity defect. There are no fatal errors, undefined citations/references, or overfull boxes. Corrected source/PDF/bibliography SHA-256 values are `BD2963900E834BD2623958776476EF4B4576983B8F2926D4FEDA27509D496924`, `D346C39253B8BC44B96968A4509BED14369F0632742352ACA7EE5B8027F42ED3`, and `B936C7F6AF1E173CEB771D5BB430F3652846B759C494E71B674D3071D387AC00`.
- The accepted corrected candidate was promoted byte-for-byte to active extension manuscript path `research/icsec2026/extension/manuscript/`; all 24 files match the candidate. The evaluated frozen manuscript remains at `research/icsec2026/manuscript/main.pdf` with unchanged SHA-256 `992A1C9AA41F4295BF7F97CA081D79A7DE2ABBB4B419B2A0B82144C1B50928DF`.
- Claim, anonymity, layout, and provenance audits pass. Pair-1 source/backup reverified 95/95 and Pair-2 source/backup 81/81 with zero issues and unchanged inventory hashes. The prior 31-row integration source/backup reverified with zero issues. Nineteen frozen/reviewed inventory-file hashes were checked against their recorded values and remain unchanged. Pair-specific 12/12 and 3/3 values, boundary observations, explicit-marker/cumulative-counter distinction, references, and Friday `NO-GO` decision are unchanged.
- Corrected integration package: `research/icsec2026/extension/analysis/f411_claim_correction_20260902/`. Its inventory contains 27 rows plus the inventory file, zero verification issues, and SHA-256 `B832BFA847EE553AC6AD142FFDFABFA5BAF2298D73A0B8A350A042A224311106`. Exact-copy backup `C:/WashiOS-extension-backup/f411_claim_correction_20260902` independently verifies 27/27 rows with the same inventory hash and 28 files.
- Final disposition: `MANUSCRIPT_EXTENSION_ACCEPTED_AWAITING_FINAL_REVIEW`. Modified/new milestone files are the Research Director's `NEXT_TASK.md`, corrected candidate, active extension manuscript, validator, corrected integration package, byte-preservation attributes, and this session entry. Remaining time: milestone complete. Next action: commit, synchronize, and stop with `WORK_REVIEW_REQUIRED`.
