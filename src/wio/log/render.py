# SPDX-License-Identifier: Apache-2.0
"""Render the selected rows in the two forms of the log command.

Rendering uses the report alone, so it treats live and retired Works alike.
"""

from typing import TYPE_CHECKING

from wio.formats import encode_json
from wio.formats.event_lines import format_event_time

if TYPE_CHECKING:
    from collections.abc import Iterator

    from wio.log.show import Report, Review, Row
    from wio.models.events import Envelope


def render(report: Report, *, as_json: bool) -> str:
    """Render one report in the selected output form.

    The JSON document preserves field order and full commit ids. Text displays
    abbreviated commits and leaves the skip count to a separate diagnostic.

    Args:
        report: Selected rows and the global skip count.
        as_json: Whether to produce a JSON document in place of text.

    Returns:
        A JSON document with a final newline even when no Works are selected.
        The text form has a final newline when it has any rows, and is empty
        otherwise.
    """
    if as_json:
        works = {
            work: [_json_row(row) for row in rows]
            for work, rows in report.works.items()
        }
        return encode_json({"works": works, "skipped": report.skipped}) + "\n"
    return "".join(_text(report))


def _text(report: Report) -> Iterator[str]:
    """Render Work headings followed by the lines belonging to each row."""
    for work, rows in report.works.items():
        yield f"{work}\n"
        for row in rows:
            yield from _text_row(row)


def _text_row(row: Row) -> Iterator[str]:
    """Render the context before the reviews of its action and stage."""
    prefix = f"  {row.action} {row.stage}"
    if row.context is not None:
        time = format_event_time(row.context.time)
        yield f"{prefix}  entered {time}  {_session_text(row.context)}\n"
    for review in row.reviews:
        yield _review_line(prefix, review)


def _review_line(prefix: str, review: Review) -> str:
    """Render a review with an abbreviated commit and citations in source order."""
    event = review.event
    time = format_event_time(review.time)
    line = f"{prefix}  {event.judge} {event.result} {event.commit[:12]}  {time}"
    if event.cited:
        cited = " ".join(f"{key}={value}" for key, value in event.cited.items())
        line += f"  {cited}"
    return line + "\n"


def _session_text(context: Envelope) -> str:
    """Describe the session, including ambiguity and missing fields."""
    if context.harness is None:
        if len(context.matches) >= 2:
            return f"ambiguous ({', '.join(context.matches)})"
        return "unknown session"
    session = "unknown" if context.session is None else encode_json(context.session)
    label = f"{context.harness}:{session}"
    if context.parent is not None:
        return f"{label} (parent {encode_json(context.parent)})"
    return label


def _json_row(row: Row) -> dict[str, object]:
    """Build a JSON row with fields in contract order."""
    context = row.context
    return {
        "action": row.action,
        "stage": row.stage,
        "entered": format_event_time(context.time) if context is not None else None,
        "session": _json_session(context) if context is not None else None,
        "reviews": [_json_review(review) for review in row.reviews],
    }


def _json_session(context: Envelope) -> dict[str, object]:
    """Expose the session details selected by the show contract."""
    return {
        "harness": context.harness,
        "session": context.session,
        "parent": context.parent,
        "matches": context.matches,
    }


def _json_review(review: Review) -> dict[str, object]:
    """Expose the full commit and citations of the retained review."""
    event = review.event
    return {
        "judge": event.judge,
        "result": event.result,
        "commit": event.commit,
        "time": format_event_time(review.time),
        "cited": dict(event.cited),
    }
