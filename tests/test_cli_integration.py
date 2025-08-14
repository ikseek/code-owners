import os
import subprocess
from pathlib import Path

from click.testing import CliRunner

from codeowners_tool import cli


def git(cwd: Path, *args: str, env: dict | None = None) -> None:
    env_vars = os.environ.copy()
    if env:
        env_vars.update(env)
    subprocess.run(["git", *args], cwd=cwd, check=True, env=env_vars)


def commit_file(repo: Path, path: Path, content: str, author: tuple[str, str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    rel = path.relative_to(repo)
    git(repo, "add", str(rel))
    name, email = author
    env = {
        "GIT_AUTHOR_NAME": name,
        "GIT_AUTHOR_EMAIL": email,
        "GIT_COMMITTER_NAME": name,
        "GIT_COMMITTER_EMAIL": email,
    }
    git(repo, "commit", "-m", "commit", env=env)


def setup_repo(tmp_path: Path):
    git(tmp_path, "init")
    alice = ("Alice", "alice@example.com")
    bob = ("Bob", "bob@example.com")
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "dir" / "file2.txt"
    commit_file(tmp_path, file1, "a1\n", alice)
    commit_file(tmp_path, file2, "b1\n", alice)
    file1.write_text("a1\nb1\nb2\n")
    rel1 = file1.relative_to(tmp_path)
    git(
        tmp_path,
        "add",
        str(rel1),
    )
    env = {
        "GIT_AUTHOR_NAME": bob[0],
        "GIT_AUTHOR_EMAIL": bob[1],
        "GIT_COMMITTER_NAME": bob[0],
        "GIT_COMMITTER_EMAIL": bob[1],
    }
    git(tmp_path, "commit", "-m", "bob updates file1", env=env)
    return tmp_path, alice[0], bob[0], file1, file2


def run_in_repo(path: Path, func):
    cwd = os.getcwd()
    os.chdir(path)
    try:
        return func()
    finally:
        os.chdir(cwd)


def test_generate_file_level_and_queries(tmp_path: Path):
    setup_repo(tmp_path)
    runner = CliRunner()

    def invoke(args):
        return run_in_repo(tmp_path, lambda: runner.invoke(cli.app, args))

    result = invoke(["generate", "--level", "file", "--top", "1"])
    assert result.exit_code == 0

    lines = (tmp_path / "CODEOWNERS").read_text().splitlines()
    assert "file1.txt Bob" in lines
    assert "dir/file2.txt Alice" in lines

    res = invoke(["less-than", "2"])
    assert res.exit_code == 0
    assert "file1.txt" in res.stdout
    assert "dir/file2.txt" in res.stdout

    res = invoke(["owned-by", "Bob"])
    assert res.exit_code == 0
    assert "file1.txt" in res.stdout
    assert "dir/file2.txt" not in res.stdout

    res = invoke(["summary"])
    assert res.exit_code == 0
    assert "Bob: 2" in res.stdout
    assert "Alice: 1" in res.stdout
    assert "unowned: 0" in res.stdout

    res = invoke(["suggest", "file1.txt"])
    assert res.exit_code == 0
    assert "Alice: 1" in res.stdout


def test_generate_directory_level(tmp_path: Path):
    setup_repo(tmp_path)
    runner = CliRunner()

    def invoke(args):
        return run_in_repo(tmp_path, lambda: runner.invoke(cli.app, args))

    result = invoke(["generate", "--level", "dir", "--top", "1"])
    assert result.exit_code == 0

    lines = (tmp_path / "CODEOWNERS").read_text().splitlines()
    assert "* Bob" in lines
    assert "dir/ Alice" in lines
