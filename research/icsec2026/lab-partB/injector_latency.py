#!/usr/bin/env python3
"""Test the E1 status-report slip against MCU time, using the campaign injector's own stamps.

The B6 run captured the controller's accept-probe edges (logic analyzer) while
run_payload_campaign.py logged the controller console with its usual reader
(pyserial read(64) with a 50 ms timeout, stamped when the line is assembled).
Every host-stamped `[OBC] PAYLOAD_ACCEPTED` line is paired with the accept edge
that precedes it; the analyzer-to-UTC skew is chosen so that the most lines land
0-90 ms after an edge.

Reports:
- E1 as computed from the frozen logs: host interval between consecutive
  ACCEPTED lines, split by whether a PAYLOAD_STATUS line lies between them,
  next to the MCU interval of the same pair of edges;
- the change in host stamp latency across a status report versus across an
  ordinary poll (a persistent step = an observation-path shift, not a late poll).

Usage: python injector_latency.py LAB_RUN_DIR CAMPAIGN_DIR OUTPUT.json
"""

from __future__ import annotations

import bisect
import datetime as dt
import json
import statistics
import sys
from pathlib import Path

import labtool as lt


def stamp(text: str) -> float:
    return dt.datetime.fromisoformat(text).timestamp()


def summary(values: list[float]) -> dict[str, float | int]:
    ordered = sorted(values)
    if not ordered:
        return {"n": 0}
    return {"n": len(ordered), "min_ms": round(ordered[0], 3), "median_ms": round(statistics.median(ordered), 3),
            "max_ms": round(ordered[-1], 3)}


def main(argv: list[str]) -> int:
    run, campaign, output = Path(argv[1]), Path(argv[2]), Path(argv[3])
    sig, _ = lt.read_vcd(run / "capture.vcd")
    edges = lt.edges(sig["accept"])
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    base = dt.datetime.strptime(manifest["captures"][0]["start_utc"], "%Y-%m-%dT%H:%M:%S.%fZ") \
        .replace(tzinfo=dt.timezone.utc).timestamp()

    lines: list[tuple[float, str]] = []
    for log in sorted(campaign.glob("raw/*/g431.log")):
        for row in log.read_text(encoding="utf-8").splitlines():
            when, _, rest = row.partition("\t")
            text = rest.split("\t", 1)[-1]
            if "PAYLOAD_ACCEPTED" in text or "PAYLOAD_STATUS" in text:
                lines.append((stamp(when) - base, "S" if "PAYLOAD_STATUS" in text else "A"))
    lines.sort()

    def pair(skew: float) -> list[tuple[float, float | None]]:
        out = []
        for t, kind in lines:
            if kind != "A":
                continue
            i = bisect.bisect_right(edges, t - skew) - 1
            lat = (t - skew - edges[i]) if i >= 0 else None
            out.append((t, edges[i] if lat is not None and 0.0 <= lat <= 0.09 else None))
        return out

    best = max((s / 1000 for s in range(-3000, 3001)),
               key=lambda s: sum(1 for _, e in pair(s) if e is not None))
    paired = pair(best)
    status_times = [t for t, kind in lines if kind == "S"]

    host_with, mcu_with, host_without, mcu_without = [], [], [], []
    step_status, step_plain = [], []
    for (t0, e0), (t1, e1) in zip(paired, paired[1:]):
        if e0 is None or e1 is None:
            continue
        mcu_iv = (e1 - e0) * 1000
        if not 400 <= mcu_iv <= 600:  # consecutive polls only (no timeouts between)
            continue
        host_iv = (t1 - t0) * 1000
        step = ((t1 - best - e1) - (t0 - best - e0)) * 1000
        has_status = any(t0 < s < t1 for s in status_times)
        (host_with if has_status else host_without).append(host_iv)
        (mcu_with if has_status else mcu_without).append(mcu_iv)
        (step_status if has_status else step_plain).append(abs(step))

    result = {
        "lab_run": run.name,
        "campaign": campaign.name,
        "capture_sha256": lt.sha256_file(run / "capture.vcd"),
        "reader": "run_payload_campaign.py SerialCapture: read(64), timeout 0.05 s, stamped at line assembly",
        "analyzer_to_utc_skew_s": best,
        "accepted_lines": sum(1 for _, k in lines if k == "A"),
        "paired_within_0_90ms": sum(1 for _, e in paired if e is not None),
        "interval_containing_status": {"host": summary(host_with), "mcu": summary(mcu_with)},
        "interval_without_status": {"host": summary(host_without), "mcu": summary(mcu_without)},
        "stamp_latency_relative_to_fastest_ms": summary(
            [((t - best - e) - min((t2 - best - e2) for t2, e2 in paired if e2 is not None)) * 1000
             for t, e in paired if e is not None]),
        "abs_latency_step_across_status_ms": summary(step_status),
        "abs_latency_step_across_plain_poll_ms": summary(step_plain),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
