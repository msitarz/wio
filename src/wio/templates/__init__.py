# SPDX-License-Identifier: Apache-2.0
"""The `wio templates` command: listing, showing and checking templates."""

from typing import TYPE_CHECKING

lazy from wio.templates.command import TemplatesCommand
lazy from wio.templates.discovery import Discovery, discover
lazy from wio.templates.errors import TemplatesError

if TYPE_CHECKING:
    from argparse import ArgumentParser, _SubParsersAction

    type _SubParsers = _SubParsersAction[ArgumentParser]


class TemplatesSpec:
    """What the usage needs to know about `wio templates`, and nothing more."""

    name = "templates"
    help = "List the project's templates."

    def configure(self, parser: ArgumentParser) -> None:
        """Add the views of `wio templates` to its subparser.

        Args:
            parser: The subparser that `wio.cli` created for `templates`.
        """
        parser.set_defaults(templates_view=None, templates_help=parser.format_help)
        views = parser.add_subparsers(title="subcommands", metavar="<subcommand>")
        _add_list(views)


def _add_list(views: _SubParsers) -> None:
    """Add `list` with its two options to the subcommands of `templates`.

    Args:
        views: The subcommands that `wio.cli` created for `templates`.
    """
    parser = views.add_parser("list", help=_LIST_HELP, description=_LIST)
    parser.add_argument("--kind", metavar="kind", default=None, help=_KIND)
    parser.add_argument("--json", action="store_true", help=_JSON)
    parser.set_defaults(templates_view="list")


_LIST_HELP = "List the templates by kind."
_LIST = (
    "List the templates grouped by kind, each with its name, whether it is the "
    "entry template of its kind, its shape and its description. Refuses to list "
    "while a template has an error: `wio templates check` shows every problem."
)
_KIND = "Show only the templates of this declared kind."
_JSON = "Write one JSON array of the templates instead of the grouped text."


def describe() -> TemplatesSpec:
    """Describe `wio templates` without loading its implementation.

    Returns:
        The command spec of `templates`.
    """
    return TemplatesSpec()


__all__ = ["Discovery", "TemplatesCommand", "TemplatesError", "describe", "discover"]
