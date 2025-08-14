from pathlib import Path

from codeowners_tool.codeowners import CodeOwners


def test_read_write_preserves_comments(tmp_path: Path):
    file = tmp_path / 'CODEOWNERS'
    file.write_text('# comment\n*.py alice\n')

    co = CodeOwners(file)
    co.set_owners('docs/', ['bob'])
    co.save()

    expected = '# comment\n*.py alice\ndocs/ bob\n'
    assert file.read_text() == expected

    assert co.owners_for_file(Path('test.py')) == ['alice']
    assert co.owners_for_file(Path('docs/readme.md')) == ['bob']
