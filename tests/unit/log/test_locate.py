# SPDX-License-Identifier: Apache-2.0
"""Tests for `wio.log.locate` against fakes of its ports."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import override

import pytest

from tests.fakes import value_or_raise
from tests.unit.fakes import FakeDirectories, FakeRepository, MemoryFileSystem
from wio.log.locate import EVENTS_FILE, locate_log, log_directory, log_files


@dataclass(kw_only=True)
class ListedFileSystem(MemoryFileSystem):
    """An in-memory filesystem with a caller-supplied listing for one path.

    Attributes:
        directory: The path with a configured listing.
        listing: Entries in the order given by the port, or a listing failure.
    """

    directory: Path
    listing: tuple[Path, ...] | Exception

    @override
    def list_dir(self, path: Path) -> tuple[Path, ...]:
        """List the configured directory in its supplied order.

        Args:
            path: The directory to list.

        Returns:
            The supplied entries in order for the configured directory.

        Raises:
            AssertionError: The caller requested an unexpected directory.
            Exception: The configured failure, if any.
        """
        assert path == self.directory
        return value_or_raise(self.listing)


def test_the_location_is_made_of_the_identity_and_the_home() -> None:
    """AC-1 builds the clone's log path from its identity and the Wio home.

    The example fixes both the clone name and the digest of its identity.
    """
    # Given a repository at /w/app with its .git identity, and Wio home /h.
    repository = FakeRepository(top=Path("/w/app"))
    directories = FakeDirectories(Path("/h"))

    # When the log is located.
    found = locate_log(repository, directories)

    # Then the path uses that home and identifies the clone.
    assert found == Path("/h/log/app-6f8609bd196b")


def test_the_error_of_the_repository_reaches_the_caller() -> None:
    """AC-4 propagates the repository's identity error unchanged.

    Callers can use the original exception when reporting a location failure.
    """
    # Given a repository whose identity lookup fails.
    error = RuntimeError("not in a repository")
    repository = FakeRepository(identity_error=error)
    directories = FakeDirectories(Path("/h"))

    # When locating the log.
    with pytest.raises(RuntimeError) as raised:
        locate_log(repository, directories)

    # Then the original failure reaches the caller.
    assert raised.value is error


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
    """AC-3 selects lowercase JSONL files in the order supplied by the port.

    The file names are deliberately out of alphabetical order.
    """
    # Given a directory listing with two log files, other files and a directory.
    directory = Path("/log")
    events, upper, subdirectory, other_log, notes = (
        directory / name
        for name in ("events.jsonl", "B.JSONL", "c.jsonl", "a.jsonl", "notes.txt")
    )
    filesystem = ListedFileSystem(
        directory=directory,
        listing=(events, upper, subdirectory, other_log, notes),
        files=dict.fromkeys((events, upper, other_log, notes), ""),
    )

    # When the log files are listed.
    found = log_files(directory, filesystem)

    # Then only the lowercase JSONL files remain, in the supplied order.
    assert found == (events, other_log)


def test_the_file_the_sink_appends_to_is_events_jsonl() -> None:
    """AC-3 includes the sink's events file among the log files.

    The reader and writer share the same file name.
    """
    # Given a directory containing the sink's events file.
    directory = Path("/log")
    events = directory / "events.jsonl"
    filesystem = MemoryFileSystem(files={events: ""})

    # When the log files are listed.
    found = log_files(directory, filesystem)

    # Then the sink's file is among the results.
    assert found == (directory / EVENTS_FILE,)
    assert EVENTS_FILE == "events.jsonl"


def test_a_missing_directory_has_no_files() -> None:
    """AC-3 treats a missing log directory as an empty log.

    A listing failure for an absent directory is expected before the first write.
    """
    # Given a log directory that the filesystem reports as missing.
    directory = Path("/log")
    filesystem = ListedFileSystem(directory=directory, listing=FileNotFoundError())

    # When the log files are listed.
    found = log_files(directory, filesystem)

    # Then there are no log files.
    assert found == ()


def test_a_path_that_is_a_file_raises_the_error_of_the_port() -> None:
    """AC-3 propagates a listing failure for a non-directory path.

    The original error is available to the caller.
    """
    # Given a log path that the filesystem reports as a file.
    directory = Path("/log")
    error = NotADirectoryError("a file")
    filesystem = ListedFileSystem(directory=directory, listing=error)

    # When the log files are listed.
    with pytest.raises(NotADirectoryError) as raised:
        log_files(directory, filesystem)

    # Then the original error reaches the caller.
    assert raised.value is error
