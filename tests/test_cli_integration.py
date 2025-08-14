import os
from pathlib import Path

from git import Actor, Repo
from typer.testing import CliRunner

from codeowners_tool import cli


def commit_file(repo: Repo, path: Path, content: str, author: Actor):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    repo.index.add([str(path)])
    repo.index.commit("commit", author=author, committer=author)


def setup_repo(tmp_path: Path):
    repo = Repo.init(tmp_path)
    alice = Actor("Alice", "alice@example.com")
    bob = Actor("Bob", "bob@example.com")
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "dir" / "file2.txt"
    commit_file(repo, file1, "a1\n", alice)
    commit_file(repo, file2, "b1\n", alice)
    file1.write_text("a1\nb1\nb2\n")
    repo.index.add([str(file1)])
    repo.index.commit("bob updates file1", author=bob, committer=bob)
    return repo, alice, bob, file1, file2


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

    result = invoke(["generate", "--level", "file", "--top", "2"])
    assert result.exit_code == 0

    lines = (tmp_path / "CODEOWNERS").read_text().splitlines()
    assert "file1.txt Bob Alice" in lines
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
