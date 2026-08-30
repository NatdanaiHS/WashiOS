#!/usr/bin/env python3
"""Prepare, acquire, and validate the ICSEC primary lab-extension package.

PREPARE writes the immutable randomized plan before hardware acquisition.
RUN reads that plan and captures exact-byte dual-channel logs. It stops after the
first activation, serial-health, or stabilization failure and retains the attempt.
All timing is host-observed; no value is represented as MCU execution latency.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import datetime as dt
import hashlib
import json
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable

INJECTOR_DIR = Path(__file__).resolve().parents[1] / "injector"
sys.path.insert(0, str(INJECTOR_DIR))
from run_payload_campaign import (  # noqa: E402
    SerialCapture,
    SerialEvent,
    escaped_rendering,
    send_mode,
    utc_now,
    wait_mode_confirmation,
)

DELAYS_MS = (50, 90, 100, 110, 150, 250, 500)
STATUS_RE = re.compile(
    r"^\[OBC\] PAYLOAD_STATUS state=(?P<state>\S+) "
    r"polls=(?P<polls>\d+) ok=(?P<ok>\d+) timeout=(?P<timeout>\d+) "
    r"crc=(?P<crc>\d+) seq=(?P<seq>\d+) recovery=(?P<recovery>\d+) "
    r"heartbeat=OK watchdog=OK$"
)
COUNTERS = ("timeout", "crc", "seq", "recovery")
PROHIBITED = (
    "[OBC] PAYLOAD_REJECT",
    "[OBC] PAYLOAD_TIMEOUT",
    "[OBC] PAYLOAD_OFFLINE",
    "[OBC] PAYLOAD_RECOVERED",
    "[OBC] PAYLOAD_LINK_START",
    "[OBC] PAYLOAD_POLL_WRITE_FAILED",
)


@dataclasses.dataclass(frozen=True)
class PlanRow:
    run_id: str
    order_index: int
    block: int
    condition: str
    delay_ms: int | None
    observation_s: float


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest().upper()


def git_output(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
    temporary.replace(path)


def generate_plan(seed: int, blocks: int, observation_s: float = 4.0) -> list[PlanRow]:
    if blocks not in (3, 5):
        raise ValueError("blocks must be 3 or 5")
    rng = random.Random(seed)
    conditions: list[tuple[int, str, int | None]] = []
    for block in range(1, blocks + 1):
        block_conditions = [("DELAY", delay) for delay in DELAYS_MS]
        block_conditions.extend((("NC", None), ("NC", None)))
        rng.shuffle(block_conditions)
        conditions.extend((block, condition, delay) for condition, delay in block_conditions)

    # Retry the entire deterministic shuffle stream until NC constraints pass.
    while not plan_constraints_pass([condition for _, condition, _ in conditions]):
        conditions.clear()
        for block in range(1, blocks + 1):
            block_conditions = [("DELAY", delay) for delay in DELAYS_MS]
            block_conditions.extend((("NC", None), ("NC", None)))
            rng.shuffle(block_conditions)
            conditions.extend((block, condition, delay) for condition, delay in block_conditions)

    rows = []
    for index, (block, condition, delay) in enumerate(conditions, 1):
        suffix = "NC" if condition == "NC" else f"D{delay:03d}"
        rows.append(PlanRow(f"R{index:03d}_B{block}_{suffix}", index, block,
                            condition, delay, observation_s))
    return rows


def plan_constraints_pass(conditions: list[str]) -> bool:
    nc_positions = [index for index, value in enumerate(conditions) if value == "NC"]
    if any(b - a == 1 for a, b in zip(nc_positions, nc_positions[1:])):
        return False
    return all((b - a - 1) <= 4 for a, b in zip(nc_positions, nc_positions[1:]))


def prepare(package: Path, seed: int, blocks: int, repo: Path) -> None:
    package.mkdir(parents=True, exist_ok=False)
    (package / "raw" / "nominal").mkdir(parents=True)
    (package / "raw" / "campaign").mkdir()
    (package / "raw" / "bad_crc").mkdir()
    plan = generate_plan(seed, blocks)
    plan_path = package / "run_plan.csv"
    with plan_path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[field.name for field in dataclasses.fields(PlanRow)])
        writer.writeheader()
        for row in plan:
            writer.writerow(dataclasses.asdict(row))
    manifest = {
        "schema_version": 1,
        "status": "PREPARED",
        "prepared_host_time": utc_now(),
        "seed": seed,
        "blocks": blocks,
        "delay_values_ms": list(DELAYS_MS),
        "normal_controls_per_block": 2,
        "observation_s": 4.0,
        "nominal_requested_s": 605.0,
        "plan_sha256": sha256_file(plan_path),
        "source_commit_at_prepare": git_output(repo, "rev-parse", "HEAD"),
        "source_branch": git_output(repo, "branch", "--show-current"),
        "raw_log_format": "utc_iso8601<TAB>raw_hex<TAB>escaped_ascii",
        "measurement_definitions": {
            "all_intervals": "host-observed serial receipt or command-send intervals",
            "delay_activation": "G474 exact [PAYLOAD] MODE=DELAYED delay_ms=<requested> confirmation",
            "normal_control_activation": "fresh G474 [PAYLOAD] MODE=NORMAL confirmation",
            "stabilization": "fresh NORMAL confirmation, post-confirmation serial boundary, ONLINE status baseline and later ONLINE status with ok increase >=3, zero fault-counter delta, and no prohibited marker",
            "trial_window": "four seconds beginning at the host command-send boundary after exact activation confirmation is required",
        },
        "board_configuration": {
            "controller": "G431-A NUCLEO-G431RB",
            "controller_stlink_serial": "005100243032511537333436",
            "payload": "G474-A NUCLEO-G474RE",
            "payload_stlink_serial": "0041003D3234510F37333934",
            "interboard_uart": "G431 PC4 TX -> G474 PC5 RX; G431 PC5 RX <- G474 PC4 TX; common GND; 115200 8N1",
        },
        "literal_status_warning": "heartbeat=OK watchdog=OK are literal strings, not independent measurements",
        "deviations": [],
    }
    write_json(package / "manifest.json", manifest)
    write_json(package / "configuration.json", {
        "poll_period_ms": 500,
        "response_deadline_ms": 100,
        "offline_threshold_consecutive_timeouts": 3,
        "gate_timeout_s": 15.0,
        "activation_timeout_s": 3.0,
        "post_restore_gate_required": True,
        "routine_mcu_reset_per_trial": False,
    })


def read_plan(path: Path) -> list[PlanRow]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [PlanRow(
            row["run_id"], int(row["order_index"]), int(row["block"]),
            row["condition"], int(row["delay_ms"]) if row["delay_ms"] else None,
            float(row["observation_s"]),
        ) for row in csv.DictReader(handle)]


def create_scope_down_amendment(package: Path) -> tuple[Path, Path]:
    original_path = package / "run_plan.csv"
    original_hash = sha256_file(original_path)
    if original_hash != "24AD8C20778472BFFC644557D2284D15A481804A1820BDA05A1827D3C88EBBDE":
        raise RuntimeError("original plan hash does not match the reviewed plan")
    original = read_plan(original_path)
    amended_path = package / "amended_execution_plan.csv"
    amendment_path = package / "plan_amendment.json"
    rows = []
    for row in original:
        if row.block > 3:
            continue
        if row.run_id == "R001_B1_D110":
            disposition = "COMPLETED_VALID_CARRY_FORWARD"
        elif row.run_id == "R002_B1_D500":
            disposition = "RETAINED_INVALID_NO_RETRY"
        elif row.delay_ms == 500:
            disposition = "REMOVED_SCOPE_500_UNSTARTED"
        else:
            disposition = "PLANNED_CONTINUATION"
        rows.append({**dataclasses.asdict(row), "disposition": disposition})
    fields = [field.name for field in dataclasses.fields(PlanRow)] + ["disposition"]
    with amended_path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    amended_hash = sha256_file(amended_path)
    block_four_five = [row.run_id for row in original if row.block > 3]
    decision = {
        "decision": "SCOPE_DOWN",
        "decision_host_time": utc_now(),
        "source": "research/icsec2026/NEXT_TASK.md research-review decision",
        "original_plan_path": "run_plan.csv",
        "original_plan_sha256": original_hash,
        "amended_plan_path": "amended_execution_plan.csv",
        "amended_plan_sha256": amended_hash,
        "derivation": "Preserve original order and identifiers for blocks 1-3; carry R001 valid; retain R002 invalid without retry; remove only unstarted 500 ms rows R011 and R021; execute every other row through R027.",
        "reason_500_removed": "At 500 ms the unchanged payload blocks for a controller poll period and drains queued polls before host commands, so NORMAL restoration and stabilization are not achievable without changing firmware semantics.",
        "carried_valid_rows": ["R001_B1_D110"],
        "retained_invalid_rows": ["R002_B1_D500"],
        "removed_unstarted_500_rows": ["R011_B2_D500", "R021_B3_D500"],
        "removed_blocks_4_5_rows": block_four_five,
        "planned_continuation_rows": [row["run_id"] for row in rows if row["disposition"] == "PLANNED_CONTINUATION"],
        "final_valid_target": {"delays_ms": [50, 90, 100, 110, 150, 250], "valid_per_delay": 3, "normal_controls": 6},
        "r002_locked_log_sha256": {
            "g431": "08022AE828B5AF1715BF9991FBCF8DF2B9D399263B90B64F131F2720D732EDF3",
            "g474": "3062DA9486CE630E4821D075464766DFDFE863576288C3C4469F7F6A1F7E130D",
        },
    }
    write_json(amendment_path, decision)
    return amended_path, amendment_path


def read_amended_plan(path: Path) -> list[tuple[PlanRow, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [(PlanRow(
            row["run_id"], int(row["order_index"]), int(row["block"]),
            row["condition"], int(row["delay_ms"]) if row["delay_ms"] else None,
            float(row["observation_s"]),
        ), row["disposition"]) for row in csv.DictReader(handle)]


def status_record(event: SerialEvent) -> dict[str, object] | None:
    match = STATUS_RE.match(event.text)
    if match is None:
        return None
    result: dict[str, object] = {"host_time": event.host_time, "monotonic_s": event.monotonic_s,
                                 "state": match.group("state")}
    for field in ("polls", "ok", *COUNTERS):
        result[field] = int(match.group(field))
    return result


def prohibited_records(events: Iterable[SerialEvent]) -> list[dict[str, str]]:
    return [{"host_time": event.host_time, "marker": event.text}
            for event in events if any(marker in event.text for marker in PROHIBITED)]


def gate(g431: SerialCapture, g474: SerialCapture, g474_serial: object,
         timeout_s: float = 15.0) -> dict[str, object]:
    confirmation_start = g474.snapshot()
    command_host, _ = send_mode(g474_serial, "NORMAL")
    confirmation = wait_mode_confirmation(g474, "NORMAL", confirmation_start, 3.0)
    if confirmation is None:
        return {"valid": False, "failure": "NORMAL_CONFIRMATION_MISSING",
                "normal_command_host_time": command_host}
    boundary = g431.snapshot()
    deadline = time.monotonic() + timeout_s
    statuses: list[dict[str, object]] = []
    while time.monotonic() < deadline:
        g431.assert_healthy()
        g474.assert_healthy()
        events = g431.events_since(boundary)
        statuses = [record for event in events if (record := status_record(event)) is not None]
        if len(statuses) >= 2 and int(statuses[-1]["ok"]) - int(statuses[0]["ok"]) >= 3:
            break
        time.sleep(0.05)
    events = g431.events_since(boundary)
    statuses = [record for event in events if (record := status_record(event)) is not None]
    # Recovery or timeout text preceding the first stable ONLINE status is retained
    # as pre-baseline evidence. The evaluated gate begins at that status boundary.
    baseline_mono = float(statuses[0]["monotonic_s"]) if statuses else float("inf")
    pre_baseline = [event for event in events if event.monotonic_s < baseline_mono]
    evaluated_events = [event for event in events if event.monotonic_s >= baseline_mono]
    prohibited = prohibited_records(evaluated_events)
    failures = []
    if len(statuses) < 2:
        failures.append("FEWER_THAN_TWO_POST_BOUNDARY_STATUS_RECORDS")
    elif int(statuses[-1]["ok"]) - int(statuses[0]["ok"]) < 3:
        failures.append("FEWER_THAN_THREE_SUBSEQUENT_SUCCESSES")
    if any(record["state"] != "ONLINE" for record in statuses):
        failures.append("NON_ONLINE_STATUS")
    deltas = {field: int(statuses[-1][field]) - int(statuses[0][field])
              if statuses else None for field in COUNTERS}
    if any(delta != 0 for delta in deltas.values()):
        failures.append("FAULT_COUNTER_DELTA")
    if prohibited:
        failures.append("UNRESOLVED_OR_PROHIBITED_MARKER")
    return {
        "valid": not failures,
        "normal_command_host_time": command_host,
        "normal_confirmation_host_time": confirmation.host_time,
        "serial_boundary_host_time": confirmation.host_time,
        "evaluated_boundary_host_time": statuses[0]["host_time"] if statuses else None,
        "pre_baseline_markers": prohibited_records(pre_baseline),
        "status_records": statuses,
        "counter_deltas": deltas,
        "prohibited_markers": prohibited,
        "failures": failures,
    }


def attach_pair(base: Path, g431: SerialCapture, g474: SerialCapture):
    base.mkdir(parents=True, exist_ok=False)
    a = (base / "g431.log").open("x", encoding="ascii", newline="\n")
    b = (base / "g474.log").open("x", encoding="ascii", newline="\n")
    g431.attach_log(a)
    g474.attach_log(b)
    return a, b


def detach_pair(handles: tuple[object, object], g431: SerialCapture, g474: SerialCapture) -> None:
    g431.detach_log()
    g474.detach_log()
    for handle in handles:
        handle.close()


def marker_counts(events: list[SerialEvent]) -> dict[str, object]:
    needles = {
        "accepted_response_markers": "[OBC] PAYLOAD_ACCEPTED",
        "timeout_markers": "[OBC] PAYLOAD_TIMEOUT",
        "crc_rejection_markers": "[OBC] PAYLOAD_REJECT reason=CRC",
        "sequence_rejection_markers": "[OBC] PAYLOAD_REJECT reason=SEQUENCE",
        "offline_markers": "[OBC] PAYLOAD_OFFLINE",
        "recovery_markers": "[OBC] PAYLOAD_RECOVERED",
        "restart_markers": "[OBC] PAYLOAD_LINK_START",
        "poll_write_failure_markers": "[OBC] PAYLOAD_POLL_WRITE_FAILED",
    }
    result = {name: sum(needle in event.text for event in events) for name, needle in needles.items()}
    result["accepted_normal_response_markers"] = sum(
        "[OBC] PAYLOAD_ACCEPTED" in event.text and "mode=0" in event.text for event in events
    )
    result["accepted_delayed_response_markers"] = sum(
        "[OBC] PAYLOAD_ACCEPTED" in event.text and "mode=3" in event.text for event in events
    )
    return result


def run_nominal(package: Path, g431: SerialCapture, g474: SerialCapture,
                g474_serial: object, requested_s: float,
                run_id: str = "NOMINAL_001") -> dict[str, object]:
    handles = attach_pair(package / "raw" / "nominal" / run_id, g431, g474)
    try:
        stabilization = gate(g431, g474, g474_serial)
        if not stabilization["valid"]:
            return {"valid": False, "stabilization": stabilization,
                    "invalid_reason": "PRE_NOMINAL_STABILIZATION_FAILED"}
        start_index = g431.snapshot()
        start_mono = time.monotonic()
        start_host = utc_now()
        time.sleep(requested_s)
        end_mono = time.monotonic()
        end_host = utc_now()
        g431.assert_healthy(); g474.assert_healthy()
        events = [event for event in g431.events_since(start_index)
                  if start_mono <= event.monotonic_s <= end_mono]
        statuses = [record for event in events if (record := status_record(event)) is not None]
        deltas = {field: int(statuses[-1][field]) - int(statuses[0][field])
                  if statuses else None for field in COUNTERS}
        failures = []
        duration = end_mono - start_mono
        if duration < 600.0: failures.append("WINDOW_SHORTER_THAN_600_SECONDS")
        if len(statuses) < 115: failures.append("FEWER_THAN_115_STATUS_RECORDS")
        if any(record["state"] != "ONLINE" for record in statuses): failures.append("NON_ONLINE_STATUS")
        if not all(int(b["ok"]) > int(a["ok"]) for a, b in zip(statuses, statuses[1:])):
            failures.append("OK_NOT_STRICTLY_INCREASING")
        if any(delta != 0 for delta in deltas.values()): failures.append("FAULT_COUNTER_DELTA")
        prohibited = prohibited_records(events)
        if prohibited: failures.append("PROHIBITED_MARKER")
        return {"valid": not failures, "invalid_reason": ";".join(failures),
                "requested_s": requested_s, "duration_s": round(duration, 6),
                "window_start_host_time": start_host, "window_end_host_time": end_host,
                "stabilization": stabilization, "status_count": len(statuses),
                "status_records": statuses, "counter_deltas": deltas,
                "prohibited_markers": prohibited}
    finally:
        detach_pair(handles, g431, g474)


def resume_after_nominal_failure(package: Path, g431_port: str,
                                 g474_port: str, repo: Path) -> int:
    import serial  # type: ignore[import-not-found]
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "FAILED":
        raise RuntimeError("resume requires a retained FAILED acquisition")
    if (package / "campaign_results.json").exists():
        raise RuntimeError("resume is only valid before campaign acquisition begins")
    if sha256_file(package / "run_plan.csv") != manifest["plan_sha256"]:
        raise RuntimeError("precommitted run plan hash mismatch")
    packaged_firmware = {
        "payload_firmware_sha256": package / "firmware" / "g474_extension_firmware.bin",
        "controller_firmware_sha256": package / "firmware" / "g431_extension_application.bin",
        "controller_bootloader_sha256": package / "firmware" / "g431_extension_bootloader.bin",
    }
    for field, path in packaged_firmware.items():
        if not path.is_file() or sha256_file(path) != manifest[field]:
            raise RuntimeError(f"packaged firmware hash mismatch: {path.name}")
    plan = read_plan(package / "run_plan.csv")
    history = manifest.setdefault("acquisition_attempts", [])
    history.append({
        "attempt": "NOMINAL_001",
        "started_host_time": manifest.get("acquisition_started_host_time"),
        "finished_host_time": manifest.get("acquisition_finished_host_time"),
        "status": "INVALID_SERIAL_CAPTURE_FAILURE",
        "failure": manifest.get("failure"),
        "final_normal_command_error": manifest.get("final_normal_command_error"),
        "raw_path": "raw/nominal/NOMINAL_001",
    })
    manifest.update(
        status="RUNNING_RESUME_NOMINAL_002",
        resume_started_host_time=utc_now(),
        resume_source_commit=git_output(repo, "rev-parse", "HEAD"),
        resume_source_status=git_output(repo, "status", "--porcelain=v1"),
    )
    write_json(manifest_path, manifest)
    g431_serial = serial.Serial(g431_port, 115200, timeout=0.05, write_timeout=1.0)
    try:
        g474_serial = serial.Serial(g474_port, 115200, timeout=0.05, write_timeout=1.0)
    except Exception:
        g431_serial.close(); raise
    g431 = SerialCapture("g431", g431_serial); g474 = SerialCapture("g474", g474_serial)
    g431.start(); g474.start()
    status = "FAILED_RESUME"
    resume_failure = None
    try:
        nominal = run_nominal(package, g431, g474, g474_serial, 605.0, "NOMINAL_002")
        write_json(package / "nominal_validation_002.json", nominal)
        if not nominal["valid"]: raise RuntimeError("NOMINAL_002_VALIDATION_FAILED")
        results = []
        results_path = package / "campaign_results.json"
        for row in plan:
            result = run_trial(row, package, g431, g474, g474_serial)
            results.append(result); write_json(results_path, results)
            if not result["valid"]: raise RuntimeError(f"TRIAL_FAILED:{row.run_id}")
        mechanisms = []
        for exposure in ("SHORT", "SUSTAINED"):
            result = run_bad_crc(package, exposure, g431, g474, g474_serial)
            mechanisms.append(result); write_json(package / "bad_crc_results.json", mechanisms)
            if not result["valid"]: raise RuntimeError(f"BAD_CRC_FAILED:{exposure}")
        status = "ACQUISITION_COMPLETE"
        return 0
    except Exception as exc:
        resume_failure = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        try: send_mode(g474_serial, "NORMAL")
        except Exception as exc: manifest["resume_final_normal_error"] = f"{type(exc).__name__}: {exc}"
        g431.stop(); g474.stop(); g431_serial.close(); g474_serial.close()
        history.append({
            "attempt": "NOMINAL_002_AND_PRIMARY_SEQUENCE",
            "finished_host_time": utc_now(),
            "status": status,
            "failure": resume_failure,
            "raw_path": "raw/nominal/NOMINAL_002",
        })
        manifest.update(status=status, resume_finished_host_time=utc_now())
        if resume_failure is not None: manifest["resume_failure"] = resume_failure
        write_json(manifest_path, manifest)


def run_trial(row: PlanRow, package: Path, g431: SerialCapture, g474: SerialCapture,
              g474_serial: object) -> dict[str, object]:
    handles = attach_pair(package / "raw" / "campaign" / row.run_id, g431, g474)
    result: dict[str, object] = dataclasses.asdict(row)
    try:
        result["pre_stabilization"] = gate(g431, g474, g474_serial)
        if not result["pre_stabilization"]["valid"]:
            result.update(valid=False, invalid_reason="PRE_STABILIZATION_FAILED")
            return result
        activation_start = g474.snapshot()
        command = "NORMAL" if row.condition == "NC" else f"DELAYED {row.delay_ms}"
        command_host, command_mono = send_mode(g474_serial, command)
        expected = "NORMAL" if row.condition == "NC" else f"DELAYED delay_ms={row.delay_ms}"
        confirmation = wait_mode_confirmation(g474, expected, activation_start, 3.0)
        result["activation_command_host_time"] = command_host
        result["activation_confirmation_host_time"] = confirmation.host_time if confirmation else None
        result["activation_confirmed"] = confirmation is not None
        if confirmation is None:
            result.update(valid=False, invalid_reason="EXACT_ACTIVATION_NOT_CONFIRMED")
            return result
        controller_start = g431.snapshot()
        time.sleep(row.observation_s)
        end_mono = time.monotonic()
        g431.assert_healthy(); g474.assert_healthy()
        events = [event for event in g431.events_since(controller_start)
                  if command_mono <= event.monotonic_s <= end_mono]
        result["observations"] = marker_counts(events)
        result["observed_markers"] = [{"host_time": event.host_time, "marker": event.text}
                                      for event in events if "[OBC] PAYLOAD_" in event.text]
        restore_start = g474.snapshot()
        restore_host, _ = send_mode(g474_serial, "NORMAL")
        restored = wait_mode_confirmation(g474, "NORMAL", restore_start, 3.0)
        result["restore_command_host_time"] = restore_host
        result["restore_confirmation_host_time"] = restored.host_time if restored else None
        if restored is None:
            result.update(valid=False, invalid_reason="NORMAL_RESTORE_NOT_CONFIRMED")
            return result
        result["post_stabilization"] = gate(g431, g474, g474_serial)
        if not result["post_stabilization"]["valid"]:
            result.update(valid=False, invalid_reason="POST_STABILIZATION_FAILED")
            return result
        result.update(valid=True, invalid_reason="", unexpected_outcome="")
        return result
    finally:
        detach_pair(handles, g431, g474)


def run_bad_crc(package: Path, exposure: str, g431: SerialCapture,
                g474: SerialCapture, g474_serial: object) -> dict[str, object]:
    handles = attach_pair(package / "raw" / "bad_crc" / exposure, g431, g474)
    result: dict[str, object] = {"exposure": exposure}
    try:
        result["pre_stabilization"] = gate(g431, g474, g474_serial)
        if not result["pre_stabilization"]["valid"]:
            result.update(valid=False, invalid_reason="PRE_STABILIZATION_FAILED")
            return result
        g431_start = g431.snapshot(); g474_start = g474.snapshot()
        command_host, command_mono = send_mode(g474_serial, "BAD_CRC")
        activation = wait_mode_confirmation(g474, "BAD_CRC", g474_start, 3.0)
        result["activation_command_host_time"] = command_host
        result["activation_confirmation_host_time"] = activation.host_time if activation else None
        if activation is None:
            result.update(valid=False, invalid_reason="BAD_CRC_ACTIVATION_NOT_CONFIRMED")
            return result
        target = "[OBC] PAYLOAD_REJECT reason=CRC" if exposure == "SHORT" else "[OBC] PAYLOAD_OFFLINE consecutive=3"
        target_event = g431.wait_for(lambda event: target in event.text, g431_start, 4.0)
        result["target_marker"] = target
        result["target_host_time"] = target_event.host_time if target_event else None
        restore_start = g474.snapshot()
        restore_host, restore_mono = send_mode(g474_serial, "NORMAL")
        restored = wait_mode_confirmation(g474, "NORMAL", restore_start, 3.0)
        result["restore_command_host_time"] = restore_host
        result["restore_confirmation_host_time"] = restored.host_time if restored else None
        time.sleep(0.25)
        events = [event for event in g431.events_since(g431_start)
                  if event.monotonic_s >= command_mono]
        result["observed_markers"] = [{"host_time": event.host_time, "marker": event.text}
                                      for event in events if "[OBC] PAYLOAD_" in event.text]
        result["observations"] = marker_counts(events)
        pre_restore_offline = any("[OBC] PAYLOAD_OFFLINE" in event.text and
                                  event.monotonic_s < restore_mono for event in events)
        result["offline_before_restore"] = pre_restore_offline
        if target_event is None:
            result.update(valid=False, invalid_reason="MECHANISM_TARGET_NOT_OBSERVED")
            return result
        if restored is None:
            result.update(valid=False, invalid_reason="NORMAL_RESTORE_NOT_CONFIRMED")
            return result
        if exposure == "SHORT" and pre_restore_offline:
            result.update(valid=False, invalid_reason="OFFLINE_BEFORE_IMMEDIATE_RESTORE")
            return result
        result["post_stabilization"] = gate(g431, g474, g474_serial)
        if not result["post_stabilization"]["valid"]:
            result.update(valid=False, invalid_reason="POST_STABILIZATION_FAILED")
            return result
        result.update(valid=True, invalid_reason="")
        return result
    finally:
        detach_pair(handles, g431, g474)


def preflight_hardware(package: Path, g431_port: str, g474_port: str,
                       run_id: str = "FLASH_CHECK") -> int:
    import serial  # type: ignore[import-not-found]
    g431_serial = serial.Serial(g431_port, 115200, timeout=0.05, write_timeout=1.0)
    try:
        g474_serial = serial.Serial(g474_port, 115200, timeout=0.05, write_timeout=1.0)
    except Exception:
        g431_serial.close(); raise
    g431 = SerialCapture("g431", g431_serial); g474 = SerialCapture("g474", g474_serial)
    g431.start(); g474.start()
    result: dict[str, object] = {
        "run_id": f"PREFLIGHT_{run_id}",
        "condition": "DELAY_90_READINESS_ONLY",
        "g431_port": g431_port,
        "g474_port": g474_port,
        "started_host_time": utc_now(),
    }
    handles = attach_pair(package / "raw" / "preflight" / run_id, g431, g474)
    try:
        start_g431 = g431.snapshot(); start_g474 = g474.snapshot()
        command_host, _ = send_mode(g474_serial, "DELAYED 90")
        activation = wait_mode_confirmation(g474, "DELAYED delay_ms=90", start_g474, 3.0)
        accepted = g431.wait_for(
            lambda event: "[OBC] PAYLOAD_ACCEPTED" in event.text and "mode=3" in event.text,
            start_g431, 3.0,
        )
        restore_start = g474.snapshot()
        restore_host, _ = send_mode(g474_serial, "NORMAL")
        restored = wait_mode_confirmation(g474, "NORMAL", restore_start, 3.0)
        stabilization = gate(g431, g474, g474_serial)
        result.update(
            activation_command_host_time=command_host,
            exact_activation_confirmation_host_time=activation.host_time if activation else None,
            accepted_response_host_time=accepted.host_time if accepted else None,
            restore_command_host_time=restore_host,
            restore_confirmation_host_time=restored.host_time if restored else None,
            stabilization=stabilization,
        )
        failures = []
        if activation is None: failures.append("EXACT_DELAY_ACTIVATION_MISSING")
        if accepted is None: failures.append("ACCEPTED_RESPONSE_MARKER_MISSING")
        if restored is None: failures.append("NORMAL_RESTORE_MISSING")
        if not stabilization["valid"]: failures.append("STABILIZATION_FAILED")
        result.update(valid=not failures, invalid_reason=";".join(failures),
                      finished_host_time=utc_now())
        write_json(package / f"preflight_validation_{run_id.lower()}.json", result)
        return 0 if not failures else 2
    finally:
        detach_pair(handles, g431, g474)
        try: send_mode(g474_serial, "NORMAL")
        except Exception: pass
        g431.stop(); g474.stop(); g431_serial.close(); g474_serial.close()


def recover_payload_only(package: Path, g431_port: str, g474_port: str,
                         stlink_serial: str) -> int:
    import serial  # type: ignore[import-not-found]
    run_dir = package / "raw" / "recovery" / "PAYLOAD_ONLY_RESET_001"
    g431_serial = serial.Serial(g431_port, 115200, timeout=0.05, write_timeout=1.0)
    try:
        g474_serial = serial.Serial(g474_port, 115200, timeout=0.05, write_timeout=1.0)
    except Exception:
        g431_serial.close(); raise
    g431 = SerialCapture("g431", g431_serial); g474 = SerialCapture("g474", g474_serial)
    g431.start(); g474.start(); handles = attach_pair(run_dir, g431, g474)
    result: dict[str, object] = {
        "run_id": "PAYLOAD_ONLY_RESET_001",
        "purpose": "Exceptional recovery from retained R002 500 ms host-command starvation",
        "controller_reset_authorized": False,
        "payload_reset_authorized": True,
        "payload_stlink_serial": stlink_serial,
        "started_host_time": utc_now(),
    }
    try:
        openocd_root = Path.home() / ".platformio" / "packages" / "tool-openocd"
        executable = openocd_root / "bin" / "openocd.exe"
        scripts = openocd_root / "openocd" / "scripts"
        if not executable.is_file(): raise RuntimeError("OpenOCD executable not found")
        ready_start = g474.snapshot(); controller_start = g431.snapshot()
        command = [str(executable), "-d2", "-s", str(scripts),
                   "-c", f"adapter serial {stlink_serial}",
                   "-f", "interface/stlink.cfg", "-c", "transport select hla_swd",
                   "-f", "target/stm32g4x.cfg", "-c", "init; reset run; shutdown;"]
        completed = subprocess.run(command, text=True, capture_output=True, timeout=30.0)
        (run_dir / "openocd_reset.log").write_text(
            completed.stdout + completed.stderr, encoding="utf-8", newline="\n"
        )
        result["openocd_exit_code"] = completed.returncode
        result["reset_command"] = command
        ready = g474.wait_for(
            lambda event: "[PAYLOAD] READY board=NUCLEO-G474RE mode=NORMAL" in event.text,
            ready_start, 5.0,
        )
        result["payload_ready_host_time"] = ready.host_time if ready else None
        normal_start = g474.snapshot(); normal_host, _ = send_mode(g474_serial, "NORMAL")
        normal = wait_mode_confirmation(g474, "NORMAL", normal_start, 3.0)
        result["normal_command_host_time"] = normal_host
        result["normal_confirmation_host_time"] = normal.host_time if normal else None
        stabilization = gate(g431, g474, g474_serial)
        result["stabilization"] = stabilization
        controller_events = g431.events_since(controller_start)
        result["controller_recovery_markers"] = [
            {"host_time": event.host_time, "marker": event.text}
            for event in controller_events if "[OBC] PAYLOAD_RECOVERED" in event.text
        ]
        result["controller_link_start_markers"] = [
            {"host_time": event.host_time, "marker": event.text}
            for event in controller_events if "[OBC] PAYLOAD_LINK_START" in event.text
        ]
        failures = []
        if completed.returncode != 0: failures.append("OPENOCD_RESET_FAILED")
        if ready is None: failures.append("PAYLOAD_READY_NOT_OBSERVED")
        if normal is None: failures.append("NORMAL_NOT_CONFIRMED")
        if not stabilization["valid"]: failures.append("STABILIZATION_FAILED")
        result.update(valid=not failures, invalid_reason=";".join(failures),
                      finished_host_time=utc_now())
        write_json(package / "payload_recovery_validation.json", result)
        return 0 if not failures else 2
    finally:
        detach_pair(handles, g431, g474)
        g431.stop(); g474.stop(); g431_serial.close(); g474_serial.close()


def continue_amended_campaign(package: Path, g431_port: str, g474_port: str,
                              repo: Path) -> int:
    import serial  # type: ignore[import-not-found]
    amendment = json.loads((package / "plan_amendment.json").read_text(encoding="utf-8"))
    amended_path = package / "amended_execution_plan.csv"
    if sha256_file(amended_path) != amendment["amended_plan_sha256"]:
        raise RuntimeError("amended execution plan hash mismatch")
    recovery = json.loads((package / "payload_recovery_validation.json").read_text(encoding="utf-8"))
    if not recovery.get("valid"):
        raise RuntimeError("payload-only recovery gate did not pass")
    firmware_checks = {
        package / "firmware" / "g474_extension_firmware.bin": "5581492429080BD58177A37733981ABA12DA6074BA40EAC0157B86E027B479E7",
        package / "firmware" / "g431_extension_application.bin": "6515796C07D37C19E21B0104B477EA4C6451B66A995EBEF6510725764441E727",
        package / "firmware" / "g431_extension_bootloader.bin": "FE591BF7292AD0D40F8FEE4AF5779118AE0D0083FF362F5BE9CCB156ADFE619E",
    }
    for path, expected in firmware_checks.items():
        if sha256_file(path) != expected: raise RuntimeError(f"firmware changed: {path.name}")
    planned = [row for row, disposition in read_amended_plan(amended_path)
               if disposition == "PLANNED_CONTINUATION"]
    results_path = package / "continuation_results.json"
    if results_path.exists(): raise RuntimeError("continuation results already exist")
    write_json(results_path, [])
    continuation_manifest = {
        "status": "RUNNING",
        "started_host_time": utc_now(),
        "source_commit": git_output(repo, "rev-parse", "HEAD"),
        "source_status": git_output(repo, "status", "--porcelain=v1"),
        "amended_plan_sha256": amendment["amended_plan_sha256"],
        "g431_port": g431_port, "g474_port": g474_port,
        "planned_continuation_rows": [row.run_id for row in planned],
        "firmware_sha256": {path.name: expected for path, expected in firmware_checks.items()},
    }
    continuation_manifest_path = package / "continuation_manifest.json"
    write_json(continuation_manifest_path, continuation_manifest)
    g431_serial = serial.Serial(g431_port, 115200, timeout=0.05, write_timeout=1.0)
    try:
        g474_serial = serial.Serial(g474_port, 115200, timeout=0.05, write_timeout=1.0)
    except Exception:
        g431_serial.close(); raise
    g431 = SerialCapture("g431", g431_serial); g474 = SerialCapture("g474", g474_serial)
    g431.start(); g474.start(); results = []; status = "FAILED"; failure = None
    try:
        for row in planned:
            result = run_trial(row, package, g431, g474, g474_serial)
            results.append(result); write_json(results_path, results)
            if not result["valid"]: raise RuntimeError(f"TRIAL_FAILED:{row.run_id}")
        mechanisms = []
        for exposure in ("SHORT", "SUSTAINED"):
            result = run_bad_crc(package, exposure, g431, g474, g474_serial)
            mechanisms.append(result); write_json(package / "bad_crc_results.json", mechanisms)
            if not result["valid"]: raise RuntimeError(f"BAD_CRC_FAILED:{exposure}")
        status = "ACQUISITION_COMPLETE"
        return 0
    except Exception as exc:
        failure = f"{type(exc).__name__}: {exc}"; raise
    finally:
        try: send_mode(g474_serial, "NORMAL")
        except Exception as exc: continuation_manifest["final_normal_error"] = f"{type(exc).__name__}: {exc}"
        g431.stop(); g474.stop(); g431_serial.close(); g474_serial.close()
        continuation_manifest.update(status=status, failure=failure,
                                     finished_host_time=utc_now(), completed_rows=len(results))
        write_json(continuation_manifest_path, continuation_manifest)


def parse_raw_log(path: Path) -> tuple[list[str], list[str]]:
    texts = []; failures = []
    with path.open(encoding="ascii", newline="") as handle:
        for line_number, line in enumerate(handle, 1):
            fields = line.rstrip("\r\n").split("\t", 2)
            if len(fields) != 3:
                failures.append(f"{path.name}:{line_number}:FIELD_COUNT"); continue
            host_time, raw_hex, rendered = fields
            try: dt.datetime.fromisoformat(host_time)
            except ValueError: failures.append(f"{path.name}:{line_number}:BAD_TIMESTAMP")
            try: raw = bytes.fromhex(raw_hex)
            except ValueError:
                failures.append(f"{path.name}:{line_number}:BAD_HEX"); continue
            if escaped_rendering(raw) != rendered:
                failures.append(f"{path.name}:{line_number}:RENDERING_MISMATCH")
            texts.append(raw.decode("ascii", errors="backslashreplace").rstrip("\r\n"))
    if not texts: failures.append(f"{path.name}:NO_RECORDS")
    return texts, failures


def finalize_evidence(package: Path, repo: Path) -> int:
    failures: list[str] = []
    checks: dict[str, object] = {}
    original = read_plan(package / "run_plan.csv")
    amendment = json.loads((package / "plan_amendment.json").read_text(encoding="utf-8"))
    amended = read_amended_plan(package / "amended_execution_plan.csv")
    original_hash = sha256_file(package / "run_plan.csv")
    amended_hash = sha256_file(package / "amended_execution_plan.csv")
    checks["original_plan_sha256"] = original_hash
    checks["amended_plan_sha256"] = amended_hash
    if original_hash != amendment["original_plan_sha256"]: failures.append("ORIGINAL_PLAN_HASH_MISMATCH")
    if amended_hash != amendment["amended_plan_sha256"]: failures.append("AMENDED_PLAN_HASH_MISMATCH")

    initial = json.loads((package / "campaign_results.json").read_text(encoding="utf-8"))
    continuation = json.loads((package / "continuation_results.json").read_text(encoding="utf-8"))
    continuation_manifest = json.loads((package / "continuation_manifest.json").read_text(encoding="utf-8"))
    bad_crc = json.loads((package / "bad_crc_results.json").read_text(encoding="utf-8"))
    nominal = json.loads((package / "nominal_validation_002.json").read_text(encoding="utf-8"))
    recovery = json.loads((package / "payload_recovery_validation.json").read_text(encoding="utf-8"))
    if continuation_manifest.get("status") != "ACQUISITION_COMPLETE": failures.append("CONTINUATION_NOT_COMPLETE")
    if not nominal.get("valid"): failures.append("NOMINAL_002_INVALID")
    if not recovery.get("valid"): failures.append("PAYLOAD_RECOVERY_INVALID")
    if len(initial) != 2 or initial[0]["run_id"] != "R001_B1_D110" or not initial[0]["valid"]:
        failures.append("CARRIED_R001_INVALID")
    if len(initial) != 2 or initial[1]["run_id"] != "R002_B1_D500" or initial[1]["valid"] or initial[1]["invalid_reason"] != "NORMAL_RESTORE_NOT_CONFIRMED":
        failures.append("R002_INVALID_LEDGER_MISMATCH")
    planned_ids = [row.run_id for row, disposition in amended if disposition == "PLANNED_CONTINUATION"]
    if [row["run_id"] for row in continuation] != planned_ids: failures.append("CONTINUATION_ORDER_MISMATCH")
    if len(continuation) != 23 or any(not row["valid"] for row in continuation): failures.append("CONTINUATION_VALID_COUNT_MISMATCH")

    result_by_id = {row["run_id"]: row for row in [*initial, *continuation]}
    all_valid = [initial[0], *continuation]
    raw_validation_failures = []
    for result in [*initial, *continuation]:
        run_id = result["run_id"]
        run_dir = package / "raw" / "campaign" / run_id
        g431_text, g431_failures = parse_raw_log(run_dir / "g431.log")
        g474_text, g474_failures = parse_raw_log(run_dir / "g474.log")
        raw_validation_failures.extend(f"{run_id}:{item}" for item in [*g431_failures, *g474_failures])
        if result.get("activation_confirmed"):
            marker = "[PAYLOAD] MODE=NORMAL" if result["condition"] == "NC" else f"[PAYLOAD] MODE=DELAYED delay_ms={result['delay_ms']}"
            if not any(marker in text for text in g474_text): failures.append(f"{run_id}:ACTIVATION_RAW_MISSING")
        if result.get("valid") and not any("[PAYLOAD] MODE=NORMAL" in text for text in g474_text):
            failures.append(f"{run_id}:RESTORE_RAW_MISSING")
        if result.get("valid") and (not result["pre_stabilization"]["valid"] or not result["post_stabilization"]["valid"]):
            failures.append(f"{run_id}:STABILIZATION_INVALID")
        for marker in result.get("observed_markers", []):
            if marker["marker"] not in g431_text: failures.append(f"{run_id}:RESULT_MARKER_RAW_MISSING")
    failures.extend(raw_validation_failures)

    delay_summary = {}
    for delay in (50, 90, 100, 110, 150, 250):
        rows = [row for row in all_valid if row["condition"] == "DELAY" and row["delay_ms"] == delay]
        if len(rows) != 3: failures.append(f"DELAY_{delay}_VALID_COUNT")
        def observed_count(key: str, needle: str | None = None) -> int:
            total = 0
            for row in rows:
                if key in row["observations"]: total += int(row["observations"][key] > 0)
                elif needle is not None: total += int(any(needle in marker["marker"] for marker in row["observed_markers"]))
            return total
        delay_summary[str(delay)] = {
            "valid_observations": len(rows),
            "accepted_delayed_response_observed": observed_count("accepted_delayed_response_markers", "[OBC] PAYLOAD_ACCEPTED"),
            "timeout_observed": observed_count("timeout_markers"),
            "sequence_rejection_observed": observed_count("sequence_rejection_markers"),
            "offline_observed": observed_count("offline_markers"),
            "restoration_confirmed": sum(bool(row.get("restore_confirmation_host_time")) for row in rows),
            "recovery_observed": sum(any("PAYLOAD_RECOVERED" in marker["marker"] for marker in row["post_stabilization"].get("pre_baseline_markers", [])) for row in rows),
        }
        # Older carried R001 predates split accepted-mode counters; only mode=3 is condition acceptance.
        delay_summary[str(delay)]["accepted_delayed_response_observed"] = sum(
            any("[OBC] PAYLOAD_ACCEPTED" in marker["marker"] and "mode=3" in marker["marker"] for marker in row["observed_markers"])
            for row in rows
        )

    nc_rows = [row for row in all_valid if row["condition"] == "NC"]
    if len(nc_rows) != 6: failures.append("NC_VALID_COUNT")
    nc_fields = ("crc_rejection_markers", "sequence_rejection_markers", "timeout_markers",
                 "offline_markers", "recovery_markers", "restart_markers", "poll_write_failure_markers")
    nc_false = {field: sum(int(row["observations"].get(field, 0)) for row in nc_rows) for field in nc_fields}
    if any(nc_false.values()): failures.append("NC_FALSE_MARKER_OBSERVED")

    if len(bad_crc) != 2 or [row["exposure"] for row in bad_crc] != ["SHORT", "SUSTAINED"]:
        failures.append("BAD_CRC_EXPOSURE_SET")
    else:
        short, sustained = bad_crc
        if not short["valid"] or short["observations"]["crc_rejection_markers"] < 1 or short["observations"]["offline_markers"] != 0:
            failures.append("BAD_CRC_SHORT_MECHANISM")
        ordered = [marker["marker"] for marker in sustained["observed_markers"]]
        required = ["PAYLOAD_REJECT reason=CRC", "PAYLOAD_TIMEOUT consecutive=1",
                    "PAYLOAD_TIMEOUT consecutive=2", "PAYLOAD_OFFLINE consecutive=3"]
        positions = [next((i for i, value in enumerate(ordered) if needle in value), -1) for needle in required]
        if not sustained["valid"] or any(position < 0 for position in positions) or positions != sorted(positions):
            failures.append("BAD_CRC_SUSTAINED_MECHANISM")
        for row in bad_crc:
            run_dir = package / "raw" / "bad_crc" / row["exposure"]
            g431_text, raw_a = parse_raw_log(run_dir / "g431.log")
            g474_text, raw_b = parse_raw_log(run_dir / "g474.log")
            failures.extend(f"BAD_CRC_{row['exposure']}:{item}" for item in [*raw_a, *raw_b])
            if not any("[PAYLOAD] MODE=BAD_CRC" in text for text in g474_text): failures.append(f"BAD_CRC_{row['exposure']}:ACTIVATION_RAW_MISSING")
            if not any("[PAYLOAD] MODE=NORMAL" in text for text in g474_text): failures.append(f"BAD_CRC_{row['exposure']}:RESTORE_RAW_MISSING")
            if not any("PAYLOAD_REJECT reason=CRC" in text for text in g431_text): failures.append(f"BAD_CRC_{row['exposure']}:CRC_RAW_MISSING")

    firmware_expected = {
        "g474_extension_firmware.bin": "5581492429080BD58177A37733981ABA12DA6074BA40EAC0157B86E027B479E7",
        "g431_extension_application.bin": "6515796C07D37C19E21B0104B477EA4C6451B66A995EBEF6510725764441E727",
        "g431_extension_bootloader.bin": "FE591BF7292AD0D40F8FEE4AF5779118AE0D0083FF362F5BE9CCB156ADFE619E",
    }
    firmware_actual = {name: sha256_file(package / "firmware" / name) for name in firmware_expected}
    if firmware_actual != firmware_expected: failures.append("FIRMWARE_HASH_MISMATCH")
    r002_hashes = {"g431": sha256_file(package / "raw" / "campaign" / "R002_B1_D500" / "g431.log"),
                   "g474": sha256_file(package / "raw" / "campaign" / "R002_B1_D500" / "g474.log")}
    if r002_hashes != amendment["r002_locked_log_sha256"]: failures.append("R002_LOCKED_HASH_MISMATCH")
    partial_hash = sha256_file(package / "PARTIAL_SHA256SUMS.csv")
    if partial_hash != "F3DEC9EEED1D7C49942AA52A3722F7D571FBFAA0D98BEAC48F13B24C4BDF5C0C": failures.append("PARTIAL_INVENTORY_CHANGED")
    frozen = {
        "dataset_inventory": sha256_file(repo / "research" / "icsec2026" / "runs" / "full_20260830_seed20260830_n30" / "SHA256SUMS.csv"),
        "provenance_inventory": sha256_file(repo / "research" / "icsec2026" / "provenance" / "20260830_023830" / "PROVENANCE_SHA256SUMS.csv"),
    }
    if frozen["dataset_inventory"] != "DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD": failures.append("FROZEN_DATASET_HASH")
    if frozen["provenance_inventory"] != "84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC": failures.append("FROZEN_PROVENANCE_HASH")

    ledger_path = package / "final_results_ledger.csv"
    with ledger_path.open("x", newline="", encoding="utf-8") as handle:
        fields = [field.name for field in dataclasses.fields(PlanRow)] + ["final_disposition", "attempted", "valid", "invalid_reason", "g431_raw", "g474_raw"]
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for row in original:
            result = result_by_id.get(row.run_id)
            if result is not None:
                disposition = "ATTEMPTED_VALID" if result["valid"] else "ATTEMPTED_INVALID"
            elif row.block <= 3 and row.delay_ms == 500:
                disposition = "REMOVED_SCOPE_500_UNSTARTED"
            else:
                disposition = "REMOVED_SCOPE_BLOCKS_4_5"
            raw_base = f"raw/campaign/{row.run_id}" if result is not None else ""
            writer.writerow({**dataclasses.asdict(row), "final_disposition": disposition,
                             "attempted": result is not None, "valid": result["valid"] if result else "",
                             "invalid_reason": result.get("invalid_reason", "") if result else "",
                             "g431_raw": f"{raw_base}/g431.log" if raw_base else "",
                             "g474_raw": f"{raw_base}/g474.log" if raw_base else ""})
    ledger_counts = {"original_plan_rows": len(original), "attempted_rows": len(result_by_id),
                     "valid_rows": len(all_valid), "invalid_rows": sum(not row["valid"] for row in result_by_id.values()),
                     "scope_removed_rows": len(original) - len(result_by_id)}
    summary = {
        "scope": "Sequential observations on G431-A/G474-A with unchanged extension firmware; descriptive only",
        "nominal": {key: nominal[key] for key in ("valid", "requested_s", "duration_s", "status_count", "counter_deltas", "prohibited_markers")},
        "ledger_counts": ledger_counts,
        "delay_summary": delay_summary,
        "normal_control": {"valid_observations": len(nc_rows), "false_markers": nc_false},
        "bad_crc": {"short": bad_crc[0], "sustained": bad_crc[1],
                    "timestamp_note": "Harness control flow waited for the target marker before issuing restore; equal displayed host timestamps may occur at host clock resolution."},
        "invalid_attempts": [{"run_id": initial[1]["run_id"], "invalid_reason": initial[1]["invalid_reason"], "included_in_valid_denominator": False}],
        "scope_removed": amendment["removed_unstarted_500_rows"] + amendment["removed_blocks_4_5_rows"],
        "interpretation_boundary": "No device-population, independence, long-duration, qualification, or MCU-execution-latency inference.",
    }
    summary_path = package / "descriptive_summary.json"; write_json(summary_path, summary)
    source_state = {"finalizer_host_time": utc_now(), "branch": git_output(repo, "branch", "--show-current"),
                    "commit": git_output(repo, "rev-parse", "HEAD"), "status": git_output(repo, "status", "--porcelain=v1"),
                    "acquisition_commit": continuation_manifest["source_commit"],
                    "finalizer_sha256": sha256_file(Path(__file__).resolve())}
    write_json(package / "extension_source_state.json", source_state)
    write_json(package / "backup_record.json", {"status": "READY_TO_COPY_AFTER_COMMIT",
               "method": "Exact directory copy followed by verification of every EXTENSION_SHA256SUMS.csv row",
               "planned_target": "C:/WashiOS-extension-backup/primary_20260830_seed20260830_b5"})
    validation = {"valid": not failures, "validated_host_time": utc_now(), "failures": failures,
                  "checks": checks, "ledger_counts": ledger_counts, "firmware_sha256": firmware_actual,
                  "r002_locked_log_sha256": r002_hashes, "partial_inventory_sha256": partial_hash,
                  "frozen_inventory_sha256": frozen, "raw_log_format_failures": raw_validation_failures,
                  "nominal_valid": nominal["valid"], "payload_recovery_valid": recovery["valid"],
                  "bad_crc_valid": all(row["valid"] for row in bad_crc),
                  "output_sha256": {"final_results_ledger.csv": sha256_file(ledger_path),
                                    "descriptive_summary.json": sha256_file(summary_path)}}
    write_json(package / "final_validation.json", validation)
    return 0 if not failures else 2


def run_hardware(package: Path, g431_port: str, g474_port: str,
                 g474_firmware: Path, g431_firmware: Path,
                 g431_bootloader: Path, repo: Path) -> int:
    import serial  # type: ignore[import-not-found]
    if g431_port.upper() == g474_port.upper():
        raise ValueError("serial ports must differ")
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    plan_path = package / "run_plan.csv"
    if sha256_file(plan_path) != manifest["plan_sha256"]:
        raise RuntimeError("precommitted run plan hash mismatch")
    plan = read_plan(plan_path)
    manifest.update(status="RUNNING", acquisition_started_host_time=utc_now(),
                    source_commit_at_acquisition=git_output(repo, "rev-parse", "HEAD"),
                    source_status_at_acquisition=git_output(repo, "status", "--porcelain=v1"),
                    g431_port=g431_port, g474_port=g474_port,
                    payload_firmware_sha256=sha256_file(g474_firmware),
                    payload_firmware_size=g474_firmware.stat().st_size,
                    controller_firmware_sha256=sha256_file(g431_firmware),
                    controller_firmware_size=g431_firmware.stat().st_size,
                    controller_bootloader_sha256=sha256_file(g431_bootloader),
                    controller_bootloader_size=g431_bootloader.stat().st_size)
    firmware_dir = package / "firmware"
    firmware_dir.mkdir(exist_ok=False)
    shutil.copy2(g474_firmware, firmware_dir / "g474_extension_firmware.bin")
    shutil.copy2(g431_firmware, firmware_dir / "g431_extension_application.bin")
    shutil.copy2(g431_bootloader, firmware_dir / "g431_extension_bootloader.bin")
    write_json(manifest_path, manifest)
    g431_serial = serial.Serial(g431_port, 115200, timeout=0.05, write_timeout=1.0)
    try:
        g474_serial = serial.Serial(g474_port, 115200, timeout=0.05, write_timeout=1.0)
    except Exception:
        g431_serial.close(); raise
    g431 = SerialCapture("g431", g431_serial); g474 = SerialCapture("g474", g474_serial)
    g431.start(); g474.start()
    status = "FAILED"
    try:
        nominal = run_nominal(package, g431, g474, g474_serial, 605.0)
        write_json(package / "nominal_validation.json", nominal)
        if not nominal["valid"]: raise RuntimeError("NOMINAL_VALIDATION_FAILED")
        results = []
        results_path = package / "campaign_results.json"
        for row in plan:
            result = run_trial(row, package, g431, g474, g474_serial)
            results.append(result); write_json(results_path, results)
            if not result["valid"]: raise RuntimeError(f"TRIAL_FAILED:{row.run_id}")
        mechanisms = []
        for exposure in ("SHORT", "SUSTAINED"):
            result = run_bad_crc(package, exposure, g431, g474, g474_serial)
            mechanisms.append(result); write_json(package / "bad_crc_results.json", mechanisms)
            if not result["valid"]: raise RuntimeError(f"BAD_CRC_FAILED:{exposure}")
        status = "ACQUISITION_COMPLETE"
        return 0
    except Exception as exc:
        manifest["failure"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        try:
            send_mode(g474_serial, "NORMAL")
        except Exception as exc:
            manifest["final_normal_command_error"] = f"{type(exc).__name__}: {exc}"
        g431.stop(); g474.stop(); g431_serial.close(); g474_serial.close()
        manifest.update(status=status, acquisition_finished_host_time=utc_now())
        write_json(manifest_path, manifest)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--package", required=True, type=Path)
    prep.add_argument("--seed", type=int, default=20260830)
    prep.add_argument("--blocks", type=int, choices=(3, 5), default=5)
    run = sub.add_parser("run")
    run.add_argument("--package", required=True, type=Path)
    run.add_argument("--g431-port", required=True)
    run.add_argument("--g474-port", required=True)
    run.add_argument("--g474-firmware", required=True, type=Path)
    run.add_argument("--g431-firmware", required=True, type=Path)
    run.add_argument("--g431-bootloader", required=True, type=Path)
    check = sub.add_parser("preflight")
    check.add_argument("--package", required=True, type=Path)
    check.add_argument("--g431-port", required=True)
    check.add_argument("--g474-port", required=True)
    check.add_argument("--run-id", default="FLASH_CHECK")
    resume = sub.add_parser("resume")
    resume.add_argument("--package", required=True, type=Path)
    resume.add_argument("--g431-port", required=True)
    resume.add_argument("--g474-port", required=True)
    amend = sub.add_parser("amend")
    amend.add_argument("--package", required=True, type=Path)
    recover = sub.add_parser("recover-payload")
    recover.add_argument("--package", required=True, type=Path)
    recover.add_argument("--g431-port", required=True)
    recover.add_argument("--g474-port", required=True)
    recover.add_argument("--stlink-serial", required=True)
    continuation = sub.add_parser("continue-amended")
    continuation.add_argument("--package", required=True, type=Path)
    continuation.add_argument("--g431-port", required=True)
    continuation.add_argument("--g474-port", required=True)
    finalize = sub.add_parser("finalize")
    finalize.add_argument("--package", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo = Path(__file__).resolve().parents[3]
    if args.command == "prepare":
        prepare(args.package.resolve(), args.seed, args.blocks, repo)
        return 0
    if args.command == "preflight":
        return preflight_hardware(args.package.resolve(), args.g431_port, args.g474_port,
                                  args.run_id)
    if args.command == "resume":
        return resume_after_nominal_failure(args.package.resolve(), args.g431_port,
                                            args.g474_port, repo)
    if args.command == "amend":
        amended, amendment = create_scope_down_amendment(args.package.resolve())
        print(f"amended_plan={amended} sha256={sha256_file(amended)}")
        print(f"amendment={amendment} sha256={sha256_file(amendment)}")
        return 0
    if args.command == "recover-payload":
        return recover_payload_only(args.package.resolve(), args.g431_port,
                                    args.g474_port, args.stlink_serial)
    if args.command == "continue-amended":
        return continue_amended_campaign(args.package.resolve(), args.g431_port,
                                         args.g474_port, repo)
    if args.command == "finalize":
        return finalize_evidence(args.package.resolve(), repo)
    return run_hardware(args.package.resolve(), args.g431_port, args.g474_port,
                        args.g474_firmware.resolve(), args.g431_firmware.resolve(),
                        args.g431_bootloader.resolve(), repo)


if __name__ == "__main__":
    sys.exit(main())
