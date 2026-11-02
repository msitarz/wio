# SPDX-License-Identifier: Apache-2.0
"""Tests for the adapters of `wio.env`."""

from wio.env import adapters


def test_the_environment_adapters_module_holds_no_adapter_yet() -> None:
    """The ports of `wio.env` have no adapter until a component needs one."""
    # Given the module that holds the adapters of wio.env

    # When its public classes are listed
    public = [
        name
        for name, value in vars(adapters).items()
        if isinstance(value, type) and value.__module__ == adapters.__name__
    ]

    # Then there are none
    assert public == []
