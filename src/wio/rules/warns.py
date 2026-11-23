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
    """Find the warnings of the rule files, the entries and the rule bodies.

    It returns the warnings of the discovery as they are, and not its errors, and
    then three kinds of its own, each reported once. The config is valid, so
    every reference in it is well-formed and names a ruleset; what needs the rule
    files is which rulesets an entry names and which roots reach them.

    A reach warning is one for each ruleset that an entry of a stage's
    `rules_include` or of `rules_always_include` names, nested rule presets
    included, when the ruleset is not root-independent and none of the roots that
    the entry counts reaches it. It is placed at the entry's key path and says
    which ruleset it is, that it is not root-independent and that none of the
    roots reaches it, and that the fix is to mark it `root_independent` or to name
    it in a root's `rule_presets`. A root reaches the rulesets that the include
    entries of its rule presets name, which `apply_layers` gives for no roots and
    no stage; a ruleset that the config's `rulesets` table does not list is not
    root-independent. A stage counts the roots of its own
    `roots`, with `@work`, which is not known here, standing for every root of the
    config, so a stage with no `roots`, a stage with `@work` and the entries of
    `rules_always_include` count a ruleset as reached when any root reaches it,
    and `roots = []` counts none. An exclude, an entry of a root's `rule_presets`
    and a ruleset that the discovery left out are not judged.

    A veto warning is one for each entry of `rules_always_include` whose rules an
    entry of `rules_always_exclude` also delivers. It is placed at the include
    entry, names the exclude entries, each in backticks as written, and the rules
    with their qualified codes and names in the order of C-2 of `wio rules`, says
    that the veto wins and that one of the two entries should go.

    A heading warning is one for each rule whose body has a real Markdown
    heading, as `read_outline` finds it, at the file and the line of the first
    heading, naming the rule with its name and the heading as written, whichever
    form the rule's metadata block has.

    It does no input or output, and the result is in the order of
    `sort_diagnostics` whatever the order of the tables and of the entries.

    Args:
        config: The settings, whose roots, stages, rule presets, rulesets and
            always fields are read.
        discovery: What `discover` returned: the rulesets that were read and the
            faults found while reading them.

    Returns:
        The warnings, each at the key or the file that the author has to edit.
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
    """Warn about the entries whose rulesets no counted root reaches.

    Args:
        config: The settings, whose stages, always includes and rulesets are read.
        catalog: What the entries are resolved in.
        reach: The rulesets that each root reaches, as `apply_layers` gives them.

    Returns:
        A warning for each ruleset that an entry names and that is neither
        root-independent nor reached by a root that the entry counts.
    """
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
    """Find the rulesets that the roots of a stage reach.

    Args:
        roots: The stage's `roots`, or `None` when it sets none.
        reach: The rulesets that each root reaches.
        every: The rulesets that any root reaches.

    Returns:
        All of `every` for a stage with no `roots` or with `@work` among them,
        which stand for any root of the config, and otherwise what the roots that
        the stage names reach, nothing for `[]`.
    """
    if roots is None or "@work" in roots:
        return every
    return frozenset().union(*(reach.get(name, frozenset()) for name in roots))


def _unreached(
    where: str, entries: Sequence[str], reached: frozenset[str], catalog: RuleCatalog
) -> Iterator[Diagnostic]:
    """Warn about the rulesets of some entries that nothing reaches.

    Args:
        where: The key path of the list.
        entries: The references, as written.
        reached: The canonical names of the rulesets that count as reached,
            root-independent ones included.
        catalog: What the entries are resolved in.

    Returns:
        A warning at `<where>[<index>]` for each ruleset that the entry names,
        nested rule presets included, and that is not in `reached`.
    """
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
    """Warn about the always includes that the always excludes veto.

    Args:
        config: The settings, whose always fields are read.
        catalog: What the entries are resolved in.

    Returns:
        A warning at each include entry whose rules an exclude entry also names.
    """
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
    """Find the exclude entries that take rules of an include entry.

    Args:
        delivered: The rules that the include entry delivers.
        vetoes: Each exclude entry with the rules it delivers.

    Returns:
        Each exclude entry that shares a rule with the include entry, with the
        rules it shares, in the order of the exclude entries.
    """
    common = [(entry, delivered & rules) for entry, rules in vetoes]
    return [(entry, shared) for entry, shared in common if shared]


def _vetoed(hit: Sequence[tuple[str, set[Rule]]]) -> str:
    """Word the warning of an always include that is vetoed.

    Args:
        hit: Each exclude entry with the rules it shares with the include entry.

    Returns:
        The message, which names the exclude entries and the rules in the order
        of C-2 of `wio rules`, and says that the veto wins.
    """
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
    """Warn about the rules whose body has a real Markdown heading.

    Args:
        rulesets: The rulesets that were read.

    Returns:
        A warning at the file and the line of the first heading of each such
        rule.
    """
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
