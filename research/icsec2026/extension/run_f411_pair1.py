#!/usr/bin/env python3
"""Acquire the gated F411 Pair-1 bring-up, NORMAL window, and one 110 ms pilot."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
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
    send_mode,
    utc_now,
    wait_mode_confirmation,
)

CONTROLLER_STLINK = "066BFF495051727187053106"
PAYLOAD_STLINK = "066EFF495051727187053015"
STATUS_RE = re.compile(
    r"^\[OBC\] PAYLOAD_STATUS state=(?P<state>\S+) "
    r"polls=(?P<polls>\d+) ok=(?P<ok>\d+) timeout=(?P<timeout>\d+) "
    r"crc=(?P<crc>\d+) seq=(?P<seq>\d+) recovery=(?P<recovery>\d+) "
    r"heartbeat=OK watchdog=OK$"
)
COUNTERS = ("timeout", "crc", "seq", "recovery")
CONTROLLER_PROHIBITED = (
    "[OBC] PAYLOAD_REJECT",
    "[OBC] PAYLOAD_TIMEOUT",
    "[OBC] PAYLOAD_OFFLINE",
    "[OBC] PAYLOAD_RECOVERED",
    "[OBC] PAYLOAD_LINK_START",
    "[OBC] PAYLOAD_POLL_WRITE_FAILED",
    "[OBC] UART_RX_OVERFLOW",
    "[OBC] UART_RX_ERROR",
)
SERIAL_PROHIBITED = (
    "UART_RX_OVERFLOW",
    "UART_RX_ERROR",
    "LINK_WRITE_FAILED",
)


def write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
    temporary.replace(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest().upper()


def status_record(event: SerialEvent) -> dict[str, object] | None:
    match = STATUS_RE.match(event.text)
    if match is None:
        return None
    result: dict[str, object] = {
        "host_time": event.host_time,
        "monotonic_s": event.monotonic_s,
        "state": match.group("state"),
    }
    for field in ("polls", "ok", *COUNTERS):
        result[field] = int(match.group(field))
    return result


def marker_records(events: Iterable[SerialEvent], needles: tuple[str, ...]) -> list[dict[str, str]]:
    return [
        {"host_time": event.host_time, "marker": event.text}
        for event in events
        if any(needle in event.text for needle in needles)
    ]


def validate_normal_statuses(statuses: list[dict[str, object]]) -> list[str]:
    failures: list[str] = []
    if len(statuses) < 10:
        failures.append("FEWER_THAN_10_STATUS_RECORDS")
    if any(record["state"] != "ONLINE" for record in statuses):
        failures.append("NON_ONLINE_STATUS")
    if not all(int(b["ok"]) > int(a["ok"]) for a, b in zip(statuses, statuses[1:])):
        failures.append("OK_NOT_STRICTLY_INCREASING")
    if statuses:
        for field in COUNTERS:
            if int(statuses[-1][field]) - int(statuses[0][field]) != 0:
                failures.append(f"{field.upper()}_COUNTER_DELTA")
    return failures


def classify_pilot_markers(markers: list[str]) -> str | None:
    if any("[OBC] PAYLOAD_ACCEPTED" in marker and "mode=3" in marker for marker in markers):
        return "ACCEPTED_DELAYED_RESPONSE"
    if any("[OBC] PAYLOAD_OFFLINE" in marker for marker in markers):
        return "TIMEOUT_REJECTION_OFFLINE"
    if any("[OBC] PAYLOAD_TIMEOUT" in marker for marker in markers):
        return "TIMEOUT_PATH"
    if any("[OBC] PAYLOAD_REJECT" in marker for marker in markers):
        return "REJECTION_PATH"
    return None


def attach_logs(base: Path, controller: SerialCapture, payload: SerialCapture):
    base.mkdir(parents=True, exist_ok=False)
    controller_log = (base / "controller.log").open("x", encoding="ascii", newline="\n")
    payload_log = (base / "payload.log").open("x", encoding="ascii", newline="\n")
    controller.attach_log(controller_log)
    payload.attach_log(payload_log)
    return controller_log, payload_log


def detach_logs(handles: tuple[object, object], controller: SerialCapture,
                payload: SerialCapture) -> None:
    controller.detach_log()
    payload.detach_log()
    for handle in handles:
        handle.close()


def open_pair(controller_port: str, payload_port: str):
    import serial  # type: ignore[import-not-found]
    controller_serial = serial.Serial(controller_port, 115200, timeout=0.05, write_timeout=1.0)
    try:
        payload_serial = serial.Serial(payload_port, 115200, timeout=0.05, write_timeout=1.0)
    except Exception:
        controller_serial.close()
        raise
    controller = SerialCapture("f411-p1-controller", controller_serial)
    payload = SerialCapture("f411-p1-payload", payload_serial)
    controller.start()
    payload.start()
    return controller_serial, payload_serial, controller, payload


def close_pair(resources: tuple[object, object, SerialCapture, SerialCapture]) -> None:
    controller_serial, payload_serial, controller, payload = resources
    controller.stop()
    payload.stop()
    controller_serial.close()
    payload_serial.close()


def gate(controller: SerialCapture, payload: SerialCapture, payload_serial: object,
         timeout_s: float = 20.0) -> dict[str, object]:
    confirmation_start = payload.snapshot()
    command_host, _ = send_mode(payload_serial, "NORMAL")
    confirmation = wait_mode_confirmation(payload, "NORMAL", confirmation_start, 3.0)
    if confirmation is None:
        return {"valid": False, "failures": ["NORMAL_CONFIRMATION_MISSING"],
                "normal_command_host_time": command_host}
    boundary = controller.snapshot()
    payload_boundary = payload.snapshot()
    deadline = time.monotonic() + timeout_s
    statuses: list[dict[str, object]] = []
    while time.monotonic() < deadline:
        controller.assert_healthy()
        payload.assert_healthy()
        statuses = [record for event in controller.events_since(boundary)
                    if (record := status_record(event)) is not None]
        if len(statuses) >= 2 and int(statuses[-1]["ok"]) - int(statuses[0]["ok"]) >= 3:
            break
        time.sleep(0.05)
    controller_events = controller.events_since(boundary)
    payload_events = payload.events_since(payload_boundary)
    statuses = [record for event in controller_events
                if (record := status_record(event)) is not None]
    failures: list[str] = []
    if len(statuses) < 2:
        failures.append("FEWER_THAN_TWO_STATUS_RECORDS")
    elif int(statuses[-1]["ok"]) - int(statuses[0]["ok"]) < 3:
        failures.append("FEWER_THAN_THREE_SUBSEQUENT_SUCCESSES")
    if any(record["state"] != "ONLINE" for record in statuses):
        failures.append("NON_ONLINE_STATUS")
    deltas = {field: int(statuses[-1][field]) - int(statuses[0][field])
              if statuses else None for field in COUNTERS}
    if any(delta != 0 for delta in deltas.values()):
        failures.append("FAULT_COUNTER_DELTA")
    prohibited = marker_records(controller_events, CONTROLLER_PROHIBITED) + \
        marker_records(payload_events, SERIAL_PROHIBITED)
    if prohibited:
        failures.append("PROHIBITED_MARKER")
    return {
        "valid": not failures,
        "normal_command_host_time": command_host,
        "normal_confirmation_host_time": confirmation.host_time,
        "status_records": statuses,
        "counter_deltas": deltas,
        "prohibited_markers": prohibited,
        "failures": failures,
    }


def openocd_program(serial: str, elf: Path, log_path: Path) -> dict[str, object]:
    root = Path.home() / ".platformio" / "packages" / "tool-openocd"
    executable = root / "bin" / "openocd.exe"
    scripts = root / "openocd" / "scripts"
    command = [
        str(executable), "-d2", "-s", str(scripts),
        "-c", f"adapter serial {serial}",
        "-f", "interface/stlink.cfg",
        "-c", "transport select hla_swd",
        "-f", "target/stm32f4x.cfg",
        "-c", f"program {elf.as_posix()} verify reset exit",
    ]
    completed = subprocess.run(command, text=True, capture_output=True, timeout=60.0)
    log_path.write_text(completed.stdout + completed.stderr, encoding="utf-8", newline="\n")
    return {"command": command, "exit_code": completed.returncode,
            "log": log_path.name, "elf_sha256": sha256_file(elf)}


def bringup(package: Path, controller_port: str, payload_port: str,
            controller_elf: Path, payload_elf: Path, run_id: str) -> int:
    run_dir = package / "raw" / "bringup" / run_id
    resources = open_pair(controller_port, payload_port)
    controller_serial, payload_serial, controller, payload = resources
    handles = attach_logs(run_dir, controller, payload)
    result: dict[str, object] = {"run_id": run_id, "started_host_time": utc_now()}
    try:
        payload_start = payload.snapshot()
        controller_start = controller.snapshot()
        payload_flash = openocd_program(PAYLOAD_STLINK, payload_elf, run_dir / "flash_payload.log")
        controller_flash = openocd_program(CONTROLLER_STLINK, controller_elf,
                                           run_dir / "flash_controller.log")
        payload_ready = payload.wait_for(
            lambda event: "[PAYLOAD] READY board=NUCLEO-F411RE role=PAYLOAD" in event.text,
            payload_start, 8.0)
        controller_ready = controller.wait_for(
            lambda event: "[OBC] READY board=NUCLEO-F411RE role=CONTROLLER" in event.text,
            controller_start, 8.0)
        normal_start = payload.snapshot()
        command_host, _ = send_mode(payload_serial, "NORMAL")
        normal = wait_mode_confirmation(payload, "NORMAL", normal_start, 3.0)
        link_active = payload.wait_for(lambda event: "[PAYLOAD] LINK_ACTIVE" in event.text,
                                       payload_start, 10.0)
        online = controller.wait_for(
            lambda event: "[OBC] PAYLOAD_STATUS state=ONLINE" in event.text,
            controller_start, 10.0)
        time.sleep(1.0)
        controller_events = controller.events_since(controller_start)
        payload_events = payload.events_since(payload_start)
        prohibited = marker_records(controller_events, ("UART_RX_", "PAYLOAD_POLL_WRITE_FAILED")) + \
            marker_records(payload_events, SERIAL_PROHIBITED)
        failures = []
        if payload_flash["exit_code"] != 0: failures.append("PAYLOAD_FLASH_FAILED")
        if controller_flash["exit_code"] != 0: failures.append("CONTROLLER_FLASH_FAILED")
        if payload_ready is None: failures.append("PAYLOAD_READY_MISSING")
        if controller_ready is None: failures.append("CONTROLLER_READY_MISSING")
        if normal is None: failures.append("NORMAL_CONFIRMATION_MISSING")
        if link_active is None: failures.append("LINK_ACTIVE_MISSING")
        if online is None: failures.append("CONTROLLER_ONLINE_MISSING")
        if prohibited: failures.append("UART_OR_WRITE_FAILURE")
        result.update(
            payload_flash=payload_flash,
            controller_flash=controller_flash,
            normal_command_host_time=command_host,
            payload_ready_host_time=payload_ready.host_time if payload_ready else None,
            controller_ready_host_time=controller_ready.host_time if controller_ready else None,
            normal_confirmation_host_time=normal.host_time if normal else None,
            link_active_host_time=link_active.host_time if link_active else None,
            controller_online_host_time=online.host_time if online else None,
            prohibited_markers=prohibited,
            valid=not failures,
            invalid_reason=";".join(failures),
            finished_host_time=utc_now(),
        )
        write_json(package / "bringup_validation.json", result)
        return 0 if not failures else 2
    finally:
        detach_logs(handles, controller, payload)
        close_pair(resources)


def normal_window(package: Path, controller_port: str, payload_port: str) -> int:
    resources = open_pair(controller_port, payload_port)
    controller_serial, payload_serial, controller, payload = resources
    handles = attach_logs(package / "raw" / "normal" / "NORMAL_001", controller, payload)
    result: dict[str, object] = {"run_id": "NORMAL_001", "requested_s": 65.0,
                                "started_host_time": utc_now()}
    try:
        pre_gate = gate(controller, payload, payload_serial)
        if not pre_gate["valid"]:
            result.update(valid=False, invalid_reason="PRE_NORMAL_GATE_FAILED",
                          pre_stabilization=pre_gate, finished_host_time=utc_now())
            write_json(package / "normal_validation.json", result)
            return 2
        controller_start = controller.snapshot()
        payload_start = payload.snapshot()
        start_mono = time.monotonic()
        start_host = utc_now()
        time.sleep(65.0)
        end_mono = time.monotonic()
        controller.assert_healthy()
        payload.assert_healthy()
        controller_events = [event for event in controller.events_since(controller_start)
                             if start_mono <= event.monotonic_s <= end_mono]
        payload_events = [event for event in payload.events_since(payload_start)
                          if start_mono <= event.monotonic_s <= end_mono]
        statuses = [record for event in controller_events
                    if (record := status_record(event)) is not None]
        failures = validate_normal_statuses(statuses)
        prohibited = marker_records(controller_events, CONTROLLER_PROHIBITED) + \
            marker_records(payload_events, SERIAL_PROHIBITED)
        if prohibited:
            failures.append("PROHIBITED_MARKER")
        result.update(
            pre_stabilization=pre_gate,
            window_start_host_time=start_host,
            window_end_host_time=utc_now(),
            duration_s=round(end_mono - start_mono, 6),
            status_count=len(statuses),
            status_records=statuses,
            counter_deltas={field: int(statuses[-1][field]) - int(statuses[0][field])
                            if statuses else None for field in COUNTERS},
            prohibited_markers=prohibited,
            valid=not failures,
            invalid_reason=";".join(failures),
            finished_host_time=utc_now(),
        )
        write_json(package / "normal_validation.json", result)
        return 0 if not failures else 2
    finally:
        detach_logs(handles, controller, payload)
        close_pair(resources)


def pilot(package: Path, controller_port: str, payload_port: str) -> int:
    resources = open_pair(controller_port, payload_port)
    controller_serial, payload_serial, controller, payload = resources
    handles = attach_logs(package / "raw" / "pilot" / "PILOT_D110_001", controller, payload)
    result: dict[str, object] = {"run_id": "PILOT_D110_001", "delay_ms": 110,
                                "observation_s": 4.0, "started_host_time": utc_now()}
    try:
        pre_gate = gate(controller, payload, payload_serial)
        result["pre_stabilization"] = pre_gate
        if not pre_gate["valid"]:
            result.update(valid=False, invalid_reason="PRE_STABILIZATION_FAILED",
                          disposition="PAIR1_PILOT_FAIL", finished_host_time=utc_now())
            write_json(package / "pilot_validation.json", result)
            return 2
        activation_start = payload.snapshot()
        command_host, command_mono = send_mode(payload_serial, "DELAYED 110")
        activation = wait_mode_confirmation(payload, "DELAYED delay_ms=110",
                                             activation_start, 3.0)
        result["activation_command_host_time"] = command_host
        result["activation_confirmation_host_time"] = activation.host_time if activation else None
        if activation is None:
            result.update(valid=False, invalid_reason="EXACT_ACTIVATION_NOT_CONFIRMED",
                          disposition="PAIR1_PILOT_FAIL", finished_host_time=utc_now())
            write_json(package / "pilot_validation.json", result)
            return 2
        controller_start = controller.snapshot()
        payload_start = payload.snapshot()
        time.sleep(4.0)
        end_mono = time.monotonic()
        controller.assert_healthy()
        payload.assert_healthy()
        controller_events = [event for event in controller.events_since(controller_start)
                             if command_mono <= event.monotonic_s <= end_mono]
        payload_events = [event for event in payload.events_since(payload_start)
                          if command_mono <= event.monotonic_s <= end_mono]
        observed_markers = [event.text for event in controller_events
                            if "[OBC] PAYLOAD_" in event.text]
        outcome = classify_pilot_markers(observed_markers)
        restore_start = payload.snapshot()
        restore_host, _ = send_mode(payload_serial, "NORMAL")
        restored = wait_mode_confirmation(payload, "NORMAL", restore_start, 3.0)
        post_gate = gate(controller, payload, payload_serial) if restored is not None else None
        serial_failures = marker_records(controller_events, ("UART_RX_",)) + \
            marker_records(payload_events, SERIAL_PROHIBITED)
        failures = []
        if outcome is None: failures.append("UNAMBIGUOUS_TERMINAL_OUTCOME_MISSING")
        if restored is None: failures.append("NORMAL_RESTORE_NOT_CONFIRMED")
        if post_gate is None or not post_gate["valid"]: failures.append("POST_STABILIZATION_FAILED")
        if serial_failures: failures.append("SERIAL_OR_UART_FAILURE")
        result.update(
            observed_markers=[{"host_time": event.host_time, "marker": event.text}
                              for event in controller_events if "[OBC] PAYLOAD_" in event.text],
            outcome=outcome,
            restore_command_host_time=restore_host,
            restore_confirmation_host_time=restored.host_time if restored else None,
            post_stabilization=post_gate,
            serial_failure_markers=serial_failures,
            valid=not failures,
            invalid_reason=";".join(failures),
            unexpected_outcome="",
            disposition="PAIR1_PILOT_PASS" if not failures else "PAIR1_PILOT_FAIL",
            finished_host_time=utc_now(),
        )
        write_json(package / "pilot_validation.json", result)
        return 0 if not failures else 2
    finally:
        detach_logs(handles, controller, payload)
        close_pair(resources)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("bringup", "normal", "pilot"))
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--controller-port", required=True)
    parser.add_argument("--payload-port", required=True)
    parser.add_argument("--controller-elf", type=Path)
    parser.add_argument("--payload-elf", type=Path)
    parser.add_argument("--run-id", default="BRINGUP_001")
    args = parser.parse_args()
    if args.command == "bringup":
        if args.controller_elf is None or args.payload_elf is None:
            parser.error("bringup requires --controller-elf and --payload-elf")
        return bringup(args.package, args.controller_port, args.payload_port,
                       args.controller_elf.resolve(), args.payload_elf.resolve(), args.run_id)
    if args.command == "normal":
        return normal_window(args.package, args.controller_port, args.payload_port)
    return pilot(args.package, args.controller_port, args.payload_port)


if __name__ == "__main__":
    raise SystemExit(main())
