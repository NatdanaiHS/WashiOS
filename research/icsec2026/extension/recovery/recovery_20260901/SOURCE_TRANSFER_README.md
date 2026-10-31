# WashiOS Frozen-Baseline Evidence Transfer

## Package identity

- Packaging timestamp: `2026-09-01T19:15:55.5657824+07:00`
- Source repository: `C:\WashiOS`
- Source Git branch: `experiment/icsec-extension-20260830`
- Source Git HEAD: `5d42a209cf8c2edd7787cbff46de04c6592badd8`
- Source working tree at pre-copy checkpoint: `CLEAN`

## Required original evidence paths

- `C:\WashiOS\research\icsec2026\runs\full_20260830_seed20260830_n30`
- `C:\WashiOS\research\icsec2026\provenance\20260830_023830`

Both required directories were found at exactly these paths.

## Included companion metadata

The package preserves repository-relative paths beneath the transfer root and includes:

- the complete `full_20260830_seed20260830_n30` directory, including `DATASET_README.md`, `manifest.json`, `run_plan.csv`, `results.csv`, `summary.json`, `validation.json`, all 180 raw controller/payload logs, the packaged G474 firmware binary, and `SHA256SUMS.csv`;
- every file referenced by the frozen dataset inventory, which adds the complete pre-campaign N0 package `n0_pre_20260830_0205` and post-campaign N0 package `n0_post_20260830_0224`;
- the complete `20260830_023830` provenance addendum, including its inventory, read-only full-flash captures and OpenOCD logs, capture reports, binary comparison reports, flash-layout inventories, clean rebuild binaries/ELFs/logs/reports, source-state patches and selected untracked source copies, toolchain/package metadata, executable hashes, and provenance scripts;
- deterministic table-generation metadata explicitly needed to reproduce the frozen projections: `generate_manuscript_tables.py`, `TABLE_PROVENANCE.json`, `n0_controls.csv`, `fault_outcomes.csv`, and `latency_summary.csv`;
- `research/icsec2026/SESSION_STATE.md`, because the frozen dataset and provenance documentation explicitly reference it for the working-state and independent inventory hashes.

The table-provenance inputs are already present through the campaign and N0 packages. Their recorded generator, input, and output SHA-256 values were verified before copying.

## Intentionally excluded

- The frozen manuscript and its PDF/build/render artifacts were not copied or modified.
- Later paper-direction, claim-matrix, narrative method/results/limitations, and submission-extension artifacts were excluded, except for the explicitly requested deterministic table generator/provenance/outputs listed above.
- The pre-campaign pilot directory was not copied because it is not listed by either frozen baseline inventory and is not part of the approved 90-trial campaign/N0 dataset. Its existence was checked; it is not a missing reference.
- Live repository source files outside the provenance addendum were not copied. The provenance package already contains the frozen tracked-worktree patch, staged patch, tracked-file list, selected untracked source copies, source inventory, build artifacts, and toolchain records.
- Git object/history data (`.git`) was not copied or altered; branch, HEAD, and status are recorded here instead.
- External PlatformIO/framework/toolchain directory trees were not added. The original provenance explicitly records that they were not vendored and supplies package metadata, selected versions, paths, build logs, and executable hashes instead.
- No unrelated evidence created after the original campaign was collected.

## Counts and size

- Copied source-evidence files: `268`
- Copied source-evidence size: `1,608,098` bytes
- Final transfer-directory files, including this README and the inventory: `270`
- Final transfer-directory size: `0001663907` bytes

`TRANSFER_FILE_INVENTORY.csv` inventories all copied evidence plus this README. It intentionally does not self-list because a file cannot contain its own final SHA-256.

## Integrity and source-preservation result

- Frozen dataset inventory SHA-256: `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD`
- Frozen provenance inventory SHA-256: `84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC`
- Dataset inventory verification: 195 rows, zero missing files, size mismatches, or hash mismatches.
- Provenance inventory verification: 65 rows, zero missing files, size mismatches, or hash mismatches.
- Copy verification: 268 copied files, zero count/size/hash mismatches against the pre-copy source snapshot.
- Source post-copy verification: zero size, timestamp, or SHA-256 changes across all 268 selected source files.
- Git branch, HEAD, and porcelain status remained unchanged during copying.

The source evidence was read only. No original evidence was modified, renamed, moved, deleted, regenerated, overwritten, or repaired. No experiment, flash operation, build, table generation, Git history operation, commit, or push was performed.

## Uncertainty and referenced artifacts

No referenced frozen-baseline artifact was missing. All repository-relative files listed by the two frozen inventories and all paths/hashes recorded by `TABLE_PROVENANCE.json` were located and verified.

The original provenance limitations remain unchanged: captures cover internal user flash rather than option bytes/OTP/system ROM/RAM/peripheral state; unattributed non-`0xFF` flash regions remain uninterpreted; and external dependency trees were not fully vendored. These are documented scope limitations, not packaging omissions or newly discovered missing artifacts.
