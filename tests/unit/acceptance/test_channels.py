# SPDX-License-Identifier: Apache-2.0
"""Tests for the channel marker."""

import subprocess
import sys
from pathlib import Path

import pytest

from tests.acceptance.channels import Channel

ROOT = Path(__file__).resolve().parents[3]
SCENARIO = "tests/acceptance/cli/test_bare.py"


def _pytest(*args: str) -> subprocess.CompletedProcess[str]:
    """Run pytest in a subprocess on the repository.

    Args:
        *args: The arguments after `-m pytest`.

    Returns:
        The completed process, with its output decoded.
    """
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _cases(*marker: str) -> list[str]:
    """List the ids of the first scenario's cases under a marker expression.

    Args:
        *marker: The `-m` option and its value, or nothing.

    Returns:
        The bracketed ids of the collected cases, sorted.
    """
    result = _pytest("--collect-only", "-q", *marker, SCENARIO)
    return sorted(
        line.split("[")[1].rstrip("]")
        for line in result.stdout.splitlines()
        if "::" in line and line.endswith("]")
    )


@pytest.mark.slow
def test_the_first_scenario_has_one_case_per_channel() -> None:
    """Both channels collect, the CLI one is slow, and the default is fast."""
    # Given the first scenario, marked with both channels

    # When it is collected with each marker expression
    both = _cases("-m", "slow or not slow")
    slow = _cases("-m", "slow")
    default = _cases()

    # Then the cases are the channels, the slow one and the fast one
    assert both == sorted([Channel.IN_PROCESS.value, Channel.CLI.value])
    assert slow == [Channel.CLI.value]
    assert default == [Channel.IN_PROCESS.value]
