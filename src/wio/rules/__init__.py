# SPDX-License-Identifier: Apache-2.0
"""The `wio rules` command: creating, checking, listing and showing rules."""

from dataclasses import astuple, dataclass
from functools import partial
from typing import TYPE_CHECKING, Final

lazy from wio.rules.anywhere import Origin, SelectedAnywhere, selected_anywhere
lazy from wio.rules.applicability import select
lazy from wio.rules.checking import check_rules
lazy from wio.rules.chooser import RuleSelector
lazy from wio.rules.command import RulesCommand
lazy from wio.rules.discovery import Discovery, discover, refuse_on_errors
lazy from wio.rules.errors import check_errors
lazy from wio.rules.expansion import (
    ConfigScope,
    Expansion,
    Problem,
    RuleCatalog,
    RulesetScope,
    Scope,
    expand,
)
lazy from wio.rules.explaining import RuleExplanation, explain
lazy from wio.rules.inputs import (
    Layer,
    build_rule_catalog,
    chain_labels,
    chain_text,
    layer_label,
    resolve_ruleset,
    ruleset_map,
)
lazy from wio.rules.layers import Layered, RuleLayers, apply_layers
lazy from wio.rules.manifest import ManifestReading, read_manifest
lazy from wio.rules.narrowing import narrow
lazy from wio.rules.reading import RULE_NAME, RULE_NAME_FORM, RuleReading, read_rule
lazy from wio.rules.roots import roots_of_path, stage_roots
lazy from wio.rules.warns import check_warnings

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace
    from collections.abc import Callable, Sequence

    from wio.env.ports import Environment
    from wio.io.ports import FileSystem, Repository, Stdio
    from wio.ports import Settings
    from wio.rules.ports import WorkRoots


@dataclass(frozen=True)
class Services:
    """What a subcommand of `wio rules` reads the project through.

    Provisional: a subcommand that needs another port adds a field.

    Attributes:
        settings: Loads the config.
        repository: Finds the repository root.
        files: Lists and reads files.
        environment: Gives the working directory that a path argument is
            resolved against.
        work_roots: Gives the roots of a Work, for `--work`.
    """

    settings: Settings
    repository: Repository
    files: FileSystem
    environment: Environment
    work_roots: WorkRoots


@dataclass(frozen=True, slots=True)
class Subcommand:
    """One entry of the table of `wio rules`: what it is and what it does.

    Each subcommand adds one to `SUBCOMMANDS`. Describing reads `name`, `help` and
    `configure` and nothing else, so `handler` is the only field that may load the
    code of the subcommand.

    Attributes:
        name: What the user types after `wio rules` to choose it.
        help: The line of `wio rules --help` that introduces it.
        configure: Declares its arguments on its subparser, with no I/O, because
            every run describes every subcommand.
        handler: Does the work with the services, the parsed arguments and the
            streams. It returns 0, or 1 when a check fails, and raises a
            `WioError` for a mistake that the user must fix.
    """

    name: str
    help: str
    configure: Callable[[ArgumentParser], None]
    handler: Callable[[Services, Namespace, Stdio], int]


def json_option(parser: ArgumentParser, *, help: str) -> None:  # noqa: A002
    """Declare the `--json` option of a subcommand.

    Every subcommand that writes JSON declares the option here, so that it has
    one spelling and one meaning: with it, standard output holds one JSON
    document and nothing else on exit 0 or 1, and nothing on exit 2.

    Args:
        parser: The subparser.
        help: What `--help` says of it.
    """
    parser.add_argument("--json", dest="json", action="store_true", help=help)


_CHECK_HELP = "Report every fault of the rule files and the references."
_CHECK_JSON = "Write one JSON array of the findings instead of the text."


