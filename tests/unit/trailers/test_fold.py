# SPDX-License-Identifier: Apache-2.0
"""Tests of the fold form of `wio trailers`, run with fakes of its ports.

A range is a list of commits, oldest first, each with a message that may hold one or
more records.
"""

import io
from argparse import ArgumentParser
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import pytest

from tests.unit.fakes import FakeStdio
from tests.unit.trailers.test_validation import FakeContracts
from tests.unit.trailers.test_write import FakeSettings
from wio.models.commits import Commit
from wio.trailers import Services
from wio.trailers.errors import TrailersError
from wio.trailers.fold import configure_fold, run_fold

if TYPE_CHECKING:
    from wio.io.ports import History


@dataclass(frozen=True)
class FakeHistory:
    """The `History` port over one range of commits, which refuses any other."""

    commits: tuple[Commit, ...]

    def history(self, revision_range: str) -> tuple[Commit, ...]:
        """List the commits of the range.

        Args:
            revision_range: The range.

        Returns:
            The commits, for the range `a..b`.

        Raises:
            ValueError: For any other range.
        """
        if revision_range != "a..b":
            message = f"unknown revision in {revision_range}"
            raise ValueError(message)
        return self.commits


def _id(number: int) -> str:
    """Make the full id of the commit with a number.

    Args:
        number: The number of the commit.

    Returns:
        A 40-digit hexadecimal id.
    """
    return f"{number:040x}"


def _record(
    work: str,
    stage: str = "implementation",
    *,
    items: str | None = None,
    result: str | None = None,
    judge: str | None = None,
) -> str:
    """Write one record paragraph for a Work.

    Args:
        work: The `Wio-Work` value.
        stage: The stage.
        items: The `Wio-Items` value, or `None` for none.
        result: The `Wio-Result` value, or `None` for none.
        judge: The `Wio-Judge` value, or `None` for none.

    Returns:
        The paragraph without a trailing newline.
    """
    lines = [f"Wio-Work: {work}", "Wio-Action: deliver", f"Wio-Stage: {stage}"]
    lines += [f"Wio-Items: {items}"] if items else []
    lines += [f"Wio-Result: {result}"] if result else []
    lines += [f"Wio-Judge: {judge}"] if judge else []
    return "\n".join(lines)


def _commit(number: int, *paragraphs: str) -> Commit:
    """Make a commit whose message holds the paragraphs.

    Args:
        number: The number that gives the commit its id.
        *paragraphs: The paragraphs after the subject.

    Returns:
        The commit.
    """
    return Commit(_id(number), "\n\n".join(["feat: x", *paragraphs]))


def _revert(number: int, target: str) -> Commit:
    """Make a revert of a commit.

    Args:
        number: The number that gives the revert its id.
        target: The id the revert names, as it writes it.

    Returns:
        The commit, with the message that `git revert` writes.
    """
    return Commit(_id(number), f'Revert "x"\n\nThis reverts commit {target}.')


def _run(
    form: str,
    commits: tuple[Commit, ...],
    *,
    body: str = "",
    revision_range: str = "a..b",
) -> tuple[str, str]:
    """Run a form of the fold on a range.

    Args:
        form: `block` or `body`.
        commits: The commits of the range `a..b`, oldest first.
        body: What standard input holds, for `body`.
        revision_range: The range to fold.

    Returns:
        What was written to standard output and to standard error.
    """
    parser = ArgumentParser(prog="wio trailers fold")
    configure_fold(parser)
    args = parser.parse_args([form, revision_range])
    out, err = io.StringIO(), io.StringIO()
    history = cast("History", FakeHistory(commits))
    services = Services(FakeSettings(), FakeContracts(), history)
    code = run_fold(services, args, FakeStdio(io.StringIO(body), out, err))
    assert code == 0
    return out.getvalue(), err.getvalue()


A_IMPL = "Wio-Work: a\nWio-Action: deliver\nWio-Stage: implementation\n"


def test_consecutive_records_of_one_work_and_stage_become_one() -> None:
    """AC-1: two commits of one stage, the items united and the result latest."""
    # Given two consecutive commits whose records are for Work `a`, action
    # `deliver` and stage `implementation`, the first with items `AC-1` and result
    # `fail`, the second with items `AC-2` and result `pass`
    commits = (
        _commit(1, _record("a", items="AC-1", result="fail")),
        _commit(2, _record("a", items="AC-2", result="pass")),
    )

    # When `wio trailers fold block` runs on the range
    out, _ = _run("block", commits)

    # Then it prints one record for `a` with items `AC-1, AC-2` and the result `pass`
    assert out == f"{A_IMPL}Wio-Items: AC-1, AC-2\nWio-Result: pass\n"


