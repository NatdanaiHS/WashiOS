#!/usr/bin/env python3
"""Freeze toolchain, dependency, executable, and package metadata provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest().upper()


def run(command: list[str], cwd: Path) -> dict[str, object]:
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    return {
        "command": command,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--pio", required=True, type=Path)
    parser.add_argument("--python", required=True, type=Path)
    parser.add_argument("--toolchain-bin", required=True, type=Path)
    parser.add_argument("--openocd", required=True, type=Path)
    parser.add_argument("--platformio-root", required=True, type=Path)
    args = parser.parse_args()

    output = args.output_dir.resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite toolchain provenance: {output}")
    output.mkdir(parents=True)
    repo = args.repo_root.resolve()
    gcc = args.toolchain_bin / "arm-none-eabi-gcc.exe"
    gxx = args.toolchain_bin / "arm-none-eabi-g++.exe"
    objcopy = args.toolchain_bin / "arm-none-eabi-objcopy.exe"
    commands = [
        ["git", "--version"],
        [str(args.pio.resolve()), "--version"],
        [str(args.pio.resolve()), "system", "info", "--json-output"],
        [str(args.pio.resolve()), "pkg", "list", "-d", str(repo / "core")],
        [str(args.pio.resolve()), "pkg", "list", "-d", str(repo / "bootloader")],
        [str(args.pio.resolve()), "pkg", "list", "-d", str(repo / "demo-payload")],
        [str(args.python.resolve()), "--version"],
        [str(args.python.resolve()), "-m", "pip", "--version"],
        [str(args.python.resolve()), "-m", "pip", "freeze", "--all"],
        [str(gcc.resolve()), "--version"],
        [str(gxx.resolve()), "--version"],
        [str(objcopy.resolve()), "--version"],
        [str(args.openocd.resolve()), "--version"],
        ["pwsh", "--version"],
    ]
    command_results = [run(command, repo) for command in commands]
    (output / "command_versions.json").write_text(
        json.dumps(command_results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    executables = [args.pio, args.python, gcc, gxx, objcopy, args.openocd]
    executable_records = []
    for executable in executables:
        resolved = executable.resolve()
        executable_records.append(
            {
                "path": str(resolved),
                "byte_count": resolved.stat().st_size,
                "sha256": sha256_file(resolved),
            }
        )
    (output / "executable_hashes.json").write_text(
        json.dumps(executable_records, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    metadata_sources = [
        args.platformio_root / "platforms" / "ststm32" / "platform.json",
        args.platformio_root / "packages" / "framework-stm32cubeg4" / "package.json",
        args.platformio_root / "packages" / "toolchain-gccarmnoneeabi" / "package.json",
        args.platformio_root / "packages" / "tool-openocd" / "package.json",
    ]
    metadata_dir = output / "package_metadata"
    metadata_dir.mkdir()
    metadata_records = []
    for index, source in enumerate(metadata_sources, start=1):
        source = source.resolve()
        if not source.is_file():
            metadata_records.append({"source": str(source), "status": "MISSING"})
            continue
        destination = metadata_dir / f"{index:02d}_{source.parent.name}_{source.name}"
        shutil.copyfile(source, destination)
        metadata_records.append(
            {
                "source": str(source),
                "copy": destination.relative_to(output).as_posix(),
                "byte_count": destination.stat().st_size,
                "sha256": sha256_file(destination),
                "status": "COPIED",
            }
        )
    (output / "package_metadata_index.json").write_text(
        json.dumps(metadata_records, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    host = {
        "platform": platform.platform(),
        "python_version": sys.version,
        "python_executable": sys.executable,
        "os_name": os.name,
        "machine": platform.machine(),
        "processor": platform.processor(),
    }
    (output / "host.json").write_text(
        json.dumps(host, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    failures = [record for record in command_results if record["exit_code"] != 0]
    print(f"captured {len(command_results)} version commands; failures={len(failures)}")
    return 0 if not failures else 2


if __name__ == "__main__":
    sys.exit(main())
