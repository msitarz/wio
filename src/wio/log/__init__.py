# SPDX-License-Identifier: Apache-2.0
"""Describe the commands for reading and recording the events of a clone.

The usage can be built without locating the log or loading the implementation.
"""

from argparse import ArgumentTypeError
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import ArgumentParser


class LogSpec:
    """The command spec that declares the log forms without wiring the ports."""

    name = "log"
    help = "Show events and record reviews."

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

        review = forms.add_parser("review", help="Record a gate review in the log.")
        review.add_argument("work", type=_single_work)
        review.add_argument("action")
        review.add_argument("stage")
        review.add_argument("--result", required=True)
        review.add_argument("--judge", default="agent")
        review.add_argument("--cite", action="append", default=[], metavar="KEY=RESULT")
        review.add_argument(
            "--json", action="store_true", help="Write one JSON document."
        )
        review.set_defaults(log_form="review")


def _single_work(work: str) -> str:
    """Keep the Work argument when it names a single Work."""
    if "," in work:
        message = "name one Work for a review"
        raise ArgumentTypeError(message)
    return work


def describe() -> LogSpec:
    """Describe the log command without consulting its ports.

    Returns:
        The command spec used to build the CLI parser.
    """
    return LogSpec()
