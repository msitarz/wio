# SPDX-License-Identifier: Apache-2.0
"""The errors that only the rule files and the config show together.

The discovery judges each rule and manifest on its own, and `wio config check`
judges the references of the config as text. What is left is the faults that
need both: a reference that names nothing in its ruleset, a rule preset that
includes itself through others, a manifest that defines `all`, and a
root-independent ruleset that a root reaches. This module finds them without
reading a file, so that `wio rules check` can add them to the faults of the
discovery.
"""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.formats.cycles import cycle_key, cycle_message, rule_preset_cycles
from wio.formats.grammar import Qualified, item_kind, parse_reference
from wio.formats.wording import and_list, declared, item_path, join_path
from wio.models.diagnostics import Diagnostic, sort_diagnostics
from wio.rules.expansion import ConfigScope, RulesetScope, expand
from wio.rules.inputs import build_rule_catalog, resolve_ruleset, ruleset_map

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from wio.models.config import Config, RulePreset
    from wio.models.rule import LoadedRuleset
    from wio.rules.discovery import Discovery
    from wio.rules.expansion import Problem, RuleCatalog, Scope


def check_errors(config: Config, discovery: Discovery) -> tuple[Diagnostic, ...]:
    """Find the errors of the rule files, the manifests and the references.

    It returns the errors of the discovery as they are, and not its warnings,
    and then the errors of the references. The config is valid, so every
    reference in it is well-formed, and what needs the rule files is whether the
    item after the dot exists. Each entry is judged where it is written and by
    itself with `expand`: an entry of the config in the config scope, and each
    entry of each rule preset of a manifest, include or exclude, in the scope of
    its ruleset. A problem that belongs to a rule preset that the entry reached
    is not the entry's, so it is reported at that rule preset's own key and once,
    however many entries reach it, and a `cycle` problem is dropped because the
    cycles of a manifest are found by `rule_preset_cycles`. A reference is judged
    against what the discovery returned, so a rule or a ruleset that it left out
    is a reference to nothing. A family that the manifest declares and that holds
    no rule is valid.

    The reason of a failed entry is derived from the entry and the catalog,
    because a `Problem` carries only its kind, reference and route: an unknown
    family lists the families that the ruleset declares, an unknown code the
    codes of its family and an unknown rule preset the rule presets of its
    manifest, each worded with `declared`; a ruleset that was not read says so,
    an entry that is not in the form of a reference says that, and a qualified
    entry of a manifest says that a manifest names only its own items.

    A cycle of the rule presets of a manifest is one error for each cycle, at
    the `rules_include` of the first member by name, or at its `rules_exclude`
    when none of its includes names a member, naming every member with
    `and_list`. The edges are the entries of both lists that name a rule preset
    of the manifest, so a cycle that closes through an exclude is reported too,
    and `all`, which is the whole ruleset and never a rule preset, is no edge and
    no node.
    A rule preset called `all` is one error at its key that says `all` is
    reserved for the whole ruleset. A root whose rule presets reach a
    root-independent ruleset, directly or through a rule preset of the config,
    is one error at the entry of the root that reaches it, naming the ruleset,
    the root and, when it is reached through one, the rule preset of the config;
    a stage that includes such a ruleset is not an error.

    It does no input or output, and the result is in the order of
    `sort_diagnostics` whatever the order of the tables of the config, of the
    rulesets and of the entries.

    Args:
        config: The settings, whose roots, stages, rule presets and always
            fields are read.
        discovery: What `discover` returned: the rulesets that were read and the
            faults found while reading them.

    Returns:
        The errors, each at the key where it is written: a key path of the config
        for an entry of the config, and the manifest's path followed by `#` and a
        key path for an entry or a rule preset of a manifest.
    """
    catalog = build_rule_catalog(config, ruleset_map(discovery))
    entries = [*_config_entries(config), *_manifest_entries(discovery.rulesets)]
    found = [
        *(d for d in discovery.diagnostics if d.severity == "error"),
        *filter(None, (_judge(entry, catalog) for entry in entries)),
        *_cycle_errors(discovery.rulesets),
        *_reserved_errors(discovery.rulesets),
        *_reach_errors(config, catalog),
    ]
    return sort_diagnostics(found)


@dataclass(frozen=True)
class _Entry:
    """One reference as it is written, and the place it is written at."""

    where: str
    text: str
    scope: Scope


def _listed(
    where: str, key: str, texts: Sequence[str], scope: Scope
) -> Iterator[_Entry]:
    """List the entries of one list with their key paths.

    Args:
        where: The key path of the table that holds the list.
        key: The name of the list.
        texts: The references, as written.
        scope: What a bare name of them is.

    Returns:
        An entry for each reference, at `<where>.<key>[<index>]`.
    """
    path = join_path(where, key) if where else key
    for index, text in enumerate(texts):
        yield _Entry(item_path(path, index), text, scope)


