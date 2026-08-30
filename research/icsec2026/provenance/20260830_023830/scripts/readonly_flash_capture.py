#!/usr/bin/env python3
"""Acquire a full STM32 flash image with an explicitly selected ST-LINK probe.

The generated OpenOCD command is deliberately limited to attach, halt, memory
dump, resume, and shutdown. It never requests programming, erase, unprotect,
option-byte changes, or reset.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path


FORBIDDEN_COMMAND_WORDS = ("program", "erase", "unprotect", "option", "reset")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openocd", required=True, type=Path)
    parser.add_argument("--scripts", required=True, type=Path)
    parser.add_argument("--stlink-serial", required=True)
    parser.add_argument("--board", required=True)
    parser.add_argument("--address", required=True, type=lambda value: int(value, 0))
    parser.add_argument("--length", required=True, type=lambda value: int(value, 0))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    for path in (args.output, args.log, args.report):
        if path.exists():
            raise SystemExit(f"refusing to overwrite existing provenance artifact: {path}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output_for_openocd = args.output.resolve().as_posix()
    operation = (
        f"init; targets; halt; dump_image {{{output_for_openocd}}} "
        f"0x{args.address:08X} 0x{args.length:X}; resume; shutdown;"
    )
    lowered = operation.lower()
    present = [word for word in FORBIDDEN_COMMAND_WORDS if word in lowered]
    if present:
        raise SystemExit(f"internal safety check rejected OpenOCD operation: {present}")

    command = [
        str(args.openocd.resolve()),
        "-d2",
        "-s",
        str(args.scripts.resolve()),
        "-f",
        "interface/stlink.cfg",
        "-c",
        f"adapter serial {args.stlink_serial}",
        "-c",
        "transport select swd",
        "-f",
        "target/stm32g4x.cfg",
        "-c",
        operation,
    ]
    started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds")
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    finished = dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds")
    log_text = completed.stdout + completed.stderr
    args.log.write_text(log_text, encoding="utf-8")

    report: dict[str, object] = {
        "schema_version": 1,
        "board": args.board,
        "stlink_serial": args.stlink_serial,
        "address_start": f"0x{args.address:08X}",
        "address_end_inclusive": f"0x{args.address + args.length - 1:08X}",
        "requested_byte_count": args.length,
        "started_host_time": started,
        "finished_host_time": finished,
        "openocd_exit_code": completed.returncode,
        "operation": operation,
        "safety": "No program, erase, unprotect, option-byte, or reset command issued.",
        "status": "FAILED",
    }
    if completed.returncode == 0 and args.output.is_file():
        actual_size = args.output.stat().st_size
        report["actual_byte_count"] = actual_size
        report["sha256"] = sha256_file(args.output)
        report["status"] = "COMPLETE" if actual_size == args.length else "SIZE_MISMATCH"
    else:
        report["failure"] = "OpenOCD read-only acquisition did not complete; see log."
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "COMPLETE" else 2


if __name__ == "__main__":
    sys.exit(main())
