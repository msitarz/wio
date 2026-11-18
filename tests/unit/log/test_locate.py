# SPDX-License-Identifier: Apache-2.0
"""Tests for `wio.log.locate` against fakes of its ports."""

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from wio.log import locate

if TYPE_CHECKING:
    from wio.env.ports import Directories
    from wio.io.ports import Repository


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


@pytest.mark.skip(reason="stub of the architecture stage")
def test_two_clones_have_two_locations_under_one_home() -> None:
    """AC-1: the identities `/w/app/.git` and `/w/other/.git` have two digests."""
    # Given the identities of two clones and one home
    # When log_directory runs for each
    # Then they give /h/log/app-6f8609bd196b and /h/log/other-58e6d3787679


@pytest.mark.skip(reason="stub of the architecture stage")
def test_one_clone_under_two_homes_keeps_its_name() -> None:
    """AC-1: only the home differs between the two results."""
    # Given the identity /w/app/.git and the homes /h1 and /h2
    # When log_directory runs for each
    # Then the results are /h1/log/app-6f8609bd196b and /h2/log/app-6f8609bd196b


@pytest.mark.skip(reason="stub of the architecture stage")
def test_the_name_of_a_log_tells_which_repository_it_is_for() -> None:
    """AC-2: names are slugs, `repo` when nothing is left, each ends in a digest."""
    # Given the identities /Users/x/Code/My App/.git, /srv/git/app.git, /w/.git,
    # /w/日本/.git and /.git, each with the home /h
    # When log_directory runs for each
    # Then the last components start with my-app-, app-, w-, repo- and repo-, and
    # each ends in 12 lowercase hexadecimal characters


@pytest.mark.skip(reason="stub of the architecture stage")
def test_a_long_name_is_cut_without_the_dash_that_ends_it() -> None:
    """AC-2: a 59-character name is cut to 40 characters and trimmed of `-`."""
    # Given an identity whose repository name has a `-` as its 40th character
    # When log_directory runs for it
    # Then the name is the first 40 characters without that `-`


@pytest.mark.skip(reason="stub of the architecture stage")
def test_the_digest_decides_the_identity() -> None:
    """AC-2: two identities with one name differ in their digests."""
    # Given /a/b/app/.git and /a/c/app/.git
    # When log_directory runs for each
    # Then both names start with app- and the digests differ


@pytest.mark.skip(reason="stub of the architecture stage")
def test_the_files_of_a_log_are_the_lowercase_jsonl_files_in_order() -> None:
    """AC-3: other names, `B.JSONL` and a directory are left out."""
    # Given a FileSystem fake whose list_dir gives events.jsonl, a.jsonl, notes.txt,
    # B.JSONL and a directory c.jsonl in its sorted order
    # When log_files runs for it
    # Then it gives a.jsonl and events.jsonl, in that order


@pytest.mark.skip(reason="stub of the architecture stage")
def test_the_file_the_sink_appends_to_is_events_jsonl() -> None:
    """AC-3: `EVENTS_FILE` names the file a log holds."""
    # Given a directory that holds events.jsonl
    # When log_files runs for it
    # Then the result holds EVENTS_FILE, whose value is events.jsonl


@pytest.mark.skip(reason="stub of the architecture stage")
def test_a_missing_directory_has_no_files() -> None:
    """AC-3: a directory the port reports as missing has no file."""
    # Given a FileSystem fake whose directory does not exist
    # When log_files runs for it
    # Then it gives no file


@pytest.mark.skip(reason="stub of the architecture stage")
def test_a_path_that_is_a_file_raises_the_error_of_the_port() -> None:
    """AC-3: the `NotADirectoryError` of the port reaches the caller."""
    # Given a path that is a file
    # When log_files runs for it
    # Then the NotADirectoryError of the port is raised unchanged