def test_neighbors_that_differ_only_in_the_work_become_one_list() -> None:
    """AC-2: the same record for two Works."""
    # Given consecutive commits whose records for Works `a` and `b` have the same
    # action, stage, items, result and judge
    commits = (
        _commit(1, _record("a", items="AC-1")),
        _commit(2, _record("b", items="AC-1")),
    )

    # When `wio trailers fold block` runs on the range
    out, _ = _run("block", commits)

    # Then it prints one record whose `Wio-Work` is `a, b`
    assert out == (
        "Wio-Work: a, b\nWio-Action: deliver\nWio-Stage: implementation\n"
        "Wio-Items: AC-1\n"
    )


def test_a_record_between_two_others_keeps_them_apart() -> None:
    """AC-3: a re-delivered child after its parent's integration."""
    # Given a range whose records are, in order, child `a` delivering
    # `implementation`, parent `p` integrating, and `a` delivering `implementation`
    # again
    commits = (
        _commit(1, _record("a")),
        _commit(2, _record("p", "integration")),
        _commit(3, _record("a")),
    )

    # When `wio trailers fold block` runs on the range
    out, _ = _run("block", commits)

    # Then it prints three records in that order, each its own paragraph
    paragraphs = out.rstrip("\n").split("\n\n")
    assert [p.splitlines()[0] for p in paragraphs] == [
        "Wio-Work: a",
        "Wio-Work: p",
        "Wio-Work: a",
    ]


def test_a_commit_reverted_in_the_range_leaves_no_record() -> None:
    """AC-4: neither the reverted record nor one for the revert is printed."""
    # Given a commit with a record and a later commit in the range that reverts it
    commits = (_commit(1, _record("a")), _revert(2, _id(1)))

    # When `wio trailers fold block` runs on the range
    out, _ = _run("block", commits)

    # Then nothing is printed
    assert out == ""


def test_a_revert_of_a_revert_restores_the_record() -> None:
    """AC-4: the first commit's record is printed again."""
    # Given a commit with a record, a revert of it, and a revert of that revert
    commits = (_commit(1, _record("a")), _revert(2, _id(1)), _revert(3, _id(2)))

    # When `wio trailers fold block` runs on the range
    out, _ = _run("block", commits)

    # Then the record of the first commit is printed
    assert out == A_IMPL


def test_a_revert_of_work_outside_the_range_stays_visible_in_a_body() -> None:
    """AC-5: the revert paragraph and then the folded records, each its own."""
    # Given the body `Fix the bug.` and a commit in the range that reverts a commit
    # `1234567` outside it, beside a commit with a record
    commits = (_commit(1, _record("a")), _revert(2, "1234567"))

    # When `wio trailers fold body <range>` runs on that body
    out, _ = _run("body", commits, body="Fix the bug.")

    # Then the printed body is `Fix the bug.`, a paragraph, and the folded records
    assert out == f"Fix the bug.\n\nThis reverts commit 1234567.\n\n{A_IMPL}"


def test_a_revert_of_work_outside_the_range_stays_visible_in_a_block() -> None:
    """AC-5: the paragraph and then the folded records."""
    # Given the same range
    commits = (_commit(1, _record("a")), _revert(2, "1234567"))

    # When `wio trailers fold block <range>` runs
    out, _ = _run("block", commits)

    # Then it prints the paragraph and then the folded records
    assert out == f"This reverts commit 1234567.\n\n{A_IMPL}"


def test_a_body_without_the_records_gets_them_at_its_end() -> None:
    """AC-6: the prose is unchanged, a blank line and the folded records follow."""
    # Given a body of prose and a range with records
    commits = (_commit(1, _record("a")),)

    # When `wio trailers fold body` runs on the body and the range
    out, _ = _run("body", commits, body="Fix the bug.\n\nMore prose.")

    # Then it prints the prose, a blank line and the folded records
    assert out == f"Fix the bug.\n\nMore prose.\n\n{A_IMPL}"


def test_a_body_that_ends_with_older_records_has_them_replaced() -> None:
    """AC-6: a record paragraph inside the prose stays, the trailing one goes."""
    # Given a body of prose that holds a record paragraph, and that ends with a
    # record of the range's earlier state
    inside = _record("z", "architecture")
    body = f"Intro.\n\n{inside}\n\nMore prose.\n\n{_record('a', items='AC-1')}"
    commits = (_commit(1, _record("a", items="AC-1, AC-2")),)

    # When `wio trailers fold body` runs on it
    out, _ = _run("body", commits, body=body)

    # Then the printed body ends with the current folded records, holds the trailing
    # older one no longer, and keeps the record paragraph inside the prose
    assert (
        out == f"Intro.\n\n{inside}\n\nMore prose.\n\n{A_IMPL}Wio-Items: AC-1, AC-2\n"
    )


