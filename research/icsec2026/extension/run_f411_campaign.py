#!/usr/bin/env python3
"""Prepare and execute the predefined 12-row F411 Pair-1 campaign."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import time
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from run_f411_pair1 import (
    CONTROLLER_PROHIBITED,
    CONTROLLER_STLINK,
    COUNTERS,
    PAYLOAD_STLINK,
    SERIAL_PROHIBITED,
    SerialCapture,
    SerialEvent,
    close_pair,
    marker_records,
    open_pair,
    openocd_program,
    send_mode,
    sha256_file,
    status_record,
    utc_now,
    validate_normal_statuses,
    wait_mode_confirmation,
    write_json,
)

CAMPAIGN_ID = "F411_P1_CAMPAIGN_20260901_B3"
PRECHECK_ID = "F411_P1_CAMPAIGN_20260901_B3_PRECHECK"
MANIFEST_SCHEMA = "washios.icsec2026.f411_pair1_campaign.v1"
CONTROLLER_BOARD_ID = "F411-A"
PAYLOAD_BOARD_ID = "F411-B"
CONTROLLER_FIRMWARE_ELF = "f411_p1_fixed_controller.elf"
CONTROLLER_FIRMWARE_BIN = "f411_p1_fixed_controller.bin"
PAYLOAD_FIRMWARE_ELF = "f411_p1_payload.elf"
PAYLOAD_FIRMWARE_BIN = "f411_p1_payload.bin"
COMPLETE_DISPOSITION = "F411_P1_CAMPAIGN_COMPLETE_AWAITING_REVIEW"
STOPPED_DISPOSITION = "F411_P1_CAMPAIGN_STOPPED_INVALID_AWAITING_REVIEW"
CLAIM_BOUNDARY = "sequential descriptive evidence from one fixed F411 pair; separate from every prior package"
CODE_PATHS: tuple[Path, ...] | None = None
SEED = 20260901
EXPOSURE_S = 4.0
EXPECTED_CONTROLLER_ELF = "9AA52D103E977A8B18968A0B7F3D69E74361AC5E5FFDFA6B3CBC49A3AD722D78"
EXPECTED_CONTROLLER_BIN = "8686113C4A83E1600EBE66FB3B3F8795853011B4B0E69D91F9E68EBB3FD8FE68"
EXPECTED_PAYLOAD_ELF = "0BC0EAAA7830B001CD31F1805C1002275E62FAF8DE6BC8C1AF44ABF5A2005493"
EXPECTED_PAYLOAD_BIN = "52F145488CAD9D3A9711F77DF1DFB9F76DFEAE6660FE9E1FBD5560AA738BFBBB"
RESET_OR_FAULT = ("RESET", "HARDFAULT", "FAULT", "STACK_OVERFLOW")
PLAN = (
    (1, "F411P1_C01_B1_NC", 1, "NC", None),
    (2, "F411P1_C02_B1_D110", 1, "D110", 110),
    (3, "F411P1_C03_B1_D090", 1, "D090", 90),
    (4, "F411P1_C04_B1_D100", 1, "D100", 100),
    (5, "F411P1_C05_B2_D090", 2, "D090", 90),
    (6, "F411P1_C06_B2_NC", 2, "NC", None),
    (7, "F411P1_C07_B2_D100", 2, "D100", 100),
    (8, "F411P1_C08_B2_D110", 2, "D110", 110),
    (9, "F411P1_C09_B3_D100", 3, "D100", 100),
    (10, "F411P1_C10_B3_D110", 3, "D110", 110),
    (11, "F411P1_C11_B3_NC", 3, "NC", None),
    (12, "F411P1_C12_B3_D090", 3, "D090", 90),
)


def plan_rows() -> list[dict[str, object]]:
    return [
        {"row": row, "run_id": run_id, "block": block,
         "condition": condition, "delay_ms": delay_ms}
        for row, run_id, block, condition, delay_ms in PLAN
    ]


def write_plan(path: Path) -> None:
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=("row", "run_id", "block", "condition", "delay_ms"),
            lineterminator="\n")
        writer.writeheader()
        writer.writerows(plan_rows())


def initial_ledger() -> dict[str, object]:
    return {
        "campaign_id": CAMPAIGN_ID,
        "fixed_planned_denominator": 12,
        "replacement_or_retry_allowed": False,
        "rows": [dict(row, status="PLANNED", attempted=False, valid=None,
                      invalid_reason=None) for row in plan_rows()],
    }


def prepare_package(package: Path, controller_elf: Path, controller_bin: Path,
                    payload_elf: Path, payload_bin: Path) -> int:
    if package.exists():
        raise FileExistsError(f"exclusive campaign package already exists: {package}")
    expected = (
        (controller_elf, EXPECTED_CONTROLLER_ELF),
        (controller_bin, EXPECTED_CONTROLLER_BIN),
        (payload_elf, EXPECTED_PAYLOAD_ELF),
        (payload_bin, EXPECTED_PAYLOAD_BIN),
    )
    for path, digest in expected:
        if sha256_file(path) != digest:
            raise ValueError(f"firmware hash mismatch: {path}")
    package.mkdir(parents=True, exist_ok=False)
    (package / "firmware").mkdir()
    (package / "raw" / "rows").mkdir(parents=True)
    (package / ".gitattributes").write_text("* -text\n", encoding="ascii", newline="\n")
    copies = {
        CONTROLLER_FIRMWARE_ELF: controller_elf,
        CONTROLLER_FIRMWARE_BIN: controller_bin,
        PAYLOAD_FIRMWARE_ELF: payload_elf,
        PAYLOAD_FIRMWARE_BIN: payload_bin,
    }
    for name, source in copies.items():
        shutil.copyfile(source, package / "firmware" / name)
    write_plan(package / "run_plan.csv")
    write_json(package / "attempt_ledger.json", initial_ledger())
    write_json(package / "condition_definitions.json", {
        "NC": {"payload_mode": "NORMAL", "delay_ms": None,
               "interpretation": "healthy Normal Control, not C0 or ablation"},
        "D090": {"payload_mode": "DELAYED", "delay_ms": 90},
        "D100": {"payload_mode": "DELAYED", "delay_ms": 100},
        "D110": {"payload_mode": "DELAYED", "delay_ms": 110},
        "exposure_s": EXPOSURE_S,
    })
    write_json(package / "validity_rules.json", {
        "first_invalid_stop": True,
        "retry_or_replacement": False,
        "required": [
            "exact row identity, condition, and order",
            "continuous exact-byte dual capture",
            "fresh NORMAL confirmation and pre-stabilization",
            "exact delayed activation confirmation or confirmed NC",
            "four-second exposure",
            "one confirmed NORMAL restoration-equivalent command",
            "recovery when OFFLINE occurred",
            "passed post-stabilization and raw integrity",
        ],
        "unexpected_scientific_outcome_is_invalid": False,
    })
    harness = Path(__file__).resolve()
    code_paths = CODE_PATHS or (
        harness,
        harness.with_name("test_f411_campaign.py"),
        harness.with_name("validate_f411_campaign.py"),
    )
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "campaign_id": CAMPAIGN_ID,
        "precheck_id": PRECHECK_ID,
        "seed": SEED,
        "locked": True,
        "locked_host_time": utc_now(),
        "fixed_denominator": 12,
        "order": plan_rows(),
        "controller": {"board_id": CONTROLLER_BOARD_ID, "stlink_serial": CONTROLLER_STLINK,
                       "elf_sha256": EXPECTED_CONTROLLER_ELF,
                       "bin_sha256": EXPECTED_CONTROLLER_BIN},
        "payload": {"board_id": PAYLOAD_BOARD_ID, "stlink_serial": PAYLOAD_STLINK,
                    "elf_sha256": EXPECTED_PAYLOAD_ELF,
                    "bin_sha256": EXPECTED_PAYLOAD_BIN},
        "semantics": {"uart": "115200 8N1", "poll_ms": 500,
                      "deadline_ms": 100, "offline_after_timeouts": 3,
                      "exposure_s": EXPOSURE_S, "reset_between_rows": False},
        "code_hashes": {path.as_posix(): sha256_file(path) for path in code_paths},
        "claim_boundary": CLAIM_BOUNDARY,
    }
    write_json(package / "locked_manifest.json", manifest)
    return 0


def accepted_records(events: Iterable[SerialEvent]) -> list[dict[str, object]]:
    return [
        {"host_time": event.host_time, "monotonic_s": event.monotonic_s,
         "marker": event.text}
        for event in events if "[OBC] PAYLOAD_ACCEPTED" in event.text
    ]


def stabilization(controller: SerialCapture, payload: SerialCapture,
                  controller_boundary: int, payload_boundary: int,
                  timeout_s: float = 20.0) -> dict[str, object]:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        controller.assert_healthy()
        payload.assert_healthy()
        events = controller.events_since(controller_boundary)
        statuses = [record for event in events
                    if (record := status_record(event)) is not None]
        if len(statuses) >= 2 and len(accepted_records(events)) >= 3:
            break
        time.sleep(0.05)
    controller_events = controller.events_since(controller_boundary)
    payload_events = payload.events_since(payload_boundary)
    statuses = [record for event in controller_events
                if (record := status_record(event)) is not None]
    accepts = accepted_records(controller_events)
    failures: list[str] = []
    if len(statuses) < 2:
        failures.append("FEWER_THAN_TWO_STATUS_RECORDS")
    if len(accepts) < 3:
        failures.append("FEWER_THAN_THREE_ACCEPTED_EXCHANGES")
    if any(record["state"] != "ONLINE" for record in statuses):
        failures.append("NON_ONLINE_STATUS")
    if not all(int(b["ok"]) > int(a["ok"])
               for a, b in zip(statuses, statuses[1:])):
        failures.append("OK_NOT_STRICTLY_INCREASING")
    deltas = {field: int(statuses[-1][field]) - int(statuses[0][field])
              if statuses else None for field in COUNTERS}
    if any(delta != 0 for delta in deltas.values()):
        failures.append("FAULT_COUNTER_DELTA")
    prohibited = marker_records(
        controller_events, CONTROLLER_PROHIBITED + RESET_OR_FAULT) + marker_records(
            payload_events, SERIAL_PROHIBITED + RESET_OR_FAULT)
    if prohibited:
        failures.append("PROHIBITED_MARKER")
    return {"valid": not failures, "status_records": statuses,
            "accepted_exchanges": accepts, "counter_deltas": deltas,
            "prohibited_markers": prohibited, "failures": failures}


def fresh_normal_gate(controller: SerialCapture, payload: SerialCapture,
                      payload_serial: object) -> dict[str, object]:
    confirmation_boundary = payload.snapshot()
    command_host, _ = send_mode(payload_serial, "NORMAL")
    confirmation = wait_mode_confirmation(payload, "NORMAL", confirmation_boundary, 3.0)
    if confirmation is None:
        return {"valid": False, "normal_command_host_time": command_host,
                "normal_confirmation_host_time": None,
                "failures": ["NORMAL_CONFIRMATION_MISSING"]}
    controller_boundary = controller.snapshot()
    payload_boundary = payload.snapshot()
    result = stabilization(controller, payload, controller_boundary, payload_boundary)
    result.update(normal_command_host_time=command_host,
                  normal_confirmation_host_time=confirmation.host_time,
                  controller_boundary=controller_boundary,
                  payload_boundary=payload_boundary)
    return result


def outcome_summary(events: Iterable[SerialEvent], condition: str) -> dict[str, object]:
    records = [{"host_time": event.host_time, "monotonic_s": event.monotonic_s,
                "marker": event.text}
               for event in events if "[OBC] PAYLOAD_" in event.text]
    texts = [str(record["marker"]) for record in records]
    summary = {
        "accepted_mode_0": sum("PAYLOAD_ACCEPTED" in text and "mode=0" in text for text in texts),
        "accepted_mode_3": sum("PAYLOAD_ACCEPTED" in text and "mode=3" in text for text in texts),
        "timeout": sum("PAYLOAD_TIMEOUT" in text for text in texts),
        "sequence_rejection": sum("PAYLOAD_REJECT reason=SEQUENCE" in text for text in texts),
        "crc_rejection": sum("PAYLOAD_REJECT reason=CRC" in text for text in texts),
        "offline": sum("PAYLOAD_OFFLINE" in text for text in texts),
        "recovery_during_exposure": sum("PAYLOAD_RECOVERED" in text for text in texts),
        "restart": sum("PAYLOAD_LINK_START" in text for text in texts),
        "poll_write_failure": sum("PAYLOAD_POLL_WRITE_FAILED" in text for text in texts),
        "records": records,
    }
    if condition == "NC":
        summary["classification"] = "NORMAL_CONTROL_OBSERVATION"
        summary["false_marker_count"] = sum(int(summary[name]) for name in (
            "timeout", "sequence_rejection", "crc_rejection", "offline",
            "recovery_during_exposure", "restart", "poll_write_failure"))
        summary["explicit_attributable_outcome"] = True
    else:
        explicit = any(int(summary[name]) > 0 for name in (
            "accepted_mode_3", "timeout", "sequence_rejection", "crc_rejection", "offline"))
        summary["explicit_attributable_outcome"] = explicit
        summary["classification"] = "DELAYED_EXPLICIT_MARKERS" if explicit else None
    return summary


def readable(path: Path, events: Iterable[SerialEvent]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        for event in events:
            handle.write(f"{event.host_time}\t{event.text}\n")


def append_boundary(handle: object, value: dict[str, object]) -> None:
    handle.write(json.dumps(value, sort_keys=True) + "\n")
    handle.flush()


def update_ledger(package: Path, ledger: dict[str, object]) -> None:
    write_json(package / "attempt_ledger.json", ledger)


def mark_remaining(ledger: dict[str, object], after_row: int) -> None:
    for row in ledger["rows"]:  # type: ignore[index]
        if int(row["row"]) > after_row and row["status"] == "PLANNED":
            row.update(status="NOT_ATTEMPTED_AFTER_STOP", attempted=False,
                       valid=None, invalid_reason="FIRST_INVALID_STOP")


def summarize_campaign(ledger: dict[str, object], validations: list[dict[str, object]]) -> dict[str, object]:
    by_condition: dict[str, dict[str, object]] = {}
    validations_by_id = {str(item["run_id"]): item for item in validations}
    for condition in ("NC", "D090", "D100", "D110"):
        planned = [row for row in ledger["rows"] if row["condition"] == condition]  # type: ignore[index]
        attempted = [row for row in planned if row["attempted"]]
        valid = [row for row in attempted if row["valid"] is True]
        invalid = [row for row in attempted if row["valid"] is False]
        not_attempted = [row for row in planned if not row["attempted"]]
        counts: defaultdict[str, int] = defaultdict(int)
        for row in valid:
            outcome = validations_by_id[str(row["run_id"])]["outcome"]
            for name in ("accepted_mode_0", "accepted_mode_3", "timeout",
                         "sequence_rejection", "crc_rejection", "offline",
                         "recovery_during_exposure", "restart", "poll_write_failure"):
                counts[name] += int(outcome[name])
            counts["restoration_confirmed"] += int(
                validations_by_id[str(row["run_id"])]["restore_confirmation_host_time"] is not None)
            counts["recovery_after_restore"] += int(
                validations_by_id[str(row["run_id"])]["recovery_host_time"] is not None)
        by_condition[condition] = {
            "planned": len(planned), "attempted": len(attempted),
            "valid": len(valid), "invalid": len(invalid),
            "not_attempted_after_stop": len(not_attempted),
            "valid_row_marker_counts": dict(counts),
        }
    rows = ledger["rows"]  # type: ignore[index]
    return {
        "campaign_id": CAMPAIGN_ID,
        "planned": len(rows),
        "attempted": sum(bool(row["attempted"]) for row in rows),
        "valid": sum(row["valid"] is True for row in rows),
        "invalid": sum(row["valid"] is False for row in rows),
        "not_attempted_after_stop": sum(row["status"] == "NOT_ATTEMPTED_AFTER_STOP" for row in rows),
        "conditions": by_condition,
        "population_interval_or_reliability_estimate": None,
    }


def acquire(package: Path, controller_port: str, payload_port: str,
            controller_elf: Path, payload_elf: Path) -> int:
    master_dir = package / "raw" / "master"
    terminal_paths = (package / "precheck_validation.json",
                      package / "campaign_validation.json",
                      package / "final_disposition.json")
    if master_dir.exists() or any(path.exists() for path in terminal_paths):
        raise FileExistsError("campaign acquisition path already exists")
    manifest = json.loads((package / "locked_manifest.json").read_text(encoding="utf-8"))
    if not manifest.get("locked") or manifest.get("campaign_id") != CAMPAIGN_ID:
        raise ValueError("locked campaign manifest mismatch")
    if sha256_file(controller_elf) != EXPECTED_CONTROLLER_ELF:
        raise ValueError("controller ELF hash mismatch before serial open")
    if sha256_file(payload_elf) != EXPECTED_PAYLOAD_ELF:
        raise ValueError("payload ELF hash mismatch before serial open")
    ledger = json.loads((package / "attempt_ledger.json").read_text(encoding="utf-8"))
    if ledger != initial_ledger():
        raise ValueError("attempt ledger is not pristine locked state")

    master_dir.mkdir(parents=True, exist_ok=False)
    controller_log = (master_dir / "controller.log").open("x", encoding="ascii", newline="\n")
    payload_log = (master_dir / "payload.log").open("x", encoding="ascii", newline="\n")
    boundary_handle = (package / "row_boundary_ledger.jsonl").open("x", encoding="utf-8", newline="\n")
    resources = None
    validations: list[dict[str, object]] = []
    precheck_valid = False
    run_exception: str | None = None
    try:
        resources = open_pair(controller_port, payload_port)
        controller_serial, payload_serial, controller, payload = resources
        controller.attach_log(controller_log)
        payload.attach_log(payload_log)
        controller_start = controller.snapshot()
        payload_start = payload.snapshot()
        payload_flash = openocd_program(PAYLOAD_STLINK, payload_elf,
                                        master_dir / "flash_payload.log")
        controller_flash = openocd_program(CONTROLLER_STLINK, controller_elf,
                                           master_dir / "flash_controller.log")
        payload_ready = payload.wait_for(
            lambda e: "[PAYLOAD] READY board=NUCLEO-F411RE role=PAYLOAD" in e.text,
            payload_start, 8.0)
        controller_ready = controller.wait_for(
            lambda e: "[OBC] READY board=NUCLEO-F411RE role=CONTROLLER" in e.text,
            controller_start, 8.0)
        link_start = controller.wait_for(lambda e: "[OBC] PAYLOAD_LINK_START" in e.text,
                                         controller_start, 8.0)
        normal_boundary = payload.snapshot()
        normal_command_host, _ = send_mode(payload_serial, "NORMAL")
        normal = wait_mode_confirmation(payload, "NORMAL", normal_boundary, 3.0)
        online = controller.wait_for(lambda e: "[OBC] PAYLOAD_ONLINE" in e.text,
                                     controller_start, 8.0)
        link_active = payload.wait_for(lambda e: "[PAYLOAD] LINK_ACTIVE" in e.text,
                                       payload_start, 8.0)
        bringup_failures: list[str] = []
        if payload_flash["exit_code"] != 0: bringup_failures.append("PAYLOAD_FLASH_FAILED")
        if controller_flash["exit_code"] != 0: bringup_failures.append("CONTROLLER_FLASH_FAILED")
        if payload_ready is None: bringup_failures.append("PAYLOAD_READY_MISSING")
        if controller_ready is None: bringup_failures.append("CONTROLLER_READY_MISSING")
        if link_start is None: bringup_failures.append("LINK_START_MISSING")
        if normal is None: bringup_failures.append("NORMAL_CONFIRMATION_MISSING")
        if online is None: bringup_failures.append("ONLINE_TRANSITION_MISSING")
        if link_active is None: bringup_failures.append("LINK_ACTIVE_MISSING")

        pre_controller_boundary = controller.snapshot()
        pre_payload_boundary = payload.snapshot()
        pre_start_mono = time.monotonic()
        pre_start_host = utc_now()
        if not bringup_failures:
            time.sleep(65.0)
        pre_end_mono = time.monotonic()
        controller_events = [e for e in controller.events_since(pre_controller_boundary)
                             if pre_start_mono <= e.monotonic_s <= pre_end_mono]
        payload_events = [e for e in payload.events_since(pre_payload_boundary)
                          if pre_start_mono <= e.monotonic_s <= pre_end_mono]
        statuses = [record for event in controller_events
                    if (record := status_record(event)) is not None]
        pre_failures = list(bringup_failures)
        if not bringup_failures:
            pre_failures.extend(validate_normal_statuses(statuses))
        prohibited = marker_records(
            controller_events, CONTROLLER_PROHIBITED + RESET_OR_FAULT) + marker_records(
                payload_events, SERIAL_PROHIBITED + RESET_OR_FAULT)
        if prohibited: pre_failures.append("PROHIBITED_MARKER")
        precheck = {
            "record_id": PRECHECK_ID, "scientific_row": False,
            "payload_flash": payload_flash, "controller_flash": controller_flash,
            "payload_ready_host_time": payload_ready.host_time if payload_ready else None,
            "controller_ready_host_time": controller_ready.host_time if controller_ready else None,
            "link_start_host_time": link_start.host_time if link_start else None,
            "initial_normal_command_host_time": normal_command_host,
            "initial_normal_confirmation_host_time": normal.host_time if normal else None,
            "online_transition_host_time": online.host_time if online else None,
            "link_active_host_time": link_active.host_time if link_active else None,
            "window_start_host_time": pre_start_host,
            "window_end_host_time": utc_now(),
            "window_duration_s_monotonic": round(pre_end_mono - pre_start_mono, 6),
            "status_records": statuses,
            "counter_deltas": {field: int(statuses[-1][field]) - int(statuses[0][field])
                               if statuses else None for field in COUNTERS},
            "prohibited_markers": prohibited,
            "valid": not pre_failures, "failures": pre_failures,
        }
        write_json(package / "precheck_validation.json", precheck)
        precheck_valid = not pre_failures
        if not precheck_valid:
            mark_remaining(ledger, 0)
            update_ledger(package, ledger)
        else:
            for plan in plan_rows():
                row_number = int(plan["row"])
                run_id = str(plan["run_id"])
                condition = str(plan["condition"])
                row_dir = package / "raw" / "rows" / run_id
                row_dir.mkdir(exist_ok=False)
                row_ledger = ledger["rows"][row_number - 1]
                row_ledger.update(status="ATTEMPTED", attempted=True,
                                  started_host_time=utc_now())
                update_ledger(package, ledger)
                row_controller_start = controller.snapshot()
                row_payload_start = payload.snapshot()
                row_result: dict[str, object] = dict(plan)
                row_result.update(started_host_time=utc_now(), exposure_s=EXPOSURE_S)
                failures: list[str] = []
                pre_gate = fresh_normal_gate(controller, payload, payload_serial)
                row_result["pre_stabilization"] = pre_gate
                if not pre_gate["valid"]:
                    failures.append("PRE_STABILIZATION_FAILED")
                activation_command_host = None
                activation_confirmation_host = None
                activation_equivalent_host = None
                exposure_start_host = None
                exposure_end_host = None
                restore_command_host = None
                restore_confirmation_host = None
                recovery_host = None
                outcome: dict[str, object] = {"classification": None,
                                              "explicit_attributable_outcome": False}
                post_gate = None
                exposure_controller_boundary = controller.snapshot()
                exposure_payload_boundary = payload.snapshot()
                if not failures:
                    if condition == "NC":
                        activation_equivalent_host = utc_now()
                    else:
                        confirmation_boundary = payload.snapshot()
                        activation_command_host, _ = send_mode(
                            payload_serial, f"DELAYED {int(plan['delay_ms'])}")
                        confirmation = wait_mode_confirmation(
                            payload, f"DELAYED delay_ms={int(plan['delay_ms'])}",
                            confirmation_boundary, 3.0)
                        activation_confirmation_host = confirmation.host_time if confirmation else None
                        if confirmation is None:
                            failures.append("EXACT_ACTIVATION_NOT_CONFIRMED")
                    if not failures:
                        exposure_controller_boundary = controller.snapshot()
                        exposure_payload_boundary = payload.snapshot()
                        exposure_start_mono = time.monotonic()
                        exposure_start_host = utc_now()
                        time.sleep(EXPOSURE_S)
                        exposure_end_mono = time.monotonic()
                        exposure_end_host = utc_now()
                        exposure_controller_events = [
                            e for e in controller.events_since(exposure_controller_boundary)
                            if exposure_start_mono <= e.monotonic_s <= exposure_end_mono]
                        exposure_payload_events = [
                            e for e in payload.events_since(exposure_payload_boundary)
                            if exposure_start_mono <= e.monotonic_s <= exposure_end_mono]
                        outcome = outcome_summary(exposure_controller_events, condition)
                        serial_failures = marker_records(
                            exposure_controller_events,
                            ("UART_RX_", "PAYLOAD_POLL_WRITE_FAILED") + RESET_OR_FAULT) + marker_records(
                                exposure_payload_events, SERIAL_PROHIBITED + RESET_OR_FAULT)
                        if serial_failures: failures.append("SERIAL_OR_UART_FAILURE")
                        if condition != "NC" and not outcome["explicit_attributable_outcome"]:
                            failures.append("EXPLICIT_ATTRIBUTABLE_OUTCOME_MISSING")

                if pre_gate.get("normal_confirmation_host_time") is not None:
                    restore_boundary = payload.snapshot()
                    restore_controller_boundary = controller.snapshot()
                    restore_command_host, _ = send_mode(payload_serial, "NORMAL")
                    restored = wait_mode_confirmation(payload, "NORMAL", restore_boundary, 3.0)
                    restore_confirmation_host = restored.host_time if restored else None
                    if restored is None:
                        failures.append("NORMAL_RESTORE_NOT_CONFIRMED")
                    if int(outcome.get("offline", 0)) > 0:
                        recovered = controller.wait_for(
                            lambda e: "[OBC] PAYLOAD_RECOVERED" in e.text,
                            restore_controller_boundary, 5.0)
                        recovery_host = recovered.host_time if recovered else None
                        if recovered is None: failures.append("RECOVERY_MARKER_MISSING")
                    if restored is not None:
                        post_controller_boundary = controller.snapshot()
                        post_payload_boundary = payload.snapshot()
                        post_gate = stabilization(controller, payload,
                                                  post_controller_boundary,
                                                  post_payload_boundary)
                        if not post_gate["valid"]:
                            failures.append("POST_STABILIZATION_FAILED")

                controller.assert_healthy()
                payload.assert_healthy()
                row_controller_events = controller.events_since(row_controller_start)
                row_payload_events = payload.events_since(row_payload_start)
                readable(row_dir / "controller_readable.txt", row_controller_events)
                readable(row_dir / "payload_readable.txt", row_payload_events)
                row_result.update(
                    activation_command_host_time=activation_command_host,
                    activation_confirmation_host_time=activation_confirmation_host,
                    activation_equivalent_host_time=activation_equivalent_host,
                    exposure_start_host_time=exposure_start_host,
                    exposure_end_host_time=exposure_end_host,
                    outcome=outcome,
                    restore_command_host_time=restore_command_host,
                    restore_confirmation_host_time=restore_confirmation_host,
                    recovery_host_time=recovery_host,
                    post_stabilization=post_gate,
                    valid=not failures, failures=failures,
                    finished_host_time=utc_now())
                write_json(row_dir / "validation.json", row_result)
                append_boundary(boundary_handle, {
                    "row": row_number, "run_id": run_id, "condition": condition,
                    "row_controller_start": row_controller_start,
                    "row_payload_start": row_payload_start,
                    "exposure_controller_boundary": exposure_controller_boundary,
                    "exposure_payload_boundary": exposure_payload_boundary,
                    "activation_command_host_time": activation_command_host,
                    "activation_confirmation_host_time": activation_confirmation_host,
                    "activation_equivalent_host_time": activation_equivalent_host,
                    "exposure_start_host_time": exposure_start_host,
                    "exposure_end_host_time": exposure_end_host,
                    "restore_command_host_time": restore_command_host,
                    "restore_confirmation_host_time": restore_confirmation_host,
                    "finished_host_time": row_result["finished_host_time"],
                })
                validations.append(row_result)
                row_ledger.update(
                    status="VALID" if not failures else "INVALID",
                    valid=not failures, invalid_reason=";".join(failures) or None,
                    finished_host_time=row_result["finished_host_time"])
                if failures:
                    mark_remaining(ledger, row_number)
                update_ledger(package, ledger)
                if failures:
                    break
    except Exception as exc:
        run_exception = f"HARNESS_EXCEPTION:{type(exc).__name__}:{exc}"
        attempted_rows = [row for row in ledger["rows"] if row["attempted"]]
        current = attempted_rows[-1] if attempted_rows else None
        if current is not None and current["status"] == "ATTEMPTED":
            current.update(status="INVALID", valid=False, invalid_reason=run_exception,
                           finished_host_time=utc_now())
            mark_remaining(ledger, int(current["row"]))
        else:
            mark_remaining(ledger, 0 if current is None else int(current["row"]))
        update_ledger(package, ledger)
    finally:
        if resources is not None:
            _, _, controller, payload = resources
            controller.detach_log()
            payload.detach_log()
            close_pair(resources)
        boundary_handle.close()
        controller_log.close()
        payload_log.close()
        write_json(package / "port_close_status.json", {
            "controller_port_closed": resources is not None,
            "payload_port_closed": resources is not None,
            "closed_host_time": utc_now(),
        })

    summary = summarize_campaign(ledger, validations)
    summary["precheck_valid"] = precheck_valid
    summary["harness_exception"] = run_exception
    complete = (precheck_valid and summary["attempted"] == 12 and
                summary["valid"] == 12 and summary["invalid"] == 0 and
                run_exception is None)
    summary["campaign_valid"] = complete
    summary["terminal_disposition"] = (
        COMPLETE_DISPOSITION if complete else STOPPED_DISPOSITION)
    write_json(package / "descriptive_condition_summary.json", summary)
    write_json(package / "campaign_validation.json", {
        "campaign_id": CAMPAIGN_ID, "precheck_valid": precheck_valid,
        "row_validations": validations, "accounting": summary,
        "valid": complete, "failures": [] if complete else [
            run_exception or "PRECHECK_OR_FIRST_INVALID_STOP"],
    })
    write_json(package / "final_disposition.json", {
        "campaign_id": CAMPAIGN_ID,
        "disposition": summary["terminal_disposition"],
        "accounting": {key: summary[key] for key in (
            "planned", "attempted", "valid", "invalid", "not_attempted_after_stop")},
        "campaign_is_separate_from_pilot": True,
        "second_pair_or_manuscript_authorized": False,
        "finished_host_time": utc_now(),
    })
    return 0 if complete else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--package", type=Path, required=True)
    prepare.add_argument("--controller-elf", type=Path, required=True)
    prepare.add_argument("--controller-bin", type=Path, required=True)
    prepare.add_argument("--payload-elf", type=Path, required=True)
    prepare.add_argument("--payload-bin", type=Path, required=True)
    run = sub.add_parser("acquire")
    run.add_argument("--package", type=Path, required=True)
    run.add_argument("--controller-port", required=True)
    run.add_argument("--payload-port", required=True)
    run.add_argument("--controller-elf", type=Path, required=True)
    run.add_argument("--payload-elf", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        return prepare_package(args.package.resolve(), args.controller_elf.resolve(),
                               args.controller_bin.resolve(), args.payload_elf.resolve(),
                               args.payload_bin.resolve())
    return acquire(args.package.resolve(), args.controller_port, args.payload_port,
                   args.controller_elf.resolve(), args.payload_elf.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
