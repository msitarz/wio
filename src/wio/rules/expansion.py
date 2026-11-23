# SPDX-License-Identifier: Apache-2.0
"""The expansion of a rule preset, a family or a code into the rules it selects.

It works on values alone: the rulesets, their aliases and the config's rule
presets reach it as a `RuleCatalog`, so it reads no file and the same catalog
and entries always give the same expansion. The four layers and the roots that
apply are built on it elsewhere, and reporting a problem as a diagnostic is for
`wio rules check`.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, cast

from wio.formats.grammar import (
    Bare,
    Malformed,
    Qualified,
    item_kind,
    parse_own_item,
    parse_reference,
)
from wio.models.config import RulePreset
from wio.models.frozen import freeze
lazy from wio.rules.inputs import resolve_ruleset

if TYPE_CHECKING:
    from collections.abc import Generator, Mapping, Sequence

    from wio.models.rule import LoadedRuleset, Rule
    from wio.models.rules import Route, Routes


@dataclass(frozen=True)
class ConfigScope:
    """The scope of the config's entries, where a bare name is a rule preset.

    An item of a ruleset is written `<ruleset>.<item>`, with the ruleset's name
    or alias.
    """


@dataclass(frozen=True)
class RulesetScope:
    """The scope of a manifest's entries, which name the ruleset's own items.

    Attributes:
        name: The canonical name of the ruleset. A bare name is a family, a code
            or a rule preset of that ruleset.
    """

    name: str


type Scope = ConfigScope | RulesetScope


@dataclass(frozen=True)
class RuleCatalog:
    """What the references of an expansion are resolved in.

    Attributes:
        rulesets: The rulesets by canonical name.
        aliases: Each alias mapped to the canonical name it stands for.
        presets: The config's rule presets by name.
    """

    rulesets: Mapping[str, LoadedRuleset] = field(default=frozendict())
    aliases: Mapping[str, str] = field(default=frozendict())
    presets: Mapping[str, RulePreset] = field(default=frozendict())


type ProblemKind = Literal["unknown", "malformed", "qualified-in-manifest", "cycle"]
"""What is wrong with an entry that could not be expanded."""


@dataclass(frozen=True)
class Problem:
    """An entry that could not be expanded.

    Attributes:
        kind: `unknown` for an entry that names nothing, `malformed` for text
            that is not a reference, `qualified-in-manifest` for `<ruleset>.<item>`
            inside a manifest, and `cycle` for a rule preset that includes
            itself.
        reference: The entry as written; for a cycle, the entry that closes it,
            which names the rule preset where the cycle started.
        route: The rule presets it was found in, outermost first, empty for an
            entry of the list that was expanded; for a cycle it ends with the
            rule preset that closes it.
    """

    kind: ProblemKind
    reference: str
    route: Route


@dataclass(frozen=True)
class Expansion:
    """The rules that a list of entries selects, and how.

    It is immutable and hashable: `expand` builds the mappings as `frozendict`s,
    and a caller that builds one does the same. The rules are in the order of
    ruleset name, family, number of the code and text of the code.

    Attributes:
        rules: The rules selected, each with every route that selected it.
        removed: The rules that an exclude took out, each with every route of
            the removal. An exclude removes from the includes of its own list,
            and that of a nested rule preset does not reach outside that preset,
            so a rule is in both `rules` and `removed` when one entry includes
            it and an exclude inside another entry's preset names it.
        rulesets: The canonical names of the rulesets that an include entry
            named, nested rule presets included, even when the excludes leave
            none of their rules; an exclude entry and an entry that names
            nothing name none.
        problems: What could not be expanded, sorted by route, then reference,
            then kind. An entry with a problem selects nothing and the others
            are still expanded.
    """

    rules: Mapping[Rule, Routes]
    removed: Mapping[Rule, Routes]
    rulesets: frozenset[str]
    problems: tuple[Problem, ...]


def expand(
    include: Sequence[str],
    exclude: Sequence[str],
    scope: Scope,
    catalog: RuleCatalog,
) -> Expansion:
    """Expand a list of includes and excludes into the rules it selects.

    The includes are expanded, then the excludes are expanded and removed from
    them. An entry is a family, a code or a rule preset, and a rule preset takes
    its own includes and then removes its own excludes; its entries are read in
    the scope of its own ruleset, or of the config. A ruleset has a rule preset
    `all` that holds all its rules, whatever its manifest says of that name. A
    family that its manifest declares and that holds no rule selects nothing and
    is no problem. The grammar of an entry is that of `wio.formats.grammar`: a
    bare upper-case name is malformed in the config's scope, and
    `parse_own_item` reads the entries of a manifest.

    It does no input or output and raises nothing for an entry or a cycle, and
    the result does not depend on the order of the tables of the catalog or of
    the entries of a list.

    Args:
        include: The references to select, as written.
        exclude: The references to remove from what the includes select.
        scope: What a bare name is.
        catalog: The rulesets, aliases and rule presets to resolve them in.

    Returns:
        The expansion.
    """
    expander = _Expander(catalog)
    result = _run(expander.level(include, exclude, scope, (), (), named=True))
    return Expansion(
        rules=_ordered(result.selected),
        removed=_ordered(result.removed),
        rulesets=frozenset(expander.named),
        problems=tuple(
            sorted(expander.problems, key=lambda p: (p.route, p.reference, p.kind))
        ),
    )


def _ordered(found: dict[Rule, set[Route]]) -> frozendict[Rule, Routes]:
    """Order rules as C-2 of `wio rules` says and sort the routes of each.

    Args:
        found: The routes of each rule.

    Returns:
        The rules by ruleset name, family, number of the code and text of the
        code, each with its routes sorted, as a frozen mapping.
    """
    order = sorted(found, key=lambda r: (r.ruleset, r.family, r.number, r.code))
    return freeze({rule: tuple(sorted(found[rule])) for rule in order})


@dataclass
class _Result:
    """What expanding a list of entries selected and removed, with routes.

    Attributes:
        selected: The routes of each rule that the includes selected and the
            excludes of the list left.
        removed: The routes of each rule that an exclude of the list or of a rule
            preset below it took out.
    """

    selected: dict[Rule, set[Route]] = field(default_factory=dict)
    removed: dict[Rule, set[Route]] = field(default_factory=dict)


def _merge(target: dict[Rule, set[Route]], source: dict[Rule, set[Route]]) -> None:
    """Add the routes of some rules to those of others.

    Args:
        target: Where the routes are added.
        source: The routes to add.
    """
    for rule, routes in source.items():
        target.setdefault(rule, set()).update(routes)


type _Frame = Generator[_Frame, _Result, _Result]
"""One step of an expansion that waits for the steps below it.

