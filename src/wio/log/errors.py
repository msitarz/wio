# SPDX-License-Identifier: Apache-2.0
"""Errors that stop a log command before it can report results.

The CLI reports these as conditions a user can fix.
"""

from wio.errors import WioError


class LogError(WioError):
    """A log that the command cannot locate or read.

    The message describes the failure from the underlying port.
    """
