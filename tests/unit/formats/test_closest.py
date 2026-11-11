# SPDX-License-Identifier: Apache-2.0
"""Tests of the closest key in `wio.formats`."""

from wio.formats import closest_key


def test_the_closest_known_key_is_found_or_none() -> None:
    """AC-3: `descriptions` finds `description`, `zzz` and no keys find none."""
    # Given the known keys `description` and `kind`
    known = ("description", "kind")

    # When `closest_key` runs for `descriptions`, for `zzz`, and for `kind` with
    # no keys
    found = [
        closest_key("descriptions", known),
        closest_key("zzz", known),
        closest_key("kind", ()),
    ]

    # Then the results are `description`, none and none
    assert found == ["description", None, None]
