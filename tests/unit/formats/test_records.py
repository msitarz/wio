# SPDX-License-Identifier: Apache-2.0
"""Tests of the reader and the shape check of records in `wio.formats`.

Each test is a stub for one criterion of the Work that builds them, and skips
until the implementation stage fills it in.
"""

import pytest

STUB = "filled in by the implementation stage"


def test_a_valid_message_has_no_finding() -> None:
    """AC-1: valid records of every form, no record and a fenced example."""
    # Given messages of R in every valid form, with no record, and with only a
    # fenced example
    # When `check_shape` reads each with the `scan` reader
    # Then it returns no finding for any
    pytest.skip(STUB)


def test_the_work_value_is_judged() -> None:
    """AC-2: an invalid id, an invalid list and a record with no Work."""
    # Given R with `k3 m9xq`, `none, k3m9xq` and `k3m9xq, k3m9xq`, and a record
    # with no `Wio-Work`
    # When `check_shape` reads each
    # Then it returns one `malformed` finding for each, with the key `Wio-Work`
    pytest.skip(STUB)


def test_the_other_keys_are_judged() -> None:
    """AC-3: a missing key, a forbidden key, a repeated key and a lone judge."""
    # Given R without `Wio-Stage`, `none` with a stage, a second `Wio-Stage`
    # and a judge with no result
    # When `check_shape` reads each
    # Then it returns one `malformed` finding for each, with the key at fault
    pytest.skip(STUB)


def test_the_values_are_judged_by_their_form_only() -> None:
    """AC-4: a wrong form is malformed, a name the config may not list is not."""
    # Given R with a badly formed stage, action, result, judge and items, and R
    # with `nosuch` and `maybe`
    # When `check_shape` reads each with the `scan` reader
    # Then the first five give one `malformed` finding each and the last two
    # none
    pytest.skip(STUB)


def test_an_unknown_key_is_a_finding_of_its_own() -> None:
    """AC-5: `Wio-Criteria` is `unknown-key`, and a `none` record also breaks."""
    # Given R with a `Wio-Criteria` line, and `Wio-Work: none` with the same
    # line
    # When `check_shape` reads each with the `scan` reader
    # Then the first gives one `unknown-key` finding, and the second also one
    # `malformed` finding for the forbidden key
    pytest.skip(STUB)


def test_a_line_the_reader_cannot_see_is_found() -> None:
    """AC-6: prose in a paragraph under `scan`, an early record under `git`."""
    # Given a paragraph of R and a prose line, and R followed by a later record
    # When `check_shape` reads them with the `scan` and the `git` reader
    # Then it returns one `invisible` finding for each `Wio-` line not seen
    pytest.skip(STUB)


def test_findings_say_what_is_wrong_and_where() -> None:
    """AC-7: line numbers, non-empty messages and the order of the message."""
    # Given a message with a body paragraph and R with bad items and an unknown
    # key
    # When `check_shape` reads it with the `scan` reader
    # Then the `malformed` and `unknown-key` findings come in that order, each
    # with its 1-based line number and a non-empty message
    pytest.skip(STUB)


def test_the_scan_reader_decides_what_is_a_record() -> None:
    """AC-8: only the middle record is read, with no rejected line."""
    # Given R in the middle, another in a fenced block and a `# Wio-Work` line
    # When `read` reads it with the `scan` reader
    # Then the `Reading` holds R alone with line numbers and no rejected line
    pytest.skip(STUB)


def test_the_git_reader_decides_what_is_a_record() -> None:
    """AC-8: R before a `Co-authored-by` paragraph is rejected, not read."""
    # Given R, a blank line and a `Co-authored-by` paragraph
    # When `read` reads it with the `git` reader
    # Then the `Reading` holds no record and the three `Wio-` lines of R as
    # rejected lines
    pytest.skip(STUB)
