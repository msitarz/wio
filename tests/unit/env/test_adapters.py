# SPDX-License-Identifier: Apache-2.0
"""Tests for the adapters of `wio.env`."""

from typing import TYPE_CHECKING

import pytest

from wio.env import adapters

if TYPE_CHECKING:
    from wio.env.ports import Environment


def _wired() -> Environment:
    """Wire the adapter where the port is expected.

    Returns:
        A `ProcessEnvironment`, which type checking accepts as an `Environment`.
    """
    return adapters.ProcessEnvironment()


def test_the_module_holds_the_adapters_of_the_ports_that_have_one() -> None:
    """AC-5: `Environment` and `Entropy` have an adapter; the others wait for a Work."""
    # Given the module that holds the adapters of the environment component

    # When its public classes are listed
    public = [
        name
        for name, value in vars(adapters).items()
        if isinstance(value, type) and value.__module__ == adapters.__name__
    ]

    # Then the adapters of the environment and of randomness are the only ones
    assert public == ["ProcessEnvironment", "SystemEntropy"]


def test_the_other_members_name_themselves_and_the_work_that_implements_them() -> None:
    """AC-5: `get` raises `NotImplementedError` and says who implements it."""
    # Given a ProcessEnvironment
    environment = _wired()

    # When each member other than the working directory runs
    # Then it raises NotImplementedError naming the member and the Work
    with pytest.raises(NotImplementedError) as caught:
        environment.get("HOME")
    assert str(caught.value) == "get is implemented by the Work that first needs it"


def test_the_entropy_gives_exactly_the_bytes_asked_for() -> None:
    """The adapter reads as many bytes as it is asked for, and differs between calls."""
    # Given the adapter of randomness
    entropy = adapters.SystemEntropy()

    # When it is asked for six bytes, twice, and for none
    first, second, none = entropy.random_bytes(6), entropy.random_bytes(6), b""

    # Then each is six bytes long, the two differ, and none is empty
    assert (len(first), len(second)) == (6, 6)
    assert first != second
    assert entropy.random_bytes(0) == none
