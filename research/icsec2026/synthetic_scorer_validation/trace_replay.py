from __future__ import annotations

import copy
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CAMPAIGN = ROOT / "research" / "icsec2026" / "runs" / "full_20260830_seed20260830_n30"
RECOVERY_LEDGER = (
    ROOT
    / "research"
    / "icsec2026"
    / "extension"
    / "recovery"
    / "recovery_20260901"
    / "PRIMARY_COPY_LEDGER.csv"
)
BASELINE_RUN_ID = "R005_P02"
FAULT_MODE = "BAD_CRC"

EXPECTED_SOURCE_HASHES = {
    "research/icsec2026/runs/full_20260830_seed20260830_n30/run_plan.csv":
        "08BCBDD505DA95460ABFADE719411409501DE7B6F40BE648B30CB4E986F051B7",
    "research/icsec2026/runs/full_20260830_seed20260830_n30/results.csv":
        "770FB1FEF5BFD6B529906B35CBA67D9BAC2887DED241EA38D8CB914A157478CE",
    "research/icsec2026/runs/full_20260830_seed20260830_n30/manifest.json":
        "10D966EE6F43BB70EAAFA713723F9C56EEDA51757E605BEB80A8578E0ABEE67F",
    "research/icsec2026/runs/full_20260830_seed20260830_n30/summary.json":
        "124554F98A93639B4C2C8C18A708DC14A1D5673823A4CD2F84DB0F563083E1CA",
    "research/icsec2026/runs/full_20260830_seed20260830_n30/validation.json":
        "D06426EE043D32B032FA3267E7A8DDAB0AD345FD1F69807E93E9F47507BA84EB",
    "research/icsec2026/runs/full_20260830_seed20260830_n30/SHA256SUMS.csv":
        "DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD",
    "research/icsec2026/runs/full_20260830_seed20260830_n30/raw/R005_P02/g431.log":
        "E73BA0A35F6F048A6C77A2422E9DCF5FBB190426E84EC66A2A31191A08C8D5C4",
    "research/icsec2026/runs/full_20260830_seed20260830_n30/raw/R005_P02/g474.log":
        "0B720C6913A8961EEE331CDBAC9B574685818FDE7D2CFF6E309C21935A9C9C30",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)


def relative_ms(value: str, origin: str) -> float:
    return round((parse_time(value) - parse_time(origin)).total_seconds() * 1000.0, 6)


def resolve_sources() -> dict[str, Path]:
    resolved: dict[str, Path] = {}
    for relative in EXPECTED_SOURCE_HASHES:
        candidate = ROOT / relative
        if candidate.is_file():
            resolved[relative] = candidate

    with RECOVERY_LEDGER.open(encoding="utf-8-sig", newline="") as handle:
        ledger = {row["path"]: row for row in csv.DictReader(handle)}
    for name in ("g431.log", "g474.log"):
        relative = (
            "research/icsec2026/runs/full_20260830_seed20260830_n30/"
            f"raw/{BASELINE_RUN_ID}/{name}"
        )
        row = ledger[relative]
        assert row["valid"] == "True"
        assert row["expected_sha256"] == EXPECTED_SOURCE_HASHES[relative]
        resolved[relative] = Path(row["source_path"])

    assert set(resolved) == set(EXPECTED_SOURCE_HASHES)
    return resolved


def snapshot_sources(resolved: dict[str, Path]) -> dict[str, dict[str, Any]]:
    snapshot: dict[str, dict[str, Any]] = {}
    for relative, path in sorted(resolved.items()):
        assert path.is_file(), relative
        actual = sha256(path)
        expected = EXPECTED_SOURCE_HASHES[relative]
        assert actual == expected, f"source hash mismatch: {relative}"
        snapshot[relative] = {
            "bytes": path.stat().st_size,
            "expected_sha256": expected,
            "resolved_path": str(path),
            "sha256": actual,
        }
    return snapshot


def read_raw(path: Path) -> list[dict[str, str]]:
    records = []
    for line in path.read_text(encoding="ascii").splitlines():
        host_time, raw_hex, rendering = line.split("\t", 2)
        records.append({"host_time": host_time, "raw_hex": raw_hex, "rendering": rendering})
    return records


def find_raw(records: list[dict[str, str]], host_time: str, marker: str) -> dict[str, str]:
    matches = [
        record
        for record in records
        if record["host_time"] == host_time and marker in record["rendering"]
    ]
    assert len(matches) == 1, (host_time, marker)
    return matches[0]


