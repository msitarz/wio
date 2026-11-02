# SPDX-License-Identifier: Apache-2.0
"""The types for a rule and for the selection of rules for a stage.

The stubs are the spec until the Work that implements `wio rule` replaces them
with a `.py` of the same annotations. They declare no fields: the rule
metadata is that Work's to settle.
"""

from collections.abc import Mapping

class Rule:
    """One atomic do-or-don't instruction, identified by its code.

    A rule is selected by root, type and tags, and shown in a bundle with its
    code, its name and its body exactly as written.
    """

class Decision:
    """Whether one rule applies to a Work at a stage, and why.

    For an included rule it holds the roots the rule applies to, which group
    the rules in a bundle; for an excluded one, the reason it was left out,
    which `wio context` can explain.
    """

type Selection = Mapping[Rule, Decision]
"""Every rule considered for a stage, in a fixed order, with its decision."""
