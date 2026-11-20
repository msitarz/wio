# SPDX-License-Identifier: Apache-2.0
"""Contract scenarios for the log show command.

The scenarios describe the CLI output and the behavior across event files.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio
    from tests.sandbox import Sandbox


_WORK = "k3m9xq"
_REVIEW_COMMIT = "a" * 40
_EMPTY_REPORT: dict[str, dict[str, object] | int] = {"works": {}, "skipped": 0}


def _event(stage: str, time: str, *, kind: str = "context", **fields: object) -> bytes:
    """Create a version 1 event line for a log fixture.

    Args:
        stage: The recorded stage name.
        time: The UTC time of day, including milliseconds.
        kind: The event type.
        **fields: Replacements for any wire field, with None omitting a field.

    Returns:
        The JSON event encoded as bytes with a terminating newline.
    """
    record: dict[str, object] = {
        "v": 1,
        "type": kind,
        "work": _WORK,
        "action": "deliver",
        "stage": stage,
        "time": f"2026-11-18T{time}Z",
        "directory": "/w/app",
    }
    if kind == "context":
        record.update(
            bundle="bundle", size=12, rules={}, harness="claude-code", session="c1"
        )
    else:
        record.update(
            commit=_REVIEW_COMMIT, judge="agent", result="pass", cited={}, hashes={}
        )
    record.update(fields)
    return (
        json.dumps(
            {key: value for key, value in record.items() if value is not None}
        ).encode()
        + b"\n"
    )


def _write_log(wio: Wio, sandbox: Sandbox, files: dict[str, bytes]) -> None:
    """Install a standalone clone and populate its event log.

    Args:
        wio: Initializes a clone whose fixture has no Work contracts.
        sandbox: Supplies the clone's root and isolated Wio home.
        files: Log file names and their raw data, including any damaged lines.
    """
    wio.fixture("config/rich")
    identity = sandbox.root.resolve() / ".git"
    digest = hashlib.sha256(os.fsencode(identity)).hexdigest()[:12]
    directory = Path(sandbox.env["WIO_HOME"]) / "log" / f"repo-{digest}"
    directory.mkdir(parents=True)
    for name, data in files.items():
        (directory / name).write_bytes(data)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize("args", [[], ["-h"]])
def test_log_help_names_show(wio: Wio, args: list[str]) -> None:
    """AC-1 makes show discoverable without locating a repository.

    Args:
        wio: The command facade with no registered repository.
        args: Arguments following log.
    """
    # Given a working directory with no repository.

    # When help is requested.
    output = wio.run(["log", *args])

    # Then help names show and exits successfully.
    assert output.exit_code == 0
    assert "show" in output.stdout
    assert output.stderr == ""


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize("args", [["nonsense"], ["--json"], ["show", "a", "b"]])
def test_log_rejects_invalid_usage(wio: Wio, args: list[str]) -> None:
    """AC-1 rejects unknown forms and misplaced or extra arguments.

    Args:
        wio: The command facade with no registered repository.
        args: Invalid arguments following log.
    """
    # Given a working directory with no repository.

    # When the invalid command runs.
    output = wio.run(["log", *args])

    # Then there is a usage error on standard error only.
    assert output.exit_code == 2
    assert output.stdout == ""
    assert "error:" in output.stderr


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize("empty_directory", [False, True])
def test_show_without_events_returns_the_empty_forms(
    wio: Wio,
    sandbox: Sandbox,
    empty_directory: bool,  # noqa: FBT001
) -> None:
    """AC-4 shows an absent or empty log without creating it.

    Args:
        wio: The command facade that initializes the clone.
        sandbox: Supplies the clone and its Wio home.
        empty_directory: Whether to create an empty directory before showing.
    """
    # Given a clone with no log directory or an empty one.
    if empty_directory:
        _write_log(wio, sandbox, {})
    else:
        wio.fixture("config/rich")

    # When both output forms are requested.
    text = wio.run(["log", "show"])
    document = wio.run(["log", "show", "--json"])

    # Then both succeed and JSON still returns a document.
    assert (text.exit_code, text.stdout, text.stderr) == (0, "", "")
    assert (document.exit_code, document.stderr) == (0, "")
    assert json.loads(document.stdout) == _EMPTY_REPORT
    assert Path(sandbox.env["WIO_HOME"]).exists() is empty_directory


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_show_retains_the_latest_context_for_each_stage(
    wio: Wio, sandbox: Sandbox
) -> None:
    """AC-2 selects the latest context and places stages by event time.

    Args:
        wio: Runs the show command.
        sandbox: Supplies the clone whose log is read.
    """
    # Given append order differs from event time.
    data = (
        _event("architecture", "10:09:00.000", session="c2")
        + _event("wiring", "10:07:00.000")
        + _event("architecture", "10:00:00.000")
        + _event("architecture", "10:05:00.000")
    )
    _write_log(wio, sandbox, {"events.jsonl": data})

    # When show selects the Work.
    output = wio.run(["log", "show", _WORK])

    # Then wiring comes before the latest architecture entry.
    assert (output.exit_code, output.stderr) == (0, "")
    assert output.stdout == (
        "k3m9xq\n"
        '  deliver wiring  entered 2026-11-18T10:07:00.000Z  claude-code:"c1"\n'
        '  deliver architecture  entered 2026-11-18T10:09:00.000Z  claude-code:"c2"\n'
    )


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_show_formats_session_labels_and_utc_times(wio: Wio, sandbox: Sandbox) -> None:
    """AC-2 renders the possible session labels with millisecond UTC timestamps.

    Args:
        wio: Runs the show command.
        sandbox: Supplies the clone whose log is read.
    """
    # Given a parent, ordered matches, no session evidence and a known harness.
    data = (
        _event(
            "architecture", "10:00:00.123", harness="codex", session="t2", parent="s1"
        )
        + _event(
            "wiring",
            "10:01:00.000",
            harness=None,
            session=None,
            matches=["claude-code", "codex"],
        )
        + _event(
            "implementation",
            "10:02:00.000",
            harness=None,
            session=None,
            matches=["codex"],
        )
        + _event(
            "integration", "10:03:00.000", harness="codex", session=None, parent="s1"
        )
    )
    _write_log(wio, sandbox, {"events.jsonl": data})

    # When the text output is requested.
    output = wio.run(["log", "show"])

    # Then each label describes the evidence in its latest context.
    assert (output.exit_code, output.stderr) == (0, "")
    assert output.stdout == (
        "k3m9xq\n"
        "  deliver architecture  entered 2026-11-18T10:00:00.123Z"
        '  codex:"t2" (parent "s1")\n'
        "  deliver wiring  entered 2026-11-18T10:01:00.000Z"
        "  ambiguous (claude-code, codex)\n"
        "  deliver implementation  entered 2026-11-18T10:02:00.000Z  unknown session\n"
        "  deliver integration  entered 2026-11-18T10:03:00.000Z"
        '  codex:unknown (parent "s1")\n'
    )


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_show_retains_reviews_by_judge_and_commit(wio: Wio, sandbox: Sandbox) -> None:
    """AC-3 retains the latest review for each judge and reviewed commit.

    Args:
        wio: Runs both output forms of the command.
        sandbox: Supplies the clone whose log contains the reviews.
    """
    # Given a revised review, two judges and a second reviewed commit.
    data = (
        _event("docs-review", "10:10:00.000", kind="review")
        + _event("docs-review", "10:00:00.000", kind="review", result="fail")
        + _event(
            "docs-review",
            "10:05:00.000",
            kind="review",
            judge="human",
            cited={"AC-3": "fail", "AC-1": "pass"},
        )
        + _event("docs-review", "10:11:00.000", kind="review", commit="b" * 40)
    )
    _write_log(wio, sandbox, {"events.jsonl": data})

    # When both forms are requested for that Work.
    text = wio.run(["log", "show", _WORK])
    document = wio.run(["log", "show", _WORK, "--json"])

    # Then the retained reviews are ordered by their positions in the history.
    assert (text.exit_code, text.stderr, document.exit_code, document.stderr) == (
        0,
        "",
        0,
        "",
    )
    assert text.stdout == (
        "k3m9xq\n"
        "  deliver docs-review  human pass aaaaaaaaaaaa  2026-11-18T10:05:00.000Z"
        "  AC-3=fail AC-1=pass\n"
        "  deliver docs-review  agent pass aaaaaaaaaaaa  2026-11-18T10:10:00.000Z\n"
        "  deliver docs-review  agent pass bbbbbbbbbbbb  2026-11-18T10:11:00.000Z\n"
    )
    report = json.loads(document.stdout)
    assert list(report) == ["works", "skipped"]
    (row,) = report["works"][_WORK]
    assert list(row) == ["action", "stage", "entered", "session", "reviews"]
    assert row["entered"] is row["session"] is None
    first = row["reviews"][0]
    assert list(first) == ["judge", "result", "commit", "time", "cited"]
    assert first == {
        "judge": "human",
        "result": "pass",
        "commit": _REVIEW_COMMIT,
        "time": "2026-11-18T10:05:00.000Z",
        "cited": {"AC-3": "fail", "AC-1": "pass"},
    }
    assert list(first["cited"]) == ["AC-3", "AC-1"]
    assert [
        (review["judge"], review["commit"], review["result"])
        for review in row["reviews"]
    ] == [
        ("human", _REVIEW_COMMIT, "pass"),
        ("agent", _REVIEW_COMMIT, "pass"),
        ("agent", "b" * 40, "pass"),
    ]


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_show_groups_context_and_reviews_and_places_the_row_by_its_latest_event(
    wio: Wio,
    sandbox: Sandbox,
) -> None:
    """AC-3 positions a stage by its latest event of either kind.

    Args:
        wio: Runs both output forms of the command.
        sandbox: Supplies the clone whose log contains interleaved events.
    """
    # Given a review-only row and a mixed row whose review follows wiring.
    data = (
        _event("architecture-review", "09:55:00.000", kind="review")
        + _event(
            "docs-review",
            "10:00:00.000",
            harness="codex",
            session="t2",
            matches=["codex"],
        )
        + _event("wiring", "10:05:00.000")
        + _event("docs-review", "10:10:00.000", kind="review")
    )
    _write_log(wio, sandbox, {"events.jsonl": data})

    # When both output forms are requested.
    text = wio.run(["log", "show"])
    document = wio.run(["log", "show", "--json"])

    # Then the mixed row comes last and prints context before its review.
    assert (text.exit_code, document.exit_code) == (0, 0)
    assert text.stdout == (
        "k3m9xq\n"
        "  deliver architecture-review  agent pass aaaaaaaaaaaa"
        "  2026-11-18T09:55:00.000Z\n"
        '  deliver wiring  entered 2026-11-18T10:05:00.000Z  claude-code:"c1"\n'
        '  deliver docs-review  entered 2026-11-18T10:00:00.000Z  codex:"t2"\n'
        "  deliver docs-review  agent pass aaaaaaaaaaaa  2026-11-18T10:10:00.000Z\n"
    )
    early, wiring, gate = json.loads(document.stdout)["works"][_WORK]
    assert early["stage"] == "architecture-review"
    assert early["entered"] is early["session"] is None
    assert wiring["stage"] == "wiring"
    assert wiring["reviews"] == []
    assert gate["stage"] == "docs-review"
    assert gate["entered"] == "2026-11-18T10:00:00.000Z"
    assert gate["session"] == {
        "harness": "codex",
        "session": "t2",
        "parent": None,
        "matches": ["codex"],
    }
    assert list(gate["session"]) == ["harness", "session", "parent", "matches"]
    assert len(gate["reviews"]) == 1


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_show_finds_retired_work_and_selects_an_absent_work(
    wio: Wio,
    sandbox: Sandbox,
) -> None:
    """AC-4 selects by recorded Work id without reading the Works tree.

    Args:
        wio: Runs show with and without a Work filter.
        sandbox: Supplies the clone whose log refers to a missing Work.
    """
    # Given a log with a context event for a Work absent from the clone.
    data = _event(
        "architecture", "10:00:00.000", harness="codex", session="t2", matches=["codex"]
    )
    _write_log(wio, sandbox, {"events.jsonl": data})

    # When showing all Works and then requesting a different Work.
    existing = wio.run(["log", "show", "--json"])
    absent = wio.run(["log", "show", "other1"])
    absent_json = wio.run(["log", "show", "other1", "--json"])

    # Then the recorded Work is present and the missing selection has empty output.
    assert (existing.exit_code, existing.stderr) == (0, "")
    assert json.loads(existing.stdout) == {
        "works": {
            _WORK: [
                {
                    "action": "deliver",
                    "stage": "architecture",
                    "entered": "2026-11-18T10:00:00.000Z",
                    "session": {
                        "harness": "codex",
                        "session": "t2",
                        "parent": None,
                        "matches": ["codex"],
                    },
                    "reviews": [],
                }
            ]
        },
        "skipped": 0,
    }
    assert (absent.exit_code, absent.stdout, absent.stderr) == (0, "", "")
    assert (absent_json.exit_code, absent_json.stderr) == (0, "")
    assert json.loads(absent_json.stdout) == _EMPTY_REPORT


@pytest.mark.channels(Channel.CLI)
@pytest.mark.parametrize("flags", [[], ["--json"]])
def test_show_outside_a_repository_reports_a_usage_error(
    wio: Wio, flags: list[str]
) -> None:
    """AC-4 reports a location error when repository discovery fails.

    Args:
        wio: Runs in a directory with no repository.
        flags: The requested output form.
    """
    # Given a directory outside any repository.

    # When show tries to find the clone's log.
    output = wio.run(["log", "show", *flags])

    # Then it reports the repository failure without a partial report.
    assert (output.exit_code, output.stdout) == (2, "")
    assert "not inside a git repository" in output.stderr


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_show_skips_damaged_lines_and_replaces_bytes_in_valid_json(
    wio: Wio,
    sandbox: Sandbox,
) -> None:
    """AC-5 counts malformed lines and preserves otherwise valid UTF-8 replacements.

    Args:
        wio: Runs both output forms of the command.
        sandbox: Supplies the clone whose logs contain damaged bytes.
    """
    # Given a torn last line, an unsupported version, and two invalid UTF-8 uses.
    good = _event("architecture", "10:00:00.000")
    replaced = _event("wiring", "10:01:00.000", session="session-marker")
    _write_log(
        wio,
        sandbox,
        {
            "a.jsonl": good + b'{"torn":',
            "events.jsonl": (
                replaced.replace(b"session-marker", b"c\xff")
                + _event("integration", "10:02:00.000", v=2)
                + b"\xff\n"
            ),
        },
    )

    # When both output forms are requested.
    text = wio.run(["log", "show"])
    document = wio.run(["log", "show", "--json"])

    # Then the next file starts cleanly, and only damaged lines count as skipped.
    assert (text.exit_code, text.stderr) == (
        0,
        "note: skipped 3 lines of the event log\n",
    )
    assert text.stdout == (
        "k3m9xq\n"
        '  deliver architecture  entered 2026-11-18T10:00:00.000Z  claude-code:"c1"\n'
        '  deliver wiring  entered 2026-11-18T10:01:00.000Z  claude-code:"c\\ufffd"\n'
    )
    assert (document.exit_code, document.stderr) == (0, "")
    report = json.loads(document.stdout)
    assert report["skipped"] == 3
    assert report["works"][_WORK][1]["session"]["session"] == "c\ufffd"


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_show_counts_bad_lines_even_when_the_work_filter_excludes_every_row(
    wio: Wio,
    sandbox: Sandbox,
) -> None:
    """AC-5 keeps the global skipped count and uses a singular note.

    Args:
        wio: Runs show with and without filters.
        sandbox: Supplies the clone whose log has one damaged line.
    """
    # Given an event for each of two Works and one damaged line.
    data = (
        _event("wiring", "10:00:00.000")
        + b"broken\n"
        + _event("architecture", "10:01:00.000", work="zz9999")
    )
    _write_log(wio, sandbox, {"events.jsonl": data})

    # When each output form selects one Work or a Work with no events.
    text = wio.run(["log", "show", _WORK])
    selected = wio.run(["log", "show", _WORK, "--json"])
    empty = wio.run(["log", "show", "other1", "--json"])

    # Then the filtered report still includes the common damage count.
    assert (text.exit_code, text.stderr) == (
        0,
        "note: skipped 1 line of the event log\n",
    )
    assert "zz9999" not in text.stdout
    assert (selected.exit_code, selected.stderr) == (0, "")
    report = json.loads(selected.stdout)
    assert report["skipped"] == 1
    assert list(report["works"]) == [_WORK]
    assert (empty.exit_code, empty.stderr) == (0, "")
    assert json.loads(empty.stdout) == {"works": {}, "skipped": 1}


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_show_orders_works_and_breaks_event_time_ties_by_file_and_line(
    wio: Wio,
    sandbox: Sandbox,
) -> None:
    """AC-6 orders Works by id and breaks equal timestamps deterministically.

    Args:
        wio: Runs show on the whole history.
        sandbox: Supplies the clone whose log spans several files.
    """
    # Given same-time events in two files, a same-file tie and out-of-order Works.
    _write_log(
        wio,
        sandbox,
        {
            "events.jsonl": _event("integration", "10:05:00.000")
            + _event("wiring", "10:00:00.000")
            + _event("architecture", "10:05:00.000", action="define"),
            "a.jsonl": (
                _event("architecture", "09:55:00.000", work="zz9999")
                + _event("architecture", "10:05:00.000", session="first")
                + _event("architecture", "10:05:00.000", session="last")
            ),
        },
    )

    # When the full report is requested.
    output = wio.run(["log", "show", "--json"])

    # Then Works are sorted and time ties follow file and line order.
    assert (output.exit_code, output.stderr) == (0, "")
    works = json.loads(output.stdout)["works"]
    assert list(works) == [_WORK, "zz9999"]
    rows = works[_WORK]
    assert [(row["action"], row["stage"]) for row in rows] == [
        ("deliver", "wiring"),
        ("deliver", "architecture"),
        ("deliver", "integration"),
        ("define", "architecture"),
    ]
    assert rows[1]["session"]["session"] == "last"


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize(
    ("session", "parent", "label"),
    [
        (
            'a\n\x1bb"\\\x7fé\U0001f600\udcff',
            "\t",
            r'claude-code:"a\n\u001bb\"\\\u007f\u00e9\ud83d\ude00\udcff" (parent "\t")',
        ),
        ("", None, 'claude-code:""'),
        ("abc", "", 'claude-code:"abc" (parent "")'),
        (None, None, "claude-code:unknown"),
        (None, "def", 'claude-code:unknown (parent "def")'),
    ],
)
def test_show_quotes_present_session_fields(
    wio: Wio, sandbox: Sandbox, session: str | None, parent: str | None, label: str
) -> None:
    """AC-6 renders JSON literals in text and keeps the original JSON values."""
    # Given one recorded context, which may lack a session as in earlier logs.
    stage = "wiring"
    time = "10:00:00.000"
    line = _event(stage, time, session=session, parent=parent)
    _write_log(wio, sandbox, {"events.jsonl": line})

    # When both report formats are requested.
    text = wio.run(["log", "show"])
    document = wio.run(["log", "show", "--json"])

    # Then text stays on one report line and JSON retains the original fields.
    assert text.exit_code == document.exit_code == 0
    assert text.stderr == document.stderr == ""
    assert text.stdout == (
        f"{_WORK}\n  deliver {stage}  entered 2026-11-18T{time}Z  {label}\n"
    )
    shown = json.loads(document.stdout)["works"][_WORK][0]["session"]
    assert (shown["session"], shown["parent"]) == (session, parent)
