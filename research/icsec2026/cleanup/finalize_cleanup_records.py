import csv
import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()

plan = list(csv.DictReader((HERE / "CLEANUP_PLAN.csv").open(encoding="utf-8-sig", newline="")))
moved = [row for row in plan if row["action"] in {"MOVE", "ARCHIVE"}]
relocations = []
for row in moved:
    old = ROOT / row["current_path"]
    new = ROOT / row["proposed_path"]
    if old.exists():
        raise RuntimeError(f"old path still exists: {row['current_path']}")
    if not new.is_file():
        raise FileNotFoundError(row["proposed_path"])
    post_hash = sha256(new)
    if new.stat().st_size != int(row["bytes"]) or post_hash != row["sha256"]:
        raise RuntimeError(f"post-move mismatch: {row['proposed_path']}")
    relocations.append({
        "old_path": row["current_path"],
        "new_path": row["proposed_path"],
        "action": row["action"],
        "bytes": row["bytes"],
        "pre_sha256": row["sha256"],
        "post_sha256": post_hash,
        "protected": row["protected"],
        "reason": row["reason"],
    })

with (HERE / "PATH_RELOCATION.csv").open("w", encoding="utf-8", newline="") as stream:
    fields = ["old_path", "new_path", "action", "bytes", "pre_sha256", "post_sha256", "protected", "reason"]
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(relocations)

tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).split(b"\0")
tracked_paths = [x.decode("utf-8").replace("\\", "/") for x in tracked if x]
untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=ROOT).split(b"\0")
untracked_paths = [x.decode("utf-8").replace("\\", "/") for x in untracked if x]
ignored = subprocess.check_output(["git", "ls-files", "--others", "-i", "--exclude-standard", "-z"], cwd=ROOT).split(b"\0")
ignored_paths = [x.decode("utf-8").replace("\\", "/") for x in ignored if x]

inventory = []
for tracking, paths in (("tracked", tracked_paths), ("untracked", untracked_paths), ("ignored", ignored_paths)):
    for rel in paths:
        path = ROOT / rel
        if path.is_file():
            inventory.append({"path": rel, "tracking": tracking, "bytes": path.stat().st_size, "sha256": sha256(path)})
inventory.sort(key=lambda x: x["path"])
with (HERE / "POST_CLEANUP_INVENTORY.csv").open("w", encoding="utf-8", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=["path", "tracking", "bytes", "sha256"])
    writer.writeheader()
    writer.writerows(inventory)

manuscript_rows = [x for x in inventory if x["path"].startswith(("research/icsec2026/submission/", "research/icsec2026/archive/manuscripts/", "research/icsec2026/extension/analysis/"))]
groups = defaultdict(list)
for row in manuscript_rows:
    groups[row["sha256"]].append(row)
duplicate_rows = []
for digest, rows in sorted(groups.items()):
    if len(rows) < 2:
        continue
    group_id = digest[:16]
    for row in sorted(rows, key=lambda x: x["path"]):
        if row["path"].startswith("research/icsec2026/submission/"):
            disposition = "CANONICAL_ACTIVE"
        elif row["path"].startswith("research/icsec2026/archive/manuscripts/"):
            disposition = "ARCHIVED_HISTORY"
        else:
            disposition = "IMMUTABLE_PROVENANCE_SNAPSHOT"
        duplicate_rows.append({
            "group_id": group_id,
            "sha256": digest,
            "bytes": row["bytes"],
            "path": row["path"],
            "disposition": disposition,
            "action": "NO_DELETE",
            "reason": "exact SHA-256 duplicate retained for provenance; deletion not authorized",
        })
with (HERE / "DUPLICATE_DISPOSITION.csv").open("w", encoding="utf-8", newline="") as stream:
    fields = ["group_id", "sha256", "bytes", "path", "disposition", "action", "reason"]
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(duplicate_rows)

summary = {
    "relocation_rows": len(relocations),
    "protected_relocation_rows": sum(x["protected"] == "true" for x in relocations),
    "post_inventory_rows": len(inventory),
    "duplicate_groups": len({x["group_id"] for x in duplicate_rows}),
    "duplicate_rows": len(duplicate_rows),
    "deletions": 0,
}
(HERE / "RELOCATION_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2))
