# SPDX-License-Identifier: Apache-2.0
"""The `wio contracts` command: creating, checking and showing Work contracts."""

from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Final

lazy from wio.contracts.checking import run_check
lazy from wio.contracts.command import ContractsCommand
lazy from wio.contracts.context_view import ContractViews as ContractViews
lazy from wio.contracts.creation import run_new
lazy from wio.contracts.discovery import (
    WorkDiscovery,
    discover_works,
    explain_not_a_work,
    find_work,
)
lazy from wio.contracts.errors import ContractsError
lazy from wio.contracts.hierarchy import Hierarchy, build_hierarchy
lazy from wio.contracts.listing import run_list
lazy from wio.contracts.location import (
    IdGenerator,
    NameArguments,
    RandomIds,
    choose_slug,
    decide_place,
    new_id,
    write_new,
)
lazy from wio.contracts.lookup import WorkLookup
lazy from wio.contracts.resolve import render_resolved, resolve_work
lazy from wio.contracts.showing import run_show
lazy from wio.contracts.skeleton import run_skeleton

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace
    from collections.abc import Callable, Sequence

    from wio.contracts.ports import TemplateCatalog
    from wio.env.ports import Entropy, Environment
    from wio.io.ports import FileSystem, Repository, Stdio
    from wio.ports import Settings


@dataclass(frozen=True)
class Services:
    """What a subcommand reads the project through.

    Provisional: a leaf that needs another port adds a field.

    Attributes:
        settings: Loads the config.
        repository: Finds the repository root.
        files: Lists and reads files.
        catalog: Finds the templates of the project.
        entropy: Gives the random bytes of a new id.
        environment: Gives the working directory that a path argument is
            resolved against.
    """

    settings: Settings
    repository: Repository
    files: FileSystem
    catalog: TemplateCatalog
    entropy: Entropy
    environment: Environment


@dataclass(frozen=True)
class Subcommand:
    """One subcommand of `wio contracts`, described and run apart.

    Provisional: the field names and the handler's signature may change, and the
    entry holds at least these four things.

    Attributes:
        name: The subcommand's name, as typed after `wio contracts`.
        help: One line that `wio contracts --help` shows for it.
        configure: Adds its arguments to its subparser. It does no I/O, because
            it runs on every run.
        handler: Runs it with the services, the parsed arguments and the
            streams, and returns the exit code: 0, or 1 for a failed check. A
            mistake the user must fix is a `ContractsError`, and not a code.
    """

    name: str
    help: str
    configure: Callable[[ArgumentParser], None]
    handler: Callable[[Services, Namespace, Stdio], int]


_CHECK_HELP = "Report every problem of the Works."
_CHECK_JSON = "Write one JSON array of the problems instead of the text."
_LIST_HELP = "List the Works with their hierarchy and their overrides."
_LIST_JSON = "Write one JSON array of the Works instead of the text."
_NEW_HELP = "Create a Work from a template or as a bare contract."
_NEW_JSON = "Write one JSON object describing the created Work."
_SHOW_HELP = "Show one Work with its facts, its actions and its resolved contract."
_SHOW_JSON = "Write one JSON object of the Work instead of the text."
_SKELETON_HELP = "Print a template's skeleton for an existing Work."


def _json_option(parser: ArgumentParser, *, help: str) -> None:  # noqa: A002
    """Add the `--json` option of a subcommand.

    Args:
        parser: The subparser.
        help: What `--help` says of it.
    """
    parser.add_argument("--json", action="store_true", help=help)


def _configure_show(parser: ArgumentParser) -> None:
    """Add the argument that names the Work to show, and `--json`.

    Args:
        parser: The subparser.
    """
    parser.add_argument("work", help="Id of the Work, or the path of its contract.")
    _json_option(parser, help=_SHOW_JSON)


def _configure_skeleton(parser: ArgumentParser) -> None:
    """Add the template to print, `--work` and `--keep`.

    `--work` is not marked required here, because `run_skeleton` reports its
    absence with a pointer to `wio templates show`, which the parser cannot.

    Args:
        parser: The subparser.
    """
    parser.add_argument("template", help="Name of the template.")
    parser.add_argument("--work", help="Id of the Work whose identity to carry.")
    parser.add_argument(
        "--keep", action="append", default=[], help="Key of the Work to carry."
    )


