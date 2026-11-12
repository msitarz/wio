# SPDX-License-Identifier: Apache-2.0
"""The errors of `wio.contracts`."""

from wio.errors import DiagnosticsError


class ContractsError(DiagnosticsError):
    """A mistake in a contracts command that the user must fix.

    It carries the message that the command line prints after `error: `, and it
    exits 2. A refusal that is raised with diagnostics keeps them, and the
    command line then writes its message as it is, which is the diagnostics
    rendered one to a line, as `wio templates` does. The name and its one
    message argument are what the subcommands of `wio contracts` raise.
    """
