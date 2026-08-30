"""Generate manuscript tables only after verifying the frozen evidence hashes."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
PAPER_DIR = Path(__file__).resolve().parent
TABLE_DIR = PAPER_DIR / "tables"

SOURCES = {
    "campaign_summary": (
        "research/icsec2026/runs/full_20260830_seed20260830_n30/summary.json",
        "124554F98A93639B4C2C8C18A708DC14A1D5673823A4CD2F84DB0F563083E1CA",
    ),
    "campaign_validation": (
        "research/icsec2026/runs/full_20260830_seed20260830_n30/validation.json",
        "D06426EE043D32B032FA3267E7A8DDAB0AD345FD1F69807E93E9F47507BA84EB",
    ),
    "pre_n0_validation": (
        "research/icsec2026/runs/n0_pre_20260830_0205/validation.json",
        "872BA8EFD5E8F3505C6DEC62AFCAAC59A892D1ED407DDE67E7256B631FBEAA12",
    ),
    "post_n0_validation": (
        "research/icsec2026/runs/n0_post_20260830_0224/validation.json",
        "B3EF1165183D2EEBB0049B11D006A602D2EE36AE5669BD8EA5E92BA091E095F1",
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_verified_sources() -> dict[str, dict]:
    loaded = {}
    for key, (relative, expected) in SOURCES.items():
        path = REPO / relative
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(f"Frozen source hash mismatch: {relative}: {actual} != {expected}")
        loaded[key] = json.loads(path.read_text(encoding="utf-8"))
    if loaded["campaign_validation"].get("valid") is not True:
        raise RuntimeError("Frozen campaign validation is not valid")
    if loaded["campaign_validation"].get("issues"):
        raise RuntimeError("Frozen campaign validation contains issues")
    return loaded


def write_csv(name: str, fieldnames: list[str], rows: list[dict]) -> Path:
    path = TABLE_DIR / name
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return path


def main() -> None:
    evidence = load_verified_sources()
    summary = evidence["campaign_summary"]
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    n0_rows = []
    for key in ("pre_n0_validation", "post_n0_validation"):
        source = evidence[key]
        records = source["status_records"]
        n0_rows.append(
            {
                "phase": source["phase"],
                "duration_s": source["duration_s"],
                "status_records": source["status_count"],
                "all_status_online": str(source["all_status_online"]).lower(),
                "ok_first": records[0]["ok"],
                "ok_last": records[-1]["ok"],
                "ok_strictly_increasing": str(source["ok_strictly_increasing"]).lower(),
                "timeout_delta": source["counter_deltas"]["timeout"],
                "crc_delta": source["counter_deltas"]["crc"],
                "seq_delta": source["counter_deltas"]["seq"],
                "recovery_delta": source["counter_deltas"]["recovery"],
                "prohibited_marker_count": len(source["prohibited_markers"]),
                "valid": str(source["valid"]).lower(),
                "source_path": SOURCES[key][0],
                "source_sha256": SOURCES[key][1],
            }
        )
    n0_path = write_csv("n0_controls.csv", list(n0_rows[0]), n0_rows)

    outcome_rows = []
    latency_rows = []
    for mode in ("SILENT", "BAD_CRC", "DELAYED"):
        fault = summary["faults"][mode]
        outcome_rows.append(
            {
                "fault_mode": mode,
                "planned_trials": fault["planned_trials"],
                "valid_trials": fault["valid_trials"],
                "invalid_trials": fault["invalid_trials"],
                "activation_confirmed_trials": fault["activation_confirmed_trials"],
                "restoration_confirmed_trials": fault["restoration_confirmed_trials"],
                "detection_successes": fault["detection"]["successes"],
                "detection_trials": fault["detection"]["trials"],
                "detection_observed_proportion": fault["detection"]["proportion"],
                "detection_exact_95_ci_lower": fault["detection"]["exact_95_ci_lower"],
                "detection_exact_95_ci_upper": fault["detection"]["exact_95_ci_upper"],
                "offline_observed_trials": fault["offline_observed_trials"],
                "recovery_successes": fault["recovery"]["successes"],
                "recovery_trials": fault["recovery"]["trials"],
                "recovery_observed_proportion": fault["recovery"]["proportion"],
                "recovery_exact_95_ci_lower": fault["recovery"]["exact_95_ci_lower"],
                "recovery_exact_95_ci_upper": fault["recovery"]["exact_95_ci_upper"],
                "restart_marker_observed_trials": fault["restart_marker_observed_trials"],
                "source_path": SOURCES["campaign_summary"][0],
                "source_sha256": SOURCES["campaign_summary"][1],
            }
        )
        for metric, source_key, definition in (
            (
                "command_to_detector_marker",
                "detection_latency",
                "host timestamp at injection command send to host timestamp at first predefined detector marker",
            ),
            (
                "restore_command_to_recovery_marker",
                "recovery_latency",
                "host timestamp at NORMAL command send to host timestamp at PAYLOAD_RECOVERED marker",
            ),
        ):
            latency = fault[source_key]
            latency_rows.append(
                {
                    "fault_mode": mode,
                    "metric": metric,
                    "n": latency["n"],
                    "median_ms": latency["median_ms"],
                    "iqr_ms": latency["iqr_ms"],
                    "q1_ms": latency["q1_ms"],
                    "q3_ms": latency["q3_ms"],
                    "min_ms": latency["min_ms"],
                    "max_ms": latency["max_ms"],
                    "timing_basis": definition,
                    "source_path": SOURCES["campaign_summary"][0],
                    "source_sha256": SOURCES["campaign_summary"][1],
                }
            )
    outcome_path = write_csv("fault_outcomes.csv", list(outcome_rows[0]), outcome_rows)
    latency_path = write_csv("latency_summary.csv", list(latency_rows[0]), latency_rows)

    generated = [n0_path, outcome_path, latency_path]
    provenance = {
        "schema_version": 1,
        "derivation": "Deterministic field projection from hash-verified frozen JSON; no inferential tests or recomputation of summary statistics.",
        "generator": {
            "path": str(Path(__file__).resolve().relative_to(REPO)).replace("\\", "/"),
            "sha256": sha256(Path(__file__)),
        },
        "inputs": {
            key: {"path": relative, "sha256": expected}
            for key, (relative, expected) in SOURCES.items()
        },
        "outputs": {
            path.name: {
                "path": str(path.resolve().relative_to(REPO)).replace("\\", "/"),
                "sha256": sha256(path),
            }
            for path in generated
        },
    }
    provenance_path = TABLE_DIR / "TABLE_PROVENANCE.json"
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(generated)} tables and {provenance_path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
