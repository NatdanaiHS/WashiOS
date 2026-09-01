import csv
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CLEANUP = Path(__file__).resolve().parent
FREEZE = ROOT / "research/icsec2026/cleanup_freeze_20260902"
BRANCH = "experiment/icsec-extension-20260830"
EXPECTED_HEAD = "79a7fcbd3ec760621bde11670b660d6300466766"

MOVES = [
    ("research/icsec2026/extension/final_pass_submission_20260902", "research/icsec2026/submission", "MOVE", "authorized canonical submission package"),
    ("research/icsec2026/manuscript", "research/icsec2026/archive/manuscripts/evaluated_baseline_20260830", "ARCHIVE", "authorized evaluated-baseline manuscript archive"),
    ("research/icsec2026/extension/manuscript_candidate_f411_20260902", "research/icsec2026/archive/manuscripts/f411_candidate_20260902", "ARCHIVE", "authorized historical F411 candidate archive"),
    ("research/icsec2026/extension/manuscript_candidate_f411_20260902_corrected", "research/icsec2026/archive/manuscripts/f411_candidate_corrected_20260902", "ARCHIVE", "authorized corrected F411 candidate archive"),
    ("research/icsec2026/extension/manuscript", "research/icsec2026/archive/manuscripts/pre_final_active_20260902", "ARCHIVE", "authorized pre-FINAL active manuscript archive"),
    ("research/icsec2026/extension/submission_candidate_20260902", "research/icsec2026/archive/manuscripts/submission_candidate_20260902", "ARCHIVE", "authorized submission-candidate archive"),
    ("research/icsec2026/extension/validate_f411_claim_correction.py", "research/icsec2026/archive/manuscripts/tooling/validate_f411_claim_correction.py", "ARCHIVE", "authorized path-specific historical validator archive"),
]

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()

def nul_list(*args):
    data = subprocess.check_output(["git", *args, "-z"], cwd=ROOT)
    return [x.decode("utf-8").replace("\\", "/") for x in data.split(b"\0") if x]

def verify_rows(csv_path: Path, external: bool):
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig", newline="")))
    issues = []
    for row in rows:
        path = (Path(row["scope"]) / row["path"]) if external else (ROOT / row["path"])
        if not path.is_file():
            issues.append({"path": str(path), "issue": "missing"})
        elif path.stat().st_size != int(row["bytes"]):
            issues.append({"path": str(path), "issue": "size"})
        elif sha256(path) != row["sha256"]:
            issues.append({"path": str(path), "issue": "sha256"})
    return rows, issues

branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
origin = subprocess.check_output(["git", "rev-parse", f"origin/{BRANCH}"], cwd=ROOT, text=True).strip()
status_lines = [x for x in subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=ROOT, text=True).splitlines() if x]
allowed_status = [" M research/icsec2026/NEXT_TASK.md", "?? research/icsec2026/cleanup/"]
if branch != BRANCH or head != EXPECTED_HEAD or origin != EXPECTED_HEAD or status_lines != allowed_status:
    raise RuntimeError({"branch": branch, "head": head, "origin": origin, "status": status_lines})

repo_rows, repo_issues = verify_rows(FREEZE / "PROTECTED_REPOSITORY_FILES.csv", False)
external_rows, external_issues = verify_rows(FREEZE / "PROTECTED_EXTERNAL_BACKUP_FILES.csv", True)
freeze_rows = list(csv.DictReader((FREEZE / "FREEZE_PACKAGE_SHA256SUMS.csv").open(encoding="utf-8-sig", newline="")))
freeze_issues = []
for row in freeze_rows:
    path = FREEZE / row["path"]
    if not path.is_file() or path.stat().st_size != int(row["bytes"]) or sha256(path) != row["sha256"]:
        freeze_issues.append({"path": str(path), "issue": "missing/size/sha256"})

