#!/usr/bin/env python3
"""Compare a retained verifyta results directory against the expected-verdict oracle.

Usage: check_verdicts.py [results_dir]   (default: newest directory under draft-camera-ready/results/)
Exit 0 when every configuration's verdict sequence equals the expectation; 1 otherwise.
The oracle below is the machine-readable form of draft-camera-ready/EXPECTED_VERDICTS.md.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

FORMAL = Path(__file__).resolve().parents[1]

S, N = "S", "N"
EXPECTED: dict[str, list[str]] = {
    # payload_link.q: Q0 Q1 Q2 Q2T Q3 Q3T Q4 Q4T Q5 Q6 Q7 Q8 Q9a Q9b Q9c1 Q9c2 Q10 Q11a Q11b
    # DRAFT-CAMERA-READY oracle, PREDICTED analytically before the first run (2026-10-18) from the
    # model's predicates: ACCEPTS = d + 9 + 1 + 4 < 100 (d <= 85); TIMES_OUT = d + 2 + 2 > 103 + SLIP
    # (d >= 100 at SLIP 0, d >= 160 at SLIP 60). Timeout-mode pattern (SILENT, BAD_CRC, TIMES_OUT):
    # every bound tight -> Q2T Q3T Q4T and both Q9c fail. Band pattern at SLIP 0: both Q9c hold, Q4T
    # fails (OFFLINE reachable). ACCEPTS pattern: Q4T vacuous, both Q9c fail.
    "payload_silent":      [S, S, S, N, S, N, S, N, S, S, S, S, S, S, N, N, S, S, S],
    "payload_badcrc":      [S, S, S, N, S, N, S, N, S, S, S, S, S, S, N, N, S, S, S],
    "payload_delayed_50":  [S, S, S, S, S, S, S, S, S, S, S, S, S, S, N, N, S, S, S],
    # CORRECTED 2026-10-18 after run 20261018T073529Z (see results/20261018T073529Z_q4t_probe/): Q4T was
    # predicted N for the d = 90 band and is S. The recovery bound holds but is not attained there: the
    # worst case is 513 ms (573 with the status block), because staying OFFLINE requires a decode later
    # than 5 ms after the poll. Original prediction: SSSSSSSNSSSSSSSSSSS.
    "payload_delayed_90":  [S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S],
    "payload_delayed_100": [S, S, S, N, S, N, S, N, S, S, S, S, S, S, N, N, S, S, S],
    "payload_delayed_110": [S, S, S, N, S, N, S, N, S, S, S, S, S, S, N, N, S, S, S],
    "payload_delayed_150": [S, S, S, N, S, N, S, N, S, S, S, S, S, S, N, N, S, S, S],
    "payload_delayed_250": [S, S, S, N, S, N, S, N, S, S, S, S, S, S, N, N, S, S, S],
    # Jitter sensitivity at d = 100 (no status block): TIMES_OUT = 104 > 101 + J holds for J <= 2, so
    # J in {0,1} gives the timeout pattern; J = 5 puts d = 100 in the band (band pattern).
    "payload_delayed_100_j0": [S, S, S, N, S, N, S, N, S, S, S, S, S, S, N, N, S, S, S],
    "payload_delayed_100_j1": [S, S, S, N, S, N, S, N, S, S, S, S, S, S, N, N, S, S, S],
    "payload_delayed_100_j5": [S, S, S, S, S, S, S, N, S, S, S, S, S, S, S, S, S, S, S],
    # With the status block (SLIP 60): SILENT/BAD_CRC/d250 keep the timeout pattern with bounds +60.
    # d = 90 stays in the band. d = 110 is in the band only because of the block: a timeout is
    # reachable (Q9c1 S) but one block per 5 s cannot rescue every poll of a 1326 ms window (Q9c2 N).
    "payload_silent_status":      [S, S, S, N, S, N, S, N, S, S, S, S, S, S, N, N, S, S, S],
    "payload_badcrc_status":      [S, S, S, N, S, N, S, N, S, S, S, S, S, S, N, N, S, S, S],
    # CORRECTED 2026-10-18 after run 20261018T073529Z (see results/20261018T073529Z_q4t_probe/): Q4T was
    # predicted N for the d = 90 band and is S. The recovery bound holds but is not attained there: the
    # worst case is 513 ms (573 with the status block), because staying OFFLINE requires a decode later
    # than 5 ms after the poll. Original prediction: SSSSSSSNSSSSSSSSSSS.
    "payload_delayed_90_status":  [S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S],
    "payload_delayed_110_status": [S, S, S, S, S, S, S, N, S, S, S, S, S, S, S, N, S, S, S],
    "payload_delayed_250_status": [S, S, S, N, S, N, S, N, S, S, S, S, S, S, N, N, S, S, S],
    # watchdog_gating.q: Q0 W1a W1b W2 W3hb W3pl W3T W5 W6pl W6hb W7
    "watchdog_nostall":    [S, S, S, S, S, S, S, S, S, S, S],
    "watchdog_stall":      [S, N, N, S, S, S, N, S, S, S, S],
    # boot_policy.q: Q0 B1 B2 B3 B4 B5a B5b B6 B7 B7r B8 B8b B8c B9
    "boot_shipped":        [S, S, S, S, S, S, S, S, S, N, N, S, S, S],
    "boot_design":         [S, S, S, S, S, S, S, S, N, S, N, S, N, S],
    # F4 fix (FALLBACK_RESETS 1): resetBootAttempts() before activateBootSlot() on the
    # fallback path. B8 now holds; B8c is vacuous because no over-limit launch occurs.
    "boot_f4fix":          [S, S, S, S, S, S, S, S, S, N, S, S, S, S],
}

VERDICT_RE = re.compile(r"-- Formula is (NOT satisfied|satisfied)\.")


def verdicts(out_file: Path) -> list[str]:
    return [N if v.startswith("NOT") else S for v in VERDICT_RE.findall(out_file.read_text(encoding="utf-8", errors="replace"))]


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        results = Path(argv[1])
    else:
        dirs = sorted(p for p in (FORMAL / "results").iterdir() if p.is_dir())
        if not dirs:
            print("no results directory found", file=sys.stderr)
            return 2
        results = dirs[-1]
    failures = 0
    total = 0
    for name, expected in EXPECTED.items():
        out = results / f"{name}.out"
        if not out.exists():
            print(f"MISSING  {name}")
            failures += 1
            continue
        actual = verdicts(out)
        total += len(actual)
        err = results / f"{name}.err"
        if err.exists() and err.stat().st_size > 0 and "exit" in err.read_text(errors="replace"):
            print(f"ERROR    {name}: see {err.name}")
            failures += 1
            continue
        if actual == expected:
            print(f"OK       {name}: {''.join(actual)}")
        else:
            failures += 1
            diff = [str(i + 1) for i, (a, e) in enumerate(zip(actual, expected)) if a != e]
            print(f"MISMATCH {name}: got {''.join(actual)} expected {''.join(expected)} (formulas {', '.join(diff) or 'count'})")
    print(f"{results.name}: {len(EXPECTED) - failures}/{len(EXPECTED)} configurations match; {total} verdicts checked")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
