# SPDX-License-Identifier: Apache-2.0
"""Tests of the layout of the blocks that two listings share."""

import pytest

from wio.formats import Block, render_blocks

pytestmark = pytest.mark.xfail(
    raises=NotImplementedError, strict=True, reason="render_blocks is a stub"
)


def test_keys_are_padded_to_the_widest_and_details_follow_the_title() -> None:
    """AC-10: indent by depth, padded keys, suffix and details under the title."""
    # Given blocks of two depths with keys of different widths, a suffix and
    # detail lines
    blocks = [
        Block(0, "a", "First", "[x]", ("one", "two")),
        Block(1, "long-key", "Second", None, ()),
        Block(2, "b", "Third", None, ("three",)),
    ]

    # When they are rendered
    text = render_blocks(blocks)

    # Then each key is padded to the widest of all, each depth adds two spaces,
    # the suffix follows after two spaces and the details start at the title
    assert text == (
        "a         First  [x]\n"
        "          one\n"
        "          two\n"
        "  long-key  Second\n"
        "    b         Third\n"
        "              three\n"
    )


def test_no_block_renders_nothing() -> None:
    """AC-10: an empty sequence gives an empty string."""
    # Given no block
    blocks: list[Block] = []

    # When they are rendered
    text = render_blocks(blocks)

    # Then the text is empty
    assert not text
