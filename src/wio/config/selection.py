# SPDX-License-Identifier: Apache-2.0
"""The checks of the rule references that the config makes, and of the rulesets.

Every function is a `Check` of `wio.config.checks`, and like those of
`wio.config.pipelines` it judges the best-effort `Config` as it stands and never
raises for a problem of the config. A reference is judged as text, and its
ruleset part against the directories of `.agents/wio/rules` that the port
`CheckInputs.files` shows below `CheckInputs.root`: `is_dir` of the rules
directory before `list_dir` of it, `is_dir` of each entry, and `exists` of its
`ruleset.toml`, and nothing else; no check reads a file's content. A ruleset is
known by its directory name or by its alias (A-1). Whether the family, code or
rule preset after the dot exists needs the rule files, which the rules Work
reads. Every `where` is a key path built with `join_path` and `item_path`, except
that a directory is at `.agents/wio/rules/<name>`, as written; a config that
selects rules names rulesets that exist, so a fixture or a test whose config
selects a ruleset holds its directory with a `ruleset.toml`; a message words
its names and lists with `quoted` and `and_list` of `wio.config.messages`, and
says that none is declared when a list would be empty. The checks are appended
to `wio.config.CHECKS`.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from wio.config.checks import CheckInputs
    from wio.models.config import Config
    from wio.models.diagnostics import Diagnostic


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
    del inputs
    return Rulesets((), ())


def parse_reference(text: str) -> Reference:
    """Judge the form of a reference from its text.

    Args:
        text: The reference as the config writes it.

    Returns:
        `Bare` for a name without a dot in the form of a rule preset name, and
        `Qualified` for `<ruleset>.<item>` whose parts have their forms. Any
        other text is `Malformed`, with the first of these sentences that
        applies: "`<text>` is not a rule preset name; a bare name is a rule
        preset of the config, a lowercase letter, then lowercase letters, digits,
        `-` and `_`."; "`<text>` has more than one dot; a reference is a bare
        name or `<ruleset>.<item>`."; "the ruleset part `<part>` of `<text>` is
        not a ruleset name; a ruleset name is a lowercase letter, then lowercase
        letters, digits, `-` and `_`."; and "the item `<part>` of `<text>` is not
        a family (upper-case letters), a code (a family and digits) or a rule
        preset (a lowercase letter, then lowercase letters, digits, `-` and
        `_`)."
    """
    del text
    return Malformed("")


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
        message of a `Malformed` reference; for `Takes.ROOT` a qualified item that
        is not a rule preset, saying "a root takes rule presets only"; for
        `Takes.VETO` a bare name or a qualified rule preset, saying "only
        qualified codes and families are allowed in `rules_always_exclude`"; a
        ruleset part that is not in `known`, saying "unknown ruleset `<part>`"
        and "Declared rulesets and aliases: `a`, `b`." or "No rulesets are
        declared."; a bare name that is not in `presets`, saying "unknown rule
        preset `<name>`" and "Declared rule presets: `a`, `b`." or "No rule
        presets are declared." An item after the dot is never looked up.
    """
    del text, takes, known, presets
    return None


# The leaves are stubs of one shape until the implementation stage, so the
# duplicate detector skips them, and the markers go with the stubs.
# jscpd:ignore-start  # noqa: ERA001
def check_rule_references(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check every reference the config makes to a ruleset or a rule preset.

    Args:
        config: The settings, whose references are read.
        inputs: The repository root and the port that shows the ruleset
            directories.

    Returns:
        At most one error for each entry, from `judge_reference`, at its key
        path: `stages.<name>.rules_include[<i>]` and `rules_exclude[<i>]`,
        `rule_presets.<name>.rules_include[<i>]` and `rules_exclude[<i>]`,
        `roots.<name>.rule_presets[<i>]`, `rules_always_include[<i>]` and
        `rules_always_exclude[<i>]`. A root takes `Takes.ROOT`,
        `rules_always_exclude` takes `Takes.VETO`, and every other field takes
        `Takes.ANY`. The names known are every directory name, one without a
        `ruleset.toml` included, and the alias, in the form of a ruleset name, of
        each `[rulesets.<name>]` table whose name is a directory; with no rules
        directory a qualified reference is an unknown ruleset, and a config with
        none gets no diagnostic.
    """
    del config, inputs
    return ()


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
        that names every preset of the group in sorted order, not as a path; the
        groups come from `find_cycles` of `wio.config.pipelines`. Only a bare name in
        a preset's `rules_include` that is a rule preset of the config is an edge;
        `rules_exclude` and qualified references are not.
    """
    del config, inputs
    return ()


def check_rulesets(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check the ruleset directories and the `[rulesets]` table together.

    Args:
        config: The settings, whose `rulesets` table is read.
        inputs: The repository root and the port that shows the ruleset
            directories.

    Returns:
        An error at `.agents/wio/rules/<name>`, as written, for a directory whose
        name is not a ruleset name, naming the form of one, and one for a
        directory without a `ruleset.toml`; both when both apply. An error at
        `rulesets.<name>` for a table that has no directory. For an alias, an
        error at `rulesets.<name>.alias` when it is not a ruleset name in form,
        when an earlier ruleset in the table has it, naming that ruleset, and
        when it is the name of another ruleset, a directory or a table, naming
        it; the first that applies, so an alias gets one error, and an alias equal
        to its own ruleset's name is not a clash. The name of a table is not
        judged for its form. Each message names the ruleset and what is wrong.
    """
    del config, inputs
    return ()


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
    del config, inputs
    return ()


# jscpd:ignore-end  # noqa: ERA001