prevalidation = {
    "schema": "icsec-pre-cleanup-validation-v1",
    "recorded_utc": datetime.now(timezone.utc).isoformat(),
    "branch": branch,
    "head": head,
    "origin_branch": origin,
    "working_tree_at_milestone_start": [" M research/icsec2026/NEXT_TASK.md"],
    "working_tree_during_plan_generation": status_lines,
    "protected_repository_rows": len(repo_rows),
    "freeze_package_rows": len(freeze_rows),
    "external_backup_rows": len(external_rows),
    "issues": repo_issues + freeze_issues + external_issues,
}
prevalidation["status"] = "PASS" if not prevalidation["issues"] else "FAIL"
(CLEANUP / "PRE_CLEANUP_VALIDATION.json").write_text(json.dumps(prevalidation, indent=2) + "\n", encoding="utf-8")
if prevalidation["status"] != "PASS":
    raise RuntimeError(prevalidation)

protected = {row["path"] for row in repo_rows}
tracked = set(nul_list("ls-files", "--cached"))
untracked = set(nul_list("ls-files", "--others", "--exclude-standard"))
ignored = set(nul_list("ls-files", "--others", "-i", "--exclude-standard"))
all_paths = sorted(tracked | untracked | ignored)

for old, new, _, _ in MOVES:
    if not (ROOT / old).exists():
        raise FileNotFoundError(old)
    if (ROOT / new).exists():
        raise FileExistsError(new)

hash_cache = {}
for rel in all_paths:
    path = ROOT / rel
    if path.is_file():
        hash_cache[rel] = sha256(path)
hash_counts = Counter(hash_cache.values())

text_suffixes = {".py", ".json", ".md", ".tex", ".csv", ".txt", ".patch", ".toml", ".ini", ".yaml", ".yml", ".ps1"}
reference_text = []
for rel in sorted(tracked):
    path = ROOT / rel
    if path.is_file() and path.suffix.lower() in text_suffixes and path.stat().st_size <= 2_000_000:
        try:
            reference_text.append(path.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            pass
corpus = "\n".join(reference_text)

inventory = []
for rel in all_paths:
    path = ROOT / rel
    if not path.is_file():
        continue
    classification = "KEEP"
    action = "KEEP"
    proposed = rel
    reason = "retained in place"
    move_root = None
    for old, new, category, why in MOVES:
        if rel == old or rel.startswith(old + "/"):
            suffix = rel[len(old):].lstrip("/")
            proposed = new + (("/" + suffix) if suffix else "")
            classification = category
            action = category
            reason = why
            move_root = old
            break
    if action == "KEEP" and rel in protected:
        classification = "PROTECTED"
        reason = "immutable protected content retained at current path"
    elif action == "KEEP" and rel in ignored:
        classification = "GENERATED"
        reason = "ignored/generated file retained; deletion not authorized"
    reference_hit = False
    reference_basis = ""
    if move_root:
        reference_hit = move_root in corpus or rel in corpus
        reference_basis = move_root if reference_hit else "none found in tracked text manifests/scripts/build/docs"
    inventory.append({
        "current_path": rel,
        "proposed_path": proposed,
        "action": action,
        "classification": classification,
        "tracking": "tracked" if rel in tracked else ("ignored" if rel in ignored else "untracked"),
        "bytes": path.stat().st_size,
        "sha256": hash_cache[rel],
        "exact_hash_copy_count": hash_counts[hash_cache[rel]],
        "protected": str(rel in protected).lower(),
        "referenced_by_build_script_manifest": str(reference_hit).lower(),
        "reference_basis": reference_basis,
        "reason": reason,
    })

fields = ["current_path", "proposed_path", "action", "classification", "tracking", "bytes", "sha256", "exact_hash_copy_count", "protected", "referenced_by_build_script_manifest", "reference_basis", "reason"]
for name in ("PRE_CLEANUP_INVENTORY.csv", "CLEANUP_PLAN.csv"):
    with (CLEANUP / name).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(inventory)

summary = {
    "files": len(inventory),
    "classifications": dict(Counter(x["classification"] for x in inventory)),
    "planned_move_files": sum(x["action"] in {"MOVE", "ARCHIVE"} for x in inventory),
    "planned_deletions": sum(x["action"] == "DELETE_EXACT_DUPLICATE" for x in inventory),
    "protected_planned_moves": sum(x["action"] in {"MOVE", "ARCHIVE"} and x["protected"] == "true" for x in inventory),
    "duplicate_hash_groups": sum(n > 1 for n in hash_counts.values()),
}
(CLEANUP / "PRE_CLEANUP_INVENTORY_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"prevalidation": prevalidation, "inventory": summary}, indent=2))
