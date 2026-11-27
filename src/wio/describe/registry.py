# SPDX-License-Identifier: Apache-2.0
"""Code-derived registry of engine and subcommand descriptions."""

import builtins
import dataclasses
import importlib.metadata
import types
import typing
from functools import cache
from typing import TYPE_CHECKING

from wio.describe.models import (
    CommandDescription,
    CommandForm,
    CommandSummary,
    Concept,
    EngineDescription,
    ExitCode,
    ReferenceEntry,
    ReferenceTable,
)
from wio.errors import WioError
from wio.formats.directives import COMBINING, DIRECTIVES
from wio.models.config import Config

if TYPE_CHECKING:
    from collections.abc import Sequence

_DISTRIBUTION = "work-it-out"

_ENGINE_SUMMARY = (
    "Configurable, stage-gated workflow engine for AI agents, with contracts, "
    "templates, rules and git-trailer audit records."
)

_EXIT_CODES: tuple[ExitCode, ...] = (
    ExitCode(0, "Success, including `--help` and `--version`."),
    ExitCode(1, "A check ran and reported one or more error diagnostics."),
    ExitCode(
        2,
        "Usage error or `WioError`: invalid arguments, missing config, or a "
        "condition the user must fix.",
    ),
    ExitCode(
        70,
        "Internal software error (unexpected exception or invalid exit code).",
    ),
)

_CONCEPTS: tuple[Concept, ...] = (
    Concept("Work", "A deliverable unit tracked by a contract with a 6-character id."),
    Concept(
        "Contract",
        "Markdown file under `[works] dir` stating intent, criteria and constraints.",
    ),
    Concept(
        "Template",
        "Markdown blueprint with `<!-- wio: ... -->` section directives.",
    ),
    Concept("Action", "Lifecycle operation (`define`, `deliver`, `amend`, `ratify`)."),
    Concept("Stage", "One step in an action pipeline; gates require a fresh session."),
    Concept("Root", "Named repository area that selects applicable rulesets."),
    Concept("Rule", "Scoped coding or writing guideline delivered with stage context."),
    Concept(
        "Trailer",
        "`Wio-*` git commit trailer recording work, stage and gate results.",
    ),
)

