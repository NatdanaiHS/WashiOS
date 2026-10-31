#!/usr/bin/env python3
"""Capture and validate one dedicated nominal-control (N0) window."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

from run_payload_campaign import SerialCapture, SerialEvent, send_mode, utc_now, wait_mode_confirmation


STATUS_PATTERN = re.compile(
    r"^\[OBC\] PAYLOAD_STATUS state=(?P<state>\S+) "
    r"polls=(?P<polls>\d+) ok=(?P<ok>\d+) timeout=(?P<timeout>\d+) "
    r"crc=(?P<crc>\d+) seq=(?P<seq>\d+) recovery=(?P<recovery>\d+) "
    r"heartbeat=OK watchdog=OK$"
)
PROHIBITED_MARKERS = (
    "[OBC] PAYLOAD_TIMEOUT",
    "[OBC] PAYLOAD_OFFLINE",
    "[OBC] PAYLOAD_REJECT",
    "[OBC] PAYLOAD_RECOVERED",
    "[OBC] PAYLOAD_LINK_START",
)
COUNTERS = ("timeout", "crc", "seq", "recovery")


def validate_n0_events(events: list[SerialEvent], duration_s: float) -> dict[str, object]:
    statuses = []
    prohibited = []
    for event in events:
        match = STATUS_PATTERN.match(event.text)
        if match is not None:
            record: dict[str, object] = {
                "host_time": event.host_time,
                "state": match.group("state"),
            }
            for field in ("polls", "ok", *COUNTERS):
                record[field] = int(match.group(field))
            statuses.append(record)
        for marker in PROHIBITED_MARKERS:
            if marker in event.text:
                prohibited.append({"host_time": event.host_time, "marker": event.text})

    ok_values = [int(record["ok"]) for record in statuses]
    ok_strictly_increasing = all(
        later > earlier for earlier, later in zip(ok_values, ok_values[1:])
    )
    all_online = all(record["state"] == "ONLINE" for record in statuses)
    counter_deltas = {
        counter: (int(statuses[-1][counter]) - int(statuses[0][counter]))
        if statuses
        else None
        for counter in COUNTERS
    }
    failures = []
    if duration_s < 60.0:
        failures.append("WINDOW_SHORTER_THAN_60_SECONDS")
    if len(statuses) < 10:
        failures.append("FEWER_THAN_10_ONLINE_STATUS_RECORDS")
    if not all_online:
        failures.append("NON_ONLINE_STATUS_OBSERVED")
    if not ok_strictly_increasing:
        failures.append("OK_COUNTER_NOT_STRICTLY_INCREASING")
    if any(delta != 0 for delta in counter_deltas.values()):
        failures.append("FAULT_COUNTER_DELTA_NONZERO")
    if prohibited:
        failures.append("PROHIBITED_TRANSITION_MARKER_OBSERVED")

    return {
        "valid": not failures,
        "duration_s": round(duration_s, 6),
        "status_count": len(statuses),
        "all_status_online": all_online,
        "ok_strictly_increasing": ok_strictly_increasing,
        "counter_deltas": counter_deltas,
        "prohibited_markers": prohibited,
        "failures": failures,
        "status_records": statuses,
    }


def write_json(path: Path, value: dict[str, object]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
    temporary.replace(path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="new unique directory under research/icsec2026/runs")
    parser.add_argument("--phase", required=True, choices=("pre", "post"))
    parser.add_argument("--g431-port", required=True)
    parser.add_argument("--g474-port", required=True)
    parser.add_argument("--duration-s", type=float, default=65.0)
    parser.add_argument("--confirm-timeout-s", type=float, default=3.0)
    parser.add_argument("--baud", type=int, default=115200)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.duration_s < 60.0:
        raise SystemExit("N0 duration must be at least 60 seconds")
    if args.g431_port.upper() == args.g474_port.upper():
        raise SystemExit("G431 and G474 ports must be different")
    try:
        import serial  # type: ignore[import-not-found]
    except ImportError as exc:
        raise SystemExit("pyserial is required") from exc

    script_path = Path(__file__).resolve()
    run_dir = script_path.parents[1] / "runs" / args.name
    run_dir.mkdir(parents=True, exist_ok=False)
    g431_log = (run_dir / "g431.log").open("x", encoding="ascii", newline="\n")
    g474_log = (run_dir / "g474.log").open("x", encoding="ascii", newline="\n")
    manifest_path = run_dir / "manifest.json"
    validation_path = run_dir / "validation.json"
    manifest: dict[str, object] = {
        "schema_version": 1,
        "name": args.name,
        "condition": "N0_NOMINAL_CONTROL",
        "phase": args.phase,
        "status": "RUNNING",
        "started_host_time": utc_now(),
        "g431_port": args.g431_port,
        "g474_port": args.g474_port,
        "baud": args.baud,
        "requested_duration_s": args.duration_s,
        "raw_log_format": "utc_iso8601<TAB>raw_hex<TAB>escaped_ascii",
        "literal_status_warning": "heartbeat=OK watchdog=OK are literal strings, not independent measurements",
    }
    write_json(manifest_path, manifest)

    g431_serial = None
    g474_serial = None
    g431 = None
    g474 = None
    exit_code = 2
    try:
        g431_serial = serial.Serial(args.g431_port, args.baud, timeout=0.05, write_timeout=1.0)
        g474_serial = serial.Serial(args.g474_port, args.baud, timeout=0.05, write_timeout=1.0)
        g431 = SerialCapture("g431", g431_serial)
        g474 = SerialCapture("g474", g474_serial)
        g431.attach_log(g431_log)
        g474.attach_log(g474_log)
        g431.start()
        g474.start()

        confirmation_start = g474.snapshot()
        command_time, _ = send_mode(g474_serial, "NORMAL")
        confirmation = wait_mode_confirmation(
            g474, "NORMAL", confirmation_start, args.confirm_timeout_s
        )
        if confirmation is None:
            raise RuntimeError("N0_NORMAL_ACTIVATION_NOT_CONFIRMED")
        window_start_mono = confirmation.monotonic_s
        window_start_host = confirmation.host_time
        print(f"[{utc_now()}] N0 {args.phase} window started", flush=True)
        time.sleep(args.duration_s)
        g431.assert_healthy()
        g474.assert_healthy()
        window_end_mono = time.monotonic()
        window_end_host = utc_now()

        window_events = [
            event
            for event in g431.events_since(0)
            if window_start_mono <= event.monotonic_s <= window_end_mono
        ]
        validation = validate_n0_events(
            window_events, window_end_mono - window_start_mono
        )
        validation.update(
            {
                "phase": args.phase,
                "normal_command_host_time": command_time,
                "window_start_host_time": window_start_host,
                "window_end_host_time": window_end_host,
            }
        )
        write_json(validation_path, validation)
        manifest.update(
            {
                "status": "COMPLETE" if validation["valid"] else "FAILED_VALIDATION",
                "finished_host_time": utc_now(),
                "window_start_host_time": window_start_host,
                "window_end_host_time": window_end_host,
                "validation_file": "validation.json",
            }
        )
        write_json(manifest_path, manifest)
        print(
            f"[{utc_now()}] N0 {args.phase} status={manifest['status']} "
            f"records={validation['status_count']}",
            flush=True,
        )
        exit_code = 0 if validation["valid"] else 2
    except Exception as exc:
        manifest.update(
            {
                "status": "FAILED",
                "finished_host_time": utc_now(),
                "failure": f"{type(exc).__name__}: {exc}",
            }
        )
        write_json(manifest_path, manifest)
        print(manifest["failure"], file=sys.stderr, flush=True)
    finally:
        if g431 is not None:
            g431.detach_log()
            g431.stop()
        if g474 is not None:
            g474.detach_log()
            g474.stop()
        g431_log.close()
        g474_log.close()
        if g431_serial is not None:
            g431_serial.close()
        if g474_serial is not None:
            g474_serial.close()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
