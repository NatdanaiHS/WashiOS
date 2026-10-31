#!/usr/bin/env python3
"""Camera-ready Part B lab helper: run directories, logic-analyzer capture, analysis.

Subcommands
  new      create a new, exclusively named evidence directory
  check    check that sigrok-cli and the analyzer are visible
  capture  record the logic analyzer (and optional serial consoles) into a run
  analyze  compute B1/B2/B5/B6/B3 timing from a run's capture.vcd
  close    write the run's SHA-256 inventory and mark it closed

See RUNBOOK.md in this directory for the full procedure.
"""

from __future__ import annotations

import argparse
import bisect
import datetime as dt
import hashlib
import json
import os
import shutil
import statistics
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUNS = HERE / "runs"

# Logic-analyzer channel maps. Keys are analyzer inputs (D0..D7), values are
# the signal names the analysis uses. See RUNBOOK.md for the physical wiring.
SETUPS = {
    # B1, B2, B5, B6: one wiring for the whole first session.
    "A": {
        "D0": "poll",       # G431 D2  / PA10 toggle per poll sent
        "D1": "loop",       # G431 D4  / PB5  toggle per PayloadLinkTask loop
        "D2": "status",     # G431 D5  / PB4  high during reportStatus()
        "D3": "write",      # G431 D6  / PB10 high during writeLine()
        "D4": "accept",     # G431 D8  / PA9  toggle per accepted response
        "D5": "timeout",    # G431 D7  / PA8  rises on each timeout detection
        "D6": "recovery",   # G431 D9  / PC7  toggle per PAYLOAD_RECOVERED
        "D7": "pl_fault",   # G474 D8  / PA9  high while a fault mode is applied
    },
    # B3: watchdog stall injection.
    "B": {
        "D0": "stall",      # G431 D10 / PB6  rises when the stall begins
        "D1": "wdrec",      # G431 D11 / PA7  rises at the WATCHDOG_TIMEOUT record
        "D2": "nrst",       # G431 NRST (CN6 pin 3 "RESET") low pulse on reset
        "D3": "led",        # G431 D13 / PA5  heartbeat LED / bootloader beacon
        "D4": "loop",       # G431 D4  / PB5  toggles only while the app runs
    },
}

FIRMWARE = [
    "core/.pio/build/nucleo_g431rb_payload_demo_lab/firmware.elf",
    "core/.pio/build/nucleo_g431rb_payload_demo_stall_link/firmware.elf",
    "core/.pio/build/nucleo_g431rb_payload_demo_stall_heartbeat/firmware.elf",
    "core/.pio/build/nucleo_g431rb_payload_demo_lab_slot_b/firmware.elf",
    "bootloader/.pio/build/nucleo_g431rb_payload_demo_lab/firmware.elf",
    "bootloader/.pio/build/nucleo_g431rb_payload_demo_stall_link/firmware.elf",
    "bootloader/.pio/build/nucleo_g431rb_payload_demo_stall_heartbeat/firmware.elf",
    "demo-payload/.pio/build/nucleo_g474re_lab/firmware.elf",
]

SIGROK_CANDIDATES = [
    r"C:\Program Files\sigrok\sigrok-cli\sigrok-cli.exe",
    r"C:\Program Files (x86)\sigrok\sigrok-cli\sigrok-cli.exe",
]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def git(*args: str) -> str:
    result = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True)
    return result.stdout.strip()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def resolve_run(name: str) -> Path:
    path = Path(name)
    if not path.is_absolute():
        path = RUNS / name if (RUNS / name).exists() else Path.cwd() / name
    if not (path / "manifest.json").exists():
        raise SystemExit(f"not a run directory (no manifest.json): {path}")
    return path


def ensure_open(run: Path) -> dict:
    manifest = load_json(run / "manifest.json")
    if manifest.get("status") == "CLOSED":
        raise SystemExit(f"{run.name} is closed; create a new run instead of reusing it")
    return manifest


