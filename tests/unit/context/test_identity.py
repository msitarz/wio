# SPDX-License-Identifier: Apache-2.0
"""Tests of the bundle id."""

import pytest

from wio.context.identity import bundle_id

_PENDING = pytest.mark.xfail(strict=True)


@_PENDING
def test_the_id_is_the_one_that_the_algorithm_gives() -> None:
    """AC-1: the known text has the known id, each time."""
    # Given the text `a` and a newline
    text = "a\n"

    # When its id is computed twice
    found = bundle_id(text), bundle_id(text)

    # Then it is the first 12 digits of its SHA-256 both times
    assert found == ("87428fc52280", "87428fc52280")


@_PENDING
@pytest.mark.parametrize(
    "changed",
    [
        "b header\nbody\n",
        "a header\nbodY\n",
        "a header\nbody",
        "a header\nbody\n\n",
        "a header\r\nbody\n",
    ],
    ids=["first", "middle", "last-removed", "added", "line-end"],
)
def test_any_change_to_the_text_changes_the_id(changed: str) -> None:
    """AC-2: one changed, added or removed character gives another id."""
    # Given a text and its id
    first = bundle_id("a header\nbody\n")

    # When one character of the text changes
    second = bundle_id(changed)

    # Then the id differs
    assert second != first
