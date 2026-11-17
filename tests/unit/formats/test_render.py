# SPDX-License-Identifier: Apache-2.0
"""Tests of the renderer of records in `wio.formats`.

Each test is one scenario of the Work that builds the renderer.
"""

import pytest

from wio.formats import render

FIELDS = {
    "Wio-Judge": "human",
    "Wio-Items": "AC-1",
    "Wio-Work": "k3m9xq",
    "Wio-Result": "pass",
    "Wio-Stage": "architecture-review",
    "Wio-Action": "deliver",
}


def test_fields_given_in_any_order_come_out_in_the_order_of_the_keys() -> None:
    """AC-6: six lines in order, and a key outside the six is refused."""
    # Given the six fields in any order
    # When `render` runs, and again with a field `Wio-Nope: x` added
    text = render(FIELDS)

    # Then the first returns the six lines in the order of the keys, each ending
    # with a newline, and the second raises `ValueError` naming `Wio-Nope`
    assert text == (
        "Wio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: architecture-review\n"
        "Wio-Items: AC-1\nWio-Result: pass\nWio-Judge: human\n"
    )
    with pytest.raises(ValueError, match="Wio-Nope"):
        render({**FIELDS, "Wio-Nope": "x"})
