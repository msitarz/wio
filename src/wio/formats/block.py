# SPDX-License-Identifier: Apache-2.0
"""The reader of the metadata block that opens a file."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wio.models.block import MetadataBlock


def read_metadata_block(text: str) -> MetadataBlock | None:
    """Split a text into its metadata block and its body.

    The block is a `<!-- wio ... -->` comment or `+++` front matter on the
    first line of the text, after an optional leading U+FEFF. The comment ends
    at the first `-->`. CRLF and LF read alike. It reads no file, and it loads
    no TOML decoder for a text that has no block.

    Args:
        text: The text of a file, decoded as UTF-8.

    Returns:
        The block with its form, version, data and body, or `None` for a text
        that has no block, or whose `+++` front matter has no `wio =` in it.

    Raises:
        MetadataBlockError: The block claims to be wio's but does not close,
            is not valid TOML, or has a `wio` marker other than the integer 1.
            It carries the line of the text.
    """
    raise NotImplementedError
