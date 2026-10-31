#!/usr/bin/env python3
"""Read-only independent validation of the retained F411 scientific pilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_f411_pair1 import write_json


def escaped_rendering(raw: bytes) -> str:
    rendered: list[str] = []
    for byte in raw:
        if 0x20 <= byte <= 0x7E and byte != 0x5C:
            rendered.append(chr(byte))
        elif byte == 0x5C:
            rendered.append("\\\\")
        elif byte == 0x0A:
            rendered.append("\\n")
        elif byte == 0x0D:
            rendered.append("\\r")
        elif byte == 0x09:
            rendered.append("\\t")
        else:
            rendered.append(f"\\x{byte:02x}")
    return "".join(rendered)


def validate_log(path: Path) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    texts: list[str] = []
    for number, line in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
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
        if escaped_rendering(raw) != rendered:
            failures.append(f"{path.name}:{number}:RENDER_MISMATCH")
        texts.append(rendered)
    return failures, texts


def count(texts: list[str], marker: str) -> int:
    return sum(marker in text for text in texts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    package = args.package.resolve()
    raw = package / "raw" / "F411_P1_SCI_PILOT_001_D110"
    controller_failures, controller = validate_log(raw / "controller.log")
    payload_failures, payload = validate_log(raw / "payload.log")
    precondition = json.loads((package / "precondition_validation.json").read_text())
    pilot = json.loads((package / "pilot_validation.json").read_text())
    flash_controller = (raw / "flash_controller.log").read_text(errors="replace")
    flash_payload = (raw / "flash_payload.log").read_text(errors="replace")
    partial_final = [text for text in controller if text.endswith("PAYLOAD_ACCE")]
    failures = controller_failures + payload_failures
    checks = {
        "precondition_id_exact": precondition.get("record_id") ==
            "F411_P1_SCI_PILOT_001_D110_PRECHECK",
        "precondition_valid": precondition.get("valid") is True,
        "pilot_id_exact": pilot.get("run_id") == "F411_P1_SCI_PILOT_001_D110",
        "pilot_valid_original": pilot.get("valid") is True,
        "activation_exactly_once": count(payload, "MODE=DELAYED delay_ms=110") == 1,
        "offline_observed": count(controller, "PAYLOAD_OFFLINE consecutive=3") == 1,
        "recovery_observed": count(controller, "PAYLOAD_RECOVERED recoveries=1") == 1,
        "controller_flash_verified": flash_controller.count("** Verified OK **") == 1,
        "payload_flash_verified": flash_payload.count("** Verified OK **") == 1,
        "ports_closed": json.loads((package / "port_close_status.json").read_text()) ==
            {"closed_host_time": json.loads((package / "port_close_status.json").read_text())["closed_host_time"],
             "controller_port_closed": True, "payload_port_closed": True},
    }
    failures.extend(name for name, passed in checks.items() if not passed)
    result = {
        "schema": "washios.icsec2026.f411_pair1_scientific_independent_validation.v1",
        "checks": checks,
        "raw_record_counts": {"controller": len(controller), "payload": len(payload)},
        "raw_format_or_render_failures": controller_failures + payload_failures,
        "marker_counts": {
            "controller_status": count(controller, "PAYLOAD_STATUS state="),
            "accepted": count(controller, "PAYLOAD_ACCEPTED"),
            "timeout_transition": count(controller, "PAYLOAD_TIMEOUT consecutive="),
            "sequence_reject": count(controller, "PAYLOAD_REJECT reason=SEQUENCE"),
            "offline": count(controller, "PAYLOAD_OFFLINE consecutive=3"),
            "recovery": count(controller, "PAYLOAD_RECOVERED recoveries=1"),
            "payload_normal_confirmations": count(payload, "[PAYLOAD] MODE=NORMAL"),
            "payload_delayed_110_confirmations": count(payload, "MODE=DELAYED delay_ms=110"),
        },
        "capture_boundary_partial_records": partial_final,
        "capture_boundary_partial_record_count": len(partial_final),
        "failures": failures,
        "valid_raw_and_machine_evidence": not failures,
    }
    write_json(package / "independent_raw_validation.json", result)
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
