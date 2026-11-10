# SPDX-License-Identifier: Apache-2.0
"""The type of a metadata block that was read from a text."""

from dataclasses import dataclass
from typing import Literal

type BlockForm = Literal["comment", "front-matter"]


@dataclass(frozen=True)
class MetadataBlock:
    """The metadata block of a text and the body that follows it.

    It is immutable. The form is kept so that a writer can restore it.

    Attributes:
        form: `"comment"` for a `<!-- wio ... -->` block, `"front-matter"` for
            a `+++` block.
        version: The wio format version of the block, which is 1.
        data: The decoded TOML of the block, without the `wio` key.
        body: The text from the body start line on, byte for byte.
        body_start_line: The line of the text, counted from 1, on which the
            body begins: the line after the one that holds the closing
            delimiter, or that same line when text follows a closing `-->`.
    """

    form: BlockForm
    version: int
    data: dict[str, object]
    body: str
    body_start_line: int