def test_a_body_that_already_has_them_prints_nothing() -> None:
    """AC-7: folding twice."""
    # Given the body that `wio trailers fold body` printed for a range
    commits = (_commit(1, _record("a")), _commit(2, _record("p", "integration")))
    first, _ = _run("body", commits, body="Fix the bug.")

    # When `wio trailers fold body` runs on that body and the same range
    second, _ = _run("body", commits, body=first)

    # Then it prints nothing
    assert second == ""


def test_a_listed_work_folds_like_a_single_one_and_none_prints_nothing() -> None:
    """AC-8: `a, b` is `a` and then `b`, and `none` is dropped."""
    # Given a commit whose record has `Wio-Work: a, b`, and a commit whose record has
    # `Wio-Work: none`
    listed = (_commit(1, _record("a, b")),)
    separate = (_commit(1, _record("a")), _commit(2, _record("b")))
    none = (_commit(1, "Wio-Work: none"),)

    # When `wio trailers fold block` runs on each range
    # Then the first prints as it would for one record of `a` and then one of `b`,
    # and the second prints nothing
    assert _run("block", listed)[0] == _run("block", separate)[0]
    assert _run("block", none) == ("", "")


@pytest.mark.parametrize("form", ["block", "body"])
def test_a_range_that_does_not_resolve_prints_nothing(form: str) -> None:
    """AC-9: each form raises `TrailersError`, which exits 2, and writes nothing."""
    # Given a range whose revision does not exist
    # When `wio trailers fold block <range>` and `wio trailers fold body <range>` run
    # Then each raises a `TrailersError` and writes nothing
    with pytest.raises(TrailersError):
        _run(form, (), revision_range="nosuch..b")


def test_an_abbreviated_id_names_a_commit_of_the_range() -> None:
    """A revert that writes a prefix of an id takes that commit back."""
    # Given a commit and a revert that names it by the first seven digits
    commits = (_commit(1, _record("a")), _revert(2, _id(1)[:7]))

    # When the block is folded
    out, _ = _run("block", commits)

    # Then the record is gone and no revert line is kept for it
    assert out == ""


def test_a_revert_of_outside_work_that_a_later_revert_takes_back_is_not_kept() -> None:
    """The line of a revert that was itself reverted disappears."""
    # Given a revert of a commit outside the range, and a revert of that revert
    commits = (_revert(1, "1234567"), _revert(2, _id(1)), _commit(3, _record("a")))

    # When the block is folded
    out, _ = _run("block", commits)

    # Then only the record is printed
    assert out == A_IMPL


def test_neighbors_of_a_dropped_commit_merge() -> None:
    """A record between two others, once it is taken back, no longer separates them."""
    # Given a commit, a commit that is reverted, and a commit of the same stage
    commits = (
        _commit(1, _record("a", items="AC-1")),
        _commit(2, _record("p", "integration")),
        _revert(3, _id(2)),
        _commit(4, _record("a", items="AC-2")),
    )

    # When the block is folded
    out, _ = _run("block", commits)

    # Then the two commits of `a` are one record
    assert out == f"{A_IMPL}Wio-Items: AC-1, AC-2\n"


def test_the_later_result_wins_and_an_earlier_judge_stands_when_absent() -> None:
    """The first step takes the later values, and keeps the earlier when absent."""
    # Given three commits of one stage with a result and a judge, a new result, and
    # none
    commits = (
        _commit(1, _record("a", result="fail", judge="agent")),
        _commit(2, _record("a", result="pass")),
        _commit(3, _record("a", items="AC-1")),
    )

    # When the block is folded
    out, _ = _run("block", commits)

    # Then the latest result stands and the judge of the first is kept
    assert out == f"{A_IMPL}Wio-Items: AC-1\nWio-Result: pass\nWio-Judge: agent\n"


def test_neighbors_that_differ_in_the_judge_stay_apart() -> None:
    """The second step needs equal results and judges."""
    # Given records of two Works that differ only in the judge
    commits = (
        _commit(1, _record("a", result="pass", judge="agent")),
        _commit(2, _record("b", result="pass", judge="human")),
    )

    # When the block is folded
    out, _ = _run("block", commits)

    # Then there are two records
    assert len(out.rstrip("\n").split("\n\n")) == 2


def test_a_work_that_a_list_already_names_starts_the_next_record() -> None:
    """The second step merges neighbors only, and a list names no Work twice."""
    # Given four commits of one stage for the Works `a`, `b`, `a` and `b`
    commits = tuple(_commit(n, _record(w)) for n, w in enumerate("abab", start=1))

    # When the block is folded
    out, _ = _run("block", commits)

    # Then there are two records, each for `a, b`
    records = out.rstrip("\n").split("\n\n")
    assert [r.splitlines()[0] for r in records] == ["Wio-Work: a, b"] * 2


