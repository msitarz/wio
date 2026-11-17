# SPDX-License-Identifier: Apache-2.0
"""Tests of `GitHistory` and of the index and tree reads of `GitRepository`.

The examples use a temporary repository: `c1` adds `a.txt` and `sub/d.txt`, a
branch `side` forks from `c1` with `s1` that adds `s.txt`, and on the main branch
`c2` adds `b.txt` and `c3` merges `side` and deletes `b.txt`. Each commit is
tagged with its name.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.fakes import FakeEnvironment
from tests.support import enter, git
from wio.env.adapters import ProcessEnvironment
from wio.io import adapters
lazy from tests.sandbox import Sandbox

if TYPE_CHECKING:
    from collections.abc import Callable

    from wio.io.ports import History, Repository


@dataclass(frozen=True)
class Built:
    """The repository of the examples.

    Attributes:
        ids: The full id of each commit, by name.
        messages: The message of each commit as committed, by name.
    """

    ids: dict[str, str]
    messages: dict[str, str]


def _commit(sandbox: Sandbox, name: str) -> str:
    """Commit the index with a subject, a body and a trailer paragraph.

    Args:
        sandbox: The repository to commit in.
        name: The commit's name, which is also its tag.

    Returns:
        The message as committed, without its trailing newline.
    """
    subject, body, trailer = (
        f"{name}: subject",
        f"The body of {name}.",
        "Wio-Work: none",
    )
    git(sandbox, "commit", "-q", "-m", subject, "-m", body, "-m", trailer, check=True)
    git(sandbox, "tag", name, check=True)
    return f"{subject}\n\n{body}\n\n{trailer}"


def _write(sandbox: Sandbox, name: str, text: str) -> None:
    """Write a file in the sandbox and stage it.

    Args:
        sandbox: The repository.
        name: The path relative to the root.
        text: The content.
    """
    path = sandbox.root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    git(sandbox, "add", name, check=True)


def _build(sandbox: Sandbox) -> Built:
    """Create the repository of the examples.

    Args:
        sandbox: An empty repository directory.

    Returns:
        The commits' ids and messages.
    """
    git(sandbox, "init", "-q", "-b", "main", check=True)
    _write(sandbox, "a.txt", "a\n")
    _write(sandbox, "sub/d.txt", "d\n")
    messages = {"c1": _commit(sandbox, "c1")}
    git(sandbox, "checkout", "-q", "-b", "side", check=True)
    _write(sandbox, "s.txt", "s\n")
    messages["s1"] = _commit(sandbox, "s1")
    git(sandbox, "checkout", "-q", "main", check=True)
    _write(sandbox, "b.txt", "b\n")
    messages["c2"] = _commit(sandbox, "c2")
    git(sandbox, "merge", "-q", "--no-ff", "--no-commit", "side", check=True)
    git(sandbox, "rm", "-q", "b.txt", check=True)
    messages["c3"] = _commit(sandbox, "c3")
    ids = {n: git(sandbox, "rev-parse", n, check=True).stdout.strip() for n in messages}
    return Built(ids, messages)


def _history(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> tuple[Built, History, Repository]:
    """Build the repository and wire both adapters to it.

    Args:
        sandbox: An empty repository directory.
        monkeypatch: The test's monkeypatch, which enters the sandbox.

    Returns:
        The repository's commits and the adapters, as the ports they satisfy.
    """
    built = _build(sandbox)
    enter(sandbox, monkeypatch)
    environment = ProcessEnvironment()
    return built, adapters.GitHistory(environment), adapters.GitRepository(environment)


@pytest.mark.slow
def test_a_range_lists_its_commits_oldest_first(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-1: a range, an empty range and a rejected range."""
    # Given the repository
    built, history, _ = _history(sandbox, monkeypatch)

    # When `history("c1..c3")`, `history("c3..c3")` and `history("nosuch..c3")` run
    commits = history.history("c1..c3")
    empty = history.history("c3..c3")
    with pytest.raises(ValueError, match="nosuch"):
        history.history("nosuch..c3")

    # Then the first holds `s1` and `c2` in either order and then `c3`, each with
    # its full id and its message as committed, and the second holds none
    assert {c.id for c in commits[:2]} == {built.ids["s1"], built.ids["c2"]}
    assert commits[2].id == built.ids["c3"]
    assert all(len(c.id) == 40 for c in commits)
    by_id = {c.id: c.message for c in commits}
    assert by_id[built.ids["c3"]] == built.messages["c3"]
    assert empty == []


