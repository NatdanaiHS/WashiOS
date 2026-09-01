# ICSEC 2026 Lab-Extension Recovery Checkpoint

Recovery performed: 2026-09-01T15:51:37+07:00

This checkpoint reconstructs the repository and retained evidence after the 2026-08-30 lab session. It does not infer completion from plans or manuscript prose, and it did not start an experiment, communicate with a board, flash firmware, or modify `NEXT_TASK.md`.

## 1. Git / provenance state

### Git state before this recovery report

- Active branch: `experiment/icsec-extension-20260830`.
- Local HEAD: `06f1ab7fa7dffb3d0a6d5b30216e4d3713d1f80e`.
- Upstream: `origin/experiment/icsec-extension-20260830` at the same commit; ahead/behind was `0/0` after `git fetch --prune origin`.
- The working tree was clean.
- `main`, `origin/main`, and tag `icsec-2026-evaluated-state` all resolve to the frozen commit `8a47d070c549274c59cdbde2495afa8d353a93b3` (`8a47d07`). That commit is an ancestor of the extension HEAD.
- A path-limited `git diff` from the frozen commit to extension HEAD found no Git changes to the frozen dataset, frozen provenance package, or submission-safe manuscript.
- `NEXT_TASK.md` remains at the reviewed oscilloscope milestone and was not changed during recovery.

### Inventory-file state versus retained-file state

The following inventory *files* retain their recorded SHA-256 values:

| Package | Inventory | Inventory-file SHA-256 | Current row verification |
|---|---|---:|---:|
| Frozen 90-trial dataset | `research/icsec2026/runs/full_20260830_seed20260830_n30/SHA256SUMS.csv` | `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD` | **10/195 paths present; 185 missing; 9 exact; 1 checkout line-ending mismatch** |
| Frozen provenance | `research/icsec2026/provenance/20260830_023830/PROVENANCE_SHA256SUMS.csv` | `84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC` | **55/65 paths present; 10 missing; 28 exact; 27 checkout line-ending mismatches** |
| Primary extension | `research/icsec2026/extension/evidence/primary_20260830_seed20260830_b5/EXTENSION_SHA256SUMS.csv` | `8B4CB2AB87CD317905AA4A219B81E99E2E459DC3EEF386D14286297476177C0B` | 88/88, zero issues |
| G431-B replication | `research/icsec2026/extension/evidence/replication_g431b_20260830_seed20260830_b3/REPLICATION_SHA256SUMS.csv` | `F13EBB7FEB42FB3F67E56A8503CB6D70A5F630F2C864A16B22D5BF4D9D19CCE9` | 42/42, zero issues |
| Scope feasibility | `research/icsec2026/extension/evidence/scope_g431b_g474a_110ms_20260830/SCOPE_FEASIBILITY_SHA256SUMS.csv` | `519E7E142DFAFEA4736CA74D945B3197D106714F9B6B1A6B45C75309EC4B1B0E` | 19/19, zero issues |

The frozen Git commit is unchanged, but the current checkout is **not a complete copy of the frozen baseline evidence**. The missing frozen-dataset paths are the 180 campaign raw serial logs, four N0 raw serial logs, and `firmware/g474_payload_firmware.bin`. The missing frozen-provenance paths are:

- `flash/g431_full_flash_0x08000000_0x20000.bin`
- `flash/g431_openocd_read.log`
- `flash/g474_full_flash_0x08000000_0x80000.bin`
- `flash/g474_openocd_read.log`
- `rebuild/g431_application/build.log`
- `rebuild/g431_application/firmware.bin`
- `rebuild/g431_application/firmware.elf`
- `rebuild/g431_bootloader/build.log`
- `rebuild/g431_bootloader/firmware.bin`
- `rebuild/g431_bootloader/firmware.elf`