def load_baseline(resolved: dict[str, Path]) -> list[dict[str, Any]]:
    with (CAMPAIGN / "results.csv").open(encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row["run_id"] == BASELINE_RUN_ID]
    assert len(rows) == 1
    row = rows[0]
    assert row["fault_mode"] == FAULT_MODE
    assert row["activation_confirmed"] == "True"
    assert row["detection_observed"] == "True"
    assert row["recovery_observed"] == "True"
    assert row["invalid_reason"] == ""

    g431_key = (
        "research/icsec2026/runs/full_20260830_seed20260830_n30/"
        f"raw/{BASELINE_RUN_ID}/g431.log"
    )
    g474_key = (
        "research/icsec2026/runs/full_20260830_seed20260830_n30/"
        f"raw/{BASELINE_RUN_ID}/g474.log"
    )
    g431 = read_raw(resolved[g431_key])
    g474 = read_raw(resolved[g474_key])
    find_raw(g474, row["activation_host_time"], "[PAYLOAD] MODE=BAD_CRC")
    find_raw(g431, row["detection_host_time"], row["detection_event"])
    find_raw(g474, row["restore_confirmation_host_time"], "[PAYLOAD] MODE=NORMAL")
    find_raw(g431, row["recovery_host_time"], "[OBC] PAYLOAD_RECOVERED")

    origin = row["injection_host_time"]
    events = [
        {
            "event_id": "fault_requested",
            "kind": "fault_request",
            "mode": FAULT_MODE,
            "relative_ms": 0.0,
            "source": "HOST",
        },
        {
            "event_id": "activation_confirmed",
            "kind": "payload_mode_confirmation",
            "mode": FAULT_MODE,
            "relative_ms": relative_ms(row["activation_host_time"], origin),
            "source": "PAYLOAD",
        },
        {
            "event_id": "detector_marker",
            "kind": "detector_marker",
            "marker": row["detection_event"],
            "relative_ms": relative_ms(row["detection_host_time"], origin),
            "source": "CONTROLLER",
        },
        {
            "event_id": "restore_requested",
            "kind": "restore_request",
            "mode": "NORMAL",
            "relative_ms": relative_ms(row["restore_command_host_time"], origin),
            "source": "HOST",
        },
        {
            "event_id": "restoration_confirmed",
            "kind": "payload_mode_confirmation",
            "mode": "NORMAL",
            "relative_ms": relative_ms(row["restore_confirmation_host_time"], origin),
            "source": "PAYLOAD",
        },
        {
            "event_id": "recovery_marker",
            "kind": "recovery_marker",
            "marker": "[OBC] PAYLOAD_RECOVERED",
            "relative_ms": relative_ms(row["recovery_host_time"], origin),
            "source": "CONTROLLER",
        },
    ]
    return events


def sorted_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(events, key=lambda event: (event["relative_ms"], event["event_id"]))


def event_report(event: dict[str, Any] | None) -> dict[str, Any]:
    if event is None:
        return {"confirmed": False, "event_id": None, "mode": None}
    return {"confirmed": True, "event_id": event["event_id"], "mode": event["mode"]}


