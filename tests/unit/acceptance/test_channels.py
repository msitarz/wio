# SPDX-License-Identifier: Apache-2.0
"""Tests for the channel marker and the expected failure of the first scenario."""

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
        if "[" in line
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


@pytest.mark.slow
def test_the_first_scenario_is_expected_to_fail_on_both_channels() -> None:
    """It xfails in the fast run and in the slow run, and both exit 0."""
    # Given the delivered tree

    # When the scenario runs on each channel
    fast = _pytest("-q", SCENARIO)
    slow = _pytest("-q", "-m", "slow", SCENARIO)

    # Then each reports an expected failure and exits 0
    assert (fast.returncode, "1 xfailed" in fast.stdout) == (0, True)
    assert (slow.returncode, "1 xfailed" in slow.stdout) == (0, True)


@pytest.mark.slow
def test_the_first_scenario_fails_on_the_assertion() -> None:
    """With xfail ignored, the failure is an AssertionError on the description."""
    # Given the scenario on either channel

    # When it runs with xfail ignored
    result = _pytest("-q", "--runxfail", "-m", "slow or not slow", SCENARIO)

    # Then both fail with an AssertionError about the missing description
    assert result.returncode == 1
    assert result.stdout.count("AssertionError") == 2
    assert result.stdout.count("Work It Out! Agentic Workflow Engine") >= 2
    assert "ImportError" not in result.stdout
