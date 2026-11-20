# SPDX-License-Identifier: Apache-2.0
"""Exercise the recording sink through fake ports and the real line codec.

An append serves as the observable boundary for a stamped event, and stderr
shows how the sink reports failures without raising them.
"""

import json
from dataclasses import dataclass
from errno import EACCES, ENOSPC, EROFS
from io import StringIO
from pathlib import Path
from typing import override

import pytest

from tests.fakes import FakeEnvironment
from tests.unit.fakes import (
    FakeClock,
    FakeDirectories,
    FakeRepository,
    FakeStdio,
    MemoryFileSystem,
)
from wio.formats.event_lines import Entry, decode_lines
from wio.log.sink import LogSink
from wio.models.config import Log
from wio.models.events import ContextEvent, Envelope, ReviewEvent

_HOME = Path("/h")
_EVENTS = _HOME / "log/app-6f8609bd196b/events.jsonl"
_VARIABLES = {"CLAUDE_CODE_SESSION_ID": "c1", "AI_AGENT": "x"}
_REVIEW = ReviewEvent(
    "k3m9xq", "deliver", "architecture-review", "f" * 40, "agent", "pass", {}, {}
)
_CONTEXT = ContextEvent(
    "k3m9xq", "deliver", "architecture", "bundle", 12, {}, None, None
)
_WRITE_WARNING = f"warning: the event log could not be written: {_EVENTS}: "
_LOCATION_WARNING = "warning: the event log could not be located: "
_SWITCH_WARNING = (
    'warning: WIO_LOG must be "off" to switch the log off; the log stays on'
)
_HINT = (
    "hint: add an exception to your harness's configuration for ~/.agents/wio "
    "or set $WIO_HOME to a directory your harness allows"
)


@dataclass(frozen=True)
class Recording:
    """The sink and its observable recording ports.

    Attributes:
        sink: The sink under test.
        environment: Supplies the switch, cwd and configured variables.
        clock: Supplies the envelope timestamp.
        directories: Supplies a fixed Wio home.
        repository: Supplies the clone identity.
        filesystem: Records every file operation.
        stderr: Collects diagnostics.
    """

    sink: LogSink
    environment: FakeEnvironment
    clock: FakeClock
    directories: FakeDirectories
    repository: FakeRepository
    filesystem: MemoryFileSystem
    stderr: StringIO


@pytest.fixture
def recording() -> Recording:
    """Wire a sink to a fixed clone, session and clock.

    Returns:
        The sink and the fake ports that tests can inspect or make fail.
    """
    environment = FakeEnvironment(Path("/w/app/sub"), _VARIABLES.copy())
    clock = FakeClock(1795000000.0)
    directories = FakeDirectories(_HOME)
    repository = FakeRepository(Path("/w/app"))
    filesystem = MemoryFileSystem()
    stderr = StringIO()
    stdio = FakeStdio(stderr=stderr)
    sink = LogSink(
        environment, clock, directories, repository, filesystem, stdio, Log()
    )
    return Recording(
        sink, environment, clock, directories, repository, filesystem, stderr
    )


def _entries(recording: Recording) -> tuple[Entry, ...]:
    """Decode the calls made to the file port.

    Args:
        recording: The sink and the fake file port that recorded its operations.

    Returns:
        The decoded entries in append order.

    Raises:
        AssertionError: An append does not contain one valid event line for
            the clone's events file.
    """
    entries: list[Entry] = []
    for path, text in recording.filesystem.appends:
        assert path == _EVENTS
        assert text.endswith("\n")
        assert text.count("\n") == 1
        decoded = decode_lines(text)
        assert decoded.skipped == 0
        assert len(decoded.entries) == 1
        entries.extend(decoded.entries)
    return tuple(entries)


