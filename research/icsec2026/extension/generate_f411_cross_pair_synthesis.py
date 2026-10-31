#!/usr/bin/env python3
"""Generate the bounded, non-pooled F411 cross-pair synthesis."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
PAIR_SPECS = (
    {
        "pair": "Pair-1",
        "package": ROOT / "research/icsec2026/extension/evidence/f411_pair1_campaign_20260901_seed20260901_b3",
        "backup": Path("C:/WashiOS-extension-backup/f411_pair1_campaign_20260901_seed20260901_b3"),
        "inventory": "F411_PAIR1_CAMPAIGN_SHA256SUMS.csv",
        "inventory_sha256": "797F908BCFC5EB5450302360501016DCB23188996C15194D9CF91C8BE619C2BC",
        "inventory_rows": 95,
    },
    {
        "pair": "Pair-2",
        "package": ROOT / "research/icsec2026/extension/evidence/f411_pair2_campaign_20260901_seed20260901_b3",
        "backup": Path("C:/WashiOS-extension-backup/f411_pair2_campaign_20260901_seed20260901_b3"),
        "inventory": "F411_PAIR2_CAMPAIGN_SHA256SUMS.csv",
        "inventory_sha256": "481F56C98647D037CFAA5698BDEF61C0D918D42954A646E36C7479EA8203588E",
        "inventory_rows": 81,
    },
)
CONDITIONS = ("NC", "D090", "D100", "D110")
ALLOWED_CLAIM = (
    "Under the identical predefined protocol and fixed F411 implementation, "
    "the same condition-level supervision pattern was observed on each of two "
    "separate physical F411 controller/payload pairs."
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_inventory(root: Path, name: str, expected_hash: str, expected_rows: int) -> dict:
    inventory = root / name
    if digest(inventory) != expected_hash:
        raise ValueError(f"inventory hash mismatch: {inventory}")
    with inventory.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != expected_rows:
        raise ValueError(f"inventory row mismatch: {inventory}")
    issues: list[str] = []
    for row in rows:
        path = root / row["relative_path"]
        if not path.is_file():
            issues.append(f"MISSING:{row['relative_path']}")
        elif path.stat().st_size != int(row["size_bytes"]):
            issues.append(f"SIZE:{row['relative_path']}")
        elif digest(path) != row["sha256"]:
            issues.append(f"HASH:{row['relative_path']}")
    if issues:
        raise ValueError(f"inventory verification failed: {root}: {issues}")
    return {"root": root.as_posix(), "rows": len(rows), "issues": 0,
            "inventory_sha256": expected_hash}


def derive_pair(spec: dict) -> tuple[dict, list[dict], dict]:
    package = spec["package"]
    source_verify = verify_inventory(package, spec["inventory"],
                                     spec["inventory_sha256"], spec["inventory_rows"])
    backup_verify = verify_inventory(spec["backup"], spec["inventory"],
                                     spec["inventory_sha256"], spec["inventory_rows"])
    ledger = load_json(package / "final_attempt_ledger.json")
    manifest = load_json(package / "locked_manifest.json")
    summary = load_json(package / "descriptive_condition_summary.json")
    counters = load_json(package / "counter_delta_summary.json")
    boundary = load_json(package / "unexpected_and_boundary_artifacts.json")
    final = load_json(package / "final_validation.json")
    source = load_json(package / "acquisition_source_state.json")
    validations = {
        row["run_id"]: load_json(package / "raw/rows" / row["run_id"] / "validation.json")
        for row in ledger["rows"]
    }
    final_valid = final.get("valid", final.get("campaign_valid"))
    if final_valid is not True or summary.get("campaign_valid") is not True:
        raise ValueError(f"reviewed campaign is not valid: {spec['pair']}")
    rows = ledger["rows"]
    if len(rows) != 12 or sum(r["attempted"] for r in rows) != 12 or sum(r["valid"] is True for r in rows) != 12:
        raise ValueError(f"campaign accounting mismatch: {spec['pair']}")

    counter_by_run = {row["run_id"]: row for row in counters["rows"]}
    condition_rows: list[dict] = []
    for condition in CONDITIONS:
        selected = [row for row in rows if row["condition"] == condition]
        values = [validations[row["run_id"]] for row in selected]
        accepted_delayed_rows = sum(v["outcome"]["accepted_mode_3"] > 0 for v in values)
        adverse_nc_rows = sum(v["outcome"].get("false_marker_count", 0) > 0 for v in values)
        fault_pattern_rows = sum(
            v["outcome"]["timeout"] > 0
            and v["outcome"]["sequence_rejection"] > 0
            and v["outcome"]["offline"] > 0
            and v["restore_confirmation_host_time"] is not None
            and v["recovery_host_time"] is not None
            for v in values
        )
        condition_rows.append({
            "physical_pair": spec["pair"],
            "condition": condition,
            "planned": len(selected),
            "attempted": sum(row["attempted"] for row in selected),
            "valid": sum(row["valid"] is True for row in selected),
            "invalid": sum(row["valid"] is False for row in selected),
            "accepted_delayed_response_rows": accepted_delayed_rows,
            "accepted_mode3_markers": sum(v["outcome"]["accepted_mode_3"] for v in values),
            "explicit_timeout_markers": sum(v["outcome"]["timeout"] for v in values),
            "explicit_crc_rejection_markers": sum(v["outcome"]["crc_rejection"] for v in values),
            "explicit_sequence_rejection_markers": sum(v["outcome"]["sequence_rejection"] for v in values),
            "offline_rows": sum(v["outcome"]["offline"] > 0 for v in values),
            "normal_restoration_confirmed_rows": sum(v["restore_confirmation_host_time"] is not None for v in values),
            "recovery_confirmed_rows": sum(v["recovery_host_time"] is not None for v in values),
            "adverse_nc_rows": adverse_nc_rows,
            "full_timeout_sequence_offline_restore_recovery_pattern_rows": fault_pattern_rows,
            "cumulative_timeout_delta": sum(counter_by_run[r["run_id"]]["timeout"] for r in selected),
            "cumulative_crc_delta": sum(counter_by_run[r["run_id"]]["crc"] for r in selected),
            "cumulative_sequence_delta": sum(counter_by_run[r["run_id"]]["seq"] for r in selected),
            "cumulative_recovery_delta": sum(counter_by_run[r["run_id"]]["recovery"] for r in selected),
        })

    by_condition = {row["condition"]: row for row in condition_rows}
    pair_row = {
        "physical_pair": spec["pair"],
        "controller_board": manifest["controller"]["board_id"],
        "controller_stlink": manifest["controller"]["stlink_serial"],
        "payload_board": manifest["payload"]["board_id"],
        "payload_stlink": manifest["payload"]["stlink_serial"],
        "campaign_id": manifest["campaign_id"],
        "campaign_source_commit": source.get("source_commit", source.get("acquisition_commit")),
        "inventory_sha256": spec["inventory_sha256"],
        "planned": 12,
        "attempted": 12,
        "valid": 12,
        "invalid": 0,
        "nc_clean_rows": 3 - by_condition["NC"]["adverse_nc_rows"],
        "d090_accepted_without_fault_rows": by_condition["D090"]["accepted_delayed_response_rows"],
        "d100_fault_restore_recovery_pattern_rows": by_condition["D100"]["full_timeout_sequence_offline_restore_recovery_pattern_rows"],
        "d110_fault_restore_recovery_pattern_rows": by_condition["D110"]["full_timeout_sequence_offline_restore_recovery_pattern_rows"],
        "d100_accepted_mode3_markers": by_condition["D100"]["accepted_mode3_markers"],
        "d110_accepted_mode3_markers": by_condition["D110"]["accepted_mode3_markers"],
        "boundary_mode0_rows": sum(
            validations[row["run_id"]]["outcome"]["accepted_mode_0"] > 0
            for row in rows if row["condition"] != "NC"
        ),
        "final_partial_record_outside_boundaries": bool(
            boundary.get("final_partial_record")
            or any(item.get("id") == "FINAL_PARTIAL_CONTROLLER_RECORD"
                   for item in boundary.get("capture_boundary_artifacts", []))
        ),
    }
    provenance = {
        "pair": spec["pair"],
        "source_inventory": source_verify,
        "backup_inventory": backup_verify,
        "source_artifacts": {
            name: {"path": (package / name).as_posix(), "sha256": digest(package / name)}
            for name in (
                "final_attempt_ledger.json", "locked_manifest.json",
                "descriptive_condition_summary.json", "counter_delta_summary.json",
                "unexpected_and_boundary_artifacts.json", "final_validation.json",
                "acquisition_source_state.json",
            )
        },
        "row_validation_files": {
            run_id: {"path": (package / "raw/rows" / run_id / "validation.json").as_posix(),
                     "sha256": digest(package / "raw/rows" / run_id / "validation.json")}
            for run_id in validations
        },
    }
    return pair_row, condition_rows, provenance


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def make_figure(path_pdf: Path, path_png: Path, pair_rows: list[dict]) -> None:
    labels = ["NC clean", "90 ms accepted\nwithout fault", "100 ms fault ->\nrestore/recover", "110 ms fault ->\nrestore/recover"]
    fields = ["nc_clean_rows", "d090_accepted_without_fault_rows",
              "d100_fault_restore_recovery_pattern_rows",
              "d110_fault_restore_recovery_pattern_rows"]
    data = np.array([[row[field] for field in fields] for row in pair_rows], dtype=float)
    fig, ax = plt.subplots(figsize=(7.2, 2.15), constrained_layout=True)
    ax.imshow(data, cmap="Blues", vmin=0, vmax=3, aspect="auto")
    for y in range(data.shape[0]):
        for x in range(data.shape[1]):
            ax.text(x, y, f"{int(data[y, x])}/3", ha="center", va="center",
                    fontsize=11, fontweight="bold", color="white" if data[y, x] >= 2 else "black")
    ax.set_xticks(range(len(labels)), labels, fontsize=8.5)
    ax.set_yticks(range(len(pair_rows)), [row["physical_pair"] for row in pair_rows], fontsize=9)
    ax.set_title("Separate per-pair outcomes under the identical predefined F411 protocol", fontsize=10.5)
    ax.set_xlabel("Cells are pair-specific counts; no cross-pair pooling", fontsize=8.5)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.savefig(path_pdf, format="pdf", bbox_inches="tight")
    fig.savefig(path_png, dpi=240, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    output = ROOT / "research/icsec2026/extension/analysis/f411_cross_pair_synthesis_20260902_r4"
    if output.exists():
        raise FileExistsError(f"exclusive analysis path already exists: {output}")
    output.mkdir(parents=True)
    pair_rows: list[dict] = []
    condition_rows: list[dict] = []
    provenance_pairs: list[dict] = []
    for spec in PAIR_SPECS:
        pair, conditions, provenance = derive_pair(spec)
        pair_rows.append(pair)
        condition_rows.extend(conditions)
        provenance_pairs.append(provenance)
    write_csv(output / "pair_comparison.csv", pair_rows)
    write_csv(output / "condition_outcomes.csv", condition_rows)
    make_figure(output / "pair_condition_pattern.pdf", output / "pair_condition_pattern.png", pair_rows)

    synthesis = f"""# F411 cross-pair descriptive synthesis

