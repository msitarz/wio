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


def render_blocks(blocks: Sequence[Block], *, spaced: bool = False) -> str:
    """Lay out blocks as the text of a listing.

    Each first line is two spaces for each depth, the key padded to the widest key
    of all the blocks, two spaces and the title, then two more spaces and the
    suffix when there is one. Each detail is on its own line, indented to the
    title. Nothing is cut or wrapped. With `spaced`, a blank line separates one
    block from the next, and none follows the last. It reads and writes nothing.

    Args:
        blocks: The blocks, in the order to print them.
        spaced: Whether to put a blank line between the blocks, so that blocks
            with long details can be told apart.

    Returns:
        The lines, each ended by a newline, and an empty string for no block.
    """
    width = max((len(block.key) for block in blocks), default=0)
    lines: list[str] = []
    for number, block in enumerate(blocks):
        if spaced and number:
            lines.append("")
        lines.extend(_lines(block, width))
    return "".join(f"{line}\n" for line in lines)


def _lines(block: Block, width: int) -> list[str]:
    """Lay out one block."""
    indent = "  " * block.depth
    suffix = f"  {block.suffix}" if block.suffix else ""
    first = f"{indent}{block.key.ljust(width)}  {block.title}{suffix}"
    pad = indent + " " * (width + 2)
    return [first, *(pad + detail for detail in block.details)]
