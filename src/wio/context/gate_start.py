# SPDX-License-Identifier: Apache-2.0
"""Reading the starting commit and dirty flag for a gate stage."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wio.context.ports import ReviewedCommit
    from wio.io.ports import Repository


@dataclass(frozen=True)
class GateStart:
    """The review start commit and dirty flag for a gate stage, plus warnings.

    Attributes:
        start: Full commit id where the gate review starts, or `None`.
        dirty: Whether the working tree had uncommitted changes, or `None`.
        warnings: Warnings for any port read that failed with `ValueError` or
            `RuntimeError`.
    """

    start: str | None = None
    dirty: bool | None = None
    warnings: tuple[str, ...] = ()


def read_gate_start(
    action: str,
    stage: str,
    *,
    is_gate: bool,
    reviewed: ReviewedCommit,
    repository: Repository,
) -> GateStart:
    """Read `start` and `dirty` for a gate stage before bundle delivery.

    A non-gate stage performs no reads and returns an empty `GateStart`. For a
    gate stage, `reviewed.find(action, stage)` and `repository.is_dirty()` are
    read independently: a `ValueError` or `RuntimeError` from either drops only
    that field and adds a warning naming `start` or `dirty`. Any other
    exception propagates as a bug.

    Args:
        action: The action being run.
        stage: The stage being entered.
        is_gate: Whether the stage has `gate = true` in the config.
        reviewed: Port that finds the reviewed commit from history.
        repository: Port that reports whether the working tree is dirty.

    Returns:
        The `GateStart` carrying `start`, `dirty`, and any warnings.
    """
    raise NotImplementedError
