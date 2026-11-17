# SPDX-License-Identifier: Apache-2.0
"""The spec of the renderer of the `Wio-*` records of a commit message.

The write command prints a record with it and the gate leaf reuses it, so no
command lays out a record on its own, as the parser of `wio.formats` is the one
reader of records. It renders and judges nothing: the form and the fields of a
record are judged by `check_shape` and by the validator of `wio.trailers`.

The stub is the spec until the wiring stage of the Work that builds the renderer
writes the module `wio.formats.render` and deletes this stub, so the spec and the
code never coexist.
"""

from collections.abc import Mapping

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
    ...
