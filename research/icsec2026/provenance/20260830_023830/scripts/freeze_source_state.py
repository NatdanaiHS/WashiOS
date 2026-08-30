#!/usr/bin/env python3
"""Freeze commit/diff/status and selected untracked experiment source files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


SELECTED_UNTRACKED = (
    "demo-payload/src/HostModeCommandParser.hpp",
    "demo-payload/test/test_host_mode_command/test_main.cpp",
    "research/icsec2026/NEXT_TASK.md",
    "research/icsec2026/SESSION_STATE.md",
    "research/icsec2026/injector/requirements.txt",
    "research/icsec2026/injector/run_payload_campaign.py",
    "research/icsec2026/injector/run_n0_control.py",
    "research/icsec2026/injector/summarize_payload_campaign.py",
    "research/icsec2026/injector/create_sha256_inventory.py",
    "research/icsec2026/injector/test_run_payload_campaign.py",
    "research/icsec2026/injector/test_n0_control.py",
    "research/icsec2026/injector/test_campaign_summary.py",
    "research/icsec2026/injector/test_sha256_inventory.py",
)


def git(repo: Path, *arguments: str) -> bytes:
    return subprocess.check_output(["git", *arguments], cwd=repo)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    output = args.output_dir.resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite source-state bundle: {output}")
    output.mkdir(parents=True)

    commit = git(repo, "rev-parse", "HEAD").decode("ascii").strip()
    branch = git(repo, "branch", "--show-current").decode("utf-8").strip()
    (output / "commit.json").write_text(
        json.dumps({"commit": commit, "branch": branch}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "tracked_worktree.patch").write_bytes(git(repo, "diff", "--binary", "HEAD"))
    (output / "staged.patch").write_bytes(git(repo, "diff", "--binary", "--cached", "HEAD"))
    (output / "git_status_porcelain_v1.txt").write_bytes(
        git(repo, "status", "--porcelain=v1", "-uall")
    )
    (output / "tracked_files.txt").write_bytes(git(repo, "ls-files"))

    copies = output / "untracked_source_copies"
    records = []
    missing = []
    for relative in SELECTED_UNTRACKED:
        source = repo / relative
        if not source.is_file():
            missing.append(relative)
            continue
        destination = copies / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        records.append(
            {
                "repository_path": relative,
                "bundle_path": destination.relative_to(output).as_posix(),
                "byte_count": destination.stat().st_size,
                "sha256": sha256_file(destination),
            }
        )
    with (output / "untracked_source_inventory.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=("repository_path", "bundle_path", "byte_count", "sha256")
        )
        writer.writeheader()
        writer.writerows(records)
    report = {
        "schema_version": 1,
        "commit": commit,
        "branch": branch,
        "selected_untracked_count": len(records),
        "missing_selected_files": missing,
        "raw_datasets_duplicated": False,
        "dataset_reference": "research/icsec2026/runs/full_20260830_seed20260830_n30/",
        "dataset_inventory_sha256": "DC7A2CD54F1CF1E3DA9E3F35DCACFD921E2F5D8828BF2411C4F7874252C5CCCD",
    }
    (output / "source_state_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, sort_keys=True))
    return 0 if not missing else 2


if __name__ == "__main__":
    sys.exit(main())
