# SPDX-License-Identifier: Apache-2.0
"""The renderer of the `Wio-*` records of a commit message.

The write command prints a record with it and the gate leaf reuses it, so no
command lays out a record on its own, as the parser of `wio.formats` is the one
reader of records. It renders and judges nothing: the form and the fields of a
record are judged by `check_shape` and by the validator of `wio.trailers`.
"""

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Mapping


KEYS: Final = (
    "Wio-Work",
    "Wio-Action",
    "Wio-Stage",
    "Wio-Items",
    "Wio-Result",
    "Wio-Judge",
)
"""The six keys of a record, in the order that a record lists them."""


def render(fields: Mapping[str, str]) -> str:
    """Render the fields of one record as a paragraph of trailers.

    The keys are the six that a record has, `Wio-Work`, `Wio-Action`, `Wio-Stage`,
    `Wio-Items`, `Wio-Result` and `Wio-Judge`, and the lines come in that order
    whatever the order of `fields`. A key that `fields` lacks gives no line, and a
    value is written as it is, so a value that holds a line end is the caller's to
    refuse.

    Args:
        fields: The value of each key that the record has.

    Returns:
        One `Key: value` line for each key given, in the order above, each ending
        with a newline, and nothing else.

    Raises:
        ValueError: If a key is not one of the six. The message names the key.
    """
    unknown = next((key for key in fields if key not in KEYS), None)
    if unknown is not None:
        message = f"`{unknown}` is not a key of a record."
        raise ValueError(message)
    return "".join(f"{key}: {fields[key]}\n" for key in KEYS if key in fields)
