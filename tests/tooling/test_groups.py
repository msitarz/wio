# SPDX-License-Identifier: Apache-2.0
"""Tests that a group marker selects the tests of its directory, and only those."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "tests"
GROUPS = sorted(
    path.name
    for path in TESTS.iterdir()
    if path.is_dir() and any(path.rglob("test_*.py"))
)


@pytest.mark.slow
@pytest.mark.parametrize("group", GROUPS)
def test_a_group_marker_selects_the_tests_of_its_directory(group: str) -> None:
    """The marker of a group is the name of its directory under `tests/`."""
    # Given the name of a directory that holds tests

    # When pytest collects the tests that carry that marker
    done = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "-m",
            group,
            "-o",
            "addopts=",
            "--import-mode=importlib",
            "tests",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    selected = [line for line in done.stdout.splitlines() if "::" in line]

    # Then it collects some, and every one is in that directory
    assert selected
    assert {line.split("/")[1] for line in selected} == {group}
