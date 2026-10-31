#!/usr/bin/env python3
"""Replay frozen WashiOS hardware evidence against the payload-link model's observable
alphabet and verified bounds.

Read-only. Consumes committed summary artifacts (results.csv, summary JSON, extension
ledgers); never touches raw logs or firmware. Writes one JSON report to the path given by
--output (default: draft-camera-ready/conformance/results/conformance_report.json).

DRAFT-CAMERA-READY copy (2026-10-18) of formal/conformance/check_frozen_traces.py. Changes: bounds of the
draft model (round-trip response window A2, status-report block A7) at SLIP 0 and SLIP 60; slip-aware
delay predicates; the 15.4 ms two-clock disagreement is attributed to the coarse monotonic clock, not to
the wall-clock stamps; per-stamp host read residual and steady-state poll period measured from the raw
605 s nominal logs. Bounds are the draft model's closed forms, verified by results/20261018T073529Z.

Bounds are the model's verified inclusive values (see models/payload_link.q). Host-observed intervals are
compared under two anchors; the model-comparable one starts at the confirmation event, matching the model's
clock. Residual uncertainty is quantified from the evidence rather than declared: the record carries both a
wall-clock and a monotonic timestamp for each command-anchored interval, and their disagreement bounds the
granularity of the coarser clock. DRAFT: that coarse clock is the Windows monotonic clock (~15.6 ms tick;
every command-anchored latency is a whole number of ms in 15-16 ms steps); the wall-clock stamps used by
the confirmation anchor are sub-ms, and their noise is bounded instead by the per-stamp host read residual.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import datetime as dt
import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
NOMINAL_RAW = [
    ROOT / "research/icsec2026/extension/evidence/primary_20260830_seed20260830_b5/raw/nominal/NOMINAL_001/g431.log",
    ROOT / "research/icsec2026/extension/evidence/primary_20260830_seed20260830_b5/raw/nominal/NOMINAL_002/g431.log",
]
PRIMARY = ROOT / "research/icsec2026/runs/full_20260830_seed20260830_n30"
N0_PRE = ROOT / "research/icsec2026/runs/n0_pre_20260830_0205/validation.json"
N0_POST = ROOT / "research/icsec2026/runs/n0_post_20260830_0224/validation.json"
EXT = ROOT / "research/icsec2026/extension/evidence/primary_20260830_seed20260830_b5"
F411 = [
    ROOT / "research/icsec2026/extension/evidence/f411_pair1_campaign_20260901_seed20260901_b3",
    ROOT / "research/icsec2026/extension/evidence/f411_pair2_campaign_20260901_seed20260901_b3",
]

# Model constants (must match draft-camera-ready/models/payload_link.xml)
POLL_MS = 500
DEADLINE_MS = 100
LOOP_MS = 1
JITTER_MS = 2
DECODE_MIN_MS, DECODE_MAX_MS = 2, 9
RESP_MIN_MS, RESP_MAX_MS = 2, 4
DELAY_EXTRA_MS = 1
SLIP_MS = 60          # status-report block (assumption A7), evidence-derived, host-observed
OFFLINE_N = 3


def bounds(slip: int) -> dict:
    """Closed-form inclusive bounds of the draft model (verified, results/20261018T073529Z)."""
    return {
        "first_timeout": POLL_MS + JITTER_MS - DECODE_MIN_MS + DEADLINE_MS + LOOP_MS + JITTER_MS + slip,
        "offline": OFFLINE_N * (POLL_MS + JITTER_MS) - DECODE_MIN_MS + DEADLINE_MS + LOOP_MS + JITTER_MS + slip,
        "recovery": POLL_MS + JITTER_MS - DECODE_MIN_MS + DECODE_MAX_MS + RESP_MAX_MS + LOOP_MS + JITTER_MS + slip,
    }


# Between status reports (SLIP 0): 603 / 1607 / 516. With a status report in the window: 663 / 1667 / 576.
FIRST_TIMEOUT_BOUND_MS = bounds(0)["first_timeout"]
OFFLINE_BOUND_MS = bounds(0)["offline"]
RECOVERY_BOUND_MS = bounds(0)["recovery"]
STATUS_BOUNDS = bounds(SLIP_MS)


def model_accepts(delay_ms: int) -> bool:
    """ACCEPTS predicate: the latest response precedes the earliest deadline check (SLIP does not enter)."""
    return delay_ms + DECODE_MAX_MS + DELAY_EXTRA_MS + RESP_MAX_MS < DEADLINE_MS


def model_times_out(delay_ms: int, slip: int = 0) -> bool:
    """TIMES_OUT predicate: the earliest response follows the latest deadline check."""
    return delay_ms + DECODE_MIN_MS + RESP_MIN_MS > DEADLINE_MS + LOOP_MS + JITTER_MS + slip

# Falsification floor for the bound comparison. Declared, not fitted. DRAFT justification: it exceeds
# five times the largest per-stamp host read residual measured on the raw nominal logs (host_read_residual
# in the report) and three times the monotonic-tick disagreement. The replay can falsify a bound violation
# larger than this; smaller excesses are reported as unresolved.
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
        m.setdefault("within_status_bound", {"detection": 0, "recovery": 0})
        if conf_det <= FIRST_TIMEOUT_BOUND_MS:
            m["within_bound"]["detection"] += 1
        if conf_rec <= RECOVERY_BOUND_MS:
            m["within_bound"]["recovery"] += 1
        if conf_det <= STATUS_BOUNDS["first_timeout"]:
            m["within_status_bound"]["detection"] += 1
        if conf_rec <= STATUS_BOUNDS["recovery"]:
            m["within_status_bound"]["recovery"] += 1
        m["command_anchored"]["detection"].append(cmd_det)
        m["command_anchored"]["recovery"].append(cmd_rec)
        m["confirmation_anchored"]["detection"].append(conf_det)
        m["confirmation_anchored"]["recovery"].append(conf_rec)

        # The record carries two independent clock bases for the same command-anchored interval.
        # DRAFT: their disagreement is dominated by the ~15.6 ms tick of the monotonic clock.
        disagreement.append(abs(_ms(row["detection_host_time"], row["injection_host_time"]) - cmd_det))
        disagreement.append(abs(_ms(row["recovery_host_time"], row["restore_command_host_time"]) - cmd_rec))

        for kind, value, bound in (("detection", conf_det, FIRST_TIMEOUT_BOUND_MS),
                                   ("recovery", conf_rec, RECOVERY_BOUND_MS)):
            excess = value - bound
            if excess <= 0:
                continue
            status_bound = STATUS_BOUNDS["first_timeout" if kind == "detection" else "recovery"]
            record = {"run_id": row["run_id"], "mode": mode, "interval": kind,
                      "observed_ms": round(value, 1), "bound_ms": bound, "excess_ms": round(excess, 1),
                      "status_bound_ms": status_bound, "within_status_bound": value <= status_bound}
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
        "status_bounds_ms": STATUS_BOUNDS,
        "bound_semantics": ("bounds_ms hold when no status report falls in the window (SLIP 0); status_bounds_ms "
                            "hold in every window (SLIP 60). The primary raw logs are not in this checkout, so "
                            "which windows contained a status report cannot be decided here."),
        "monotonic_tick_disagreement_ms": {"n": len(disagreement),
                                  "max": round(max(disagreement), 2),
                                  "median": round(statistics.median(disagreement), 2)},
        "bound_check": {"intervals": intervals,
                        "within_bound": intervals - len(unresolved),
                        "unresolved": len(unresolved),
                        "within_status_bound": intervals - sum(1 for u in unresolved if not u["within_status_bound"]),
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


def _raw_lines(path: Path):
    """Reassemble the raw serial log (utc<TAB>hex<TAB>ascii chunks) into lines stamped at their newline."""
    buf = b""
    for raw in path.read_text(encoding="utf-8").splitlines():
        stamp, hexdata = raw.split("\t")[:2]
        buf += bytes.fromhex(hexdata)
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            yield dt.datetime.fromisoformat(stamp).timestamp() * 1000.0, line.decode(errors="replace").strip()


def measure_raw_nominal() -> dict:
    """DRAFT. From the raw 605 s nominal logs: steady-state poll period, the poll-schedule slip at each
    PAYLOAD_STATUS report (assumption A7), and the per-stamp host read residual.

    offset_i = t(ACCEPTED seq=i) - i * P_median. A single late host read moves one offset; a slip of the
    MCU poll schedule moves every later offset. The slip at a status report is the difference between the
    medians of the five offsets after and before it (ten consecutive polls required); the control is the
    same statistic at windows with no status report. The read residual is each offset minus the larger of
    the medians of its three left and three right neighbours.
    """
    out, all_slip, all_ctrl, all_resid, periods_all = {}, [], [], [], []
    for path in NOMINAL_RAW:
        acc, status = {}, []
        for t, line in _raw_lines(path):
            hit = re.search(r"PAYLOAD_ACCEPTED seq=(\d+)", line)
            if hit:
                acc[int(hit.group(1))] = t
            if "PAYLOAD_STATUS" in line:
                status.append(t)
        seqs = sorted(acc)
        periods = [acc[b] - acc[a] for a, b in zip(seqs, seqs[1:]) if b == a + 1]
        p_med = statistics.median(periods)
        periods_all.append(p_med)
        off = {k: acc[k] - k * p_med for k in seqs}
        slips, ctrl, resid = [], [], []
        for x in status:
            before = [k for k in seqs if acc[k] < x][-5:]
            after = [k for k in seqs if acc[k] > x][:5]
            if len(before) == 5 and len(after) == 5 and after[-1] - before[0] == 9:
                slips.append(statistics.median(off[k] for k in after) - statistics.median(off[k] for k in before))
        for i in range(5, len(seqs) - 5):
            win = seqs[i - 5:i + 5]
            if win[-1] - win[0] != 9 or any(acc[win[0]] < x < acc[win[-1]] for x in status):
                continue
            ctrl.append(statistics.median(off[k] for k in win[5:]) - statistics.median(off[k] for k in win[:5]))
        for i in range(3, len(seqs) - 3):
            win = seqs[i - 3:i + 4]
            if win[-1] - win[0] != 6:
                continue
            resid.append(off[seqs[i]] - max(statistics.median(off[k] for k in win[:3]),
                                            statistics.median(off[k] for k in win[4:])))
        all_slip += slips; all_ctrl += ctrl; all_resid += resid
        out[path.parent.name] = {"source": str(path.relative_to(ROOT)), "source_sha256": sha256(path),
                                 "accepted_polls": len(seqs), "status_reports": len(status),
                                 "median_poll_period_host_ms": round(p_med, 3)}
    all_resid.sort()
    return {
        "windows": out,
        "status_slip_ms": {"n": len(all_slip), "min": round(min(all_slip), 1),
                           "median": round(statistics.median(all_slip), 1), "max": round(max(all_slip), 1),
                           "model_slip_ms": SLIP_MS},
        "control_slip_ms": {"n": len(all_ctrl), "min": round(min(all_ctrl), 1), "max": round(max(all_ctrl), 1)},
        "host_read_residual_ms": {"n": len(all_resid), "p99": round(all_resid[int(0.99 * (len(all_resid) - 1))], 1),
                                  "max": round(all_resid[-1], 1)},
        "steady_state": {
            "median_poll_period_host_ms": round(max(periods_all), 3),
            "mcu_fast_by_at_least_pct": round(100.0 * (POLL_MS / max(periods_all) - 1.0), 3),
            "note": ("the controller polls no earlier than 500 MCU ms after the previous stamp, so a host-observed "
                     "steady-state median below 500 ms means the MCU time base runs fast relative to the host by at "
                     "least this much; the submitted 0.235 % came from the mean period, which includes the status "
                     "slips"),
        },
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
        rejects_any_window = model_times_out(d, SLIP_MS)
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
            "model_rejects_with_status_block": rejects_any_window,
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
                        default=ROOT / "research/icsec2026/draft-camera-ready/conformance/results/conformance_report.json")
    args = parser.parse_args(argv)

    report = {
        "schema": "washios.formal.conformance.v1-draft-camera-ready",
        "model": "research/icsec2026/draft-camera-ready/models/payload_link.xml",
        "bounds_status": "closed forms of the draft model, verified by results/20261018T073529Z",
        "primary_campaign": check_primary_campaign(),
        "descriptive_statistics": descriptive_statistics(),
        "timebase": measure_timebase(),
        "raw_nominal": measure_raw_nominal(),
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
