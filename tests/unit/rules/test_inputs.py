# SPDX-License-Identifier: Apache-2.0
"""Tests of the inputs that every consumer of the selection builds alike."""

from pathlib import PurePosixPath
from typing import TYPE_CHECKING

import pytest

from wio.models.config import Config, RulePreset, Ruleset
from wio.models.frozen import freeze
from wio.models.rule import LoadedRuleset, Manifest
from wio.rules import (
    Discovery,
    build_rule_catalog,
    chain_labels,
    chain_text,
    layer_label,
    resolve_ruleset,
    ruleset_map,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

_STUB = pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="stub")
_ROUTE = ("demo.recommended", "demo.ARC")


def _ruleset(name: str) -> LoadedRuleset:
    """Build an empty ruleset.

    Args:
        name: Its name.

    Returns:
        The ruleset, with a manifest that declares nothing and no rule.
    """
    path = PurePosixPath(f".agents/wio/rules/{name}")
    return LoadedRuleset(name, path, Manifest(), ())


def _discovery(*names: str) -> Discovery:
    """Build a discovery of empty rulesets in the order given.

    Args:
        *names: The names of the rulesets.

    Returns:
        The discovery, with no diagnostic.
    """
    return Discovery(tuple(_ruleset(name) for name in names), ())


def _config(*tables: tuple[str, str | None], order: Sequence[str] = ()) -> Config:
    """Build a config with rulesets and a rule preset `backend`.

    Args:
        *tables: A ruleset name and its alias, if it has one.
        order: The order of the config's rule presets, `backend` and `extra`.

    Returns:
        The config.
    """
    presets = {"backend": RulePreset(("demo.ARC",), ()), "extra": RulePreset()}
    ordered = {name: presets[name] for name in (order or presets)}
    return Config(
        rulesets=freeze({name: Ruleset(alias=alias) for name, alias in tables}),
        rule_presets=freeze(ordered),
    )


@_STUB
def test_the_rulesets_are_keyed_by_canonical_name_in_order() -> None:
    """AC-1: `demo` before `web`, whatever the order of the discovery."""
    # Given a discovery that holds `web` and then `demo`
    discovery = _discovery("web", "demo")

    # When the rulesets are keyed
    found = ruleset_map(discovery)

    # Then the keys are `demo` and `web` in that order, each with its ruleset
    assert list(found) == ["demo", "web"]
    assert found["demo"].name == "demo"
    assert found["web"].name == "web"


@_STUB
def test_the_catalog_carries_the_aliases_and_the_rule_presets_of_the_config() -> None:
    """AC-2: the rulesets as given, an alias for each that has one, the presets."""
    # Given a config with `demo` aliased `d`, `web` without an alias and a rule
    # preset, and the discovery of both
    config = _config(("demo", "d"), ("web", None))
    rulesets = ruleset_map(_discovery("demo", "web"))

    # When the catalog is built
    catalog = build_rule_catalog(config, rulesets)

    # Then it has the rulesets, the alias of `demo` only, and the config's presets
    assert dict(catalog.rulesets) == dict(rulesets)
    assert dict(catalog.aliases) == {"d": "demo"}
    assert list(catalog.presets) == ["backend", "extra"]


@_STUB
def test_a_ruleset_that_the_discovery_lacks_is_not_in_the_catalog() -> None:
    """AC-3: its alias is still held."""
    # Given the config of AC-2 and a discovery that returns only `demo`
    config = _config(("demo", "d"), ("web", None))
    rulesets = ruleset_map(_discovery("demo"))

    # When the catalog is built
    catalog = build_rule_catalog(config, rulesets)

    # Then only `demo` is among the rulesets, and the alias `d` is still there
    assert list(catalog.rulesets) == ["demo"]
    assert dict(catalog.aliases) == {"d": "demo"}


@_STUB
@pytest.mark.parametrize(
    ("written", "canonical"), [("demo", "demo"), ("d", "demo"), ("nope", None)]
)
def test_a_name_or_an_alias_is_resolved_to_the_canonical_name(
    written: str, canonical: str | None
) -> None:
    """AC-4: a name, an alias, and anything else."""
    # Given the catalog of AC-2
    config = _config(("demo", "d"), ("web", None))
    catalog = build_rule_catalog(config, ruleset_map(_discovery("demo", "web")))

    # When the name is resolved
    found = resolve_ruleset(written, catalog)

    # Then a name and an alias give `demo`, and any other text gives none
    assert found == canonical


@_STUB
def test_the_labels_and_the_chain_are_the_text_that_the_outputs_print() -> None:
    """AC-5: each layer, the chain of the first, and its text."""
    # Given the four layers and a route
    # When each label, the chain and its text are written
    labels = [
        layer_label("root", "api"),
        layer_label("stage", "s"),
        layer_label("always-include", None),
        layer_label("always-exclude", None),
    ]
    chain = chain_labels(labels[0], _ROUTE)
    text = chain_text("demo.ARC001", chain)

    # Then they are the forms of `--explain` and `new`
    assert labels == [
        "root api",
        "stage s",
        "rules_always_include",
        "rules_always_exclude",
    ]
    assert chain == ("root api", "demo.recommended", "demo.ARC")
    assert text == "demo.ARC001 ← root api ← demo.recommended ← demo.ARC"


@_STUB
def test_a_chain_of_references_has_no_layer_label() -> None:
    """AC-6: the route alone, joined with the code."""
    # Given a route and no layer
    # When the chain and its text are written with no label
    chain = chain_labels(None, _ROUTE)
    text = chain_text("demo.ARC001", chain)

    # Then the chain is the route and the text joins it with the code
    assert chain == _ROUTE
    assert text == "demo.ARC001 ← demo.recommended ← demo.ARC"


@_STUB
def test_the_inputs_do_not_depend_on_the_order_of_the_config_or_the_discovery() -> None:
    """AC-7: the same results for the same inputs declared in two orders."""
    # Given the config and the discovery of AC-2 declared in two orders
    first = (
        _config(("demo", "d"), ("web", None)),
        _discovery("demo", "web"),
    )
    second = (
        _config(("web", None), ("demo", "d"), order=("extra", "backend")),
        _discovery("web", "demo"),
    )

    # When the map and the catalog are built from each
    maps = [ruleset_map(discovery) for _, discovery in (first, second)]
    catalogs = [
        build_rule_catalog(config, found)
        for (config, _), found in zip((first, second), maps, strict=True)
    ]

    # Then the keyed rulesets are in the same order and the catalogs are equal
    assert [list(found) for found in maps] == [["demo", "web"], ["demo", "web"]]
    assert catalogs[0].rulesets == catalogs[1].rulesets
    assert catalogs[0].aliases == catalogs[1].aliases
    assert dict(catalogs[0].presets) == dict(catalogs[1].presets)
