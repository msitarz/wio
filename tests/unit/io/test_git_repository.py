# SPDX-License-Identifier: Apache-2.0
"""Tests for `GitRepository`, the adapter of the `Repository` port."""

import pytest


@pytest.mark.slow
def test_root_and_identity_from_a_subdirectory() -> None:
    """AC-3: the root is the top of the tree and the identity its `.git`."""
    # Given a repository with a subdirectory, and the process running in it

    # When root and identity run

    # Then they are the absolute top of the tree and its `.git` directory
    pytest.skip("stub: implemented with the adapter")


@pytest.mark.slow
def test_a_linked_worktree_shares_the_identity_but_not_the_root() -> None:
    """AC-3: worktrees of one clone have one identity and different roots."""
    # Given a clone and a linked worktree

    # When identity runs in each

    # Then both return the same path, and the roots differ
    pytest.skip("stub: implemented with the adapter")


@pytest.mark.slow
def test_outside_a_repository_root_and_identity_raise() -> None:
    """AC-3: outside a repository both raise `RuntimeError`."""
    # Given a directory that no repository contains

    # When root or identity runs

    # Then it raises RuntimeError
    pytest.skip("stub: implemented with the adapter")


@pytest.mark.slow
def test_the_members_trailers_owns_raise_not_implemented() -> None:
    """AC-4: show_index and is_dirty name the trailers Work."""
    # Given a GitRepository in a repository

    # When show_index and is_dirty run

    # Then each raises NotImplementedError naming the trailers Work
    pytest.skip("stub: implemented with the adapter")
