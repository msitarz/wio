# SPDX-License-Identifier: Apache-2.0
"""Tests for `GitHistory` and the index and tree reads of `GitRepository`.

They run without git: a scripted `subprocess.run` answers each git command by
its name, so each test says what the adapter asks and how it reads the answer.
"""

import subprocess
from pathlib import Path

import pytest

from tests.fakes import FakeEnvironment
from wio.io import adapters
from wio.models.commits import Commit

ID1 = "1" * 40
ID2 = "2" * 40
OK = subprocess.CompletedProcess([], 0, stdout="", stderr="")


def _done(stdout: str = "", code: int = 0, stderr: str = "") -> object:
    """Make a completed git process.

    Args:
        stdout: What it printed.
        code: Its exit code.
        stderr: What it said on the error stream.

    Returns:
        The completed process.
    """
    return subprocess.CompletedProcess([], code, stdout=stdout, stderr=stderr)


def _script(
    monkeypatch: pytest.MonkeyPatch, answers: dict[str, object]
) -> list[list[str]]:
    """Answer each git command by its name and record every command.

    Args:
        monkeypatch: The test's monkeypatch fixture.
        answers: The answer for each command name, such as `log` or `show`; a
            command with no entry succeeds and prints nothing. `rev-parse`
            answers the check that the directory is in a repository, and
            `rev-parse --verify` the resolution of a revision.

    Returns:
        The list that collects every command.
    """
    calls: list[list[str]] = []

    def run(command: list[str], **_: object) -> object:
        calls.append(command)
        name = next(arg for arg in command[1:] if not arg.startswith("--no-"))
        key = "rev-parse --verify" if "--verify" in command else name
        return answers.get(key, answers.get(name, OK))

    monkeypatch.setattr(subprocess, "run", run)
    return calls


def _history() -> adapters.GitHistory:
    """Make the adapter for a working directory of a fake.

    Returns:
        The adapter.
    """
    return adapters.GitHistory(FakeEnvironment(Path("/")))


