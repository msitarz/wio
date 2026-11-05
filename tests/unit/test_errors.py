# SPDX-License-Identifier: Apache-2.0
"""Tests of `wio.errors` and of the dependency table that lets packages use it."""

import pytest


def test_a_configuration_error_is_a_wio_error() -> None:
    """A `ConfigurationError` is caught as `WioError` and keeps its message."""
    pytest.skip("architecture stub: AC-1 of the errors leaf")
    # Given a ConfigurationError raised with a message

    # When it is caught as WioError

    # Then it is caught, str of it is the message, and neither class is a
    # ValueError


def test_tach_lets_every_package_use_wio_errors() -> None:
    """`wio.errors` has no dependencies, and every other module lists it."""
    pytest.skip("architecture stub: AC-2 of the errors leaf")
    # Given tach.toml of the tree

    # When it is read

    # Then wio.errors has an empty depends_on, and every other wio.* module
    # and tests.unit list wio.errors
