# SPDX-License-Identifier: Apache-2.0
"""Tests of the commit-time check of `wio trailers`, run with fakes of its ports.

The examples use a Work `k3m9xq` in the index with an item `AC-1`, a leaf whose
`deliver` is the `typed-boundary` stage preset, which lists `architecture`, which is
not a gate, and `architecture-review`, which is a gate. The config also has the stage
`integration`, which is not a gate and which that preset does not list, its results
are `pass`, `fail` and `unknown` and its reader is `scan` unless a scenario says
otherwise. R is the paragraph `Wio-Work: k3m9xq`, `Wio-Action: deliver` and
`Wio-Stage: architecture`, and M is the subject `feat: add x`, a blank line and R, so
R's lines are 3 to 5.
"""

import io
from argparse import ArgumentParser
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING, cast, override

import pytest

from tests.unit.fakes import FakeStdio, MemoryFileSystem
from tests.unit.trailers.test_validation import CONFIG, FakeContracts
from wio.models.config import Config, Trailers
from wio.trailers import Services
from wio.trailers.check import (
    check_commit_message,
    configure_check,
    has_exempt_subject,
    run_check,
)
from wio.trailers.errors import TrailersError

if TYPE_CHECKING:
    from wio.io.ports import FileSystem, History

R = "Wio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: architecture"
M = f"feat: add x\n\n{R}"
GIT_CONFIG = replace(CONFIG, trailers=Trailers(reader="git"))


@dataclass(frozen=True)
class WorkingTree(FakeContracts):
    """The `Contracts` port over the working tree, which lacks `d4e5f6`."""

    @override
    def items(self, work_id: str) -> frozenset[str] | None:
        """Find the items of a Work, none for `d4e5f6`.

        Args:
            work_id: The Work's id.

        Returns:
            Its items, or `None` for a Work that the working tree lacks.
        """
        return None if work_id == "d4e5f6" else super().items(work_id)


@dataclass(frozen=True)
class Settings:
    """The `Settings` port, loading a fixed config."""

    config: Config = CONFIG

    def load(self) -> Config:
        """Load the config.

        Returns:
            The config the fake was given.
        """
        return self.config


def _run(
    message: str,
    *,
    path: str | None = None,
    files: dict[Path, str] | None = None,
    config: Config = CONFIG,
) -> tuple[int, str]:
    """Run the check on a message given on standard input or in a file.

    Args:
        message: The commit message, which standard input holds.
        path: The path argument, or `None` for none.
        files: The files of the file system, by path.
        config: The config the settings load.

    Returns:
        The exit code and what was written to standard error.
    """
    parser = ArgumentParser(prog="wio trailers check")
    configure_check(parser)
    args = parser.parse_args([*([path] if path is not None else []), "--require"])
    out, err = io.StringIO(), io.StringIO()
    services = Services(
        Settings(config),
        WorkingTree(),
        cast("History", object()),
        FakeContracts(),
        cast("FileSystem", MemoryFileSystem(files or {})),
    )
    code = run_check(services, args, FakeStdio(io.StringIO(message), out, err))
    assert out.getvalue() == ""
    return code, err.getvalue()


def _messages(*, stage: str = "architecture", extra: str = "") -> str:
    """Write M with another stage and extra lines in R's paragraph.

    Args:
        stage: The `Wio-Stage` value.
        extra: Lines added to R's paragraph.

    Returns:
        The message.
    """
    paragraph = f"Wio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: {stage}{extra}"
    return f"feat: add x\n\n{paragraph}"


def test_a_message_from_a_file_and_from_standard_input_gives_one_diagnostic() -> None:
    """AC-1: the same `error: 5:` line from both inputs."""
    # Given M with `Wio-Stage: nosuch`, in a file and on standard input
    bad = _messages(stage="nosuch")

    # When `check --require <file>` and `check --require -` read it
    from_file = _run("", path="msg.txt", files={Path("msg.txt"): bad})
    from_stdin = _run(bad, path="-")

    # Then each exits 1 and prints the same diagnostic, which begins `error: 5:` and
    # names the stage
    assert from_file == from_stdin
    assert from_file[0] == 1
    assert from_file[1].startswith("error: 5:")
    assert "nosuch" in from_file[1]


def test_a_message_with_no_path_is_read_from_standard_input() -> None:
    """AC-1: `check --require` alone."""
    # Given the same message on standard input
    # When `check --require` runs with no path
    code, err = _run(_messages(stage="nosuch"))

    # Then it exits 1 and prints the same diagnostic
    assert code == 1
    assert err.startswith("error: 5:")


