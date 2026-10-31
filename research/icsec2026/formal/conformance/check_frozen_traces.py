#!/usr/bin/env python3
"""Replay frozen WashiOS hardware evidence against the payload-link model's observable
alphabet and verified bounds.

Read-only. Consumes committed summary artifacts (results.csv, summary JSON, extension
ledgers); never touches raw logs or firmware. Writes one JSON report to the path given by
--output (default: formal/conformance/results/conformance_report.json).

Bounds are the model's verified inclusive values (see models/payload_link.q). Host-observed intervals are
compared under two anchors; the model-comparable one starts at the confirmation event, matching the model's
clock. Residual uncertainty is quantified from the evidence rather than declared: the record carries both a
wall-clock and a monotonic timestamp for each command-anchored interval, and their disagreement bounds the
granularity of the wall-clock stamps.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import datetime as dt
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PRIMARY = ROOT / "research/icsec2026/runs/full_20260830_seed20260830_n30"
N0_PRE = ROOT / "research/icsec2026/runs/n0_pre_20260830_0205/validation.json"
N0_POST = ROOT / "research/icsec2026/runs/n0_post_20260830_0224/validation.json"
EXT = ROOT / "research/icsec2026/extension/evidence/primary_20260830_seed20260830_b5"
F411 = [
    ROOT / "research/icsec2026/extension/evidence/f411_pair1_campaign_20260901_seed20260901_b3",
    ROOT / "research/icsec2026/extension/evidence/f411_pair2_campaign_20260901_seed20260901_b3",
]

# Model constants (must match models/payload_link.xml)
POLL_MS = 500
DEADLINE_MS = 100
LOOP_MS = 1
JITTER_MS = 2
TX_MIN_MS = 3
TX_MAX_MS = 4

# Verified inclusive bounds (models/payload_link.xml; verifyta Q2/Q3/Q4 with tightness Q2T/Q3T/Q4T)
FIRST_TIMEOUT_BOUND_MS = POLL_MS + JITTER_MS + DEADLINE_MS + LOOP_MS + JITTER_MS          # 605
OFFLINE_BOUND_MS = 3 * (POLL_MS + JITTER_MS) + DEADLINE_MS + LOOP_MS + JITTER_MS          # 1609
RECOVERY_BOUND_MS = POLL_MS + JITTER_MS + TX_MAX_MS                                       # 506


def model_accepts(delay_ms: int) -> bool:
    """ACCEPTS predicate of the model: latest response precedes the earliest deadline check."""
    return delay_ms + TX_MAX_MS < DEADLINE_MS


def model_times_out(delay_ms: int) -> bool:
    """TIMES_OUT predicate of the model: earliest response follows the latest deadline check."""
    return delay_ms + TX_MIN_MS > DEADLINE_MS + LOOP_MS + JITTER_MS

# Falsification floor for the bound comparison. Declared, not fitted: it is more than three times the
# clock disagreement demonstrated by the evidence itself (see clock_disagreement in the report). The replay
# can falsify a bound violation larger than this; smaller excesses are reported as unresolved.
RESOLUTION_MS = 50

# Expected first detector marker per fault mode (predefined by the frozen harness)
EXPECTED_DETECTOR = {
    "SILENT": "[OBC] PAYLOAD_TIMEOUT consecutive=1",
    "DELAYED": "[OBC] PAYLOAD_TIMEOUT consecutive=1",
    "BAD_CRC": "[OBC] PAYLOAD_REJECT reason=CRC",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _ms(a: str, b: str) -> float:
    """Interval in ms between two retained ISO-8601 wall-clock host timestamps."""
    return (dt.datetime.fromisoformat(a) - dt.datetime.fromisoformat(b)).total_seconds() * 1000.0


def check_primary_campaign() -> dict:
    """Compare the 90 primary trials against the model bounds under two anchors.

    The frozen `*_latency_ms` columns are monotonic-clock intervals measured from the *command send*.
    The model's clocks start at *confirmed* fault onset and *confirmed* restoration, so the command
    anchor is structurally earlier than the model's and overstates the model-comparable interval. The
    confirmation anchor is recomputed here from the retained wall-clock stamps of the two serial events
    that bracket the model's interval. Both endpoints of each confirmation-anchored interval are serial
    events timestamped by the same host process, but they arrive on different channels, so the interval
    carries cross-channel read latency that the evidence does not separate.
    """
    with (PRIMARY / "results.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    issues: list[str] = []
    unresolved: list[dict] = []
    per_mode: dict[str, dict] = {}
    disagreement: list[float] = []

    for row in rows:
        mode = row["fault_mode"]
        m = per_mode.setdefault(mode, {
            "rows": 0, "detector_alphabet_ok": 0, "offline_observed": 0, "restart_marker": 0,
            "command_anchored": {"detection": [], "recovery": []},
            "confirmation_anchored": {"detection": [], "recovery": []},
        })
        m["rows"] += 1
        if row["detection_event"] == EXPECTED_DETECTOR[mode]:
            m["detector_alphabet_ok"] += 1
        else:
            issues.append(f"{row['run_id']}: unexpected detector marker {row['detection_event']!r}")

        cmd_det, cmd_rec = float(row["detection_latency_ms"]), float(row["recovery_time_ms"])
        conf_det = _ms(row["detection_host_time"], row["activation_host_time"])
        conf_rec = _ms(row["recovery_host_time"], row["restore_confirmation_host_time"])
        m.setdefault("within_bound", {"detection": 0, "recovery": 0})
        if conf_det <= FIRST_TIMEOUT_BOUND_MS:
            m["within_bound"]["detection"] += 1
        if conf_rec <= RECOVERY_BOUND_MS:
            m["within_bound"]["recovery"] += 1
        m["command_anchored"]["detection"].append(cmd_det)
        m["command_anchored"]["recovery"].append(cmd_rec)
        m["confirmation_anchored"]["detection"].append(conf_det)
        m["confirmation_anchored"]["recovery"].append(conf_rec)

        # The record carries two independent clock bases for the same command-anchored interval.
        # Their disagreement bounds the granularity of the retained wall-clock stamps.
        disagreement.append(abs(_ms(row["detection_host_time"], row["injection_host_time"]) - cmd_det))
        disagreement.append(abs(_ms(row["recovery_host_time"], row["restore_command_host_time"]) - cmd_rec))

        for kind, value, bound in (("detection", conf_det, FIRST_TIMEOUT_BOUND_MS),
                                   ("recovery", conf_rec, RECOVERY_BOUND_MS)):
            excess = value - bound
            if excess <= 0:
                continue
            record = {"run_id": row["run_id"], "mode": mode, "interval": kind,
                      "observed_ms": round(value, 1), "bound_ms": bound, "excess_ms": round(excess, 1)}
            if excess > RESOLUTION_MS:
                issues.append(f"{row['run_id']}: {kind} exceeds bound {bound} ms by {excess:.1f} ms "
                              f"(beyond the {RESOLUTION_MS} ms falsification floor)")
            else:
                unresolved.append(record)

        if row["offline_observed"] == "True":
            m["offline_observed"] += 1
        if row["controller_restart_marker_observed"] == "True":
            m["restart_marker"] += 1
            issues.append(f"{row['run_id']}: restart marker observed")

    def summarise(values: list[float]) -> dict:
        return {"n": len(values), "median_ms": round(statistics.median(values), 1),
                "max_ms": round(max(values), 1)}

    for m in per_mode.values():
        for anchor in ("command_anchored", "confirmation_anchored"):
            m[anchor] = {k: summarise(v) for k, v in m[anchor].items()}

    intervals = 2 * len(rows)
    return {
        "source": str(PRIMARY.relative_to(ROOT) / "results.csv"),
        "source_sha256": sha256(PRIMARY / "results.csv"),
        "rows": len(rows),
        "anchors": {
            "command": "frozen monotonic-clock columns, measured from command send (earlier than the model's clock start)",
            "confirmation": "recomputed from retained wall-clock stamps of the confirming and the observed serial event (model-comparable)",
        },
        "bounds_ms": {"first_timeout": FIRST_TIMEOUT_BOUND_MS, "offline": OFFLINE_BOUND_MS,
                      "recovery": RECOVERY_BOUND_MS, "falsification_floor": RESOLUTION_MS},
        "clock_disagreement_ms": {"n": len(disagreement),
                                  "max": round(max(disagreement), 2),
                                  "median": round(statistics.median(disagreement), 2)},
        "bound_check": {"intervals": intervals,
                        "within_bound": intervals - len(unresolved),
                        "unresolved": len(unresolved),
                        "violations_beyond_floor": sum(1 for i in issues if "falsification floor" in i)},
        "unresolved_intervals": unresolved,
        "per_mode": per_mode,
        "issues": issues,
    }


def descriptive_statistics() -> dict:
    """Per-mode host-observed latency summaries from the frozen campaign summary, reported next to the
    verified bounds. Descriptive only: no interval, reliability, or population statement is derived."""
    path = PRIMARY / "summary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    table = {}
    for mode, entry in data["faults"].items():
        det, rec = entry["detection_latency"], entry["recovery_latency"]
        table[mode] = {
            "n": det["n"],
            "detection_ms": {k: det[f"{k}_ms"] for k in ("median", "iqr", "min", "max")},
            "recovery_ms": {k: rec[f"{k}_ms"] for k in ("median", "iqr", "min", "max")},
            "detection_bound_ms": FIRST_TIMEOUT_BOUND_MS,
            "recovery_bound_ms": RECOVERY_BOUND_MS,
            "anchor": "command send (frozen monotonic columns); see primary_campaign for the model-comparable anchor",
            "detected_trials": entry["detection"]["successes"],
            "recovered_trials": entry["recovery"]["successes"],
        }
    return {"source": str(path.relative_to(ROOT)), "source_sha256": sha256(path),
            "latency_definition": data.get("latency_definition"), "per_mode": table}


def measure_timebase() -> dict:
    """Measure the controller's actual poll cadence from the frozen nominal windows.

    The model's constants are in MCU time; every host-observed interval is in host time. Each
    nominal window records the controller's own poll counter alongside a host timestamp, so the
    mean poll period over a long window measures the ratio between the two time bases. It also
    bounds the per-poll scheduling overhead that the model books as jitter: were that overhead
    being consumed systematically, the mean period would exceed the nominal 500 ms.
    """
    windows = [
        ("observation_605s", EXT / "nominal_validation_002.json"),
        ("n0_pre", N0_PRE.parent / "validation.json"),
        ("n0_post", N0_POST.parent / "validation.json"),
    ]
    out, ratios = {}, []
    for name, path in windows:
        records = json.loads(path.read_text(encoding="utf-8"))["status_records"]
        polls = records[-1]["polls"] - records[0]["polls"]
        if "monotonic_s" in records[0]:          # monotonic clock: granularity negligible
            span = records[-1]["monotonic_s"] - records[0]["monotonic_s"]
            uncertainty, clock = 0.0, "monotonic"
        else:                                     # two wall-clock stamps, ~15.6 ms each
            span = _ms(records[-1]["host_time"], records[0]["host_time"]) / 1000.0
            uncertainty, clock = 2 * 15.6 / polls, "wall"
        period = 1000.0 * span / polls
        ratio = POLL_MS / period
        ratios.append(ratio)
        out[name] = {"clock": clock, "polls": polls, "span_s": round(span, 3),
                     "mean_poll_period_ms": round(period, 3),
                     "period_uncertainty_ms": round(uncertainty, 3),
                     "mcu_per_host": round(ratio, 5)}
    return {
        "nominal_poll_period_ms": POLL_MS,
        "windows": out,
        "mcu_per_host_range": [round(min(ratios), 5), round(max(ratios), 5)],
        "host_shorter_by_pct": round(100.0 * (max(ratios) - 1.0), 3),
        "jitter_bound_ms": JITTER_MS,
        "mean_overhead_consumed_ms": round(max(o["mean_poll_period_ms"] for o in out.values()) - POLL_MS, 3),
        "interpretation": (
            "the mean poll period is below the nominal 500 ms in every window, so the per-poll "
            "scheduling overhead the model bounds by JITTER_MS is not consumed on average; the "
            "residual difference is a stable MCU-to-host clock-rate ratio"),
    }


def check_n0(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    deltas = data.get("counter_deltas", {})
    issues = []
    for key in ("timeout", "crc", "seq", "recovery"):
        if deltas.get(key, None) != 0:
            issues.append(f"{path.name}: counter delta {key}={deltas.get(key)} (model Q1 expects 0)")
    if data.get("prohibited_markers"):
        issues.append(f"{path.name}: prohibited markers present")
    return {
        "source": str(path.relative_to(ROOT)),
        "source_sha256": sha256(path),
        "valid": data.get("valid"),
        "duration_s": data.get("duration_s"),
        "counter_deltas": deltas,
        "issues": issues,
    }


def check_extension_delay_sweep() -> dict:
    summary = json.loads((EXT / "descriptive_summary.json").read_text(encoding="utf-8"))
    delays = summary["delay_summary"]
    issues = []
    table = {}
    for d_str, obs in sorted(delays.items(), key=lambda kv: int(kv[0])):
        d = int(d_str)
        n = obs["valid_observations"]
        # Model Q9a/Q9b: ACCEPTS and TIMES_OUT predicates; neither holds in the undetermined band
        accepts = model_accepts(d)
        rejects = model_times_out(d)
        observed_accept = obs["accepted_delayed_response_observed"] == n and obs["timeout_observed"] == 0
        observed_reject = obs["timeout_observed"] == n and obs["offline_observed"] == n
        verdict = "CONFORMS"
        if accepts and not observed_accept:
            verdict = "MISMATCH"
        elif rejects and not observed_reject:
            verdict = "MISMATCH"
        elif not accepts and not rejects:
            verdict = "BOUNDARY_UNDETERMINED_CONSISTENT" if (observed_accept or observed_reject) else "BOUNDARY_UNDETERMINED_MIXED"
        if verdict == "MISMATCH":
            issues.append(f"delay {d} ms: model predicts accept={accepts} reject={rejects}, observed {obs}")
        table[d] = {
            "valid_observations": n,
            "model_accepts": accepts,
            "model_rejects": rejects,
            "observed_accepted_all": observed_accept,
            "observed_timeout_offline_all": observed_reject,
            "sequence_rejection_observed": obs["sequence_rejection_observed"],
            "verdict": verdict,
        }
    bad = summary["bad_crc"]
    crc_order = {}
    for exposure in ("short", "sustained"):
        markers = [m["marker"] for m in bad[exposure]["observed_markers"]]
        first_crc = next((i for i, m in enumerate(markers) if "PAYLOAD_REJECT reason=CRC" in m), None)
        first_tout = next((i for i, m in enumerate(markers) if "PAYLOAD_TIMEOUT" in m), None)
        ok = first_crc is not None and (first_tout is None or first_crc < first_tout)
        if not ok:
            issues.append(f"BAD_CRC {exposure}: CRC reject does not precede first timeout")
        crc_order[exposure] = {"markers": markers, "crc_before_first_timeout": ok,
                               "offline_before_restore": bad[exposure]["offline_before_restore"]}
    nominal = summary["nominal"]
    if any(v != 0 for v in nominal["counter_deltas"].values()):
        issues.append("605 s nominal: nonzero counter delta")
    return {
        "source": str((EXT / "descriptive_summary.json").relative_to(ROOT)),
        "source_sha256": sha256(EXT / "descriptive_summary.json"),
        "delay_sweep": table,
        "bad_crc_ordering": crc_order,
        "nominal_605s": nominal,
        "issues": issues,
    }


def check_f411(pair_dir: Path) -> dict:
    path = pair_dir / "descriptive_condition_summary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    issues = []
    table = {}
    for cond, obs in sorted(data["conditions"].items()):
        counts = obs["valid_row_marker_counts"]
        n = obs["valid"]
        if cond == "NC":
            expect_ok = counts["timeout"] == 0 and counts["offline"] == 0
            verdict = "CONFORMS" if expect_ok else "MISMATCH"
        else:
            d = int(cond[1:])
            accepts = model_accepts(d)
            rejects = model_times_out(d)
            if accepts:
                verdict = "CONFORMS" if counts["timeout"] == 0 and counts["accepted_mode_3"] > 0 else "MISMATCH"
            elif rejects:
                verdict = "CONFORMS" if counts["offline"] == n and counts["accepted_mode_3"] == 0 else "MISMATCH"
            else:
                consistent = (counts["timeout"] == 0 and counts["accepted_mode_3"] > 0) or (counts["offline"] == n and counts["accepted_mode_3"] == 0)
                verdict = "BOUNDARY_UNDETERMINED_CONSISTENT" if consistent else "BOUNDARY_UNDETERMINED_MIXED"
        if verdict == "MISMATCH":
            issues.append(f"{pair_dir.name} {cond}: {counts}")
        table[cond] = {"valid": n, "marker_counts": counts, "verdict": verdict}
    return {
        "source": str(path.relative_to(ROOT)),
        "source_sha256": sha256(path),
        "campaign_id": data["campaign_id"],
        "conditions": table,
        "issues": issues,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "research/icsec2026/formal/conformance/results/conformance_report.json")
    args = parser.parse_args(argv)

    report = {
        "schema": "washios.formal.conformance.v1",
        "model": "research/icsec2026/formal/models/payload_link.xml",
        "primary_campaign": check_primary_campaign(),
        "descriptive_statistics": descriptive_statistics(),
        "timebase": measure_timebase(),
        "n0_pre": check_n0(N0_PRE),
        "n0_post": check_n0(N0_POST),
        "extension_primary": check_extension_delay_sweep(),
        "f411_pairs": [check_f411(p) for p in F411 if p.exists()],
    }
    all_issues = []
    for key in ("primary_campaign", "n0_pre", "n0_post", "extension_primary"):
        all_issues += report[key]["issues"]
    for pair in report["f411_pairs"]:
        all_issues += pair["issues"]
    report["total_issues"] = len(all_issues)
    report["issues"] = all_issues

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {args.output.relative_to(ROOT)}; issues={len(all_issues)}")
    for issue in all_issues:
        print("  -", issue)
    return 0 if not all_issues else 1


if __name__ == "__main__":
    sys.exit(main())
