# SPDX-License-Identifier: Apache-2.0
"""The type for a rule as selected for a stage.

The stub is the spec until the Work that implements `wio rule` replaces it with
a `.py` of the same annotations. It declares no fields: the rule metadata is
that Work's to settle.
"""

class Rule:
    """One atomic do-or-don't instruction, identified by its code.

    A rule is selected by root, type and tags, and shown in a bundle with its
    code, its name and its body exactly as written.
    """