def score_trace(trace: dict[str, Any]) -> dict[str, Any]:
    events = sorted_events(trace["events"])
    requests = [event for event in events if event["kind"] == "fault_request"]
    restores = [event for event in events if event["kind"] == "restore_request"]
    assert len(requests) == 1 and len(restores) == 1
    request = requests[0]
    restore = restores[0]
    assert request["relative_ms"] < restore["relative_ms"]

    in_fault_stage = [
        event
        for event in events
        if request["relative_ms"] < event["relative_ms"] < restore["relative_ms"]
    ]
    matching_activation = [
        event
        for event in in_fault_stage
        if event["kind"] == "payload_mode_confirmation"
        and event.get("mode") == request["mode"]
    ]
    wrong_activation = [
        event
        for event in in_fault_stage
        if event["kind"] == "payload_mode_confirmation"
        and event.get("mode") != request["mode"]
    ]
    activation = matching_activation[0] if matching_activation else None
    diagnostics: list[str] = []
    if wrong_activation:
        diagnostics.append("WRONG_MODE_ACTIVATION_CONFIRMATION")
    if activation is None:
        diagnostics.append("ACTIVATION_CONFIRMATION_MISSING")
    if len(matching_activation) > 1:
        diagnostics.append("DUPLICATE_ACTIVATION_CONFIRMATION")

    detectors = [event for event in in_fault_stage if event["kind"] == "detector_marker"]
    eligible_detectors: list[dict[str, Any]] = []
    if activation is None:
        detection_eligible = False
        detection_result = "UNSCORED"
        detection_event_id = None
        diagnostics.append("DETECTION_UNSCORED_NO_ACTIVATION")
    else:
        detection_eligible = True
        early_detectors = [
            event for event in detectors if event["relative_ms"] < activation["relative_ms"]
        ]
        if early_detectors:
            diagnostics.append("DETECTOR_BEFORE_ACTIVATION_IGNORED")
        eligible_detectors = [
            event for event in detectors if event["relative_ms"] >= activation["relative_ms"]
        ]
        if eligible_detectors:
            detection_result = "DETECTED"
            detection_event_id = eligible_detectors[0]["event_id"]
        else:
            detection_result = "NOT_DETECTED"
            detection_event_id = None
            diagnostics.append("NO_ELIGIBLE_DETECTOR_MARKER")

    after_restore = [
        event for event in events if event["relative_ms"] > restore["relative_ms"]
    ]
    matching_restoration = [
        event
        for event in after_restore
        if event["kind"] == "payload_mode_confirmation" and event.get("mode") == "NORMAL"
    ]
    restoration = matching_restoration[0] if matching_restoration else None
    if restoration is None:
        diagnostics.append("RESTORATION_CONFIRMATION_MISSING")
    if len(matching_restoration) > 1:
        diagnostics.append("DUPLICATE_RESTORATION_CONFIRMATION")

    if activation is None:
        recovery_eligible = False
        recovery_result = "UNSCORED"
        recovery_event_id = None
        diagnostics.append("RECOVERY_UNSCORED_NO_ACTIVATION")
    elif restoration is None:
        recovery_eligible = False
        recovery_result = "UNSCORED"
        recovery_event_id = None
        diagnostics.append("RECOVERY_UNSCORED_NO_RESTORATION")
    else:
        recovery_eligible = True
        eligible_recoveries = [
            event
            for event in after_restore
            if event["kind"] == "recovery_marker"
            and event["relative_ms"] >= restoration["relative_ms"]
        ]
        if eligible_recoveries:
            recovery_result = "RECOVERED"
            recovery_event_id = eligible_recoveries[0]["event_id"]
        else:
            recovery_result = "NOT_RECOVERED"
            recovery_event_id = None
            diagnostics.append("NO_ELIGIBLE_RECOVERY_MARKER")

    return {
        "activation_confirmation": event_report(activation),
        "detection": {
            "eligible": detection_eligible,
            "event_id": detection_event_id,
            "result": detection_result,
        },
        "diagnostic_codes": diagnostics,
        "recovery": {
            "eligible": recovery_eligible,
            "event_id": recovery_event_id,
            "result": recovery_result,
        },
        "restoration_confirmation": event_report(restoration),
    }


def make_trace(trace_id: str, operation: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "baseline_run_id": BASELINE_RUN_ID,
        "events": sorted_events(events),
        "fault_mode": FAULT_MODE,
        "mutation": operation,
        "schema": "washios.icsec2026.synthetic_trace_mutation.v1",
        "synthetic": True,
        "trace_id": trace_id,
    }


