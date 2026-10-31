#!/usr/bin/env python3
"""Execute the one authorized fresh F411 Pair-1 110 ms scientific pilot."""

from __future__ import annotations

import argparse
import time
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

RUN_ID = "F411_P1_SCI_PILOT_001_D110"
PRECHECK_ID = "F411_P1_SCI_PILOT_001_D110_PRECHECK"
EXPECTED_CONTROLLER_ELF = "9AA52D103E977A8B18968A0B7F3D69E74361AC5E5FFDFA6B3CBC49A3AD722D78"
EXPECTED_PAYLOAD_ELF = "0BC0EAAA7830B001CD31F1805C1002275E62FAF8DE6BC8C1AF44ABF5A2005493"
RESET_OR_FAULT = ("RESET", "HARDFAULT", "FAULT", "STACK_OVERFLOW")


def accepted_records(events: Iterable[SerialEvent]) -> list[dict[str, str]]:
    return [
        {"host_time": event.host_time, "marker": event.text}
        for event in events
        if "[OBC] PAYLOAD_ACCEPTED" in event.text
    ]


def classify_attributable_outcome(events: Iterable[SerialEvent]) -> dict[str, object]:
    markers = [
        {"host_time": event.host_time, "marker": event.text}
        for event in events
        if "[OBC] PAYLOAD_" in event.text
    ]
    texts = [str(record["marker"]) for record in markers]
    delayed = [record for record in markers
               if "PAYLOAD_ACCEPTED" in str(record["marker"])
               and "mode=3" in str(record["marker"])]
    timeout_indices = [index for index, text in enumerate(texts)
                       if "PAYLOAD_TIMEOUT" in text]
    reject_indices = [index for index, text in enumerate(texts)
                      if "PAYLOAD_REJECT" in text]
    offline_indices = [index for index, text in enumerate(texts)
                       if "PAYLOAD_OFFLINE" in text]
    if delayed and not timeout_indices and not reject_indices and not offline_indices:
        return {"valid": True, "classification": "ACCEPTED_DELAYED_RESPONSE",
                "attributable_markers": delayed, "all_markers": markers}
    if timeout_indices and offline_indices and timeout_indices[0] < offline_indices[0]:
        relevant = [record for record in markers
                    if any(token in str(record["marker"])
                           for token in ("PAYLOAD_TIMEOUT", "PAYLOAD_REJECT", "PAYLOAD_OFFLINE"))]
        return {
            "valid": True,
            "classification": "ORDERED_TIMEOUT_PATH_TO_OFFLINE",
            "timeout_count": len(timeout_indices),
            "rejection_count": len(reject_indices),
            "offline_observed": True,
            "attributable_markers": relevant,
            "all_markers": markers,
        }
    return {"valid": False, "classification": None,
            "failure": "ATTRIBUTABLE_TERMINAL_OUTCOME_MISSING",
            "all_markers": markers}


def stabilization(controller: SerialCapture, payload: SerialCapture,
                  controller_boundary: int, payload_boundary: int,
                  timeout_s: float = 20.0) -> dict[str, object]:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        controller.assert_healthy()
        payload.assert_healthy()
        controller_events = controller.events_since(controller_boundary)
        statuses = [record for event in controller_events
                    if (record := status_record(event)) is not None]
        accepts = accepted_records(controller_events)
        if len(statuses) >= 2 and len(accepts) >= 3:
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
    deltas = {field: int(statuses[-1][field]) - int(statuses[0][field])
              if statuses else None for field in COUNTERS}
    if any(delta != 0 for delta in deltas.values()):
        failures.append("FAULT_COUNTER_DELTA")
    prohibited = marker_records(controller_events, CONTROLLER_PROHIBITED + RESET_OR_FAULT) + \
        marker_records(payload_events, SERIAL_PROHIBITED)
    if prohibited:
        failures.append("PROHIBITED_MARKER")
    return {
        "valid": not failures,
        "status_records": statuses,
        "accepted_exchanges": accepts,
        "counter_deltas": deltas,
        "prohibited_markers": prohibited,
        "failures": failures,
    }


