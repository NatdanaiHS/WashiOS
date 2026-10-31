#!/usr/bin/env python3
"""Supplement PlatformIO package lists using a UTF-8 subprocess environment."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--pio", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite: {args.output}")
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    records = []
    for project in ("core", "bootloader", "demo-payload"):
        command = [str(args.pio.resolve()), "pkg", "list", "-d", str((args.repo_root / project).resolve())]
        completed = subprocess.run(
            command,
            cwd=args.repo_root.resolve(),
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        records.append(
            {
                "project": project,
                "command": command,
                "environment_override": {"PYTHONIOENCODING": "utf-8"},
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        )
    args.output.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    failures = [record for record in records if record["exit_code"] != 0]
    print(f"captured {len(records)} UTF-8 package lists; failures={len(failures)}")
    return 0 if not failures else 2


if __name__ == "__main__":
    sys.exit(main())
