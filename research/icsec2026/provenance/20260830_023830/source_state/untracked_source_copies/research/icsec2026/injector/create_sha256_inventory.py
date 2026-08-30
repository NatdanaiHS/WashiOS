#!/usr/bin/env python3
"""Create an exclusive, deterministic SHA-256 inventory for dataset artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest().upper()


def collect_files(repo_root: Path, includes: list[Path], output: Path) -> list[Path]:
    collected: set[Path] = set()
    for requested in includes:
        path = requested.resolve()
        try:
            path.relative_to(repo_root)
        except ValueError as exc:
            raise ValueError(f"included path is outside repository: {path}") from exc
        if path.is_file():
            collected.add(path)
        elif path.is_dir():
            collected.update(candidate.resolve() for candidate in path.rglob("*") if candidate.is_file())
        else:
            raise FileNotFoundError(path)
    collected.discard(output.resolve())
    return sorted(collected, key=lambda path: path.relative_to(repo_root).as_posix())


def create_inventory(repo_root: Path, includes: list[Path], output: Path) -> int:
    repo_root = repo_root.resolve()
    output = output.resolve()
    files = collect_files(repo_root, includes, output)
    with output.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("sha256", "size_bytes", "path"))
        writer.writeheader()
        for path in files:
            writer.writerow(
                {
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                    "path": path.relative_to(repo_root).as_posix(),
                }
            )
    return len(files)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--include", required=True, action="append", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        count = create_inventory(args.repo_root, args.include, args.output)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"inventoried {count} files in {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
