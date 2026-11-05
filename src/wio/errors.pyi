# SPDX-License-Identifier: Apache-2.0
"""Errors that wio reports as the user's to fix, which every package may raise."""

class WioError(Exception):
    """A condition the user must fix before a command can answer.

    The command line reports it as the user's to fix. It is not a `ValueError`,
    so a handler of `ValueError` never swallows it, and `str` of it is the
    message it was raised with.
    A package with an error of its own extends this class in its own
    `errors.py`.
    """

class ConfigurationError(WioError):
    """A problem with the settings that several components share.

    Raised, for example, by `Settings.load` when the settings cannot be read.
    """
