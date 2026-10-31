#!/usr/bin/env python3
"""Independent validator profile for the separate F411 Pair-2 campaign."""

from __future__ import annotations

from pathlib import Path
import argparse
import json

import run_f411_pair2_campaign as pair2


def main() -> int:
    pair2.configure()
    import validate_f411_campaign as validator

    validator.CAMPAIGN_ID = pair2.campaign.CAMPAIGN_ID
    validator.COMPLETE_DISPOSITION = pair2.campaign.COMPLETE_DISPOSITION
    validator.CONTROLLER_FIRMWARE_ELF = pair2.campaign.CONTROLLER_FIRMWARE_ELF
    validator.CONTROLLER_FIRMWARE_BIN = pair2.campaign.CONTROLLER_FIRMWARE_BIN
    validator.PAYLOAD_FIRMWARE_ELF = pair2.campaign.PAYLOAD_FIRMWARE_ELF
    validator.PAYLOAD_FIRMWARE_BIN = pair2.campaign.PAYLOAD_FIRMWARE_BIN
    validator.PLAN = pair2.campaign.PLAN

    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validator.validate(args.package.resolve())
    result["schema"] = "washios.icsec2026.f411_pair2_campaign_independent_validation.v1"
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
