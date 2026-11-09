# SPDX-License-Identifier: Apache-2.0
"""The checks of the rule references that the config makes, and of the rulesets.

Each check is a `Check` of `wio.config.checks`, and like those of
`wio.config.pipelines` it judges the best-effort `Config` as it stands and never
raises for a problem of the config. A reference is judged as text, and its
ruleset part against the directories of `.agents/wio/rules` that the port
`CheckInputs.files` shows below `CheckInputs.root`: `is_dir` of the rules
directory before `list_dir` of it, `is_dir` of each entry, and `exists` of its
`ruleset.toml`, and nothing else; no check reads a file's content. A ruleset is
known by its directory name or by its alias (A-1). Whether the family, code or
rule preset after the dot exists needs the rule files, which the rules Work
reads. Every `where` is a key path built with `join_path` and `item_path`, except
that a directory is at `.agents/wio/rules/<name>`, as written; a message words
its names with `and_list` and its lists with `declared` of
`wio.config.messages`, which says that none is declared when a list is empty.
The checks are appended to `wio.config.CHECKS`.
"""

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

from wio.config.messages import and_list, declared, item_path, join_path
from wio.config.pipelines import find_cycles
from wio.models.diagnostics import Diagnostic

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from wio.config.checks import CheckInputs
    from wio.models.config import Config


@dataclass(frozen=True)
class Bare:
    """A reference without a dot, which names a rule preset of the config.

    Attributes:
        name: The rule preset's name, a lowercase letter, then lowercase
            letters, digits, `-` and `_`.
    """

    name: str


@dataclass(frozen=True)
class Qualified:
    """A reference with exactly one dot, which names an item of a ruleset.

    Attributes:
        ruleset: The ruleset's name or alias, in the form of a ruleset name.
        item: A family (upper-case letters), a code (a family and digits) or a
            rule preset, in the form of a rule preset name.
    """

    ruleset: str
    item: str


@dataclass(frozen=True)
class Malformed:
    """A reference of the wrong form.

    Attributes:
        message: The sentence that says which part is wrong and the form that
            part should have, as `judge_reference` returns it.
    """

    message: str


type Reference = Bare | Qualified | Malformed
"""What a reference is, judged from its text alone."""


class Takes(Enum):
    """The kinds of reference that a field takes."""

    ROOT = auto()
    """A root's `rule_presets`: rule presets of a ruleset and of the config."""

    VETO = auto()
    """`rules_always_exclude`: qualified codes and families only."""

    ANY = auto()
    """The other fields: families, codes and rule presets, qualified or bare."""


@dataclass(frozen=True)
class Rulesets:
    """The ruleset directories under `.agents/wio/rules`.

    Attributes:
        names: The names of the entries that are directories, sorted; empty
            when `.agents/wio/rules` is not a directory.
        without_manifest: The names, sorted, of those with no `ruleset.toml`.
    """

    names: tuple[str, ...]
    without_manifest: tuple[str, ...]


_RULES = ".agents/wio/rules"
_NAME = re.compile(r"[a-z][a-z0-9_-]*")
_FAMILY = re.compile(r"[A-Z]+")
_CODE = re.compile(r"[A-Z]+[0-9]+")
_NAME_FORM = "a lowercase letter, then lowercase letters, digits, `-` and `_`"
_VETO = "only qualified codes and families are allowed in `rules_always_exclude`"


def read_rulesets(inputs: CheckInputs) -> Rulesets:
    """Read which ruleset directories there are.

    Args:
        inputs: The repository root and the port whose `is_dir`, `list_dir` and
            `exists` show the directory.

    Returns:
        The directories; the port's `list_dir` is called only when
        `.agents/wio/rules` is a directory, so a repository without one gives
        none and no error.
    """
    files = inputs.files
    rules = inputs.root / _RULES
    if not files.is_dir(rules):
        return Rulesets((), ())
    names = tuple(sorted(p.name for p in files.list_dir(rules) if files.is_dir(p)))
    bare = tuple(n for n in names if not files.exists(rules / n / "ruleset.toml"))
    return Rulesets(names, bare)


