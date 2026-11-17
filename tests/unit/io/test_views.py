# SPDX-License-Identifier: Apache-2.0
"""Tests for the read-only views of a repository as a `FileSystem`, without git."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest

from tests.unit.fakes import MemoryFileSystem
from wio.io.views import HeadFiles, IndexFiles

if TYPE_CHECKING:
    from wio.io.ports import History, Repository

ROOT = Path("/r")


@dataclass
class FakeHistory:
    """A `History` of one revision that lists and shows a dictionary of files."""

    files: dict[str, str]
    unborn: bool = False
    listed: list[str] = field(default_factory=list)

    def list_files(self, revision: str) -> list[Path]:
        """List the files of the revision, or refuse when there is no commit.

        Args:
            revision: The revision, recorded.

        Returns:
            The paths, sorted.

        Raises:
            ValueError: If the fake has no commit.
        """
        self.listed.append(revision)
        if self.unborn:
            message = f"Not a valid object name {revision}"
            raise ValueError(message)
        return sorted(Path(name) for name in self.files)

    def show(self, revision: str, path: Path) -> str | None:  # noqa: ARG002
        """Read a file of the revision.

        Args:
            revision: The revision.
            path: The file.

        Returns:
            Its text, or `None` when the fake has no such file.
        """
        return self.files.get(path.as_posix())


@dataclass
class FakeIndex:
    """A `Repository` whose index holds a dictionary of files."""

    staged: dict[str, str]

    def show_index(self, path: Path) -> str | None:
        """Read a staged file.

        Args:
            path: The file.

        Returns:
            Its text, or `None` when it is not staged.
        """
        return self.staged.get(path.as_posix())


def _history(fake: FakeHistory) -> History:
    """View a fake as the `History` port, of which it has the members that a view uses.

    Args:
        fake: The fake.

    Returns:
        The same object, typed as the port.
    """
    return cast("History", fake)


def _repository(fake: FakeIndex) -> Repository:
    """View a fake as the `Repository` port, of which it has the member a view uses.

    Args:
        fake: The fake.

    Returns:
        The same object, typed as the port.
    """
    return cast("Repository", fake)


def _head(files: dict[str, str], *, unborn: bool = False) -> HeadFiles:
    """Make a view of a revision that holds the given files.

    Args:
        files: The files by path relative to the root.
        unborn: Whether the repository has no commit.

    Returns:
        The view.
    """
    return HeadFiles(_history(FakeHistory(files, unborn=unborn)), ROOT)


def test_a_revision_is_walked_like_a_directory_tree() -> None:
    """A directory exists when a file lies below it, and lists its entries."""
    # Given a view that holds three files in two directories
    view = _head({"w/a/x.md": "x", "w/a/y.md": "y", "w/z.md": "z"})

    # When the root, a directory and a file are asked about
    answers = (
        view.is_dir(ROOT),
        view.is_dir(ROOT / "w"),
        view.is_file(ROOT / "w/z.md"),
        view.exists(ROOT / "w/a"),
        view.is_symlink(ROOT / "w/z.md"),
    )
    listing = view.list_dir(ROOT / "w")

    # Then the directories exist, the file is a file, no path is a link, and the
    # entries are direct children, sorted, as absolute paths
    assert answers == (True, True, True, True, False)
    assert listing == [ROOT / "w/a", ROOT / "w/z.md"]


def test_a_file_is_read_and_a_missing_one_or_one_outside_the_root_is_not() -> None:
    """The text is as stored, its bytes are UTF-8, and a missing path is refused."""
    # Given a view with one file
    view = _head({"a.md": "é\r\n"})

    # When it is read as text and as bytes, and a missing file and a path
    # outside the root are read
    text = view.read_text(ROOT / "a.md")
    data = view.read_bytes(ROOT / "a.md")

    # Then the text keeps its line end, and the other paths do not exist
    assert (text, data) == ("é\r\n", "é\r\n".encode())
    for path in (ROOT / "none.md", Path("/elsewhere/a.md"), Path("a.md")):
        with pytest.raises(FileNotFoundError):
            view.read_text(path)
        assert not view.exists(path)


def test_a_directory_listing_names_what_is_wrong() -> None:
    """A file is not a directory and a missing path is not found."""
    # Given a view with one file
    view = _head({"a.md": "x"})

    # When a file and a missing path are listed
    # Then the errors are those of the port
    with pytest.raises(NotADirectoryError):
        view.list_dir(ROOT / "a.md")
    with pytest.raises(FileNotFoundError):
        view.list_dir(ROOT / "nowhere")


def test_a_view_refuses_to_write() -> None:
    """Writing and appending raise `PermissionError` and change nothing."""
    # Given a view
    view = _head({"a.md": "x"})

    # When a file is written and appended to
    # Then each is refused, and the file is as it was
    with pytest.raises(PermissionError):
        view.write_text(ROOT / "a.md", "y")
    with pytest.raises(PermissionError):
        view.append_text(ROOT / "a.md", "y")
    assert view.read_text(ROOT / "a.md") == "x"


def test_a_repository_with_no_commit_holds_no_file_and_is_listed_once() -> None:
    """An unborn `HEAD` is an empty view, and the listing is read once."""
    # Given a view of a repository with no commit
    history = FakeHistory({}, unborn=True)
    view = HeadFiles(_history(history), ROOT)

    # When it is asked twice
    first = view.exists(ROOT / "a.md")
    second = view.is_dir(ROOT)

    # Then it holds nothing, and git was asked for the files once
    assert (first, second) == (False, False)
    assert history.listed == ["HEAD"]


def test_the_index_holds_the_candidates_that_are_staged() -> None:
    """A file of `HEAD` that the index lacks is gone, and staged content wins."""
    # Given `HEAD` with two files below `w`, of which the index has one, staged
    # with other content, and a file of the working tree that the index has too
    history = FakeHistory({"w/a.md": "head", "w/b.md": "head", "other/c.md": "x"})
    working = MemoryFileSystem({ROOT / "w/new.md": "disk"})
    index = FakeIndex({"w/a.md": "staged", "w/new.md": "staged new"})
    view = IndexFiles(_repository(index), _history(history), working, ROOT, Path("w"))

    # When the view is listed and read
    names = sorted(view.paths())

    # Then the staged files below `w` are held, with the staged content
    assert names == [Path("w/a.md"), Path("w/new.md")]
    assert view.read_text(ROOT / "w/a.md") == "staged"
    assert not view.exists(ROOT / "w/b.md")
    assert not view.exists(ROOT / "other/c.md")
