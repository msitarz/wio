# SPDX-License-Identifier: Apache-2.0
"""Tests of the null adapters of `wio.cli`."""

import pytest

from wio.cli.null import UnwiredComposer
from wio.errors import WioError


def test_the_unwired_composer_refuses_every_run() -> None:
    """Without a composition a run is a refusal that the user is told about."""
    # Given the composer that stands where there is no composition
    composer = UnwiredComposer()

    # When a bundle is asked for
    with pytest.raises(WioError) as raised:
        composer.compose("k3m9xq", "deliver", "architecture")

    # Then it says that none can be composed
    assert str(raised.value) == "wio context cannot compose a bundle yet"
