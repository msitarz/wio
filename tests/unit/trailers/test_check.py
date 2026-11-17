# SPDX-License-Identifier: Apache-2.0
"""Tests of the commit-time check of `wio trailers`, run with fakes of its ports.

Each test is a stub for one scenario of the Work that builds the check, and skips
until the implementation stage fills it in. The examples use a Work `k3m9xq` in the
index with an item `AC-1`, a leaf whose `deliver` is the `typed-boundary` stage
preset, which lists `architecture`, which is not a gate, and `architecture-review`,
which is a gate. The config also has the stage `integration`, which is not a gate
and which that preset does not list, its results are `pass`, `fail` and `unknown`
and its reader is `scan` unless a scenario says otherwise. R is the paragraph
`Wio-Work: k3m9xq`, `Wio-Action: deliver` and `Wio-Stage: architecture`, and M is
the subject `feat: add x`, a blank line and R, so R's lines are 3 to 5.
"""

import pytest

STUB = "filled in by the implementation stage"


def test_a_message_from_a_file_and_from_standard_input_gives_one_diagnostic() -> None:
    """AC-1: the same `error: 5:` line from both inputs."""
    # Given M with `Wio-Stage: nosuch`, in a file and on standard input
    # When `check --require <file>` and `check --require -` read it
    # Then each exits 1 and prints on standard error the same diagnostic, which
    # begins `error: 5:` and names the stage
    pytest.skip(STUB)


def test_a_message_with_no_path_is_read_from_standard_input() -> None:
    """AC-1: `check --require` alone."""
    # Given the same message on standard input
    # When `check --require` runs with no path
    # Then it exits 1 and prints the same diagnostic
    pytest.skip(STUB)


def test_a_file_that_cannot_be_read_is_a_usage_error() -> None:
    """AC-1: a path that does not exist."""
    # Given a path that does not exist
    # When `check --require <path>` runs
    # Then the command exits 2, through the usage error
    pytest.skip(STUB)


def test_a_valid_record_and_a_record_of_no_work_pass() -> None:
    """AC-2: M, and a paragraph `Wio-Work: none`, print nothing."""
    # Given M, and a message of the subject `feat: add x` and a paragraph
    # `Wio-Work: none`
    # When `check --require` reads each
    # Then each exits 0 and prints nothing
    pytest.skip(STUB)


def test_a_list_of_two_valid_works_passes() -> None:
    """AC-2: `k3m9xq, a7b2c4`."""
    # Given a second Work `a7b2c4` in the index with an item `AC-1` whose `deliver`
    # action lists `architecture`, and M with `Wio-Work: k3m9xq, a7b2c4`
    # When `check --require` reads it
    # Then the command exits 0 and prints nothing
    pytest.skip(STUB)


def test_an_action_or_a_stage_the_config_lacks_is_an_error() -> None:
    """AC-3: `nosuch` is named."""
    # Given M with `Wio-Action: nosuch`, and M with `Wio-Stage: nosuch`
    # When `check --require` reads each
    # Then each exits 1 and names the unknown name
    pytest.skip(STUB)


def test_a_work_that_exists_nowhere_is_an_error() -> None:
    """AC-4: `zz9zz9` is in neither the index nor `HEAD`."""
    # Given M with `Wio-Work: zz9zz9`
    # When `check --require` reads it
    # Then the command exits 1 and names `zz9zz9`
    pytest.skip(STUB)


def test_a_work_that_the_commit_deletes_is_found_in_head() -> None:
    """AC-4: `d4e5f6` is in `HEAD` and not in the index."""
    # Given M with `Wio-Work: d4e5f6`, whose `deliver` lists `architecture`
    # When `check --require` reads it
    # Then the command exits 0
    pytest.skip(STUB)


def test_an_item_id_outside_the_work_is_an_error() -> None:
    """AC-4: `AC-99` for `k3m9xq` and for `d4e5f6`."""
    # Given M with `Wio-Items: AC-99`, and the same for M with `Wio-Work: d4e5f6`
    # When `check --require` reads each
    # Then each exits 1 and names `AC-99`
    pytest.skip(STUB)


def test_a_list_with_one_work_that_does_not_exist_is_an_error() -> None:
    """AC-4: `k3m9xq, zz9zz9`."""
    # Given M with `Wio-Work: k3m9xq, zz9zz9`
    # When `check --require` reads it
    # Then the command exits 1 and names `zz9zz9`
    pytest.skip(STUB)


def test_a_gate_without_a_result_is_an_error() -> None:
    """AC-5: a result is required."""
    # Given M with `Wio-Stage: architecture-review` and no `Wio-Result`
    # When `check --require` reads it
    # Then the command exits 1 and reports that a result is required
    pytest.skip(STUB)


