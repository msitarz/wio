# SPDX-License-Identifier: Apache-2.0
"""The errors of `wio.contracts`."""

from wio.errors import WioError


class ContractsError(WioError):
    """A mistake in a contracts command that the user must fix.

    It carries the message that the command line prints after `error: `, and it
    exits 2. The name and its one message argument are what the subcommands of
    `wio contracts` raise.
    """