def test_stamped_events_are_individual_appends(recording: Recording) -> None:
    """AC-1 preserves the full envelope and each event through one append.

    Args:
        recording: Fake ports for the first event and a later event.
    """
    # Given the default clone, Claude Code session and a fixed clock.
    expected = Envelope(
        1795000000.0,
        "/w/app/sub",
        "claude-code",
        "c1",
        None,
        ("claude-code",),
        _VARIABLES,
    )

    # When a review and a context event are written to the same sink.
    recording.sink.write(_REVIEW)
    recording.sink.write(_CONTEXT)

    # Then the only file operations appended two complete events.
    assert _entries(recording) == (Entry(expected, _REVIEW), Entry(expected, _CONTEXT))
    assert recording.filesystem.calls == [("append_text", _EVENTS)] * 2
    _, first_text = recording.filesystem.appends[0]
    assert json.loads(first_text)["time"] == "2026-11-18T11:06:40.000Z"
    assert recording.stderr.getvalue() == ""


def test_a_codex_subagent_stamp_has_its_parent(recording: Recording) -> None:
    """AC-1 uses the session identification fields in the envelope.

    Args:
        recording: Fake ports with a configurable environment.
    """
    # Given the Codex thread and its main session.
    variables = {"CODEX_SESSION_ID": "s1", "CODEX_THREAD_ID": "t2"}
    recording.environment.variables = variables

    # When the event is written.
    recording.sink.write(_REVIEW)

    # Then the thread is the session and the main session is the parent.
    (entry,) = _entries(recording)
    assert entry.envelope == Envelope(
        1795000000.0, "/w/app/sub", "codex", "t2", "s1", ("codex",), variables
    )


def test_event_round_trips_verbatim_ids(recording: Recording) -> None:
    """AC-1 round-trips configured values through the actual line codec."""
    # Given a long session, an empty parent, and an extra value with a lone surrogate.
    session = " \n" + "x" * 129
    variables = {
        "CODEX_THREAD_ID": session,
        "CODEX_SESSION_ID": "",
        "AI_AGENT": "é/\udcff",
    }
    recording.environment.variables = variables

    # When the sink writes an event and the encoded line is read back.
    recording.sink.write(_CONTEXT)
    (entry,) = _entries(recording)

    # Then every set field survives unchanged without warnings or raw controls.
    assert entry == Entry(
        Envelope(
            1795000000.0, "/w/app/sub", "codex", session, "", ("codex",), variables
        ),
        _CONTEXT,
    )
    _, text = recording.filesystem.appends[0]
    assert text.isascii()
    assert text.count("\n") == 1
    assert recording.stderr.getvalue() == ""


@pytest.mark.parametrize(
    ("step", "error", "message"),
    [
        ("switch", OSError("denied"), "denied"),
        ("identity", RuntimeError("not in a repository"), "not in a repository"),
        ("identity", RuntimeError("a\nb"), "a b"),
        ("identity", RuntimeError("a\rb"), "a b"),
        ("identity", RuntimeError("a\r\nb"), "a b"),
        ("home", ValueError("WIO_HOME must be absolute"), "WIO_HOME must be absolute"),
        ("home", FileNotFoundError(2, "home not found"), "home not found"),
    ],
)
def test_location_and_switch_read_failures_warn(
    recording: Recording,
    step: str,
    error: Exception,
    message: str,
) -> None:
    """AC-2 distinguishes a location failure from a write failure.

    Args:
        recording: Fake ports with a writable stderr.
        step: The lookup that fails.
        error: The failure raised by the lookup.
        message: The expected diagnostic detail.
    """
    # Given the switch, identity, or home lookup fails before a path is known.
    match step:
        case "switch":
            recording.environment.errors["WIO_LOG"] = error
        case "identity":
            recording.repository.top = None
            recording.repository.message = str(error)
        case "home":
            recording.directories.home = error
        case _:
            raise AssertionError(step)

    # When the event is written.
    recording.sink.write(_REVIEW)

    # Then the sink stops before stamping or appending and warns on one line.
    assert recording.stderr.getvalue() == _LOCATION_WARNING + message + "\n"
    assert not recording.filesystem.calls
    assert recording.clock.reads == 0


