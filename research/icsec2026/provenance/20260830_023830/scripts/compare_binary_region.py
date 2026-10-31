#!/usr/bin/env python3
"""Compare a binary against a region of a captured flash image."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def differing_ranges(actual: bytes, expected: bytes) -> list[tuple[int, int]]:
    ranges = []
    start = None
    for index, (actual_byte, expected_byte) in enumerate(zip(actual, expected)):
        differs = actual_byte != expected_byte
        if differs and start is None:
            start = index
        elif not differs and start is not None:
            ranges.append((start, index))
            start = None
    if start is not None:
        ranges.append((start, len(expected)))
    return ranges


def non_ff_ranges(data: bytes, base_offset: int) -> list[tuple[int, int]]:
    ranges = []
    start = None
    for index, byte in enumerate(data):
        non_ff = byte != 0xFF
        if non_ff and start is None:
            start = index
        elif not non_ff and start is not None:
            ranges.append((base_offset + start, base_offset + index))
            start = None
    if start is not None:
        ranges.append((base_offset + start, base_offset + len(data)))
    return ranges


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", required=True, type=Path)
    parser.add_argument("--expected", required=True, type=Path)
    parser.add_argument("--capture-offset", required=True, type=lambda value: int(value, 0))
    parser.add_argument("--flash-base", default="0x08000000", type=lambda value: int(value, 0))
    parser.add_argument("--label", required=True)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--differences", required=True, type=Path)
    args = parser.parse_args()

    for output in (args.report, args.differences):
        if output.exists():
            raise SystemExit(f"refusing to overwrite: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
    capture = args.capture.read_bytes()
    expected = args.expected.read_bytes()
    end = args.capture_offset + len(expected)
    if end > len(capture):
        raise SystemExit("expected binary extends beyond captured flash")
    actual = capture[args.capture_offset:end]
    ranges = differing_ranges(actual, expected)

    with args.differences.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "region_offset_start",
                "region_offset_end_exclusive",
                "flash_address_start",
                "flash_address_end_exclusive",
                "byte_count",
                "captured_sha256",
                "expected_sha256",
            ),
        )
        writer.writeheader()
        for start, stop in ranges:
            writer.writerow(
                {
                    "region_offset_start": start,
                    "region_offset_end_exclusive": stop,
                    "flash_address_start": f"0x{args.flash_base + args.capture_offset + start:08X}",
                    "flash_address_end_exclusive": f"0x{args.flash_base + args.capture_offset + stop:08X}",
                    "byte_count": stop - start,
                    "captured_sha256": digest(actual[start:stop]),
                    "expected_sha256": digest(expected[start:stop]),
                }
            )

    trailing = capture[end:]
    trailing_non_ff = non_ff_ranges(trailing, end)
    report = {
        "schema_version": 1,
        "label": args.label,
        "capture_file": str(args.capture),
        "capture_sha256": digest(capture),
        "capture_byte_count": len(capture),
        "expected_file": str(args.expected),
        "expected_sha256": digest(expected),
        "expected_byte_count": len(expected),
        "capture_offset": args.capture_offset,
        "flash_address_start": f"0x{args.flash_base + args.capture_offset:08X}",
        "flash_address_end_exclusive": f"0x{args.flash_base + end:08X}",
        "captured_region_sha256": digest(actual),
        "exact_match": not ranges,
        "differing_range_count": len(ranges),
        "differing_byte_count": sum(stop - start for start, stop in ranges),
        "differences_file": str(args.differences),
        "bytes_after_compared_region": len(trailing),
        "non_ff_bytes_after_compared_region": sum(
            stop - start for start, stop in trailing_non_ff
        ),
        "non_ff_range_count_after_compared_region": len(trailing_non_ff),
    }
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