def _config_entries(config: Config) -> Iterator[_Entry]:
    """List the references of every field of the config that takes them.

    Args:
        config: The settings.

    Returns:
        The rule presets of the roots, the includes and excludes of the stages
        and of the config's rule presets, and the two always fields.
    """
    scope = ConfigScope()
    for name, root in config.roots.items():
        yield from _listed(
            join_path("roots", name), "rule_presets", root.rule_presets, scope
        )
    for name, stage in config.stages.items():
        where = join_path("stages", name)
        yield from _listed(where, "rules_include", stage.rules_include, scope)
        yield from _listed(where, "rules_exclude", stage.rules_exclude, scope)
    for name, preset in config.rule_presets.items():
        where = join_path("rule_presets", name)
        yield from _listed(where, "rules_include", preset.rules_include, scope)
        yield from _listed(where, "rules_exclude", preset.rules_exclude, scope)
    yield from _listed("", "rules_always_include", config.rules_always_include, scope)
    yield from _listed("", "rules_always_exclude", config.rules_always_exclude, scope)


def _manifest_entries(rulesets: Sequence[LoadedRuleset]) -> Iterator[_Entry]:
    """List the references of the rule presets of every manifest.

    Args:
        rulesets: The rulesets that were read.

    Returns:
        An entry for each include and exclude, at the manifest's path followed
        by `#` and the key path, and in the scope of its own ruleset.
    """
    for ruleset in rulesets:
        manifest = f"{ruleset.path}/ruleset.toml"
        scope = RulesetScope(ruleset.name)
        for name, preset in ruleset.manifest.rule_presets.items():
            where = f"{manifest}#{join_path('rule_presets', name)}"
            yield from _preset_entries(where, preset, scope)


def _preset_entries(where: str, preset: RulePreset, scope: Scope) -> Iterator[_Entry]:
    """List the includes and the excludes of one rule preset of a manifest.

    Args:
        where: The manifest's path and the key path of the rule preset.
        preset: The rule preset.
        scope: The scope of its own ruleset.

    Returns:
        An entry for each include and exclude, at `<where>.<key>[<index>]`.
    """
    for key, texts in (
        ("rules_include", preset.rules_include),
        ("rules_exclude", preset.rules_exclude),
    ):
        for entry in _listed("", key, texts, scope):
            yield _Entry(f"{where}.{entry.where}", entry.text, scope)


def _judge(entry: _Entry, catalog: RuleCatalog) -> Diagnostic | None:
    """Judge one entry where it is written and by itself.

    Args:
        entry: The reference and its place.
        catalog: What the reference is resolved in.

    Returns:
        An error when the entry itself cannot be expanded, or `None`. A problem
        with a route belongs to a rule preset that the entry reached and is
        reported at that rule preset's own key, and a cycle is found elsewhere.
    """
    found = expand([entry.text], [], entry.scope, catalog)
    own = [p for p in found.problems if not p.route and p.kind != "cycle"]
    if not own:
        return None
    return Diagnostic("error", entry.where, _reason(own[0], entry, catalog))


def _reason(problem: Problem, entry: _Entry, catalog: RuleCatalog) -> str:
    """Say why an entry cannot be expanded and what would do.

    Args:
        problem: What `expand` found for the entry.
        entry: The reference as written.
        catalog: The rulesets, to list what exists.

    Returns:
        The message, which lists the families, codes or rule presets that exist.
    """
    text = entry.text
    match problem.kind, entry.scope:
        case "malformed", _:
            return f"`{text}` is not a reference."
        case "qualified-in-manifest", _:
            return f"`{text}` is qualified; a manifest names only its own items."
        case _, RulesetScope(own):
            return f"`{text}` names nothing. {_siblings(own, text, catalog)}"
    match parse_reference(text):
        case Qualified(ruleset, item):
            canonical = resolve_ruleset(ruleset, catalog)
            if canonical is None:
                return f"`{ruleset}` is not a ruleset that was read."
            return f"`{text}` names nothing. {_siblings(canonical, item, catalog)}"
    known = declared(
        "Declared rule presets", "None is declared.", sorted(catalog.presets)
    )
    return f"`{text}` names no rule preset of the config. {known}"


def explain_problem(
    problem: Problem, text: str, scope: Scope, catalog: RuleCatalog
) -> str:
    """Say why an entry cannot be expanded and what would do.

    Args:
        problem: What `expand` found for the entry.
        text: The entry as written.
        scope: What a bare name is where the entry was written.
        catalog: The rulesets, to list what exists.

    Returns:
        The message that `wio rules check` gives for the entry, which starts with
        the entry in backticks and lists the families, codes or rule presets that
        exist.
    """
    return _reason(problem, _Entry("", text, scope), catalog)


