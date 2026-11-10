# SPDX-License-Identifier: Apache-2.0
"""Tests of `wio templates directives` that need a fresh interpreter."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
@pytest.mark.slow
def test_the_listing_loads_no_parser_or_writer() -> None:
    """AC-4: without `--json` none of `json`, `tomllib`, `tomlkit`, `markdown_it`."""
    # Given a new Python process
    # When `main(["templates", "directives"], stdio)` runs in it and `sys.modules`
    # is read
    # Then none of the four modules is there
