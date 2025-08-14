# codeowners-tool

CLI tool to manage GitHub CODEOWNERS files using git history.

## Installation

Use [uv](https://github.com/astral-sh/uv) to install or build the package.

## Usage

```
codeowners-tool --help
```

## Development

Enable the git hooks to run formatting and lint checks on each commit:

```
git config core.hooksPath githooks
```

The hook runs `scripts/lint.sh`, which verifies Ruff formatting and static
analysis. The same script is used in CI.
