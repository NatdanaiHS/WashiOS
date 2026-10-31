#!/usr/bin/env python3
"""Validate the bounded F411 manuscript claim correction and promotion."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[3]
OLD = ROOT / "research/icsec2026/extension/manuscript_candidate_f411_20260902"
CORRECTED = ROOT / "research/icsec2026/extension/manuscript_candidate_f411_20260902_corrected"
ACTIVE = ROOT / "research/icsec2026/extension/manuscript"
CORRECTION_PACKAGE_MANUSCRIPT = ROOT / "research/icsec2026/extension/analysis/f411_claim_correction_20260902/manuscript"
OLD_INTEGRATION = ROOT / "research/icsec2026/extension/analysis/f411_cross_pair_integration_20260902"
OLD_INTEGRATION_BACKUP = Path("C:/WashiOS-extension-backup/f411_cross_pair_integration_20260902")
FROZEN_PDF_SHA256 = "992A1C9AA41F4295BF7F97CA081D79A7DE2ABBB4B419B2A0B82144C1B50928DF"
FROZEN_COMMIT = "8a47d070c549274c59cdbde2495afa8d353a93b3"

OLD_1 = "pair-specific protocol-level reproduction on two separate F411 configurations"
NEW_1 = "pair-specific protocol-level reproduction on two separate physical F411 controller/payload pairs under one fixed F411 implementation"
OLD_2 = "protocol-level physical reproduction across two configurations"
NEW_2 = "protocol-level physical reproduction on two separate physical pairs under one fixed F411 implementation"

PAIR_SPECS = (
    (
        ROOT / "research/icsec2026/extension/evidence/f411_pair1_campaign_20260901_seed20260901_b3",
        Path("C:/WashiOS-extension-backup/f411_pair1_campaign_20260901_seed20260901_b3"),
        "F411_PAIR1_CAMPAIGN_SHA256SUMS.csv", 95,
        "797F908BCFC5EB5450302360501016DCB23188996C15194D9CF91C8BE619C2BC",
    ),
    (
        ROOT / "research/icsec2026/extension/evidence/f411_pair2_campaign_20260901_seed20260901_b3",
        Path("C:/WashiOS-extension-backup/f411_pair2_campaign_20260901_seed20260901_b3"),
        "F411_PAIR2_CAMPAIGN_SHA256SUMS.csv", 81,
        "481F56C98647D037CFAA5698BDEF61C0D918D42954A646E36C7479EA8203588E",
    ),
)

PRIOR_INVENTORY_HASHES = {
    "research/icsec2026/runs/full_20260830_seed20260830_n30/SHA256SUMS.csv": "DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD",
    "research/icsec2026/provenance/20260830_023830/PROVENANCE_SHA256SUMS.csv": "84139F0C3886C513B2511332766495F04E8EB4705ABBF417E600431C2858D3DC",
    "research/icsec2026/extension/recovery/recovery_20260901/SOURCE_TRANSFER_FILE_INVENTORY.csv": "422760C42F0B8D5BA535E37A58F87136A1A59591601BE3AB01B396D6BB17171C",
    "research/icsec2026/extension/recovery/recovery_20260901/RECOVERY_SHA256SUMS.csv": "BA40B30A7EFEA2F6E438A4B5482D8074AC5D6B834C55118DCF17B42C4BC056C1",
    "research/icsec2026/extension/evidence/primary_20260830_seed20260830_b5/EXTENSION_SHA256SUMS.csv": "8B4CB2AB87CD317905AA4A219B81E99E2E459DC3EEF386D14286297476177C0B",
    "research/icsec2026/extension/evidence/primary_20260830_seed20260830_b5/PARTIAL_SHA256SUMS.csv": "F3DEC9EEED1D7C49942AA52A3722F7D571FBFAA0D98BEAC48F13B24C4BDF5C0C",
    "research/icsec2026/extension/evidence/replication_g431b_20260830_seed20260830_b3/REPLICATION_SHA256SUMS.csv": "F13EBB7FEB42FB3F67E56A8503CB6D70A5F630F2C864A16B22D5BF4D9D19CCE9",
    "research/icsec2026/extension/evidence/scope_g431b_g474a_110ms_20260830/SCOPE_FEASIBILITY_SHA256SUMS.csv": "519E7E142DFAFEA4736CA74D945B3197D106714F9B6B1A6B45C75309EC4B1B0E",
    "research/icsec2026/extension/evidence/f411_feasibility_20260901/F411_FEASIBILITY_SHA256SUMS.csv": "540D3E46D206B9CE29806E291F8328D3B8C4F43F7A58471931AA3BEFB8A8930C",
    "research/icsec2026/extension/evidence/f411_pair1_20260901/PAIR1_SHA256SUMS.csv": "AC00A0C93083FBB553408B2EE20DC283D9002B67F853D472B28D3067E2145A3F",
    "research/icsec2026/extension/evidence/f411_pair1_20260901/PAIR1_CORRECTED_SHA256SUMS.csv": "A5C8BF48D7FD0E9CC3A120B890F11CA49FD8DBB6086FD594A321F14C778AC6C9",
    "research/icsec2026/extension/evidence/f411_engdiag_20260901/ENGDIAG_SHA256SUMS.csv": "98846023F3285F5B9F60C5387E1C54FD6D5EEAA8D5E58A42720795EC9B328DE0",
    "research/icsec2026/extension/evidence/f411_pair1_scientific_pilot_20260901/PREACQUISITION_SHA256SUMS.csv": "0123BCDA3590BF6151A12DF6A0BD1A71FC80F383EB838D44BD38D6B89EBC217D",
    "research/icsec2026/extension/evidence/f411_pair1_scientific_pilot_20260901/SCIENTIFIC_PILOT_SHA256SUMS.csv": "B8B2DB1679A21747B80DB9209E7249C755C30CF8C62464E425906951E24295D1",
    "research/icsec2026/extension/evidence/f411_pair1_campaign_20260901_seed20260901_b3/PREACQUISITION_SHA256SUMS.csv": "F82C38B2017204D723F74223051CEEF64D3F354005999C7C7C3A6BCFCED1B2FC",
    "research/icsec2026/extension/evidence/f411_pair1_campaign_20260901_seed20260901_b3/F411_PAIR1_CAMPAIGN_SHA256SUMS.csv": "797F908BCFC5EB5450302360501016DCB23188996C15194D9CF91C8BE619C2BC",
    "research/icsec2026/extension/evidence/f411_pair2_campaign_20260901_seed20260901_b3/PREACQUISITION_SHA256SUMS.csv": "DE4894ED6056B23E1A7E9A191931B754F3098D9D1B82DFD8456D7650B4A1E9BA",
    "research/icsec2026/extension/evidence/f411_pair2_campaign_20260901_seed20260901_b3/F411_PAIR2_CAMPAIGN_SHA256SUMS.csv": "481F56C98647D037CFAA5698BDEF61C0D918D42954A646E36C7479EA8203588E",
    "research/icsec2026/extension/analysis/f411_cross_pair_integration_20260902/INTEGRATION_SHA256SUMS.csv": "4C0D6FC2AF25228AB3080677D5C14C58DB83029D9041D04610E93F22C3D4BA15",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def verify_inventory(root: Path, inventory_name: str, path_field: str,
                     size_field: str, expected_rows: int, expected_hash: str) -> dict:
    inventory = root / inventory_name
    assert sha256(inventory) == expected_hash
    with inventory.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == expected_rows
    for row in rows:
        artifact = root / row[path_field]
        assert artifact.is_file(), artifact
        assert artifact.stat().st_size == int(row[size_field]), artifact
        assert sha256(artifact) == row["sha256"], artifact
    return {"root": root.as_posix(), "rows": len(rows), "issues": 0,
            "inventory_sha256": expected_hash}


def main() -> int:
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else CORRECTED / "qa/FINAL_VALIDATION.json"
    old_text = (OLD / "main.tex").read_text(encoding="utf-8")
    corrected_text = (CORRECTED / "main.tex").read_text(encoding="utf-8")
    assert old_text.count(OLD_1) == 1 and old_text.count(OLD_2) == 1
    expected = old_text.replace(OLD_1, NEW_1).replace(OLD_2, NEW_2)
    assert corrected_text == expected
    assert corrected_text.count(OLD_1) == 0 and corrected_text.count(OLD_2) == 0
    assert corrected_text.count(NEW_1) == 1 and corrected_text.count(NEW_2) == 1
    assert "24/24" not in corrected_text
    assert (OLD / "references.bib").read_bytes() == (CORRECTED / "references.bib").read_bytes()

    pdf = PdfReader(CORRECTED / "main.pdf")
    pdf_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    assert len(pdf.pages) == 5
    assert "two separate F411 configurations" not in pdf_text
    assert "physical reproduction across two configurations" not in pdf_text
    assert not (pdf.metadata.author or "").strip()

    old_inventory_hash = "4C0D6FC2AF25228AB3080677D5C14C58DB83029D9041D04610E93F22C3D4BA15"
    old_source = verify_inventory(OLD_INTEGRATION, "INTEGRATION_SHA256SUMS.csv",
                                  "path", "size", 31, old_inventory_hash)
    old_backup = verify_inventory(OLD_INTEGRATION_BACKUP, "INTEGRATION_SHA256SUMS.csv",
                                  "path", "size", 31, old_inventory_hash)
    pairs = []
    for source, backup, inventory, rows, inventory_hash in PAIR_SPECS:
        pairs.append({
            "source": verify_inventory(source, inventory, "relative_path", "size_bytes", rows, inventory_hash),
            "backup": verify_inventory(backup, inventory, "relative_path", "size_bytes", rows, inventory_hash),
        })

    candidate_files = sorted(p.relative_to(CORRECTED) for p in CORRECTED.rglob("*") if p.is_file())
    active_files = sorted(p.relative_to(ACTIVE) for p in ACTIVE.rglob("*") if p.is_file())
    package_files = sorted(p.relative_to(CORRECTION_PACKAGE_MANUSCRIPT) for p in CORRECTION_PACKAGE_MANUSCRIPT.rglob("*") if p.is_file())
    assert active_files == candidate_files
    assert package_files == candidate_files
    for relative in candidate_files:
        assert (CORRECTED / relative).read_bytes() == (ACTIVE / relative).read_bytes(), relative
        assert (CORRECTED / relative).read_bytes() == (CORRECTION_PACKAGE_MANUSCRIPT / relative).read_bytes(), relative

    for relative, expected_hash in PRIOR_INVENTORY_HASHES.items():
        assert sha256(ROOT / relative) == expected_hash, relative

    assert git("rev-parse", "main") == FROZEN_COMMIT
    assert git("rev-parse", "origin/main") == FROZEN_COMMIT
    assert git("rev-parse", "icsec-2026-evaluated-state") == FROZEN_COMMIT
    assert sha256(ROOT / "research/icsec2026/manuscript/main.pdf") == FROZEN_PDF_SHA256

    result = {
        "schema": "washios.icsec2026.f411_claim_correction.v1",
        "valid": True,
        "claim_change": {
            "authorized_replacements": 2,
            "other_source_changes": 0,
            "old_phrases_remaining": 0,
            "new_phrase_1_count": 1,
            "new_phrase_2_count": 1,
            "numerical_or_table_changes": 0,
        },
        "candidate": {
            "main_tex_sha256": sha256(CORRECTED / "main.tex"),
            "main_pdf_sha256": sha256(CORRECTED / "main.pdf"),
            "references_sha256": sha256(CORRECTED / "references.bib"),
            "pages": len(pdf.pages),
            "anonymous": True,
        },
        "active_extension_manuscript": {
            "path": ACTIVE.as_posix(),
            "file_count": len(active_files),
            "exact_candidate_copy": True,
        },
        "correction_package_manuscript": {
            "path": CORRECTION_PACKAGE_MANUSCRIPT.as_posix(),
            "file_count": len(package_files),
            "exact_candidate_copy": True,
        },
        "prior_inventory_file_hashes": PRIOR_INVENTORY_HASHES,
        "pair_inventory_verification": pairs,
        "prior_integration_verification": {"source": old_source, "backup": old_backup},
        "frozen_fallback": {
            "commit": FROZEN_COMMIT,
            "main": git("rev-parse", "main"),
            "origin_main": git("rev-parse", "origin/main"),
            "tag": git("rev-parse", "icsec-2026-evaluated-state"),
            "pdf_sha256": FROZEN_PDF_SHA256,
            "unchanged": True,
        },
        "friday_quantitative_scope_campaign": "NO-GO",
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