def test_a_result_on_a_stage_that_is_not_a_gate_is_an_error() -> None:
    """AC-5: the stage is not a gate."""
    # Given M with `Wio-Result: pass`
    # When `check --require` reads it
    # Then the command exits 1 and reports that the stage is not a gate
    pytest.skip(STUB)


def test_a_result_the_config_does_not_list_is_an_error() -> None:
    """AC-5: `maybe` on a gate."""
    # Given M with `Wio-Stage: architecture-review` and `Wio-Result: maybe`
    # When `check --require` reads it
    # Then the command exits 1 and names `maybe`
    pytest.skip(STUB)


def test_a_message_with_no_record_is_refused_on_line_one() -> None:
    """AC-6: a subject with no record, and an empty message."""
    # Given a message with the subject `feat: add x` and no record, and an empty
    # message
    # When `check --require` reads each
    # Then each exits 1 and reports on line 1 that no record was found
    pytest.skip(STUB)


@pytest.mark.parametrize("subject", ["Merge", "Revert", "Reapply", "fixup!", "squash!"])
def test_a_subject_that_git_writes_needs_no_record(subject: str) -> None:
    """AC-6: each of the five, followed by a space."""
    # Given a message with no record whose subject starts with the word and a space
    # When `check --require` reads it
    # Then it exits 0
    pytest.skip(f"{STUB}: {subject}")


def test_the_subject_is_the_first_line_that_is_not_a_comment() -> None:
    """AC-6: `# comment` before `Merge branch x`, and before `feat: add x`."""
    # Given a message of the line `# comment` and then `Merge branch x`, and a
    # message of the line `# comment` and then `feat: add x`, neither with a record
    # When `check --require` reads each
    # Then the first exits 0 and the second exits 1 and reports that no record was
    # found
    pytest.skip(STUB)


@pytest.mark.parametrize("subject", ["amend! x", "fixup!x", "Merged x"])
def test_a_subject_that_only_looks_like_one_needs_a_record(subject: str) -> None:
    """AC-6: three subjects that git does not write."""
    # Given a message with no record whose subject is `amend! x`, `fixup!x` or
    # `Merged x`
    # When `check --require` reads it
    # Then it exits 1 and reports that no record was found
    pytest.skip(f"{STUB}: {subject}")


def test_an_exempt_subject_with_a_malformed_record_is_still_refused() -> None:
    """AC-6: the exemption is only from the requirement."""
    # Given a message with the subject `Merge branch x`, a blank line and R with
    # `Wio-Work: k3 m9xq`
    # When `check --require` reads it
    # Then the command exits 1 and reports line 3, the record's `Wio-Work` line
    pytest.skip(STUB)


def test_a_malformed_or_invisible_record_is_an_error() -> None:
    """AC-7: line 3, and lines 3, 4 and 5 with no record found."""
    # Given M with `Wio-Work: k3 m9xq`, and M with the prose line `Fixes the login
    # bug` added as line 6 of R's paragraph
    # When `check --require` reads each
    # Then the first exits 1 and reports line 3, and the second exits 1 and reports
    # lines 3, 4 and 5 as records the reader cannot see, and that no record was found
    pytest.skip(STUB)


def test_a_record_outside_the_last_paragraph_is_invisible_under_git() -> None:
    """AC-7: with the reader `git`."""
    # Given the config's reader is `git`, and a message of M, a blank line and a
    # second record of R's form
    # When `check --require` reads it
    # Then the command exits 1 and reports lines 3, 4 and 5 as records the reader
    # cannot see
    pytest.skip(STUB)


def test_any_bad_record_of_a_message_is_an_error() -> None:
    """AC-7: the second record's `Wio-Stage` on line 9."""
    # Given a message of M, a blank line and a second record of R's form with
    # `Wio-Stage: nosuch`, which makes its `Wio-Stage` line 9
    # When `check --require` reads it
    # Then the command exits 1 and reports line 9
    pytest.skip(STUB)


def test_an_unknown_key_is_a_warning() -> None:
    """AC-7: `Wio-Criteria` is warned about and the exit code is 0."""
    # Given M with a `Wio-Criteria: AC-1` line
    # When `check --require` reads it
    # Then the command exits 0 and warns about `Wio-Criteria`
    pytest.skip(STUB)


def test_a_stage_outside_the_pipeline_is_a_warning() -> None:
    """AC-8: `integration`."""
    # Given M with `Wio-Stage: integration`
    # When `check --require` reads it
    # Then the command exits 0 and warns about `integration`
    pytest.skip(STUB)