# --------------------------------------------------------------------------- new

def cmd_new(args: argparse.Namespace) -> int:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    label = "".join(c if c.isalnum() or c in "-_" else "-" for c in args.label)
    run = RUNS / f"{stamp}_{args.test}_{label}"
    run.mkdir(parents=True, exist_ok=False)
    firmware = {}
    for rel in FIRMWARE:
        path = REPO / rel
        if path.exists():
            firmware[rel] = sha256_file(path)
    write_json(run / "manifest.json", {
        "status": "OPEN",
        "test": args.test,
        "label": args.label,
        "created_utc": utc_now(),
        "git_commit": git("rev-parse", "HEAD"),
        "git_branch": git("branch", "--show-current"),
        "git_status_porcelain": git("status", "--porcelain=v1"),
        "firmware_sha256_at_create": firmware,
        "flashed": args.flashed or "",
        "notes": [],
    })
    print(run)
    return 0


# ----------------------------------------------------------------------- capture

def find_sigrok() -> str:
    found = shutil.which("sigrok-cli")
    if found:
        return found
    for candidate in SIGROK_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    raise SystemExit("sigrok-cli not found. Install it (RUNBOOK.md, step 0.3) and retry.")


def cmd_check(args: argparse.Namespace) -> int:
    sigrok = find_sigrok()
    print(f"sigrok-cli: {sigrok}")
    result = subprocess.run([sigrok, "--scan"], capture_output=True, text=True)
    print(result.stdout or result.stderr)
    if "fx2lafw" not in (result.stdout + result.stderr):
        print("No fx2lafw analyzer found. Check the USB cable and the Zadig driver (RUNBOOK.md 0.4).")
        return 1
    print("Analyzer OK.")
    return 0


def log_serial(port: str, name: str, run: Path, stop: threading.Event) -> None:
    import serial  # type: ignore[import-not-found]

    out = run / f"serial_{name}.log"
    with serial.Serial(port, 115200, timeout=0.05) as link, out.open("x", encoding="utf-8") as log:
        pending = b""
        while not stop.is_set():
            chunk = link.read(256)
            if not chunk:
                continue
            pending += chunk
            while b"\n" in pending:
                line, pending = pending.split(b"\n", 1)
                log.write(f"{utc_now()}\t{line.decode('ascii', 'replace').rstrip()}\n")
                log.flush()


def cmd_capture(args: argparse.Namespace) -> int:
    run = resolve_run(args.run)
    manifest = ensure_open(run)
    out = run / "capture.vcd"
    if out.exists():
        raise SystemExit(f"{out} already exists; each run holds one capture. Make a new run.")
    channels = SETUPS[args.setup]
    sigrok = find_sigrok()
    command = [
        sigrok, "-d", "fx2lafw",
        "--config", f"samplerate={args.rate}",
        "-C", ",".join(f"{pin}={name}" for pin, name in channels.items()),
        "--time", str(int(args.seconds * 1000)),
        "-O", "vcd", "-o", str(out),
    ]

    stop = threading.Event()
    threads = []
    for spec in args.serial or []:
        port, _, name = spec.partition(":")
        thread = threading.Thread(target=log_serial, args=(port, name or port, run, stop), daemon=True)
        thread.start()
        threads.append(thread)

    manifest.setdefault("captures", []).append({
        "setup": args.setup,
        "channels": channels,
        "samplerate": args.rate,
        "seconds": args.seconds,
        "serial": args.serial or [],
        "command": command,
        "start_utc": utc_now(),
    })
    write_json(run / "manifest.json", manifest)
    print(f"Recording {args.seconds:.0f} s at {args.rate} into {out}")
    print("Do not unplug the analyzer. Ctrl+C stops early (the file is kept).")
    started = time.monotonic()
    try:
        code = subprocess.call(command)
    except KeyboardInterrupt:
        code = -2
    stop.set()
    for thread in threads:
        thread.join(timeout=2)
    manifest = load_json(run / "manifest.json")
    manifest["captures"][-1].update({
        "end_utc": utc_now(),
        "elapsed_s": round(time.monotonic() - started, 3),
        "sigrok_exit_code": code,
    })
    write_json(run / "manifest.json", manifest)
    print(f"sigrok-cli exit code {code}; captured {out.stat().st_size if out.exists() else 0} bytes")
    return 0 if code == 0 else 1


