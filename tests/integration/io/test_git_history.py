# SPDX-License-Identifier: Apache-2.0
"""Tests of `GitHistory` and of the index and tree reads of `GitRepository`.

Each test is a stub for one criterion of the Work that builds them, and skips
until the implementation stage fills it in. The examples use a temporary
repository: `c1` adds `a.txt` and `sub/d.txt`, a branch `side` forks from `c1`
with `s1` that adds `s.txt`, and on the main branch `c2` adds `b.txt` and `c3`
merges `side` and deletes `b.txt`.
"""

import pytest

STUB = "filled in by the implementation stage"


@pytest.mark.slow
def test_a_range_lists_its_commits_oldest_first() -> None:
    """AC-1: a range, an empty range and a rejected range."""
    # Given the repository
    # When `history("c1..c3")`, `history("c3..c3")` and `history("nosuch..c3")`
    # run
    # Then the first returns `s1` and `c2` in either order and then `c3`, each
    # with its full id and its message as committed; the second returns none
    # and the third raises `ValueError`
    pytest.skip(STUB)


@pytest.mark.slow
def test_first_parents_come_newest_first() -> None:
    """AC-2: a walk over a merge leaves out the merged branch."""
    # Given the repository with the merge commit `c3`
    # When `first_parents("HEAD")` and `first_parents("nosuch")` run
    # Then the first returns `c3`, `c2` and `c1` and the second raises
    # `ValueError`
    pytest.skip(STUB)


@pytest.mark.slow
def test_a_revision_resolves_to_a_full_id() -> None:
    """AC-3: a name resolves and an unknown name is refused."""
    # Given the repository
    # When `rev_parse("HEAD")` and `rev_parse("nosuch")` run
    # Then the first returns the full id of `c3` and the second raises
    # `ValueError`
    pytest.skip(STUB)


@pytest.mark.slow
def test_a_file_is_read_as_it_was_at_a_revision() -> None:
    """AC-4: the files and the content of a revision, from any directory."""
    # Given the repository, whose `b.txt` was added by `c2` and deleted by `c3`
    # When `list_files("c2")`, `show("c2", "b.txt")` and `show("c3", "b.txt")`
    # run, then `list_files("c2")` from `sub`, and `list_files("nosuch")` and
    # `show("nosuch", "b.txt")`
    # Then they return the sorted paths, the content, `None`, the same paths
    # relative to the root, and the last two raise `ValueError`
    pytest.skip(STUB)


@pytest.mark.slow
def test_a_file_is_read_as_it_is_staged() -> None:
    """AC-5: a staged file that differs from the tree and from `HEAD`."""
    # Given `a.txt` staged with one content, changed in the tree and different
    # in `HEAD`, and `new.txt` that is not staged
    # When `show_index("a.txt")` and `show_index("new.txt")` run, then
    # `show_index("a.txt")` from `sub`
    # Then they return the staged content, `None` and the staged content again
    pytest.skip(STUB)


@pytest.mark.slow
def test_the_working_tree_is_reported_as_dirty_or_clean() -> None:
    """AC-6: changes of every kind, and an ignored file."""
    # Given a clean repository with a committed ignore rule, then a modified
    # tracked file, a staged new file, an untracked file and an ignored one
    # When `is_dirty()` runs on each
    # Then it returns false for the clean one and the ignored file, and true
    # for the others
    pytest.skip(STUB)


@pytest.mark.slow
def test_a_directory_outside_a_repository_is_refused_by_every_member() -> None:
    """AC-7: each member raises `RuntimeError` that names the directory."""
    # Given a working directory that is not in a repository
    # When each member of the adapter, `show_index` and `is_dirty` run
    # Then each raises `RuntimeError` that names the working directory
    pytest.skip(STUB)


@pytest.mark.slow
def test_a_read_leaves_the_repository_as_it_was() -> None:
    """AC-8: the index, the refs and the tree are the same after every read."""
    # Given the repository with a staged file and a modified tracked file
    # When every member of the adapter, `show_index` and `is_dirty` run
    # Then the bytes of `.git/index`, the refs and the working-tree files are
    # the same as before
    pytest.skip(STUB)
