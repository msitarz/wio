# SPDX-License-Identifier: Apache-2.0
"""The errors of `wio.templates`."""

from wio.errors import WioError


class TemplatesError(WioError):
    """A problem with the templates that the user must fix before a command answers.

    The message is what the command line writes, such as the rendered
    diagnostics of the templates, so `str` of it is that text.
    """
