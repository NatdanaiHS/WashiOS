#!/usr/bin/env python3
"""Validate a completed payload campaign and generate its statistical summary."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path

from run_payload_campaign import FAULTS, RESULT_FIELDS, escaped_rendering, utc_now


def parse_bool(value: str) -> bool:
    if value == "True":
        return True
    if value == "False":
        return False
    raise ValueError(f"invalid boolean value: {value!r}")


def load_raw_log(path: Path) -> list[dict[str, object]]:
    events = []
    with path.open("r", encoding="ascii", newline="") as handle:
        for line_number, line in enumerate(handle, start=1):
            parts = line.rstrip("\n").split("\t", 2)
            if len(parts) != 3:
                raise ValueError(f"{path}:{line_number}: malformed raw record")
            host_time, raw_hex, rendered = parts
            raw = bytes.fromhex(raw_hex)
            if escaped_rendering(raw) != rendered:
                raise ValueError(f"{path}:{line_number}: rendering does not match raw hex")
            events.append(
                {
                    "host_time": host_time,
                    "raw": raw,
                    "text": raw.decode("ascii", errors="backslashreplace").rstrip("\r\n"),
                }
            )
    return events


def event_exists(
    events: list[dict[str, object]],
    marker: str,
    host_time: str | None = None,
    not_before: str | None = None,
) -> bool:
    return any(
        marker in str(event["text"])
        and (host_time is None or event["host_time"] == host_time)
        and (not_before is None or str(event["host_time"]) >= not_before)
        for event in events
    )


def validate_campaign(
    campaign_dir: Path, expected_seed: int, expected_per_fault: int
) -> tuple[dict[str, object], list[dict[str, str]]]:
    issues: list[str] = []
    with (campaign_dir / "manifest.json").open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    if manifest.get("status") != "COMPLETE":
        issues.append(f"manifest status is {manifest.get('status')!r}, not COMPLETE")
    if manifest.get("seed") != expected_seed:
        issues.append(f"manifest seed is {manifest.get('seed')!r}, expected {expected_seed}")

    with (campaign_dir / "run_plan.csv").open(newline="", encoding="utf-8") as handle:
        plan = list(csv.DictReader(handle))
    with (campaign_dir / "results.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != RESULT_FIELDS:
            issues.append("results.csv fields do not match the required schema")
        results = list(reader)

    expected_total = expected_per_fault * len(FAULTS)
    if len(plan) != expected_total:
        issues.append(f"run plan has {len(plan)} rows, expected {expected_total}")
    if len(results) != expected_total:
        issues.append(f"results have {len(results)} rows, expected {expected_total}")
    plan_ids = [row["run_id"] for row in plan]
    result_ids = [row["run_id"] for row in results]
    if len(set(plan_ids)) != len(plan_ids):
        issues.append("run plan contains duplicate run IDs")
    if len(set(result_ids)) != len(result_ids):
        issues.append("results contain duplicate run IDs")
    if plan_ids != result_ids:
        issues.append("result run IDs/order do not exactly match run plan")

    expected_counts = {mode: expected_per_fault for _, mode in FAULTS}
    plan_counts = Counter(row["fault_mode"] for row in plan)
    result_counts = Counter(row["fault_mode"] for row in results)
    if dict(plan_counts) != expected_counts:
        issues.append(f"run-plan fault counts are {dict(plan_counts)}, expected {expected_counts}")
    if dict(result_counts) != expected_counts:
        issues.append(f"result fault counts are {dict(result_counts)}, expected {expected_counts}")

    plan_by_id = {row["run_id"]: row for row in plan}
    raw_files_checked = 0
    invalid_rows = 0
    for row in results:
        run_id = row["run_id"]
        plan_row = plan_by_id.get(run_id)
        if plan_row is None:
            continue
        if any(row[field] != plan_row[field] for field in ("fault_id", "fault_mode")):
            issues.append(f"{run_id}: result fault identity differs from run plan")
        if row["seed"] != str(expected_seed):
            issues.append(f"{run_id}: result seed is {row['seed']!r}")
        if row["invalid_reason"]:
            invalid_rows += 1

        run_raw = campaign_dir / "raw" / run_id
        try:
            g431 = load_raw_log(run_raw / "g431.log")
            g474 = load_raw_log(run_raw / "g474.log")
            raw_files_checked += 2
        except (OSError, ValueError) as exc:
            issues.append(f"{run_id}: {exc}")
            continue
        if not g431:
            issues.append(f"{run_id}: empty G431 raw log")
        if not g474:
            issues.append(f"{run_id}: empty G474 raw log")

        try:
            activation_confirmed = parse_bool(row["activation_confirmed"])
            detection_observed = parse_bool(row["detection_observed"])
            offline_observed = parse_bool(row["offline_observed"])
            recovery_observed = parse_bool(row["recovery_observed"])
            restart_observed = parse_bool(row["controller_restart_marker_observed"])
        except ValueError as exc:
            issues.append(f"{run_id}: {exc}")
            continue

        activation_in_raw = event_exists(
            g474,
            f"[PAYLOAD] MODE={row['fault_mode']}",
            host_time=row["activation_host_time"] or None,
        )
        if activation_confirmed != activation_in_raw:
            issues.append(f"{run_id}: activation flag/timestamp does not match G474 raw log")
        restore_in_raw = event_exists(
            g474,
            "[PAYLOAD] MODE=NORMAL",
            host_time=row["restore_confirmation_host_time"] or None,
            not_before=row["restore_command_host_time"] or None,
        )
        if bool(row["restore_confirmation_host_time"]) != restore_in_raw:
            issues.append(f"{run_id}: restoration timestamp does not match G474 raw log")

        detection_in_raw = event_exists(
            g431,
            row["detection_event"] if detection_observed else "__NO_DETECTION__",
            host_time=row["detection_host_time"] or None,
            not_before=row["injection_host_time"] or None,
        )
        if detection_observed != detection_in_raw:
            issues.append(f"{run_id}: detection flag/event does not match G431 raw log")
        offline_in_raw = event_exists(
            g431, "[OBC] PAYLOAD_OFFLINE", not_before=row["injection_host_time"] or None
        )
        if offline_observed != offline_in_raw:
            issues.append(f"{run_id}: offline flag does not match G431 raw log")
        recovery_in_raw = event_exists(
            g431,
            "[OBC] PAYLOAD_RECOVERED",
            host_time=row["recovery_host_time"] or None,
            not_before=row["restore_command_host_time"] or None,
        )
        if recovery_observed != recovery_in_raw:
            issues.append(f"{run_id}: recovery flag/timestamp does not match G431 raw log")
        restart_in_raw = event_exists(
            g431, "[OBC] PAYLOAD_LINK_START", not_before=row["injection_host_time"] or None
        )
        if restart_observed != restart_in_raw:
            issues.append(f"{run_id}: restart-marker flag does not match G431 raw log")

    validation = {
        "valid": not issues,
        "generated_host_time": utc_now(),
        "campaign": campaign_dir.name,
        "expected_seed": expected_seed,
        "expected_per_fault": expected_per_fault,
        "expected_total": expected_total,
        "plan_rows": len(plan),
        "result_rows": len(results),
        "invalid_rows": invalid_rows,
        "raw_files_checked": raw_files_checked,
        "issues": issues,
    }
    return validation, results


def binomial_cdf(k: int, n: int, probability: float) -> float:
    return sum(
        math.comb(n, index)
        * probability**index
        * (1.0 - probability) ** (n - index)
        for index in range(k + 1)
    )


def exact_binomial_ci(successes: int, trials: int, alpha: float = 0.05) -> tuple[float, float]:
    if trials <= 0 or successes < 0 or successes > trials:
        raise ValueError("invalid binomial counts")
    tail = alpha / 2.0
    if successes == 0:
        lower = 0.0
    else:
        low, high = 0.0, successes / trials
        for _ in range(80):
            middle = (low + high) / 2.0
            upper_tail = 1.0 - binomial_cdf(successes - 1, trials, middle)
            if upper_tail < tail:
                low = middle
            else:
                high = middle
        lower = (low + high) / 2.0

    if successes == trials:
        upper = 1.0
    else:
        low, high = successes / trials, 1.0
        for _ in range(80):
            middle = (low + high) / 2.0
            lower_tail = binomial_cdf(successes, trials, middle)
            if lower_tail > tail:
                low = middle
            else:
                high = middle
        upper = (low + high) / 2.0
    return lower, upper


def latency_statistics(values: list[float]) -> dict[str, object]:
    if not values:
        return {"n": 0, "median_ms": None, "q1_ms": None, "q3_ms": None, "iqr_ms": None, "min_ms": None, "max_ms": None}
    ordered = sorted(values)
    if len(ordered) == 1:
        q1 = q3 = ordered[0]
    else:
        q1, _, q3 = statistics.quantiles(ordered, n=4, method="inclusive")
    return {
        "n": len(ordered),
        "median_ms": round(statistics.median(ordered), 3),
        "q1_ms": round(q1, 3),
        "q3_ms": round(q3, 3),
        "iqr_ms": round(q3 - q1, 3),
        "min_ms": round(ordered[0], 3),
        "max_ms": round(ordered[-1], 3),
    }


def proportion_summary(successes: int, trials: int) -> dict[str, object]:
    lower, upper = exact_binomial_ci(successes, trials)
    return {
        "successes": successes,
        "trials": trials,
        "proportion": round(successes / trials, 9),
        "exact_95_ci_lower": round(lower, 9),
        "exact_95_ci_upper": round(upper, 9),
    }


def build_summary(results: list[dict[str, str]], campaign: str, seed: int) -> dict[str, object]:
    by_fault: dict[str, object] = {}
    for _, mode in FAULTS:
        rows = [row for row in results if row["fault_mode"] == mode]
        valid = [
            row
            for row in rows
            if not row["invalid_reason"]
            and parse_bool(row["activation_confirmed"])
            and bool(row["restore_confirmation_host_time"])
        ]
        detections = [row for row in valid if parse_bool(row["detection_observed"])]
        recoveries = [row for row in valid if parse_bool(row["recovery_observed"])]
        by_fault[mode] = {
            "planned_trials": len(rows),
            "valid_trials": len(valid),
            "invalid_trials": len(rows) - len(valid),
            "activation_confirmed_trials": sum(parse_bool(row["activation_confirmed"]) for row in rows),
            "restoration_confirmed_trials": sum(bool(row["restore_confirmation_host_time"]) for row in rows),
            "offline_observed_trials": sum(parse_bool(row["offline_observed"]) for row in valid),
            "restart_marker_observed_trials": sum(parse_bool(row["controller_restart_marker_observed"]) for row in valid),
            "detection": proportion_summary(len(detections), len(valid)),
            "recovery": proportion_summary(len(recoveries), len(valid)),
            "detection_latency": latency_statistics([float(row["detection_latency_ms"]) for row in detections if row["detection_latency_ms"]]),
            "recovery_latency": latency_statistics([float(row["recovery_time_ms"]) for row in recoveries if row["recovery_time_ms"]]),
        }
    return {
        "schema_version": 1,
        "generated_host_time": utc_now(),
        "campaign": campaign,
        "seed": seed,
        "validity_definition": "invalid_reason empty, G474 activation confirmed, and G474 NORMAL restoration confirmed",
        "proportion_denominator": "valid trials for the corresponding fault mode",
        "confidence_interval": "two-sided 95% Clopper-Pearson exact binomial interval",
        "latency_definition": "host-observed serial timestamps; detection from injection command send and recovery from NORMAL restore command send",
        "quartile_definition": "inclusive linear quartiles; IQR = Q3 - Q1",
        "faults": by_fault,
    }


def write_exclusive_json(path: Path, value: dict[str, object]) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--expected-per-fault", type=int, default=30)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    campaign_dir = args.campaign_dir.resolve()
    validation, results = validate_campaign(campaign_dir, args.seed, args.expected_per_fault)
    write_exclusive_json(campaign_dir / "validation.json", validation)
    if not validation["valid"]:
        print(f"campaign validation failed with {len(validation['issues'])} issue(s)", file=sys.stderr)
        return 2
    summary = build_summary(results, campaign_dir.name, args.seed)
    write_exclusive_json(campaign_dir / "summary.json", summary)
    print(f"validated {validation['result_rows']} trials and {validation['raw_files_checked']} raw logs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
