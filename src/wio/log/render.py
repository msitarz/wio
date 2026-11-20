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
    """Render Work headings followed by the lines belonging to each row.

    Args:
        report: The ordered Works and their rows.

    Yields:
        Each line of the text report, including its terminator.
    """
    for work, rows in report.works.items():
        yield f"{work}\n"
        for row in rows:
            yield from _text_row(row)


def _text_row(row: Row) -> Iterator[str]:
    """Render the context before the reviews of its action and stage.

    Args:
        row: The context and retained reviews, either of which can be absent.

    Yields:
        The entered line when present and one line per review.
    """
    prefix = f"  {row.action} {row.stage}"
    if row.context is not None:
        time = format_event_time(row.context.time)
        yield f"{prefix}  entered {time}  {_session_text(row.context)}\n"
    for review in row.reviews:
        yield _review_line(prefix, review)


def _review_line(prefix: str, review: Review) -> str:
    """Render a review with an abbreviated commit and citations in source order.

    Args:
        prefix: The indented action and stage.
        review: The retained review with its timestamp.

    Returns:
        One review line including its terminator.
    """
    event = review.event
    time = format_event_time(review.time)
    line = f"{prefix}  {event.judge} {event.result} {event.commit[:12]}  {time}"
    if event.cited:
        cited = " ".join(f"{key}={value}" for key, value in event.cited.items())
        line += f"  {cited}"
    return line + "\n"


def _session_text(context: Envelope) -> str:
    """Describe the session, including ambiguity and missing fields.

    Args:
        context: The context event's envelope.

    Returns:
        A harness and session label, an ambiguity label, or an unknown session.
    """
    if context.harness is None:
        if len(context.matches) >= 2:
            return f"ambiguous ({', '.join(context.matches)})"
        return "unknown session"
    if context.session is None:
        return f"{context.harness}:unknown"
    label = f"{context.harness}:{_session_literal(context.session)}"
    if context.parent is not None:
        return f"{label} (parent {_session_literal(context.parent)})"
    return label


def _session_literal(value: str) -> str:
    """Format a present session or parent value for a text report."""
    return value


def _json_row(row: Row) -> dict[str, object]:
    """Build a JSON row with fields in contract order.

    Args:
        row: The report row for an action and stage.

    Returns:
        A JSON-ready mapping with null context fields for a review-only row.
    """
    context = row.context
    return {
        "action": row.action,
        "stage": row.stage,
        "entered": format_event_time(context.time) if context is not None else None,
        "session": _json_session(context) if context is not None else None,
        "reviews": [_json_review(review) for review in row.reviews],
    }


def _json_session(context: Envelope) -> dict[str, object]:
    """Expose the session details selected by the show contract.

    Args:
        context: The envelope of the latest context event.

    Returns:
        The session fields in order, with the matches represented as a sequence.
    """
    return {
        "harness": context.harness,
        "session": context.session,
        "parent": context.parent,
        "matches": context.matches,
    }


def _json_review(review: Review) -> dict[str, object]:
    """Expose the full commit and citations of the retained review.

    Args:
        review: The review event and its timestamp.

    Returns:
        The review fields in order with its cited results left in source order.
    """
    event = review.event
    return {
        "judge": event.judge,
        "result": event.result,
        "commit": event.commit,
        "time": format_event_time(review.time),
        "cited": dict(event.cited),
    }
