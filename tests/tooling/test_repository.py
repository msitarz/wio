# SPDX-License-Identifier: Apache-2.0
"""Tests that what the build and the tests need is committed, not ignored."""

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PATHSPECS = ("src/**/*.py", "src/**/*.pyi", "tests/**/*.py")


@pytest.mark.slow
def test_no_source_or_test_file_is_hidden_by_gitignore() -> None:
    """A package or test that `.gitignore` hides would pass here and fail in CI."""
    # Given the repository and the paths of the sources and tests

    # When the files that exist, match those paths, and git ignores are listed
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
            "--",
            *PATHSPECS,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    hidden = [line for line in result.stdout.splitlines() if "__pycache__" not in line]

    # Then there are none
    assert hidden == []
