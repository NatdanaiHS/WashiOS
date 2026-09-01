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
relocations = list(csv.DictReader((HERE / "PATH_RELOCATION.csv").open(encoding="utf-8-sig", newline="")))
maps = {}
for row in relocations:
    if row["old_path"] in maps:
        issues.append({"check": "path_map", "path": row["old_path"], "issue": "duplicate old path"})
    maps[row["old_path"]] = row

protected = list(csv.DictReader((FREEZE / "PROTECTED_REPOSITORY_FILES.csv").open(encoding="utf-8-sig", newline="")))
mapped_protected = 0
for row in protected:
    mapped = maps.get(row["path"])
    path = ROOT / (mapped["new_path"] if mapped else row["path"])
    if mapped:
        mapped_protected += 1
    if not path.is_file():
        issues.append({"check": "protected_repository", "path": str(path), "issue": "missing"})
    elif path.stat().st_size != int(row["bytes"]):
        issues.append({"check": "protected_repository", "path": str(path), "issue": "size"})
    elif sha256(path) != row["sha256"]:
        issues.append({"check": "protected_repository", "path": str(path), "issue": "sha256"})

external = list(csv.DictReader((FREEZE / "PROTECTED_EXTERNAL_BACKUP_FILES.csv").open(encoding="utf-8-sig", newline="")))
for row in external:
    path = Path(row["scope"]) / row["path"]
    if not path.is_file() or path.stat().st_size != int(row["bytes"]) or sha256(path) != row["sha256"]:
        issues.append({"check": "external_backup", "path": str(path), "issue": "missing/size/sha256"})

freeze_rows = list(csv.DictReader((FREEZE / "FREEZE_PACKAGE_SHA256SUMS.csv").open(encoding="utf-8-sig", newline="")))
for row in freeze_rows:
    path = FREEZE / row["path"]
    if not path.is_file() or path.stat().st_size != int(row["bytes"]) or sha256(path) != row["sha256"]:
        issues.append({"check": "freeze_package", "path": str(path), "issue": "missing/size/sha256"})

submission = ROOT / "research/icsec2026/submission"
package_rows = list(csv.DictReader((submission / "PACKAGE_SHA256SUMS.csv").open(encoding="utf-8-sig", newline="")))
for row in package_rows:
    path = submission / row["path"]
    if not path.is_file() or path.stat().st_size != int(row["bytes"]) or sha256(path) != row["sha256"]:
        issues.append({"check": "canonical_package", "path": str(path), "issue": "missing/size/sha256"})
pdf_hash = sha256(submission / "main.pdf")
if pdf_hash != "99E4180F4B172C1CC7BABFCF8BE92FCC5442B3868F7AAD1D32A13779849E765D":
    issues.append({"check": "canonical_pdf", "path": str(submission / "main.pdf"), "issue": pdf_hash})

table_prov = json.loads((ROOT / "research/icsec2026/paper/tables/TABLE_PROVENANCE.json").read_text(encoding="utf-8"))
for section in ("inputs", "outputs"):
    for name, record in table_prov[section].items():
        path = ROOT / record["path"]
        if not path.is_file() or sha256(path) != record["sha256"]:
            issues.append({"check": "primary_table_provenance", "path": record["path"], "issue": name})
generator = table_prov["generator"]
if sha256(ROOT / generator["path"]) != generator["sha256"]:
    issues.append({"check": "primary_table_generator", "path": generator["path"], "issue": "sha256"})

f411_prov = json.loads((ROOT / "research/icsec2026/extension/analysis/f411_cross_pair_synthesis_20260902_r4/PROVENANCE.json").read_text(encoding="utf-8"))
if sha256(ROOT / "research/icsec2026/extension/generate_f411_cross_pair_synthesis.py") != f411_prov["generator_sha256"]:
    issues.append({"check": "f411_generator", "path": f411_prov["generated_by"], "issue": "sha256"})
for name, expected in f411_prov["outputs"].items():
    path = ROOT / "research/icsec2026/extension/analysis/f411_cross_pair_synthesis_20260902_r4" / name
    if not path.is_file() or sha256(path) != expected:
        issues.append({"check": "f411_output", "path": str(path), "issue": "sha256"})

required_validations = [
    ("research/icsec2026/runs/full_20260830_seed20260830_n30/validation.json", "valid"),
    ("research/icsec2026/runs/n0_pre_20260830_0205/validation.json", "valid"),
    ("research/icsec2026/runs/n0_post_20260830_0224/validation.json", "valid"),
    ("research/icsec2026/extension/evidence/primary_20260830_seed20260830_b5/final_validation.json", "valid"),
    ("research/icsec2026/extension/evidence/f411_pair1_campaign_20260901_seed20260901_b3/final_validation.json", "campaign_valid"),
    ("research/icsec2026/extension/evidence/f411_pair2_campaign_20260901_seed20260901_b3/final_validation.json", "valid"),
]
for rel, field in required_validations:
    data = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    if data.get(field) is not True:
        issues.append({"check": "scientific_validation", "path": rel, "issue": f"{field} != true"})

result = {
    "schema": "icsec-post-cleanup-relocation-validation-v1",
    "status": "PASS" if not issues else "FAIL",
    "protected_repository_rows": len(protected),
    "mapped_protected_rows": mapped_protected,
    "unchanged_protected_rows": len(protected) - mapped_protected,
    "relocation_rows": len(relocations),
    "external_backup_rows": len(external),
    "freeze_package_rows": len(freeze_rows),
    "canonical_package_rows": len(package_rows),
    "canonical_pdf_sha256": pdf_hash,
    "issues": issues,
}
(HERE / "POST_CLEANUP_VALIDATION.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
raise SystemExit(0 if not issues else 1)