def _show(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Run `wio contracts show`.

    Args:
        services: What the subcommand reads the project through.
        args: The parsed arguments.
        stdio: Where the output goes.

    Returns:
        The exit code.
    """
    return run_show(services, args, stdio)


def _skeleton(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Run `wio contracts skeleton`.

    Args:
        services: What the subcommand reads the project through.
        args: The parsed arguments.
        stdio: Where the skeleton and the note go.

    Returns:
        The exit code.
    """
    return run_skeleton(services, args, stdio)


def _check(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Run `wio contracts check`.

    Args:
        services: What the subcommand reads the project through.
        args: The parsed arguments.
        stdio: Where the output goes.

    Returns:
        The exit code, 1 when the Works have an error.
    """
    return run_check(services, args, stdio)


def _list(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Run `wio contracts list`.

    Args:
        services: What the subcommand reads the project through.
        args: The parsed arguments.
        stdio: Where the output goes.

    Returns:
        The exit code.
    """
    return run_list(services, args, stdio)


def _configure_new(parser: ArgumentParser) -> None:
    """Add the options that choose and name a new Work.

    Args:
        parser: The subparser.
    """
    parser.add_argument("kind", nargs="?", help="Kind whose entry template to use.")
    parser.add_argument("--template", help="Template to use.")
    parser.add_argument("--parent", help="Id of the parent Work.")
    parser.add_argument("--slug", help="Name of the Work's directory.")
    parser.add_argument("--title", help="Title of the Work.")
    parser.add_argument("--path", help="Path of the new contract.")
    parser.add_argument("--root", action="append", default=[], help="Root to add.")
    _json_option(parser, help=_NEW_JSON)


def _new(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Run the new Work subcommand through its leaf.

    Args:
        services: What the subcommand reads the project through.
        args: The parsed arguments.
        stdio: Where the output goes.

    Returns:
        The exit code.
    """
    return run_new(services, args, stdio)


SUBCOMMANDS: Final[Sequence[Subcommand]] = (
    Subcommand("check", _CHECK_HELP, partial(_json_option, help=_CHECK_JSON), _check),
    Subcommand("list", _LIST_HELP, partial(_json_option, help=_LIST_JSON), _list),
    Subcommand("new", _NEW_HELP, _configure_new, _new),
    Subcommand("show", _SHOW_HELP, _configure_show, _show),
    Subcommand("skeleton", _SKELETON_HELP, _configure_skeleton, _skeleton),
)
"""The subcommands of `wio contracts`, to which each leaf adds its own entry.

It lives here and not in a module of its own, because describing the command
loads no module of the package besides this one, and that holds for `configure`
as well, which runs when the command is described. So an entry's `configure` is
defined in this module, and its `handler` is a function of this module that
imports the leaf's own module when it runs. A `lazy from` in the tuple would
not defer anything, because the names are used as the tuple is built.
"""


class ContractsSpec:
    """What the usage needs to know about `wio contracts`, and nothing more."""

    name = "contracts"
    help = "Create, list, check and show the Work contracts of the project."

    def __init__(self, table: Sequence[Subcommand] = SUBCOMMANDS) -> None:
        """Keep the table that the subcommands are described from.

        Args:
            table: The subcommands, which defaults to the table of the package
                and which a test replaces.
        """
        self._table = table

    def configure(self, parser: ArgumentParser) -> None:
        """Add the subcommands of `wio contracts` to its subparser.

        It does no I/O and imports no codec, and sets the defaults
        `contracts_subcommand` (`None` for the bare command) and `contracts_help`
        (the usage), so that the bare command loads no config.

        Args:
            parser: The subparser that `wio.cli` created for `contracts`.
        """
        views = parser.add_subparsers(title="subcommands", metavar="<subcommand>")
        parser.set_defaults(
            contracts_subcommand=None, contracts_help=parser.format_help
        )
        for entry in self._table:
            subparser = views.add_parser(
                entry.name, help=entry.help, description=entry.help
            )
            subparser.set_defaults(contracts_subcommand=entry.name)
            entry.configure(subparser)


def describe(table: Sequence[Subcommand] = SUBCOMMANDS) -> ContractsSpec:
    """Describe `wio contracts` without loading its implementation.

    Args:
        table: The subcommands, which a test replaces.

    Returns:
        The command spec of `contracts`.
    """
    return ContractsSpec(table)


__all__ = [
    "SUBCOMMANDS",
    "ContractViews",
    "ContractsCommand",
    "ContractsError",
    "ContractsSpec",
    "Hierarchy",
    "IdGenerator",
    "NameArguments",
    "RandomIds",
    "Services",
    "Subcommand",
    "WorkDiscovery",
    "WorkLookup",
    "build_hierarchy",
    "choose_slug",
    "decide_place",
    "describe",
    "discover_works",
    "explain_not_a_work",
    "find_work",
    "new_id",
    "render_resolved",
    "resolve_work",
    "run_check",
    "write_new",
]
