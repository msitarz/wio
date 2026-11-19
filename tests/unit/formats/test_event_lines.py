# SPDX-License-Identifier: Apache-2.0
"""Contract scenarios for the versioned event log codec."""

import json
import sys
from dataclasses import replace

import pytest

from wio.formats import Decoding, Entry, decode_lines, encode_line
from wio.models.events import ContextEvent, Envelope, ReviewEvent


@pytest.fixture
def envelope() -> Envelope:
    """Supply every common field of an event.

    Returns:
        A recording context with an exact millisecond and ordered matches.
    """
    return Envelope(
        1795000000.123,
        "/work/project",
        "codex",
        "t2",
        "s1",
        ("claude-code", "codex"),
        {"CODEX_THREAD_ID": "t2", "CODEX_SESSION_ID": "s1"},
    )


@pytest.fixture
def review() -> ReviewEvent:
    """Supply a review with citations in nonalphabetical order.

    Returns:
        A failed review with two citations and one rule hash.
    """
    return ReviewEvent(
        "k3m9xq",
        "deliver",
        "implementation-review",
        "a" * 40,
        "agent",
        "fail",
        {"ARC001": "fail", "AC-2": "pass"},
        {"ARC001": "h1"},
    )


@pytest.fixture
def context() -> ContextEvent:
    """Supply a gate context with rules in nonalphabetical order.

    Returns:
        A complete gate context for a clean checkout.
    """
    return ContextEvent(
        "k3m9xq",
        "deliver",
        "architecture-review",
        "bundle-1",
        230,
        {"contracts.CON002": "h2", "contracts.ACC001": "h1"},
        "b" * 40,
        dirty=False,
    )


def test_blank_lines_do_not_create_entries_or_count_as_skips() -> None:
    """AC-4 treats whitespace-only lines as empty log input."""
    # Given LF and CRLF lines with no records.
    text = "\n  \r\n\t\n"

    # When the text is decoded.
    decoded = decode_lines(text)

    # Then there are no entries and no skips.
    assert decoded == Decoding((), 0)


def test_review_round_trip_keeps_all_fields_and_citation_order(
    envelope: Envelope, review: ReviewEvent
) -> None:
    """AC-1 preserves the reviewed commit, decisions and complete envelope."""
    # Given a complete review and envelope at an exact millisecond.

    # When the event is encoded and read back.
    line = encode_line(envelope, review)
    decoded = decode_lines(line)

    # Then the entry equals the input and citation order is unchanged.
    assert decoded == Decoding((Entry(envelope, review),), 0)
    assert json.loads(line)["type"] == "review"
    event = decoded.entries[0].event
    assert isinstance(event, ReviewEvent)
    assert tuple(event.cited) == ("ARC001", "AC-2")


def test_context_round_trip_keeps_optional_gate_fields_and_rule_order(
    envelope: Envelope, context: ContextEvent
) -> None:
    """AC-2 preserves both kinds of context and the order of their rules."""
    # Given a gate context and one for a stage that is not a gate.
    regular = replace(context, stage="architecture", start=None, dirty=None)

    # When both contexts are written and read.
    line = encode_line(envelope, context)
    decoded = decode_lines(line + encode_line(envelope, regular))

    # Then both are restored in order, including false and absent gate fields.
    assert decoded == Decoding((Entry(envelope, context), Entry(envelope, regular)), 0)
    wire = json.loads(line)
    assert wire["type"] == "context"
    assert wire["dirty"] is False
    for entry in decoded.entries:
        assert isinstance(entry.event, ContextEvent)
        assert tuple(entry.event.rules) == ("contracts.CON002", "contracts.ACC001")


def test_event_line_escapes_newlines_and_keeps_required_empty_fields(
    envelope: Envelope, review: ReviewEvent
) -> None:
    """AC-3 writes one physical line and preserves required empty fields."""
    # Given a directory with a newline and Unicode, and explicitly empty fields.
    envelope = replace(envelope, directory="/w/a\nb/日本", harness="")
    review = replace(review, cited={}, hashes={})

    # When the review is written and read.
    line = encode_line(envelope, review)
    decoded = decode_lines(line)

    # Then the line ends in one newline and preserves the empty fields.
    assert line.endswith("\n")
    assert line.count("\n") == 1
    row = json.loads(line)
    assert (row["cited"], row["hashes"], row["harness"]) == ({}, {}, "")
    assert decoded == Decoding((Entry(envelope, review),), 0)


def test_absent_optional_fields_are_omitted_and_restored(
    envelope: Envelope, context: ContextEvent
) -> None:
    """AC-3 omits absent fields and still writes an empty required rules map."""
    # Given no harness details and a regular context with no rules.
    envelope = replace(
        envelope, harness=None, session=None, parent=None, matches=(), ids={}
    )
    context = replace(context, start=None, dirty=None, rules={})

    # When the event is encoded and decoded.
    line = encode_line(envelope, context)
    row = json.loads(line)
    decoded = decode_lines(line)

    # Then the optional fields are absent on the wire and restored on read.
    optional = {"harness", "session", "parent", "matches", "ids", "start", "dirty"}
    assert optional.isdisjoint(row)
    assert row["rules"] == {}
    assert decoded == Decoding((Entry(envelope, context),), 0)


