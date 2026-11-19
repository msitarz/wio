# SPDX-License-Identifier: Apache-2.0
"""Read a clone's log and project its history into rows.

The report is shared by the two output forms. It is derived from the events
so that reviews of Works whose contracts have gone remain visible.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from wio.env.ports import Directories
    from wio.io.ports import FileSystem, Repository
    from wio.models.events import Envelope, ReviewEvent


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
    raise NotImplementedError
