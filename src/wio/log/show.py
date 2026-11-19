# SPDX-License-Identifier: Apache-2.0
"""Read a clone's log and project its history into rows.

The report is shared by the two output forms. It is derived from the events
so that reviews of Works whose contracts have gone remain visible.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.formats.event_lines import Entry, decode_lines
from wio.log.errors import LogError
from wio.log.locate import locate_log, log_files
from wio.models.events import ContextEvent, ReviewEvent
from wio.models.frozen import freeze

if TYPE_CHECKING:
    from collections.abc import Mapping

    from wio.env.ports import Directories
    from wio.io.ports import FileSystem, Repository
    from wio.models.events import Envelope


@dataclass(frozen=True)
class Review:
    """The review retained for a judge and commit in a row.

    Attributes:
        time: The event time in seconds since the epoch.
        event: The retained review and its ordered citations.
    """

    time: float
    event: ReviewEvent


@dataclass(frozen=True)
class Row:
    """The events shown for one action and stage of a Work.

    Attributes:
        action: The action the events name.
        stage: The stage the events name.
        context: The envelope of the latest context event, if one exists.
        reviews: The latest reviews by judge and commit, in event order.
    """

    action: str
    stage: str
    context: Envelope | None
    reviews: tuple[Review, ...]


@dataclass(frozen=True)
class Report:
    """The visible rows and the damage counted across the clone's log.

    Attributes:
        works: The rows by Work id in sorted id order. Rows are ordered by
            their latest event, with ties following file name and line order.
        skipped: The number of unreadable lines across every file and Work.
    """

    works: Mapping[str, tuple[Row, ...]]
    skipped: int


def read_report(
    repository: Repository,
    directories: Directories,
    filesystem: FileSystem,
    work: str | None = None,
) -> Report:
    """Read each log file independently, then select and summarize the events.

    Args:
        repository: Supplies the identity of the clone.
        directories: Supplies the Wio home.
        filesystem: Lists the files and reads their bytes.
        work: The Work id to show, or None for all Works.

    Returns:
        Rows in Work id and latest-event order, and the global skip count.
        An absent log yields an empty report.

    Raises:
        WioError: The clone or Wio home cannot be located, or a log file
            cannot be listed or read.
    """
    try:
        directory = locate_log(repository, directories)
    except (RuntimeError, ValueError, OSError) as error:
        raise LogError(str(error)) from error
    entries: list[Entry] = []
    skipped = 0
    try:
        for path in log_files(directory, filesystem):
            decoded = decode_lines(
                filesystem.read_bytes(path).decode("utf-8", "replace")
            )
            entries.extend(decoded.entries)
            skipped += decoded.skipped
    except OSError as error:
        raise LogError(str(error)) from error
    return Report(_rows(entries, work), skipped)


def _rows(entries: list[Entry], work: str | None) -> Mapping[str, tuple[Row, ...]]:
    """Select and group rows from events in file and line order.

    Args:
        entries: The usable entries of each file, with files ordered by name.
        work: Selects a single Work when supplied.

    Returns:
        The rows by Work id, ordered by each row's latest event.
    """
    groups: dict[str, dict[tuple[str, str], list[Entry]]] = {}
    for entry in sorted(entries, key=lambda entry: entry.envelope.time):
        event = entry.event
        if work is not None and event.work != work:
            continue
        rows = groups.setdefault(event.work, {})
        key = event.action, event.stage
        history = rows.pop(key, [])
        history.append(entry)
        rows[key] = history
    return freeze(
        {
            work_id: tuple(
                _row(key, history) for key, history in groups[work_id].items()
            )
            for work_id in sorted(groups)
        }
    )


def _row(key: tuple[str, str], history: list[Entry]) -> Row:
    """Build a row with the latest context and each judge's latest review.

    Args:
        key: The action and stage of the row.
        history: The events of the row in chronological order with stable ties.

    Returns:
        A row whose retained reviews follow their own positions in the history.
    """
    context: Envelope | None = None
    reviews: dict[tuple[str, str], Review] = {}
    for entry in history:
        match entry.event:
            case ContextEvent():
                context = entry.envelope
            case ReviewEvent() as event:
                review_key = event.judge, event.commit
                reviews.pop(review_key, None)
                reviews[review_key] = Review(entry.envelope.time, event)
    return Row(*key, context, tuple(reviews.values()))
