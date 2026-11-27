# SPDX-License-Identifier: Apache-2.0
"""Recording the `context` event for a delivered bundle."""

from typing import TYPE_CHECKING

from wio.models.events import ContextEvent

if TYPE_CHECKING:
    from wio.models.bundle import CompiledBundle
    from wio.ports import EventSink


def record_entry(
    work_id: str,
    action: str,
    stage: str,
    bundle: CompiledBundle,
    events: EventSink,
    *,
    start: str | None = None,
    dirty: bool | None = None,
) -> None:
    """Record one `context` event for a delivered bundle.

    Builds a `ContextEvent` with the Work, action, stage, bundle id, body size,
    included rule hashes in bundle order, and optional gate `start` and `dirty`
    fields, and writes it to `events`. Any recording failure is handled by the
    sink as a warning and never raised.

    Args:
        work_id: The id of the Work entering the stage.
        action: The action being run.
        stage: The stage being entered.
        bundle: The delivered bundle whose metadata and rule hashes are
            recorded.
        events: The event sink to write the `context` event to.
        start: Full commit id where a gate review starts, or `None`.
        dirty: Whether the working tree was dirty for a gate, or `None`.
    """
    events.write(
        ContextEvent(
            work=work_id,
            action=action,
            stage=stage,
            bundle=bundle.id,
            size=bundle.size,
            rules=dict(bundle.rules),
            start=start,
            dirty=dirty,
        )
    )
