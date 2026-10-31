#!/usr/bin/env python3
"""Capture versions/hashes for the exact versioned toolchain selected by a build."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite: {args.output}")
    root = args.toolchain_dir.resolve()
    records = []
    for name in ("arm-none-eabi-gcc.exe", "arm-none-eabi-g++.exe", "arm-none-eabi-objcopy.exe"):
        executable = root / "bin" / name
        completed = subprocess.run(
            [str(executable), "--version"], capture_output=True, text=True, check=False
        )
        records.append(
            {
                "path": str(executable),
                "exit_code": completed.returncode,
                "version_stdout": completed.stdout,
                "version_stderr": completed.stderr,
                "byte_count": executable.stat().st_size,
                "sha256": sha256_file(executable),
            }
        )
    package_json = root / "package.json"
    result = {
        "schema_version": 1,
        "selection_basis": "PlatformIO clean build logs for both G431 environments report toolchain-gccarmnoneeabi @ 1.70201.0 (7.2.1)",
        "toolchain_directory": str(root),
        "executables": records,
        "package_metadata": {
            "path": str(package_json),
            "byte_count": package_json.stat().st_size,
            "sha256": sha256_file(package_json),
            "content": json.loads(package_json.read_text(encoding="utf-8")),
        },
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    failures = [record for record in records if record["exit_code"] != 0]
    print(f"captured exact selected toolchain; failures={len(failures)}")
    return 0 if not failures else 2


if __name__ == "__main__":
    sys.exit(main())
