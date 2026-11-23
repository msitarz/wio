# SPDX-License-Identifier: Apache-2.0
"""The ports that `wio.rules` consumes besides the shared ones in `wio.ports`.

Provisional: the architecture review may rename them. The component that
satisfies each is wired in by `wio.cli`; `wio.rules` never imports it.
"""

from typing import Protocol

class WorkRoots(Protocol):
    """The roots that a Work's contract names."""

    def roots_of(self, work_id: str) -> tuple[str, ...] | None:
        """Find the roots of a Work.

        The roots are those of the Work's contract with `@descendants` expanded
        through its descendants, each name once and sorted. The Work is looked
        up as the adapter was built, in the working tree or in the index and
        then in `HEAD`. It writes nothing.

        Args:
            work_id: The Work's id.

        Returns:
            The roots, empty for a Work that has none, or `None` when no view
            has such a Work.
        """
        ...
