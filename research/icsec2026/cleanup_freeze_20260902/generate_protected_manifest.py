import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
FREEZE_START_COMMIT = "b6fd0a9813168fefe90168b61cd8fb26dae0a48b"
BRANCH = "experiment/icsec-extension-20260830"

FINAL_PDF = ROOT / "research/icsec2026/extension/final_pass_submission_20260902/main.pdf"
FINAL_PDF_SHA256 = "99E4180F4B172C1CC7BABFCF8BE92FCC5442B3868F7AAD1D32A13779849E765D"

PROTECTED_REPOSITORY_SCOPES = [
    "research/icsec2026",
    "core",
    "bootloader",
    "demo-payload",
]

EXCLUDED_MUTABLE_CONTROL_PATHS = {
    "research/icsec2026/SESSION_STATE.md",
    "research/icsec2026/NEXT_TASK.md",
}

EVIDENCE_PACKAGES = [
    "research/icsec2026/runs/full_20260830_seed20260830_n30",
    "research/icsec2026/runs/n0_pre_20260830_0205",
    "research/icsec2026/runs/n0_post_20260830_0224",
    "research/icsec2026/extension/evidence/primary_20260830_seed20260830_b5",
    "research/icsec2026/extension/evidence/f411_pair1_campaign_20260901_seed20260901_b3",
    "research/icsec2026/extension/evidence/f411_pair2_campaign_20260901_seed20260901_b3",
]

MANUSCRIPT_PATHS = [
    "research/icsec2026/extension/final_pass_submission_20260902/main.pdf",
    "research/icsec2026/extension/final_pass_submission_20260902/main.tex",
    "research/icsec2026/extension/final_pass_submission_20260902/references.bib",
    "research/icsec2026/extension/manuscript/main.pdf",
    "research/icsec2026/extension/manuscript/main.tex",
    "research/icsec2026/extension/manuscript/references.bib",
    "research/icsec2026/extension/submission_candidate_20260902",
    "research/icsec2026/manuscript",
]

PROVENANCE_TABLE_DEPENDENCIES = [
    "research/icsec2026/paper/generate_manuscript_tables.py",
    "research/icsec2026/paper/tables/TABLE_PROVENANCE.json",
    "research/icsec2026/paper/tables/n0_controls.csv",
    "research/icsec2026/paper/tables/fault_outcomes.csv",
    "research/icsec2026/paper/tables/latency_summary.csv",
    "research/icsec2026/provenance/20260830_023830",
    "research/icsec2026/extension/generate_f411_cross_pair_synthesis.py",
    "research/icsec2026/extension/test_f411_cross_pair_synthesis.py",
    "research/icsec2026/extension/analysis/f411_cross_pair_synthesis_20260902",
    "research/icsec2026/extension/analysis/f411_cross_pair_synthesis_20260902_r2",
    "research/icsec2026/extension/analysis/f411_cross_pair_synthesis_20260902_r3",
    "research/icsec2026/extension/analysis/f411_cross_pair_synthesis_20260902_r4",
    "research/icsec2026/extension/analysis/f411_cross_pair_integration_20260902",
    "research/icsec2026/extension/analysis/f411_claim_correction_20260902",
    "research/icsec2026/extension/analysis/submission_readiness_20260902",
    "research/icsec2026/extension/final_pass_submission_20260902",
    "core/include/comms/PayloadLinkController.hpp",
    "core/src/app/PayloadLinkTask.hpp",
]

EXTERNAL_BACKUPS = [
    "C:/WashiOS-extension-backup/primary_20260830_seed20260830_b5",
    "C:/WashiOS-extension-backup/replication_g431b_20260830_seed20260830_b3",
    "C:/WashiOS-extension-backup/scope_g431b_g474a_110ms_20260830",
    "C:/WashiOS-extension-backup/f411_pair1_scientific_pilot_20260901",
    "C:/WashiOS-extension-backup/f411_pair1_campaign_20260901_seed20260901_b3",
    "C:/WashiOS-extension-backup/f411_pair2_campaign_20260901_seed20260901_b3",
    "C:/WashiOS-extension-backup/f411_cross_pair_integration_20260902",
    "C:/WashiOS-extension-backup/f411_claim_correction_20260902",
    "C:/WashiOS-extension-backup/submission_readiness_20260902",
    "C:/WashiOS-extension-backup/final_pass_submission_20260902",
]

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()

def tree_digest(rows):
    h = hashlib.sha256()
    for row in rows:
        h.update((row["path"] + "\0" + str(row["bytes"]) + "\0" + row["sha256"] + "\n").encode("utf-8"))
    return h.hexdigest().upper()

tracked = subprocess.check_output(["git", "ls-files", "-z", "--", *PROTECTED_REPOSITORY_SCOPES], cwd=ROOT)
repo_rows = []
for raw in tracked.split(b"\0"):
    if not raw:
        continue
    rel = raw.decode("utf-8").replace("\\", "/")
    if rel.startswith("research/icsec2026/cleanup_freeze_20260902/"):
        continue
    if rel in EXCLUDED_MUTABLE_CONTROL_PATHS:
        continue
    path = ROOT / rel
    if not path.is_file():
        raise FileNotFoundError(rel)
    repo_rows.append({"scope": "repository", "path": rel, "bytes": path.stat().st_size, "sha256": sha256(path)})
