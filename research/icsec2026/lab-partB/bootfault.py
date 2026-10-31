#!/usr/bin/env python3
"""B4 boot-policy fault injection on the G431 over SWD (OpenOCD from PlatformIO).

Each warm reset is observed the same way: `reset halt`, optionally stage
BootMetadata in retained RAM, put hardware breakpoints on both slots' reset
handlers, resume. If a breakpoint hits, the bootloader chose that slot and has
already committed its metadata, which is read before the application starts.
If nothing hits within the timeout, the bootloader is in its safe loop.

Mode `policy` re-halts at every launch so the application never runs (tests the
bootloader policy alone). Mode `system` lets the application run for a while
between resets (tests the integrated system, including anything the
application does to retained RAM).

Usage (one ST-LINK connected, see RUNBOOK.md):
  python bootfault.py RUN read
  python bootfault.py RUN prepare-slot-b
  python bootfault.py RUN scenario a|b|c|d [--k N] [--mode policy|system] [--resets N]
  python bootfault.py RUN restore
  python bootfault.py RUN build-prefix          # pre-fix bootloader (commit c8ab6f6^)
  python bootfault.py RUN flash-bootloader fixed|prefix
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import time
from pathlib import Path

import labtool

REPO = labtool.REPO
PIO_HOME = Path(os.environ.get("PLATFORMIO_CORE_DIR", Path.home() / ".platformio"))
OPENOCD = PIO_HOME / "packages" / "tool-openocd" / "bin" / "openocd.exe"
OPENOCD_SCRIPTS = PIO_HOME / "packages" / "tool-openocd" / "openocd" / "scripts"
NM = PIO_HOME / "packages" / "toolchain-gccarmnoneeabi" / "bin" / "arm-none-eabi-nm.exe"

SLOT_A_BASE = 0x08004000
SLOT_B_BASE = 0x08012000
SLOT_LENGTH = 56 * 1024
PAGE = 2048
CORRUPT_OFFSET = 0x800  # inside every image's .text, away from the vector table

FIXED_BOOT_ENV = "nucleo_g431rb_payload_demo_lab"
APP_A_ELF = REPO / "core/.pio/build/nucleo_g431rb_payload_demo_lab/firmware.elf"
APP_B_ELF = REPO / "core/.pio/build/nucleo_g431rb_payload_demo_lab_slot_b/firmware.elf"
FIXED_BOOT_ELF = REPO / f"bootloader/.pio/build/{FIXED_BOOT_ENV}/firmware.elf"
PREFIX_COMMIT = "c8ab6f6^"
PREFIX_TREE = REPO.parent / "WashiOS-prefix-bootloader"
PREFIX_BOOT_ELF = PREFIX_TREE / "bootloader/.pio/build/nucleo_g431rb_payload_demo/firmware.elf"

FIELDS = ["signature", "checksum", "boot_count", "confirmed_flag", "expected_firmware_crc32",
          "metadata_version", "active_slot", "slot_a_crc32", "slot_b_crc32", "slot_a_state",
          "slot_b_state", "last_boot_slot", "last_fail_reason"]
STATES = {0: "Empty", 1: "Valid", 2: "Pending", 3: "Confirmed", 4: "Bad"}
FAILS = {0: "-", 0xB0010001: "FaultLogRecoveryFailed", 0xB0010002: "BootLoopLimit",
         0xB0010003: "PriorCriticalFault", 0xB0010004: "InvalidVectorTable",
         0xB0010005: "FirmwareCrcMismatch", 0xB0010006: "NoValidFirmwareSlot",
         0xB0010007: "InvalidSlotState"}
MAGIC = 0x55AA55AA
VERSION = 2
CRC_TABLE = (0x00000000, 0x1DB71064, 0x3B6E20C8, 0x26D930AC, 0x76DC4190, 0x6B6B51F4,
             0x4DB26158, 0x5005713C, 0xEDB88320, 0xF00F9344, 0xD6D6A3E8, 0xCB61B38C,
             0x9B64C2B0, 0x86D3D2D4, 0xA00AE278, 0xBDBDF21C)


def crc_update(crc: int, data: bytes) -> int:
    for value in data:
        crc ^= value
        crc = (crc >> 4) ^ CRC_TABLE[crc & 0x0F]
        crc = (crc >> 4) ^ CRC_TABLE[crc & 0x0F]
    return crc


def crc32(data: bytes) -> int:
    return (~crc_update(0xFFFFFFFF, data)) & 0xFFFFFFFF


def metadata_checksum(m: dict[str, int]) -> int:
    crc = 0xFFFFFFFF
    for name in FIELDS:
        if name != "checksum":
            crc = crc_update(crc, struct.pack("<I", m[name]))
    return (~crc) & 0xFFFFFFFF


def symbol_address(elf: Path, fragment: str) -> int:
    out = subprocess.run([str(NM), str(elf)], capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 3 and fragment in parts[2]:
            return int(parts[0], 16)
    raise SystemExit(f"symbol {fragment} not found in {elf}")


class OpenOcd:
    def __init__(self, log: Path, serial: str | None):
        transport = "swd"
        cfg = (OPENOCD_SCRIPTS / "interface" / "stlink.cfg").read_text()
        if "hla" in cfg and "st-link" not in cfg:
            transport = "hla_swd"
        command = [str(OPENOCD), "-s", str(OPENOCD_SCRIPTS), "-f", "interface/stlink.cfg"]
        if serial:
            command += ["-c", f"adapter serial {serial}"]
        command += ["-c", f"transport select {transport}", "-f", "target/stm32g4x.cfg",
                    "-c", "reset_config none", "-c", "gdb_port disabled",
                    "-c", "telnet_port disabled", "-c", "tcl_port 6666", "-c", "init"]
        self.log = log.open("a", encoding="utf-8")
        self.proc = subprocess.Popen(command, stdout=self.log, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 10
        while True:
            try:
                self.sock = socket.create_connection(("127.0.0.1", 6666), timeout=1)
                break
            except OSError:
                if self.proc.poll() is not None or time.monotonic() > deadline:
                    raise SystemExit(f"OpenOCD did not start; see {log}")
                time.sleep(0.2)
        self.sock.settimeout(30)

    def cmd(self, text: str) -> str:
        self.log.write(f"> {text}\n")
        self.sock.sendall(text.encode() + b"\x1a")
        data = b""
        while not data.endswith(b"\x1a"):
            chunk = self.sock.recv(65536)
            if not chunk:
                raise SystemExit("OpenOCD closed the connection")
            data += chunk
        reply = data[:-1].decode(errors="replace")
        self.log.write(reply + "\n")
        self.log.flush()
        return reply

    def words(self, address: int, count: int) -> list[int]:
        reply = self.cmd(f"capture {{mdw 0x{address:08x} {count}}}")
        values = []
        for line in reply.splitlines():
            if ":" in line:
                values += [int(v, 16) for v in line.split(":", 1)[1].split()]
        if len(values) < count:
            raise SystemExit(f"mdw failed: {reply}")
        return values[:count]

    def pc(self) -> int:
        reply = self.cmd("capture {reg pc}")
        return int(reply.split(":")[-1].strip().split()[0], 16)

    def close(self) -> None:
        try:
            self.cmd("shutdown")
        except Exception:
            pass
        self.proc.wait(timeout=5)
        self.log.close()


class Bench:
    def __init__(self, run: Path, serial: str | None, boot_elf: Path):
        self.run = run
        self.events = run / "b4_events.jsonl"
        self.meta_addr = symbol_address(boot_elf, "bootMetadataE")
        self.ocd = OpenOcd(run / "openocd.log", serial)

    def record(self, kind: str, **data: object) -> dict:
        row = {"utc": labtool.utc_now(), "event": kind, **data}
        with self.events.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row) + "\n")
        return row

    def read_meta(self) -> dict:
        values = dict(zip(FIELDS, self.ocd.words(self.meta_addr, len(FIELDS))))
        values["_valid"] = (values["signature"] == MAGIC and values["metadata_version"] == VERSION
                            and values["checksum"] == metadata_checksum(values))
        return values

    def write_meta(self, m: dict[str, int]) -> None:
        m = {**m, "signature": MAGIC, "metadata_version": VERSION}
        m["checksum"] = metadata_checksum(m)
        for index, name in enumerate(FIELDS):
            self.ocd.cmd(f"mww 0x{self.meta_addr + 4 * index:08x} 0x{m[name]:08x}")

    def dump(self, address: int, length: int, name: str) -> bytes:
        path = self.run / name
        self.ocd.cmd(f"dump_image {{{path.as_posix()}}} 0x{address:08x} {length}")
        return path.read_bytes()

    def program(self, data: bytes, address: int, name: str) -> None:
        path = self.run / name
        path.write_bytes(data)
        reply = self.ocd.cmd(f"flash write_image erase {{{path.as_posix()}}} 0x{address:08x} bin")
        verify = self.ocd.cmd(f"verify_image {{{path.as_posix()}}} 0x{address:08x} bin")
        if "error" in (reply + verify).lower() or "mismatch" in verify.lower():
            raise SystemExit(f"flash write failed:\n{reply}\n{verify}")

    def reset_vector(self, base: int) -> int | None:
        value = self.ocd.words(base + 4, 1)[0]
        return None if value in (0xFFFFFFFF, 0) else value & ~1

    def boot_once(self, label: str, stage: dict[str, int] | None, mode: str,
                  app_seconds: float, timeout_s: float = 3.0) -> dict:
        ocd = self.ocd
        ocd.cmd("reset halt")
        before = self.read_meta()
        if stage is not None:
            self.write_meta(stage)
        staged = self.read_meta() if stage is not None else None
        targets = {}
        for slot, base in (("A", SLOT_A_BASE), ("B", SLOT_B_BASE)):
            vector = self.reset_vector(base)
            if vector is not None:
                targets[vector] = slot
                ocd.cmd(f"bp 0x{vector:08x} 2 hw")
        ocd.cmd("resume")
        ocd.cmd(f"catch {{wait_halt {int(timeout_s * 1000)}}}")
        halted = ocd.cmd("[target current] curstate").strip() == "halted"
        if not halted:
            ocd.cmd("halt")
        pc = ocd.pc()
        after = self.read_meta()
        ocd.cmd("rbp all")
        launched = targets.get(pc) if halted else None
        outcome = f"LAUNCHED_{launched}" if launched else (
            "SAFE_LOOP" if pc < SLOT_A_BASE else f"STOPPED_PC_0x{pc:08x}")
        row = self.record("boot", label=label, mode=mode, outcome=outcome, pc=f"0x{pc:08x}",
                          before=before, staged=staged, after=after)
        print(f"  {label:<28} {outcome:<12} boot_count={after['boot_count']} "
              f"active={'AB'[after['active_slot']] if after['active_slot'] < 2 else after['active_slot']} "
              f"A={STATES.get(after['slot_a_state'], after['slot_a_state'])} "
              f"B={STATES.get(after['slot_b_state'], after['slot_b_state'])} "
              f"fail={FAILS.get(after['last_fail_reason'], hex(after['last_fail_reason']))} "
              f"meta_valid_before_boot={before['_valid']}")
        if launched and mode == "system":
            ocd.cmd("resume")
            time.sleep(app_seconds)
            ocd.cmd("halt")
            row_after = self.read_meta()
            self.record("app_ran", label=label, seconds=app_seconds, metadata_after_app=row_after)
            print(f"  {'':<28} after {app_seconds:.1f}s of app: metadata valid={row_after['_valid']}")
        return row

    # -- slot images -------------------------------------------------------
    def save_originals(self) -> None:
        for slot, base in (("A", SLOT_A_BASE), ("B", SLOT_B_BASE)):
            name = f"original_slot_{slot}_page.bin"
            if not (self.run / name).exists():
                self.ocd.cmd("halt")
                self.dump(base + CORRUPT_OFFSET, PAGE, name)

    def corrupt(self, slot: str) -> None:
        base = SLOT_A_BASE if slot == "A" else SLOT_B_BASE
        self.save_originals()
        self.ocd.cmd("halt")
        page = bytearray((self.run / f"original_slot_{slot}_page.bin").read_bytes())
        page[16] ^= 0xFF
        self.program(bytes(page), base + CORRUPT_OFFSET, f"corrupt_slot_{slot}_page.bin")
        self.record("corrupt", slot=slot, address=f"0x{base + CORRUPT_OFFSET + 16:08x}")
        print(f"  corrupted slot {slot} at 0x{base + CORRUPT_OFFSET + 16:08x}")

    def restore(self) -> None:
        for slot, base in (("A", SLOT_A_BASE), ("B", SLOT_B_BASE)):
            original = self.run / f"original_slot_{slot}_page.bin"
            if original.exists():
                self.ocd.cmd("halt")
                current = self.dump(base + CORRUPT_OFFSET, PAGE, f"check_slot_{slot}_page.bin")
                if current != original.read_bytes():
                    self.program(original.read_bytes(), base + CORRUPT_OFFSET, f"restore_slot_{slot}_page.bin")
                    self.record("restore", slot=slot)
                    print(f"  restored slot {slot}")

    def slot_b_crc(self) -> int:
        self.ocd.cmd("halt")
        return crc32(self.dump(SLOT_B_BASE, SLOT_LENGTH, "slot_b_full.bin"))


def base_meta(a_crc: int, b_crc: int, *, active: int, a_state: int, b_state: int, count: int = 0) -> dict:
    return {"boot_count": count, "confirmed_flag": 0, "expected_firmware_crc32": a_crc,
            "active_slot": active, "slot_a_crc32": a_crc, "slot_b_crc32": b_crc,
            "slot_a_state": a_state, "slot_b_state": b_state, "last_boot_slot": active,
            "last_fail_reason": 0}


def run_scenario(bench: Bench, name: str, mode: str, k: int, resets: int, app_seconds: float) -> None:
    if name == "d" and not 1 <= k <= 3:
        raise SystemExit("scenario d needs --k 1, 2 or 3")
    bench.restore()
    # Invalid metadata makes the bootloader re-initialise it from its provisioned
    # slot A CRC; read that CRC back from the boot it then performs.
    bench.ocd.cmd("reset halt")
    bench.ocd.cmd(f"mww 0x{bench.meta_addr:08x} 0")
    seed = bench.boot_once("seed (fresh metadata)", None, "policy", 0)
    a_crc = seed["after"]["slot_a_crc32"]
    b_crc = bench.slot_b_crc()
    bench.record("scenario_start", scenario=name, mode=mode, k=k, a_crc=f"0x{a_crc:08x}", b_crc=f"0x{b_crc:08x}")
    print(f"scenario {name}: slot A CRC 0x{a_crc:08x}, slot B CRC 0x{b_crc:08x}, mode {mode}")

    if name == "a":
        bench.corrupt("A")
        stage = base_meta(a_crc, b_crc, active=0, a_state=3, b_state=1)
        bench.boot_once("a: A corrupt, B valid", stage, mode, app_seconds)
        print("  expect: LAUNCHED_B")
    elif name == "b":
        bench.corrupt("A")
        bench.corrupt("B")
        stage = base_meta(a_crc, b_crc, active=0, a_state=3, b_state=1)
        bench.boot_once("b: A and B corrupt", stage, mode, app_seconds)
        print("  expect: SAFE_LOOP, fail=NoValidFirmwareSlot")
    elif name == "c":
        stage = base_meta(a_crc, b_crc, active=1, a_state=3, b_state=2)
        bench.boot_once("c: reset 1 (B pending)", stage, mode, app_seconds)
        for index in range(2, resets + 1):
            bench.boot_once(f"c: reset {index}", None, mode, app_seconds)
        print("  expect (model): LAUNCHED_B 4 times, then SAFE_LOOP fail=BootLoopLimit")
    elif name == "d":
        stage = base_meta(a_crc, b_crc, active=0, a_state=3, b_state=2)
        bench.boot_once("d: warm 1 (A confirmed)", stage, mode, app_seconds)
        for index in range(2, k + 1):
            bench.boot_once(f"d: warm {index} (A)", None, mode, app_seconds)
        bench.corrupt("A")
        for index in range(1, resets + 1):
            bench.boot_once(f"d: after corrupt reset {index}", None, mode, app_seconds)
        print(f"  expect (model): pre-fix B launched {max(0, 4 - k)} times, fixed B launched 4 times")
    bench.restore()


def cmd_build_prefix() -> None:
    if not PREFIX_TREE.exists():
        subprocess.run(["git", "-C", str(REPO), "worktree", "add", "--detach", str(PREFIX_TREE), PREFIX_COMMIT],
                       check=True)
    target = PREFIX_TREE / "core/.pio/build/nucleo_g431rb_payload_demo/firmware.elf"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(APP_A_ELF, target)
    pio = PIO_HOME / "penv" / "Scripts" / "pio.exe"
    subprocess.run([str(pio), "run", "-e", "nucleo_g431rb_payload_demo"], cwd=PREFIX_TREE / "bootloader", check=True)
    commit = subprocess.run(["git", "-C", str(PREFIX_TREE), "rev-parse", "HEAD"], capture_output=True,
                            text=True).stdout.strip()
    print(f"pre-fix bootloader built from {commit}: {PREFIX_BOOT_ELF}")


def cmd_flash(run: Path, which: str, serial: str | None) -> None:
    elf = PREFIX_BOOT_ELF if which == "prefix" else FIXED_BOOT_ELF
    if not elf.exists():
        raise SystemExit(f"not built: {elf}")
    ocd = OpenOcd(run / "openocd.log", serial)
    reply = ocd.cmd(f"program {{{elf.as_posix()}}} verify")
    ocd.close()
    if "error" in reply.lower():
        raise SystemExit(reply)
    manifest = labtool.load_json(run / "manifest.json")
    manifest.setdefault("bootloader_flashed", []).append(
        {"utc": labtool.utc_now(), "which": which, "elf": str(elf), "sha256": labtool.sha256_file(elf)})
    labtool.write_json(run / "manifest.json", manifest)
    print(f"flashed {which} bootloader ({elf.name}); sha256 recorded in manifest")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run", nargs="?")
    parser.add_argument("action", choices=["read", "prepare-slot-b", "scenario", "restore",
                                           "build-prefix", "flash-bootloader"])
    parser.add_argument("arg", nargs="?")
    parser.add_argument("--k", type=int, default=2)
    parser.add_argument("--mode", choices=["policy", "system"], default="policy")
    parser.add_argument("--resets", type=int, default=6)
    parser.add_argument("--app-seconds", type=float, default=2.0)
    parser.add_argument("--bootloader", choices=["fixed", "prefix"], default="fixed",
                        help="which bootloader is on the board (for the metadata address)")
    parser.add_argument("--stlink-serial")
    args = parser.parse_args(argv)

    if args.action == "build-prefix":
        cmd_build_prefix()
        return 0
    if not args.run:
        parser.error("run directory required")
    run = labtool.resolve_run(args.run)
    labtool.ensure_open(run)
    if args.action == "flash-bootloader":
        cmd_flash(run, args.arg or "fixed", args.stlink_serial)
        return 0

    boot_elf = PREFIX_BOOT_ELF if args.bootloader == "prefix" else FIXED_BOOT_ELF
    bench = Bench(run, args.stlink_serial, boot_elf)
    try:
        if args.action == "read":
            m = bench.read_meta()
            bench.record("read", metadata=m)
            for name in FIELDS:
                print(f"  {name:<24} 0x{m[name]:08x}")
            print(f"  valid: {m['_valid']}")
        elif args.action == "prepare-slot-b":
            bench.ocd.cmd("reset halt")
            reply = bench.ocd.cmd(f"program {{{APP_B_ELF.as_posix()}}} verify")
            if "error" in reply.lower():
                raise SystemExit(reply)
            bench.record("slot_b_programmed", elf=str(APP_B_ELF), sha256=labtool.sha256_file(APP_B_ELF))
            print(f"slot B programmed, CRC 0x{bench.slot_b_crc():08x}")
        elif args.action == "restore":
            bench.restore()
        elif args.action == "scenario":
            if args.arg not in ("a", "b", "c", "d"):
                parser.error("scenario must be a, b, c or d")
            bench.record("bootloader_in_use", which=args.bootloader, elf=str(boot_elf),
                         sha256=labtool.sha256_file(boot_elf), metadata_address=f"0x{bench.meta_addr:08x}")
            run_scenario(bench, args.arg, args.mode, args.k, args.resets, args.app_seconds)
    finally:
        bench.ocd.cmd("resume")
        bench.ocd.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
