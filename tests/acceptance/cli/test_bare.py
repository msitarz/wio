# SPDX-License-Identifier: Apache-2.0
"""Scenarios for running `wio` with no arguments."""

import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

PYPROJECT = Path(__file__).resolve().parents[3] / "pyproject.toml"


def _description() -> str:
    """Read the project's description from `pyproject.toml`.

    Returns:
        The `description` of the `[project]` table.
    """
    with PYPROJECT.open("rb") as file:
        return str(tomllib.load(file)["project"]["description"])


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="bare `wio` prints nothing until the Work of the `cli` package",
)
def test_bare_wio_displays_its_description(wio: Wio) -> None:
    """Bare `wio` shows the project's description and exits 0."""
    # Given the description of the project
    description = _description()

    # When wio runs with no arguments
    output = wio.bare()

    # Then it shows the description, writes no error and succeeds
    assert description in output.stdout
    assert output.stderr == ""
    assert output.exit_code == 0