Those suffixes are excluded by repository-level `*.log`, `*.bin`, and `*.elf` ignore rules, and the files are not present in the frozen Git tree. The 28 present byte mismatches are text files checked out with CRLF endings: all 28 reproduce their inventory hashes after CRLF-to-LF normalization, and the canonical LF bytes remain recoverable from Git. They are reported as current-worktree byte mismatches, not content changes. The known backup root `C:/WashiOS-extension-backup/` contains complete backups of the three extension packages, but no frozen-baseline backup. No alternate copy was found in the repository or known extension backup; a broad user-profile search was stopped before exhaustive completion. The frozen inventories must not be regenerated or silently altered. Recovery of the exact missing bytes from the original lab machine/media is the immediate evidence-integrity priority.

## 2. Exact completed Aug 30 experiments

### Extended nominal N0

- `NOMINAL_002` is the one completed valid extended nominal observation: requested/observed duration 605 s, 121 ONLINE status records, strictly increasing `ok`, zero timeout/CRC/sequence/recovery counter deltas, and no prohibited transition or restart markers.
- Machine evidence: `nominal_validation_002.json` and exact-byte dual logs under `raw/nominal/NOMINAL_002/` in the primary extension package.

### Interleaved Normal Controls

- Primary G431-A/G474-A campaign: six valid NC observations across the retained three-block execution. All six have zero CRC rejection, sequence rejection, timeout, OFFLINE, recovery, restart, and poll-write-failure markers.
- G431-B/G474-A replication: three additional valid NC observations, one per block, with the same zero-false-marker result.
- These are interleaved controls for their respective sequential campaigns; they are not independent board-pair replicates.

### Inter-trial stabilization

- All 24 valid primary campaign rows passed both pre- and post-trial stabilization gates.
- The retained invalid `R002_B1_D500` passed its pre-gate but did not confirm NORMAL restoration and therefore has no valid post-gate.
- Both valid BAD_CRC exposures passed pre- and post-exposure stabilization.
- All 12 G431-B replication observations passed pre- and post-trial stabilization, and the package readiness gate passed.
- Scope attempt `S001_D110` passed pre- and post-attempt stabilization.
- One exceptional payload-only recovery operation after `R002` was separately validated and retained; it was not classified as a trial.

### Variable-delay characterization on G431-A/G474-A

- Valid observations: 18 total, three each at 50, 90, 100, 110, 150, and 250 ms.
- 50 and 90 ms: delayed response accepted in 3/3 at each delay; no timeout, sequence rejection, or OFFLINE marker.
- 100, 110, 150, and 250 ms: accepted response 0/3 at each delay; timeout, sequence rejection, and OFFLINE observed in 3/3 at each delay; NORMAL restoration and recovery confirmed in 3/3.
- The final primary campaign accounting is 45 original plan rows, 25 attempted, 24 valid including six NC rows, one invalid retained, and 20 removed from scope by review. It is descriptive evidence from one physical board pair.

### BAD_CRC to OFFLINE characterization

- SHORT exposure completed valid: ordered raw markers show an accepted normal response, `PAYLOAD_REJECT reason=CRC`, then `PAYLOAD_TIMEOUT consecutive=1`; no OFFLINE marker; NORMAL restoration and stabilization passed.
- SUSTAINED exposure completed valid: ordered raw markers show accepted normal response, CRC rejection, timeout consecutive 1, timeout consecutive 2, then `PAYLOAD_OFFLINE consecutive=3`; harness control flow waited for OFFLINE before sending NORMAL; restoration, recovery, and stabilization passed.
- The derived field `offline_before_restore=false` is not used because it contradicts the usable raw-marker/control-flow evidence boundary.

### Second-G431 replication

- G431-B identity: ST-LINK `0029002B3032511537333436`; controller host port was COM10 during acquisition.
- Same G474-A identity as primary: ST-LINK `0041003D3234510F37333934`; host port was COM9.
- Exact precommitted plan completed: 12/12 valid, zero invalid or replacement rows; three NC plus three each at 90, 100, and 110 ms.
- 90 ms reproduced acceptance without timeout/sequence/OFFLINE in 3/3. At both 100 and 110 ms, acceptance was 0/3 and timeout/sequence rejection/OFFLINE plus restoration/recovery occurred in 3/3. NC false-marker count was zero in all three observations.
- Supported claim: selected observations were reproduced on a second physical G431 controller using the same G474-A. This is not an independent board-pair replication.

### Oscilloscope feasibility

