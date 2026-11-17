# SPDX-License-Identifier: Apache-2.0
"""Tests of the later check of `wio trailers`, run with fakes of its ports.

Each test is a stub for one scenario of the Work that builds the later check, and
skips until the implementation stage fills it in. The examples use a body B of the
line `Fix the bug.`, a blank line and R, the paragraph `Wio-Work: k3m9xq`,
`Wio-Action: deliver` and `Wio-Stage: architecture`, so that R's lines are 3 to 5. A
range has the commits `c1`, `c2` and `c3` from the oldest, each of the message B. The
config's results are `pass`, `fail` and `unknown`, and its reader is `scan` unless a
scenario says otherwise.
"""

import pytest

STUB = "filled in by the implementation stage"


def test_a_body_from_a_file_and_from_standard_input_gives_one_diagnostic() -> None:
    """AC-1: the same `error: 3:` line from a file, `-` and no path."""
    # Given B with `Wio-Work: k3 m9xq`, in a file and on standard input
    # When `check <file>`, `check -` and `check` read it
    # Then each exits 1 and prints on standard error the same diagnostic, which
    # begins `error: 3:`
    pytest.skip(STUB)


@pytest.mark.parametrize(
    "case", ["no file", "path and range", "unknown range", "no repository"]
)
def test_inputs_that_cannot_be_read_are_usage_errors(case: str) -> None:
    """AC-1: each raises `TrailersError`, which exits 2."""
    # Given a path that does not exist, a call that gives a path and `--ref-range`, a
    # range `nosuch..nosuch2`, and a directory that is not in a repository
    # When `check <path>`, `check <path> --ref-range main..HEAD`, `check --ref-range
    # nosuch..nosuch2` and `check --ref-range main..HEAD` run in them
    # Then each raises a `TrailersError`
    pytest.skip(f"{STUB}: {case}")


def test_a_malformed_record_fails_a_body_and_a_range() -> None:
    """AC-2: `error: 3:` for the body, `error: <id of c2>:3:` for the range."""
    # Given B with `Wio-Work: k3 m9xq`, and a range whose `c2` has that message while
    # `c1` and `c3` are valid and `c3` also has an unknown name
    # When `check` reads the body and `--ref-range` reads the range
    # Then each exits 1, the body's diagnostic begins `error: 3:`, the range's begins
    # `error:` followed by the full id of `c2` and `:3:`, and the commits `c1` and
    # `c3` add no error
    pytest.skip(STUB)


@pytest.mark.parametrize("name", ["stage", "action", "result"])
def test_a_name_the_config_no_longer_has_is_a_warning(name: str) -> None:
    """AC-3: `nosuch`, `nosuch` and `maybe` are warned about, never refused."""
    # Given B with `Wio-Stage: nosuch`, B with `Wio-Action: nosuch`, and B with the
    # stage `architecture-review` and `Wio-Result: maybe`
    # When `check` reads each
    # Then each exits 0 and prints a `warning:` that names `nosuch`, `nosuch` and
    # `maybe`
    pytest.skip(f"{STUB}: {name}")


def test_a_work_that_was_deleted_is_not_looked_up() -> None:
    """AC-3: `d4e5f6` and `AC-99` print nothing."""
    # Given B with `Wio-Work: d4e5f6`, which is in no tree, and `Wio-Items: AC-99`
    # When `check` reads it
    # Then it exits 0 and prints nothing
    pytest.skip(STUB)


def test_a_line_the_reader_cannot_see_is_a_warning() -> None:
    """AC-4: prose in the paragraph under `scan`, a second paragraph under `git`."""
    # Given B whose paragraph also holds the prose line `Fixes the login bug`, with
    # the `scan` reader, and the range commit `c2` of that message with the `git`
    # reader and a blank line and a `Co-authored-by` paragraph after R
    # When `check` reads the body and `--ref-range` reads the range
    # Then each exits 0 and prints a `warning:` for each `Wio-` line that the reader
    # cannot see, at its line
    pytest.skip(STUB)


def test_a_name_the_engine_does_not_define_is_a_warning() -> None:
    """AC-4: `warning: 6:` names `Wio-Criteria`."""
    # Given B with a `Wio-Criteria: AC-1` line as line 6 of R's paragraph
    # When `check` reads it
    # Then it exits 0 and prints a `warning: 6:` that names `Wio-Criteria`
    pytest.skip(STUB)


@pytest.mark.parametrize("what", ["body", "commit", "empty range"])
def test_no_record_is_not_a_failure(what: str) -> None:
    """AC-5: a body, a commit and an empty range print nothing."""
    # Given a body of `Fix the bug.` alone, a range of one commit with that message,
    # and a range of no commit
    # When `check` reads the body and `--ref-range` reads each range
    # Then each exits 0 and prints nothing
    pytest.skip(f"{STUB}: {what}")
