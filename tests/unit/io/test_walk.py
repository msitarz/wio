# SPDX-License-Identifier: Apache-2.0
"""Tests of the walk of a directory of Markdown files in `wio.io`."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_walk_yields_the_visible_markdown_files() -> None:
    """AC-1: only `.md` files, not hidden, not links, and no file read."""
    # Given a tree with `a.md`, `B.MD`, a text file, a visible and a hidden
    # directory and two symbolic links, in a fake that records reads
    # When `walk_markdown` runs on its root
    # Then it yields `a.md` and `sub/f.md` in that order and has read no file


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_directory_that_cannot_be_walked_is_refused_with_the_callers_noun() -> None:
    """AC-2: link, missing, file and the missing default."""
    # Given `noun="templates"` and a link, a missing directory written as `other`, a
    # file, the missing default and an ordinary directory
    # When `refuse_directory` runs on each
    # Then the first three give one error with its message at the path as written, and
    # the last two give none


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_message_opens_with_the_noun_it_is_given() -> None:
    """AC-2: `Works` instead of `templates`."""
    # Given `noun="Works"` and a directory that is a symbolic link
    # When `refuse_directory` runs on it
    # Then the message reads `The Works directory must not be a symbolic link`
