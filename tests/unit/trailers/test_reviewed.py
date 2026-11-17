# SPDX-License-Identifier: Apache-2.0
"""Tests of the finder of the commit a gate reviewed, run with a fake history.

Each test is a stub for one scenario of the Work that builds the finder, and
skips until the implementation stage fills it in. The examples use the gate
`review-contract` of the action `define`, a Work `k3m9xq`, and a history whose
commits are numbered from the oldest, so that `c1` is the oldest and the highest
number is `HEAD`. A gate record is the record of `k3m9xq` with
`Wio-Action: define`, `Wio-Stage: review-contract` and `Wio-Result: pass`, and the
reader is `scan` unless a scenario says otherwise.
"""

import pytest

STUB = "filled in by the implementation stage"


def test_pure_gate_commits_above_the_work_commit_are_skipped() -> None:
    """AC-1: `c3` and `c2` carry only a gate record, so `c1` is returned."""
    # Given `c3` and `c2` that carry only a gate record, and `c1`, the work commit,
    # that carries the record `Wio-Work: k3m9xq`, `Wio-Action: define` and
    # `Wio-Stage: define`
    # When `reviewed_commit("define", "review-contract", ...)` runs
    # Then it returns the full id of `c1`
    pytest.skip(STUB)


def test_a_commit_that_is_pure_for_other_works_is_skipped() -> None:
    """AC-1: a gate record for `a7b2c4, b8c9d0` is still the gate's own."""
    # Given `c2` whose record is for `Wio-Work: a7b2c4, b8c9d0` with
    # `Wio-Action: define` and `Wio-Stage: review-contract`, and `c1` as above
    # When `reviewed_commit` runs
    # Then it returns the full id of `c1`, whichever Works the gate is for
    pytest.skip(STUB)


def test_another_record_beside_the_gate_s_holds_the_artifact() -> None:
    """AC-2: `c2` carries the gate record and a work record, so it is returned."""
    # Given `c2` that carries the gate record and also the record `Wio-Work:
    # k3m9xq`, `Wio-Action: define` and `Wio-Stage: define`, and `c1` below it
    # When `reviewed_commit` runs
    # Then it returns the full id of `c2`
    pytest.skip(STUB)


def test_a_commit_with_no_record_is_not_skipped() -> None:
    """AC-2: `c3` is the gate's, `c2` has no record, so `c2` is returned."""
    # Given `c3` that carries the gate record, `c2` with no record, and `c1`
    # When `reviewed_commit` runs
    # Then it returns the full id of `c2`
    pytest.skip(STUB)


def test_a_record_of_no_work_is_not_skipped() -> None:
    """AC-2: `Wio-Work: none` belongs to no gate, so `c2` is returned."""
    # Given `c2` whose only record is `Wio-Work: none`, and `c1` below it
    # When `reviewed_commit` runs
    # Then it returns the full id of `c2`
    pytest.skip(STUB)


@pytest.mark.parametrize("history", ["only gate commits", "no commit"])
def test_a_history_with_no_work_commit_has_no_reviewed_commit(history: str) -> None:
    """AC-3: `None` for a history of pure gate commits and for an empty one."""
    # Given a history of commits that each carry only a gate record, and a history
    # of no commit
    # When `reviewed_commit` runs on each
    # Then it returns `None` for each
    pytest.skip(f"{STUB}: {history}")


def test_a_record_the_reader_cannot_see_does_not_make_a_gate_commit() -> None:
    """AC-4: under `git`, a gate record before a trailing paragraph is invisible."""
    # Given `c2` whose message holds a gate record, a blank line and then the
    # paragraph `Co-authored-by: A <a@example.com>`, and `c1` below it, read with
    # the `git` reader
    # When `reviewed_commit` runs
    # Then it returns the full id of `c2`, whose record the reader cannot see
    pytest.skip(STUB)
