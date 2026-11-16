# SPDX-License-Identifier: Apache-2.0
"""How the commands that read the tree refuse what they cannot trust."""

from typing import TYPE_CHECKING, NoReturn

from wio.contracts.errors import ContractsError
lazy from wio.formats import render_text

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.contracts.discovery import WorkDiscovery
    from wio.models.diagnostics import Diagnostic

HINT = "`wio contracts check` shows every problem."
"""The line that a refusal ends with, so a person knows where to see them all."""


def refuse(errors: Sequence[Diagnostic]) -> NoReturn:
    """Refuse with some errors of discovery and the hint.

    Args:
        errors: The errors to carry, in the order to write them.

    Raises:
        ContractsError: Always. It carries the errors, and its message is each
            rendered as `error: <where>: <message>` on a line of its own, then
            `HINT`.
    """
    message = f"{render_text(errors, keep_order=True)}\n{HINT}"
    raise ContractsError(message, list(errors))


def refuse_tree(discovery: WorkDiscovery, *, shared: bool) -> None:
    """Refuse a tree that may not hold every Work.

    Args:
        discovery: What one walk of the Works directory found.
        shared: Whether a shared id also refuses the tree. A command that looks
            one Work up passes false, so that only the lookup of a shared id is
            refused.

    Raises:
        ContractsError: `incomplete`, or with `shared` also `ambiguous`, holds an
            error. It carries those errors in the order of `diagnostics`.
    """
    left = {*discovery.incomplete, *(discovery.ambiguous if shared else ())}
    refused = [error for error in discovery.diagnostics if error in left]
    if refused:
        refuse(refused)