- One planned 110 ms capture (`S001_D110`) was attempted and was serial-valid: exact activation, dual serial logs, NORMAL restoration, and pre/post stabilization are retained.
- Scope: Hantek DSO4254C; CH1 G474-A PA8/D7, CH2 G431-B PA8/D7, 10X/DC, 1 V/div, 20 ms/div, CH1 rising trigger at 1.64 V, SINGLE, 32K memory, actual 12.50 kSa/s (80 us/sample).
- Human observation reported a clean CH1 rise followed by CH2 while CH1 remained high. The scope saved Wave(Binary) internally in slot 1.
- This completed only bounded edge feasibility. It did **not** complete a quantitative timing trace.

## 3. Exact missing/incomplete experiments

- `NOMINAL_001` is retained invalid, not completed: the G431 nominal interval was captured, but G474 serial capture ended with `ClearCommError` and final NORMAL confirmation failed. Both raw logs remain in the primary package; no campaign row followed it.
- `R002_B1_D500` is retained invalid, not replaced: exact 500 ms activation occurred, but the payload's blocking delayed-response handler starved host-command processing; NORMAL was sent but not confirmed, restoration failed, and no post-stabilization gate exists.
- The other planned 500 ms observations, `R011` and `R021`, were never attempted and were review-removed.
- Original primary blocks 4 and 5 were never attempted and were review-removed. Together with `R011` and `R021`, the removed count is 20.
- No variable-delay observation above 250 ms is valid; no 500 ms result may enter a valid denominator.
- Oscilloscope `S002` through `S005` were not attempted and are retained as dropped-unattempted ledger rows. There are zero machine-readable timing traces, zero extracted endpoint-to-timeout intervals, and therefore no timing summary.
- No F411 firmware was built, flashed, or tested for either experiment role.

## 4. Unexpected findings

- A 500 ms delayed response continuously drained queued polls in the payload's blocking handler and prevented timely host-command processing. This made the mandated restoration/stabilization sequence infeasible without changing the implementation or condition set, leading to the reviewed scope-down.
- The primary transition was sharp in these observations: 90 ms accepted in 3/3, whereas 100 ms and above through 250 ms timed out in 3/3. G431-B reproduced the 90/100/110 all-or-none pattern with the same G474-A. This remains descriptive, not a population threshold estimate.
- SHORT BAD_CRC produced a CRC rejection and one timeout without OFFLINE; SUSTAINED BAD_CRC produced the raw ordered CRC-to-three-timeout-to-OFFLINE sequence.
- The scope could provide the required 20 ms/div window only at 12.50 kSa/s. The one internal waveform could not be exported because no USB media was available, so the observed edges cannot support a quantitative interval or MCU execution-time claim.
- Recovery discovered that the frozen inventory files are present and unchanged but most frozen raw/binary evidence is absent from the checkout. Earlier session text claiming all frozen rows reverified describes the original lab state and is not true of this recovered checkout.

## 5. Evidence paths and validation status

### Primary extension

- Root: `research/icsec2026/extension/evidence/primary_20260830_seed20260830_b5/`
- Final validator: `final_validation.json` reports `valid=true`, zero failures, and zero raw-log format failures.
- Ledger: `final_results_ledger.csv`; campaign records: `campaign_results.json` and `continuation_results.json`; BAD_CRC: `bad_crc_results.json`; descriptive output: `descriptive_summary.json`.
- Firmware hashes: G431 application `6515796C07D37C19E21B0104B477EA4C6451B66A995EBEF6510725764441E727`; matched bootloader `FE591BF7292AD0D40F8FEE4AF5779118AE0D0083FF362F5BE9CCB156ADFE619E`; G474 payload `5581492429080BD58177A37733981ABA12DA6074BA40EAC0157B86E027B479E7`.
- Source and exact-copy backup independently reverify 88/88 rows with zero issues. Backup: `C:/WashiOS-extension-backup/primary_20260830_seed20260830_b5/`.

### G431-B replication