def _siblings(ruleset: str, item: str, catalog: RuleCatalog) -> str:
    """List what exists next to an item that names nothing.

    Args:
        ruleset: The canonical name of the ruleset.
        item: The family, code or rule preset that was written.
        catalog: The rulesets that were read.

    Returns:
        The families, the codes of the item's family or the rule presets of the
        ruleset's manifest, depending on what the item looks like.
    """
    loaded = catalog.rulesets[ruleset]
    match item_kind(item):
        case "family":
            names = list(loaded.manifest.families)
            return declared("Declared families", "No families are declared.", names)
        case "code":
            family = re.match(r"[A-Z]+", item)
            codes = [r.code for r in loaded.rules_of(family[0] if family else "")]
            return declared(
                f"Codes of `{family[0] if family else ''}`",
                "No rule has that family.",
                codes,
            )
        case _:
            names = sorted(loaded.manifest.rule_presets)
            return declared("Rule presets", "No rule presets are declared.", names)


def _cycle_errors(rulesets: Sequence[LoadedRuleset]) -> Iterator[Diagnostic]:
    """Report each cycle of the rule presets of a manifest once.

    Args:
        rulesets: The rulesets that were read.

    Returns:
        An error for each cycle, at the key of its first member by name.
    """
    for ruleset in rulesets:
        presets = {n: p for n, p in ruleset.manifest.rule_presets.items() if n != "all"}
        for cycle in rule_preset_cycles(presets):
            yield _cycle_error(ruleset, presets[cycle[0]], cycle)


def _cycle_error(
    ruleset: LoadedRuleset, first: RulePreset, cycle: Sequence[str]
) -> Diagnostic:
    """Word the error of one cycle.

    Args:
        ruleset: The ruleset whose manifest has the cycle.
        first: The first member of the cycle by name.
        cycle: The members, sorted.

    Returns:
        The error, at the key that `cycle_key` gives.
    """
    where = f"{ruleset.path}/ruleset.toml#{join_path('rule_presets', cycle[0])}"
    return Diagnostic(
        "error", join_path(where, cycle_key(first, cycle)), cycle_message(cycle)
    )


_RESERVED = "`all` is reserved for the whole ruleset; name the rule preset otherwise."


def _reserved_errors(rulesets: Sequence[LoadedRuleset]) -> Iterator[Diagnostic]:
    """Report a rule preset called `all` in a manifest.

    Args:
        rulesets: The rulesets that were read.

    Returns:
        An error at the key of each such rule preset.
    """
    for ruleset in rulesets:
        if "all" in ruleset.manifest.rule_presets:
            where = f"{ruleset.path}/ruleset.toml#{join_path('rule_presets', 'all')}"
            yield Diagnostic("error", where, _RESERVED)


def _reach_errors(config: Config, catalog: RuleCatalog) -> Iterator[Diagnostic]:
    """Report a root that reaches a root-independent ruleset.

    Args:
        config: The settings, whose roots and rulesets are read.
        catalog: What the entries of the roots are resolved in.

    Returns:
        An error at the entry of each root that reaches one, naming the
        ruleset, the root and the rule preset of the config that the entry names.
    """
    apart = {n for n, ruleset in config.rulesets.items() if ruleset.root_independent}
    for name, root in config.roots.items():
        yield from _root_reach(name, root.rule_presets, apart, catalog)


def _root_reach(
    root: str, entries: Sequence[str], apart: set[str], catalog: RuleCatalog
) -> Iterator[Diagnostic]:
    """Report the entries of one root that reach a root-independent ruleset.

    Args:
        root: The root's name.
        entries: Its rule presets, as written.
        apart: The canonical names of the root-independent rulesets.
        catalog: What the entries are resolved in.

    Returns:
        An error at each entry that reaches one.
    """
    where = join_path(join_path("roots", root), "rule_presets")
    for index, text in enumerate(entries):
        reached = expand([text], [], ConfigScope(), catalog).rulesets & apart
        if reached:
            message = _reached(root, text, sorted(reached), catalog)
            yield Diagnostic("error", item_path(where, index), message)


def _reached(root: str, text: str, names: Sequence[str], catalog: RuleCatalog) -> str:
    """Word the error of a root that reaches root-independent rulesets.

    Args:
        root: The root's name.
        text: The entry of the root, as written.
        names: The root-independent rulesets that it reaches.
        catalog: The rule presets of the config.

    Returns:
        The message, which names the rulesets, the root and, when the entry is a
        rule preset of the config, that rule preset.
    """
    through = f" through the rule preset `{text}`" if text in catalog.presets else ""
    listed = and_list([f"`{name}`" for name in names])
    return (
        f"The root `{root}` reaches {listed}{through}, which "
        f"{'is' if len(names) == 1 else 'are'} root-independent and "
        f"{'applies' if len(names) == 1 else 'apply'} to every root; a stage "
        "includes it, not a root."
    )
