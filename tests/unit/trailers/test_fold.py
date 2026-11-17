# SPDX-License-Identifier: Apache-2.0
"""Tests of the fold form of `wio trailers`, run with fakes of its ports.

Each test is a stub for one scenario of the Work that builds the fold, and skips
until the implementation stage fills it in. A range is a list of commits, oldest
first, each with a message that may hold one or more records.
"""

import pytest

STUB = "filled in by the implementation stage"


def test_consecutive_records_of_one_work_and_stage_become_one() -> None:
    """AC-1: two commits of one stage, the items united and the result latest."""
    # Given two consecutive commits with no other record between them, whose
    # records are for Work `a`, action `deliver` and stage `implementation`, the
    # first with items `AC-1` and result `fail`, the second with items `AC-2` and
    # result `pass`
    # When `wio trailers fold block` runs on the range
    # Then it prints one record for `a` with items `AC-1, AC-2` and the result
    # `pass`
    pytest.skip(STUB)


def test_neighbors_that_differ_only_in_the_work_become_one_list() -> None:
    """AC-2: the same record for two Works."""
    # Given consecutive commits whose records for Works `a` and `b` have the same
    # action, stage, items, result and judge
    # When `wio trailers fold block` runs on the range
    # Then it prints one record whose `Wio-Work` is `a, b` and whose other fields
    # are those of the two records
    pytest.skip(STUB)


def test_a_record_between_two_others_keeps_them_apart() -> None:
    """AC-3: a re-delivered child after its parent's integration."""
    # Given a range whose records are, in order, child `a` delivering
    # `implementation`, parent `p` integrating, and `a` delivering
    # `implementation` again
    # When `wio trailers fold block` runs on the range
    # Then it prints three records in that order
    pytest.skip(STUB)


def test_a_commit_reverted_in_the_range_leaves_no_record() -> None:
    """AC-4: neither the reverted record nor one for the revert is printed."""
    # Given a commit with a record and a later commit in the range that reverts it
    # When `wio trailers fold block` runs on the range
    # Then the record of the reverted commit is not printed, and no record is
    # printed for the revert
    pytest.skip(STUB)


def test_a_revert_of_a_revert_restores_the_record() -> None:
    """AC-4: the first commit's record is printed again."""
    # Given a commit with a record, a revert of it, and a revert of that revert,
    # all in the range
    # When `wio trailers fold block` runs on the range
    # Then the record of the first commit is printed
    pytest.skip(STUB)


def test_a_revert_of_work_outside_the_range_stays_visible_in_a_body() -> None:
    """AC-5: the revert paragraph and then the folded records, each its own."""
    # Given the body `Fix the bug.` and a commit in the range that reverts a commit
    # `1234567` outside it
    # When `wio trailers fold body <range>` runs on that body
    # Then the printed body is `Fix the bug.`, a paragraph
    # `This reverts commit 1234567.`, and then the folded records, each as its own
    # paragraph
    pytest.skip(STUB)


def test_a_revert_of_work_outside_the_range_stays_visible_in_a_block() -> None:
    """AC-5: the paragraph and then the folded records."""
    # Given the same range
    # When `wio trailers fold block <range>` runs
    # Then it prints the paragraph `This reverts commit 1234567.` and then the
    # folded records
    pytest.skip(STUB)


def test_a_body_without_the_records_gets_them_at_its_end() -> None:
    """AC-6: the prose is unchanged, a blank line and the folded records follow."""
    # Given a body of prose and a range with records
    # When `wio trailers fold body` runs on the body and the range
    # Then it prints the prose, a blank line and the folded records, and the prose
    # is unchanged
    pytest.skip(STUB)


def test_a_body_that_ends_with_older_records_has_them_replaced() -> None:
    """AC-6: a record paragraph inside the prose stays, the trailing one goes."""
    # Given a body of prose that holds a record paragraph, and that ends with a
    # record of the range's earlier state
    # When `wio trailers fold body` runs on it
    # Then the printed body ends with the current folded records, holds the
    # trailing older one no longer, and keeps the record paragraph inside the prose
    pytest.skip(STUB)


def test_a_body_that_already_has_them_prints_nothing() -> None:
    """AC-7: folding twice."""
    # Given the body that `wio trailers fold body` printed for a range
    # When `wio trailers fold body` runs on that body and the same range
    # Then it prints nothing
    pytest.skip(STUB)


def test_a_listed_work_folds_like_a_single_one_and_none_prints_nothing() -> None:
    """AC-8: `a, b` is `a` and then `b`, and `none` is dropped."""
    # Given a commit whose record has `Wio-Work: a, b`, and a commit whose record
    # has `Wio-Work: none`
    # When `wio trailers fold block` runs on the range
    # Then the first prints as it would for one record of `a` and then one of `b`,
    # in that order, and the second prints nothing
    pytest.skip(STUB)


def test_a_range_that_does_not_resolve_prints_nothing() -> None:
    """AC-9: each form raises `TrailersError`, which exits 2, and writes nothing."""
    # Given a range whose revision does not exist
    # When `wio trailers fold block <range>` and `wio trailers fold body <range>`
    # run
    # Then each exits 2 and prints nothing
    pytest.skip(STUB)