def test_the_commits_of_a_range_are_read_in_the_order_git_gives(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-1: ids and messages come back without the trailing newline."""
    # Given a git whose log prints two commits
    out = f"{ID1}\0one\n\nbody\n\0{ID2}\0two\n\0"
    calls = _script(monkeypatch, {"log": _done(out)})

    # When the range is read
    commits = _history().history("a..b")

    # Then the commits are in that order, and git was asked for the oldest first
    assert commits == [Commit(ID1, "one\n\nbody"), Commit(ID2, "two")]
    log = next(c for c in calls if "log" in c)
    assert log[-3:] == ["--reverse", "--end-of-options", "a..b"]


def test_an_empty_range_has_no_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-1: a range with no commit gives an empty list."""
    # Given a git whose log prints nothing
    _script(monkeypatch, {})

    # When the range is read
    commits = _history().history("c3..c3")

    # Then there is no commit
    assert commits == []


def test_a_range_that_git_rejects_raises_value_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-1: git's own message, which names the range, is the error."""
    # Given a git that rejects the range
    answer = _done(code=128, stderr="fatal: bad revision 'nosuch..c3'\n")
    _script(monkeypatch, {"log": answer})

    # When the range is read
    # Then a `ValueError` carries git's message
    with pytest.raises(ValueError, match="nosuch"):
        _history().history("nosuch..c3")


def test_first_parents_ask_git_for_the_first_parent_walk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-2: the walk uses `--first-parent` and keeps git's newest-first order."""
    # Given a git that prints two commits
    calls = _script(monkeypatch, {"log": _done(f"{ID2}\0b\n\0{ID1}\0a\n\0")})

    # When the first parents of `HEAD` are read
    commits = _history().first_parents("HEAD")

    # Then the order is git's, and the walk followed first parents
    assert [c.id for c in commits] == [ID2, ID1]
    assert "--first-parent" in next(c for c in calls if "log" in c)


def test_a_revision_resolves_to_the_commit_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-3: the id of the commit the revision names, without the newline."""
    # Given a git that prints an id
    calls = _script(monkeypatch, {"rev-parse": _done(f"{ID1}\n")})

    # When `HEAD` is resolved
    resolved = _history().rev_parse("HEAD")

    # Then the id comes back, and a tag is peeled to its commit
    assert resolved == ID1
    assert calls[-1][-1] == "HEAD^{commit}"


def test_the_files_of_a_revision_are_sorted_relative_to_the_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-4: paths from the root of the tree, sorted, whatever git's order."""
    # Given a git that lists two paths
    calls = _script(monkeypatch, {"ls-tree": _done("sub/d.txt\0a.txt\0")})

    # When the files are listed
    files = _history().list_files("c2")

    # Then they are sorted, and git was asked for paths from the root
    assert files == [Path("a.txt"), Path("sub/d.txt")]
    assert "--full-tree" in next(c for c in calls if "ls-tree" in c)


def test_a_file_that_did_not_exist_is_none_and_a_bad_revision_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-4: a missing path gives `None`, an unknown revision `ValueError`."""
    # Given a git that finds no such file
    _script(monkeypatch, {"show": _done(code=128), "rev-parse": _done(ID1)})

    # When the file is read at a revision that exists
    content = _history().show("c3", Path("b.txt"))

    # Then there is none; and an unknown revision is refused
    assert content is None
    _script(
        monkeypatch,
        {"rev-parse --verify": _done(code=128, stderr="fatal: nosuch\n")},
    )
    with pytest.raises(ValueError, match="nosuch"):
        _history().show("nosuch", Path("b.txt"))


def test_a_file_is_read_exactly_as_git_stores_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-4: the trailing newline of a file is kept."""
    # Given a git that prints a file
    calls = _script(monkeypatch, {"show": _done("b\n"), "rev-parse": _done(ID1)})

    # When the file is read
    content = _history().show("c2", Path("sub/b.txt"))

    # Then the content is exact, and the path is named from the root
    assert content == "b\n"
    assert calls[-1][-1] == "c2:sub/b.txt"


def test_the_index_is_read_by_path_from_the_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-5: `:path` names the staged file, and a missing one is `None`."""
    # Given a git that prints a staged file
    calls = _script(monkeypatch, {"show": _done("staged\n")})
    repository = adapters.GitRepository(FakeEnvironment(Path("/")))

    # When the index is read, and then a file that git does not find
    staged = repository.show_index(Path("a.txt"))
    _script(monkeypatch, {"show": _done(code=128)})
    missing = repository.show_index(Path("new.txt"))

    # Then the staged content and none come back
    assert (staged, missing) == ("staged\n", None)
    assert calls[-1][-1] == ":a.txt"


@pytest.mark.parametrize(
    ("status", "dirty"), [("", False), (" M a.txt\n", True), ("?? u.txt\n", True)]
)
def test_the_tree_is_dirty_when_status_lists_anything(
    monkeypatch: pytest.MonkeyPatch, status: str, *, dirty: bool
) -> None:
    """AC-6: an empty status is clean, and takes no optional lock."""
    # Given a git whose status prints the given lines
    calls = _script(monkeypatch, {"status": _done(status)})
    repository = adapters.GitRepository(FakeEnvironment(Path("/")))

    # When dirtiness is asked for
    answer = repository.is_dirty()

    # Then it follows the status, and git took no optional lock
    assert answer is dirty
    assert "--no-optional-locks" in next(c for c in calls if "status" in c)


def test_a_directory_outside_a_repository_is_refused_by_every_member(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-7: each member raises `RuntimeError` that names the directory."""
    # Given a git that says the directory is not a repository
    _script(monkeypatch, {"rev-parse": _done(code=128, stderr="fatal: not a repo")})
    history = _history()
    repository = adapters.GitRepository(FakeEnvironment(Path("/")))
    calls = [
        lambda: history.rev_parse("HEAD"),
        lambda: history.history("a..b"),
        lambda: history.first_parents("HEAD"),
        lambda: history.list_files("HEAD"),
        lambda: history.show("HEAD", Path("a.txt")),
        lambda: repository.show_index(Path("a.txt")),
        repository.is_dirty,
    ]

    # When each member runs
    # Then each raises `RuntimeError` that names the working directory
    for call in calls:
        with pytest.raises(RuntimeError, match="working directory /"):
            call()