def parse_reference(text: str) -> Reference:
    """Judge the form of a reference from its text.

    Args:
        text: The reference as the config writes it.

    Returns:
        `Bare` for a name without a dot in the form of a rule preset name, and
        `Qualified` for `<ruleset>.<item>` whose parts have their forms. Any
        other text is `Malformed`, with the sentence that says which part is wrong
        and the form it should have: the whole text of a bare name, more than one
        dot, the ruleset part, or the item.
    """
    if "." not in text:
        if _NAME.fullmatch(text):
            return Bare(text)
        message = f"`{text}` is not a rule preset name; a bare name is a rule preset"
        return Malformed(f"{message} of the config, {_NAME_FORM}.")
    if text.count(".") > 1:
        message = "has more than one dot; a reference is a bare name or"
        return Malformed(f"`{text}` {message} `<ruleset>.<item>`.")
    ruleset, item = text.split(".")
    if not _NAME.fullmatch(ruleset):
        message = f"the ruleset part `{ruleset}` of `{text}` is not a ruleset name; "
        return Malformed(f"{message}a ruleset name is {_NAME_FORM}.")
    if _item_kind(item) is None:
        message = f"the item `{item}` of `{text}` is not a family (upper-case "
        return Malformed(
            f"{message}letters), a code (a family and digits) or a rule preset "
            f"({_NAME_FORM})."
        )
    return Qualified(ruleset, item)


def judge_reference(
    text: str, takes: Takes, known: Sequence[str], presets: Sequence[str]
) -> str | None:
    """Judge a reference in a field, and say what is wrong with it, once.

    Args:
        text: The reference as the config writes it.
        takes: The kinds of reference the field takes.
        known: The names and aliases of the rulesets, sorted.
        presets: The names of the config's rule presets, sorted.

    Returns:
        `None` when it is valid, otherwise the first problem of this order: the
        message of a `Malformed` reference; a kind that the field does not take; a
        ruleset part that is not in `known`; a bare name that is not in `presets`.
        An item after the dot is never looked up.
    """
    match parse_reference(text):
        case Malformed(message):
            return message
        case Bare(name):
            return _judge_bare(name, takes, presets)
        case Qualified(ruleset, item):
            return _judge_qualified(text, ruleset, item, takes, known)
        case _:
            return None