@pytest.mark.parametrize(
    ("step", "error", "message"),
    [
        (
            "directory",
            FileNotFoundError(2, "No such file or directory"),
            "No such file or directory",
        ),
        ("identify", RuntimeError("boom"), "boom"),
        ("identify", PermissionError(EACCES, "Permission denied"), "Permission denied"),
        ("clock", KeyError("x"), "'x'"),
        ("clock", ZeroDivisionError(), "ZeroDivisionError"),
        ("append", OSError("boom"), "boom"),
        ("append", OSError(ENOSPC, ""), str(OSError(ENOSPC, ""))),
        ("append", RuntimeError("boom"), "boom"),
    ],
)
def test_stamp_and_append_failures_warn_with_the_events_path(
    recording: Recording,
    step: str,
    error: Exception,
    message: str,
) -> None:
    """AC-2 reports failures once the events file is known.

    Args:
        recording: Fake ports with a writable stderr.
        step: The operation that fails.
        error: The failure raised by that operation.
        message: The expected diagnostic detail.
    """
    # Given one step after location fails, including permission outside append.
    match step:
        case "identify":
            recording.environment.errors["CLAUDE_CODE_SESSION_ID"] = error
        case "directory":
            recording.environment.errors[None] = error
        case "clock":
            recording.clock.seconds = error
        case "append":
            recording.filesystem.append_failure = error
        case _:
            raise AssertionError(step)

    # When the event is written.
    recording.sink.write(_REVIEW)

    # Then there is one write warning with no hint or further append attempt.
    assert recording.stderr.getvalue() == _WRITE_WARNING + message + "\n"
    assert len(recording.filesystem.appends) == int(step == "append")
    assert "WIO_HOME" not in recording.environment.reads


def test_encoding_failure_is_reported_before_append(recording: Recording) -> None:
    """AC-2 contains failures from the encoder too.

    Args:
        recording: Fake ports with a configurable clock.
    """
    # Given a time the line encoder refuses.
    recording.clock.seconds = float("inf")

    # When the event is written.
    recording.sink.write(_REVIEW)

    # Then the write warning names the events file and the file is untouched.
    assert (
        recording.stderr.getvalue()
        == _WRITE_WARNING + "event time must be finite and nonnegative\n"
    )
    assert not recording.filesystem.calls


@pytest.mark.parametrize(
    ("error", "home", "hint"),
    [
        (PermissionError(EACCES, "Permission denied"), None, True),
        (PermissionError(EACCES, "Permission denied"), "", True),
        (PermissionError(EACCES, "Permission denied"), "/h", False),
        (OSError(EROFS, "Read-only file system"), "", True),
        (OSError(ENOSPC, "No space left on device"), None, False),
    ],
)
def test_append_permission_hint_is_conditional(
    recording: Recording,
    error: OSError,
    home: str | None,
    hint: bool,  # noqa: FBT001 - a pytest parameter
) -> None:
    """AC-2 offers a hint only for a permission failure at the default Wio home.

    Args:
        recording: Fake ports with a configurable append and environment.
        error: The operating system error reported by the append.
        home: The value of WIO_HOME.
        hint: Whether the write warning should be followed by a hint.
    """
    # Given an append error and a default or explicitly named Wio home.
    if home is not None:
        recording.environment.variables["WIO_HOME"] = home
    recording.filesystem.append_failure = error

    # When the event is written.
    recording.sink.write(_REVIEW)

    # Then the warning uses strerror, with the hint only where applicable.
    expected = [_WRITE_WARNING + str(error.strerror)]
    if hint:
        expected.append(_HINT)
    assert recording.stderr.getvalue().splitlines() == expected
    assert len(recording.filesystem.appends) == 1


def test_failure_to_read_the_hint_variable_is_swallowed(recording: Recording) -> None:
    """AC-2 keeps the original warning when the hint cannot be evaluated.

    Args:
        recording: Fake ports with a configurable append and environment.
    """
    # Given a permission failure and a WIO_HOME lookup that fails.
    recording.filesystem.append_failure = PermissionError(EACCES, "Permission denied")

    recording.environment.errors["WIO_HOME"] = OSError("denied")

    # When the event is written.
    recording.sink.write(_REVIEW)

    # Then the original warning remains and the hint is omitted.
    assert recording.stderr.getvalue() == _WRITE_WARNING + "Permission denied\n"


