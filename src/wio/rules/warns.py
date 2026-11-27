# SPDX-License-Identifier: Apache-2.0
"""The warnings that only the rule files and the config show together.

A selection that no root can reach, a rule that both always fields name and a
heading in a rule's body do nothing wrong at first sight and fail silently: the
rule never reaches a session, or the bundle breaks. This module finds them
without reading a file, so that `wio rules check` can add them to the warnings of
the discovery. The errors are `wio.rules.errors`'s.
"""

from typing import TYPE_CHECKING

from wio.formats.outline import read_outline
from wio.formats.wording import and_list, item_path, join_path, quoted
from wio.models.diagnostics import Diagnostic, sort_diagnostics
from wio.rules.expansion import ConfigScope, expand
from wio.rules.inputs import build_rule_catalog, ruleset_map
from wio.rules.layers import apply_layers

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence

    from wio.models.config import Config
    from wio.models.rule import LoadedRuleset, Rule
    from wio.rules.discovery import Discovery
    from wio.rules.expansion import RuleCatalog


def check_warnings(config: Config, discovery: Discovery) -> tuple[Diagnostic, ...]:
    """Collect warnings from rule discovery, selection reach/veto, and bodies.

    Pure check (no I/O). Combines discovery warnings with:
    - reach warnings when an included ruleset is neither root-independent nor
      reached by any applicable root;
    - veto warnings when `rules_always_exclude` cancels `rules_always_include`;
    - heading warnings when a rule body contains a Markdown heading.

    Returns:
        Warnings sorted by `sort_diagnostics`.
    """
    rulesets = ruleset_map(discovery)
    catalog = build_rule_catalog(config, rulesets)
    reach = apply_layers(None, None, config, rulesets).reach
    found = [
        *(d for d in discovery.diagnostics if d.severity == "warning"),
        *_reach_warnings(config, catalog, reach),
        *_veto_warnings(config, catalog),
        *_heading_warnings(discovery.rulesets),
    ]
    return tuple(dict.fromkeys(sort_diagnostics(found)))


def _reach_warnings(
    config: Config, catalog: RuleCatalog, reach: Mapping[str, frozenset[str]]
) -> Iterator[Diagnostic]:
    """Warn about the entries whose rulesets no counted root reaches."""
    apart = {n for n, ruleset in config.rulesets.items() if ruleset.root_independent}
    every = frozenset().union(*reach.values())
    for name, stage in config.stages.items():
        counted = _counted(stage.roots, reach, every)
        where = join_path(join_path("stages", name), "rules_include")
        yield from _unreached(where, stage.rules_include, counted | apart, catalog)
    where = "rules_always_include"
    yield from _unreached(where, config.rules_always_include, every | apart, catalog)


def _counted(
    roots: Sequence[str] | None,
    reach: Mapping[str, frozenset[str]],
    every: frozenset[str],
) -> frozenset[str]:
    """Find the rulesets that the roots of a stage reach."""
    if roots is None or "@work" in roots:
        return every
    return frozenset().union(*(reach.get(name, frozenset()) for name in roots))


def _unreached(
    where: str, entries: Sequence[str], reached: frozenset[str], catalog: RuleCatalog
) -> Iterator[Diagnostic]:
    """Warn about the rulesets of some entries that nothing reaches."""
    for index, text in enumerate(entries):
        named = expand([text], [], ConfigScope(), catalog).rulesets
        for ruleset in sorted(named - reached):
            yield Diagnostic(
                "warning", item_path(where, index), _UNREACHED.format(ruleset)
            )


_UNREACHED = (
    "`{0}` is not root-independent and none of the roots reaches it, so its rules "
    "never reach a session. Mark it `root_independent` in `[rulesets.{0}]` or name "
    "it in a root's `rule_presets`."
)


def _veto_warnings(config: Config, catalog: RuleCatalog) -> Iterator[Diagnostic]:
    """Warn about the always includes that the always excludes veto."""
    vetoes = [
        (text, set(expand([text], [], ConfigScope(), catalog).rules))
        for text in config.rules_always_exclude
    ]
    for index, text in enumerate(config.rules_always_include):
        delivered = set(expand([text], [], ConfigScope(), catalog).rules)
        if hit := _shared(delivered, vetoes):
            yield Diagnostic(
                "warning", item_path("rules_always_include", index), _vetoed(hit)
            )


def _shared(
    delivered: set[Rule], vetoes: Sequence[tuple[str, set[Rule]]]
) -> list[tuple[str, set[Rule]]]:
    """Find the exclude entries that take rules of an include entry."""
    common = [(entry, delivered & rules) for entry, rules in vetoes]
    return [(entry, shared) for entry, shared in common if shared]


def _vetoed(hit: Sequence[tuple[str, set[Rule]]]) -> str:
    """Word the warning of an always include that is vetoed."""
    rules = sorted(
        {rule for _, common in hit for rule in common},
        key=lambda r: (r.ruleset, r.family, r.number, r.code),
    )
    named = and_list([f"{rule.qualified} {rule.name}" for rule in rules])
    entries = quoted([entry for entry, _ in hit])
    return (
        f"{entries} of `rules_always_exclude` also name {named}; the veto wins, so "
        "remove one of the two entries, as this entry adds nothing for them."
    )


def _heading_warnings(rulesets: Sequence[LoadedRuleset]) -> Iterator[Diagnostic]:
    """Warn about the rules whose body has a real Markdown heading."""
    for ruleset in rulesets:
        for rule in ruleset.rules:
            headings = read_outline(rule.body, rule.body_line)
            if headings:
                where = f"{rule.path}:{headings[0].line}"
                yield Diagnostic("warning", where, _HEADING.format(rule, headings[0]))


_HEADING = (
    "`{0.qualified} {0.name}` has a Markdown heading in its body, `{1.raw}`; a "
    "heading breaks the bundle that holds the rule, so write bold text instead."
)