# ------------------------------------------------------------------------- VCD

def read_vcd(path: Path) -> tuple[dict[str, list[tuple[float, int]]], float]:
    """Return {signal: [(time_s, level), ...]} including the initial level, and the end time."""
    scale = {"s": 1.0, "ms": 1e-3, "us": 1e-6, "ns": 1e-9, "ps": 1e-12}
    timescale = 1e-6
    ids: dict[str, str] = {}
    changes: dict[str, list[tuple[float, int]]] = {}
    now = 0.0
    header = True
    pending_ts = ""
    with path.open("r", encoding="ascii", errors="replace") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            if header:
                if pending_ts or line.startswith("$timescale"):
                    pending_ts += " " + line
                    if "$end" in line:
                        text = pending_ts.replace("$timescale", "").replace("$end", "").strip()
                        number = "".join(c for c in text if c.isdigit()) or "1"
                        unit = "".join(c for c in text if c.isalpha())
                        timescale = int(number) * scale[unit]
                        pending_ts = ""
                    continue
                if line.startswith("$var"):
                    parts = line.split()
                    ids[parts[3]] = parts[4]
                    changes.setdefault(parts[4], [])
                    continue
                if line.startswith("$enddefinitions"):
                    header = False
                continue
            if line[0] == "#":
                now = int(line[1:].split()[0]) * timescale
                # sigrok can put values on the same line as the timestamp
                rest = line.split()[1:]
                for token in rest:
                    _apply(token, now, ids, changes)
                continue
            if line.startswith("$"):
                continue
            _apply(line, now, ids, changes)
    return changes, now


def _apply(token: str, now: float, ids: dict[str, str], changes: dict[str, list[tuple[float, int]]]) -> None:
    if token[0] in "01" and token[1:] in ids:
        name = ids[token[1:]]
        level = int(token[0])
        series = changes[name]
        if not series or series[-1][1] != level:
            series.append((now, level))


def edges(series: list[tuple[float, int]], kind: str = "any") -> list[float]:
    """Times of real transitions (the initial level at t=0 is not an edge)."""
    out = []
    for index in range(1, len(series)):
        level = series[index][1]
        if kind == "any" or (kind == "rise" and level == 1) or (kind == "fall" and level == 0):
            out.append(series[index][0])
    return out


def spans(series: list[tuple[float, int]], end: float) -> list[tuple[float, float]]:
    out = []
    start = None
    for index, (time_s, level) in enumerate(series):
        if level == 1 and start is None:
            start = time_s if index > 0 else None  # skip a span already high at t=0
        elif level == 0 and start is not None:
            out.append((start, time_s))
            start = None
    return out


def describe(values_ms: list[float]) -> dict[str, float | int]:
    if not values_ms:
        return {"n": 0}
    ordered = sorted(values_ms)

    def pct(p: float) -> float:
        return ordered[min(len(ordered) - 1, max(0, round(p / 100 * (len(ordered) - 1))))]

    return {
        "n": len(ordered),
        "min_ms": round(ordered[0], 4),
        "p1_ms": round(pct(1), 4),
        "median_ms": round(statistics.median(ordered), 4),
        "mean_ms": round(statistics.fmean(ordered), 4),
        "p99_ms": round(pct(99), 4),
        "max_ms": round(ordered[-1], 4),
    }


def next_after(times: list[float], t: float, limit_s: float) -> float | None:
    index = bisect.bisect_right(times, t)
    if index < len(times) and times[index] - t <= limit_s:
        return times[index]
    return None


# --------------------------------------------------------------------- analyses

