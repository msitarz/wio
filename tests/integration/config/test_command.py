# SPDX-License-Identifier: Apache-2.0
"""Tests of what a fresh interpreter loads when `wio config` is described and run."""

import pytest


@pytest.mark.slow
def test_describing_the_command_loads_no_submodule_of_the_package() -> None:
    """AC-5: the table of commands is described without the implementation."""
    # Given a new Python process
    # When the table of commands is described
    # Then no submodule of `wio.config` is in `sys.modules`
    pytest.skip("stub: the implementation stage writes this test")


@pytest.mark.slow
def test_listing_the_settings_does_not_load_json() -> None:
    """AC-5: only `--json` imports the `json` module."""
    # Given a new Python process and a valid config
    # When `wio config list` runs without `--json`
    # Then `json` is not in `sys.modules`
    pytest.skip("stub: the implementation stage writes this test")
