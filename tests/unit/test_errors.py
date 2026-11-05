# SPDX-License-Identifier: Apache-2.0
"""Tests of `wio.errors` and of the dependency table that lets packages use it."""

import tomllib
from pathlib import Path

import pytest

from wio.errors import ConfigurationError, WioError

TACH = Path(__file__).parents[2] / "tach.toml"


def test_a_configuration_error_is_a_wio_error() -> None:
    """A `ConfigurationError` is caught as `WioError` and keeps its message."""

    # Given a ConfigurationError raised with a message
    message = "no config at /x"

    def fail() -> None:
        raise ConfigurationError(message)

    # When it is caught as WioError
    with pytest.raises(WioError) as caught:
        fail()

    # Then it is caught, str of it is the message, and neither class is a
    # ValueError
    assert isinstance(caught.value, ConfigurationError)
    assert str(caught.value) == "no config at /x"
    assert not issubclass(WioError, ValueError)
    assert not issubclass(ConfigurationError, ValueError)


def test_tach_lets_every_package_use_wio_errors() -> None:
    """`wio.errors` has no dependencies, and every other module lists it."""
    # Given tach.toml of the tree
    text = TACH.read_text(encoding="utf-8")

    # When it is read
    modules = {m["path"]: m["depends_on"] for m in tomllib.loads(text)["modules"]}

    # Then wio.errors has an empty depends_on, and every other wio.* module
    # and tests.unit list wio.errors
    assert modules["wio.errors"] == []
    users = [p for p in modules if p.startswith("wio.") or p == "tests.unit"]
    assert [
        p for p in users if p != "wio.errors" and "wio.errors" not in modules[p]
    ] == []