_COMMANDS: dict[str, CommandDescription] = {
    "config": CommandDescription(
        name="config",
        summary="Show the project's settings and where each one comes from.",
        forms=(
            CommandForm(
                "wio config list [--json]",
                "List every setting with its source.",
            ),
            CommandForm(
                "wio config show [<key.path>] [--json]",
                "Show a setting or table in full with its source and description.",
            ),
            CommandForm(
                "wio config check [--json]",
                "Validate `.agents/wio/config.toml` and report diagnostics.",
            ),
        ),
        invariants=(
            (
                "Every setting resolves from `.agents/wio/config.toml` or its "
                "built-in default."
            ),
            "`check` exits 1 on error diagnostics and 2 when no config file exists.",
        ),
    ),
    "context": CommandDescription(
        name="context",
        summary="Print what an agent session reads for a stage of a Work.",
        forms=(
            CommandForm(
                "wio context <work> <action> <stage> [--output [<path>]]",
                (
                    "Compile the contract, stage goal, skill and applicable rules "
                    "into a bundle (or write it to a file with `--output`)."
                ),
            ),
        ),
        invariants=(
            "Resolves inherited sections from ancestor contracts automatically.",
            "Selects rulesets matching the Work's roots and the stage's rule filter.",
            (
                "Records a context event to the clone log when writable; never "
                "fails on log errors."
            ),
        ),
    ),
    "contracts": CommandDescription(
        name="contracts",
        summary="Create, list, check and show the Work contracts of the project.",
        forms=(
            CommandForm(
                (
                    "wio contracts new [<kind>] [--template <name>] "
                    "[--title <text> | --slug <slug> | --path <path>] "
                    "[--parent <id>] [--root <name>] [--json]"
                ),
                "Create a new contract from a kind or template with a fresh id.",
            ),
            CommandForm(
                "wio contracts list [--json]",
                (
                    "List all contracts in tree order with their ids, templates "
                    "and dependencies."
                ),
            ),
            CommandForm(
                "wio contracts show <id-or-path> [--json]",
                (
                    "Show a contract's facts, actions, dependents and resolved "
                    "view with inherited sections."
                ),
            ),
            CommandForm(
                "wio contracts skeleton <work> <template> [--keep roots|actions]",
                "Print a template skeleton pre-populated for an existing Work.",
            ),
            CommandForm(
                "wio contracts check [--json]",
                (
                    "Validate all contracts against their templates, ids and "
                    "dependency graph."
                ),
            ),
        ),
        invariants=(
            (
                "Contracts never store status fields; progress lives in git "
                "commit trailers."
            ),
            (
                "`check` validates the whole tree for duplicate ids, cycles and "
                "broken dependencies."
            ),
        ),
    ),
    "describe": CommandDescription(
        name="describe",
        summary="Describe the wio engine or one subcommand offline.",
        forms=(
            CommandForm(
                "wio describe [--json]",
                "Show version, exit codes, core concepts and registered subcommands.",
            ),
            CommandForm(
                "wio describe <command> [--json]",
                (
                    "Show one subcommand's forms, invariants and code-derived "
                    "reference data."
                ),
            ),
        ),
        invariants=(
            "Runs offline without a git repository or `.agents/wio/config.toml`.",
            "Produces deterministic output with no timestamps.",
        ),
    ),
    "log": CommandDescription(
        name="log",
        summary="Show events and record reviews.",
        forms=(
            CommandForm(
                "wio log show [--work <id>] [--json]",
                "Show recorded stage context and gate review events.",
            ),
            CommandForm(
                (
                    "wio log review <work> <action> <stage> --result <r> "
                    "[--judge <j>] [--cite <items>] [--reviewed <sha>]"
                ),
                "Record a gate review result in the clone event log.",
            ),
        ),
        invariants=(
            "Events are stored per clone outside the working tree.",
            "`review` validates the work, action, stage and result before recording.",
        ),
    ),
    "rules": CommandDescription(
        name="rules",
        summary="Create, list, check and show the rules of the project.",
        forms=(
            CommandForm(
                "wio rules list [--path <file>] [--root <name>] [--json]",
                "List rules, optionally filtered by file path or root.",
            ),
            CommandForm(
                "wio rules show <rule-id> [--json]",
                "Show the full text and metadata of one rule.",
            ),
            CommandForm(
                "wio rules check [--json]",
                "Validate all ruleset files and report diagnostics.",
            ),
            CommandForm(
                (
                    "wio rules new <ruleset> <family> --name <name> "
                    "[--description <text>] [--json]"
                ),
                "Create the next rule of a family in a ruleset.",
            ),
        ),
        invariants=(
            "Rules are grouped into rulesets and selected by root or file path.",
            "Rule ids follow `<ruleset>.<CODE>` and must be unique.",
        ),
    ),
    "templates": CommandDescription(
        name="templates",
        summary="List, show, check and explain the project's templates.",
        forms=(
            CommandForm(
                "wio templates list [--kind <kind>] [--json]",
                "List available contract templates grouped by kind.",
            ),
            CommandForm(
                "wio templates show <name>",
                "Print a template prepared as a contract skeleton.",
            ),
            CommandForm(
                "wio templates check [--json]",
                "Validate all templates under `[templates] dir`.",
            ),
            CommandForm(
                "wio templates directives [--json]",
                "Print the `<!-- wio: ... -->` heading directive grammar.",
            ),
        ),
        invariants=(
            (
                "Directives appear in one `<!-- wio: ... -->` comment at the "
                "end of a heading."
            ),
            "Supported directives are derived directly from `wio.formats.directives`.",
        ),
    ),
    "trailers": CommandDescription(
        name="trailers",
        summary="Print, check and fold the Wio records of commits.",
        forms=(
            CommandForm(
                (
                    "wio trailers <work> <action> <stage> [--items <ids>] "
                    "[--result <r>] [--judge <j>] [--cite <items>] "
                    "[--reviewed <sha>]"
                ),
                "Print `Wio-*` trailers for a commit message.",
            ),
            CommandForm(
                "wio trailers none",
                "Print the `Wio-Work: none` record for a commit outside any Work.",
            ),
            CommandForm(
                "wio trailers check [--require] [<file> | --body <file> | --range <r>]",
                "Validate `Wio-*` trailers in a commit message, body or range.",
            ),
            CommandForm(
                "wio trailers fold <range>",
                "Fold `Wio-*` trailers across a commit range for a pull request.",
            ),
        ),
        invariants=(
            (
                "Every commit carries `Wio-*` trailers (`Wio-Work: none` when "
                "outside a Work)."
            ),
            "Gate commits record `Wio-Result` and `Wio-Judge`.",
        ),
    ),
}


def registered_commands() -> tuple[str, ...]:
    """Return the sorted names of all commands in the descriptor registry.

    Returns:
        Sorted tuple of command names.
    """
    return tuple(sorted(_COMMANDS))


