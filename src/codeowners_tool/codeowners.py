from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import pathspec


@dataclass
class Rule:
    pattern: str
    owners: List[str]


@dataclass
class Line:
    original: str
    rule: Optional[Rule] = None


class CodeOwners:
    """Utility to read and write CODEOWNERS file while preserving comments."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.lines: List[Line] = []
        if path.exists():
            self.load()

    def load(self) -> None:
        self.lines = []
        for raw in self.path.read_text().splitlines():
            if raw.strip() == "" or raw.lstrip().startswith("#"):
                self.lines.append(Line(original=raw))
            else:
                parts = raw.split()
                pattern, owners = parts[0], parts[1:]
                self.lines.append(Line(original=raw, rule=Rule(pattern, owners)))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w") as fh:
            for line in self.lines:
                if line.rule:
                    fh.write(f"{line.rule.pattern} {' '.join(line.rule.owners)}\n")
                else:
                    fh.write(f"{line.original}\n")

    def find_rule(self, pattern: str) -> Optional[Rule]:
        for line in self.lines:
            if line.rule and line.rule.pattern == pattern:
                return line.rule
        return None

    def set_owners(self, pattern: str, owners: List[str]) -> None:
        rule = self.find_rule(pattern)
        if rule:
            rule.owners = owners
        else:
            self.lines.append(Line(original="", rule=Rule(pattern, owners)))

    def rules(self) -> List[Rule]:
        return [line.rule for line in self.lines if line.rule]

    def owners_for_file(self, filepath: Path) -> List[str]:
        """Return owners for a file path relative to repo root."""
        rel = str(filepath)
        for line in self.lines:
            if not line.rule:
                continue
            spec = pathspec.PathSpec.from_lines("gitwildmatch", [line.rule.pattern])
            if spec.match_file(rel):
                return line.rule.owners
        return []


# Typical locations for CODEOWNERS file according to GitHub docs.
CODEOWNERS_LOCATIONS = [
    Path("CODEOWNERS"),
    Path(".github") / "CODEOWNERS",
    Path("docs") / "CODEOWNERS",
]


def find_codeowners_file(root: Path, create: bool = False) -> Path:
    for location in CODEOWNERS_LOCATIONS:
        candidate = root / location
        if candidate.exists():
            return candidate
    # default to root CODEOWNERS
    candidate = root / "CODEOWNERS"
    if create:
        candidate.touch()
    return candidate