def run(package: Path, controller_port: str, payload_port: str,
        controller_elf: Path, payload_elf: Path) -> int:
    run_dir = package / "raw" / RUN_ID
    validation_paths = [package / "precondition_validation.json",
                        package / "pilot_validation.json"]
    if run_dir.exists() or any(path.exists() for path in validation_paths):
        raise FileExistsError("exclusive scientific run path already exists")
    if sha256_file(controller_elf) != EXPECTED_CONTROLLER_ELF:
        raise ValueError("controller ELF hash mismatch before serial open")
    if sha256_file(payload_elf) != EXPECTED_PAYLOAD_ELF:
        raise ValueError("payload ELF hash mismatch before serial open")

    run_dir.mkdir(parents=True, exist_ok=False)
    controller_log = (run_dir / "controller.log").open("x", encoding="ascii", newline="\n")
    payload_log = (run_dir / "payload.log").open("x", encoding="ascii", newline="\n")
    resources = None
    delayed_command_sent = False
    restore_command_sent = False
    result: dict[str, object] = {
        "run_id": RUN_ID,
        "precondition_id": PRECHECK_ID,
        "scientific_observation": True,
        "campaign_denominator": False,
        "started_host_time": utc_now(),
    }
    try:
        resources = open_pair(controller_port, payload_port)
        controller_serial, payload_serial, controller, payload = resources
        controller.attach_log(controller_log)
        payload.attach_log(payload_log)
        controller_start = controller.snapshot()
        payload_start = payload.snapshot()

        payload_flash = openocd_program(PAYLOAD_STLINK, payload_elf,
                                        run_dir / "flash_payload.log")
        controller_flash = openocd_program(CONTROLLER_STLINK, controller_elf,
                                           run_dir / "flash_controller.log")
        payload_ready = payload.wait_for(
            lambda event: "[PAYLOAD] READY board=NUCLEO-F411RE role=PAYLOAD" in event.text,
            payload_start, 8.0)
        controller_ready = controller.wait_for(
            lambda event: "[OBC] READY board=NUCLEO-F411RE role=CONTROLLER" in event.text,
            controller_start, 8.0)
        link_start = controller.wait_for(
            lambda event: "[OBC] PAYLOAD_LINK_START" in event.text,
            controller_start, 8.0)
        normal_start = payload.snapshot()
        initial_normal_host, _ = send_mode(payload_serial, "NORMAL")
        initial_normal = wait_mode_confirmation(payload, "NORMAL", normal_start, 3.0)
        online_transition = controller.wait_for(
            lambda event: "[OBC] PAYLOAD_ONLINE" in event.text,
            controller_start, 8.0)
        link_active = payload.wait_for(
            lambda event: "[PAYLOAD] LINK_ACTIVE" in event.text,
            payload_start, 8.0)

        bringup_failures: list[str] = []
        if payload_flash["exit_code"] != 0: bringup_failures.append("PAYLOAD_FLASH_FAILED")
        if controller_flash["exit_code"] != 0: bringup_failures.append("CONTROLLER_FLASH_FAILED")
        if payload_ready is None: bringup_failures.append("PAYLOAD_READY_MISSING")
        if controller_ready is None: bringup_failures.append("CONTROLLER_READY_MISSING")
        if link_start is None: bringup_failures.append("PAYLOAD_LINK_START_MISSING")
        if initial_normal is None: bringup_failures.append("INITIAL_NORMAL_CONFIRMATION_MISSING")
        if online_transition is None: bringup_failures.append("ONLINE_TRANSITION_MISSING")
        if link_active is None: bringup_failures.append("LINK_ACTIVE_MISSING")

        normal_boundary = controller.snapshot()
        normal_payload_boundary = payload.snapshot()
        normal_start_mono = time.monotonic()
        normal_start_host = utc_now()
        if not bringup_failures:
            time.sleep(65.0)
        normal_end_mono = time.monotonic()
        controller_events = [event for event in controller.events_since(normal_boundary)
                             if normal_start_mono <= event.monotonic_s <= normal_end_mono]
        payload_events = [event for event in payload.events_since(normal_payload_boundary)
                          if normal_start_mono <= event.monotonic_s <= normal_end_mono]
        statuses = [record for event in controller_events
                    if (record := status_record(event)) is not None]
        normal_failures = list(bringup_failures)
        if not bringup_failures:
            normal_failures.extend(validate_normal_statuses(statuses))
            prohibited = marker_records(controller_events, CONTROLLER_PROHIBITED + RESET_OR_FAULT) + \
                marker_records(payload_events, SERIAL_PROHIBITED + RESET_OR_FAULT)
            if prohibited:
                normal_failures.append("PROHIBITED_MARKER")
        else:
            prohibited = []

        fresh_normal_host = None
        fresh_normal = None
        pre_stabilization = None
        if not normal_failures:
            fresh_start = payload.snapshot()
            fresh_normal_host, _ = send_mode(payload_serial, "NORMAL")
            fresh_normal = wait_mode_confirmation(payload, "NORMAL", fresh_start, 3.0)
            if fresh_normal is None:
                normal_failures.append("FRESH_NORMAL_CONFIRMATION_MISSING")
            else:
                stabilize_controller = controller.snapshot()
                stabilize_payload = payload.snapshot()
                pre_stabilization = stabilization(controller, payload,
                                                  stabilize_controller,
                                                  stabilize_payload)
                if not pre_stabilization["valid"]:
                    normal_failures.append("PRE_STABILIZATION_FAILED")

        precondition = {
            "record_id": PRECHECK_ID,
            "scientific_trial": False,
            "payload_flash": payload_flash,
            "controller_flash": controller_flash,
            "payload_ready_host_time": payload_ready.host_time if payload_ready else None,
            "controller_ready_host_time": controller_ready.host_time if controller_ready else None,
            "payload_link_start_host_time": link_start.host_time if link_start else None,
            "initial_normal_command_host_time": initial_normal_host,
            "initial_normal_confirmation_host_time": initial_normal.host_time if initial_normal else None,
            "online_transition_host_time": online_transition.host_time if online_transition else None,
            "link_active_host_time": link_active.host_time if link_active else None,
            "normal_window_start_host_time": normal_start_host,
            "normal_window_end_host_time": utc_now(),
            "normal_window_duration_s": round(normal_end_mono - normal_start_mono, 6),
            "normal_status_count": len(statuses),
            "normal_status_records": statuses,
            "normal_counter_deltas": {
                field: int(statuses[-1][field]) - int(statuses[0][field])
                if statuses else None for field in COUNTERS
            },
            "normal_prohibited_markers": prohibited,
            "fresh_normal_command_host_time": fresh_normal_host,
            "fresh_normal_confirmation_host_time": fresh_normal.host_time if fresh_normal else None,
            "pre_stabilization": pre_stabilization,
            "valid": not normal_failures,
            "failures": normal_failures,
        }
        write_json(package / "precondition_validation.json", precondition)
        if normal_failures:
            result.update(valid=False, failures=normal_failures,
                          delayed_command_sent=False,
                          disposition="F411_P1_SCI_PILOT_FAIL")
            write_json(package / "pilot_validation.json", result)
            return 2

        activation_boundary = payload.snapshot()
        exposure_controller_boundary = controller.snapshot()
        exposure_payload_boundary = payload.snapshot()
        activation_host, activation_mono = send_mode(payload_serial, "DELAYED 110")
        delayed_command_sent = True
        activation = wait_mode_confirmation(payload, "DELAYED delay_ms=110",
                                             activation_boundary, 3.0)
        if activation is None:
            result.update(valid=False, failures=["EXACT_ACTIVATION_NOT_CONFIRMED"],
                          delayed_command_sent=True,
                          disposition="F411_P1_SCI_PILOT_FAIL")
            write_json(package / "pilot_validation.json", result)
            return 2

        time.sleep(4.0)
        exposure_end_mono = time.monotonic()
        exposure_events = [event for event in controller.events_since(exposure_controller_boundary)
                           if activation_mono <= event.monotonic_s <= exposure_end_mono]
        exposure_payload_events = [event for event in payload.events_since(exposure_payload_boundary)
                                   if activation_mono <= event.monotonic_s <= exposure_end_mono]
        outcome = classify_attributable_outcome(exposure_events)
        exposure_serial_failures = marker_records(
            exposure_events,
            ("UART_RX_", "PAYLOAD_POLL_WRITE_FAILED") + RESET_OR_FAULT,
        ) + \
            marker_records(exposure_payload_events, SERIAL_PROHIBITED + RESET_OR_FAULT)

        restore_boundary = payload.snapshot()
        restore_controller_boundary = controller.snapshot()
        restore_host, _ = send_mode(payload_serial, "NORMAL")
        restore_command_sent = True
        restored = wait_mode_confirmation(payload, "NORMAL", restore_boundary, 3.0)
        recovered = None
        if bool(outcome.get("offline_observed")):
            recovered = controller.wait_for(
                lambda event: "[OBC] PAYLOAD_RECOVERED" in event.text,
                restore_controller_boundary, 5.0)
        post_controller_boundary = controller.snapshot()
        post_payload_boundary = payload.snapshot()
        post_stabilization = stabilization(controller, payload,
                                           post_controller_boundary,
                                           post_payload_boundary)
        failures: list[str] = []
        if not outcome["valid"]: failures.append("ATTRIBUTABLE_OUTCOME_INVALID")
        if restored is None: failures.append("NORMAL_RESTORE_NOT_CONFIRMED")
        if bool(outcome.get("offline_observed")) and recovered is None:
            failures.append("RECOVERY_MARKER_MISSING")
        if not post_stabilization["valid"]:
            failures.append("POST_STABILIZATION_FAILED")
        if exposure_serial_failures:
            failures.append("SERIAL_OR_UART_FAILURE")
        result.update(
            activation_command_host_time=activation_host,
            activation_confirmation_host_time=activation.host_time,
            exposure_duration_s=4.0,
            outcome=outcome,
            restore_command_host_time=restore_host,
            restore_confirmation_host_time=restored.host_time if restored else None,
            recovery_host_time=recovered.host_time if recovered else None,
            post_stabilization=post_stabilization,
            exposure_serial_failure_markers=exposure_serial_failures,
            delayed_command_sent=delayed_command_sent,
            restore_command_sent=restore_command_sent,
            valid=not failures,
            failures=failures,
            disposition=("F411_P1_SCI_PILOT_PASS_AWAITING_REVIEW"
                         if not failures else "F411_P1_SCI_PILOT_FAIL"),
            finished_host_time=utc_now(),
        )
        write_json(package / "pilot_validation.json", result)
        return 0 if not failures else 2
    except Exception as exc:
        result.update(valid=False, failures=[f"HARNESS_EXCEPTION:{type(exc).__name__}:{exc}"],
                      delayed_command_sent=delayed_command_sent,
                      restore_command_sent=restore_command_sent,
                      disposition="F411_P1_SCI_PILOT_FAIL",
                      finished_host_time=utc_now())
        write_json(package / "pilot_validation.json", result)
        return 2
    finally:
        if resources is not None:
            _, _, controller, payload = resources
            controller.detach_log()
            payload.detach_log()
            close_pair(resources)
        controller_log.close()
        payload_log.close()
        write_json(package / "port_close_status.json", {
            "controller_port_closed": resources is not None,
            "payload_port_closed": resources is not None,
            "closed_host_time": utc_now(),
        })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--controller-port", required=True)
    parser.add_argument("--payload-port", required=True)
    parser.add_argument("--controller-elf", type=Path, required=True)
    parser.add_argument("--payload-elf", type=Path, required=True)
    args = parser.parse_args()
    return run(args.package.resolve(), args.controller_port, args.payload_port,
               args.controller_elf.resolve(), args.payload_elf.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
