# SPDX-License-Identifier: Apache-2.0
"""Tests that each shared helper is defined once and used by the components."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_each_helper_is_defined_once_in_its_package() -> None:
    """AC-10: each helper lives in the package named for it."""
    # Given the sources of `src/wio` after the change
    # When their syntax trees are searched for the definitions of the helpers, for
    # the use of `severity == "error"` and for the imports of the helper modules
    # Then each helper is defined only in its package, the components define
    # none of the old private copies, and each helper module imports only what the
    # contract lists
