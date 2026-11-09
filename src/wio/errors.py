# SPDX-License-Identifier: Apache-2.0
"""Errors that wio reports as the user's to fix, which every package may raise."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from wio.models.diagnostics import Diagnostic


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
    It keeps the diagnostics it was raised with, in the order given, and
    `str` of it is the message. An error that is given diagnostics has them
    rendered, one `<severity>: <where>: <message>` line each, as its message, so
    that the command line can write it as it is.

    Attributes:
        diagnostics: The findings that caused the error; empty when it has
            none.
    """

    diagnostics: tuple[Diagnostic, ...]

    def __init__(self, message: str, diagnostics: Iterable[Diagnostic] = ()) -> None:
        """Keep the message and the diagnostics.

        Args:
            message: What `str` of the error returns, such as the rendered
                diagnostics.
            diagnostics: The findings that caused the error.
        """
        super().__init__(message)
        self.diagnostics = tuple(diagnostics)
