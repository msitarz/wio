# SPDX-License-Identifier: Apache-2.0
"""Tests of the finder of the commit a gate reviewed, run with a fake history.

The examples use the gate `review-contract` of the action `define`, a Work
`k3m9xq`, and a history whose commits are numbered from the oldest, so that `c1`
is the oldest and the highest number is `HEAD`. A gate record is the record of
`k3m9xq` with `Wio-Action: define`, `Wio-Stage: review-contract` and
`Wio-Result: pass`, and the reader is `scan` unless a scenario says otherwise.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import pytest

from tests.unit.trailers.test_fold import _commit, _id
from wio.trailers.reviewed import reviewed_commit

if TYPE_CHECKING:
    from wio.io.ports import History
    from wio.models.commits import Commit
    from wio.models.config import Reader

PENDING = pytest.mark.xfail(
    raises=NotImplementedError, strict=True, reason="implementation stage"
)
GATE = (
    "Wio-Work: k3m9xq\nWio-Action: define\nWio-Stage: review-contract\nWio-Result: pass"
)
WORK = "Wio-Work: k3m9xq\nWio-Action: define\nWio-Stage: define"


@dataclass(frozen=True)
class FirstParents:
    """A `History` port over a line of commits, which gives them newest first."""

    commits: tuple[Commit, ...]

    def first_parents(self, revision: str) -> tuple[Commit, ...]:
        """List the commits, newest first.

        Args:
            revision: The revision, which must be `HEAD`.

        Returns:
            The commits from `HEAD` down.
        """
        assert revision == "HEAD"
        return tuple(reversed(self.commits))


def _find(*commits: Commit, reader: Reader = "scan") -> str | None:
    """Find the commit that the gate `review-contract` of `define` reviewed.

    Args:
        *commits: The commits of the history from the oldest.
        reader: The reader of the config.

    Returns:
        What `reviewed_commit` returns.
    """
    history = cast("History", FirstParents(commits))
    return reviewed_commit("define", "review-contract", history, reader)


@PENDING
def test_pure_gate_commits_above_the_work_commit_are_skipped() -> None:
    """AC-1: `c3` and `c2` carry only a gate record, so `c1` is returned."""
    # Given `c3` and `c2` that carry only a gate record, and `c1`, the work commit,
    # that carries the record `Wio-Work: k3m9xq`, `Wio-Action: define` and
    # `Wio-Stage: define`
    commits = (_commit(1, WORK), _commit(2, GATE), _commit(3, GATE))

    # When `reviewed_commit("define", "review-contract", ...)` runs
    found = _find(*commits)

    # Then it returns the full id of `c1`
    assert found == _id(1)


@PENDING
def test_a_commit_that_is_pure_for_other_works_is_skipped() -> None:
    """AC-1: a gate record for `a7b2c4, b8c9d0` is still the gate's own."""
    # Given `c2` whose record is for `Wio-Work: a7b2c4, b8c9d0` with
    # `Wio-Action: define` and `Wio-Stage: review-contract`, and `c1` as above
    others = GATE.replace("k3m9xq", "a7b2c4, b8c9d0")
    commits = (_commit(1, WORK), _commit(2, others))

    # When `reviewed_commit` runs
    found = _find(*commits)

    # Then it returns the full id of `c1`, whichever Works the gate is for
    assert found == _id(1)


@PENDING
def test_another_record_beside_the_gate_s_holds_the_artifact() -> None:
    """AC-2: `c2` carries the gate record and a work record, so it is returned."""
    # Given `c2` that carries the gate record and also the record `Wio-Work:
    # k3m9xq`, `Wio-Action: define` and `Wio-Stage: define`, and `c1` below it
    commits = (_commit(1, WORK), _commit(2, GATE, WORK))

    # When `reviewed_commit` runs
    found = _find(*commits)

    # Then it returns the full id of `c2`
    assert found == _id(2)


@PENDING
def test_a_commit_with_no_record_is_not_skipped() -> None:
    """AC-2: `c3` is the gate's, `c2` has no record, so `c2` is returned."""
    # Given `c3` that carries the gate record, `c2` with no record, and `c1`
    commits = (_commit(1, WORK), _commit(2), _commit(3, GATE))

    # When `reviewed_commit` runs
    found = _find(*commits)

    # Then it returns the full id of `c2`
    assert found == _id(2)


@PENDING
def test_a_record_of_no_work_is_not_skipped() -> None:
    """AC-2: `Wio-Work: none` belongs to no gate, so `c2` is returned."""
    # Given `c2` whose only record is `Wio-Work: none`, and `c1` below it
    commits = (_commit(1, WORK), _commit(2, "Wio-Work: none"))

    # When `reviewed_commit` runs
    found = _find(*commits)

    # Then it returns the full id of `c2`
    assert found == _id(2)


@PENDING
def test_a_history_of_only_gate_commits_has_no_reviewed_commit() -> None:
    """AC-3: `None` for a history of pure gate commits."""
    # Given a history of commits that each carry only a gate record
    commits = (_commit(1, GATE), _commit(2, GATE))

    # When `reviewed_commit` runs on it
    found = _find(*commits)

    # Then it returns `None`
    assert found is None


def test_an_empty_history_has_no_reviewed_commit() -> None:
    """AC-3: `None` for a history of no commit."""
    # Given a history of no commit
    # When `reviewed_commit` runs on it
    found = _find()

    # Then it returns `None`
    assert found is None


@PENDING
def test_a_record_the_reader_cannot_see_does_not_make_a_gate_commit() -> None:
    """AC-4: under `git`, a gate record before a trailing paragraph is invisible."""
    # Given `c2` whose message holds a gate record, a blank line and then the
    # paragraph `Co-authored-by: A <a@example.com>`, and `c1` below it, read with
    # the `git` reader
    after = "Co-authored-by: A <a@example.com>"
    commits = (_commit(1, WORK), _commit(2, GATE, after))

    # When `reviewed_commit` runs
    found = _find(*commits, reader="git")

    # Then it returns the full id of `c2`, whose record the reader cannot see
    assert found == _id(2)