def describe_engine(commands: Sequence[str] | None = None) -> EngineDescription:
    """Build the top-level description of the `wio` engine.

    Performs no filesystem or network I/O and returns deterministic data.

    Args:
        commands: Optional sequence of command names to include. When omitted,
            every command in the descriptor registry is included.

    Returns:
        The immutable `EngineDescription` for the installed `wio` package.

    Raises:
        WioError: If `commands` contains a name that is not registered.
    """
    names = registered_commands() if commands is None else tuple(sorted(commands))
    summaries = tuple(
        CommandSummary(name=name, summary=_lookup(name).summary) for name in names
    )
    return EngineDescription(
        version=importlib.metadata.version(_DISTRIBUTION),
        summary=_ENGINE_SUMMARY,
        exit_codes=_EXIT_CODES,
        concepts=_CONCEPTS,
        commands=summaries,
    )


def describe_command(name: str) -> CommandDescription:
    """Build the detailed description of one `wio` subcommand.

    Combines concise per-command semantics with code-derived reference tables
    (config schema keys for `config`, directive grammar for `templates`).

    Args:
        name: Subcommand name to describe.

    Returns:
        The immutable `CommandDescription` for `name`.

    Raises:
        WioError: If `name` is not a registered command; the message lists all
            valid command names.
    """
    base = _lookup(name)
    match name:
        case "config":
            return dataclasses.replace(base, references=(_config_reference(),))
        case "templates":
            return dataclasses.replace(base, references=(_directives_reference(),))
        case _:
            return base


def _lookup(name: str) -> CommandDescription:
    """Return the base descriptor for `name` or raise `WioError`."""
    description = _COMMANDS.get(name)
    if description is None:
        valid = ", ".join(registered_commands())
        message = f"unknown command {name!r}; valid commands are: {valid}"
        raise WioError(message)
    return description


@cache
def _config_reference() -> ReferenceTable:
    """Derive the config key reference table from `wio.models.config.Config`."""
    entries = tuple(_collect_config_entries(Config, ""))
    return ReferenceTable(title="Config schema keys", entries=entries)


def _collect_config_entries(cls: type, prefix: str) -> list[ReferenceEntry]:
    """Walk a config dataclass and collect leaf and open-table key entries."""
    hints = typing.get_type_hints(cls)
    entries: list[ReferenceEntry] = []
    for field in dataclasses.fields(cls):
        path = f"{prefix}.{field.name}".lstrip(".")
        hint = _unwrap_alias(hints[field.name])
        description = str(field.metadata["description"])
        entries.extend(_field_entries(path, hint, description))
    return entries


def _field_entries(path: str, hint: object, description: str) -> list[ReferenceEntry]:
    """Build reference entries for one config dataclass field."""
    if dataclasses.is_dataclass(hint) and isinstance(hint, type):
        return _collect_config_entries(hint, path)
    if typing.get_origin(hint) is builtins.frozendict:
        return _open_table_entries(path, hint, description)
    return [ReferenceEntry(path, _format_hint(hint), description)]


def _open_table_entries(
    path: str, hint: object, description: str
) -> list[ReferenceEntry]:
    """Build reference entries for a `frozendict` open table and its member fields."""
    entries = [ReferenceEntry(path, "table", description)]
    value_type = _unwrap_alias(typing.get_args(hint)[1])
    if dataclasses.is_dataclass(value_type) and isinstance(value_type, type):
        entries.extend(_collect_config_entries(value_type, f"{path}.<name>"))
    return entries


def _unwrap_alias(hint: object) -> object:
    """Resolve a PEP 695 `type` alias to its underlying annotation."""
    return hint.__value__ if isinstance(hint, typing.TypeAliasType) else hint


def _format_union(args: tuple[object, ...]) -> str:
    """Format a union annotation, omitting `NoneType`."""
    parts = [_format_hint(_unwrap_alias(a)) for a in args if a is not type(None)]
    return " | ".join(parts)


def _format_hint(hint: object) -> str:
    """Format a config field type annotation concisely."""
    origin = typing.get_origin(hint)
    args = typing.get_args(hint)
    match origin:
        case types.UnionType:
            return _format_union(args)
        case typing.Literal:
            return " | ".join(str(a) for a in args)
        case builtins.tuple:
            return "list[str]"
        case _:
            return hint.__name__ if isinstance(hint, type) else str(hint)


@cache
def _directives_reference() -> ReferenceTable:
    """Derive the template directive reference table from `wio.formats.directives`."""
    entries = tuple(
        ReferenceEntry(key=spec.name, value=spec.syntax, description=spec.meaning)
        for spec in (*DIRECTIVES, *COMBINING)
    )
    return ReferenceTable(title="Template directives", entries=entries)
