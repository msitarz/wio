# SPDX-License-Identifier: Apache-2.0
"""Tests of what `wio contracts` imports, in a fresh interpreter."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
@pytest.mark.slow
def test_bare_contracts_loads_no_codec() -> None:
    """AC-1: `tomlkit`, `json` and `markdown_it` stay unloaded."""
    # Given a new Python process
    # When `main(["contracts"], stdio)` of `wio.cli` runs and `sys.modules` is read
    # Then none of `tomlkit`, `json` and `markdown_it` is there
