# SPDX-License-Identifier: Apache-2.0
"""Read effective `Wio-*` records from git history, dropping reverted commits."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wio.io.ports import History
    from wio.models.config import Reader


@dataclass(frozen=True)
class EffectiveRecord:
    """One effective `Wio-*` record from a non-reverted commit.

    It is immutable.

    Attributes:
        commit: The full 40-character hexadecimal SHA of the commit carrying
            the record.
        work: The 6-character Work id (never `"none"`).
        action: The action name recorded on the commit.
        stage: The stage name recorded on the commit.
        result: The gate result when present, or `None`.
        judge: The gate judge (`"human"` or `"agent"`) when present, or `None`.
    """

    commit: str
    work: str
    action: str
    stage: str
    result: str | None
    judge: str | None


def read_effective_records(
    history: History,
    reader: Reader,
) -> tuple[EffectiveRecord, ...]:
    """Read effective `Wio-*` records from first-parent history, oldest first.

    Walks `history.first_parents("HEAD")`, drops commits whose changes were
    reverted by a later `This reverts commit <sha>.` commit (restoring them if
    a subsequent revert reverts the revert commit), parses each remaining
    commit's `Wio-*` records using `reader`, and skips commits without records,
    malformed records, and `Wio-Work: none`. When a single record lists
    multiple comma-separated Work ids, emits one `EffectiveRecord` per id in
    the listed order.

    Args:
        history: Read-only git history port.
        reader: Configured `trailers.reader` (`"scan"` or `"git"`).

    Returns:
        Effective records in oldest-to-newest commit order, preserving
        in-commit record order, or `()` when history is empty.
    """
    raise NotImplementedError
