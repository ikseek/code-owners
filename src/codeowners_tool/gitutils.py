from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Iterable
import subprocess


def list_tracked_files(root: Path) -> Iterable[Path]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [root / f for f in result.stdout.splitlines()]


def blame_file(path: Path) -> Counter:
    counter: Counter[str] = Counter()
    try:
        result = subprocess.run(
            ["git", "-C", str(path.parent), "blame", "--line-porcelain", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return counter
    for line in result.stdout.splitlines():
        if line.startswith("author "):
            counter[line[7:]] += 1
    return counter


def aggregate_directory(path: Path) -> Counter:
    counter: Counter[str] = Counter()
    for file in list_tracked_files(path):
        counter.update(blame_file(file))
    return counter
