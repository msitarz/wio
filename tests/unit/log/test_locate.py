# SPDX-License-Identifier: Apache-2.0
"""Tests for `wio.log.locate` against fakes of its ports."""

import re
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from wio.log import locate
from wio.log.locate import EVENTS_FILE, log_directory, log_files

if TYPE_CHECKING:
    from wio.env.ports import Directories
    from wio.io.ports import FileSystem, Repository


def _repository(identity: Path | Exception) -> Repository:
    """Make a `Repository` that gives an identity, or raises when given an error.

    Args:
        identity: The identity `identity` gives, or the error it raises.

    Returns:
        A mock, which type checking takes for the port.
    """
    repository = Mock()
    if isinstance(identity, Exception):
        repository.identity.side_effect = identity
    else:
        repository.identity.return_value = identity
    return repository


def _directories(home: Path) -> Directories:
    """Make `Directories` whose Wio home is fixed.

    Args:
        home: The path `wio_home` gives.

    Returns:
        A mock, which type checking takes for the port.
    """
    directories = Mock()
    directories.wio_home.return_value = home
    return directories


def test_the_location_is_made_of_the_identity_and_the_home(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-1: `locate_log` passes the identity and the home to `log_directory`."""
    # Given a Repository and Directories fakes and a log_directory that records
    # what it is given
    seen: list[tuple[Path, Path]] = []

    def record(identity: Path, home: Path) -> Path:
        """Record the arguments and give a fixed place.

        Args:
            identity: The identity given.
            home: The home given.

        Returns:
            A fixed place.
        """
        seen.append((identity, home))
        return Path("/place")

    monkeypatch.setattr(locate, "log_directory", record)

    # When locate_log runs
    found = locate.locate_log(
        _repository(Path("/w/app/.git")), _directories(Path("/h"))
    )

    # Then it gives what log_directory gave, for the identity and the home
    assert found == Path("/place")
    assert seen == [(Path("/w/app/.git"), Path("/h"))]


def test_the_error_of_the_repository_reaches_the_caller() -> None:
    """AC-4: `locate_log` raises what `Repository.identity` raises, unchanged."""
    # Given a Repository whose identity fails with a RuntimeError
    error = RuntimeError("not in a repository")

    # When locate_log runs
    # Then the same error is raised
    with pytest.raises(RuntimeError) as raised:
        locate.locate_log(_repository(error), _directories(Path("/h")))
    assert raised.value is error


def _filesystem(
    entries: list[str], directories: frozenset[str] = frozenset()
) -> FileSystem:
    """Make a `FileSystem` whose `list_dir` gives entries, in the order given.

    Args:
        entries: The names of the entries of the directory, in the order `list_dir`
            gives them.
        directories: The names among them that are directories.

    Returns:
        A mock, which type checking takes for the port.
    """
    filesystem = Mock()
    filesystem.list_dir.return_value = [Path("/log") / name for name in entries]

    def is_file(path: Path) -> bool:
        """Tell whether an entry is a file, which it is unless a directory.

        Args:
            path: The entry.

        Returns:
            False for the names that are directories.
        """
        return path.name not in directories

    filesystem.is_file.side_effect = is_file
    return filesystem


def test_two_clones_have_two_locations_under_one_home() -> None:
    """AC-1: the identities `/w/app/.git` and `/w/other/.git` have two digests."""
    # Given the identities of two clones and one home
    home = Path("/h")

    # When log_directory runs for each
    app = log_directory(Path("/w/app/.git"), home)
    other = log_directory(Path("/w/other/.git"), home)

    # Then they give /h/log/app-6f8609bd196b and /h/log/other-58e6d3787679
    assert app == Path("/h/log/app-6f8609bd196b")
    assert other == Path("/h/log/other-58e6d3787679")


def test_one_clone_under_two_homes_keeps_its_name() -> None:
    """AC-1: only the home differs between the two results."""
    # Given the identity /w/app/.git
    identity = Path("/w/app/.git")

    # When log_directory runs for the homes /h1 and /h2
    first = log_directory(identity, Path("/h1"))
    second = log_directory(identity, Path("/h2"))

    # Then the results are /h1/log/app-6f8609bd196b and /h2/log/app-6f8609bd196b
    assert first == Path("/h1/log/app-6f8609bd196b")
    assert second == Path("/h2/log/app-6f8609bd196b")


@pytest.mark.parametrize(
    ("identity", "prefix"),
    [
        ("/Users/x/Code/My App/.git", "my-app-"),
        ("/srv/git/app.git", "app-"),
        ("/w/.git", "w-"),
        ("/w/\u65e5\u672c/.git", "repo-"),
        ("/.git", "repo-"),
    ],
)
def test_the_name_of_a_log_tells_which_repository_it_is_for(
    identity: str, prefix: str
) -> None:
    """AC-2: names are slugs, `repo` when nothing is left, each ends in a digest."""
    # Given an identity of a clone and the home /h
    # When log_directory runs for it
    found = log_directory(Path(identity), Path("/h"))

    # Then the last component starts with the name and ends in 12 hex characters
    assert found.parent == Path("/h/log")
    assert re.fullmatch(re.escape(prefix) + "[0-9a-f]{12}", found.name)


def test_a_long_name_is_cut_without_the_dash_that_ends_it() -> None:
    """AC-2: a 59-character name is cut to 40 characters and trimmed of `-`."""
    # Given an identity whose repository name has 59 characters and a `-` as its 40th
    identity = Path("/w/" + "-".join(["a" * 9] * 6) + "/.git")

    # When log_directory runs for it
    found = log_directory(identity, Path("/h"))

    # Then the name is the first 40 characters without the `-` that ends them
    assert found.name.rsplit("-", 1)[0] == "-".join(["a" * 9] * 4)


def test_the_digest_decides_the_identity() -> None:
    """AC-2: two identities with one name differ in their digests."""
    # Given /a/b/app/.git and /a/c/app/.git
    # When log_directory runs for each
    first = log_directory(Path("/a/b/app/.git"), Path("/h"))
    second = log_directory(Path("/a/c/app/.git"), Path("/h"))

    # Then both names start with app- and the digests differ
    assert first.name.startswith("app-")
    assert second.name.startswith("app-")
    assert first.name != second.name


def test_the_files_of_a_log_are_the_lowercase_jsonl_files_in_order() -> None:
    """AC-3: other names, `B.JSONL` and a directory are left out."""
    # Given a FileSystem fake whose list_dir gives events.jsonl, a.jsonl, notes.txt,
    # B.JSONL and a directory c.jsonl, in the order of the fake
    filesystem = _filesystem(
        ["a.jsonl", "B.JSONL", "c.jsonl", "events.jsonl", "notes.txt"],
        frozenset({"c.jsonl"}),
    )

    # When log_files runs for it
    found = log_files(Path("/log"), filesystem)

    # Then it gives a.jsonl and events.jsonl, in that order
    assert found == (Path("/log/a.jsonl"), Path("/log/events.jsonl"))


def test_the_file_the_sink_appends_to_is_events_jsonl() -> None:
    """AC-3: `EVENTS_FILE` names the file a log holds."""
    # Given a FileSystem fake whose directory holds events.jsonl
    filesystem = _filesystem(["events.jsonl"])

    # When log_files runs for it
    found = log_files(Path("/log"), filesystem)

    # Then the result holds EVENTS_FILE, whose value is events.jsonl
    assert Path("/log") / EVENTS_FILE in found
    assert EVENTS_FILE == "events.jsonl"


def test_a_missing_directory_has_no_files() -> None:
    """AC-3: a directory the port reports as missing has no file."""
    # Given a FileSystem fake whose directory does not exist
    filesystem = Mock()
    filesystem.list_dir.side_effect = FileNotFoundError

    # When log_files runs for it
    found = log_files(Path("/log"), filesystem)

    # Then it gives no file
    assert found == ()


def test_a_path_that_is_a_file_raises_the_error_of_the_port() -> None:
    """AC-3: the `NotADirectoryError` of the port reaches the caller."""
    # Given a FileSystem fake whose list_dir raises NotADirectoryError
    error = NotADirectoryError("a file")
    filesystem = Mock()
    filesystem.list_dir.side_effect = error

    # When log_files runs for it
    # Then the NotADirectoryError of the port is raised unchanged
    with pytest.raises(NotADirectoryError) as raised:
        log_files(Path("/log"), filesystem)
    assert raised.value is error
