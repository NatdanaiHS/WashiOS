# Next Executable Milestone: Recover the Frozen Baseline Evidence

Go to the lab and locate the exact original frozen-dataset and frozen-provenance bytes on the original machine or media. This milestone is data recovery only: do not connect to, flash, reset, command, or acquire from any board or oscilloscope.

Use a new exclusive staging root outside the frozen repository paths. Treat the source media as read-only. Reconstruct the inventory-relative directory layout using exact original copies for ignored raw logs/binaries/ELFs and exact committed blob bytes for tracked files; do not use CRLF working-tree representations where the inventory requires LF bytes.

Verify every staged artifact against the existing unchanged inventories:

- dataset inventory SHA-256: `DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD`, requiring 195/195 exact rows;
- provenance inventory SHA-256: `84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC`, requiring 65/65 exact rows.

Pass only with zero missing files, zero size mismatches, and zero SHA-256 mismatches across both inventories. Then create a second exclusive copy and independently reverify every row. Record source location, copy commands/tool versions, row counts, mismatches, inventory-file hashes, destination paths, and final verification results in an append-only recovery record outside all frozen evidence and manuscript paths.

Stop immediately if an exact original artifact cannot be found or any row mismatches. Preserve the staging copy and a complete missing/mismatch ledger; do not regenerate an inventory, normalize an unknown original, substitute a rebuild, rerun an experiment, or begin F411/scope work. The frozen commit and manuscript remain unchanged regardless of outcome.
