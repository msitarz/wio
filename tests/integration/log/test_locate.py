# SPDX-License-Identifier: Apache-2.0
"""Tests for `wio.log.locate` against real git and a real disk."""

import pytest


@pytest.mark.skip(reason="stub of the architecture stage")
@pytest.mark.slow
def test_worktrees_of_one_clone_share_a_location() -> None:
    """AC-1: the main checkout and a worktree of it find the same log."""
    # Given a real clone with a commit, a worktree of it and an empty $WIO_HOME
    # When locate_log runs from the main checkout and from the worktree
    # Then both give the same path


@pytest.mark.skip(reason="stub of the architecture stage")
@pytest.mark.slow
def test_finding_the_location_creates_nothing() -> None:
    """AC-4: $WIO_HOME still holds nothing."""
    # Given a real clone and a $WIO_HOME that names an empty directory
    # When locate_log runs
    # Then it gives a path under $WIO_HOME/log/ and $WIO_HOME holds nothing


@pytest.mark.skip(reason="stub of the architecture stage")
@pytest.mark.slow
def test_outside_a_repository_the_error_of_the_port_is_raised() -> None:
    """AC-4: the `RuntimeError` of git reaches the caller unchanged."""
    # Given a working directory that is not in a repository
    # When locate_log runs with the Repository of git
    # Then the RuntimeError of the port is raised unchanged


@pytest.mark.skip(reason="stub of the architecture stage")
@pytest.mark.slow
def test_a_relative_wio_home_raises_the_error_of_the_port() -> None:
    """AC-4: the `ValueError` of the directories reaches the caller unchanged."""
    # Given a real clone and $WIO_HOME set to relative/dir
    # When locate_log runs with the real Directories
    # Then the ValueError of the port is raised unchanged


@pytest.mark.skip(reason="stub of the architecture stage")
def test_a_symlink_to_a_file_is_found_and_one_to_a_directory_is_not() -> None:
    """AC-3: the real `is_file` follows a symlink to a file and not to a directory."""
    # Given a directory on disk that holds link.jsonl, a symlink to a file, and
    # dir.jsonl, a symlink to a directory
    # When log_files runs for it with the real FileSystem
    # Then it gives link.jsonl and not dir.jsonl


@pytest.mark.skip(reason="stub of the architecture stage")
def test_a_missing_directory_stays_missing() -> None:
    """AC-3: looking for the files of a log creates nothing."""
    # Given a path on disk that does not exist
    # When log_files runs for it with the real FileSystem
    # Then it gives no file and the path still does not exist