@pytest.mark.slow
def test_first_parents_come_newest_first(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-2: a walk over a merge leaves out the merged branch."""
    # Given the repository with the merge commit `c3`
    built, history, _ = _history(sandbox, monkeypatch)

    # When `first_parents("HEAD")` and `first_parents("nosuch")` run
    commits = history.first_parents("HEAD")
    with pytest.raises(ValueError, match="nosuch"):
        history.first_parents("nosuch")

    # Then the first holds `c3`, `c2` and `c1`, and not `s1`
    assert [c.id for c in commits] == [built.ids[n] for n in ("c3", "c2", "c1")]


@pytest.mark.slow
def test_a_revision_resolves_to_a_full_id(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-3: a name resolves and an unknown name is refused."""
    # Given the repository
    built, history, _ = _history(sandbox, monkeypatch)

    # When `rev_parse("HEAD")` and `rev_parse("nosuch")` run
    resolved = history.rev_parse("HEAD")
    with pytest.raises(ValueError, match="nosuch"):
        history.rev_parse("nosuch")

    # Then the first is the full id of `c3`
    assert resolved == built.ids["c3"]


@pytest.mark.slow
def test_a_file_is_read_as_it_was_at_a_revision(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-4: the files and the content of a revision, from any directory."""
    # Given the repository, whose `b.txt` was added by `c2` and deleted by `c3`
    _, history, _ = _history(sandbox, monkeypatch)

    # When the files and the content are read, then from `sub`, and for `nosuch`
    files = history.list_files("c2")
    added = history.show("c2", Path("b.txt"))
    deleted = history.show("c3", Path("b.txt"))
    monkeypatch.chdir(sandbox.root / "sub")
    from_sub = history.list_files("c2")
    with pytest.raises(ValueError, match="nosuch"):
        history.list_files("nosuch")
    with pytest.raises(ValueError, match="nosuch"):
        history.show("nosuch", Path("b.txt"))

    # Then they are the sorted paths, the content, none and the same paths
    assert files == [Path("a.txt"), Path("b.txt"), Path("sub/d.txt")]
    assert added == "b\n"
    assert deleted is None
    assert from_sub == files


@pytest.mark.slow
def test_a_file_is_read_as_it_is_staged(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-5: a staged file that differs from the tree and from `HEAD`."""
    # Given `a.txt` staged with one content, changed in the tree, and `new.txt`
    # that is not staged
    _, _, repository = _history(sandbox, monkeypatch)
    _write(sandbox, "a.txt", "staged\n")
    (sandbox.root / "a.txt").write_text("in the tree\n", encoding="utf-8")
    (sandbox.root / "new.txt").write_text("new\n", encoding="utf-8")

    # When the index is read for each, then from `sub`
    staged = repository.show_index(Path("a.txt"))
    missing = repository.show_index(Path("new.txt"))
    monkeypatch.chdir(sandbox.root / "sub")
    from_sub = repository.show_index(Path("a.txt"))

    # Then the staged content, none and the staged content again come back
    assert (staged, missing, from_sub) == ("staged\n", None, "staged\n")


@pytest.mark.slow
def test_the_working_tree_is_reported_as_dirty_or_clean(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-6: changes of every kind, and an ignored file."""
    # Given a clean repository with a committed ignore rule
    _, _, repository = _history(sandbox, monkeypatch)
    _write(sandbox, ".gitignore", "*.log\n")
    git(sandbox, "commit", "-q", "-m", "ignore", check=True)
    clean = repository.is_dirty()

    # When an ignored file is made, then each kind of change in turn
    (sandbox.root / "x.log").write_text("x\n", encoding="utf-8")
    ignored = repository.is_dirty()
    (sandbox.root / "a.txt").write_text("changed\n", encoding="utf-8")
    modified = repository.is_dirty()
    git(sandbox, "checkout", "-q", "--", "a.txt", check=True)
    _write(sandbox, "added.txt", "added\n")
    staged = repository.is_dirty()
    git(sandbox, "rm", "-q", "-f", "added.txt", check=True)
    (sandbox.root / "untracked.txt").write_text("u\n", encoding="utf-8")
    untracked = repository.is_dirty()

    # Then only the clean and the ignored repository are not dirty
    assert (clean, ignored, modified, staged, untracked) == (
        False,
        False,
        True,
        True,
        True,
    )


@pytest.mark.slow
def test_a_directory_outside_a_repository_is_refused_by_every_member(
    tmp_path: Path,
) -> None:
    """AC-7: each member raises `RuntimeError` that names the directory."""
    # Given a working directory that is not in a repository
    outside = tmp_path / "outside"
    outside.mkdir()
    environment = FakeEnvironment(outside)
    history, repository = (
        adapters.GitHistory(environment),
        adapters.GitRepository(environment),
    )
    history_calls = {
        "rev_parse": ("HEAD",),
        "history": ("HEAD~1..HEAD",),
        "first_parents": ("HEAD",),
        "list_files": ("HEAD",),
        "show": ("HEAD", Path("a.txt")),
    }
    calls: list[tuple[Callable[..., object], tuple[object, ...]]] = [
        (getattr(history, name), args) for name, args in history_calls.items()
    ]
    calls += [(repository.show_index, (Path("a.txt"),)), (repository.is_dirty, ())]

    # When each member runs
    # Then each raises `RuntimeError` that names the working directory
    for call, args in calls:
        with pytest.raises(RuntimeError) as caught:
            call(*args)
        assert str(outside) in str(caught.value)


def _snapshot(sandbox: Sandbox) -> dict[str, bytes]:
    """Read every byte of the repository that a read must not change.

    Args:
        sandbox: The repository.

    Returns:
        The content of `.git/index`, `HEAD`, each loose ref and each
        working-tree file, by path.
    """
    root = sandbox.root
    paths = [root / ".git" / "index", root / ".git" / "HEAD"]
    paths += [p for p in (root / ".git" / "refs").rglob("*") if p.is_file()]
    paths += [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]
    return {str(p.relative_to(root)): p.read_bytes() for p in paths if p.exists()}


@pytest.mark.slow
def test_a_read_leaves_the_repository_as_it_was(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-8: the index, the refs and the tree are the same after every read."""
    # Given the repository with a staged file and a modified tracked file
    _, history, repository = _history(sandbox, monkeypatch)
    _write(sandbox, "staged.txt", "staged\n")
    (sandbox.root / "a.txt").write_text("modified\n", encoding="utf-8")
    before = _snapshot(sandbox)

    # When every member runs
    history.rev_parse("HEAD")
    history.history("c1..c3")
    history.first_parents("HEAD")
    history.list_files("c2")
    history.show("c2", Path("b.txt"))
    repository.show_index(Path("staged.txt"))
    repository.is_dirty()

    # Then the bytes of the index, the refs and the tree are the same
    assert _snapshot(sandbox) == before


@pytest.mark.slow
def test_line_endings_come_back_as_committed(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-1, AC-4, AC-5: a CRLF in a file or a message is not turned into an LF."""
    # Given a file and a commit message with CRLF line endings
    _, history, repository = _history(sandbox, monkeypatch)
    (sandbox.root / "crlf.txt").write_bytes(b"a\r\nb\r\n")
    git(sandbox, "add", "crlf.txt", check=True)
    message = sandbox.root.parent / "message"
    message.write_bytes(b"crlf\r\n\r\nbody\r\n")
    git(sandbox, "commit", "-q", "--cleanup=verbatim", "-F", str(message), check=True)
    (sandbox.root / "staged.txt").write_bytes(b"x\r\ny\r\n")
    git(sandbox, "add", "staged.txt", check=True)

    # When the file, the message and the staged file are read
    content = history.show("HEAD", Path("crlf.txt"))
    commit = history.first_parents("HEAD")[0]
    staged = repository.show_index(Path("staged.txt"))

    # Then every carriage return is still there
    assert content == "a\r\nb\r\n"
    assert commit.message.startswith("crlf\r\n\r\nbody")
    assert staged == "x\r\ny\r\n"


@pytest.mark.slow
def test_a_directory_is_not_a_file(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-4, AC-5: a path that names a directory reads as no file."""
    # Given the repository, in which `sub` is a directory
    _, history, repository = _history(sandbox, monkeypatch)

    # When the directory is read at a revision and in the index
    at_revision = history.show("c1", Path("sub"))
    staged = repository.show_index(Path("sub"))

    # Then both are none
    assert (at_revision, staged) == (None, None)