It yields the step it needs, receives that step's result, and returns its own.
`_run` drives the steps from a list and not from the call stack, so the depth of
nested rule presets is limited by memory and never by the recursion limit.
"""


def _run(frame: _Frame) -> _Result:
    """Run a step and the steps it waits for, deepest first.

    Args:
        frame: The outermost step.

    Returns:
        What the outermost step returned.
    """
    stack = [frame]
    value: _Result | None = None
    while stack:
        try:
            child = stack[-1].send(cast("_Result", value))
        except StopIteration as done:
            stack.pop()
            value = done.value
        else:
            stack.append(child)
            value = None
    return cast("_Result", value)


class _Expander:
    """One expansion: it resolves entries in a catalog and keeps what it meets."""

    def __init__(self, catalog: RuleCatalog) -> None:
        """Start an expansion.

        Args:
            catalog: What the references are resolved in.
        """
        self.catalog = catalog
        self.problems: set[Problem] = set()
        self.named: set[str] = set()

    def level(
        self,
        include: Sequence[str],
        exclude: Sequence[str],
        scope: Scope,
        prefix: Route,
        path: tuple[tuple[str, str], ...],
        *,
        named: bool,
    ) -> _Frame:
        """Expand one list: the includes, and then the excludes removed from them.

        Args:
            include: The entries to select.
            exclude: The entries to remove from what the includes select.
            scope: What a bare name is.
            prefix: The rule presets this list belongs to, outermost first.
            path: The rule presets being expanded, to find a cycle.
            named: Whether the rulesets that the includes name are recorded.

        Returns:
            The rules selected and removed. An exclude removes only from the
            includes of this list, so what a nested rule preset removed stays in
            `removed` and reaches no further.
        """
        result = _Result()
        for text in include:
            found = yield self.entry(text, scope, prefix, path, named=named)
            _merge(result.selected, found.selected)
            _merge(result.removed, found.removed)
        taken: dict[Rule, set[Route]] = {}
        for text in exclude:
            excluded = yield self.entry(text, scope, prefix, path, named=False)
            _merge(taken, excluded.selected)
        for rule, routes in taken.items():
            if rule in result.selected:
                del result.selected[rule]
                result.removed.setdefault(rule, set()).update(routes)
        return result

    def entry(
        self,
        text: str,
        scope: Scope,
        prefix: Route,
        path: tuple[tuple[str, str], ...],
        *,
        named: bool,
    ) -> _Frame:
        """Expand one entry.

        Args:
            text: The entry as written.
            scope: What a bare name is.
            prefix: The rule presets the entry was found in.
            path: The rule presets being expanded.
            named: Whether the ruleset it names is recorded.

        Returns:
            What it selects and what nested rule presets removed; nothing for an
            entry that is a problem, which is recorded.
        """
        match scope, self._read(text, scope):
            case _, Malformed():
                return self._problem("malformed", text, prefix)
            case RulesetScope(), Qualified():
                return self._problem("qualified-in-manifest", text, prefix)
            case ConfigScope(), Bare(name):
                return (
                    yield self._config_preset(name, text, prefix, path, named=named)
                )
            case RulesetScope(own), Bare(name):
                return (yield self._item(own, name, text, prefix, path, named=named))
            case _, Qualified(ruleset, item):
                canonical = self._canonical(ruleset)
                if canonical is None:
                    return self._problem("unknown", text, prefix)
                step = self._item(canonical, item, text, prefix, path, named=named)
                return (yield step)
        return _Result()

    @staticmethod
    def _read(text: str, scope: Scope) -> Bare | Qualified | Malformed:
        """Read an entry with the grammar of its scope.

        Args:
            text: The entry.
            scope: The config's scope or a manifest's.

        Returns:
            What `parse_reference` or `parse_own_item` says.
        """
        match scope:
            case ConfigScope():
                return parse_reference(text)
            case RulesetScope():
                return parse_own_item(text)

    def _canonical(self, name: str) -> str | None:
        """Resolve a ruleset's name or alias.

        Args:
            name: The name or alias as written.

        Returns:
            The canonical name, or `None` when no ruleset has it. A name wins
            over an alias.
        """
        return resolve_ruleset(name, self.catalog)

    def _problem(self, kind: ProblemKind, text: str, route: Route) -> _Result:
        """Record a problem.

        Args:
            kind: What is wrong.
            text: The entry as written.
            route: The rule presets it was found in.

        Returns:
            An empty result, since the entry selects nothing.
        """
        self.problems.add(Problem(kind, text, route))
        return _Result()

    def _config_preset(
        self,
        name: str,
        text: str,
        prefix: Route,
        path: tuple[tuple[str, str], ...],
        *,
        named: bool,
    ) -> _Frame:
        """Expand a bare name of the config's scope, a rule preset of the config.

        Args:
            name: The rule preset's name.
            text: The entry as written.
            prefix: The rule presets the entry was found in.
            path: The rule presets being expanded.
            named: Whether rulesets are recorded.

        Returns:
            The rule preset's expansion, or nothing with a problem.
        """
        preset = self.catalog.presets.get(name)
        if preset is None:
            return self._problem("unknown", text, prefix)
        step = self._preset(
            ("", name), name, preset, ConfigScope(), text, prefix, path, named=named
        )
        return (yield step)

    def _preset(
        self,
        key: tuple[str, str],
        reference: str,
        preset: RulePreset,
        scope: Scope,
        text: str,
        prefix: Route,
        path: tuple[tuple[str, str], ...],
        *,
        named: bool,
    ) -> _Frame:
        """Expand a rule preset unless it is already being expanded.

        Args:
            key: The ruleset and name that identify the rule preset.
            reference: Its canonical reference, which its route shows.
            preset: Its includes and excludes.
            scope: The scope of its own entries.
            text: The entry that named it, as written.
            prefix: The rule presets the entry was found in.
            path: The rule presets being expanded.
            named: Whether rulesets are recorded.

        Returns:
            Its expansion, or nothing with a `cycle` problem when it includes
            itself.
        """
        route = (*prefix, reference)
        if key in path:
            return self._problem("cycle", text, route)
        step = self.level(
            preset.rules_include,
            preset.rules_exclude,
            scope,
            route,
            (*path, key),
            named=named,
        )
        return (yield step)

    def _item(
        self,
        canonical: str,
        item: str,
        text: str,
        prefix: Route,
        path: tuple[tuple[str, str], ...],
        *,
        named: bool,
    ) -> _Frame:
        """Expand a family, a code or a rule preset of a ruleset.

        Args:
            canonical: The ruleset's canonical name.
            item: What follows the dot, or the bare name of a manifest.
            text: The entry as written.
            prefix: The rule presets the entry was found in.
            path: The rule presets being expanded.
            named: Whether the ruleset is recorded when the item exists.

        Returns:
            The rules it names, or nothing with an `unknown` problem when the
            ruleset, the family, the code or the rule preset does not exist.
        """
        ruleset = self.catalog.rulesets.get(canonical)
        found = None if ruleset is None else self._rules_of(ruleset, item)
        if ruleset is None or found is None:
            return self._problem("unknown", text, prefix)
        if named:
            self.named.add(canonical)
        route = (*prefix, f"{canonical}.{item}")
        if isinstance(found, RulePreset):
            step = self._preset(
                (canonical, item),
                f"{canonical}.{item}",
                found,
                RulesetScope(canonical),
                text,
                prefix,
                path,
                named=named,
            )
            return (yield step)
        return _Result(selected={rule: {route} for rule in found})

    @staticmethod
    def _rules_of(
        ruleset: LoadedRuleset, item: str
    ) -> tuple[Rule, ...] | RulePreset | None:
        """Look an item up in a ruleset.

        Args:
            ruleset: The ruleset.
            item: A family, a code or a rule preset name.

        Returns:
            The rules of a declared family, the rule of a code, all the rules for
            `all`, the manifest's rule preset, or `None` when there is none.
        """
        match item_kind(item):
            case "family":
                declared = item in ruleset.manifest.families
                return ruleset.rules_of(item) if declared else None
            case "code":
                rule = ruleset.get(item)
                return None if rule is None else (rule,)
            case "rule preset" if item == "all":
                return ruleset.rules
            case "rule preset":
                return ruleset.manifest.rule_presets.get(item)
            case _:
                return None
