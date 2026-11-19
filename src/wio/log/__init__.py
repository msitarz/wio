# SPDX-License-Identifier: Apache-2.0
"""Describe the commands for reading and recording the events of a clone.

The usage can be built without locating the log or loading the implementation.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import ArgumentParser


class LogSpec:
    """The command spec that declares the log forms without wiring the ports."""

    name = "log"
    help = "Show recorded events."

    def configure(self, parser: ArgumentParser) -> None:
        """Declare help and the arguments supported by the log forms.

        Args:
            parser: The subparser that wio created for the log command.
        """
        parser.set_defaults(log_form=None, log_help=parser.format_help)
        forms = parser.add_subparsers(title="subcommands", metavar="<subcommand>")
        show = forms.add_parser("show", help="Show the recorded stages and reviews.")
        show.add_argument(
            "work", nargs="?", metavar="WORK", help="Show only this Work."
        )
        show.add_argument(
            "--json", action="store_true", help="Write one JSON document."
        )
        show.set_defaults(log_form="show")


def describe() -> LogSpec:
    """Describe the log command without consulting its ports.

    Returns:
        The command spec used to build the CLI parser.
    """
    return LogSpec()
