# SPDX-License-Identifier: Apache-2.0
"""Tests of the layout of the blocks that two listings share."""

from wio.formats import Block, render_blocks


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


def test_spaced_blocks_have_a_blank_line_between_them_and_none_after() -> None:
    """A blank line separates the blocks, and the last one is followed by none."""
    # Given three blocks, the second without details
    blocks = [
        Block(0, "a", "First", None, ("one",)),
        Block(0, "bb", "Second", None, ()),
        Block(0, "c", "Third", None, ("three",)),
    ]

    # When they are rendered spaced and not spaced
    spaced = render_blocks(blocks, spaced=True)
    plain = render_blocks(blocks)

    # Then the spaced text has a blank line between blocks and ends at the last
    # line, and the plain text is the same without those blank lines
    assert spaced == ("a   First\n    one\n\nbb  Second\n\nc   Third\n    three\n")
    assert spaced.replace("\n\n", "\n") == plain
    assert not render_blocks([], spaced=True)
