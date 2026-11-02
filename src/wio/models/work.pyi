# SPDX-License-Identifier: Apache-2.0
"""The types for a Work as the components pass it around.

These stubs are the spec until the Work that implements a type replaces its
stub with a `.py` of the same annotations. They declare no fields: a field
arrives with the Work that first reads it.
"""

class ResolvedContract:
    """A Work's contract with the inheritable sections of its ancestors.

    It is what a context bundle shows an agent for a Work: the Work's own
    contract plus the sections its ancestors mark as inherited, so the agent
    never reads a parent's whole contract.
    """
