# SPDX-License-Identifier: Apache-2.0
"""The errors of `wio.templates`."""

from wio.errors import DiagnosticsError


class TemplatesError(DiagnosticsError):
    """A problem with the templates that the user must fix before a command answers.

    It keeps the diagnostics it was raised with, as every `DiagnosticsError`
    does, and `str` of it is the message, so the command line writes it as it is
    when it carries diagnostics.
    """
