# SPDX-License-Identifier: Apache-2.0
"""The indented blocks that `wio contracts list` and `wio rules list` print."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True)
class Block:
    """One entry of a listing: a first line and the details under it.

    Attributes:
        depth: How many levels the block is indented, two spaces for each.
        key: What the first line starts with, padded to the widest key.
        title: What follows the key.
        suffix: What follows the title after two more spaces, if any.
        details: The lines under the first, each written only as given.
    """

    depth: int
    key: str
    title: str
    suffix: str | None
    details: tuple[str, ...]


def render_blocks(blocks: Sequence[Block]) -> str:
    """Lay out blocks as the text of a listing.

    Each first line is two spaces for each depth, the key padded to the widest key
    of all the blocks, two spaces and the title, then two more spaces and the
    suffix when there is one. Each detail is on its own line, indented to the
    title. Nothing is cut or wrapped. It reads and writes nothing.

    Args:
        blocks: The blocks, in the order to print them.

    Returns:
        The lines, each ended by a newline, and an empty string for no block.
    """
    del blocks
    raise NotImplementedError