def test_a_file_that_cannot_be_read_is_a_usage_error() -> None:
    """AC-1: a path that does not exist."""
    # Given a path that does not exist
    # When `check --require <path>` runs
    # Then it raises a `TrailersError`, which exits 2
    with pytest.raises(TrailersError):
        _run("", path="nope.txt")


def test_the_option_require_is_required_until_the_later_check_adds_its_mode() -> None:
    """The form of this leaf is the commit-time mode only."""
    # Given the parser of the check form
    parser = ArgumentParser(prog="wio trailers check")
    configure_check(parser)

    # When it parses a call without `--require`
    # Then argparse refuses it with the usage error 2
    with pytest.raises(SystemExit) as caught:
        parser.parse_args(["msg.txt"])
    assert caught.value.code == 2


@pytest.mark.parametrize(
    "message", [M, "feat: add x\n\nWio-Work: none"], ids=["record", "none"]
)
def test_a_valid_record_and_a_record_of_no_work_pass(message: str) -> None:
    """AC-2: M, and a paragraph `Wio-Work: none`, print nothing."""
    # Given a valid message
    # When `check --require` reads it
    code, err = _run(message)

    # Then it exits 0 and prints nothing
    assert (code, err) == (0, "")


def test_a_list_of_two_valid_works_passes() -> None:
    """AC-2: `k3m9xq, a7b2c4`."""
    # Given a second Work `a7b2c4` in the index and M with `Wio-Work: k3m9xq, a7b2c4`
    message = M.replace("k3m9xq", "k3m9xq, a7b2c4")

    # When `check --require` reads it
    code, err = _run(message)

    # Then the command exits 0 and prints nothing
    assert (code, err) == (0, "")


@pytest.mark.parametrize(
    "message", [M.replace("deliver", "nosuch"), _messages(stage="nosuch")]
)
def test_an_action_or_a_stage_the_config_lacks_is_an_error(message: str) -> None:
    """AC-3: `nosuch` is named."""
    # Given M with `Wio-Action: nosuch`, or M with `Wio-Stage: nosuch`
    # When `check --require` reads it
    code, err = _run(message)

    # Then it exits 1 and names the unknown name
    assert code == 1
    assert "nosuch" in err


def test_a_work_that_exists_nowhere_is_an_error() -> None:
    """AC-4: `zz9zz9` is in neither the index nor `HEAD`."""
    # Given M with `Wio-Work: zz9zz9`
    # When `check --require` reads it
    code, err = _run(M.replace("k3m9xq", "zz9zz9"))

    # Then the command exits 1 and names `zz9zz9`
    assert code == 1
    assert "zz9zz9" in err


def test_a_work_that_the_commit_deletes_is_found_in_head() -> None:
    """AC-4: `d4e5f6` is in `HEAD` and not in the index."""
    # Given M with `Wio-Work: d4e5f6`, whose `deliver` lists `architecture`
    # When `check --require` reads it
    code, err = _run(M.replace("k3m9xq", "d4e5f6"))

    # Then the command exits 0
    assert (code, err) == (0, "")


@pytest.mark.parametrize("work", ["k3m9xq", "d4e5f6"])
def test_an_item_id_outside_the_work_is_an_error(work: str) -> None:
    """AC-4: `AC-99` for `k3m9xq` and for `d4e5f6`."""
    # Given M with `Wio-Items: AC-99`, for each Work
    # When `check --require` reads it
    code, err = _run(_messages().replace("k3m9xq", work) + "\nWio-Items: AC-99")

    # Then it exits 1 and names `AC-99`
    assert code == 1
    assert "AC-99" in err


def test_a_list_with_one_work_that_does_not_exist_is_an_error() -> None:
    """AC-4: `k3m9xq, zz9zz9`."""
    # Given M with `Wio-Work: k3m9xq, zz9zz9`
    # When `check --require` reads it
    code, err = _run(M.replace("k3m9xq", "k3m9xq, zz9zz9"))

    # Then the command exits 1 and names `zz9zz9`
    assert code == 1
    assert "zz9zz9" in err


@pytest.mark.parametrize(
    ("message", "words"),
    [
        (_messages(stage="architecture-review"), "result required"),
        (M + "\nWio-Result: pass", "not a gate"),
        (_messages(stage="architecture-review") + "\nWio-Result: maybe", "maybe"),
    ],
    ids=["missing", "stray", "unlisted"],
)
def test_a_result_must_be_present_exactly_on_a_gate_and_listed(
    message: str, words: str
) -> None:
    """AC-5: a result is required, the stage is not a gate, `maybe` is named."""
    # Given a gate without a result, a result on a stage that is no gate, and a
    # result the config does not list
    # When `check --require` reads each
    code, err = _run(message)

    # Then it exits 1 and says so
    assert code == 1
    assert words in err


