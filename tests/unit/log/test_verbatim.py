# SPDX-License-Identifier: Apache-2.0
"""Test boundaries for recording and displaying verbatim harness values."""

import pytest


@pytest.mark.skip(reason="Delivery skeleton for verbatim event recording")
def test_event_round_trips_verbatim_ids() -> None:
    """AC-1 through AC-5 preserve configured values in the recorded envelope."""
    # Given configured session, parent, and extra variables.
    # When the sink records an event and the line codec reads it.
    # Then selected fields and all set values round-trip unchanged.


@pytest.mark.skip(reason="Delivery skeleton for escaped text reports")
def test_log_report_escapes_session_values() -> None:
    """AC-6 escapes present values in text and preserves them in JSON."""
    # Given a context event with control characters in its session fields.
    # When the report renders the recorded context.
    # Then text uses JSON literals and JSON preserves the original values.