- Root: `research/icsec2026/extension/evidence/replication_g431b_20260830_seed20260830_b3/`
- Final validator: `final_validation.json` reports valid with zero validation and raw-log failures.
- Ledger/result evidence: `results_ledger.csv`, `results.json`, and `descriptive_cross_controller_summary.json`.
- Source and exact-copy backup independently reverify 42/42 rows with zero issues. Backup: `C:/WashiOS-extension-backup/replication_g431b_20260830_seed20260830_b3/`.

### Scope feasibility

- Root: `research/icsec2026/extension/evidence/scope_g431b_g474a_110ms_20260830/`
- `validation.json` validates the feasibility record but explicitly fails the quantitative milestone: fewer than five timing traces, no native waveform, no machine-readable data, no screenshot, and no extracted interval.
- Attempt/disposition: `capture_results.json`, `capture_disposition.csv`, and `FEASIBILITY_RECORD.json`; exact settings: `scope_settings.json` and `measurement_protocol.json`.
- Source and exact-copy backup independently reverify 19/19 rows with zero issues. Backup: `C:/WashiOS-extension-backup/scope_g431b_g474a_110ms_20260830/`.

### Frozen baseline

- Frozen Git state and the two inventory-file hashes remain unchanged.
- Full row-level validation is currently impossible because 185 dataset artifacts and 10 provenance artifacts are absent. Of the retained paths, one dataset text file and 27 provenance text files are CRLF working-tree representations; each matches its inventory after deterministic LF normalization, and its canonical LF blob remains in Git. The missing artifacts are an evidence-integrity failure of the recovered checkout, not evidence that the original bytes changed.

## 6. F411 feasibility assessment

This was a read-only source, build-configuration, board-manual, and MCU-datasheet audit. The four physical NUCLEO-F411RE identities and condition were not enumerated or tested.

### Existing build support

- Controller/core: `core/platformio.ini` has `[env:genericSTM32F411RE]` using `board = genericSTM32F411RE` and STM32Cube. It is a generic F4 portability build, not a NUCLEO-F411RE experiment-role environment.
- Bootloader: `bootloader/platformio.ini` has no F411 environment; its WashiBoot layout and build flags are G431-specific.
- Payload simulator: `demo-payload/platformio.ini` has no F411 environment; its only embedded environments are G474 and G474 scope instrumentation.
- PlatformIO itself includes a `nucleo_f411re` board definition, so an ST-LINK-targeted board environment can be added later without creating a custom board definition.

### UARTs, pins, and VCP conflict

- On NUCLEO-F411RE, the default ST-LINK virtual COM path uses USART2: PA2/USART2_TX on Arduino D1 and PA3/USART2_RX on Arduino D0. This is the appropriate host observation/control UART for both roles.
- USART2 therefore must not also be used for the payload link. Electrically attaching a second driver to the VCP-connected path would create a conflict; changing the board solder bridges would also make host setup less uniform.
- The smallest clean payload-link choice is USART1 on PA9/USART1_TX and PA10/USART1_RX. On this board PA9 is Arduino D8/CN10 pin 21 and PA10 is Arduino D2/CN10 pin 33, so the pair can retain ST-LINK VCP on USART2 while cross-connecting USART1 TX/RX and common ground.
- USART6 is another MCU alternate-function option (for example PC6/PC7), and those pins are exposed on the Morpho connectors, but USART1 PA9/PA10 is the simpler, better-documented experiment wiring choice.
- Sources: ST UM1724, *STM32 Nucleo-64 boards (MB1136)*, connector/VCP tables (`https://www.st.com/resource/en/user_manual/um1724-stlinkv21-in-circuit-debuggerprogrammer-for-stm8-and-stm32-stmicroelectronics.pdf`); ST STM32F411xC/xE datasheet, alternate-function table (`https://www.st.com/resource/en/datasheet/stm32f411re.pdf`).

### Current semantic gaps and smallest required changes

The controller and payload roles are portable in principle, but neither current F411 build preserves the experiment semantics:

