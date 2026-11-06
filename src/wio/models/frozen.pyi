# SPDX-License-Identifier: Apache-2.0
"""The one place that builds a `frozendict`.

The stub is the spec until the implementation stage replaces it with a `.py`
of the same annotations. The checker's stub of `frozendict` rejects a call with
a mapping, so the only suppression of that error lives in the implementation,
as `docs/known-issues.md` says.
"""

from collections.abc import Mapping

def freeze[K, V](mapping: Mapping[K, V]) -> frozendict[K, V]:
    """Freeze a mapping.

    Args:
        mapping: The mapping to copy.

    Returns:
        An immutable `frozendict` with the same items, hashable when its keys
        and values are.
    """
    ...
