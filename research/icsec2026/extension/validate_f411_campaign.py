#!/usr/bin/env python3
"""Independent validation for the retained predefined F411 Pair-1 campaign."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from run_f411_campaign import (
    CAMPAIGN_ID,
    COMPLETE_DISPOSITION,
    CONTROLLER_FIRMWARE_BIN,
    CONTROLLER_FIRMWARE_ELF,
    EXPECTED_CONTROLLER_BIN,
    EXPECTED_CONTROLLER_ELF,
    EXPECTED_PAYLOAD_BIN,
    EXPECTED_PAYLOAD_ELF,
    PAYLOAD_FIRMWARE_BIN,
    PAYLOAD_FIRMWARE_ELF,
    PLAN,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def validate_raw(path: Path) -> tuple[int, list[str], list[str]]:
    failures: list[str] = []
    texts: list[str] = []
    lines = path.read_text(encoding="ascii").splitlines()
    for number, line in enumerate(lines, 1):
        parts = line.split("\t", 2)
        if len(parts) != 3:
            failures.append(f"{path.name}:{number}:FIELD_COUNT")
            continue
        _, raw_hex, rendered = parts
        try:
            raw = bytes.fromhex(raw_hex)
        except ValueError:
            failures.append(f"{path.name}:{number}:RAW_HEX")
            continue
        expected = "".join(
            chr(byte) if 0x20 <= byte <= 0x7E and byte != 0x5C
            else "\\\\" if byte == 0x5C
            else "\\n" if byte == 0x0A
            else "\\r" if byte == 0x0D
            else "\\t" if byte == 0x09
            else f"\\x{byte:02x}"
            for byte in raw)
        if expected != rendered:
            failures.append(f"{path.name}:{number}:RENDER_MISMATCH")
        texts.append(rendered)
    return len(lines), failures, texts


def validate(package: Path) -> dict[str, object]:
    failures: list[str] = []
    manifest = json.loads((package / "locked_manifest.json").read_text(encoding="utf-8"))
    ledger = json.loads((package / "attempt_ledger.json").read_text(encoding="utf-8"))
    precheck = json.loads((package / "precheck_validation.json").read_text(encoding="utf-8"))
    campaign = json.loads((package / "campaign_validation.json").read_text(encoding="utf-8"))
    disposition = json.loads((package / "final_disposition.json").read_text(encoding="utf-8"))
    with (package / "run_plan.csv").open(encoding="utf-8", newline="") as handle:
        plan = list(csv.DictReader(handle))
    expected_plan = [
        {"row": str(row), "run_id": run_id, "block": str(block),
         "condition": condition, "delay_ms": "" if delay is None else str(delay)}
        for row, run_id, block, condition, delay in PLAN]
    if plan != expected_plan: failures.append("PLAN_MISMATCH")
    if manifest.get("campaign_id") != CAMPAIGN_ID or not manifest.get("locked"):
        failures.append("MANIFEST_MISMATCH")
    firmware = package / "firmware"
    firmware_checks = {
        "controller_elf": digest(firmware / CONTROLLER_FIRMWARE_ELF) == EXPECTED_CONTROLLER_ELF,
        "controller_bin": digest(firmware / CONTROLLER_FIRMWARE_BIN) == EXPECTED_CONTROLLER_BIN,
        "payload_elf": digest(firmware / PAYLOAD_FIRMWARE_ELF) == EXPECTED_PAYLOAD_ELF,
        "payload_bin": digest(firmware / PAYLOAD_FIRMWARE_BIN) == EXPECTED_PAYLOAD_BIN,
    }
    failures.extend(f"FIRMWARE_{name.upper()}" for name, valid in firmware_checks.items() if not valid)
    controller_count, controller_failures, controller_text = validate_raw(
        package / "raw" / "master" / "controller.log")
    payload_count, payload_failures, payload_text = validate_raw(
        package / "raw" / "master" / "payload.log")
    failures.extend(controller_failures + payload_failures)
    rows = ledger.get("rows", [])
    attempted = [row for row in rows if row.get("attempted")]
    valid_rows = [row for row in attempted if row.get("valid") is True]
    invalid_rows = [row for row in attempted if row.get("valid") is False]
    row_file_failures: list[str] = []
    validations: list[dict[str, object]] = []
    for row in attempted:
        path = package / "raw" / "rows" / str(row["run_id"]) / "validation.json"
        if not path.is_file():
            row_file_failures.append(f"MISSING:{row['run_id']}")
            continue
        value = json.loads(path.read_text(encoding="utf-8"))
        validations.append(value)
        if value.get("run_id") != row["run_id"] or value.get("condition") != row["condition"]:
            row_file_failures.append(f"IDENTITY:{row['run_id']}")
    failures.extend(row_file_failures)
    activation_counts = {
        "D090": sum("MODE=DELAYED delay_ms=90" in text for text in payload_text),
        "D100": sum("MODE=DELAYED delay_ms=100" in text for text in payload_text),
        "D110": sum("MODE=DELAYED delay_ms=110" in text for text in payload_text),
        "NORMAL": sum("[PAYLOAD] MODE=NORMAL" in text for text in payload_text),
    }
    complete = (len(rows) == 12 and len(attempted) == 12 and len(valid_rows) == 12
                and not invalid_rows and precheck.get("valid") is True
                and campaign.get("valid") is True
                and disposition.get("disposition") == COMPLETE_DISPOSITION)
    if complete:
        if activation_counts["D090"] != 3: failures.append("D090_ACTIVATION_COUNT")
        if activation_counts["D100"] != 3: failures.append("D100_ACTIVATION_COUNT")
        if activation_counts["D110"] != 3: failures.append("D110_ACTIVATION_COUNT")
    return {
        "schema": "washios.icsec2026.f411_pair1_campaign_independent_validation.v1",
        "campaign_id": CAMPAIGN_ID,
        "firmware_checks": firmware_checks,
        "raw_record_counts": {"controller": controller_count, "payload": payload_count},
        "raw_failures": controller_failures + payload_failures,
        "accounting": {"planned": len(rows), "attempted": len(attempted),
                       "valid": len(valid_rows), "invalid": len(invalid_rows),
                       "not_attempted": len(rows) - len(attempted)},
        "activation_confirmation_counts": activation_counts,
        "row_validation_count": len(validations),
        "failures": failures,
        "valid": not failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.package.resolve())
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
