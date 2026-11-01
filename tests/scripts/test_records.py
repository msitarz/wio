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
    # Given a commit message that ends with a well-formed record
    message = _message("docs: x", record)

    # When its problems are computed
    problems = records.message_problems(message)

    # Then there are none
    assert problems == []


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
    # Given a commit message whose record has one malformed field
    message = _message("docs: x", record)

    # When its problems are computed
    problems = records.message_problems(message)

    # Then one of them describes that field
    assert any(problem in found for found in problems), problems


def test_a_message_without_a_record_is_reported() -> None:
    """A commit must say which Work it belongs to, or that it belongs to none."""
    # Given a commit message with prose and no record
    message = _message("docs: x", "Body.")

    # When its problems are computed
    problems = records.message_problems(message)

    # Then the only problem says how to add a record
    assert problems == ["no Wio-* record; add one, or `Wio-Work: none`"]


@pytest.mark.parametrize(
    "subject", ["Merge branch 'x'", 'Revert "docs: x"', "fixup! docs: x"]
)
def test_merge_revert_and_fixup_commits_need_no_record(subject: str) -> None:
    """Commits that are merged, reverted or squashed away are not checked."""
    # Given a merge, revert or fixup commit message without a record
    message = _message(subject, "Body.")

    # When its problems are computed
    problems = records.message_problems(message)

    # Then there are none
    assert problems == []


def test_records_in_fenced_code_and_comments_are_ignored() -> None:
    """Quoted example records and git's comment lines do not count."""
    # Given a message whose only records are in fenced code and in a comment
    message = _message("docs: x", f"```text\n{RECORD}\n```", "# Wio-Work: k3m9xq")

    # When its records are read
    found = records.records(message)

    # Then none are found
    assert found == []


def test_a_paragraph_with_prose_is_not_a_record() -> None:
    """Every line of a record must be a trailer."""
    # Given a paragraph that starts with prose and ends with trailers
    message = _message("docs: x", f"Some prose.\n{RECORD}")

    # When the message's records are read
    found = records.records(message)

    # Then the paragraph is not a record
    assert found == []


def test_several_records_are_read_in_order() -> None:
    """A message can hold one record per paragraph."""
    # Given a message with a record for architecture, then one for wiring
    second = "Wio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: wiring"
    message = _message("docs: x", RECORD, second)

    # When its records are read
    found = records.records(message)

    # Then both are found, in the order of the message
    assert [dict(record)["Wio-Stage"] for record in found] == ["architecture", "wiring"]


def test_collect_keeps_records_of_works_and_drops_the_rest() -> None:
    """Only `Wio-*` fields of records that name a Work are collected."""
    # Given a commit with a record and a co-author, and a commit with no Work
    commits = [
        ("a1", _message("a", f"{RECORD}\nCo-Authored-By: A <a@example.com>")),
        ("b2", _message("b", "Wio-Work: none")),
    ]

    # When their records are collected
    collected = records.collect(commits)

    # Then only the first record's Wio-* fields remain
    assert collected == [RECORD]


def test_collect_leaves_out_reverted_commits() -> None:
    """A commit reverted later in the range keeps no record."""
    # Given a commit with a record and a later commit that reverts it
    commits = [
        ("c0ffee1234", _message("docs: a", RECORD)),
        ("deadbeef56", _message('Revert "docs: a"', "This reverts commit c0ffee1234.")),
    ]

    # When their records are collected
    collected = records.collect(commits)

    # Then the reverted commit's record is left out
    assert collected == []


def test_collect_restores_a_commit_whose_revert_is_reverted() -> None:
    """A revert of a revert brings the original record back."""
    # Given a commit, its revert, and a revert of that revert
    commits = [
        ("c0ffee1234", _message("docs: a", RECORD)),
        ("deadbeef56", _message('Revert "docs: a"', "This reverts commit c0ffee1234.")),
        ("f00dcafe78", _message('Revert "Revert"', "This reverts commit deadbeef56.")),
    ]

    # When their records are collected
    collected = records.collect(commits)

    # Then the original record counts again
    assert collected == [RECORD]


