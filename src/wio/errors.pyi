# SPDX-License-Identifier: Apache-2.0
"""Errors that wio reports as the user's to fix, which every package may raise."""

class WioError(Exception):
    """A condition the user must fix before a command can answer.

    The command line catches it, reports `error:` and its message on standard
    error, and exits 2. It is not a `ValueError`, so a handler of `ValueError`
    never swallows it, and `str` of it is the message it was raised with.
    A package with an error of its own extends this class in its own
    `errors.py`.
    """

class ConfigurationError(WioError):
    """A problem with the settings that several components share.

    Raised where the settings cannot be read or are inconsistent.
    """
