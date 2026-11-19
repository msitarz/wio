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
from unittest.mock import Mock, call

import pytest

from tests.unit.fakes import FakeStdio
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
    environment: Mock
    clock: Mock
    directories: Mock
    repository: Mock
    filesystem: Mock
    stderr: StringIO


@pytest.fixture
def recording() -> Recording:
    """Wire a sink to a fixed clone, session and clock.

    Returns:
        The sink and the fake ports that tests can inspect or make fail.
    """
    environment = Mock()
    environment.get.side_effect = _VARIABLES.get
    environment.working_directory.return_value = Path("/w/app/sub")
    clock = Mock()
    clock.now.return_value = 1795000000.0
    directories = Mock()
    directories.wio_home.return_value = _HOME
    repository = Mock()
    repository.identity.return_value = Path("/w/app/.git")
    filesystem = Mock()
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
        AssertionError: The port did anything other than append valid event lines
            to the clone's events file.
    """
    entries: list[Entry] = []
    for method in recording.filesystem.method_calls:
        _, (path, text), kwargs = method
        assert method == call.append_text(path, text)
        assert not kwargs
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
    first_text = recording.filesystem.append_text.call_args_list[0].args[1]
    assert json.loads(first_text)["time"] == "2026-11-18T11:06:40.000Z"
    assert recording.stderr.getvalue() == ""


def test_a_codex_subagent_stamp_has_its_parent(recording: Recording) -> None:
    """AC-1 uses the session identification fields in the envelope.

    Args:
        recording: Fake ports with a configurable environment.
    """
    # Given the Codex thread and its main session.
    variables = {"CODEX_SESSION_ID": "s1", "CODEX_THREAD_ID": "t2"}
    recording.environment.get.side_effect = variables.get

    # When the event is written.
    recording.sink.write(_REVIEW)

    # Then the thread is the session and the main session is the parent.
    (entry,) = _entries(recording)
    assert entry.envelope == Envelope(
        1795000000.0, "/w/app/sub", "codex", "t2", "s1", ("codex",), variables
    )


def test_identification_warns_at_every_write(recording: Recording) -> None:
    """AC-1 keeps identification warnings and records an unknown session.

    Args:
        recording: Fake ports with a configurable environment.
    """
    # Given an unusable Claude Code session id.
    variables = {"CLAUDE_CODE_SESSION_ID": "bad value!"}
    recording.environment.get.side_effect = variables.get

    # When two events are written.
    recording.sink.write(_REVIEW)
    recording.sink.write(_REVIEW)

    # Then both events retain just the harness and both warnings omit the value.
    expected = Envelope(
        1795000000.0, "/w/app/sub", "claude-code", None, None, ("claude-code",), {}
    )
    assert _entries(recording) == (Entry(expected, _REVIEW), Entry(expected, _REVIEW))
    warning = "warning: CLAUDE_CODE_SESSION_ID has an invalid id"
    assert recording.stderr.getvalue().splitlines() == [warning, warning]


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
    methods = {
        "switch": recording.environment.get,
        "identity": recording.repository.identity,
        "home": recording.directories.wio_home,
    }
    methods[step].side_effect = error

    # When the event is written.
    recording.sink.write(_REVIEW)

    # Then the sink stops before stamping or appending and warns on one line.
    assert recording.stderr.getvalue() == _LOCATION_WARNING + message + "\n"
    assert recording.filesystem.mock_calls == recording.clock.mock_calls == []


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
    faults = {
        "identify": (recording.environment.get, [None, error]),
        "directory": (recording.environment.working_directory, error),
        "clock": (recording.clock.now, error),
        "append": (recording.filesystem.append_text, error),
    }
    method, failure = faults[step]
    method.side_effect = failure

    # When the event is written.
    recording.sink.write(_REVIEW)

    # Then there is one write warning with no hint or further append attempt.
    assert recording.stderr.getvalue() == _WRITE_WARNING + message + "\n"
    assert recording.filesystem.append_text.call_count == int(step == "append")
    assert call.get("WIO_HOME") not in recording.environment.mock_calls


def test_encoding_failure_is_reported_before_append(recording: Recording) -> None:
    """AC-2 contains failures from the encoder too.

    Args:
        recording: Fake ports with a configurable clock.
    """
    # Given a time the line encoder refuses.
    recording.clock.now.return_value = float("inf")

    # When the event is written.
    recording.sink.write(_REVIEW)

    # Then the write warning names the events file and the file is untouched.
    assert (
        recording.stderr.getvalue()
        == _WRITE_WARNING + "event time must be finite and nonnegative\n"
    )
    assert recording.filesystem.mock_calls == []


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
    variables = _VARIABLES | {"WIO_HOME": home}
    recording.environment.get.side_effect = variables.get
    recording.filesystem.append_text.side_effect = error

    # When the event is written.
    recording.sink.write(_REVIEW)

    # Then the warning uses strerror, with the hint only where applicable.
    expected = [_WRITE_WARNING + str(error.strerror)]
    if hint:
        expected.append(_HINT)
    assert recording.stderr.getvalue().splitlines() == expected
    assert recording.filesystem.append_text.call_count == 1


def test_failure_to_read_the_hint_variable_is_swallowed(recording: Recording) -> None:
    """AC-2 keeps the original warning when the hint cannot be evaluated.

    Args:
        recording: Fake ports with a configurable append and environment.
    """
    # Given a permission failure and a WIO_HOME lookup that fails.
    recording.filesystem.append_text.side_effect = PermissionError(
        EACCES, "Permission denied"
    )

    def get(name: str) -> str | None:
        """Read the fixed environment, except for the inaccessible home value.

        Args:
            name: The environment variable to look up.

        Returns:
            The variable's value, if set.

        Raises:
            OSError: When the sink reads WIO_HOME.
        """
        if name == "WIO_HOME":
            message = "denied"
            raise OSError(message)
        return _VARIABLES.get(name)

    recording.environment.get.side_effect = get

    # When the event is written.
    recording.sink.write(_REVIEW)

    # Then the original warning remains and the hint is omitted.
    assert recording.stderr.getvalue() == _WRITE_WARNING + "Permission denied\n"


def test_failure_to_write_an_identification_warning_stops_the_append(
    recording: Recording,
) -> None:
    """AC-2 reports a failed identification warning as a write failure.

    Args:
        recording: Fake ports with a configurable environment and stderr.
    """
    # Given a malformed session id and stderr that fails on its first write.
    variables = {"CLAUDE_CODE_SESSION_ID": "bad value!"}
    recording.environment.get.side_effect = variables.get
    stderr = Mock()
    stderr.write.side_effect = [ValueError("stderr unavailable"), None]
    recording.sink.stdio.stderr = stderr

    # When the event is written.
    recording.sink.write(_REVIEW)

    # Then the sink reports the failure with the events path and omits the append.
    assert stderr.write.call_args_list == [
        call("warning: CLAUDE_CODE_SESSION_ID has an invalid id\n"),
        call(_WRITE_WARNING + "stderr unavailable\n"),
    ]
    assert recording.filesystem.mock_calls == []


def test_failure_to_write_a_warning_is_swallowed(recording: Recording) -> None:
    """AC-2 contains stderr failures during diagnosis.

    Args:
        recording: Fake ports with a configurable stderr.
    """
    # Given a permission failure and an unavailable standard error stream.
    recording.filesystem.append_text.side_effect = PermissionError(
        EACCES, "Permission denied"
    )
    stderr = Mock()
    stderr.write.side_effect = ValueError("closed")
    recording.sink.stdio.stderr = stderr

    # When the event is written.
    recording.sink.write(_REVIEW)

    # Then it attempts the write warning once and skips the hint.
    stderr.write.assert_called_once_with(_WRITE_WARNING + "Permission denied\n")
    assert recording.filesystem.append_text.call_count == 1
    assert call.get("WIO_HOME") not in recording.environment.mock_calls


def test_off_short_circuits_recording(recording: Recording) -> None:
    """AC-3 consults only the switch when it is off.

    Args:
        recording: Fake ports that expose all attempted calls.
    """
    # Given the exact switch, a malformed session, and a failing repository.
    variables = {"WIO_LOG": "off", "CLAUDE_CODE_SESSION_ID": "bad value!"}
    recording.environment.get.side_effect = variables.get
    recording.repository.identity.side_effect = RuntimeError("not in a repository")

    # When the event is written.
    recording.sink.write(_REVIEW)

    # Then it exits after reading the switch and has no side effects.
    assert recording.environment.mock_calls == [call.get("WIO_LOG")]
    assert recording.repository.mock_calls == recording.directories.mock_calls == []
    assert recording.filesystem.mock_calls == recording.clock.mock_calls == []
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
    recording.environment.get.side_effect = variables.get

    # When the event is written.
    recording.sink.write(_REVIEW)

    # Then it appends and any warning omits the switch value.
    assert len(_entries(recording)) == 1
    assert recording.stderr.getvalue().splitlines() == ([warning] if warning else [])
