# SPDX-License-Identifier: Apache-2.0
"""The one place that builds a `frozendict`.

The checker's stub of `frozendict` rejects a call with a mapping, so the only
suppression of that error lives here, as `docs/known-issues.md` says.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


def freeze[K, V](mapping: Mapping[K, V]) -> frozendict[K, V]:
    """Freeze a mapping.

    Args:
        mapping: The mapping to copy.

    Returns:
        An immutable `frozendict` with the same items, hashable when its keys
        and values are.
    """
    # See docs/known-issues.md: pyrefly's stub of `frozendict` takes no mapping.
    return frozendict(mapping)  # pyrefly: ignore[bad-argument-count]