def analyze_jitter(sig: dict, end: float, nominal_ms: float) -> dict:
    polls = edges(sig["poll"])
    status_spans = spans(sig["status"], end)
    status_starts = [s for s, _ in status_spans]
    fault = sig.get("pl_fault", [])
    fault_spans = spans(fault, end) if fault else []

    def in_fault(t: float) -> bool:
        return any(a - 0.6 <= t <= b + 3.0 for a, b in fault_spans)

    regular, after_status = [], []
    for a, b in zip(polls, polls[1:]):
        if in_fault(b):
            continue
        period = (b - a) * 1000
        # reportStatus() runs after sendPoll() in the same loop, so a status span
        # can start at the same sample as poll `a`; it delays poll `b`.
        index = bisect.bisect_left(status_starts, a)
        if index < len(status_starts) and status_starts[index] < b:
            after_status.append(period)
        else:
            regular.append(period)

    def deviation(values: list[float]) -> dict:
        if not values:
            return {}
        devs = [v - nominal_ms for v in values]
        return {"min_dev_ms": round(min(devs), 4), "max_dev_ms": round(max(devs), 4),
                "max_abs_dev_ms": round(max(abs(d) for d in devs), 4)}

    loops = edges(sig.get("loop", []))
    loop_periods = [(b - a) * 1000 for a, b in zip(loops, loops[1:])]
    status_periods = [(b - a) * 1000 for a, b in zip(status_starts, status_starts[1:])]
    return {
        "nominal_poll_period_ms": nominal_ms,
        "polls": len(polls),
        "status_reports": len(status_spans),
        "capture_span_s": round(end, 3),
        "poll_period_regular": {**describe(regular), **deviation(regular)},
        "poll_period_containing_status_report": {**describe(after_status), **deviation(after_status)},
        "poll_period_all": {**describe(regular + after_status), **deviation(regular + after_status)},
        "status_report_period": describe(status_periods),
        "loop_period": describe(loop_periods),
        "excluded_polls_near_fault_modes": len(polls) - 1 - len(regular) - len(after_status),
    }


def analyze_status_slip(sig: dict, end: float, nominal_ms: float) -> dict:
    status_spans = spans(sig["status"], end)
    write_spans = spans(sig["write"], end)
    polls = edges(sig["poll"])
    rows = []
    for start, stop in status_spans:
        inner = [(a, b) for a, b in write_spans if start <= a and b <= stop]
        before = [p for p in polls if p <= start]
        after = next_after(polls, start, 2.0)
        slip = None
        if before and after is not None:
            slip = (after - before[-1]) * 1000 - nominal_ms
        rows.append({
            "status_start_s": round(start, 6),
            "status_ms": round((stop - start) * 1000, 4),
            "write_ms": round(sum(b - a for a, b in inner) * 1000, 4),
            "next_poll_slip_ms": None if slip is None else round(slip, 4),
        })
    all_writes = [(b - a) * 1000 for a, b in write_spans]
    status_ms = [r["status_ms"] for r in rows]
    write_ms = [r["write_ms"] for r in rows]
    slips = [r["next_poll_slip_ms"] for r in rows if r["next_poll_slip_ms"] is not None]
    explained = None
    if status_ms and slips:
        gap = statistics.median(slips) - statistics.median(status_ms)
        explained = {
            "median_slip_minus_median_status_ms": round(gap, 4),
            "write_share_of_status_span": round(sum(write_ms) / max(sum(status_ms), 1e-9), 4),
        }
    return {
        "status_span": describe(status_ms),
        "status_write_span": describe(write_ms),
        "all_console_writes": describe(all_writes),
        "writes_at_or_over_10ms_uart_timeout": sum(1 for w in all_writes if w >= 9.9),
        "next_poll_slip_after_status": describe(slips),
        "explanation_check": explained,
        "per_status_report": rows,
    }


