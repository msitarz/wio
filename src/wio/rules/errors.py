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

from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.formats.wording import item_path, join_path
from wio.models.diagnostics import Diagnostic, sort_diagnostics
from wio.rules.expansion import ConfigScope, RulesetScope, expand
from wio.rules.inputs import build_rule_catalog, ruleset_map

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
    cycles of a manifest are found by `find_cycles`. A reference is judged
    against what the discovery returned, so a rule or a ruleset that it left out
    is a reference to nothing. A family that the manifest declares and that holds
    no rule is valid.

    The reason of a failed entry is derived from the entry and the catalog,
    because a `Problem` carries only its kind, reference and route: an unknown
    family lists the families that the ruleset declares, an unknown code the
    codes of its family, an unknown rule preset the rule presets of its manifest
    and a ruleset that was not read says so, with `declared`; an entry that is
    not in the form of a reference says that, and a qualified entry of a
    manifest says that a manifest names only its own items.

    A cycle of the rule presets of a manifest is one error for each cycle, at
    the `rules_include` of the first member by name, or at its `rules_exclude`
    when the edge that leaves it is an exclude, naming every member with
    `and_list`. The edges are the entries of both lists that name a rule preset
    of the manifest, so a cycle that closes through an exclude is reported too.
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
    del problem, entry, catalog
    raise NotImplementedError


def _cycle_errors(rulesets: Sequence[LoadedRuleset]) -> Iterator[Diagnostic]:
    """Report each cycle of the rule presets of a manifest once.

    Args:
        rulesets: The rulesets that were read.

    Returns:
        An error for each cycle, as `check_errors` words it.
    """
    del rulesets
    raise NotImplementedError


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


_RESERVED = "`all` is reserved for the whole ruleset; name the rule preset otherwise."


def _reach_errors(config: Config, catalog: RuleCatalog) -> Iterator[Diagnostic]:
    """Report a root that reaches a root-independent ruleset.

    Args:
        config: The settings, whose roots and rulesets are read.
        catalog: What the entries of the roots are resolved in.

    Returns:
        An error at the entry of each root that reaches one, as `check_errors`
        words it.
    """
    del config, catalog
    raise NotImplementedError