1. Add explicit `nucleo_f411re` controller and payload build environments, with separate experiment-role flags and ST-LINK upload/debug configuration.
2. Generalize the controller's `WASHIOS_PAYLOAD_DEMO && STM32G431xx` compile guards so `PayloadLinkTask` can run on F411.
3. Add a second F411 UART for the payload link, preferably USART1 PA9/PA10, while keeping USART2 PA2/PA3 for host logs/control.
4. Implement F4 interrupt-driven receive and a ring buffer for the payload UART. The current F4 `Stm32Uart::available()` returns zero and receive is blocking; that cannot preserve the controller's nonblocking polling/parser behavior.
5. Port the demo payload's G4-specific HAL include, clock/pin setup, USART status/clear-register handling, and IRQ routines to F4 while preserving exact command parsing, activation confirmation, response modes, and host logging.
6. Preserve the experimental constants and control flow exactly: protocol framing/CRC/sequence behavior, 115200 8N1, 500 ms poll cadence, 100 ms deadline, three-consecutive-timeout OFFLINE rule, exact requested-delay confirmation, NORMAL restoration, and stabilization gates.
7. Decide explicitly whether F411 uses a standalone application at `0x08000000` or receives a new F411 WashiBoot port. The bootloader is not the measured payload-supervision construct, so standalone deployment is the smallest engineering path, but it is a recorded platform difference and cannot be called binary/configuration replication.

### Pair feasibility and scientific comparability

- With four healthy NUCLEO-F411RE boards, two physically independent F411-controller/F411-payload pairs are technically feasible: each board has ST-LINK VCP on USART2 for host control/observation and a separate exposed USART1 link. Each pair requires crossed PA9/PA10 and common ground, distinct ST-LINK serial identities, and separate host ports.
- The result would **not be directly comparable as MCU-level timing replication** of G431/G474 because both endpoints change MCU family, clock tree, HAL/register implementation, UART behavior, binary, and potentially boot/watchdog behavior.
- If the wire protocol, injected behavior, controller state machine, deadlines, activation evidence, and gates are preserved, it can be reported as **protocol-level/cross-platform replication**. Counts must not be pooled with the G431/G474 observations or described as independent replications of the same hardware configuration.
- It would be scientifically inappropriate if used to claim a G431 hardware threshold, G474 response timing, MCU-internal execution latency, or direct board-population generalization.
- Overall engineering risk: **HIGH**. The electrical layout is straightforward, but both experimental roles require unimplemented F4 interrupt-UART work, the payload is G4-specific, and the F411 boot/deployment equivalence is unresolved. Host-only tests reduce but do not remove the need for careful on-hardware semantic validation.

## 7. Hardware-only tasks that still require G431/G474 lab access

- Export the Hantek internal Wave(Binary) slot 1 through supported media/software, preserving the native file and scope metadata. Until exported, S001 remains human-observed feasibility only. Export does not retroactively supply the four unattempted traces.
- If the Research Director reauthorizes a quantitative scope milestone, reacquire at least five native traces with machine-readable exports and screenshots under a sampling/window configuration adequate for the stated construct. This is a new campaign and must not be inferred from S001.
- Any additional G431/G474 conditions, controllers, payload boards, oscilloscopes, resets, flashes, or observations require renewed lab access and fresh identity/port verification.
- No hardware access is needed to recover missing frozen files if an original storage copy exists; that is a data-recovery task. Re-running the frozen 90-trial campaign would create new evidence and would not restore the original bytes.

## 8. Recommended checkpoint from which work should continue

1. Treat the three extension packages as the current intact evidence checkpoint: primary scope-down complete, G431-B replication complete within its claim boundary, and scope quantitative timing dropped with one retained feasibility attempt.
2. Before any scientific reuse or submission claim that depends on the frozen 90-trial baseline/provenance, locate an exact original copy of the 195 missing frozen artifacts and verify each byte against the existing frozen inventories. Do not regenerate inventories and do not substitute reruns.
3. Await the Research Director's next `NEXT_TASK.md`. Do not begin F411 implementation from this report alone. If F411 is selected, define the claim in advance as protocol-level/cross-platform replication and bring up one role/pair at a time before committing scarce hardware time to two pairs.
4. Keep the primary sustained BAD_CRC claim tied to ordered raw markers and the harness wait-for-OFFLINE control flow; do not cite `offline_before_restore=false`.
