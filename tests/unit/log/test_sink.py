# SPDX-License-Identifier: Apache-2.0
"""Contract scenarios for a sink built over fake ports.

These scenarios check the append boundary, including how failures affect
the caller and what appears on standard error.
"""

import pytest


def test_stamped_events_are_individual_appends() -> None:
    """AC-1 records each event with its own envelope.

    Check the complete decoded event and envelope at the append boundary.
    """
    # Given the clone /w/app/.git, cwd /w/app/sub, home /h, clock 1795000000,
    # and Claude Code with session c1 and AI_AGENT=x.
    # When two events are written.
    # Then the only filesystem calls are two appends to
    # /h/log/app-6f8609bd196b/events.jsonl. Each line decodes to its event
    # with the clock and cwd above, Claude Code, c1, and both recorded ids.
    pytest.skip("Pending log sink implementation")


def test_the_stamp_preserves_session_identity() -> None:
    """AC-1 preserves the parent and diagnostics of session identification.

    Identification runs for each append attempt after successful location.
    """
    # Given a Codex subagent t2 of s1, and separately a malformed Claude ID.
    # When the Codex event is written once and the Claude event twice.
    # Then Codex has session t2 and parent s1. Both Claude events have an
    # unknown session and each warning names the variable without its value.
    pytest.skip("Pending log sink implementation")


def test_location_and_switch_read_failures_warn() -> None:
    """AC-2 reports failures before the events file is known.

    The location warning uses one line and identifies the underlying problem.
    """
    # Given a switch read, clone identity, or home lookup that raises.
    # When write is called.
    # Then it returns without appending and emits one location warning,
    # using strerror when provided and folding line breaks.
    pytest.skip("Pending log sink implementation")


def test_stamp_and_append_failures_warn() -> None:
    """AC-2 names the events file after successful location.

    Failures may come from identification, clock, cwd, encoding, or append.
    """
    # Given one of those steps raises, including empty exception text,
    # OSError without strerror, and permission denied outside append.
    # When write is called.
    # Then it returns and warns with the events path and error message or
    # exception class. Permission errors outside append have no hint.
    pytest.skip("Pending log sink implementation")


def test_append_permission_hint_is_conditional() -> None:
    """AC-2 offers the home hint for permission failures at append.

    The hint is relevant to the default Wio home and can fail independently.
    """
    # Given permission denied, a read-only filesystem, or no space on append,
    # with WIO_HOME unset, empty, explicitly named, or failing on lookup.
    # When write is called, including with a closed stderr.
    # Then it always returns. Only permission denied and read-only append
    # errors get a hint, and only with WIO_HOME absent or empty.
    pytest.skip("Pending log sink implementation")


def test_the_switch_is_exact() -> None:
    """AC-3 switches recording off before any other port is consulted.

    An unrecognized nonempty value warns and leaves recording enabled.
    """
    # Given WIO_LOG values off, OFF, maybe, empty, or absent.
    # When write is called.
    # Then off reads only WIO_LOG and makes no warnings or writes.
    # Other values append, with one value-free warning for OFF and maybe.
    pytest.skip("Pending log sink implementation")
