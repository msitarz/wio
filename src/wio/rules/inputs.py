# SPDX-License-Identifier: Apache-2.0
"""The inputs that every consumer of the selection builds in the same way.

The expansion, the layers, the rules selected anywhere, the checks and the
commands all need the rulesets by canonical name, the aliases and the config's
rule presets, and every output that says where a rule came from needs the same
chain of labels. Each is written here once, so that no two consumers can differ.
This module reads no file.
"""

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Mapping

    from wio.models.config import Config
    from wio.models.rule import LoadedRuleset
    from wio.models.rules import Route
    from wio.rules.discovery import Discovery
    from wio.rules.expansion import RuleCatalog

type Layer = Literal["root", "stage", "always-include", "always-exclude"]
"""The four layers that select rules, in the order they apply."""


def ruleset_map(discovery: Discovery) -> Mapping[str, LoadedRuleset]:
    """Key the rulesets of a discovery by their canonical names.

    Args:
        discovery: What `discover` returned.

    Returns:
        A frozen mapping with one entry for each ruleset of the discovery, keyed
        by the name of its directory, in the order of ruleset name that C-2 of
        `wio rules` gives, whatever the order of the discovery.
    """
    raise NotImplementedError


def build_rule_catalog(
    config: Config, rulesets: Mapping[str, LoadedRuleset]
) -> RuleCatalog:
    """Build the catalog that `expand` resolves its references in.

    The config is valid, so no two rulesets share an alias and no alias is the
    name of another ruleset.

    Args:
        config: The settings, whose `rulesets` table gives the aliases and whose
            `rule_presets` the rule presets.
        rulesets: The rulesets by canonical name, as `ruleset_map` gives them.

    Returns:
        A frozen catalog with the rulesets as given and in their order, the
        alias of each ruleset of the config that has one, mapped to that
        ruleset's name, even for a ruleset whose files were not read, and the
        config's rule presets.
    """
    del rulesets
    msg = f"build_rule_catalog of {len(config.rulesets)} rulesets is declared"
    raise NotImplementedError(msg)


def resolve_ruleset(name: str, catalog: RuleCatalog) -> str | None:
    """Resolve the name or the alias of a ruleset.

    Args:
        name: A ruleset's name or alias, as written.
        catalog: The rulesets and the aliases.

    Returns:
        The canonical name of the ruleset that `name` names, a name before an
        alias, or `None` when no ruleset of the catalog has it, including an
        alias of a ruleset whose files were not read. A command turns `None` into
        a refusal that names what was written.
    """
    msg = f"resolve_ruleset of {name} is declared"
    del catalog
    raise NotImplementedError(msg)


def layer_label(layer: Layer, name: str | None) -> str:
    """Write the label of a layer.

    Args:
        layer: Which layer.
        name: The name of the root or of the stage, which those two layers need;
            the two always layers take no name and ignore one.

    Returns:
        `root <name>`, `stage <name>`, `rules_always_include` or
        `rules_always_exclude`.
    """
    del layer, name
    raise NotImplementedError("layer_label is declared")  # noqa: EM101


def chain_labels(label: str | None, route: Route) -> tuple[str, ...]:
    """Write the chain of labels that says where a rule came from.

    Args:
        label: The label of the layer, or `None` for a listing of references,
            which has no layer.
        route: The route of the rule, as `expand` returns it.

    Returns:
        The label when there is one, followed by the elements of the route; the
        array that the JSON output carries.
    """
    msg = f"chain_labels of {label} is declared"
    del route
    raise NotImplementedError(msg)


def chain_text(code: str, labels: tuple[str, ...]) -> str:
    """Write the text of a chain for a `from:`, `by:` or `selected:` line.

    Args:
        code: The rule's qualified code.
        labels: The chain of labels.

    Returns:
        The code and the labels joined by ` ← `.
    """
    msg = f"chain_text of {code} is declared"
    del labels
    raise NotImplementedError(msg)
