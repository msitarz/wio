# SPDX-License-Identifier: Apache-2.0
"""Tests for the record script that stands in for `wio trailers check`."""

import io
import subprocess
lazy from pathlib import Path

import pytest

from scripts import records

RECORD = "Wio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: architecture"


def _message(*paragraphs: str) -> str:
    """Join paragraphs into a commit message.

    Args:
        *paragraphs: The paragraphs, subject first.

    Returns:
        The message.
    """
    return "\n\n".join(paragraphs) + "\n"


@pytest.mark.parametrize(
    "record",
    [
        RECORD,
        f"{RECORD}\nWio-Criteria: AC-1, AC-3",
        f"{RECORD}\nWio-Result: pass",
        f"{RECORD}\nCo-Authored-By: A Person <a@example.com>",
        "Wio-Work: none",
    ],
)
def test_valid_records_have_no_problems(record: str) -> None:
    """A well-formed record, or the explicit opt-out, passes."""
    assert records.message_problems(_message("docs: x", record)) == []


@pytest.mark.parametrize(
    ("record", "problem"),
    [
        ("Wio-Action: deliver", "Wio-Work is missing"),
        ("Wio-Work: k3m9xq\nWio-Action: deliver", "Wio-Stage is missing"),
        ("Wio-Work: K3M9XQ\nWio-Action: a\nWio-Stage: b", "is not a Work id"),
        ("Wio-Work: k3m9xi\nWio-Action: a\nWio-Stage: b", "is not a Work id"),
        (f"{RECORD}\nWio-Criteria: 1, 3", "must look like"),
        (f"{RECORD}\nWio-Result: maybe", "must be one of"),
        (f"{RECORD}\nWio-Stage: wiring", "appears more than once"),
        (f"{RECORD}\nWio-Typo: x", "unknown trailer Wio-Typo"),
        ("Wio-Work: none\nWio-Stage: define", "not allowed when Wio-Work is none"),
        ("Wio-Work: k3m9xq\nWio-Action: Deliver\nWio-Stage: x", "is not a name"),
    ],
)
def test_malformed_records_are_reported(record: str, problem: str) -> None:
    """Each malformed field gives a message that names it."""
    problems = records.message_problems(_message("docs: x", record))

    assert any(problem in found for found in problems), problems


def test_a_message_without_a_record_is_reported() -> None:
    """A commit must say which Work it belongs to, or that it belongs to none."""
    assert records.message_problems(_message("docs: x", "Body.")) == [
        "no Wio-* record; add one, or `Wio-Work: none`"
    ]


@pytest.mark.parametrize("subject", ["Merge branch 'x'", "fixup! docs: x"])
def test_merge_and_fixup_commits_need_no_record(subject: str) -> None:
    """Commits that are merged or squashed away are not checked."""
    assert records.message_problems(_message(subject, "Body.")) == []


def test_records_in_fenced_code_and_comments_are_ignored() -> None:
    """Quoted example records and git's comment lines do not count."""
    message = _message("docs: x", f"```text\n{RECORD}\n```", "# Wio-Work: k3m9xq")

    assert records.records(message) == []


def test_a_paragraph_with_prose_is_not_a_record() -> None:
    """Every line of a record must be a trailer."""
    assert records.records(_message("docs: x", f"Some prose.\n{RECORD}")) == []


def test_several_records_are_read_in_order() -> None:
    """A message can hold one record per paragraph."""
    second = "Wio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: wiring"

    found = records.records(_message("docs: x", RECORD, second))

    assert [dict(record)["Wio-Stage"] for record in found] == ["architecture", "wiring"]


def test_collect_keeps_records_of_works_and_drops_the_rest() -> None:
    """Only `Wio-*` fields of records that name a Work are collected."""
    messages = [
        _message("a", f"{RECORD}\nCo-Authored-By: A <a@example.com>"),
        _message("b", "Wio-Work: none"),
    ]

    assert records.collect(messages) == [RECORD]


def test_with_records_replaces_the_records_at_the_end_of_a_body() -> None:
    """The body keeps its prose and gets exactly the given records."""
    body = "## Outcome\r\n\r\nText.\r\n\r\nWio-Work: abcdef\r\nWio-Action: a"

    updated = records.with_records(body, [RECORD])

    assert updated == f"## Outcome\n\nText.\n\n{RECORD}\n"
    assert records.with_records(updated, [RECORD]) == updated


def test_check_command_reads_a_message_file(tmp_path: Path) -> None:
    """The commit-msg hook passes the message file and gets the exit code."""
    valid = tmp_path / "valid"
    valid.write_text(_message("docs: x", RECORD), encoding="utf-8")
    invalid = tmp_path / "invalid"
    invalid.write_text(_message("docs: x"), encoding="utf-8")

    assert records.main(["check", str(valid)]) == 0
    assert records.main(["check", str(invalid)]) == 1


def _commit(repo: Path, message: str) -> None:
    """Make an empty commit in a repository.

    Args:
        repo: The repository.
        message: The commit message.
    """
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-q",
            "--allow-empty",
            "--no-verify",
            "-m",
            message,
        ],
        check=True,
    )


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a git repository with one root commit and work inside it.

    Args:
        tmp_path: pytest's temporary directory.
        monkeypatch: pytest's monkeypatch fixture.

    Returns:
        The repository's path.
    """
    for key, value in {"NAME": "Test", "EMAIL": "test@example.com"}.items():
        monkeypatch.setenv(f"GIT_AUTHOR_{key}", value)
        monkeypatch.setenv(f"GIT_COMMITTER_{key}", value)
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    _commit(tmp_path, "chore: root")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_commits_command_fails_only_on_malformed_records(repo: Path) -> None:
    """A commit without a record is a warning; a malformed record fails."""
    _commit(repo, _message("docs: no record"))
    assert records.main(["commits", "HEAD~1..HEAD"]) == 0

    _commit(repo, _message("docs: bad", "Wio-Work: k3m9xq"))
    assert records.main(["commits", "HEAD~1..HEAD"]) == 1


def test_body_command_appends_the_commits_records(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The body gets the records of the range's commits, oldest first."""
    _commit(repo, _message("docs: a", RECORD))
    monkeypatch.setattr("sys.stdin", io.StringIO("## Outcome\n\nText."))

    assert records.main(["body", "HEAD~1..HEAD"]) == 0
    assert capsys.readouterr().out == f"## Outcome\n\nText.\n\n{RECORD}\n"


def test_body_command_prints_nothing_when_the_body_is_current(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A body that already ends with the records needs no edit."""
    _commit(repo, _message("docs: a", RECORD))
    body = (
        f"## Outcome\r\n\r\nText.\r\n\r\n{RECORD.replace(chr(10), chr(13) + chr(10))}"
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(body))

    assert records.main(["body", "HEAD~1..HEAD"]) == 0
    assert not capsys.readouterr().out