def check_rule_references(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check every reference the config makes to a ruleset or a rule preset.

    Args:
        config: The settings, whose references are read.
        inputs: The repository root and the port that shows the ruleset
            directories.

    Returns:
        At most one error for each entry, from `judge_reference`, at its key path.
        A root takes `Takes.ROOT`, `rules_always_exclude` takes `Takes.VETO`, and
        every other field takes `Takes.ANY`. The names known are those of
        `_known_names`: the directories whose names have the form of a ruleset
        name and the valid aliases of their `[rulesets]` tables.
    """
    known = _known_names(config, read_rulesets(inputs))
    presets = sorted(config.rule_presets)
    for where, text, takes in _references(config):
        problem = judge_reference(text, takes, known, presets)
        if problem is not None:
            yield Diagnostic("error", where, problem)


def check_rule_preset_cycles(
    config: Config, inputs: CheckInputs
) -> Iterable[Diagnostic]:
    """Check that the rule presets of the config do not form a cycle.

    Args:
        config: The settings, whose rule presets are read.
        inputs: Unused; the check reads no file.

    Returns:
        One error for each group of rule presets that include one another,
        directly or through others, a self loop included, at
        `rule_presets.<first>.rules_include` where `<first>` is the least name,
        naming every preset of the group in sorted order, not as a path. Only a
        bare name in `rules_include` that is a rule preset of the config is an
        edge.
    """
    del inputs
    graph = {
        name: [ref for ref in preset.rules_include if ref in config.rule_presets]
        for name, preset in config.rule_presets.items()
    }
    for group in find_cycles(graph):
        where = join_path(join_path("rule_presets", group[0]), "rules_include")
        yield Diagnostic("error", where, _cycle_message(group))


def check_rulesets(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check the ruleset directories and the `[rulesets]` table together.

    Args:
        config: The settings, whose `rulesets` table is read.
        inputs: The repository root and the port that shows the ruleset
            directories.

    Returns:
        An error at `.agents/wio/rules/<name>` for a directory whose name is not a
        ruleset name and one for a directory without a `ruleset.toml`, both when
        both apply; an error at `rulesets.<name>` for a table with no directory;
        and, for an alias, one error at `rulesets.<name>.alias`: not a ruleset
        name in form, the alias of an earlier table, or the name of another
        ruleset, directory or table. The name of a table is not judged for form.
    """
    rulesets = read_rulesets(inputs)
    for name in rulesets.names:
        if not _NAME.fullmatch(name):
            message = f"`{name}` is not a ruleset name; a ruleset name is {_NAME_FORM}."
            yield Diagnostic("error", f"{_RULES}/{name}", message)
    for name in rulesets.without_manifest:
        message = f"`{name}` has no `ruleset.toml`; its rules would be skipped."
        yield Diagnostic("error", f"{_RULES}/{name}", message)
    yield from _table_faults(config, rulesets)


def check_always_include_note(
    config: Config, inputs: CheckInputs
) -> Iterable[Diagnostic]:
    """Tell a driver what every session receives.

    Args:
        config: The settings, whose `rules_always_include` is read.
        inputs: Unused; the check reads no file.

    Returns:
        When `rules_always_include` is not empty, one note at it that says every
        session receives the entries and lists them, in the order written; none
        otherwise.
    """
    del inputs
    if config.rules_always_include:
        listed = and_list([f"`{entry}`" for entry in config.rules_always_include])
        message = f"every session receives the rules {listed}."
        yield Diagnostic("note", "rules_always_include", message)


def _known_names(config: Config, rulesets: Rulesets) -> list[str]:
    """List the names and aliases that a reference may use for a ruleset.

    Args:
        config: The settings, whose `rulesets` table is read.
        rulesets: The directories.

    Returns:
        The sorted directory names in the form of a ruleset name, and the valid
        alias of each `[rulesets.<name>]` table whose name is a directory.
    """
    names = [name for name in rulesets.names if _NAME.fullmatch(name)]
    aliases = [
        table.alias
        for name, table in config.rulesets.items()
        if name in rulesets.names and table.alias and _NAME.fullmatch(table.alias)
    ]
    return sorted({*names, *aliases})


def _cycle_message(group: Sequence[str]) -> str:
    """Word the error of a group of rule presets that include one another.

    Args:
        group: The names of the presets, sorted.

    Returns:
        The sentence, in the singular for a preset that includes itself.
    """
    names = and_list([f"`{name}`" for name in group])
    verb = "include one another" if len(group) > 1 else "includes itself"
    return f"{names} {verb}; a cycle has no resolved set."


def _item_kind(item: str) -> str | None:
    """Tell what kind of name the part after the dot is.

    Args:
        item: The part of a qualified reference after the dot.

    Returns:
        `family`, `code` or `rule preset`, or `None` when it has no such form.
    """
    if _FAMILY.fullmatch(item):
        return "family"
    if _CODE.fullmatch(item):
        return "code"
    return "rule preset" if _NAME.fullmatch(item) else None


def _judge_bare(name: str, takes: Takes, presets: Sequence[str]) -> str | None:
    """Judge a bare name in a field.

    Args:
        name: The rule preset's name.
        takes: The kinds of reference the field takes.
        presets: The names of the config's rule presets, sorted.

    Returns:
        The problem, or `None`.
    """
    if takes is Takes.VETO:
        return f"`{name}` is a rule preset; {_VETO}."
    if name in presets:
        return None
    listed = declared("Declared rule presets", "No rule presets are declared.", presets)
    return f"unknown rule preset `{name}`. {listed}"


def _judge_qualified(
    text: str, ruleset: str, item: str, takes: Takes, known: Sequence[str]
) -> str | None:
    """Judge a qualified reference in a field.

    Args:
        text: The reference as written.
        ruleset: Its ruleset part.
        item: Its item part.
        takes: The kinds of reference the field takes.
        known: The names and aliases of the rulesets, sorted.

    Returns:
        The problem, or `None`.
    """
    kind = _item_kind(item)
    if takes is Takes.ROOT and kind != "rule preset":
        return f"a root takes rule presets only; `{text}` is a {kind}."
    if takes is Takes.VETO and kind == "rule preset":
        return f"`{text}` is a rule preset; {_VETO}."
    if ruleset in known:
        return None
    listed = declared(
        "Declared rulesets and aliases", "No rulesets are declared.", known
    )
    return f"unknown ruleset `{ruleset}`. {listed}"


def _entries(
    where: str, entries: Sequence[str], takes: Takes
) -> Iterable[tuple[str, str, Takes]]:
    """Pair each entry of a list with its key path and what its field takes.

    Args:
        where: The key path of the list.
        entries: The references.
        takes: The kinds of reference the field takes.

    Returns:
        A key path, a reference and the kinds, for each entry.
    """
    for index, text in enumerate(entries):
        yield item_path(where, index), text, takes


def _selection(
    where: str, include: Sequence[str], exclude: Sequence[str]
) -> Iterable[tuple[str, str, Takes]]:
    """Pair the entries of a table's `rules_include` and `rules_exclude`.

    Args:
        where: The key path of the table.
        include: Its `rules_include`.
        exclude: Its `rules_exclude`.

    Returns:
        A key path, a reference and `Takes.ANY`, for each entry.
    """
    yield from _entries(join_path(where, "rules_include"), include, Takes.ANY)
    yield from _entries(join_path(where, "rules_exclude"), exclude, Takes.ANY)


def _references(config: Config) -> Iterable[tuple[str, str, Takes]]:
    """Find every reference of the config, with its key path and field.

    Args:
        config: The settings.

    Returns:
        A key path, a reference and the kinds its field takes, for each entry of
        the stages, the config's rule presets, the roots and the two always
        fields.
    """
    for name, stage in config.stages.items():
        where = join_path("stages", name)
        yield from _selection(where, stage.rules_include, stage.rules_exclude)
    for name, preset in config.rule_presets.items():
        where = join_path("rule_presets", name)
        yield from _selection(where, preset.rules_include, preset.rules_exclude)
    for name, root in config.roots.items():
        where = join_path(join_path("roots", name), "rule_presets")
        yield from _entries(where, root.rule_presets, Takes.ROOT)
    yield from _entries("rules_always_include", config.rules_always_include, Takes.ANY)
    yield from _entries("rules_always_exclude", config.rules_always_exclude, Takes.VETO)


def _table_faults(config: Config, rulesets: Rulesets) -> Iterable[Diagnostic]:
    """Judge the `[rulesets]` table against the directories.

    Args:
        config: The settings, whose `rulesets` table is read.
        rulesets: The directories.

    Returns:
        An error for a table without a directory, and one for an alias that is
        not valid.
    """
    names = {*rulesets.names, *config.rulesets}
    taken: dict[str, str] = {}
    for name, table in config.rulesets.items():
        where = join_path("rulesets", name)
        if name not in rulesets.names:
            message = f"`{name}` has no directory under `{_RULES}`."
            yield Diagnostic("error", where, message)
        alias = table.alias
        if alias is None:
            continue
        fault = _alias_fault(name, alias, taken, names)
        taken.setdefault(alias, name)
        if fault is not None:
            yield Diagnostic("error", join_path(where, "alias"), fault)


def _alias_fault(
    name: str, alias: str, taken: dict[str, str], names: set[str]
) -> str | None:
    """Judge the alias of one ruleset.

    Args:
        name: The ruleset's name.
        alias: Its alias.
        taken: Each alias of an earlier table mapped to that table's name.
        names: Every ruleset name, directory or table.

    Returns:
        The first problem: not a ruleset name in form, the alias of an earlier
        table, or the name of another ruleset; `None` when there is none.
    """
    head = f"alias `{alias}` of `{name}`"
    if not _NAME.fullmatch(alias):
        return f"{head} is not a ruleset name; a ruleset name is {_NAME_FORM}."
    if alias in taken:
        return f"{head} is also the alias of `{taken[alias]}`."
    if alias != name and alias in names:
        return f"{head} is also the name of a ruleset."
    return None
