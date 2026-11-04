# SPDX-License-Identifier: Apache-2.0
"""The types for a rule and for the selection of rules for a stage.

The stubs are the spec until the Work that implements `wio rules` replaces them
with a `.py` of the same annotations. They declare no fields: the rule
metadata is that Work's to settle.
"""

from collections.abc import Mapping

class Rule:
    """One atomic do-or-don't instruction, identified by its qualified code.

    A rule is selected by name: by the rule presets of the roots a stage
    selects, by the stage, and by the config's always fields. It applies when
    its ruleset is root-independent or reached by one of those roots, and is
    shown in a bundle with its qualified code, its name and its body exactly as
    written.
    """

class Decision:
    """Whether one rule applies to a Work at a stage, and why.

    For an included rule it holds the roots the rule applies to, which group
    the rules in a bundle, and the layers that selected it; for an excluded
    one, the reason it was left out (excluded by a layer, vetoed by
    `rules_always_exclude`, or cut by roots), which `wio rules list --explain`
    shows.
    """

type Selection = Mapping[Rule, Decision]
"""Every rule considered for a stage, in a fixed order, with its decision."""
