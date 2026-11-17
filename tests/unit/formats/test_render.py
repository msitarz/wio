# SPDX-License-Identifier: Apache-2.0
"""Tests of the renderer of records in `wio.formats`.

Each test is a stub for one scenario of the Work that builds the renderer, and
skips until the implementation stage fills it in.
"""

import pytest

STUB = "filled in by the implementation stage"


def test_fields_given_in_any_order_come_out_in_the_order_of_the_keys() -> None:
    """AC-6: six lines in order, and a key outside the six is refused."""
    # Given the fields `Wio-Judge: human`, `Wio-Items: AC-1`, `Wio-Work: k3m9xq`,
    # `Wio-Result: pass`, `Wio-Stage: architecture-review` and
    # `Wio-Action: deliver`
    # When `render` runs, and again with a field `Wio-Nope: x` added
    # Then the first returns the six lines in the order of the keys, each ending
    # with a newline, and the second raises `ValueError` naming `Wio-Nope`
    pytest.skip(STUB)
