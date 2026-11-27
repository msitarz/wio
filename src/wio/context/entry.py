# SPDX-License-Identifier: Apache-2.0
"""Recording the `context` event for a delivered bundle."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wio.models.bundle import CompiledBundle
    from wio.ports import EventSink


def record_entry(
    work_id: str,
    action: str,
    stage: str,
    bundle: CompiledBundle,
    events: EventSink,
) -> None:
    """Record one `context` event for a delivered bundle.

    Builds a `ContextEvent` with the Work, action, stage, bundle id, body size,
    and included rule hashes in bundle order, with `start` and `dirty` omitted
    (`None`), and writes it to `events`. Any recording failure is handled by
    the sink as a warning and never raised.

    Args:
        work_id: The id of the Work entering the stage.
        action: The action being run.
        stage: The stage being entered.
        bundle: The delivered bundle whose metadata and rule hashes are
            recorded.
        events: The event sink to write the `context` event to.
    """
    raise NotImplementedError