def test_reader_skips_bad_lines_and_keeps_supported_lines_in_order(
    envelope: Envelope, review: ReviewEvent, context: ContextEvent
) -> None:
    """AC-4 keeps reading after ten distinct malformed records."""
    # Given valid records around a blank line and ten invalid records.
    review_line = encode_line(envelope, review)
    context_line = encode_line(envelope, context)
    review_row = json.loads(review_line)
    missing = dict(review_row)
    del missing["result"]
    invalid = (
        '{"v": 1, "type": "re',
        json.dumps(review_row | {"v": 2}),
        json.dumps(review_row | {"type": "other"}),
        json.dumps(missing),
        json.dumps(review_row | {"cited": []}),
        json.dumps(review_row | {"time": "yesterday"}),
        json.dumps(review_row | {"time": "2026-11-18T13:06:40.123+02:00"}),
        json.dumps(review_row | {"hashes": {"ARC001": 1}}),
        json.dumps(json.loads(context_line) | {"size": True}),
        "[1]",
    )
    text = "\n".join((review_line, *invalid, "", context_line.rstrip("\n")))

    # When the mixed input is decoded.
    decoded = decode_lines(text)

    # Then the valid records survive in order and all ten failures are counted.
    assert decoded == Decoding((Entry(envelope, review), Entry(envelope, context)), 10)


def test_reader_ignores_unknown_fields_on_supported_records(
    envelope: Envelope, review: ReviewEvent
) -> None:
    """AC-4 preserves version 1 records that carry additional fields."""
    # Given a supported review with an extra field added by a later writer.
    row = json.loads(encode_line(envelope, review)) | {"later": 1}

    # When the record is read.
    decoded = decode_lines(json.dumps(row))

    # Then the additional field is ignored.
    assert decoded == Decoding((Entry(envelope, review),), 0)


def test_oversized_unknown_integer_does_not_hide_a_supported_record(
    envelope: Envelope, review: ReviewEvent
) -> None:
    """AC-4 ignores future integers without lifting the runtime's digit limit."""
    # Given a version 1 review with a valid oversized JSON integer in a new field.
    row = encode_line(envelope, review).removesuffix("}\n")
    digits = sys.get_int_max_str_digits() or sys.int_info.default_max_str_digits
    extended = row + ', "later": {"large": ' + "9" * (digits + 1) + "}}"

    # When the record is read.
    decoded = decode_lines(extended)

    # Then the current event survives and no line is skipped.
    assert decoded == Decoding((Entry(envelope, review),), 0)


@pytest.mark.parametrize(
    "field",
    [
        {"v": True},
        {"v": 1.0},
        {"matches": ["codex", 2]},
        {"ids": {"CODEX_THREAD_ID": 1}},
        {"harness": None},
        {"time": "2026-11-18 11:06:40.123Z"},
        {"time": "1969-12-31T23:59:59Z"},
        {"time": "2026-02-30T11:06:40.123Z"},
    ],
)
def test_supported_record_requires_the_expected_wire_types_and_time(
    envelope: Envelope, review: ReviewEvent, field: dict[str, object]
) -> None:
    """AC-4 rejects a record whose supplied field has the wrong wire shape."""
    # Given a supported review with one malformed field.
    row = json.loads(encode_line(envelope, review)) | field

    # When it is decoded.
    decoded = decode_lines(json.dumps(row))

    # Then the line is skipped.
    assert decoded == Decoding((), 1)


@pytest.mark.parametrize(
    ("time", "expected", "timestamp"),
    [
        (1795000000.123, 1795000000.123, "2026-11-18T11:06:40.123Z"),
        (1795000000.123956, 1795000000.123, "2026-11-18T11:06:40.123Z"),
        (1795000000.1239998, 1795000000.124, "2026-11-18T11:06:40.124Z"),
    ],
)
def test_timestamp_is_truncated_after_microsecond_rounding(
    envelope: Envelope,
    review: ReviewEvent,
    time: float,
    expected: float,
    timestamp: str,
) -> None:
    """AC-5 writes UTC milliseconds after the stated microsecond rounding."""
    # Given an envelope with the time to encode.
    envelope = replace(envelope, time=time)

    # When the review is encoded and read back.
    line = encode_line(envelope, review)
    decoded = decode_lines(line)

    # Then the wire timestamp and the decoded millisecond agree.
    assert json.loads(line)["time"] == timestamp
    assert decoded == Decoding((Entry(replace(envelope, time=expected), review),), 0)
