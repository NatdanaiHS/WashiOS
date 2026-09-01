import hashlib
import csv
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
MANUSCRIPT = ROOT / "research/icsec2026/extension/manuscript"
PRIMARY = ROOT / "research/icsec2026/extension/evidence/primary_20260830_seed20260830_b5"

checks = []
def check(name, condition, detail):
    checks.append({"name": name, "pass": bool(condition), "detail": detail})

nom = json.loads((PRIMARY / "nominal_validation_002.json").read_text(encoding="utf-8"))
check("extended_nominal_valid", nom["valid"] is True and nom["invalid_reason"] == "", "valid and no invalid reason")
check("extended_nominal_duration", nom["requested_s"] == 605.0 and nom["duration_s"] == 605.0, "requested=observed=605.0 s")
check("extended_nominal_records", nom["status_count"] == 121 and len(nom["status_records"]) == 121, "121 status records")
check("extended_nominal_online", all(r["state"] == "ONLINE" for r in nom["status_records"]), "all records ONLINE")
check("extended_nominal_ok", nom["status_records"][0]["ok"] == 1760 and nom["status_records"][-1]["ok"] == 2960, "ok 1760--2960")
check("extended_nominal_zero_deltas", all(v == 0 for v in nom["counter_deltas"].values()), str(nom["counter_deltas"]))
check("extended_nominal_no_prohibited", nom["prohibited_markers"] == [], "empty prohibited-marker list")

bad = json.loads((PRIMARY / "bad_crc_results.json").read_text(encoding="utf-8"))
short, sustained = bad
sm = [x["marker"] for x in short["observed_markers"]]
lm = [x["marker"] for x in sustained["observed_markers"]]
check("bad_crc_both_valid", len(bad) == 2 and all(x["valid"] and not x["invalid_reason"] for x in bad), "SHORT and SUSTAINED retained")
check("bad_crc_short_order", ["reason=CRC", "consecutive=1"] == [next(s for s in sm if "reason=CRC" in s).split("PAYLOAD_REJECT ")[1], next(s for s in sm if "TIMEOUT" in s).split("PAYLOAD_TIMEOUT ")[1]], "CRC reject precedes timeout; no OFFLINE")
check("bad_crc_sustained_order", next(i for i,s in enumerate(lm) if "reason=CRC" in s) < next(i for i,s in enumerate(lm) if "consecutive=1" in s) < next(i for i,s in enumerate(lm) if "consecutive=2" in s) < next(i for i,s in enumerate(lm) if "OFFLINE consecutive=3" in s), "raw marker order CRC, 1, 2, OFFLINE 3")
check("bad_crc_restore_after_offline", sustained["restore_confirmation_host_time"] > sustained["observed_markers"][-1]["host_time"], "uses raw/control-flow order, not derived offline_before_restore")

tex = (MANUSCRIPT / "main.tex").read_text(encoding="utf-8")
required = ["separate 605-s nominal observation", "121 ONLINE records", "1760 to 2960", "OFFLINE marker at count three", "two physical F411 pairs under the same F411 configuration"]
for text in required:
    check("manuscript_contains_" + re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_"), text in tex, text)
for forbidden in ["Cross-Configuration", "two configurations", "offline_before_restore"]:
    check("claim_boundary_absent_" + re.sub(r"[^a-z0-9]+", "_", forbidden.lower()).strip("_"), forbidden not in tex, forbidden)
check("anonymous_author", "\\author{}" in tex and "pdfauthor={}" in tex, "empty author fields")
check("anonymous_no_repository_url", not re.search(r"github|gitlab|C:\\\\|WashiOS", tex, re.I), "no identifying repository/path")

bib = (MANUSCRIPT / "references.bib").read_text(encoding="utf-8")
dois = ["10.1109/32.44380", "10.1109/EDCC.2015.14", "10.3390/s22041360", "10.3390/s24123733", "10.1016/j.actaastro.2018.11.011", "10.1590/jatm.v17.1379"]
check("six_verified_dois_present", all(d.lower() in bib.lower() for d in dois) and bib.count("@") == 6, "six DOI-verified references")

main = subprocess.check_output(["git", "rev-parse", "main"], cwd=ROOT, text=True).strip()
origin_main = subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip()
tag = subprocess.check_output(["git", "rev-parse", "icsec-2026-evaluated-state"], cwd=ROOT, text=True).strip()
frozen = "8a47d070c549274c59cdbde2495afa8d353a93b3"
check("frozen_refs", main == origin_main == tag == frozen, f"main={main}; origin/main={origin_main}; tag={tag}")
frozen_pdf = ROOT / "research/icsec2026/manuscript/main.pdf"
check("frozen_manuscript_pdf", hashlib.sha256(frozen_pdf.read_bytes()).hexdigest().upper() == "992A1C9AA41F4295BF7F97CA081D79A7DE2ABBB4B419B2A0B82144C1B50928DF", "immutable evaluated manuscript")

for rel, expected in {
    "nominal_validation_002.json": "3119D5994378E00C7ACE945B0FCB96CBA28C5855CDFEA445CD26570FD52A74FD",
    "bad_crc_results.json": "F6332F913FFA91432032AA1E5582AE78378F8880FC22D11B921C5B793ADC4E90",
    "FINAL_MANIFEST.json": "D8424545495CCF2EBA2BF87BE5B68CDA79D3AA41239217140F54D20BD0DCE91E",
}.items():
    actual = hashlib.sha256((PRIMARY / rel).read_bytes()).hexdigest().upper()
    check("frozen_hash_" + rel, actual == expected, actual)

def verify_pair_inventory(label, source, backup, inventory):
    rows = list(csv.DictReader((source / inventory).open(encoding="utf-8-sig", newline="")))
    issues = []
    for row in rows:
        for root in (source, backup):
            f = root / row["relative_path"]
            if not f.is_file() or f.stat().st_size != int(row["size_bytes"]) or hashlib.sha256(f.read_bytes()).hexdigest().upper() != row["sha256"].upper():
                issues.append(f"{root}:{row['relative_path']}")
    check(label, not issues, f"{len(rows)}/{len(rows)} rows in source and backup; issues={len(issues)}")

backup_root = Path("C:/WashiOS-extension-backup")
p1 = ROOT / "research/icsec2026/extension/evidence/f411_pair1_campaign_20260901_seed20260901_b3"
p2 = ROOT / "research/icsec2026/extension/evidence/f411_pair2_campaign_20260901_seed20260901_b3"
verify_pair_inventory("pair1_source_backup_inventory", p1, backup_root / p1.name, "F411_PAIR1_CAMPAIGN_SHA256SUMS.csv")
verify_pair_inventory("pair2_source_backup_inventory", p2, backup_root / p2.name, "F411_PAIR2_CAMPAIGN_SHA256SUMS.csv")

candidate = ROOT / "research/icsec2026/extension/submission_candidate_20260902"
for name in ("main.tex", "references.bib", "main.pdf"):
    check("candidate_matches_active_" + name, (candidate / name).read_bytes() == (MANUSCRIPT / name).read_bytes(), name)
try:
    from pypdf import PdfReader
    check("candidate_page_count", len(PdfReader(candidate / "main.pdf").pages) == 5, "5 pages within ICSEC 4--6 page requirement")
except Exception as exc:
    check("candidate_page_count", False, repr(exc))

result = {"schema": "icsec-submission-readiness-validation-v1", "status": "PASS" if all(x["pass"] for x in checks) else "FAIL", "checks": checks}
(OUT / "FINAL_VALIDATION.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
raise SystemExit(0 if result["status"] == "PASS" else 1)
