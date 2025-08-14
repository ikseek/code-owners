from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import List

import typer
from rich import print

from .codeowners import CodeOwners, find_codeowners_file
from .gitutils import blame_file, list_tracked_files

app = typer.Typer(help="Manage GitHub CODEOWNERS file based on git history")


@app.command()
def add(pattern: str, owners: List[str]):
    """Add or replace owners for a given pattern."""
    root = Path.cwd()
    co_path = find_codeowners_file(root, create=True)
    co = CodeOwners(co_path)
    co.set_owners(pattern, owners)
    co.save()
    print(f"Updated {co_path} with {pattern} -> {owners}")


@app.command()
def generate(
    level: str = typer.Option("file", help="file or dir", case_sensitive=False),
    top: int = typer.Option(1, help="Top N owners for each entry"),
):
    """Generate CODEOWNERS from git history."""
    root = Path.cwd()
    co_path = find_codeowners_file(root, create=True)
    co = CodeOwners(co_path)
    files = list_tracked_files(root)
    if level.lower() == "dir":
        by_dir: defaultdict[Path, Counter[str]] = defaultdict(Counter)
        for file in files:
            rel = file.relative_to(root)
            counter = blame_file(file)
            by_dir[rel.parent].update(counter)
        for dirpath, counter in by_dir.items():
            owners = [name for name, _ in counter.most_common(top)]
            pattern = str(dirpath / "") if str(dirpath) != "." else "*"
            co.set_owners(pattern, owners)
    else:
        for file in files:
            rel = file.relative_to(root)
            counter = blame_file(file)
            owners = [name for name, _ in counter.most_common(top)]
            pattern = str(rel)
            co.set_owners(pattern, owners)
    co.save()
    print(f"Generated {co_path}")


@app.command("less-than")
def less_than(n: int):
    """List files with fewer than N owners."""
    root = Path.cwd()
    co = CodeOwners(find_codeowners_file(root))
    for file in list_tracked_files(root):
        rel = file.relative_to(root)
        owners = co.owners_for_file(rel)
        if len(owners) < n:
            print(rel)


@app.command("owned-by")
def owned_by(owner: str):
    """List files owned by a particular person."""
    root = Path.cwd()
    co = CodeOwners(find_codeowners_file(root))
    for file in list_tracked_files(root):
        rel = file.relative_to(root)
        owners = co.owners_for_file(rel)
        if owner in owners:
            print(rel)


@app.command()
def summary():
    """List project owners and amount of lines they own."""
    root = Path.cwd()
    co = CodeOwners(find_codeowners_file(root))
    owner_lines: Counter[str] = Counter()
    unowned = 0
    for file in list_tracked_files(root):
        rel = file.relative_to(root)
        owners = co.owners_for_file(rel)
        contributions = blame_file(file)
        if owners:
            for o in owners:
                owner_lines[o] += contributions.get(o, 0)
        else:
            unowned += sum(contributions.values())
    for owner, lines in owner_lines.most_common():
        print(f"{owner}: {lines}")
    print(f"unowned: {unowned}")


@app.command()
def suggest(path: Path, count: int = typer.Option(1, help="Number of candidates")):
    """Suggest additional owners for a file."""
    root = Path.cwd()
    file = path if path.is_absolute() else root / path
    contributions = blame_file(file)
    co = CodeOwners(find_codeowners_file(root))
    current = set(co.owners_for_file(path))
    shown = 0
    for author, lines in contributions.most_common():
        if author in current:
            continue
        print(f"{author}: {lines}")
        shown += 1
        if shown >= count:
            break


if __name__ == "__main__":
    app()
