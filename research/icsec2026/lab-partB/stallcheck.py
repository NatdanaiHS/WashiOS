#!/usr/bin/env python3
"""B3 follow-up: what the bootloader does after an injected-stall IWDG reset.

Run alongside `labtool.py capture` (the analyzer shows the application's loop
activity stop). Each trial:
  1. emulate a cold start over SWD: invalidate the retained BootMetadata and
     FaultLog signatures, then `reset run`;
  2. wait for the stall build to stall (10 s), record WATCHDOG_TIMEOUT and be
     reset by the IWDG;
  3. halt and read where the core is (bootloader safe loop or application) and
     the retained metadata's last_fail_reason;
  4. warm-reset once more and check again that the application is not relaunched.

The SWD invalidation stands in for removing power: it puts the retained RAM in
the state the bootloader treats as a cold start. Results go to stall_trials.jsonl.

Usage: python stallcheck.py RUN --trials 10 [--stlink-serial SER]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time

import bootfault as bf
import labtool

SLOT_A_END = 0x08012000


def function_range(elf, name: str) -> tuple[int, int]:
    out = subprocess.run([str(bf.NM), "-S", "-C", str(elf)], capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        parts = line.split(maxsplit=3)
        if len(parts) == 4 and name in parts[3]:
            start = int(parts[0], 16)
            return start, start + int(parts[1], 16)
    raise SystemExit(f"{name} not found in {elf}")


def where(pc: int, safe_loop: tuple[int, int]) -> str:
    if safe_loop[0] <= pc < safe_loop[1]:
        return "BOOTLOADER_SAFE_LOOP"
    if bf.SLOT_A_BASE <= pc < SLOT_A_END:
        return "APPLICATION"
    return f"OTHER_0x{pc:08x}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run")
    parser.add_argument("--trials", type=int, default=10)
    parser.add_argument("--wait-s", type=float, default=16.0, help="cold start to inspection")
    parser.add_argument("--stlink-serial")
    args = parser.parse_args(argv)

    run = labtool.resolve_run(args.run)
    labtool.ensure_open(run)
    bench = bf.Bench(run, args.stlink_serial, bf.FIXED_BOOT_ELF)
    safe_loop = function_range(bf.FIXED_BOOT_ELF, "Stm32G4Beacon::enterSafeLoop")
    fault_log = bf.symbol_address(bf.FIXED_BOOT_ELF, "systemFaultLogE")
    out = run / "stall_trials.jsonl"
    ocd = bench.ocd
    try:
        for trial in range(1, args.trials + 1):
            ocd.cmd("halt")
            ocd.cmd(f"mww 0x{bench.meta_addr:08x} 0")
            ocd.cmd(f"mww 0x{fault_log:08x} 0")
            ocd.cmd("reset run")
            started = labtool.utc_now()
            time.sleep(args.wait_s)
            ocd.cmd("halt")
            pc = ocd.pc()
            meta = bench.read_meta()
            first = where(pc, safe_loop)
            ocd.cmd("reset run")
            time.sleep(3.0)
            ocd.cmd("halt")
            pc2 = ocd.pc()
            second = where(pc2, safe_loop)
            ocd.cmd("resume")
            row = {"trial": trial, "cold_start_utc": started, "after_stall": first, "pc": f"0x{pc:08x}",
                   "last_fail_reason": f"0x{meta['last_fail_reason']:08x}",
                   "last_fail_name": bf.FAILS.get(meta["last_fail_reason"], "?"),
                   "after_warm_reset": second, "pc_after_warm_reset": f"0x{pc2:08x}"}
            with out.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row) + "\n")
            print(f"trial {trial:2}: after stall {first:<22} fail={row['last_fail_name']:<20} "
                  f"after warm reset {second}")
    finally:
        ocd.cmd("reset run")
        ocd.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
