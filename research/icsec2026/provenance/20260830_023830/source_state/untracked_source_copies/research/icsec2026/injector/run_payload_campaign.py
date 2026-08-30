#!/usr/bin/env python3
"""Run repeatable G431/G474 payload fault-injection campaigns.

Raw log format is one host record per received serial line:
    <UTC ISO-8601>\t<exact received bytes as hex>\t<escaped ASCII rendering>

The hex field is authoritative and preserves the exact received bytes, including
line terminators. The rendering is provided only for inspection and marker matching.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import datetime as dt
import json
import random
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Iterable, TextIO


FAULTS = (
    ("P01", "SILENT"),
    ("P02", "BAD_CRC"),
    ("P03", "DELAYED"),
)

RESULT_FIELDS = (
    "run_id",
    "fault_id",
    "fault_mode",
    "seed",
    "activation_confirmed",
    "activation_host_time",
    "injection_host_time",
    "detection_observed",
    "detection_event",
    "detection_host_time",
    "detection_latency_ms",
    "offline_observed",
    "restore_command_host_time",
    "restore_confirmation_host_time",
    "recovery_observed",
    "recovery_host_time",
    "recovery_time_ms",
    "controller_restart_marker_observed",
    "outcome",
    "invalid_reason",
)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds")


def repository_commit(repo_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


@dataclasses.dataclass(frozen=True)
class RunPlanEntry:
    run_id: str
    fault_id: str
    fault_mode: str
    order_index: int
    pre_injection_offset_s: float


def generate_run_plan(
    seed: int,
    repetitions: int,
    offset_min_s: float,
    offset_max_s: float,
) -> list[RunPlanEntry]:
    if repetitions < 1:
        raise ValueError("repetitions must be at least 1")
    if offset_min_s < 0.0 or offset_max_s < offset_min_s:
        raise ValueError("invalid pre-injection offset range")

    rng = random.Random(seed)
    ordered_faults = list(FAULTS) * repetitions
    rng.shuffle(ordered_faults)
    plan = []
    for index, (fault_id, fault_mode) in enumerate(ordered_faults, start=1):
        plan.append(
            RunPlanEntry(
                run_id=f"R{index:03d}_{fault_id}",
                fault_id=fault_id,
                fault_mode=fault_mode,
                order_index=index,
                pre_injection_offset_s=round(
                    rng.uniform(offset_min_s, offset_max_s), 3
                ),
            )
        )
    return plan


@dataclasses.dataclass(frozen=True)
class SerialEvent:
    source: str
    host_time: str
    monotonic_s: float
    raw: bytes
    text: str


def escaped_rendering(raw: bytes) -> str:
    rendered = []
    for byte in raw:
        if 0x20 <= byte <= 0x7E and byte != 0x5C:
            rendered.append(chr(byte))
        elif byte == 0x5C:
            rendered.append("\\\\")
        elif byte == 0x0D:
            rendered.append("\\r")
        elif byte == 0x0A:
            rendered.append("\\n")
        else:
            rendered.append(f"\\x{byte:02x}")
    return "".join(rendered)


class SerialCapture:
    def __init__(self, source: str, serial_port: object):
        self.source = source
        self.serial_port = serial_port
        self._condition = threading.Condition()
        self._events: list[SerialEvent] = []
        self._log: TextIO | None = None
        self._pending = bytearray()
        self._stop = False
        self._error: str | None = None
        self._thread = threading.Thread(
            target=self._reader, name=f"capture-{source}", daemon=True
        )

    def start(self) -> None:
        self._thread.start()

    def attach_log(self, log_file: TextIO) -> None:
        with self._condition:
            if self._log is not None:
                raise RuntimeError(f"{self.source} log already attached")
            self._log = log_file

    def detach_log(self) -> None:
        with self._condition:
            self._flush_pending_locked()
            if self._log is not None:
                self._log.flush()
            self._log = None

    def snapshot(self) -> int:
        with self._condition:
            return len(self._events)

    def events_since(self, index: int) -> list[SerialEvent]:
        with self._condition:
            return list(self._events[index:])

    def wait_for(
        self,
        predicate: Callable[[SerialEvent], bool],
        after_index: int,
        timeout_s: float,
    ) -> SerialEvent | None:
        deadline = time.monotonic() + timeout_s
        with self._condition:
            while True:
                for event in self._events[after_index:]:
                    if predicate(event):
                        return event
                remaining = deadline - time.monotonic()
                if remaining <= 0.0:
                    return None
                self._condition.wait(remaining)

    def stop(self) -> None:
        self._stop = True
        self._thread.join(timeout=2.0)
        with self._condition:
            self._flush_pending_locked()

    def assert_healthy(self) -> None:
        with self._condition:
            if self._error is not None:
                raise RuntimeError(f"{self.source} serial capture failed: {self._error}")
            if not self._thread.is_alive() and not self._stop:
                raise RuntimeError(f"{self.source} serial capture stopped unexpectedly")

    def _reader(self) -> None:
        try:
            while not self._stop:
                data = self.serial_port.read(64)
                if not data:
                    continue
                with self._condition:
                    self._pending.extend(data)
                    while True:
                        newline = self._pending.find(b"\n")
                        if newline < 0:
                            break
                        raw = bytes(self._pending[: newline + 1])
                        del self._pending[: newline + 1]
                        self._record_locked(raw)
        except Exception as exc:
            with self._condition:
                self._error = f"{type(exc).__name__}: {exc}"
                self._condition.notify_all()

    def _flush_pending_locked(self) -> None:
        if self._pending:
            raw = bytes(self._pending)
            self._pending.clear()
            self._record_locked(raw)

    def _record_locked(self, raw: bytes) -> None:
        event = SerialEvent(
            source=self.source,
            host_time=utc_now(),
            monotonic_s=time.monotonic(),
            raw=raw,
            text=raw.decode("ascii", errors="backslashreplace").rstrip("\r\n"),
        )
        self._events.append(event)
        if self._log is not None:
            self._log.write(
                f"{event.host_time}\t{raw.hex()}\t{escaped_rendering(raw)}\n"
            )
            self._log.flush()
        self._condition.notify_all()


class CampaignStore:
    def __init__(
        self,
        runs_root: Path,
        campaign: str,
        manifest: dict[str, object],
        plan: Iterable[RunPlanEntry],
    ):
        self.campaign_dir = runs_root / campaign
        self.raw_dir = self.campaign_dir / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=False)
        self.manifest_path = self.campaign_dir / "manifest.json"
        self.plan_path = self.campaign_dir / "run_plan.csv"
        self.results_path = self.campaign_dir / "results.csv"
        self.manifest = manifest
        self._write_manifest()
        with self.plan_path.open("x", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=[field.name for field in dataclasses.fields(RunPlanEntry)])
            writer.writeheader()
            for entry in plan:
                writer.writerow(dataclasses.asdict(entry))
        with self.results_path.open("x", newline="", encoding="utf-8") as handle:
            csv.DictWriter(handle, fieldnames=RESULT_FIELDS).writeheader()

    def open_run_logs(self, run_id: str) -> tuple[TextIO, TextIO]:
        run_dir = self.raw_dir / run_id
        run_dir.mkdir(exist_ok=False)
        return (
            (run_dir / "g431.log").open("x", encoding="ascii", newline="\n"),
            (run_dir / "g474.log").open("x", encoding="ascii", newline="\n"),
        )

    def append_result(self, result: dict[str, object]) -> None:
        with self.results_path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS)
            writer.writerow({field: result.get(field, "") for field in RESULT_FIELDS})
            handle.flush()

    def record_state(self, run_id: str, state: str) -> None:
        history = self.manifest.setdefault("state_history", [])
        assert isinstance(history, list)
        history.append({"host_time": utc_now(), "run_id": run_id, "state": state})
        self._write_manifest()
        print(f"[{utc_now()}] {run_id} {state}", flush=True)

    def finalize(self, status: str) -> None:
        self.manifest["status"] = status
        self.manifest["finished_host_time"] = utc_now()
        self._write_manifest()

    def _write_manifest(self) -> None:
        temporary = self.manifest_path.with_suffix(".json.tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(self.manifest, handle, indent=2, sort_keys=True)
            handle.write("\n")
        temporary.replace(self.manifest_path)


def first_event(
    events: Iterable[SerialEvent], predicate: Callable[[SerialEvent], bool]
) -> SerialEvent | None:
    return next((event for event in events if predicate(event)), None)


def detection_event(fault_mode: str, events: Iterable[SerialEvent]) -> SerialEvent | None:
    if fault_mode == "BAD_CRC":
        return first_event(events, lambda event: "[OBC] PAYLOAD_REJECT reason=CRC" in event.text)
    if fault_mode in ("SILENT", "DELAYED"):
        return first_event(
            events,
            lambda event: "[OBC] PAYLOAD_TIMEOUT" in event.text
            or "[OBC] PAYLOAD_OFFLINE" in event.text,
        )
    raise ValueError(f"unknown fault mode: {fault_mode}")


def send_mode(serial_port: object, mode: str) -> tuple[str, float]:
    host_time = utc_now()
    monotonic_s = time.monotonic()
    serial_port.write(f"MODE {mode}\n".encode("ascii"))
    serial_port.flush()
    return host_time, monotonic_s


def wait_mode_confirmation(
    capture: SerialCapture, mode: str, after_index: int, timeout_s: float
) -> SerialEvent | None:
    marker = f"[PAYLOAD] MODE={mode}"
    return capture.wait_for(lambda event: marker in event.text, after_index, timeout_s)


def blank_result(entry: RunPlanEntry, seed: int) -> dict[str, object]:
    result = {field: "" for field in RESULT_FIELDS}
    result.update(
        {
            "run_id": entry.run_id,
            "fault_id": entry.fault_id,
            "fault_mode": entry.fault_mode,
            "seed": seed,
            "activation_confirmed": False,
            "detection_observed": False,
            "offline_observed": False,
            "recovery_observed": False,
            "controller_restart_marker_observed": False,
            "outcome": "INVALID",
        }
    )
    return result


def run_one(
    entry: RunPlanEntry,
    seed: int,
    store: CampaignStore,
    g431: SerialCapture,
    g474: SerialCapture,
    g474_serial: object,
    confirm_timeout_s: float,
    precondition_observe_s: float,
    observe_s: float,
    recovery_observe_s: float,
) -> dict[str, object]:
    result = blank_result(entry, seed)
    g431_log, g474_log = store.open_run_logs(entry.run_id)
    g431.attach_log(g431_log)
    g474.attach_log(g474_log)
    run_g431_start = g431.snapshot()

    try:
        g431.assert_healthy()
        g474.assert_healthy()
        store.record_state(entry.run_id, "PRECONDITION_NORMAL")
        normal_start = g474.snapshot()
        send_mode(g474_serial, "NORMAL")
        if wait_mode_confirmation(g474, "NORMAL", normal_start, confirm_timeout_s) is None:
            result["invalid_reason"] = "PRECONDITION_NORMAL_NOT_CONFIRMED"
            return result
        time.sleep(precondition_observe_s)
        g431.assert_healthy()
        g474.assert_healthy()

        store.record_state(entry.run_id, "WAIT_RANDOM_OFFSET")
        time.sleep(entry.pre_injection_offset_s)
        g431.assert_healthy()
        g474.assert_healthy()

        store.record_state(entry.run_id, "INJECT")
        activation_start = g474.snapshot()
        injection_time, injection_mono = send_mode(g474_serial, entry.fault_mode)
        result["injection_host_time"] = injection_time

        store.record_state(entry.run_id, "CONFIRM_ACTIVATION")
        activation = wait_mode_confirmation(
            g474, entry.fault_mode, activation_start, confirm_timeout_s
        )
        if activation is None:
            result["invalid_reason"] = "FAULT_ACTIVATION_NOT_CONFIRMED"
        else:
            result["activation_confirmed"] = True
            result["activation_host_time"] = activation.host_time

        store.record_state(entry.run_id, "OBSERVE")
        time.sleep(observe_s)
        g431.assert_healthy()
        g474.assert_healthy()

        store.record_state(entry.run_id, "RESTORE_NORMAL")
        restore_start = g474.snapshot()
        restore_time, restore_mono = send_mode(g474_serial, "NORMAL")
        result["restore_command_host_time"] = restore_time
        restore_confirmation = wait_mode_confirmation(
            g474, "NORMAL", restore_start, confirm_timeout_s
        )
        if restore_confirmation is not None:
            result["restore_confirmation_host_time"] = restore_confirmation.host_time
        elif not result["invalid_reason"]:
            result["invalid_reason"] = "NORMAL_RESTORE_NOT_CONFIRMED"

        store.record_state(entry.run_id, "OBSERVE_RECOVERY")
        time.sleep(recovery_observe_s)
        g431.assert_healthy()
        g474.assert_healthy()

        g431_events = g431.events_since(run_g431_start)
        if not g431_events and not result["invalid_reason"]:
            result["invalid_reason"] = "G431_NO_SERIAL_LINES"
        post_injection = [event for event in g431_events if event.monotonic_s >= injection_mono]
        detected = detection_event(entry.fault_mode, post_injection)
        offline = first_event(post_injection, lambda event: "[OBC] PAYLOAD_OFFLINE" in event.text)
        recovered = first_event(
            post_injection,
            lambda event: event.monotonic_s >= restore_mono
            and "[OBC] PAYLOAD_RECOVERED" in event.text,
        )
        restart = first_event(
            post_injection, lambda event: "[OBC] PAYLOAD_LINK_START" in event.text
        )

        if detected is not None:
            result["detection_observed"] = True
            result["detection_event"] = detected.text
            result["detection_host_time"] = detected.host_time
            result["detection_latency_ms"] = round(
                (detected.monotonic_s - injection_mono) * 1000.0, 3
            )
        result["offline_observed"] = offline is not None
        if recovered is not None:
            result["recovery_observed"] = True
            result["recovery_host_time"] = recovered.host_time
            if restore_confirmation is not None:
                result["recovery_time_ms"] = round(
                    (recovered.monotonic_s - restore_mono) * 1000.0, 3
                )
        result["controller_restart_marker_observed"] = restart is not None

        if result["invalid_reason"]:
            result["outcome"] = "INVALID"
        elif detected is None:
            result["outcome"] = "NO_DETECTION_OBSERVED"
        elif recovered is not None:
            result["outcome"] = "DETECTED_RECOVERY_OBSERVED"
        else:
            result["outcome"] = "DETECTED_NO_RECOVERY_MARKER"
        return result
    finally:
        store.record_state(entry.run_id, "FINALIZE")
        g431.detach_log()
        g474.detach_log()
        g431_log.close()
        g474_log.close()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", required=True, help="new, unique campaign directory name")
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--g431-port", required=True)
    parser.add_argument("--g474-port", required=True)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--offset-min-s", type=float, default=0.25)
    parser.add_argument("--offset-max-s", type=float, default=1.25)
    parser.add_argument("--confirm-timeout-s", type=float, default=3.0)
    parser.add_argument("--precondition-observe-s", type=float, default=1.5)
    parser.add_argument("--observe-s", type=float, default=4.0)
    parser.add_argument("--recovery-observe-s", type=float, default=3.0)
    parser.add_argument("--baud", type=int, default=115200)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.g431_port.upper() == args.g474_port.upper():
        raise SystemExit("G431 and G474 ports must be different")

    try:
        import serial  # type: ignore[import-not-found]
    except ImportError as exc:
        raise SystemExit(
            "pyserial is required for hardware runs; install with: python -m pip install pyserial"
        ) from exc

    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[3]
    runs_root = script_path.parents[1] / "runs"
    plan = generate_run_plan(
        args.seed, args.repetitions, args.offset_min_s, args.offset_max_s
    )
    manifest: dict[str, object] = {
        "schema_version": 1,
        "campaign": args.campaign,
        "status": "RUNNING",
        "started_host_time": utc_now(),
        "branch_commit": repository_commit(repo_root),
        "seed": args.seed,
        "g431_port": args.g431_port,
        "g474_port": args.g474_port,
        "baud": args.baud,
        "repetitions": args.repetitions,
        "timing": {
            "offset_min_s": args.offset_min_s,
            "offset_max_s": args.offset_max_s,
            "confirm_timeout_s": args.confirm_timeout_s,
            "precondition_observe_s": args.precondition_observe_s,
            "observe_s": args.observe_s,
            "recovery_observe_s": args.recovery_observe_s,
        },
        "raw_log_format": "utc_iso8601<TAB>raw_hex<TAB>escaped_ascii",
        "measurement_definitions": {
            "activation": "G474 [PAYLOAD] MODE=<fault> confirmation",
            "silent_detection": "first G431 PAYLOAD_TIMEOUT or PAYLOAD_OFFLINE after injection",
            "bad_crc_detection": "first G431 PAYLOAD_REJECT reason=CRC after injection",
            "delayed_detection": "first G431 PAYLOAD_TIMEOUT or PAYLOAD_OFFLINE after injection; based on inspected 250 ms responder delay and 100 ms controller deadline",
            "recovery_time_ms": "G431 PAYLOAD_RECOVERED host time minus MODE NORMAL command-send host time; only populated when NORMAL confirmation is also observed",
            "restart_marker": "G431 PAYLOAD_LINK_START after injection; absence is not proof that no MCU reset occurred",
        },
        "literal_status_warning": "heartbeat=OK watchdog=OK are literal status strings and are not independently measured states",
    }
    store = CampaignStore(runs_root, args.campaign, manifest, plan)

    g431_serial = serial.Serial(args.g431_port, args.baud, timeout=0.05, write_timeout=1.0)
    try:
        g474_serial = serial.Serial(args.g474_port, args.baud, timeout=0.05, write_timeout=1.0)
    except Exception:
        g431_serial.close()
        raise

    g431 = SerialCapture("g431", g431_serial)
    g474 = SerialCapture("g474", g474_serial)
    g431.start()
    g474.start()
    status = "COMPLETE"
    try:
        for entry in plan:
            try:
                result = run_one(
                    entry,
                    args.seed,
                    store,
                    g431,
                    g474,
                    g474_serial,
                    args.confirm_timeout_s,
                    args.precondition_observe_s,
                    args.observe_s,
                    args.recovery_observe_s,
                )
            except Exception as exc:
                result = blank_result(entry, args.seed)
                result["invalid_reason"] = f"HARNESS_EXCEPTION:{type(exc).__name__}"
                store.append_result(result)
                raise
            store.append_result(result)
            if result["invalid_reason"]:
                status = f"ABORTED_{result['invalid_reason']}"
                break
    except KeyboardInterrupt:
        status = "INTERRUPTED"
        raise
    except Exception:
        status = "FAILED"
        raise
    finally:
        store.finalize(status)
        g431.stop()
        g474.stop()
        g431_serial.close()
        g474_serial.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
