# SPDX-License-Identifier: Apache-2.0
"""Tests of the discovery of Works on a real disk."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_real_symbolic_link_is_not_followed_and_a_real_tree_is_walked() -> None:
    """AC-1: a link to a marked file is no Work, and no file is written."""
    # Given a repository on disk with Works in both block forms, a symbolic link
    # to a marked file and a hidden directory with a marked file
    # When the Works are discovered through the real file system
    # Then the Works are those of the files that are not links or hidden, and
    # the files on disk are as they were


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_real_works_directory_that_is_a_symbolic_link_is_refused() -> None:
    """AC-7: the directory is judged before it is walked."""
    # Given a repository whose configured Works directory is a symbolic link to
    # a directory of Works
    # When the Works are discovered through the real file system
    # Then there is no Work and one error that begins `The Works directory`
