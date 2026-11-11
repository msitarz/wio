# SPDX-License-Identifier: Apache-2.0
"""Tests of the import direction between `wio.templates` and `wio.contracts`."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
@pytest.mark.slow
def test_wio_templates_imports_nothing_of_wio_contracts() -> None:
    """AC-7: `src/wio/templates` imports nothing of `wio.contracts`."""
    # Given the sources of `src/wio/templates`
    # When the imports of its modules are read from their syntax trees, and `tach check`
    # runs
    # Then the trees show no import of `wio.contracts`, and `tach check` reports none
