# SPDX-License-Identifier: Apache-2.0
"""The `wio trailers` command: writing and checking the records of commits."""

from argparse import REMAINDER, RawDescriptionHelpFormatter
from dataclasses import dataclass
from typing import TYPE_CHECKING

lazy from wio.trailers.command import TrailersCommand

if TYPE_CHECKING:
    from argparse import ArgumentParser

    from wio.io.ports import FileSystem, History
    from wio.ports import EventSink, Settings
    from wio.trailers.ports import Contracts, StageRules


@dataclass(frozen=True)
class Services:
    """What a form of `wio trailers` reads the project through.

    Provisional: a leaf that needs another port adds a field, and `wio.cli` builds
    the value from the adapters.

    Attributes:
        settings: Loads the config.
        contracts: Finds the items and the pipelines of the Works that a record
            names.
        history: Gives the commits of a range with their messages.
        staged_contracts: Finds the Works in the index and then in `HEAD`, as the
            check of a commit message needs them, where `contracts` finds them in
            the working tree and then in `HEAD`.
        files: Reads the file that holds a message to check.
        rules: Gives the rules that a stage selects for a Work, which a review may
            cite.
        events: Takes the `review` event of a recorded gate result.
    """

    settings: Settings
    contracts: Contracts
    history: History
    staged_contracts: Contracts
    files: FileSystem
    rules: StageRules
    events: EventSink


_FORMS = """\
Print a checked record, check a message, a body or a range, fold a range, or print
the record of a commit with no Work.

forms:
  <work> <action> <stage>  Print the record of a Work, an action and a stage.
  check                    Check a commit message, a body or a range of commits.
  fold                     Fold the records of a range into a block or a body.
  none                     Print the record of a commit that belongs to no Work.
"""
"""What `wio trailers --help` says, with one line for each form."""


class TrailersSpec:
    """What the usage needs to know about `wio trailers`, and nothing more."""

    name = "trailers"
    help = "Print, check and fold the Wio records of commits."

    def configure(self, parser: ArgumentParser) -> None:
        """Add the arguments of `wio trailers` to its subparser.

        It does no I/O and loads no module of the package. The subparser takes
        every argument after `trailers` as `forms`, with `nargs=argparse.REMAINDER`,
        and leaves them to the group, so an option before the first argument, which
        no form takes there, is refused by argparse as an unrecognized argument with
        the exit code 2, while an option after it is captured for its form. The
        description is formatted with `RawDescriptionHelpFormatter` and lists the
        write form, `check`, `fold` and `none`, one line each, so `wio trailers
        --help` shows the four forms and exits 0.

        Args:
            parser: The subparser that `wio.cli` created for `trailers`.
        """
        parser.description = _FORMS
        parser.formatter_class = RawDescriptionHelpFormatter
        parser.add_argument(
            "forms",
            nargs=REMAINDER,
            metavar="<form>",
            help="The form and its arguments.",
        )


def describe() -> TrailersSpec:
    """Describe `wio trailers` without loading its implementation.

    Returns:
        The command spec of `trailers`.
    """
    return TrailersSpec()


__all__ = ["Services", "TrailersCommand", "TrailersSpec", "describe"]
