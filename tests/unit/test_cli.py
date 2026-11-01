# SPDX-License-Identifier: Apache-2.0
"""Tests for the command-line entry points."""

from wio.cli import hello


def test_hello() -> None:
    """The placeholder entry point answers with a fixed word."""
    # Given no setup

    # When the placeholder is called
    answer = hello()

    # Then it answers "world"
    assert answer == "world"