@pytest.mark.parametrize("message", ["feat: add x", ""], ids=["subject", "empty"])
def test_a_message_with_no_record_is_refused_on_line_one(message: str) -> None:
    """AC-6: a subject with no record, and an empty message."""
    # Given a message with no record
    # When `check --require` reads it
    code, err = _run(message)

    # Then it exits 1 and reports on line 1 that no record was found
    assert code == 1
    assert err.startswith("error: 1:")
    assert "no record was found" in err


@pytest.mark.parametrize("subject", ["Merge", "Revert", "Reapply", "fixup!", "squash!"])
def test_a_subject_that_git_writes_needs_no_record(subject: str) -> None:
    """AC-6: each of the five, followed by a space."""
    # Given a message with no record whose subject starts with the word and a space
    # When `check --require` reads it
    code, err = _run(f"{subject} x")

    # Then it exits 0
    assert (code, err) == (0, "")


def test_the_subject_is_the_first_line_that_is_not_a_comment() -> None:
    """AC-6: `# comment` before `Merge branch x`, and before `feat: add x`."""
    # Given two messages with a comment line before the subject, with no record
    merge = _run("# comment\nMerge branch x")
    feature = _run("# comment\nfeat: add x")

    # When `check --require` reads each
    # Then the first exits 0 and the second exits 1 and reports that no record was
    # found
    assert merge == (0, "")
    assert feature[0] == 1
    assert "no record was found" in feature[1]


@pytest.mark.parametrize("subject", ["amend! x", "fixup!x", "Merged x"])
def test_a_subject_that_only_looks_like_one_needs_a_record(subject: str) -> None:
    """AC-6: three subjects that git does not write."""
    # Given a message with no record whose subject only looks like one
    # When `check --require` reads it
    code, err = _run(subject)

    # Then it exits 1 and reports that no record was found
    assert code == 1
    assert "no record was found" in err


def test_an_exempt_subject_with_a_malformed_record_is_still_refused() -> None:
    """AC-6: the exemption is only from the requirement."""
    # Given a message with the subject `Merge branch x` and R with `Wio-Work: k3 m9xq`
    message = M.replace("feat: add x", "Merge branch x").replace("k3m9xq", "k3 m9xq")

    # When `check --require` reads it
    code, err = _run(message)

    # Then the command exits 1 and reports line 3
    assert code == 1
    assert err.startswith("error: 3:")


def test_a_malformed_or_invisible_record_is_an_error() -> None:
    """AC-7: line 3, and lines 3, 4 and 5 with no record found."""
    # Given M with `Wio-Work: k3 m9xq`, and M with a prose line added to R's paragraph
    malformed = _run(M.replace("k3m9xq", "k3 m9xq"))
    invisible = _run(_messages(extra="\nFixes the login bug"))

    # When `check --require` reads each
    # Then the first exits 1 and reports line 3, and the second exits 1 and reports
    # lines 3, 4 and 5 as records the reader cannot see, and that no record was found
    assert malformed[0] == 1
    assert malformed[1].startswith("error: 3:")
    lines = [line.split(":")[1].strip() for line in invisible[1].splitlines()]
    assert (invisible[0], lines) == (1, ["1", "3", "4", "5"])
    assert "no record was found" in invisible[1].splitlines()[0]


def test_a_record_outside_the_last_paragraph_is_invisible_under_git() -> None:
    """AC-7: with the reader `git`."""
    # Given the config's reader is `git`, and M, a blank line and a second record
    message = f"{M}\n\n{R}"

    # When `check --require` reads it
    code, err = _run(message, config=GIT_CONFIG)

    # Then the command exits 1 and reports lines 3, 4 and 5 as records the reader
    # cannot see
    lines = [line.split(":")[1].strip() for line in err.splitlines()]
    assert (code, lines) == (1, ["3", "4", "5"])


def test_any_bad_record_of_a_message_is_an_error() -> None:
    """AC-7: the second record's `Wio-Stage` on line 9."""
    # Given M, a blank line and a second record with `Wio-Stage: nosuch`
    message = f"{M}\n\n{R.replace('architecture', 'nosuch')}"

    # When `check --require` reads it
    code, err = _run(message)

    # Then the command exits 1 and reports line 9
    assert code == 1
    assert err.startswith("error: 9:")


