# SPDX-License-Identifier: Apache-2.0
"""Tests of the walk of a directory of Markdown files in `wio.io`."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from tests.unit.fakes import ROOT, MemoryFileSystem
from wio.io.walk import refuse_directory, walk_markdown
from wio.models.diagnostics import Diagnostic

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

TEMPLATES = ".agents/wio/templates"


@dataclass
class _Listing(MemoryFileSystem):
    """A file system that lists the root in a fixed order and fails on a read."""

    order: tuple[str, ...] = ()

    @override
    def read_text(self, path: Path) -> str:
        """Fail: the walk reads no file.

        Args:
            path: The file.

        Raises:
            AssertionError: Always.
        """
        message = f"the walk read {path}"
        raise AssertionError(message)

    @override
    def list_dir(self, path: Path) -> Sequence[Path]:
        """List the root as `order` says and any other directory sorted.

        Args:
            path: The directory.

        Returns:
            Its entries.
        """
        if path == ROOT:
            return [ROOT / name for name in self.order]
        return super().list_dir(path)


def test_the_walk_yields_the_visible_markdown_files() -> None:
    """AC-1: only `.md` files, not hidden, not links, and no file read."""
    # Given a tree with `a.md`, `B.MD`, a text file, a visible and a hidden
    # directory and two symbolic links, in a fake that records reads
    files = _Listing(
        {
            ROOT / "a.md": "",
            ROOT / "B.MD": "",
            ROOT / "notes.txt": "",
            ROOT / "sub" / "f.md": "",
            ROOT / ".hidden" / "c.md": "",
            ROOT / "linked" / "d.md": "",
            ROOT / "e.md": "",
        },
        order=("a.md", "B.MD", "notes.txt", "sub", ".hidden", "linked", "e.md"),
    )
    files.links = {ROOT / "linked", ROOT / "e.md"}

    # When `walk_markdown` runs on its root
    found = list(walk_markdown(ROOT, files))

    # Then it yields `a.md` and `sub/f.md` in that order and has read no file
    assert found == [ROOT / "a.md", ROOT / "sub" / "f.md"]


def test_a_directory_that_cannot_be_walked_is_refused_with_the_callers_noun() -> None:
    """AC-2: link, missing, file and the missing default."""
    # Given `noun="templates"` and a link, a missing directory written as `other`,
    # a file, the missing default and an ordinary directory
    files = MemoryFileSystem(
        {ROOT / "file": "x", ROOT / "dir" / "a.md": ""}, links={ROOT / "link"}
    )
    cases = {
        "link": ROOT / "link",
        "other": ROOT / "other",
        "file": ROOT / "file",
        TEMPLATES: ROOT / TEMPLATES,
        "dir": ROOT / "dir",
    }

    # When `refuse_directory` runs on each
    refused = {
        written: refuse_directory(
            directory, written, files, noun="templates", default=TEMPLATES
        )
        for written, directory in cases.items()
    }

    # Then the first three give one error with its message at the path as written,
    # and the last two give none
    assert refused == {
        "link": [
            Diagnostic(
                "error", "link", "The templates directory must not be a symbolic link"
            )
        ],
        "other": [
            Diagnostic("error", "other", "The templates directory does not exist")
        ],
        "file": [
            Diagnostic("error", "file", "The templates directory is not a directory")
        ],
        TEMPLATES: None,
        "dir": None,
    }


def test_the_message_opens_with_the_noun_it_is_given() -> None:
    """AC-2: `Works` instead of `templates`."""
    # Given `noun="Works"` and a directory that is a symbolic link
    files = MemoryFileSystem(links={ROOT / "link"})

    # When `refuse_directory` runs on it
    refused = refuse_directory(
        ROOT / "link", "link", files, noun="Works", default=".agents/wio/works"
    )

    # Then the message reads `The Works directory must not be a symbolic link`
    assert refused == [
        Diagnostic("error", "link", "The Works directory must not be a symbolic link")
    ]
