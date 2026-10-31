#!/usr/bin/env python3
"""Prepare and execute manually armed oscilloscope captures at DELAYED 110 ms."""

from __future__ import annotations

import argparse
import csv
import dataclasses
import json
import shutil
import sys
from pathlib import Path

import run_primary_extension as primary


TRACE_COUNT = 5
DELAY_MS = 110


def prepare(package: Path, repo: Path) -> None:
    package.mkdir(parents=True, exist_ok=False)
    (package / "raw" / "campaign").mkdir(parents=True)
    (package / "scope").mkdir()
    plan = [primary.PlanRow(f"S{i:03d}_D110", i, 1, "DELAY", DELAY_MS, 4.0)
            for i in range(1, TRACE_COUNT + 1)]
    plan_path = package / "capture_plan.csv"
    with plan_path.open("x", newline="", encoding="utf-8") as handle:
        fields = [field.name for field in dataclasses.fields(primary.PlanRow)]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(dataclasses.asdict(row) for row in plan)
    primary.write_json(package / "manifest.json", {
        "status": "PREPARED",
        "prepared_host_time": primary.utc_now(),
        "source_commit_at_prepare": primary.git_output(repo, "rev-parse", "HEAD"),
        "source_branch": primary.git_output(repo, "branch", "--show-current"),
        "source_status_at_prepare": primary.git_output(repo, "status", "--porcelain=v1"),
        "capture_plan_sha256": primary.sha256_file(plan_path),
        "planned_traces": TRACE_COUNT,
        "delay_ms": DELAY_MS,
        "board_pair": "G431-B with G474-A",
        "endpoint_interval_definition": "G474-A PA8/D7 rising edge immediately before HAL_Delay(110) after a valid decoded poll, to G431-B PA8/D7 rising edge immediately after controller.service increments the first timeout count and before timeout serial logging",
        "same_exchange_rule": "The G431 marker must rise during the corresponding G474 110 ms high pulse; poll period is 500 ms",
        "scope_channel_map": {"CH1": "G474-A PA8/D7 endpoint-delay marker", "CH2": "G431-B PA8/D7 first-timeout marker", "ground": "shared board/scope ground"},
        "raw_serial_format": "utc_iso8601<TAB>raw_hex<TAB>escaped_ascii",
        "timing_claim": "Hardware-observed endpoint-behavior-start to timeout-marker interval under this instrumented 110 ms setup only",
        "deviations": [],
    })
    primary.write_json(package / "measurement_protocol.json", {
        "required_edges": ["CH1 rising", "CH2 rising"],
        "trigger": "single acquisition on CH1 rising near 1.65 V",
        "recommended_timebase": "20 ms/div or equivalent window showing at least 20 ms pre-trigger and 130 ms post-trigger",
        "recommended_vertical": "1 V/div, DC coupling, actual probe attenuation recorded",
        "minimum_sample_rate": "1 MSa/s",
        "valid_trace": "Both clean edges present, CH2 rising occurs within the same CH1 high pulse, native waveform and screenshot retained, serial trial valid",
        "uncertainty": "derive from actual sample interval and scope cursor/export resolution; do not infer MCU execution latency",
        "scope_settings_status": "PENDING_HUMAN_RECORD",
    })


def read_plan(package: Path, manifest: dict[str, object]) -> list[primary.PlanRow]:
    path = package / "capture_plan.csv"
    if primary.sha256_file(path) != manifest["capture_plan_sha256"]:
        raise RuntimeError("capture plan hash mismatch")
    rows = primary.read_plan(path)
    if len(rows) != TRACE_COUNT or any(row.delay_ms != DELAY_MS for row in rows):
        raise RuntimeError("capture plan content mismatch")
    return rows


def capture(package: Path, trace_id: str, g431_port: str, g474_port: str,
            g431_app: Path, g431_boot: Path, g474_payload: Path, repo: Path) -> int:
    import serial  # type: ignore[import-not-found]
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    plan = read_plan(package, manifest)
    results_path = package / "capture_results.json"
    results = json.loads(results_path.read_text(encoding="utf-8")) if results_path.exists() else []
    if len(results) >= len(plan) or plan[len(results)].run_id != trace_id:
        raise RuntimeError("trace must be the next unattempted precommitted row")
    expected = {
        "g431_scope_application.bin": "9F5B0041A7939468ED20736E0FDA2659FF90A106CC9C08610C0272CBE0FABC0A",
        "g431_scope_bootloader.bin": "7C36C0CBDEFECB31ABBD857B15E2AA28D7CBBDF5FBF5B4629666B13F23F716F2",
        "g474_scope_payload.bin": "9718A3B7080162235E27D6A2A8333DFF6F631C667D50E0AB90DC53749CEE917D",
    }
    sources = {"g431_scope_application.bin": g431_app, "g431_scope_bootloader.bin": g431_boot,
               "g474_scope_payload.bin": g474_payload}
    actual = {name: primary.sha256_file(path) for name, path in sources.items()}
    if actual != expected:
        raise RuntimeError(f"instrumented firmware hash mismatch: {actual}")
    firmware_dir = package / "firmware"
    if not firmware_dir.exists():
        firmware_dir.mkdir()
        for name, path in sources.items(): shutil.copy2(path, firmware_dir / name)
    g431_serial = serial.Serial(g431_port, 115200, timeout=0.05, write_timeout=1.0)
    try:
        g474_serial = serial.Serial(g474_port, 115200, timeout=0.05, write_timeout=1.0)
    except Exception:
        g431_serial.close(); raise
    g431 = primary.SerialCapture("g431_b", g431_serial)
    g474 = primary.SerialCapture("g474_a", g474_serial)
    g431.start(); g474.start()
    result: dict[str, object]
    try:
        result = primary.run_trial(plan[len(results)], package, g431, g474, g474_serial)
    finally:
        try: primary.send_mode(g474_serial, "NORMAL")
        except Exception: pass
        g431.stop(); g474.stop(); g431_serial.close(); g474_serial.close()
    result["scope_files_status"] = "PENDING_HUMAN_SAVE"
    result["source_commit"] = primary.git_output(repo, "rev-parse", "HEAD")
    result["source_status"] = primary.git_output(repo, "status", "--porcelain=v1")
    results.append(result); primary.write_json(results_path, results)
    manifest.update(status="CAPTURE_IN_PROGRESS", attempted_traces=len(results),
                    valid_serial_trials=sum(bool(row["valid"]) for row in results),
                    source_commit_at_capture=primary.git_output(repo, "rev-parse", "HEAD"),
                    firmware_sha256=actual, g431_port=g431_port.upper(), g474_port=g474_port.upper())
    primary.write_json(manifest_path, manifest)
    return 0 if result["valid"] else 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare"); prep.add_argument("--package", required=True, type=Path)
    run = sub.add_parser("capture"); run.add_argument("--package", required=True, type=Path)
    run.add_argument("--trace-id", required=True); run.add_argument("--g431-port", required=True); run.add_argument("--g474-port", required=True)
    run.add_argument("--g431-application", required=True, type=Path); run.add_argument("--g431-bootloader", required=True, type=Path); run.add_argument("--g474-payload", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv); repo = Path(__file__).resolve().parents[3]
    if args.command == "prepare": prepare(args.package.resolve(), repo); return 0
    return capture(args.package.resolve(), args.trace_id, args.g431_port, args.g474_port,
                   args.g431_application.resolve(), args.g431_bootloader.resolve(),
                   args.g474_payload.resolve(), repo)


if __name__ == "__main__": sys.exit(main())
