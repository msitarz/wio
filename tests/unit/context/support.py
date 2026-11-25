# SPDX-License-Identifier: Apache-2.0
"""The decisions that the tests of the rules section share."""

from typing import TYPE_CHECKING

from wio.models.rules import Decision, Reason

if TYPE_CHECKING:
    from wio.models.rules import ReasonKind


def applies(*roots: str) -> Decision:
    """Decide that a rule applies to roots.

    Args:
        *roots: The roots, none for a root-independent rule.

    Returns:
        The decision.
    """
    return Decision(
        included=True,
        roots=roots,
        root_independent=not roots,
        effects=(),
        reason=None,
    )


def left_out(kind: ReasonKind, *, root_independent: bool = False) -> Decision:
    """Decide that a rule does not apply.

    Args:
        kind: Why it is out.
        root_independent: The setting of its ruleset.

    Returns:
        The decision.
    """
    return Decision(
        included=False,
        roots=(),
        root_independent=root_independent,
        effects=(),
        reason=Reason(kind, "stage" if kind == "excluded" else None),
    )