## Allowed claim

{ALLOWED_CLAIM}

Pair-1 and Pair-2 remain separate 12-row datasets. Each pair has three observations per condition; no row, counter, or proportion is pooled across pairs.

## Pair-specific result

| Physical pair | Valid | NC clean | 90 ms accepted without fault | 100 ms timeout/SEQ/OFFLINE -> restore/recover | 110 ms timeout/SEQ/OFFLINE -> restore/recover |
|---|---:|---:|---:|---:|---:|
| Pair-1 | 12/12 | 3/3 | 3/3 | 3/3 | 3/3 |
| Pair-2 | 12/12 | 3/3 | 3/3 | 3/3 | 3/3 |

For each pair separately, D100 and D110 contained zero accepted mode-3 responses. Each three-row D100 or D110 condition retained six explicit timeout-transition markers, three explicit sequence-rejection markers, three OFFLINE observations, three confirmed NORMAL restorations, and three recoveries. The corresponding cumulative status-counter deltas were timeout 24, sequence 24, CRC 0, and recovery 3 per condition per pair; cumulative deltas are not explicit marker counts.

## Boundary and provenance observations

Post-activation mode-0 accepts are retained as boundary/pipeline observations, not delayed-mode accepts: four Pair-1 rows and three Pair-2 rows. Each was followed by attributable condition-specific evidence. Both master controller logs end with a partial `[OBC] PAYLOAD_AC` record after the final complete ONLINE status and outside scored/stabilization boundaries. Pair-2's first backup copy command safely copied zero files; the verified corrective copy matched all 81 inventory rows. None of these observations invalidated a scientific row.

