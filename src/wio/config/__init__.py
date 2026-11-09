# SPDX-License-Identifier: Apache-2.0
"""The `wio config` command: reading, showing and validating the project's settings."""

from typing import TYPE_CHECKING

lazy from wio.config.checks import CHECKS, Check, CheckInputs
lazy from wio.config.command import ConfigCommand
lazy from wio.config.loader import Loaded, load_config
lazy from wio.config.settings import ConfigSettings

if TYPE_CHECKING:
    from argparse import ArgumentParser


class ConfigSpec:
    """What the usage needs to know about `wio config`, and nothing more."""

    name = "config"
    help = "Show the project's settings and where each one comes from."

    def configure(self, parser: ArgumentParser) -> None:
        """Add the views of `wio config` to its subparser.

        Args:
            parser: The subparser that `wio.cli` created for `config`.
        """
        parser.set_defaults(config_view=None, config_help=parser.format_help)
        views = parser.add_subparsers(title="subcommands", metavar="<subcommand>")
        listing = views.add_parser(
            "list", help="List every setting with its source.", description=_LIST
        )
        listing.add_argument("--json", action="store_true", help=_JSON)
        listing.set_defaults(config_view="list")
        shown = views.add_parser(
            "show", help="Show a setting or a table in full.", description=_SHOW
        )
        shown.add_argument("key", nargs="?", default="", metavar="key.path", help=_KEY)
        shown.add_argument("--json", action="store_true", help=_JSON)
        shown.set_defaults(config_view="show")
        checked = views.add_parser(
            "check",
            help="Check the settings and print every diagnostic.",
            description=_CHECK,
        )
        checked.add_argument("--json", action="store_true", help=_CHECK_JSON)
        checked.set_defaults(config_view="check")


_LIST = (
    "List every setting that has a value, one per line, with the file or the "
    "default as its source."
)
_SHOW = (
    "Show the setting or the table at a key path in full, each with its source. "
    "A single setting is followed by its description."
)
_CHECK = (
    "Check the config and print every diagnostic, one per line. Exits 1 when any "
    "is an error, 2 when there is no config to check."
)
_CHECK_JSON = "Write the diagnostics as a JSON array of severity, where and message."
_KEY = "The key path of a setting or a table, such as stages.define; all by default."
_JSON = "Write one JSON object that maps each key path to its value and source."


def describe() -> ConfigSpec:
    """Describe `wio config` without loading its implementation.

    Returns:
        The command spec of `config`.
    """
    return ConfigSpec()


__all__ = [
    "CHECKS",
    "Check",
    "CheckInputs",
    "ConfigCommand",
    "ConfigSettings",
    "Loaded",
    "describe",
    "load_config",
]
