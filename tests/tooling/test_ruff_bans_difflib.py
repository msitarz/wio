# SPDX-License-Identifier: Apache-2.0
"""Tests that ruff bans `difflib` outside `wio.formats`."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
@pytest.mark.slow
def test_only_wio_formats_may_import_difflib() -> None:
    """AC-4: ruff reports `TID251` for `difflib` outside `wio.formats`."""
    # Given a probe file that imports `difflib`
    # When it is linted as a file of wio.config and of wio.formats
    # Then it is reported for the first and not for the second