class FailingStderr(StringIO):
    """An in-memory stream that rejects messages with a configured prefix."""

    def __init__(self, prefix: str) -> None:
        """Start with no output and a single category of message to reject.

        Args:
            prefix: The prefix of messages that fail to write.
        """
        super().__init__()
        self.prefix = prefix
        self.rejected: list[str] = []

    @override
    def write(self, text: str, /) -> int:
        """Write a message unless it matches the configured failure.

        Args:
            text: The message to write.

        Returns:
            The number of characters written.

        Raises:
            ValueError: The message matches the failure prefix.
        """
        if text.startswith(self.prefix):
            self.rejected.append(text)
            message = "stderr unavailable"
            raise ValueError(message)
        return super().write(text)


def test_failure_to_write_an_identification_warning_stops_the_append(
    recording: Recording,
) -> None:
    """AC-2 reports a failed identification warning as a write failure.

    Args:
        recording: Fake ports with a configurable environment and stderr.
    """
    # Given an unknown preference and stderr that rejects identification warnings.
    variables = {"WIO_PREFER_HARNESS": "unrecognized"}
    recording.environment.variables = variables
    stderr = FailingStderr("warning: WIO_PREFER_HARNESS")
    recording.sink.stdio.stderr = stderr

    # When the event is written.
    recording.sink.write(_REVIEW)

    # Then the sink reports the failure with the events path and omits the append.
    assert stderr.getvalue() == _WRITE_WARNING + "stderr unavailable\n"
    assert not recording.filesystem.calls


def test_failure_to_write_a_warning_is_swallowed(recording: Recording) -> None:
    """AC-2 contains stderr failures during diagnosis.

    Args:
        recording: Fake ports with a configurable stderr.
    """
    # Given a permission failure and an unavailable standard error stream.
    recording.filesystem.append_failure = PermissionError(EACCES, "Permission denied")
    stderr = FailingStderr(_WRITE_WARNING)
    recording.sink.stdio.stderr = stderr

    # When the event is written.
    recording.sink.write(_REVIEW)

    # Then it attempts the write warning once and skips the hint.
    assert stderr.rejected == [_WRITE_WARNING + "Permission denied\n"]
    assert stderr.getvalue() == ""
    assert len(recording.filesystem.appends) == 1
    assert "WIO_HOME" not in recording.environment.reads


def test_off_short_circuits_recording(recording: Recording) -> None:
    """AC-3 consults only the switch when it is off.

    Args:
        recording: Fake ports that expose all attempted calls.
    """
    # Given the exact switch, a malformed session, and a failing repository.
    variables = {"WIO_LOG": "off", "CLAUDE_CODE_SESSION_ID": "bad value!"}
    recording.environment.variables = variables
    recording.repository.top = None

    # When the event is written.
    recording.sink.write(_REVIEW)

    # Then it exits after reading the switch and has no side effects.
    assert recording.environment.reads == ["WIO_LOG"]
    assert recording.repository.identity_reads == 0
    assert not recording.directories.reads
    assert not recording.filesystem.calls
    assert recording.clock.reads == 0
    assert recording.stderr.getvalue() == ""


@pytest.mark.parametrize(
    ("switch", "warning"),
    [("maybe", _SWITCH_WARNING), ("OFF", _SWITCH_WARNING), ("", "")],
)
def test_other_switch_values_leave_recording_on(
    recording: Recording,
    switch: str,
    warning: str,
) -> None:
    """AC-3 leaves the log on for other values of the switch.

    Args:
        recording: Fake ports with a configurable environment.
        switch: The value of WIO_LOG.
        warning: The expected warning, or an empty string.
    """
    # Given an unrecognized nonempty switch value or an empty one.
    variables = _VARIABLES | {"WIO_LOG": switch}
    recording.environment.variables = variables

    # When the event is written.
    recording.sink.write(_REVIEW)

    # Then it appends and any warning omits the switch value.
    assert len(_entries(recording)) == 1
    assert recording.stderr.getvalue().splitlines() == ([warning] if warning else [])
