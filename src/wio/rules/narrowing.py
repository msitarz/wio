# SPDX-License-Identifier: Apache-2.0
"""Narrowing a listing to the rules that references name or that nothing selects."""

from dataclasses import replace
from typing import TYPE_CHECKING

from wio.errors import WioError
lazy from wio.models.listing import Listing
lazy from wio.rules.errors import explain_problem
lazy from wio.rules.expansion import ConfigScope, RulesetScope, expand
lazy from wio.rules.inputs import build_rule_catalog
lazy from wio.rules.layers import apply_layers

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from wio.models.config import Config
    from wio.models.listing import Row
    from wio.models.rule import LoadedRuleset, Rule
    from wio.models.rules import Route
    from wio.rules.anywhere import SelectedAnywhere
    from wio.rules.expansion import Problem, RuleCatalog


def narrow(
    listing: Listing,
    references: Sequence[str],
    *,
    not_selected: bool,
    config: Config,
    rulesets: Mapping[str, LoadedRuleset],
    anywhere: SelectedAnywhere,
) -> Listing:
    """Keep the rows of a listing that references name, or that nothing selects.

    With references, a row is kept when any reference delivers its rule, as
    `expand` returns it in the config's scope, and the row's `via` holds the
    routes by which the references delivered it. With `not_selected`, a row is
    kept when no include entry of the config delivers its rule, among the rules
    that the roots of the listing can reach and the root-independent ones, or
    among every rule when the listing applies no roots; together with references,
    it keeps the rules that they deliver and no entry does. The rows stay in the
    order of the listing, the header's references and mark are set from the
    arguments, replacing any that the listing held, and a listing that keeps
    nothing is no error. It does no input or output, and the result does not
    depend on the order of the references, except in the header, or of the
    tables of the config and the rulesets.

    Args:
        listing: The listing of a view, with every rule it considers.
        references: The references as written, in the scope of the config.
        not_selected: Whether to keep only the rules that no entry delivers.
        config: The settings, whose rulesets and roots are read.
        rulesets: The rulesets by name, as `ruleset_map` gives them.
        anywhere: The rules that some include entry delivers, which the caller
            computes once for the repository.

    Returns:
        The narrowed listing.

    Raises:
        WioError: A reference names nothing, is not in the form of a reference,
            closes a cycle or reaches an entry that cannot be expanded. It names
            the reference and says why, and no listing is returned.
    """
    rows = listing.rows
    if references:
        catalog = build_rule_catalog(config, rulesets)
        rows = _kept_by(rows, _delivered(references, catalog))
    if not_selected:
        reached = _candidates(listing.header.roots, config, rulesets)
        rows = tuple(
            row
            for row in rows
            if row.rule.ruleset in reached and row.rule not in anywhere.selected
        )
    header = replace(
        listing.header, references=tuple(references), not_selected=not_selected
    )
    return Listing(header, rows)


def _kept_by(
    rows: tuple[Row, ...], routes: Mapping[Rule, tuple[Route, ...]]
) -> tuple[Row, ...]:
    """Keep the rows whose rule was delivered, with the routes that delivered it."""
    return tuple(
        replace(row, via=routes[row.rule]) for row in rows if row.rule in routes
    )


def _delivered(
    references: Sequence[str], catalog: RuleCatalog
) -> dict[Rule, tuple[Route, ...]]:
    """Expand the references and join the rules they deliver."""
    found: dict[Rule, set[Route]] = {}
    for reference in references:
        expansion = expand([reference], [], ConfigScope(), catalog)
        if expansion.problems:
            raise WioError(_refusal(reference, expansion.problems[0], catalog))
        for rule, routes in expansion.rules.items():
            found.setdefault(rule, set()).update(routes)
    return {rule: tuple(sorted(routes)) for rule, routes in found.items()}


def _refusal(reference: str, problem: Problem, catalog: RuleCatalog) -> str:
    """Say why a reference is refused."""
    where = problem.route
    if problem.kind == "cycle":
        return f"`{reference}` closes a cycle: {' -> '.join(where)}."
    if not where:
        return explain_problem(problem, reference, ConfigScope(), catalog)
    scope = RulesetScope(where[-1].partition(".")[0])
    why = explain_problem(problem, problem.reference, scope, catalog)
    return f"`{reference}` reaches the rule preset `{where[-1]}`, where {why}"


def _candidates(
    roots: tuple[str, ...] | None,
    config: Config,
    rulesets: Mapping[str, LoadedRuleset],
) -> frozenset[str]:
    """Find the rulesets whose rules `--not-selected` considers."""
    if roots is None:
        return frozenset(rulesets)
    reach = apply_layers(None, None, config, rulesets).reach
    apart = {n for n, ruleset in config.rulesets.items() if ruleset.root_independent}
    return frozenset(apart.union(*(reach.get(root, frozenset()) for root in roots)))