def test_the_revert_of_a_merge_takes_its_commit_back() -> None:
    """`git revert -m` ends the line with a comma and says which parent."""
    # Given a commit and a revert that `git revert -m` wrote for it
    revert = Commit(
        _id(2),
        f'Revert "x"\n\nThis reverts commit {_id(1)}, reversing\nchanges made to x.',
    )

    # When the block is folded
    out, _ = _run("block", (_commit(1, _record("a")), revert))

    # Then nothing is printed
    assert out == ""


def test_an_upper_case_abbreviated_id_names_a_commit_of_the_range() -> None:
    """The id of a revert is matched without regard to the case of its digits."""
    # Given a commit whose id has letters and a revert that writes a prefix of it in
    # upper case
    first = Commit("ab" * 20, f"feat: x\n\n{_record('a')}")

    # When the block is folded
    out, _ = _run("block", (first, _revert(2, "ABABAB")))

    # Then the record is gone
    assert out == ""


def test_a_prefix_that_two_commits_share_names_no_commit_of_the_range() -> None:
    """An ambiguous id counts as a commit outside the range and stays visible."""
    # Given two commits whose ids start alike and a revert that names that prefix
    commits = (_commit(1, _record("a")), _commit(2, _record("b")))
    revert = _revert(3, _id(1)[:7])

    # When the block is folded
    out, _ = _run("block", (*commits, revert))

    # Then the revert line is printed and both records stay
    assert out.startswith(f"This reverts commit {_id(1)[:7]}.\n\n")
    assert "Wio-Work: a, b" in out


def test_a_revert_of_a_later_commit_names_a_commit_outside_the_range() -> None:
    """A revert can only take back what came before it."""
    # Given a revert that names a commit that comes after it
    commits = (_revert(1, _id(2)), _commit(2, _record("a")))

    # When the block is folded
    out, _ = _run("block", commits)

    # Then the revert line is kept and the record stays
    assert out == f"This reverts commit {_id(2)}.\n\n{A_IMPL}"


def test_a_revert_of_a_revert_of_a_revert_drops_the_record_again() -> None:
    """Each revert takes back the one before it."""
    # Given a commit and three reverts, each of the one before
    commits = (
        _commit(1, _record("a")),
        _revert(2, _id(1)),
        _revert(3, _id(2)),
        _revert(4, _id(3)),
    )

    # When the block is folded
    out, _ = _run("block", commits)

    # Then nothing is printed
    assert out == ""


def test_the_reverts_of_outside_work_come_in_the_order_of_the_history() -> None:
    """Each revert paragraph is its own, in the order of the commits."""
    # Given two reverts of commits outside the range
    commits = (_revert(1, "2222222"), _revert(2, "1111111"))

    # When the block is folded
    out, _ = _run("block", commits)

    # Then the paragraphs are in that order
    assert out == "This reverts commit 2222222.\n\nThis reverts commit 1111111.\n"


def test_the_line_ends_of_the_prose_are_kept_and_a_second_run_prints_nothing() -> None:
    """A body with CRLF line ends keeps them in the prose and folds once."""
    # Given a body of prose with CRLF line ends
    commits = (_commit(1, _record("a")),)
    first, _ = _run("body", commits, body="Fix.\r\nMore.")

    # When it is folded, and the result is folded again
    second, _ = _run("body", commits, body=first)

    # Then the prose keeps its line ends, and the second run prints nothing
    assert first == f"Fix.\r\nMore.\n\n{A_IMPL}"
    assert second == ""


def test_whitespace_before_the_tail_and_after_it_is_not_part_of_either() -> None:
    """A blank line with spaces and trailing spaces do not change the fold."""
    # Given a body with a line of spaces after the prose and spaces after the tail
    commits = (_commit(1, _record("a")),)
    body = f"Fix.\n   \n{A_IMPL.rstrip()}   \n"

    # When it is folded
    out, _ = _run("body", commits, body=body)

    # Then the body already ends with the block, so nothing is printed
    assert out == ""


@pytest.mark.parametrize(
    ("works", "expected"),
    [
        (["a", "b", "c"], ["a, b, c"]),
        (["a", "b", "b", "a"], ["a, b", "a"]),
        (["a, b", "b"], ["a, b"]),
        (["b", "a, b"], ["b, a", "b"]),
    ],
    ids=["three", "repeat", "list-then-member", "member-then-list"],
)
def test_neighbors_merge_into_lists_that_name_no_work_twice(
    works: list[str], expected: list[str]
) -> None:
    """The second step keeps each list free of a repeated Work, in history order."""
    # Given commits of one stage whose records name the Works given, a list at a time
    commits = tuple(_commit(n, _record(w)) for n, w in enumerate(works, start=1))

    # When the block is folded
    out, _ = _run("block", commits)

    # Then the records name the Works as expected
    records = out.rstrip("\n").split("\n\n")
    assert [r.splitlines()[0].removeprefix("Wio-Work: ") for r in records] == expected
