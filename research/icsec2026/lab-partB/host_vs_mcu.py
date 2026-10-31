#!/usr/bin/env python3
"""Compare host-stamped console lines with MCU-side GPIO edges from one B1 run.

The B1 run captured both the controller's accept-probe edges (logic analyzer,
1 MSa/s) and the host stamp of every `[OBC] PAYLOAD_ACCEPTED` line written right
after each acceptance. Lines and edges are paired in order (counts must match).

Reports, for the same polls:
- mean poll period from the analyzer and from host stamps (clock agreement);
- host-stamped intervals with and without a status report between them
  (the E1 measure from the frozen logs) against the MCU intervals;
- per-line host latency relative to its MCU edge (offset removed).

Usage: python host_vs_mcu.py RUN_DIR OUTPUT.json
"""

from __future__ import annotations

import datetime as dt
import json
import statistics
import sys
from pathlib import Path

import labtool as lt


def stamp(text: str) -> float:
    return dt.datetime.strptime(text, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=dt.timezone.utc).timestamp()


def summary(values: list[float]) -> dict[str, float | int]:
    ordered = sorted(values)
    return {"n": len(ordered), "min_ms": round(ordered[0], 3), "median_ms": round(statistics.median(ordered), 3),
            "mean_ms": round(statistics.fmean(ordered), 3), "p99_ms": round(ordered[int(0.99 * (len(ordered) - 1))], 3),
            "max_ms": round(ordered[-1], 3)}


def main(argv: list[str]) -> int:
    run, output = Path(argv[1]), Path(argv[2])
    sig, _ = lt.read_vcd(run / "capture.vcd")
    mcu = lt.edges(sig["accept"])
    host, status_after = [], set()
    for line in (run / "serial_g431.log").read_text(encoding="utf-8").splitlines():
        when, _, text = line.partition("\t")
        if "PAYLOAD_ACCEPTED" in text:
            host.append(stamp(when))
        elif "PAYLOAD_STATUS" in text:
            status_after.add(len(host))  # status line follows the len(host)-th accepted line
    if len(host) != len(mcu):
        raise SystemExit(f"cannot pair: {len(host)} host lines, {len(mcu)} MCU edges")

    n = len(mcu) - 1
    host_iv = [(b - a) * 1000 for a, b in zip(host, host[1:])]
    mcu_iv = [(b - a) * 1000 for a, b in zip(mcu, mcu[1:])]
    # interval i spans accepted lines i and i+1; it contains a status line if one follows line i+1's predecessor
    with_status = [i for i in range(n) if (i + 1) in status_after]
    without = [i for i in range(n) if (i + 1) not in status_after]
    raw = [h - m for h, m in zip(host, mcu)]
    latency = [(r - min(raw)) * 1000 for r in raw]
    first_after_status = [latency[i] for i in sorted(status_after) if i < len(latency)]

    result = {
        "run": run.name,
        "capture_sha256": lt.sha256_file(run / "capture.vcd"),
        "serial_sha256": lt.sha256_file(run / "serial_g431.log"),
        "pairs": len(mcu),
        "status_reports": len(status_after),
        "mean_period_ms": {"analyzer": round((mcu[-1] - mcu[0]) / n * 1000, 4),
                           "host": round((host[-1] - host[0]) / n * 1000, 4)},
        "interval_containing_status": {"host": summary([host_iv[i] for i in with_status]),
                                       "mcu": summary([mcu_iv[i] for i in with_status])},
        "interval_without_status": {"host": summary([host_iv[i] for i in without]),
                                    "mcu": summary([mcu_iv[i] for i in without])},
        "host_line_latency_offset_removed": summary(latency),
        "host_latency_first_line_after_status": summary(first_after_status),
        "note": "host latency is relative to the smallest observed host-minus-MCU offset; "
                "it includes the 75-byte line serialization, ST-LINK VCP and host scheduling",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
