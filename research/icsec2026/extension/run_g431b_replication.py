#!/usr/bin/env python3
"""Acquire and freeze the bounded G431-B/G474-A replication milestone.

The primary evidence package is read-only. This harness reuses its exact-byte
capture, activation confirmation, trial, and stabilization implementation while
creating an exclusive replication package with a separately seeded 12-row plan.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import json
import random
import shutil
import sys
from pathlib import Path

import run_primary_extension as primary


CONDITIONS: tuple[tuple[str, int | None], ...] = (
    ("NC", None), ("DELAY", 90), ("DELAY", 100), ("DELAY", 110),
)
EXPECTED_FIRMWARE = {
    "g431_b_application.bin": "6515796C07D37C19E21B0104B477EA4C6451B66A995EBEF6510725764441E727",
    "g431_b_bootloader.bin": "FE591BF7292AD0D40F8FEE4AF5779118AE0D0083FF362F5BE9CCB156ADFE619E",
    "g474_a_payload.bin": "5581492429080BD58177A37733981ABA12DA6074BA40EAC0157B86E027B479E7",
}
PRIMARY_INVENTORY = "8B4CB2AB87CD317905AA4A219B81E99E2E459DC3EEF386D14286297476177C0B"
FROZEN_DATASET = "DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD"
FROZEN_PROVENANCE = "84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC"


def generate_plan(seed: int) -> list[primary.PlanRow]:
    rng = random.Random(seed)
    rows: list[primary.PlanRow] = []
    order = 0
    for block in range(1, 4):
        block_conditions = list(CONDITIONS)
        rng.shuffle(block_conditions)
        for condition, delay_ms in block_conditions:
            order += 1
            suffix = "NC" if condition == "NC" else f"D{delay_ms:03d}"
            rows.append(primary.PlanRow(
                f"RB{order:03d}_B{block}_{suffix}", order, block,
                condition, delay_ms, 4.0,
            ))
    return rows


def prepare(package: Path, seed: int, repo: Path) -> None:
    package.mkdir(parents=True, exist_ok=False)
    (package / "raw" / "campaign").mkdir(parents=True)
    (package / "raw" / "readiness").mkdir()
    plan_path = package / "run_plan.csv"
    with plan_path.open("x", newline="", encoding="utf-8") as handle:
        fields = [field.name for field in dataclasses.fields(primary.PlanRow)]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(dataclasses.asdict(row) for row in generate_plan(seed))
    primary.write_json(package / "manifest.json", {
        "schema_version": 1,
        "status": "PREPARED_PLAN_LOCKED",
        "prepared_host_time": primary.utc_now(),
        "scope": "Second-controller reproduction: G431-B with the same G474-A; not an independent board pair",
        "seed": seed,
        "blocks": 3,
        "planned_observations": 12,
        "conditions_per_block": ["NC", "DELAY_90_MS", "DELAY_100_MS", "DELAY_110_MS"],
        "observation_s": 4.0,
        "plan_sha256": primary.sha256_file(plan_path),
        "source_branch_at_prepare": primary.git_output(repo, "branch", "--show-current"),
        "source_commit_at_prepare": primary.git_output(repo, "rev-parse", "HEAD"),
        "source_status_at_prepare": primary.git_output(repo, "status", "--porcelain=v1"),
        "raw_log_format": "utc_iso8601<TAB>raw_hex<TAB>escaped_ascii; raw_hex is authoritative",
        "timing_definition": "Host-observed serial receipt and command-send boundaries; no MCU execution-latency inference",
        "measurement_definitions": {
            "activation": "Exact G474 MODE=NORMAL or MODE=DELAYED delay_ms=<requested> confirmation; command-send alone is insufficient",
            "trial_window": "Four seconds from confirmed-condition command boundary using the primary harness implementation",
            "stabilization": "Fresh NORMAL confirmation, serial boundary, ONLINE baseline and later ONLINE with ok increase >=3, zero counter delta, no unresolved marker",
            "reproduction": "An outcome is reproduced only when actually observed in all three G431-B rows and in all three reviewed G431-A rows for that condition",
        },
        "board_identity": {"controller": "G431-B NUCLEO-G431RB", "payload": "G474-A NUCLEO-G474RE"},
        "wiring": "G431 PC4 TX -> G474 PC5 RX; G431 PC5 RX <- G474 PC4 TX; common GND; 115200 8N1",
        "routine_mcu_reset_per_trial": False,
        "deviations": [],
    })
    primary.write_json(package / "configuration.json", {
        "poll_period_ms": 500,
        "response_deadline_ms": 100,
        "offline_threshold_consecutive_timeouts": 3,
        "gate_timeout_s": 15.0,
        "activation_timeout_s": 3.0,
        "observation_s": 4.0,
        "post_restore_gate_required": True,
        "conditions_ms": [90, 100, 110],
        "normal_controls": 3,
    })


def validate_plan(package: Path, manifest: dict[str, object]) -> list[primary.PlanRow]:
    plan_path = package / "run_plan.csv"
    if primary.sha256_file(plan_path) != manifest["plan_sha256"]:
        raise RuntimeError("precommitted replication plan hash mismatch")
    rows = primary.read_plan(plan_path)
    if len(rows) != 12:
        raise RuntimeError("replication plan must contain exactly 12 rows")
    for block in range(1, 4):
        membership = {(row.condition, row.delay_ms) for row in rows if row.block == block}
        if membership != set(CONDITIONS):
            raise RuntimeError(f"block {block} condition membership mismatch")
    return rows


def acquire(package: Path, g431_port: str, g474_port: str,
            g431_stlink: str, g474_stlink: str,
            g431_app: Path, g431_boot: Path, g474_payload: Path,
            repo: Path) -> int:
    import serial  # type: ignore[import-not-found]
    if g431_port.upper() == g474_port.upper():
        raise ValueError("controller and payload ports must differ")
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "PREPARED_PLAN_LOCKED":
        raise RuntimeError("acquisition requires a fresh locked replication package")
    rows = validate_plan(package, manifest)
    supplied = {
        "g431_b_application.bin": g431_app,
        "g431_b_bootloader.bin": g431_boot,
        "g474_a_payload.bin": g474_payload,
    }
    actual = {name: primary.sha256_file(path) for name, path in supplied.items()}
    if actual != EXPECTED_FIRMWARE:
        raise RuntimeError(f"firmware hash mismatch: {actual}")
    firmware_dir = package / "firmware"
    firmware_dir.mkdir(exist_ok=False)
    for name, source in supplied.items():
        shutil.copy2(source, firmware_dir / name)
    manifest.update(
        status="ACQUISITION_RUNNING",
        acquisition_started_host_time=primary.utc_now(),
        source_commit_at_acquisition=primary.git_output(repo, "rev-parse", "HEAD"),
        source_status_at_acquisition=primary.git_output(repo, "status", "--porcelain=v1"),
        board_identity={
            "controller": "G431-B NUCLEO-G431RB",
            "controller_stlink_serial": g431_stlink.upper(),
            "controller_port": g431_port.upper(),
            "payload": "G474-A NUCLEO-G474RE",
            "payload_stlink_serial": g474_stlink.upper(),
            "payload_port": g474_port.upper(),
        },
        firmware_sha256=actual,
    )
    primary.write_json(manifest_path, manifest)
    g431_serial = serial.Serial(g431_port, 115200, timeout=0.05, write_timeout=1.0)
    try:
        g474_serial = serial.Serial(g474_port, 115200, timeout=0.05, write_timeout=1.0)
    except Exception:
        g431_serial.close()
        raise
    g431 = primary.SerialCapture("g431_b", g431_serial)
    g474 = primary.SerialCapture("g474_a", g474_serial)
    g431.start(); g474.start()
    results: list[dict[str, object]] = []
    failure: str | None = None
    status = "ACQUISITION_FAILED"
    try:
        readiness_handles = primary.attach_pair(package / "raw" / "readiness" / "LINK_GATE_001", g431, g474)
        try:
            readiness = primary.gate(g431, g474, g474_serial)
        finally:
            primary.detach_pair(readiness_handles, g431, g474)
        primary.write_json(package / "readiness_validation.json", readiness)
        if not readiness["valid"]:
            raise RuntimeError("READINESS_STABILIZATION_FAILED")
        results_path = package / "results.json"
        for row in rows:
            result = primary.run_trial(row, package, g431, g474, g474_serial)
            results.append(result)
            primary.write_json(results_path, results)
            if not result["valid"]:
                raise RuntimeError(f"TRIAL_FAILED:{row.run_id}:{result.get('invalid_reason')}")
        status = "ACQUISITION_COMPLETE"
        return 0
    except Exception as exc:
        failure = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        try:
            start = g474.snapshot()
            host_time, _ = primary.send_mode(g474_serial, "NORMAL")
            confirmation = primary.wait_mode_confirmation(g474, "NORMAL", start, 3.0)
            manifest["final_normal_command_host_time"] = host_time
            manifest["final_normal_confirmation_host_time"] = confirmation.host_time if confirmation else None
        except Exception as exc:
            manifest["final_normal_error"] = f"{type(exc).__name__}: {exc}"
        g431.stop(); g474.stop(); g431_serial.close(); g474_serial.close()
        manifest.update(status=status, acquisition_finished_host_time=primary.utc_now(),
                        attempted_rows=len(results), failure=failure)
        primary.write_json(manifest_path, manifest)


def parse_raw_log(path: Path) -> list[str]:
    texts: list[str] = []
    with path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, 1):
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 3:
                raise ValueError(f"{path}:{line_number}: expected three fields")
            raw = bytes.fromhex(fields[1])
            if primary.escaped_rendering(raw) != fields[2]:
                raise ValueError(f"{path}:{line_number}: readable rendering mismatch")
            texts.append(raw.decode("ascii", errors="backslashreplace").rstrip("\r\n"))
    return texts


def summarize_rows(rows: list[dict[str, object]]) -> tuple[dict[str, object], dict[str, int]]:
    fields = (
        "crc_rejection_markers", "sequence_rejection_markers", "timeout_markers",
        "offline_markers", "recovery_markers", "restart_markers",
        "poll_write_failure_markers",
    )
    nc_rows = [row for row in rows if row["condition"] == "NC"]
    nc_false = {field: sum(int(row["observations"][field]) for row in nc_rows) for field in fields}
    delay_summary: dict[str, object] = {}
    for delay in (90, 100, 110):
        selected = [row for row in rows if row["condition"] == "DELAY" and row["delay_ms"] == delay]
        delay_summary[str(delay)] = {
            "valid_observations": sum(bool(row["valid"]) for row in selected),
            "accepted_delayed_response_observed": sum(int(row["observations"]["accepted_delayed_response_markers"] > 0) for row in selected),
            "timeout_observed": sum(int(row["observations"]["timeout_markers"] > 0) for row in selected),
            "sequence_rejection_observed": sum(int(row["observations"]["sequence_rejection_markers"] > 0) for row in selected),
            "offline_observed": sum(int(row["observations"]["offline_markers"] > 0) for row in selected),
            "restoration_confirmed": sum(bool(row.get("restore_confirmation_host_time")) for row in selected),
            "recovery_observed": sum(any("PAYLOAD_RECOVERED" in item["marker"] for item in row["post_stabilization"].get("pre_baseline_markers", [])) for row in selected),
        }
    return delay_summary, nc_false


def finalize(package: Path, repo: Path) -> int:
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    if manifest.get("status") != "ACQUISITION_COMPLETE":
        failures.append("ACQUISITION_NOT_COMPLETE")
    rows = json.loads((package / "results.json").read_text(encoding="utf-8"))
    planned = validate_plan(package, manifest)
    if [row["run_id"] for row in rows] != [row.run_id for row in planned]:
        failures.append("RESULT_ORDER_MISMATCH")
    if len(rows) != 12 or any(not row.get("valid") for row in rows):
        failures.append("VALID_ROW_COUNT_MISMATCH")
    raw_failures: list[str] = []
    for row in rows:
        run_id = row["run_id"]
        try:
            g431 = parse_raw_log(package / "raw" / "campaign" / run_id / "g431.log")
            g474 = parse_raw_log(package / "raw" / "campaign" / run_id / "g474.log")
            activation = "[PAYLOAD] MODE=NORMAL" if row["condition"] == "NC" else f"[PAYLOAD] MODE=DELAYED delay_ms={row['delay_ms']}"
            if not any(activation in text for text in g474):
                raw_failures.append(f"{run_id}:ACTIVATION_MISSING")
            if not any("[PAYLOAD] MODE=NORMAL" in text for text in g474):
                raw_failures.append(f"{run_id}:RESTORATION_MISSING")
            for item in row.get("observed_markers", []):
                if item["marker"] not in g431:
                    raw_failures.append(f"{run_id}:MARKER_NOT_IN_RAW")
        except Exception as exc:
            raw_failures.append(f"{run_id}:{type(exc).__name__}:{exc}")
    failures.extend(raw_failures)
    delay_summary, nc_false = summarize_rows(rows)
    if any(nc_false.values()):
        failures.append("NC_FALSE_MARKER_OBSERVED")
    primary_root = repo / "research" / "icsec2026" / "extension" / "evidence" / "primary_20260830_seed20260830_b5"
    hashes = {
        "primary_inventory": primary.sha256_file(primary_root / "EXTENSION_SHA256SUMS.csv"),
        "dataset_inventory": primary.sha256_file(repo / "research" / "icsec2026" / "runs" / "full_20260830_seed20260830_n30" / "SHA256SUMS.csv"),
        "provenance_inventory": primary.sha256_file(repo / "research" / "icsec2026" / "provenance" / "20260830_023830" / "PROVENANCE_SHA256SUMS.csv"),
    }
    expected_hashes = {"primary_inventory": PRIMARY_INVENTORY, "dataset_inventory": FROZEN_DATASET, "provenance_inventory": FROZEN_PROVENANCE}
    if hashes != expected_hashes:
        failures.append("FROZEN_OR_PRIMARY_INVENTORY_CHANGED")
    firmware = {path.name: primary.sha256_file(path) for path in (package / "firmware").iterdir() if path.is_file()}
    if firmware != EXPECTED_FIRMWARE:
        failures.append("PACKAGED_FIRMWARE_HASH_MISMATCH")
    primary_summary = json.loads((primary_root / "descriptive_summary.json").read_text(encoding="utf-8"))
    outcomes = (
        "accepted_delayed_response_observed", "timeout_observed", "sequence_rejection_observed",
        "offline_observed", "restoration_confirmed", "recovery_observed",
    )
    reproduction: dict[str, object] = {}
    for delay in (90, 100, 110):
        original = primary_summary["delay_summary"][str(delay)]
        second = delay_summary[str(delay)]
        reproduced = {}
        for outcome in outcomes:
            original_all = original[outcome] == 3
            second_all = second[outcome] == 3
            original_none = original[outcome] == 0
            second_none = second[outcome] == 0
            reproduced[outcome] = {
                "g431_a_count": original[outcome], "g431_b_count": second[outcome],
                "same_all_or_none_pattern": (original_all and second_all) or (original_none and second_none),
            }
        reproduction[str(delay)] = reproduced
    summary = {
        "scope": "Selected observations on G431-B using the same G474-A; second-controller reproduction only, not an independent board pair",
        "accounting": {"planned": 12, "attempted": len(rows), "valid": sum(bool(row["valid"]) for row in rows), "invalid": sum(not bool(row["valid"]) for row in rows)},
        "g431_b_delay_summary": delay_summary,
        "normal_control": {"valid_observations": sum(row["condition"] == "NC" and row["valid"] for row in rows), "false_markers": nc_false},
        "cross_controller_reproduction": reproduction,
        "interpretation_boundary": "No independent-pair, device-population, qualification, long-duration, mission-reliability, or MCU execution-latency inference",
    }
    primary.write_json(package / "descriptive_cross_controller_summary.json", summary)
    with (package / "results_ledger.csv").open("x", newline="", encoding="utf-8") as handle:
        fields = [field.name for field in dataclasses.fields(primary.PlanRow)] + ["attempted", "valid", "invalid_reason", "unexpected_outcome", "g431_raw", "g474_raw"]
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for plan_row, result in zip(planned, rows):
            writer.writerow({**dataclasses.asdict(plan_row), "attempted": True, "valid": result["valid"],
                             "invalid_reason": result.get("invalid_reason", ""), "unexpected_outcome": result.get("unexpected_outcome", ""),
                             "g431_raw": f"raw/campaign/{plan_row.run_id}/g431.log", "g474_raw": f"raw/campaign/{plan_row.run_id}/g474.log"})
    primary.write_json(package / "source_state.json", {
        "finalized_host_time": primary.utc_now(), "branch": primary.git_output(repo, "branch", "--show-current"),
        "commit": primary.git_output(repo, "rev-parse", "HEAD"), "status": primary.git_output(repo, "status", "--porcelain=v1"),
        "harness_sha256": primary.sha256_file(Path(__file__).resolve()),
    })
    validation = {"valid": not failures, "validated_host_time": primary.utc_now(), "failures": failures,
                  "raw_log_failures": raw_failures, "inventory_recheck_sha256": hashes,
                  "firmware_sha256": firmware, "plan_sha256": primary.sha256_file(package / "run_plan.csv")}
    primary.write_json(package / "final_validation.json", validation)
    primary.write_json(package / "FINAL_MANIFEST.json", {
        "status": "COMPLETE" if not failures else "VALIDATION_FAILED",
        "scope": summary["scope"], "source_branch": manifest["source_branch_at_prepare"],
        "acquisition_source_commit": manifest["source_commit_at_acquisition"], "frozen_base_commit": "8a47d070c549274c59cdbde2495afa8d353a93b3",
        "board_identity": manifest["board_identity"], "wiring": manifest["wiring"], "firmware_sha256": firmware,
        "plan": {"seed": manifest["seed"], "sha256": manifest["plan_sha256"], "rows": 12},
        "accounting": summary["accounting"], "last_confirmed_payload_state": "NORMAL after final valid post-stabilization gate",
        "validation": "final_validation.json valid=true" if not failures else "final_validation.json contains failures",
        "interpretation_boundary": summary["interpretation_boundary"],
    })
    primary.write_json(package / "backup_record.json", {"status": "READY_TO_COPY_AFTER_COMMIT", "planned_target": f"C:/WashiOS-extension-backup/{package.name}", "method": "Exact directory copy and independent verification of every inventory row"})
    return 0 if not failures else 2


def inventory(package: Path, repo: Path) -> int:
    output = package / "REPLICATION_SHA256SUMS.csv"
    if output.exists():
        raise FileExistsError(output)
    files = sorted(path for path in package.rglob("*") if path.is_file() and path != output)
    with output.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle); writer.writerow(["sha256", "size", "path"])
        for path in files:
            writer.writerow([primary.sha256_file(path), path.stat().st_size, path.relative_to(repo).as_posix()])
    print(f"inventory_rows={len(files)} sha256={primary.sha256_file(output)}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--package", required=True, type=Path)
    prep.add_argument("--seed", type=int, default=20260830)
    run = sub.add_parser("acquire")
    run.add_argument("--package", required=True, type=Path)
    run.add_argument("--g431-port", required=True); run.add_argument("--g474-port", required=True)
    run.add_argument("--g431-stlink", required=True); run.add_argument("--g474-stlink", required=True)
    run.add_argument("--g431-application", required=True, type=Path)
    run.add_argument("--g431-bootloader", required=True, type=Path)
    run.add_argument("--g474-payload", required=True, type=Path)
    final = sub.add_parser("finalize"); final.add_argument("--package", required=True, type=Path)
    inv = sub.add_parser("inventory"); inv.add_argument("--package", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo = Path(__file__).resolve().parents[3]
    if args.command == "prepare":
        prepare(args.package.resolve(), args.seed, repo); return 0
    if args.command == "acquire":
        return acquire(args.package.resolve(), args.g431_port, args.g474_port,
                       args.g431_stlink, args.g474_stlink,
                       args.g431_application.resolve(), args.g431_bootloader.resolve(),
                       args.g474_payload.resolve(), repo)
    if args.command == "finalize":
        return finalize(args.package.resolve(), repo)
    return inventory(args.package.resolve(), repo)


if __name__ == "__main__":
    sys.exit(main())