def analyze_roundtrip(sig: dict, end: float) -> dict:
    polls = edges(sig["poll"])
    accepts = edges(sig["accept"])
    fault = sig.get("pl_fault", [])
    fault_spans = spans(fault, end) if fault else []
    latencies = []
    for p in polls:
        if any(a - 0.6 <= p <= b + 3.0 for a, b in fault_spans):
            continue
        hit = next_after(accepts, p, 0.1)
        if hit is not None:
            latencies.append((hit - p) * 1000)
    return {"poll_to_accept": describe(latencies), "polls_without_accept_within_100ms":
            sum(1 for p in polls) - len(latencies)}


def analyze_recovery(sig: dict, end: float) -> dict:
    fault = sig["pl_fault"]
    applied = edges(fault, "rise")
    restored = edges(fault, "fall")
    timeouts = edges(sig["timeout"], "rise")
    recoveries = edges(sig["recovery"])
    rows = []
    for index, start in enumerate(applied):
        stop = next((t for t in restored if t > start), None)
        detect = next_after(timeouts, start, 5.0)
        recover = next_after(recoveries, stop, 10.0) if stop is not None else None
        rows.append({
            "trial": index + 1,
            "fault_applied_s": round(start, 6),
            "first_timeout_after_apply_ms": None if detect is None else round((detect - start) * 1000, 4),
            "normal_restored_s": None if stop is None else round(stop, 6),
            "recovery_after_restore_ms": None if recover is None else round((recover - stop) * 1000, 4),
        })
    recov = [r["recovery_after_restore_ms"] for r in rows if r["recovery_after_restore_ms"] is not None]
    detect = [r["first_timeout_after_apply_ms"] for r in rows if r["first_timeout_after_apply_ms"] is not None]
    return {
        "trials_seen": len(rows),
        "detection_first_timeout": describe(detect),
        "recovery_interval": describe(recov),
        "recoveries_over_500ms": [r for r in rows if (r["recovery_after_restore_ms"] or 0) > 500],
        "per_trial": rows,
        "note": "BAD_CRC trials detect by rejection, so a missing first_timeout is expected there; "
                "match trial order to the campaign's run_plan.csv.",
    }


def analyze_watchdog(sig: dict, end: float) -> dict:
    stalls = edges(sig["stall"], "rise")
    records = edges(sig["wdrec"], "rise")
    resets = edges(sig["nrst"], "fall")
    loops = edges(sig["loop"])
    leds = edges(sig["led"])
    rows = []
    for index, stall in enumerate(stalls):
        record = next_after(records, stall, 5.0)
        reset = next_after(resets, record if record is not None else stall, 5.0)
        relaunch = next_after(loops, reset, 20.0) if reset is not None else None
        led_after = [t for t in leds if reset is not None and reset < t <= reset + 3.0]
        led_gaps = [(b - a) * 1000 for a, b in zip(led_after, led_after[1:])]
        rows.append({
            "trial": index + 1,
            "stall_s": round(stall, 6),
            "stall_to_record_ms": None if record is None else round((record - stall) * 1000, 4),
            "record_to_reset_ms": None if record is None or reset is None
            else round((reset - record) * 1000, 4),
            "stall_to_reset_ms": None if reset is None else round((reset - stall) * 1000, 4),
            "app_relaunched_after_reset": relaunch is not None,
            "relaunch_after_reset_ms": None if relaunch is None else round((relaunch - reset) * 1000, 4),
            "led_median_toggle_gap_after_reset_ms":
                round(statistics.median(led_gaps), 3) if led_gaps else None,
        })
    return {
        "trials": len(rows),
        "stall_to_record": describe([r["stall_to_record_ms"] for r in rows if r["stall_to_record_ms"] is not None]),
        "record_to_reset": describe([r["record_to_reset_ms"] for r in rows if r["record_to_reset_ms"] is not None]),
        "stall_to_reset": describe([r["stall_to_reset_ms"] for r in rows if r["stall_to_reset_ms"] is not None]),
        "relaunched_without_power_cycle": sum(1 for r in rows if r["app_relaunched_after_reset"]),
        "per_trial": rows,
        "compare_with": "W3 952/1652 ms (stall->record), W5/W6 + IWDG max 2170 ms (record->reset)",
        "beacon_hint": "app heartbeat LED toggles every ~500 ms; a much faster toggle after reset "
                       "with no loop activity is the bootloader beacon",
    }


