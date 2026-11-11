# SPDX-License-Identifier: Apache-2.0
"""Tests of the closest key in `wio.formats`."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_closest_known_key_is_found_or_none() -> None:
    """AC-3: `descriptions` finds `description`, `zzz` and no keys find none."""
    # Given the known keys `description` and `kind`
    # When `closest_key` runs for `descriptions`, for `zzz`, and for `kind` with no keys
    # Then the results are `description`, none and none
