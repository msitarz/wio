# SPDX-License-Identifier: Apache-2.0
"""The `wio templates` command: listing, showing and checking templates."""

from typing import TYPE_CHECKING

lazy from wio.templates.command import TemplatesCommand
lazy from wio.templates.discovery import Discovery, discover
lazy from wio.templates.errors import TemplatesError
lazy from wio.templates.reference import render_reference
lazy from wio.templates.show import show_skeleton

if TYPE_CHECKING:
    from argparse import ArgumentParser, _SubParsersAction

    type _SubParsers = _SubParsersAction[ArgumentParser]


class TemplatesSpec:
    """What the usage needs to know about `wio templates`, and nothing more."""

    name = "templates"
    help = "List, show and explain the project's templates."

    def configure(self, parser: ArgumentParser) -> None:
        """Add the views of `wio templates` to its subparser.

        Args:
            parser: The subparser that `wio.cli` created for `templates`.
        """
        views = parser.add_subparsers(title="subcommands", metavar="<subcommand>")
        parser.set_defaults(templates_view=None, templates_help=parser.format_help)
        listing = _subcommand(views, "list", _LIST_HELP, _LIST)
        listing.add_argument("--kind", metavar="kind", default=None, help=_KIND)
        listing.add_argument("--json", action="store_true", help=_JSON)
        shown = _subcommand(views, "show", _SHOW_HELP, _SHOW)
        shown.add_argument("name", metavar="name", help=_NAME)
        grammar = _subcommand(views, "directives", _DIRECTIVES_HELP, _DIRECTIVES)
        grammar.add_argument("--json", action="store_true", help=_DIRECTIVES_JSON)


def _subcommand(views: _SubParsers, view: str, short: str, long: str) -> ArgumentParser:
    """Add a subcommand of `templates` and name its view.

    Args:
        views: The subcommands that `wio.cli` created for `templates`.
        view: The subcommand's name, which `templates_view` holds when chosen.
        short: The line that `wio templates --help` shows for it.
        long: The description that its own `--help` shows.

    Returns:
        The subparser, for its arguments.
    """
    parser = views.add_parser(view, help=short, description=long)
    parser.set_defaults(templates_view=view)
    return parser


_LIST_HELP = "List the templates by kind."
_LIST = (
    "List the templates grouped by kind, each with its name, whether it is the "
    "entry template of its kind, its shape and its description. Refuses to list "
    "while a template has an error: `wio templates check` shows every problem."
)
_SHOW_HELP = "Print a template as the skeleton of a contract."
_SHOW = (
    "Print the skeleton of the template with this name, exactly as `wio contracts "
    "new` would write it but without an id, and nothing else. Refuses while a "
    "template has an error: `wio templates check` shows every problem."
)
_DIRECTIVES_HELP = "Print the directives that a template may use."
_DIRECTIVES = (
    "Print every directive of the grammar with its syntax, its meaning and its "
    "examples. It reads no file of the project and no config, so it works "
    "anywhere."
)
_DIRECTIVES_JSON = "Write one JSON array of the directives instead of the list."
_NAME = "The template's name, which is its file's name without `.md`."
_KIND = "Show only the templates of this declared kind."
_JSON = "Write one JSON array of the templates instead of the grouped text."


def describe() -> TemplatesSpec:
    """Describe `wio templates` without loading its implementation.

    Returns:
        The command spec of `templates`.
    """
    return TemplatesSpec()


__all__ = [
    "Discovery",
    "TemplatesCommand",
    "TemplatesError",
    "describe",
    "discover",
    "render_reference",
    "show_skeleton",
]
