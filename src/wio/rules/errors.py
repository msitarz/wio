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
    """Collect errors from rule discovery, reference resolution, and manifests.

    Pure check (no I/O). Combines discovery errors with unresolved config and
    manifest references, manifest preset cycles, reserved `all` preset names,
    and roots reaching root-independent rulesets.

    Returns:
        Errors sorted by `sort_diagnostics`, placed at the config key path or
        `<manifest>#<key-path>` where each problem is written.
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
    """List the entries of one list with their key paths."""
    path = join_path(where, key) if where else key
    for index, text in enumerate(texts):
        yield _Entry(item_path(path, index), text, scope)


def _config_entries(config: Config) -> Iterator[_Entry]:
    """List the references of every field of the config that takes them."""
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
    """List the references of the rule presets of every manifest."""
    for ruleset in rulesets:
        manifest = f"{ruleset.path}/ruleset.toml"
        scope = RulesetScope(ruleset.name)
        for name, preset in ruleset.manifest.rule_presets.items():
            where = f"{manifest}#{join_path('rule_presets', name)}"
            yield from _preset_entries(where, preset, scope)


def _preset_entries(where: str, preset: RulePreset, scope: Scope) -> Iterator[_Entry]:
    """List the includes and the excludes of one rule preset of a manifest."""
    for key, texts in (
        ("rules_include", preset.rules_include),
        ("rules_exclude", preset.rules_exclude),
    ):
        for entry in _listed("", key, texts, scope):
            yield _Entry(f"{where}.{entry.where}", entry.text, scope)


def _judge(entry: _Entry, catalog: RuleCatalog) -> Diagnostic | None:
    """Judge one entry where it is written and by itself."""
    found = expand([entry.text], [], entry.scope, catalog)
    own = [p for p in found.problems if not p.route and p.kind != "cycle"]
    if not own:
        return None
    return Diagnostic("error", entry.where, _reason(own[0], entry, catalog))


def _reason(problem: Problem, entry: _Entry, catalog: RuleCatalog) -> str:
    """Say why an entry cannot be expanded and what would do."""
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
    """List what exists next to an item that names nothing."""
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
    """Report each cycle of the rule presets of a manifest once."""
    for ruleset in rulesets:
        presets = {n: p for n, p in ruleset.manifest.rule_presets.items() if n != "all"}
        for cycle in rule_preset_cycles(presets):
            yield _cycle_error(ruleset, presets[cycle[0]], cycle)


def _cycle_error(
    ruleset: LoadedRuleset, first: RulePreset, cycle: Sequence[str]
) -> Diagnostic:
    """Word the error of one cycle."""
    where = f"{ruleset.path}/ruleset.toml#{join_path('rule_presets', cycle[0])}"
    return Diagnostic(
        "error", join_path(where, cycle_key(first, cycle)), cycle_message(cycle)
    )


_RESERVED = "`all` is reserved for the whole ruleset; name the rule preset otherwise."


def _reserved_errors(rulesets: Sequence[LoadedRuleset]) -> Iterator[Diagnostic]:
    """Report a rule preset called `all` in a manifest."""
    for ruleset in rulesets:
        if "all" in ruleset.manifest.rule_presets:
            where = f"{ruleset.path}/ruleset.toml#{join_path('rule_presets', 'all')}"
            yield Diagnostic("error", where, _RESERVED)


def _reach_errors(config: Config, catalog: RuleCatalog) -> Iterator[Diagnostic]:
    """Report a root that reaches a root-independent ruleset."""
    apart = {n for n, ruleset in config.rulesets.items() if ruleset.root_independent}
    for name, root in config.roots.items():
        yield from _root_reach(name, root.rule_presets, apart, catalog)


def _root_reach(
    root: str, entries: Sequence[str], apart: set[str], catalog: RuleCatalog
) -> Iterator[Diagnostic]:
    """Report the entries of one root that reach a root-independent ruleset."""
    where = join_path(join_path("roots", root), "rule_presets")
    for index, text in enumerate(entries):
        reached = expand([text], [], ConfigScope(), catalog).rulesets & apart
        if reached:
            message = _reached(root, text, sorted(reached), catalog)
            yield Diagnostic("error", item_path(where, index), message)


def _reached(root: str, text: str, names: Sequence[str], catalog: RuleCatalog) -> str:
    """Word the error of a root that reaches root-independent rulesets."""
    through = f" through the rule preset `{text}`" if text in catalog.presets else ""
    listed = and_list([f"`{name}`" for name in names])
    return (
        f"The root `{root}` reaches {listed}{through}, which "
        f"{'is' if len(names) == 1 else 'are'} root-independent and "
        f"{'applies' if len(names) == 1 else 'apply'} to every root; a stage "
        "includes it, not a root."
    )