def _check(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Run `wio rules check` through its own module.

    Args:
        services: What the subcommand reads the project through.
        args: The parsed arguments.
        stdio: Where the report goes.

    Returns:
        The exit code, 1 when the report holds an error.
    """
    from wio.rules.checking import run_check

    return run_check(services, args, stdio)


_LIST_HELP = "List the rules that a root, a path, a Work or a stage is given."
_LIST_JSON = "Write one JSON object with the header and the rules."


def _configure_list(parser: ArgumentParser) -> None:
    """Declare the arguments of `wio rules list`.

    Args:
        parser: The subparser.
    """
    views = parser.add_mutually_exclusive_group()
    views.add_argument("--root", help="The root whose rules to list.")
    views.add_argument("--path", help="A file whose roots to apply.")
    views.add_argument("--work", help="The id of a Work whose roots to apply.")
    parser.add_argument("--stage", help="The stage whose layer to apply.")
    parser.add_argument(
        "--not-selected",
        dest="not_selected",
        action="store_true",
        help="List the rules that nothing selects.",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Say where each rule came from.",
    )
    json_option(parser, help=_LIST_JSON)
    parser.add_argument(
        "references", nargs="*", help="Rules, families or rulesets to narrow to."
    )


_NEW_HELP = "Create the next rule of a family in a ruleset."
_NEW_JSON = "Write one JSON object with the new rule and what selects it."


def _configure_new(parser: ArgumentParser) -> None:
    """Declare the arguments of `wio rules new`.

    Args:
        parser: The subparser.
    """
    parser.add_argument("ruleset", help="The ruleset, by its name or its alias.")
    parser.add_argument("family", help="The family, such as ARC, to add a rule to.")
    parser.add_argument("--name", required=True, help="The name of the new rule.")
    parser.add_argument("--description", help="A one-line description of the new rule.")
    json_option(parser, help=_NEW_JSON)


def _new(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Run `wio rules new` through its own module.

    Args:
        services: What the subcommand reads and writes the project through.
        args: The parsed arguments.
        stdio: Where the result goes.

    Returns:
        0 after the rule was created.
    """
    from wio.rules.creating import run_new

    return run_new(services, args, stdio)


_SHOW_HELP = "Show one rule by its qualified code."
_SHOW_REFERENCE = "The rule, as <ruleset>.<code>; the ruleset may be an alias."
_SHOW_JSON = "Write one JSON object with the rule instead of the text."


def _configure_show(parser: ArgumentParser) -> None:
    """Declare the arguments of `wio rules show`.

    Args:
        parser: The subparser.
    """
    json_option(parser, help=_SHOW_JSON)
    parser.add_argument("reference", help=_SHOW_REFERENCE)


def _show(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Run `wio rules show` through its own module.

    Args:
        services: What the subcommand reads the project through.
        args: The parsed arguments.
        stdio: Where the rule goes.

    Returns:
        0 after the rule was printed.
    """
    from wio.rules import showing

    return showing.run_show(services, args, stdio)


def _list(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Run `wio rules list` through its own module.

    Args:
        services: What the subcommand reads the project through.
        args: The parsed arguments.
        stdio: Where the listing goes.

    Returns:
        0 after the listing.
    """
    from wio.rules.listing import run_list

    return run_list(services, args, stdio)


SUBCOMMANDS: Final[Sequence[Subcommand]] = (
    Subcommand("check", _CHECK_HELP, partial(json_option, help=_CHECK_JSON), _check),
    Subcommand("list", _LIST_HELP, _configure_list, _list),
    Subcommand("new", _NEW_HELP, _configure_new, _new),
    Subcommand("show", _SHOW_HELP, _configure_show, _show),
)
"""The subcommands of `wio rules`, to which each subcommand Work adds an entry.

It lives here and not in a module of its own, because describing the command
loads no module of the package besides this one, and that holds for `configure`
as well, which runs when the command is described. So an entry's `configure` is
defined in this module, and its `handler` is a function of this module that
imports the module of the subcommand when it runs. A `lazy from` in the tuple
would not defer anything, because the names are used as the tuple is built.
"""


class RulesSpec:
    """What the usage needs to know about `wio rules`, and nothing more."""

    name = "rules"
    help = "Create, list, check and show the rules of the project."

    def __init__(self, table: Sequence[Subcommand] = SUBCOMMANDS) -> None:
        """Remember which subcommands to describe.

        Args:
            table: The entries; the package's own table unless a test passes
                another.
        """
        self._entries = tuple(table)

    def configure(self, parser: ArgumentParser) -> None:
        """Declare each entry of the table as a subparser of `rules`.

        Nothing is read or imported here. The defaults `rules_subcommand`, which
        is `None` when no subcommand was typed, and `rules_help`, the usage text,
        let the bare command answer without loading a config.

        Args:
            parser: The subparser that `wio.cli` created for `rules`.
        """
        parser.set_defaults(rules_subcommand=None, rules_help=parser.format_help)
        views = parser.add_subparsers(title="subcommands", metavar="<subcommand>")
        for name, text, configure, _ in map(astuple, self._entries):
            subparser = views.add_parser(name, help=text, description=text)
            subparser.set_defaults(rules_subcommand=name)
            configure(subparser)


def describe(table: Sequence[Subcommand] = SUBCOMMANDS) -> RulesSpec:
    """Describe `wio rules` without loading its implementation.

    Args:
        table: The subcommands, which a test replaces.

    Returns:
        The command spec of `rules`.
    """
    return RulesSpec(table)


__all__ = [
    "RULE_NAME",
    "RULE_NAME_FORM",
    "SUBCOMMANDS",
    "ConfigScope",
    "Discovery",
    "Expansion",
    "Layer",
    "Layered",
    "ManifestReading",
    "Origin",
    "Problem",
    "RuleCatalog",
    "RuleExplanation",
    "RuleLayers",
    "RuleReading",
    "RuleSelector",
    "RulesCommand",
    "RulesSpec",
    "RulesetScope",
    "Scope",
    "SelectedAnywhere",
    "Services",
    "Subcommand",
    "apply_layers",
    "build_rule_catalog",
    "chain_labels",
    "chain_text",
    "check_errors",
    "check_rules",
    "check_warnings",
    "describe",
    "discover",
    "expand",
    "explain",
    "json_option",
    "layer_label",
    "narrow",
    "read_manifest",
    "read_rule",
    "refuse_on_errors",
    "resolve_ruleset",
    "roots_of_path",
    "ruleset_map",
    "select",
    "selected_anywhere",
    "stage_roots",
]
