from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[3]
SUBMISSION = ROOT / "research" / "icsec2026" / "submission"
MANUSCRIPT = (SUBMISSION / "main.tex").read_text(encoding="utf-8")
BIBLIOGRAPHY = (SUBMISSION / "references.bib").read_text(encoding="utf-8")


def load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def sha256(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest().upper()


assert sha256("research/icsec2026/POSITIONING_LOCK.md") == (
    "0D4AE41D32A70EB334856341094D598DE1DF7F7A2E3CE95BF03BDD6E512CE1CE"
)
assert sha256(
    "research/icsec2026/extension/evidence/primary_20260830_seed20260830_b5/"
    "nominal_validation_002.json"
) == "3119D5994378E00C7ACE945B0FCB96CBA28C5855CDFEA445CD26570FD52A74FD"
assert sha256(
    "research/icsec2026/extension/evidence/primary_20260830_seed20260830_b5/"
    "bad_crc_results.json"
) == "F6332F913FFA91432032AA1E5582AE78378F8880FC22D11B921C5B793ADC4E90"

summary = load("research/icsec2026/runs/full_20260830_seed20260830_n30/summary.json")
validation = load("research/icsec2026/runs/full_20260830_seed20260830_n30/validation.json")
assert validation["valid"] and validation["issues"] == []
assert (validation["plan_rows"], validation["result_rows"], validation["raw_files_checked"]) == (
    90,
    90,
    180,
)

expected = {
    "SILENT": ((383.0, 288.75, 485.0, 196.25, 125.0, 578.0), (297.0, 144.25, 375.0, 230.75, 78.0, 516.0)),
    "BAD_CRC": ((359.5, 171.25, 464.25, 293.0, 78.0, 531.0), (359.0, 113.75, 417.25, 303.5, 47.0, 531.0)),
    "DELAYED": ((406.0, 297.0, 512.0, 215.0, 156.0, 610.0), (296.5, 187.25, 425.5, 238.25, 94.0, 531.0)),
}
for mode, (det_expected, rec_expected) in expected.items():
    item = summary["faults"][mode]
    assert (
        item["planned_trials"],
        item["valid_trials"],
        item["invalid_trials"],
        item["activation_confirmed_trials"],
        item["restoration_confirmed_trials"],
        item["offline_observed_trials"],
        item["restart_marker_observed_trials"],
    ) == (30, 30, 0, 30, 30, 30, 0)
    assert (item["detection"]["successes"], item["detection"]["trials"], item["detection"]["proportion"]) == (30, 30, 1.0)
    assert (item["recovery"]["successes"], item["recovery"]["trials"], item["recovery"]["proportion"]) == (30, 30, 1.0)
    det = item["detection_latency"]
    rec = item["recovery_latency"]
    assert (det["median_ms"], det["q1_ms"], det["q3_ms"], det["iqr_ms"], det["min_ms"], det["max_ms"]) == det_expected
    assert (rec["median_ms"], rec["q1_ms"], rec["q3_ms"], rec["iqr_ms"], rec["min_ms"], rec["max_ms"]) == rec_expected

for name, duration, count, first, last in (
    ("n0_pre_20260830_0205", 65.0, 13, 1835, 1955),
    ("n0_post_20260830_0224", 65.0, 13, 3049, 3169),
):
    n0 = load(f"research/icsec2026/runs/{name}/validation.json")
    assert n0["valid"] and n0["duration_s"] == duration and n0["status_count"] == count
    assert (n0["status_records"][0]["ok"], n0["status_records"][-1]["ok"]) == (first, last)
    assert n0["counter_deltas"] == {"crc": 0, "recovery": 0, "seq": 0, "timeout": 0}
    assert n0["prohibited_markers"] == []

nominal = load(
    "research/icsec2026/extension/evidence/primary_20260830_seed20260830_b5/"
    "nominal_validation_002.json"
)
assert nominal["valid"] and nominal["duration_s"] == 605.0 and nominal["status_count"] == 121
assert (nominal["status_records"][0]["ok"], nominal["status_records"][-1]["ok"]) == (1760, 2960)
assert {row["state"] for row in nominal["status_records"]} == {"ONLINE"}
assert nominal["counter_deltas"] == {"crc": 0, "recovery": 0, "seq": 0, "timeout": 0}
assert nominal["prohibited_markers"] == []

bad_crc = load(
    "research/icsec2026/extension/evidence/primary_20260830_seed20260830_b5/"
    "bad_crc_results.json"
)
by_exposure = {row["exposure"]: row for row in bad_crc}
assert set(by_exposure) == {"SHORT", "SUSTAINED"}
assert all(row["valid"] and not row["invalid_reason"] for row in bad_crc)
assert [row["marker"] for row in by_exposure["SHORT"]["observed_markers"]][-2:] == [
    "[OBC] PAYLOAD_REJECT reason=CRC",
    "[OBC] PAYLOAD_TIMEOUT consecutive=1",
]
assert [row["marker"] for row in by_exposure["SUSTAINED"]["observed_markers"]][-4:] == [
    "[OBC] PAYLOAD_REJECT reason=CRC",
    "[OBC] PAYLOAD_TIMEOUT consecutive=1",
    "[OBC] PAYLOAD_TIMEOUT consecutive=2",
    "[OBC] PAYLOAD_OFFLINE consecutive=3 heartbeat=OK watchdog=OK",
]

synthesis = (ROOT / "research/icsec2026/extension/analysis/f411_cross_pair_synthesis_20260902_r4/SYNTHESIS.md").read_text(encoding="utf-8")
for required in (
    "Pair-1 | 12/12 | 3/3 | 3/3 | 3/3 | 3/3",
    "Pair-2 | 12/12 | 3/3 | 3/3 | 3/3 | 3/3",
    "zero accepted mode-3 responses",
    "four Pair-1 rows and three Pair-2 rows",
    "timeout 24, sequence 24",
):
    assert required in synthesis

pdf = PdfReader(SUBMISSION / "main.pdf")
assert 4 <= len(pdf.pages) <= 6
text = "\n".join(page.extract_text() or "" for page in pdf.pages)
for required in (
    "Host orchestrator",
    "Eligible for detection scoring",
    "Eligible for recovery scoring",
    "Missing activation confirmation:",
    "detection and recovery unscored",
    "Activation confirmed; missing restoration confirmation:",
    "detection remains scoreable; recovery unscored",
):
    assert required in text
for required in (
    "causal eligibility boundary",
    "not an independent physical measurement of UART behavior",
    "without a verified total order",
    "temporally ambiguous",
    "detection unscored",
    "complete-trial validity indicator",
    r"V_i = A_i \land S_i \land \neg E_i",
):
    assert required in MANUSCRIPT
assert "(1)" in text
assert "references" in text.lower() and "[10]" in text
assert len(re.findall(r"^@\w+\{", BIBLIOGRAPHY, flags=re.MULTILINE)) == 10
for required in (
    "OpenAI ChatGPT",
    "OpenAI Codex",
    "Anthropic Claude",
    "No AI-generated data were used",
):
    assert required in MANUSCRIPT
assert not any(token in text.lower() for token in ("anonymous artifact", "anonymous repository", "state-of-the-art", "superior"))
assert not any(token in MANUSCRIPT for token in ("main_old", "main_new", "final2", "offline_before_restore"))
assert list(SUBMISSION.glob("main*.tex")) == [SUBMISSION / "main.tex"]
log_path = SUBMISSION / "build" / "main.log"
if log_path.is_file():
    log = log_path.read_text(encoding="utf-8", errors="replace").lower()
    assert "there were undefined references" not in log
    assert re.search(r"(?:citation|reference)[^\n]*undefined", log) is None

scorer_assertions = load(
    "research/icsec2026/synthetic_scorer_validation/automated_assertions.json"
)
assert scorer_assertions["overall_pass"]
assert scorer_assertions["assertions"] == {
    "all_expected_outcomes_matched": True,
    "all_original_sources_unchanged": True,
    "exactly_five_mutations": True,
}
pre_activation = load(
    "research/icsec2026/synthetic_scorer_validation/actual_outcomes.json"
)["detector_before_activation_confirmation"]
assert pre_activation["activation_confirmation"]["confirmed"]
assert pre_activation["detection"] == {
    "eligible": False,
    "event_id": None,
    "result": "UNSCORED",
}
assert pre_activation["diagnostic_codes"] == [
    "CROSS_CHANNEL_DETECTOR_ACTIVATION_ORDER_AMBIGUOUS",
    "DETECTION_UNSCORED_TEMPORAL_ORDER_AMBIGUOUS",
]

pdf_hash = sha256("research/icsec2026/submission/main.pdf")
recorded_pdf_hash = (SUBMISSION / "FINAL_PDF_SHA256.txt").read_text(encoding="ascii").split()[0]
assert recorded_pdf_hash == pdf_hash
with (SUBMISSION / "PACKAGE_SHA256SUMS.csv").open(encoding="utf-8-sig", newline="") as handle:
    package_rows = list(csv.DictReader(handle))
assert package_rows
for row in package_rows:
    artifact = SUBMISSION / row["path"]
    assert artifact.is_file()
    assert artifact.stat().st_size == int(row["bytes"])
    assert hashlib.sha256(artifact.read_bytes()).hexdigest().upper() == row["sha256"]

print("PASS: evidence values, denominators, hashes, boundaries, bibliography, PDF text, and 4-6 page count")
