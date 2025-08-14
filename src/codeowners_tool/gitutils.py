from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable

from git import Repo


def get_repo(root: Path | None = None) -> Repo:
    return Repo(root or Path.cwd(), search_parent_directories=True)


def list_tracked_files(root: Path) -> Iterable[Path]:
    repo = get_repo(root)
    files = repo.git.ls_files().splitlines()
    return [root / f for f in files]


def blame_file(path: Path) -> Counter:
    repo = get_repo(path.parent)
    counter: Counter[str] = Counter()
    try:
        blamed = repo.blame("HEAD", str(path))
    except Exception:
        return counter
    for commit, lines in blamed:
        name = commit.author.name
        counter[name] += len(lines)
    return counter


def aggregate_directory(path: Path) -> Counter:
    counter: Counter[str] = Counter()
    for file in list_tracked_files(path):
        counter.update(blame_file(file))
    return counter