def create_mutations(baseline: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    traces: dict[str, dict[str, Any]] = {}

    events = [event for event in copy.deepcopy(baseline) if event["event_id"] != "activation_confirmed"]
    traces["missing_activation_confirmation"] = make_trace(
        "missing_activation_confirmation",
        "remove the matching BAD_CRC payload confirmation",
        events,
    )

    events = [event for event in copy.deepcopy(baseline) if event["event_id"] != "restoration_confirmed"]
    traces["missing_restoration_confirmation"] = make_trace(
        "missing_restoration_confirmation",
        "remove the matching NORMAL restoration confirmation after valid activation",
        events,
    )

    events = copy.deepcopy(baseline)
    activation = next(event for event in events if event["event_id"] == "activation_confirmed")
    activation["event_id"] = "wrong_mode_activation_confirmation"
    activation["mode"] = "SILENT"
    traces["wrong_mode_activation_confirmation"] = make_trace(
        "wrong_mode_activation_confirmation",
        "replace the BAD_CRC activation confirmation with a SILENT confirmation",
        events,
    )

    events = copy.deepcopy(baseline)
    activation = next(event for event in events if event["event_id"] == "activation_confirmed")
    detector = next(event for event in events if event["event_id"] == "detector_marker")
    detector["relative_ms"] = round(activation["relative_ms"] / 2.0, 6)
    traces["detector_before_activation_confirmation"] = make_trace(
        "detector_before_activation_confirmation",
        "move the detector marker before the matching activation confirmation",
        events,
    )

    events = copy.deepcopy(baseline)
    activation = next(event for event in events if event["event_id"] == "activation_confirmed")
    duplicate = copy.deepcopy(activation)
    duplicate["event_id"] = "activation_confirmed_duplicate"
    duplicate["relative_ms"] = round(activation["relative_ms"] + 0.001, 6)
    events.append(duplicate)
    traces["duplicate_matching_confirmation"] = make_trace(
        "duplicate_matching_confirmation",
        "insert one duplicate matching BAD_CRC activation confirmation",
        events,
    )

    assert len(traces) == 5
    return traces


def confirmation(confirmed: bool, event_id: str | None, mode: str | None) -> dict[str, Any]:
    return {"confirmed": confirmed, "event_id": event_id, "mode": mode}


def expected_outcomes() -> dict[str, dict[str, Any]]:
    confirmed_activation = confirmation(True, "activation_confirmed", "BAD_CRC")
    confirmed_restoration = confirmation(True, "restoration_confirmed", "NORMAL")
    no_confirmation = confirmation(False, None, None)
    return {
        "detector_before_activation_confirmation": {
            "activation_confirmation": confirmed_activation,
            "detection": {"eligible": True, "event_id": None, "result": "NOT_DETECTED"},
            "diagnostic_codes": [
                "DETECTOR_BEFORE_ACTIVATION_IGNORED",
                "NO_ELIGIBLE_DETECTOR_MARKER",
            ],
            "recovery": {"eligible": True, "event_id": "recovery_marker", "result": "RECOVERED"},
            "restoration_confirmation": confirmed_restoration,
        },
        "duplicate_matching_confirmation": {
            "activation_confirmation": confirmed_activation,
            "detection": {"eligible": True, "event_id": "detector_marker", "result": "DETECTED"},
            "diagnostic_codes": ["DUPLICATE_ACTIVATION_CONFIRMATION"],
            "recovery": {"eligible": True, "event_id": "recovery_marker", "result": "RECOVERED"},
            "restoration_confirmation": confirmed_restoration,
        },
        "missing_activation_confirmation": {
            "activation_confirmation": no_confirmation,
            "detection": {"eligible": False, "event_id": None, "result": "UNSCORED"},
            "diagnostic_codes": [
                "ACTIVATION_CONFIRMATION_MISSING",
                "DETECTION_UNSCORED_NO_ACTIVATION",
                "RECOVERY_UNSCORED_NO_ACTIVATION",
            ],
            "recovery": {"eligible": False, "event_id": None, "result": "UNSCORED"},
            "restoration_confirmation": confirmed_restoration,
        },
        "missing_restoration_confirmation": {
            "activation_confirmation": confirmed_activation,
            "detection": {"eligible": True, "event_id": "detector_marker", "result": "DETECTED"},
            "diagnostic_codes": [
                "RESTORATION_CONFIRMATION_MISSING",
                "RECOVERY_UNSCORED_NO_RESTORATION",
            ],
            "recovery": {"eligible": False, "event_id": None, "result": "UNSCORED"},
            "restoration_confirmation": no_confirmation,
        },
        "wrong_mode_activation_confirmation": {
            "activation_confirmation": no_confirmation,
            "detection": {"eligible": False, "event_id": None, "result": "UNSCORED"},
            "diagnostic_codes": [
                "WRONG_MODE_ACTIVATION_CONFIRMATION",
                "ACTIVATION_CONFIRMATION_MISSING",
                "DETECTION_UNSCORED_NO_ACTIVATION",
                "RECOVERY_UNSCORED_NO_ACTIVATION",
            ],
            "recovery": {"eligible": False, "event_id": None, "result": "UNSCORED"},
            "restoration_confirmation": confirmed_restoration,
        },
    }


def main() -> int:
    resolved = resolve_sources()
    before = snapshot_sources(resolved)
    summary = json.loads((CAMPAIGN / "summary.json").read_text(encoding="utf-8"))
    assert sum(item["planned_trials"] for item in summary["faults"].values()) == 90
    assert all(item["valid_trials"] == 30 for item in summary["faults"].values())

    baseline = load_baseline(resolved)
    traces = create_mutations(baseline)
    expected = expected_outcomes()
    actual = {trace_id: score_trace(trace) for trace_id, trace in traces.items()}

    mutation_dir = HERE / "mutations"
    mutation_dir.mkdir(exist_ok=True)
    mutation_paths = {
        "missing_activation_confirmation": "mutations/01_missing_activation_confirmation.json",
        "missing_restoration_confirmation": "mutations/02_missing_restoration_confirmation.json",
        "wrong_mode_activation_confirmation": "mutations/03_wrong_mode_activation_confirmation.json",
        "detector_before_activation_confirmation": "mutations/04_detector_before_activation_confirmation.json",
        "duplicate_matching_confirmation": "mutations/05_duplicate_matching_confirmation.json",
    }
    for trace_id, relative in mutation_paths.items():
        write_json(HERE / relative, traces[trace_id])
    assert len(list(mutation_dir.glob("*.json"))) == 5

    manifest = {
        "baseline": {
            "fault_mode": FAULT_MODE,
            "run_id": BASELINE_RUN_ID,
            "source_logs": [
                "research/icsec2026/runs/full_20260830_seed20260830_n30/raw/R005_P02/g431.log",
                "research/icsec2026/runs/full_20260830_seed20260830_n30/raw/R005_P02/g474.log",
            ],
            "source_result": "research/icsec2026/runs/full_20260830_seed20260830_n30/results.csv#R005_P02",
        },
        "mutation_count": 5,
        "mutations": [
            {
                "operation": traces[trace_id]["mutation"],
                "path": mutation_paths[trace_id],
                "trace_id": trace_id,
            }
            for trace_id in mutation_paths
        ],
        "schema": "washios.icsec2026.synthetic_mutation_manifest.v1",
    }
    write_json(HERE / "mutation_manifest.json", manifest)
    write_json(HERE / "expected_outcomes.json", expected)
    write_json(HERE / "actual_outcomes.json", actual)

    scenario_assertions = {
        trace_id: {
            "actual_equals_expected": actual[trace_id] == expected[trace_id],
            "pass": actual[trace_id] == expected[trace_id],
        }
        for trace_id in sorted(traces)
    }
    after = snapshot_sources(resolved)
    unchanged = before == after
    assertion_record = {
        "assertion_count": len(scenario_assertions) + 3,
        "assertions": {
            "all_expected_outcomes_matched": all(
                item["pass"] for item in scenario_assertions.values()
            ),
            "all_original_sources_unchanged": unchanged,
            "exactly_five_mutations": len(traces) == 5
            and len(list(mutation_dir.glob("*.json"))) == 5,
        },
        "overall_pass": unchanged
        and len(traces) == 5
        and all(item["pass"] for item in scenario_assertions.values()),
        "scenario_assertions": scenario_assertions,
        "schema": "washios.icsec2026.synthetic_replay_assertions.v1",
    }
    write_json(HERE / "automated_assertions.json", assertion_record)

    source_record = {
        "all_sources_unchanged": unchanged,
        "baseline_run_id": BASELINE_RUN_ID,
        "frozen_90_trial_summary_sha256": EXPECTED_SOURCE_HASHES[
            "research/icsec2026/runs/full_20260830_seed20260830_n30/summary.json"
        ],
        "post_execution": after,
        "pre_execution": before,
        "schema": "washios.icsec2026.synthetic_replay_source_hashes.v1",
    }
    write_json(HERE / "source_hashes.json", source_record)

    derived = [
        "trace_replay.py",
        "mutation_manifest.json",
        "expected_outcomes.json",
        "actual_outcomes.json",
        "automated_assertions.json",
        "source_hashes.json",
        *mutation_paths.values(),
    ]
    with (HERE / "derived_hashes.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("sha256", "bytes", "path"))
        writer.writeheader()
        for relative in derived:
            path = HERE / relative
            writer.writerow(
                {"sha256": sha256(path), "bytes": path.stat().st_size, "path": relative}
            )

    assert assertion_record["overall_pass"]
    print("TRACE_REPLAY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
