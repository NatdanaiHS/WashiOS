import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()

issues = []
repo_rows = list(csv.DictReader((HERE / "PROTECTED_REPOSITORY_FILES.csv").open(encoding="utf-8-sig", newline="")))
for row in repo_rows:
    path = ROOT / row["path"]
    if not path.is_file():
        issues.append({"scope": "repository", "path": row["path"], "issue": "missing"})
    elif path.stat().st_size != int(row["bytes"]):
        issues.append({"scope": "repository", "path": row["path"], "issue": "size"})
    elif digest(path) != row["sha256"]:
        issues.append({"scope": "repository", "path": row["path"], "issue": "sha256"})

backup_rows = list(csv.DictReader((HERE / "PROTECTED_EXTERNAL_BACKUP_FILES.csv").open(encoding="utf-8-sig", newline="")))
for row in backup_rows:
    path = Path(row["scope"]) / row["path"]
    if not path.is_file():
        issues.append({"scope": row["scope"], "path": row["path"], "issue": "missing"})
    elif path.stat().st_size != int(row["bytes"]):
        issues.append({"scope": row["scope"], "path": row["path"], "issue": "size"})
    elif digest(path) != row["sha256"]:
        issues.append({"scope": row["scope"], "path": row["path"], "issue": "sha256"})

state = json.loads((HERE / "FREEZE_STATE.json").read_text(encoding="utf-8"))
pdf = ROOT / state["final_manuscript"]["pdf"]
if digest(pdf) != state["final_manuscript"]["pdf_sha256"]:
    issues.append({"scope": "final_manuscript", "path": str(pdf), "issue": "sha256"})

result = {
    "schema": "icsec-cleanup-protection-validation-v1",
    "status": "PASS" if not issues else "FAIL",
    "repository_rows_checked": len(repo_rows),
    "external_backup_rows_checked": len(backup_rows),
    "final_pdf_sha256": digest(pdf),
    "issues": issues,
}
(HERE / "VALIDATION.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
raise SystemExit(0 if not issues else 1)