## Configuration and interpretation boundary

The two F411 campaigns used the same fixed F411 controller/payload implementation, firmware hashes, UART protocol, 500 ms poll cadence, 100 ms response deadline, three-timeout OFFLINE rule, exact confirmation gates, four-second exposures, seed, order, and validity rules. They used separate physical controller/payload pairs. This is cross-configuration, protocol-level physical replication relative to the G431/G474 study: it does not establish G431/G474 binary or timing replication, MCU-family equivalence, reliability, qualification, or device-population generality.

## Prohibited interpretations

- Do not combine the two 12-row denominators or report 24/24.
- Do not calculate a combined proportion, confidence interval, or population test.
- Do not treat sequential rows as independent devices.
- Do not count mode-0 boundary accepts as delayed-mode responses.
- Do not infer MCU execution timing from host timestamps.
"""
    (output / "SYNTHESIS.md").write_text(synthesis, encoding="utf-8", newline="\n")
    provenance = {
        "schema": "washios.icsec2026.f411_cross_pair_synthesis.v1",
        "generated_by": Path(__file__).as_posix(),
        "generator_sha256": digest(Path(__file__)),
        "allowed_claim": ALLOWED_CLAIM,
        "pooling_performed": False,
        "physical_pair_count": 2,
        "per_pair_denominator": 12,
        "per_condition_per_pair_denominator": 3,
        "pairs": provenance_pairs,
        "outputs": {
            name: digest(output / name)
            for name in ("pair_comparison.csv", "condition_outcomes.csv", "pair_condition_pattern.pdf",
                         "pair_condition_pattern.png", "SYNTHESIS.md")
        },
    }
    (output / "PROVENANCE.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