repo_rows.sort(key=lambda x: x["path"])

with (OUT / "PROTECTED_REPOSITORY_FILES.csv").open("w", encoding="utf-8", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=["scope", "path", "bytes", "sha256"])
    writer.writeheader()
    writer.writerows(repo_rows)

backup_rows = []
backup_summary = []
for root_text in EXTERNAL_BACKUPS:
    backup_root = Path(root_text)
    if not backup_root.is_dir():
        raise FileNotFoundError(root_text)
    current = []
    for path in sorted((p for p in backup_root.rglob("*") if p.is_file()), key=lambda p: p.as_posix().lower()):
        rel = path.relative_to(backup_root).as_posix()
        row = {"scope": root_text, "path": rel, "bytes": path.stat().st_size, "sha256": sha256(path)}
        current.append(row)
        backup_rows.append(row)
    backup_summary.append({"root": root_text, "files": len(current), "bytes": sum(x["bytes"] for x in current), "tree_sha256": tree_digest(current)})

with (OUT / "PROTECTED_EXTERNAL_BACKUP_FILES.csv").open("w", encoding="utf-8", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=["scope", "path", "bytes", "sha256"])
    writer.writeheader()
    writer.writerows(backup_rows)

head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
origin = subprocess.check_output(["git", "rev-parse", f"origin/{BRANCH}"], cwd=ROOT, text=True).strip()
status = subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=ROOT, text=True)
pdf_hash = sha256(FINAL_PDF)
if pdf_hash != FINAL_PDF_SHA256:
    raise ValueError(f"FINAL_PASS PDF hash mismatch: {pdf_hash}")

state = {
    "schema": "icsec-cleanup-protection-freeze-v1",
    "recorded_utc": datetime.now(timezone.utc).isoformat(),
    "branch": BRANCH,
    "freeze_start_commit": FREEZE_START_COMMIT,
    "head_observed_while_generating": head,
    "origin_branch_observed": origin,
    "origin_synchronized_at_freeze_start": head == origin == FREEZE_START_COMMIT,
    "working_tree_at_freeze_start": "CLEAN",
    "generation_worktree_note": "Only this new cleanup-freeze directory may be untracked while the manifest is generated.",
    "frozen_baseline": {
        "main": "8a47d070c549274c59cdbde2495afa8d353a93b3",
        "origin_main": "8a47d070c549274c59cdbde2495afa8d353a93b3",
        "tag_icsec_2026_evaluated_state": "8a47d070c549274c59cdbde2495afa8d353a93b3",
    },
    "final_manuscript": {
        "pdf": FINAL_PDF.relative_to(ROOT).as_posix(),
        "pdf_sha256": pdf_hash,
        "page_count": 5,
        "final_pass_source_commit": "21129b1795102574dceb023f984c115630b18020",
        "paths": MANUSCRIPT_PATHS,
    },
    "evidence_packages_referenced_by_manuscript": EVIDENCE_PACKAGES,
    "provenance_and_table_generation_dependencies": PROVENANCE_TABLE_DEPENDENCIES,
    "evaluated_source_revisions": {
        "primary_extension_acquisition_commit": "cfd4b1b59d5018f498e5cc083ab27e1d230ae85d",
        "payload_link_controller_blob": "e2b6c9e9bb4af62afa32daa455479575eebff19a",
        "payload_link_task_blob": "a76804eb567689588bc3b1459df9a9352ec0d4f4",
    },
    "protected_repository_scopes": PROTECTED_REPOSITORY_SCOPES,
    "excluded_mutable_control_paths": sorted(EXCLUDED_MUTABLE_CONTROL_PATHS),
    "protected_repository_files": len(repo_rows),
    "protected_repository_bytes": sum(x["bytes"] for x in repo_rows),
    "protected_repository_tree_sha256": tree_digest(repo_rows),
    "external_verified_backups": backup_summary,
    "protected_external_backup_files": len(backup_rows),
    "protected_external_backup_bytes": sum(x["bytes"] for x in backup_rows),
    "protected_external_backup_tree_sha256": tree_digest(backup_rows),
    "cleanup_rule": "Repository cleanup may not modify the byte content of any listed protected file. Relocation requires a pre/post SHA-256 match and an updated path map; deletion requires explicit Research Director authorization.",
    "generation_status_porcelain": status,
}
(OUT / "FREEZE_STATE.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "repository_files": len(repo_rows),
    "repository_tree_sha256": state["protected_repository_tree_sha256"],
    "external_backup_files": len(backup_rows),
    "external_backup_tree_sha256": state["protected_external_backup_tree_sha256"],
    "final_pdf_sha256": pdf_hash,
}, indent=2))