def cmd_analyze(args: argparse.Namespace) -> int:
    run = resolve_run(args.run)
    vcd = run / "capture.vcd"
    sig, end = read_vcd(vcd)
    tests = args.test or []
    if not tests:
        tests = ["B3"] if "stall" in sig else ["B1", "B2", "B5"] + (["B6"] if edges(sig.get("pl_fault", [])) else [])
    result: dict[str, object] = {"run": run.name, "capture_sha256": sha256_file(vcd),
                                 "analyzed_utc": utc_now(), "signals": {k: len(v) for k, v in sig.items()}}
    for test in tests:
        if test == "B1":
            result["B1_poll_jitter"] = analyze_jitter(sig, end, args.nominal_ms)
        elif test == "B2":
            result["B2_status_slip"] = analyze_status_slip(sig, end, args.nominal_ms)
        elif test == "B5":
            result["B5_round_trip"] = analyze_roundtrip(sig, end)
        elif test == "B6":
            result["B6_recovery"] = analyze_recovery(sig, end)
        elif test == "B3":
            result["B3_watchdog"] = analyze_watchdog(sig, end)
    out = run / f"analysis_{'_'.join(tests)}.json"
    write_json(out, result)
    printable = {k: v for k, v in result.items()}
    for key in ("B2_status_slip", "B6_recovery", "B3_watchdog"):
        section = printable.get(key)
        if isinstance(section, dict):
            printable[key] = {k: v for k, v in section.items() if k not in ("per_status_report",)}
    print(json.dumps(printable, indent=2))
    print(f"\nwritten: {out}")
    return 0


# ------------------------------------------------------------------------ close

def cmd_close(args: argparse.Namespace) -> int:
    run = resolve_run(args.run)
    manifest = ensure_open(run)
    if args.note:
        manifest.setdefault("notes", []).append({"utc": utc_now(), "text": args.note})
    manifest["status"] = "CLOSED"
    manifest["closed_utc"] = utc_now()
    write_json(run / "manifest.json", manifest)
    lines = []
    for path in sorted(p for p in run.rglob("*") if p.is_file() and p.name != "INVENTORY.sha256"):
        lines.append(f"{sha256_file(path)}  {path.relative_to(run).as_posix()}")
    (run / "INVENTORY.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    inventory_hash = sha256_file(run / "INVENTORY.sha256")
    print(f"closed {run.name}; INVENTORY.sha256 = {inventory_hash}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("new")
    p.add_argument("test", choices=["B1B2B5", "B1", "B2", "B3link", "B3heartbeat", "B4", "B5", "B6", "trial"])
    p.add_argument("label")
    p.add_argument("--flashed", help="what was flashed, e.g. 'G431 lab + G474 lab'")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("check")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("capture")
    p.add_argument("run")
    p.add_argument("--setup", choices=sorted(SETUPS), required=True)
    p.add_argument("--seconds", type=float, required=True)
    p.add_argument("--rate", default="1m", help="sigrok samplerate, e.g. 1m or 4m (default 1m)")
    p.add_argument("--serial", action="append", help="COMx:name, logged alongside (repeatable)")
    p.set_defaults(func=cmd_capture)

    p = sub.add_parser("analyze")
    p.add_argument("run")
    p.add_argument("--test", action="append", choices=["B1", "B2", "B3", "B5", "B6"])
    p.add_argument("--nominal-ms", type=float, default=500.0, help="nominal poll period")
    p.set_defaults(func=cmd_analyze)

    p = sub.add_parser("close")
    p.add_argument("run")
    p.add_argument("--note")
    p.set_defaults(func=cmd_close)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
