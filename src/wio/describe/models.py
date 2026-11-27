# SPDX-License-Identifier: Apache-2.0
"""Immutable descriptor models for `wio describe`."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExitCode:
    """One CLI exit code and its meaning.

    Attributes:
        code: Numeric process exit status.
        meaning: Short description of when `wio` returns this code.
    """

    code: int
    meaning: str


@dataclass(frozen=True)
class Concept:
    """One core engine concept in the top-level overview.

    Attributes:
        name: Concept name as used in the glossary and CLI.
        summary: One-sentence definition of the concept.
    """

    name: str
    summary: str


@dataclass(frozen=True)
class CommandSummary:
    """One subcommand entry in the engine overview.

    Attributes:
        name: Subcommand name as invoked after `wio`.
        summary: One-sentence description of what the subcommand does.
    """

    name: str
    summary: str


@dataclass(frozen=True)
class CommandForm:
    """One invocation form or subcommand of a `wio` command.

    Attributes:
        usage: Synopsis showing the subcommand and arguments.
        summary: One-sentence description of what this form does.
    """

    usage: str
    summary: str


@dataclass(frozen=True)
class ReferenceEntry:
    """One row of code-derived reference data for a command.

    Attributes:
        key: Identifier such as a config key path or directive name.
        value: Syntax, type, or default summary for the entry.
        description: Short explanation of the entry.
    """

    key: str
    value: str
    description: str


@dataclass(frozen=True)
class ReferenceTable:
    """A named table of code-derived reference entries.

    Attributes:
        title: Section heading for the table.
        entries: Ordered rows in the table.
    """

    title: str
    entries: tuple[ReferenceEntry, ...]


@dataclass(frozen=True)
class EngineDescription:
    """Top-level description of the `wio` engine.

    Attributes:
        version: Installed `work-it-out` package version.
        summary: One-sentence overview of `wio`.
        exit_codes: Process exit codes and their meanings.
        concepts: Core workflow concepts.
        commands: Sorted summaries of registered subcommands.
    """

    version: str
    summary: str
    exit_codes: tuple[ExitCode, ...]
    concepts: tuple[Concept, ...]
    commands: tuple[CommandSummary, ...]


@dataclass(frozen=True)
class CommandDescription:
    """Detailed description of one `wio` subcommand.

    Attributes:
        name: Subcommand name.
        summary: One-sentence description of the command.
        forms: Invocation forms and subcommands.
        invariants: Key behavioral guarantees and constraints.
        references: Optional code-derived reference tables.
    """

    name: str
    summary: str
    forms: tuple[CommandForm, ...]
    invariants: tuple[str, ...]
    references: tuple[ReferenceTable, ...] = ()
