#!/usr/bin/env python3
"""Does a PAYLOAD_STATUS report fall inside each primary-campaign interval? (assumption A7)

Read-only. The 180 raw logs of the primary campaign are gitignored and not in this checkout; they are in
the verified external backup recorded in extension/recovery/recovery_20260901/. Copy them (or only the
runs of interest, e.g. R085_P02 and R047_P02) into any directory laid out as <raw-root>/<run_id>/g431.log,
then run

    python3 research/icsec2026/draft-camera-ready/conformance/check_status_windows.py --raw-root <dir>

Every file is checked against the frozen inventory (runs/.../SHA256SUMS.csv) before use; a file whose
hash differs is reported and ignored. Interval endpoints are the frozen results.csv stamps (confirmation
anchor), so the result is directly comparable with check_frozen_traces.py. Under the draft model an
interval with no status report inside is bounded by the SLIP-0 bound and one with a status report by the
SLIP-60 bound.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_frozen_traces as cft  # noqa: E402

ROOT = cft.ROOT
PRIMARY = cft.PRIMARY
INVENTORY = PRIMARY / "SHA256SUMS.csv"
INVENTORY_PREFIX = "research/icsec2026/runs/full_20260830_seed20260830_n30/raw/"


def _stamp(text: str) -> float:
    return dt.datetime.fromisoformat(text).timestamp() * 1000.0


def load_inventory() -> dict[str, str]:
    out = {}
    with INVENTORY.open(encoding="utf-8", newline="") as handle:
        for row in csv.reader(handle):
            if len(row) >= 3 and row[2].startswith(INVENTORY_PREFIX):
                out[row[2][len(INVENTORY_PREFIX):]] = row[0].upper()
    return out


def status_stamps(log: Path) -> tuple[list[float], list[tuple[float, str]]]:
    """Host stamps (ms) of PAYLOAD_STATUS lines and of every complete line, stamped at their newline."""
    status, lines = [], []
    for t, line in cft._raw_lines(log):
        lines.append((t, line))
        if "PAYLOAD_STATUS" in line:
            status.append(t)
    return status, lines


def classify(start_ms: float, end_ms: float, status: list[float]) -> list[float]:
    """Offsets (ms after start) of the status reports that fall strictly inside [start, end]."""
    return [round(s - start_ms, 1) for s in status if start_ms < s < end_ms]


def analyse(raw_root: Path) -> dict:
    inventory = load_inventory()
    with (PRIMARY / "results.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    b0, b60 = cft.bounds(0), cft.bounds(cft.SLIP_MS)
    runs, missing, bad_hash = [], [], []
    for row in rows:
        rel = f"{row['run_id']}/g431.log"
        log = raw_root / rel
        if not log.exists():
            missing.append(row["run_id"])
            continue
        digest = hashlib.sha256(log.read_bytes()).hexdigest().upper()
        if digest != inventory.get(rel):
            bad_hash.append({"run_id": row["run_id"], "sha256": digest, "expected": inventory.get(rel)})
            continue
        status, lines = status_stamps(log)
        det0, det1 = _stamp(row["activation_host_time"]), _stamp(row["detection_host_time"])
        rec0, rec1 = _stamp(row["restore_confirmation_host_time"]), _stamp(row["recovery_host_time"])
        # anchor sanity: the frozen recovery stamp must be a PAYLOAD_RECOVERED line of this log
        anchor_ok = any(abs(t - rec1) < 0.001 and "PAYLOAD_RECOVERED" in l for t, l in lines)
        det_status, rec_status = classify(det0, det1, status), classify(rec0, rec1, status)
        rec, det = rec1 - rec0, det1 - det0
        runs.append({
            "run_id": row["run_id"], "mode": row["fault_mode"],
            "recovery_ms": round(rec, 1), "status_in_recovery_window_at_ms": rec_status,
            "recovery_bound_ms": b60["recovery"] if rec_status else b0["recovery"],
            "recovery_within": rec <= (b60["recovery"] if rec_status else b0["recovery"]),
            "detection_ms": round(det, 1), "status_in_detection_window_at_ms": det_status,
            "detection_bound_ms": b60["first_timeout"] if det_status else b0["first_timeout"],
            "detection_within": det <= (b60["first_timeout"] if det_status else b0["first_timeout"]),
            "recovery_anchor_found_in_log": anchor_ok,
            "log_sha256": digest,
        })
    with_status = [r for r in runs if r["status_in_recovery_window_at_ms"]]
    without = [r for r in runs if not r["status_in_recovery_window_at_ms"]]
    return {
        "schema": "washios.draft.status_windows.v1",
        "raw_root": str(raw_root),
        "inventory": str(INVENTORY.relative_to(ROOT)),
        "inventory_sha256": cft.sha256(INVENTORY),
        "bounds_ms": {"slip0": b0, "slip60": b60},
        "runs_checked": len(runs), "runs_missing": missing, "hash_mismatches": bad_hash,
        "recovery": {
            "with_status_in_window": len(with_status),
            "max_with_status_ms": max((r["recovery_ms"] for r in with_status), default=None),
            "max_without_status_ms": max((r["recovery_ms"] for r in without), default=None),
            "outside_applicable_bound": [r["run_id"] for r in runs if not r["recovery_within"]],
        },
        "detection_outside_applicable_bound": [r["run_id"] for r in runs if not r["detection_within"]],
        "anchor_not_found": [r["run_id"] for r in runs if not r["recovery_anchor_found_in_log"]],
        "runs": runs,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw-root", type=Path, required=True,
                        help="directory containing <run_id>/g431.log copied from the verified backup")
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).resolve().parent / "results" / "status_windows_report.json")
    args = parser.parse_args(argv)
    report = analyse(args.raw_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"checked {report['runs_checked']} runs, missing {len(report['runs_missing'])}, "
          f"hash mismatches {len(report['hash_mismatches'])}")
    for r in report["runs"]:
        if r["run_id"] in ("R085_P02", "R047_P02") or not r["recovery_within"]:
            print(f"  {r['run_id']} {r['mode']}: recovery {r['recovery_ms']} ms, status in window at "
                  f"{r['status_in_recovery_window_at_ms'] or 'none'}, bound {r['recovery_bound_ms']}, "
                  f"within={r['recovery_within']}")
    print(json.dumps(report["recovery"]))
    print(f"wrote {args.output}")
    return 0 if not report["hash_mismatches"] and not report["anchor_not_found"] else 1


if __name__ == "__main__":
    sys.exit(main())
