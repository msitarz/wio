# SPDX-License-Identifier: Apache-2.0
"""Read effective `Wio-*` records from git history, dropping reverted commits."""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.formats.records import read

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from wio.io.ports import History
    from wio.models.commits import Commit
    from wio.models.config import Reader
    from wio.models.records import Record

_REVERT_LINE = re.compile(r"^This reverts commit ([0-9a-fA-F]{4,40})\.$", re.MULTILINE)


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
    commits = tuple(reversed(history.first_parents("HEAD")))
    if not commits:
        return ()
    active = _active_commits(commits)
    return tuple(
        record for commit in active for record in _commit_records(commit, reader)
    )


def _active_commits(commits: Sequence[Commit]) -> tuple[Commit, ...]:
    """Filter out commits reverted by a later commit, honoring revert-of-revert.

    Walks newest-to-oldest so that a reverted revert commit does not apply its
    own revert, restoring the original commit.

    Args:
        commits: First-parent commits in oldest-to-newest order.

    Returns:
        The subset of commits whose changes remain active, in oldest-to-newest
        order.
    """
    known_ids = tuple(commit.id for commit in commits)
    reverted: set[str] = set()
    active: list[Commit] = []
    for commit in reversed(commits):
        if commit.id in reverted:
            continue
        active.append(commit)
        reverted.update(_reverted_targets(commit.message, known_ids))
    return tuple(reversed(active))


def _reverted_targets(message: str, known_ids: Sequence[str]) -> Iterator[str]:
    """Yield resolved commit ids reverted by standard revert lines in `message`.

    Args:
        message: Full commit message text.
        known_ids: Full commit ids present in the walked history.

    Yields:
        Full commit ids matched uniquely in `known_ids`.
    """
    for match in _REVERT_LINE.finditer(message):
        target = _resolve_sha(match.group(1).lower(), known_ids)
        if target is not None:
            yield target


def _resolve_sha(prefix: str, known_ids: Sequence[str]) -> str | None:
    """Resolve a full or prefix SHA against known commit ids in walked history.

    Args:
        prefix: Lowercased hexadecimal SHA or prefix.
        known_ids: Full commit ids present in the walked history.

    Returns:
        The matching full commit id, or `None` when absent or ambiguous.
    """
    matches = [cid for cid in known_ids if cid.startswith(prefix)]
    return matches[0] if len(matches) == 1 else None


def _commit_records(commit: Commit, reader: Reader) -> tuple[EffectiveRecord, ...]:
    """Parse valid non-`none` `Wio-*` records from one commit message.

    Args:
        commit: The commit whose message is parsed.
        reader: Configured `trailers.reader` (`"scan"` or `"git"`).

    Returns:
        Effective records from `commit` in message order.
    """
    reading = read(commit.message, reader)
    return tuple(
        effective
        for record in reading.records
        for effective in _parse_record(commit.id, record)
    )


def _unique_fields(record: Record) -> dict[str, str] | None:
    """Collect trailer key-value pairs, returning `None` if any key repeats.

    Args:
        record: Parsed record from `wio.formats.records.read`.

    Returns:
        Mapping of trailer key to value, or `None` on duplicate keys.
    """
    fields: dict[str, str] = {}
    for trailer in record.trailers:
        if trailer.key in fields:
            return None
        fields[trailer.key] = trailer.value
    return fields


def _parse_works(raw: str | None) -> tuple[str, ...] | None:
    """Split a `Wio-Work` value into Work ids, or `None` if absent/none/invalid.

    Args:
        raw: Value of the `Wio-Work` trailer, if present.

    Returns:
        Non-empty tuple of Work ids, or `None` when skipped or malformed.
    """
    if not raw or raw == "none":
        return None
    works = tuple(raw.split(", "))
    if any(not wid or wid == "none" for wid in works):
        return None
    return works


def _parse_record(commit_id: str, record: Record) -> Iterator[EffectiveRecord]:
    """Convert one parsed `Record` into zero or more `EffectiveRecord` items.

    Skips malformed records (repeated keys, missing required keys, `Wio-Judge`
    without `Wio-Result`, invalid `Wio-Work` list) and `Wio-Work: none`.

    Args:
        commit_id: Full commit SHA carrying `record`.
        record: Parsed record from `wio.formats.records.read`.

    Yields:
        One `EffectiveRecord` per Work id in `Wio-Work`.
    """
    fields = _unique_fields(record)
    if fields is None:
        return
    works = _parse_works(fields.get("Wio-Work"))
    action = fields.get("Wio-Action")
    stage = fields.get("Wio-Stage")
    result = fields.get("Wio-Result")
    judge = fields.get("Wio-Judge")
    if works is None or not action or not stage:
        return
    if judge is not None and result is None:
        return
    for work_id in works:
        yield EffectiveRecord(commit_id, work_id, action, stage, result, judge)