def test_outside_reverts_keeps_only_reverts_of_earlier_work() -> None:
    """A revert of a commit outside the range keeps its revert line."""
    # Given a revert of a commit from an earlier pull request, and a commit
    # reverted inside the range
    commits = [
        ("c0ffee1234", _message("docs: a", RECORD)),
        ("deadbeef56", _message('Revert "docs: a"', "This reverts commit c0ffee1234.")),
        ("f00dcafe78", _message('Revert "#28"', "This reverts commit 8a8ee78abc.")),
    ]

    # When the revert lines to copy are listed
    lines = records.outside_reverts(commits)

    # Then only the revert of the earlier work is kept
    assert lines == ["This reverts commit 8a8ee78abc."]


def test_with_records_keeps_revert_lines_once() -> None:
    """Revert lines go before the records and are not added twice."""
    # Given a body and a revert line to copy
    revert = "This reverts commit 8a8ee78abc."

    # When the records and revert lines are put at its end, once and again
    updated = records.with_records("## Outcome\n\nText.", [RECORD], [revert])
    again = records.with_records(updated, [RECORD], [revert])

    # Then the revert line comes once, before the record
    assert updated == f"## Outcome\n\nText.\n\n{revert}\n\n{RECORD}\n"
    assert again == updated


def test_with_records_replaces_the_records_at_the_end_of_a_body() -> None:
    """The body keeps its prose and gets exactly the given records."""
    # Given a pull request body with Windows line ends and an outdated record
    body = "## Outcome\r\n\r\nText.\r\n\r\nWio-Work: abcdef\r\nWio-Action: a"

    # When the current records are put at its end, once and then again
    updated = records.with_records(body, [RECORD])
    again = records.with_records(updated, [RECORD])

    # Then the outdated record is replaced, and a second pass changes nothing
    assert updated == f"## Outcome\n\nText.\n\n{RECORD}\n"
    assert again == updated


@pytest.mark.parametrize(
    ("paragraphs", "exit_code"), [(("docs: x", RECORD), 0), (("docs: x",), 1)]
)
def test_check_command_reads_a_message_file(
    tmp_path: Path, paragraphs: tuple[str, ...], exit_code: int
) -> None:
    """The commit-msg hook passes the message file and gets the exit code."""
    # Given a message file, with or without a record
    path = tmp_path / "COMMIT_EDITMSG"
    path.write_text(_message(*paragraphs), encoding="utf-8")

    # When the check command reads it
    code = records.main(["check", str(path)])

    # Then it exits with 0 for a record and 1 without one
    assert code == exit_code


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


@pytest.mark.slow
def test_commits_command_only_warns_about_a_missing_record(repo: Path) -> None:
    """A commit made outside the hook, without a record, does not fail CI."""
    # Given a commit without a record
    _commit(repo, _message("docs: no record"))

    # When the commits command checks it
    code = records.main(["commits", "HEAD~1..HEAD"])

    # Then it succeeds
    assert code == 0


@pytest.mark.slow
def test_commits_command_fails_on_a_malformed_record(repo: Path) -> None:
    """A record that is there but malformed fails CI."""
    # Given a commit whose record names a Work but no action or stage
    _commit(repo, _message("docs: bad", "Wio-Work: k3m9xq"))

    # When the commits command checks it
    code = records.main(["commits", "HEAD~1..HEAD"])

    # Then it fails
    assert code == 1


@pytest.mark.slow
def test_body_command_appends_the_commits_records(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The body gets the records of the range's commits, oldest first."""
    # Given a commit with a record and a pull request body without one
    _commit(repo, _message("docs: a", RECORD))
    monkeypatch.setattr("sys.stdin", io.StringIO("## Outcome\n\nText."))

    # When the body command updates the body
    code = records.main(["body", "HEAD~1..HEAD"])

    # Then it prints the body with the record at its end
    assert code == 0
    assert capsys.readouterr().out == f"## Outcome\n\nText.\n\n{RECORD}\n"


@pytest.mark.slow
def test_body_command_prints_nothing_when_the_body_is_current(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A body that already ends with the records needs no edit."""
    # Given a commit with a record and a body that ends with it, with CRLF line ends
    _commit(repo, _message("docs: a", RECORD))
    record = RECORD.replace("\n", "\r\n")
    monkeypatch.setattr("sys.stdin", io.StringIO(f"## Outcome\r\n\r\n{record}"))

    # When the body command updates the body
    code = records.main(["body", "HEAD~1..HEAD"])

    # Then it prints nothing, so the workflow does not edit the pull request
    assert code == 0
    assert not capsys.readouterr().out
