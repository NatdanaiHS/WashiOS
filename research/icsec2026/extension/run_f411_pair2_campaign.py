#!/usr/bin/env python3
"""Pair-2 identity/path profile for the reviewed F411 campaign engine."""

from __future__ import annotations

import run_f411_campaign as campaign
from pathlib import Path


PAIR2_PLAN = (
    (1, "F411P2_C01_B1_NC", 1, "NC", None),
    (2, "F411P2_C02_B1_D110", 1, "D110", 110),
    (3, "F411P2_C03_B1_D090", 1, "D090", 90),
    (4, "F411P2_C04_B1_D100", 1, "D100", 100),
    (5, "F411P2_C05_B2_D090", 2, "D090", 90),
    (6, "F411P2_C06_B2_NC", 2, "NC", None),
    (7, "F411P2_C07_B2_D100", 2, "D100", 100),
    (8, "F411P2_C08_B2_D110", 2, "D110", 110),
    (9, "F411P2_C09_B3_D100", 3, "D100", 100),
    (10, "F411P2_C10_B3_D110", 3, "D110", 110),
    (11, "F411P2_C11_B3_NC", 3, "NC", None),
    (12, "F411P2_C12_B3_D090", 3, "D090", 90),
)


def configure() -> None:
    here = Path(__file__).resolve().parent
    campaign.CAMPAIGN_ID = "F411_P2_CAMPAIGN_20260901_B3"
    campaign.PRECHECK_ID = "F411_P2_CAMPAIGN_20260901_B3_PRECHECK"
    campaign.MANIFEST_SCHEMA = "washios.icsec2026.f411_pair2_campaign.v1"
    campaign.CONTROLLER_BOARD_ID = "F411-C"
    campaign.PAYLOAD_BOARD_ID = "F411-D"
    campaign.CONTROLLER_STLINK = "0669FF495051727187053226"
    campaign.PAYLOAD_STLINK = "0663FF495051727187066042"
    campaign.CONTROLLER_FIRMWARE_ELF = "f411_p2_fixed_controller.elf"
    campaign.CONTROLLER_FIRMWARE_BIN = "f411_p2_fixed_controller.bin"
    campaign.PAYLOAD_FIRMWARE_ELF = "f411_p2_payload.elf"
    campaign.PAYLOAD_FIRMWARE_BIN = "f411_p2_payload.bin"
    campaign.COMPLETE_DISPOSITION = "F411_P2_CAMPAIGN_COMPLETE_AWAITING_REVIEW"
    campaign.STOPPED_DISPOSITION = "F411_P2_CAMPAIGN_STOPPED_INVALID_AWAITING_REVIEW"
    campaign.CLAIM_BOUNDARY = (
        "sequential descriptive evidence from independent physical F411 Pair-2; "
        "separate from Pair-1, pilot, diagnostic, and G431/G474 packages"
    )
    campaign.PLAN = PAIR2_PLAN
    campaign.CODE_PATHS = (
        here / "run_f411_campaign.py",
        here / "run_f411_pair2_campaign.py",
        here / "test_f411_campaign.py",
        here / "test_f411_pair2_campaign.py",
        here / "validate_f411_campaign.py",
        here / "validate_f411_pair2_campaign.py",
    )


def main() -> int:
    configure()
    return campaign.main()


if __name__ == "__main__":
    raise SystemExit(main())
