# SPDX-License-Identifier: Apache-2.0
"""Tests of `wio.errors` and of the dependency table that lets packages use it."""

import tomllib
from pathlib import Path

import pytest

from wio.errors import ConfigurationError, WioError
from wio.models.diagnostics import Diagnostic

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
    """`wio.models` is plain, `wio.errors` needs only it, and the rest use both."""
    # Given tach.toml of the tree
    text = TACH.read_text(encoding="utf-8")

    # When it is read
    modules = {m["path"]: m["depends_on"] for m in tomllib.loads(text)["modules"]}

    # Then wio.models has an empty depends_on, wio.errors lists only wio.models,
    # and every other wio.* module and tests.unit list wio.errors
    assert modules["wio.models"] == []
    assert modules["wio.errors"] == ["wio.models"]
    users = [p for p in modules if p.startswith("wio.") or p == "tests.unit"]
    assert [
        p
        for p in users
        if p not in {"wio.models", "wio.errors"} and "wio.errors" not in modules[p]
    ] == []


def test_a_configuration_error_keeps_its_diagnostics() -> None:
    """A `ConfigurationError` keeps the findings it was raised with (AC-5)."""
    # Given two error diagnostics and a message built from them
    diagnostics = [
        Diagnostic("error", "stages.x", "unknown stage"),
        Diagnostic("error", "a", "reserved"),
    ]
    text = "\n".join(f"{d.where}: {d.message}" for d in diagnostics)

    # When errors with and without them are caught as WioError
    message = "no config at /x"
    with pytest.raises(WioError) as bare:
        raise ConfigurationError(message)
    with pytest.raises(WioError) as full:
        raise ConfigurationError(text, diagnostics)

    # Then the first has none and the second keeps both, in order
    assert isinstance(bare.value, ConfigurationError)
    assert isinstance(full.value, ConfigurationError)
    assert bare.value.diagnostics == ()
    assert str(bare.value) == "no config at /x"
    assert full.value.diagnostics == tuple(diagnostics)
    assert str(full.value) == text
