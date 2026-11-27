# SPDX-License-Identifier: Apache-2.0
"""Self-description models, registry, renderers and CLI spec for `wio describe`."""

from typing import TYPE_CHECKING

lazy from wio.describe.command import DescribeCommand
lazy from wio.describe.models import (
    CommandDescription,
    CommandForm,
    CommandSummary,
    Concept,
    EngineDescription,
    ExitCode,
    ReferenceEntry,
    ReferenceTable,
)
lazy from wio.describe.registry import (
    describe_command,
    describe_engine,
    registered_commands,
)
lazy from wio.describe.render import (
    render_command_json,
    render_command_text,
    render_engine_json,
    render_engine_text,
)

if TYPE_CHECKING:
    from argparse import ArgumentParser


class DescribeSpec:
    """What the usage needs to know about `wio describe`, and nothing more."""

    name = "describe"
    help = "Describe the wio engine or one subcommand offline."

    def configure(self, parser: ArgumentParser) -> None:
        """Add `[<command>]` and `--json` to the `describe` subparser.

        Args:
            parser: The subparser that `wio.cli` created for `describe`.
        """
        parser.add_argument(
            "describe_command",
            nargs="?",
            default=None,
            metavar="<command>",
            help="Subcommand to describe; omit for the engine overview.",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Write the description as a single-line JSON object.",
        )


def describe() -> DescribeSpec:
    """Describe `wio describe` without loading its implementation.

    Returns:
        The command spec of `describe`.
    """
    return DescribeSpec()


__all__ = [
    "CommandDescription",
    "CommandForm",
    "CommandSummary",
    "Concept",
    "DescribeCommand",
    "DescribeSpec",
    "EngineDescription",
    "ExitCode",
    "ReferenceEntry",
    "ReferenceTable",
    "describe",
    "describe_command",
    "describe_engine",
    "registered_commands",
    "render_command_json",
    "render_command_text",
    "render_engine_json",
    "render_engine_text",
]