def test_an_unknown_key_is_a_warning() -> None:
    """AC-7: `Wio-Criteria` is warned about and the exit code is 0."""
    # Given M with a `Wio-Criteria: AC-1` line
    # When `check --require` reads it
    code, err = _run(_messages(extra="\nWio-Criteria: AC-1"))

    # Then the command exits 0 and warns about `Wio-Criteria`
    assert code == 0
    assert err.startswith("warning:")
    assert "Wio-Criteria" in err


def test_an_unknown_key_does_not_hide_a_bad_stage() -> None:
    """AC-7: the record with only a warning is still validated."""
    # Given M with a `Wio-Criteria: AC-1` line and `Wio-Stage: nosuch`
    # When `check --require` reads it
    code, err = _run(_messages(stage="nosuch", extra="\nWio-Criteria: AC-1"))

    # Then the command exits 1, names `nosuch` and warns about `Wio-Criteria`
    assert code == 1
    assert "nosuch" in err
    assert "warning:" in err


def test_diagnostics_are_sorted_by_line_as_numbers() -> None:
    """AC-1: line 9 comes before line 10."""
    # Given a message with a Work that does not exist on line 9 and an action that
    # the config lacks on line 10
    record = "Wio-Work: zz9zz9\nWio-Action: nosuch\nWio-Stage: architecture"
    message = f"feat: x\n\n{R}\n\nbody\n\n{record}\n"

    # When `check --require` reads it
    code, err = _run(message)

    # Then the diagnostic of line 9 is printed before that of line 10
    lines = [int(line.split(":")[1]) for line in err.splitlines()]
    assert (code, lines) == (1, [9, 10])


def test_a_record_of_no_work_is_not_judged_by_the_validator() -> None:
    """AC-2: `Wio-Work: none` has nothing to check."""
    # Given a message with the paragraph `Wio-Work: none`
    # When `check_commit_message` runs on it
    found = check_commit_message("feat: x\n\nWio-Work: none", FakeContracts(), CONFIG)

    # Then it returns no diagnostic
    assert found == []


def test_a_stage_outside_the_pipeline_is_a_warning() -> None:
    """AC-8: `integration`."""
    # Given M with `Wio-Stage: integration`
    # When `check --require` reads it
    code, err = _run(_messages(stage="integration"))

    # Then the command exits 0 and warns about `integration`
    assert code == 0
    assert err.startswith("warning:")
    assert "integration" in err


@pytest.mark.parametrize(
    ("message", "exempt"),
    [
        ("Merge x", True),
        ("# c\nRevert x", True),
        ("Merged x", False),
        ("", False),
        ("# only a comment", False),
        ("\nMerge x", False),
    ],
)
def test_the_exempt_subject_is_the_first_line_that_is_not_a_comment(
    message: str,
    exempt: bool,  # noqa: FBT001
) -> None:
    """A blank first line, or no subject at all, is not exempt."""
    # Given a message
    # When `has_exempt_subject` reads it
    # Then it says whether git wrote the subject
    assert has_exempt_subject(message) is exempt


def test_a_message_with_crlf_line_ends_is_read_like_one_with_lf() -> None:
    """The `#` line, the subject and the record are found with a carriage return."""
    # Given M and a merge message with a comment line, both with CRLF line ends
    valid = _run(M.replace("\n", "\r\n"))
    merge = _run("# c\r\nMerge x\r\n")

    # When `check --require` reads each
    # Then both exit 0 and print nothing
    assert valid == (0, "")
    assert merge == (0, "")


def test_a_record_in_a_fenced_block_is_not_read() -> None:
    """An example in a fence is no record, so the message has none."""
    # Given a message whose only record is in a fenced code block
    message = f"feat: x\n\n```\n{R}\n```"

    # When `check --require` reads it
    code, err = _run(message)

    # Then it exits 1 and reports that no record was found
    assert code == 1
    assert "no record was found" in err


def test_a_malformed_record_is_not_validated() -> None:
    """A repeated key makes the record malformed, so its other lines are not judged."""
    # Given R with a second `Wio-Stage` line and a stage the config lacks
    message = _messages(stage="nosuch", extra="\nWio-Stage: architecture")

    # When `check --require` reads it
    code, err = _run(message)

    # Then it exits 1 for the repeated key and does not name the stage
    assert code == 1
    assert "nosuch" not in err


@pytest.mark.parametrize("subject", ["Merge", "fixup!\tx"])
def test_a_subject_without_the_space_after_the_word_needs_a_record(
    subject: str,
) -> None:
    """The word must be followed by a space and not a tab or nothing."""
    # Given a message with no record whose subject lacks the space
    # When `check --require` reads it
    code, err = _run(subject)

    # Then it exits 1 and reports that no record was found
    assert code == 1
    assert "no record was found" in err
