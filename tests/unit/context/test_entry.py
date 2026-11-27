# SPDX-License-Identifier: Apache-2.0
"""Tests of recording a stage entry `context` event."""

from tests.unit.context.fakes import EventSinkFake
from wio.context.entry import record_entry
from wio.models.bundle import CompiledBundle
from wio.models.events import ContextEvent


def test_records_one_context_event_with_bundle_metadata_and_rule_order() -> None:
    """AC-1, AC-3: one run records one event with ordered rules and no gate fields."""
    # Given a compiled bundle with two rules in bundle order and an event sink
    bundle = CompiledBundle(
        text="bundle: 7a2383bc4098\n",
        id="7a2383bc4098",
        size=139,
        rules={"mp.ARC001": "hash-1", "mp.ERR002": "hash-2"},
    )
    sink = EventSinkFake()

    # When the stage entry is recorded
    record_entry("k3m9xq", "deliver", "architecture", bundle, sink)

    # Then one ContextEvent is written with matching fields, ordered rules, and no gate
    assert sink.recorded == [
        ContextEvent(
            work="k3m9xq",
            action="deliver",
            stage="architecture",
            bundle="7a2383bc4098",
            size=139,
            rules={"mp.ARC001": "hash-1", "mp.ERR002": "hash-2"},
            start=None,
            dirty=None,
        )
    ]
    event = sink.recorded[0]
    assert isinstance(event, ContextEvent)
    assert list(event.rules) == ["mp.ARC001", "mp.ERR002"]


def test_records_empty_rules_when_bundle_has_none() -> None:
    """AC-2: a bundle with no included rules records an empty `rules` mapping."""
    # Given a compiled bundle with no rules and an event sink
    bundle = CompiledBundle(
        text="bundle: 000000000000\n", id="000000000000", size=42, rules={}
    )
    sink = EventSinkFake()

    # When the stage entry is recorded
    record_entry("k3m9xq", "deliver", "architecture", bundle, sink)

    # Then the recorded event has an empty rules mapping
    assert len(sink.recorded) == 1
    event = sink.recorded[0]
    assert isinstance(event, ContextEvent)
    assert event.rules == {}


def test_repeated_calls_record_separate_events() -> None:
    """AC-6: each call writes its own event to the sink."""
    # Given a compiled bundle and an event sink
    bundle = CompiledBundle(
        text="bundle: 7a2383bc4098\n",
        id="7a2383bc4098",
        size=139,
        rules={"mp.ARC001": "hash-1"},
    )
    sink = EventSinkFake()

    # When the stage entry is recorded twice
    record_entry("k3m9xq", "deliver", "architecture", bundle, sink)
    record_entry("k3m9xq", "deliver", "architecture", bundle, sink)

    # Then two events are recorded
    assert len(sink.recorded) == 2
