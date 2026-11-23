# SPDX-License-Identifier: Apache-2.0
"""The `wio rules` command: creating, checking and listing rules."""

lazy from wio.rules.anywhere import Origin, SelectedAnywhere, selected_anywhere
lazy from wio.rules.applicability import select
lazy from wio.rules.discovery import Discovery, discover, refuse_on_errors
lazy from wio.rules.expansion import (
    ConfigScope,
    Expansion,
    Problem,
    RuleCatalog,
    RulesetScope,
    Scope,
    expand,
)
lazy from wio.rules.inputs import (
    Layer,
    build_rule_catalog,
    chain_labels,
    chain_text,
    layer_label,
    resolve_ruleset,
    ruleset_map,
)
lazy from wio.rules.layers import Layered, RuleLayers, apply_layers
lazy from wio.rules.manifest import ManifestReading, read_manifest
lazy from wio.rules.reading import RULE_NAME, RULE_NAME_FORM, RuleReading, read_rule

__all__ = [
    "RULE_NAME",
    "RULE_NAME_FORM",
    "ConfigScope",
    "Discovery",
    "Expansion",
    "Layer",
    "Layered",
    "ManifestReading",
    "Origin",
    "Problem",
    "RuleCatalog",
    "RuleLayers",
    "RuleReading",
    "RulesetScope",
    "Scope",
    "SelectedAnywhere",
    "apply_layers",
    "build_rule_catalog",
    "chain_labels",
    "chain_text",
    "discover",
    "expand",
    "layer_label",
    "read_manifest",
    "read_rule",
    "refuse_on_errors",
    "resolve_ruleset",
    "ruleset_map",
    "select",
    "selected_anywhere",
]
