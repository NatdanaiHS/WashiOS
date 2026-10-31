#!/usr/bin/env python3
"""Inventory non-erased byte ranges in an otherwise unattributed flash region."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", required=True, type=Path)
    parser.add_argument("--start-offset", required=True, type=lambda value: int(value, 0))
    parser.add_argument("--end-offset", required=True, type=lambda value: int(value, 0))
    parser.add_argument("--flash-base", default="0x08000000", type=lambda value: int(value, 0))
    parser.add_argument("--label", required=True)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--ranges", required=True, type=Path)
    args = parser.parse_args()
    for output in (args.report, args.ranges):
        if output.exists():
            raise SystemExit(f"refusing to overwrite: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
    capture = args.capture.read_bytes()
    if not (0 <= args.start_offset <= args.end_offset <= len(capture)):
        raise SystemExit("invalid region offsets")
    region = capture[args.start_offset : args.end_offset]
    ranges = []
    start = None
    for index, byte in enumerate(region):
        if byte != 0xFF and start is None:
            start = index
        elif byte == 0xFF and start is not None:
            ranges.append((start, index))
            start = None
    if start is not None:
        ranges.append((start, len(region)))

    with args.ranges.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("flash_address_start", "flash_address_end_exclusive", "byte_count", "sha256"),
        )
        writer.writeheader()
        for start, stop in ranges:
            writer.writerow(
                {
                    "flash_address_start": f"0x{args.flash_base + args.start_offset + start:08X}",
                    "flash_address_end_exclusive": f"0x{args.flash_base + args.start_offset + stop:08X}",
                    "byte_count": stop - start,
                    "sha256": sha256(region[start:stop]),
                }
            )
    report = {
        "schema_version": 1,
        "label": args.label,
        "capture_file": str(args.capture),
        "flash_address_start": f"0x{args.flash_base + args.start_offset:08X}",
        "flash_address_end_exclusive": f"0x{args.flash_base + args.end_offset:08X}",
        "byte_count": len(region),
        "sha256": sha256(region),
        "all_ff": not ranges,
        "non_ff_byte_count": sum(stop - start for start, stop in ranges),
        "non_ff_range_count": len(ranges),
        "ranges_file": str(args.ranges),
    }
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
