# SPDX-License-Identifier: Apache-2.0
"""The errors of `wio.templates`."""

from typing import TYPE_CHECKING

from wio.errors import DiagnosticsError
lazy from wio.formats import render_text

if TYPE_CHECKING:
    from collections.abc import Iterable

    from wio.models.diagnostics import Diagnostic


class TemplatesError(DiagnosticsError):
    """A problem with the templates that the user must fix before a command answers.

    It keeps the diagnostics it was raised with, as every `DiagnosticsError`
    does, and `str` of it is the message, so the command line writes it as it is
    when it carries diagnostics.
    """


CHECK_HINT = "`wio templates check` shows every problem."
"""The line that a refusal ends with, so a person knows where to see them all."""


def refusal(diagnostics: Iterable[Diagnostic]) -> TemplatesError:
    """Make the error of a command that refuses to work around a template problem.

    Args:
        diagnostics: The problems found, as they are to be shown.

    Returns:
        An error that carries the diagnostics, whose message is them rendered one
        to a line, then `CHECK_HINT`.
    """
    found = tuple(diagnostics)
    return TemplatesError(f"{render_text(found)}\n{CHECK_HINT}", found)
