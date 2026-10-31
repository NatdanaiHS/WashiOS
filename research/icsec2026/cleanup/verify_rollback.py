import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
FREEZE = ROOT / "research/icsec2026/cleanup_freeze_20260902"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()

issues = []
repo = list(csv.DictReader((FREEZE / "PROTECTED_REPOSITORY_FILES.csv").open(encoding="utf-8-sig", newline="")))
for row in repo:
    path = ROOT / row["path"]
    if not path.is_file() or path.stat().st_size != int(row["bytes"]) or sha256(path) != row["sha256"]:
        issues.append({"scope": "repository", "path": row["path"], "issue": "missing/size/sha256"})

freeze_rows = list(csv.DictReader((FREEZE / "FREEZE_PACKAGE_SHA256SUMS.csv").open(encoding="utf-8-sig", newline="")))
for row in freeze_rows:
    path = FREEZE / row["path"]
    if not path.is_file() or path.stat().st_size != int(row["bytes"]) or sha256(path) != row["sha256"]:
        issues.append({"scope": "freeze", "path": row["path"], "issue": "missing/size/sha256"})

external = list(csv.DictReader((FREEZE / "PROTECTED_EXTERNAL_BACKUP_FILES.csv").open(encoding="utf-8-sig", newline="")))
for row in external:
    path = Path(row["scope"]) / row["path"]
    if not path.is_file() or path.stat().st_size != int(row["bytes"]) or sha256(path) != row["sha256"]:
        issues.append({"scope": row["scope"], "path": row["path"], "issue": "missing/size/sha256"})

pdf = ROOT / "research/icsec2026/extension/final_pass_submission_20260902/main.pdf"
pdf_hash = sha256(pdf)
if pdf_hash != "99E4180F4B172C1CC7BABFCF8BE92FCC5442B3868F7AAD1D32A13779849E765D":
    issues.append({"scope": "final_pdf", "path": str(pdf), "issue": pdf_hash})

result = {
    "schema": "icsec-cleanup-rollback-validation-v1",
    "status": "PASS" if not issues else "FAIL",
    "protected_repository_rows": len(repo),
    "freeze_package_rows": len(freeze_rows),
    "external_backup_rows": len(external),
    "final_pdf_sha256": pdf_hash,
    "issues": issues,
}
(HERE / "POST_ROLLBACK_VALIDATION.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
raise SystemExit(0 if not issues else 1)
