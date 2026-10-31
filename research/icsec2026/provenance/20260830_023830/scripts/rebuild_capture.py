#!/usr/bin/env python3
"""Clean-build one PlatformIO environment and freeze its outputs without upload."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pio", required=True, type=Path)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--project", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    if output_dir.exists():
        raise SystemExit(f"refusing to overwrite rebuild output: {output_dir}")
    output_dir.mkdir(parents=True)
    repo_root = args.repo_root.resolve()
    project_dir = repo_root / args.project
    commands = [
        [str(args.pio.resolve()), "run", "-d", str(project_dir), "-e", args.environment, "-t", "clean"],
        [str(args.pio.resolve()), "run", "-d", str(project_dir), "-e", args.environment],
    ]
    if any("upload" in part.lower() for command in commands for part in command):
        raise SystemExit("internal safety check rejected upload target")

    started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds")
    log_parts = []
    exit_codes = []
    for command in commands:
        completed = subprocess.run(command, cwd=repo_root, capture_output=True, text=True, check=False)
        exit_codes.append(completed.returncode)
        log_parts.append("COMMAND: " + subprocess.list2cmdline(command) + "\n")
        log_parts.append(completed.stdout)
        log_parts.append(completed.stderr)
        if completed.returncode != 0:
            break
    finished = dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds")
    (output_dir / "build.log").write_text("".join(log_parts), encoding="utf-8")

    source_build = project_dir / ".pio" / "build" / args.environment
    artifacts: dict[str, object] = {}
    if exit_codes and all(code == 0 for code in exit_codes):
        for name in ("firmware.bin", "firmware.elf", "firmware.hex", "firmware.map"):
            source = source_build / name
            if source.is_file():
                destination = output_dir / name
                shutil.copyfile(source, destination)
                artifacts[name] = {
                    "byte_count": destination.stat().st_size,
                    "sha256": sha256_file(destination),
                }

    report = {
        "schema_version": 1,
        "project": args.project,
        "environment": args.environment,
        "commands": commands,
        "safety": "Clean and build targets only; no upload/program operation requested.",
        "started_host_time": started,
        "finished_host_time": finished,
        "exit_codes": exit_codes,
        "status": "COMPLETE" if len(exit_codes) == 2 and all(code == 0 for code in exit_codes) else "FAILED",
        "artifacts": artifacts,
    }
    (output_dir / "build_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "COMPLETE" and "firmware.bin" in artifacts else 2


if __name__ == "__main__":
    sys.exit(main())
