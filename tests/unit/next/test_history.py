# SPDX-License-Identifier: Apache-2.0
"""Unit tests for `wio.next.history`."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from wio.models.commits import Commit
from wio.next.history import EffectiveRecord, read_effective_records

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


@dataclass
class _FakeHistory:
    """In-memory `History` double returning pre-configured first-parent commits.

    Attributes:
        commits: Commits in newest-first order, matching `History.first_parents`.
    """

    commits: Sequence[Commit] = field(default_factory=tuple)

    def rev_parse(self, revision: str) -> str:
        """Return the revision unchanged."""
        return revision

    def history(self, revision_range: str) -> Sequence[Commit]:
        """Return commits oldest-first."""
        del revision_range
        return tuple(reversed(self.commits))

    def first_parents(self, revision: str) -> Sequence[Commit]:
        """Return configured first-parent commits newest-first."""
        del revision
        return self.commits

    def list_files(self, revision: str) -> Sequence[Path]:
        """Return an empty file list."""
        del revision
        return ()

    def show(self, revision: str, path: Path) -> str | None:
        """Return `None` for any file."""
        del revision, path
        return None


def test_empty_history_returns_empty_tuple() -> None:
    """Empty first-parent history yields no effective records."""
    # Given an empty git history
    history = _FakeHistory()

    # When effective records are read
    records = read_effective_records(history, "scan")

    # Then no records are returned
    assert records == ()


def test_returns_records_oldest_to_newest_preserving_in_commit_order() -> None:
    """Records are returned oldest-to-newest with in-commit order preserved."""
    # Given two commits with multiple records in newest-first history
    c1 = Commit(
        "1" * 40,
        "first\n\nWio-Work: aaa111\nWio-Action: define\nWio-Stage: define\n\n"
        "Wio-Work: aaa111\nWio-Action: define\nWio-Stage: review-contract\n"
        "Wio-Result: pass\nWio-Judge: human",
    )
    c2 = Commit(
        "2" * 40,
        "second\n\nWio-Work: aaa111\nWio-Action: deliver\nWio-Stage: architecture",
    )
    history = _FakeHistory(commits=(c2, c1))

    # When effective records are read with the scan reader
    records = read_effective_records(history, "scan")

    # Then records appear oldest-to-newest in in-commit order
    assert records == (
        EffectiveRecord("1" * 40, "aaa111", "define", "define", None, None),
        EffectiveRecord(
            "1" * 40, "aaa111", "define", "review-contract", "pass", "human"
        ),
        EffectiveRecord("2" * 40, "aaa111", "deliver", "architecture", None, None),
    )


def test_git_reader_reads_only_last_trailer_paragraph() -> None:
    """Under the `git` reader, only the final trailer paragraph is parsed."""
    # Given a commit with an earlier Wio paragraph and a trailing Wio paragraph
    c1 = Commit(
        "1" * 40,
        "squash\n\nWio-Work: aaa111\nWio-Action: define\nWio-Stage: define\n\n"
        "Wio-Work: aaa111\nWio-Action: deliver\nWio-Stage: architecture",
    )
    history = _FakeHistory(commits=(c1,))

    # When effective records are read with the git reader
    records = read_effective_records(history, "git")

    # Then only the final paragraph's record is returned
    assert records == (
        EffectiveRecord("1" * 40, "aaa111", "deliver", "architecture", None, None),
    )


def test_multi_work_record_emits_one_effective_record_per_work() -> None:
    """A record listing multiple comma-separated Works emits one entry per Work."""
    # Given a commit whose Wio-Work trailer lists two Works
    c1 = Commit(
        "1" * 40,
        "define\n\nWio-Work: aaa111, bbb222\nWio-Action: define\nWio-Stage: define",
    )
    history = _FakeHistory(commits=(c1,))

    # When effective records are read
    records = read_effective_records(history, "scan")

    # Then one EffectiveRecord is emitted per Work id in listed order
    assert records == (
        EffectiveRecord("1" * 40, "aaa111", "define", "define", None, None),
        EffectiveRecord("1" * 40, "bbb222", "define", "define", None, None),
    )


def test_skips_no_records_malformed_and_work_none() -> None:
    """Commits without records, malformed records, and Wio-Work: none are skipped."""
    # Given commits with no records, Wio-Work: none, malformed, and valid records
    c_none = Commit("1" * 40, "chore\n\nWio-Work: none")
    c_plain = Commit("2" * 40, "plain commit without trailers")
    c_missing_stage = Commit("3" * 40, "bad\n\nWio-Work: aaa111\nWio-Action: deliver")
    c_duplicate_key = Commit(
        "4" * 40,
        "dup\n\nWio-Work: aaa111\nWio-Work: bbb222\nWio-Action: deliver\n"
        "Wio-Stage: architecture",
    )
    c_judge_no_result = Commit(
        "5" * 40,
        "judge\n\nWio-Work: aaa111\nWio-Action: deliver\nWio-Stage: architecture\n"
        "Wio-Judge: agent",
    )
    c_none_in_list = Commit(
        "6" * 40,
        "list\n\nWio-Work: aaa111, none\nWio-Action: deliver\nWio-Stage: architecture",
    )
    c_valid = Commit(
        "7" * 40,
        "good\n\nWio-Work: aaa111\nWio-Action: deliver\nWio-Stage: architecture",
    )
    history = _FakeHistory(
        commits=(
            c_valid,
            c_none_in_list,
            c_judge_no_result,
            c_duplicate_key,
            c_missing_stage,
            c_plain,
            c_none,
        )
    )

    # When effective records are read
    records = read_effective_records(history, "scan")

    # Then only the valid Work record is returned
    assert records == (
        EffectiveRecord("7" * 40, "aaa111", "deliver", "architecture", None, None),
    )


def test_reverted_commit_records_are_dropped_while_revert_commit_records_stay() -> None:
    """A revert drops the target commit's records while keeping its own."""
    # Given a commit and a later revert commit that also carries a Wio record
    target = Commit(
        "a" * 40,
        "feat\n\nWio-Work: aaa111\nWio-Action: deliver\nWio-Stage: architecture",
    )
    revert = Commit(
        "b" * 40,
        f'Revert "feat"\n\nThis reverts commit {"a" * 40}.\n\n'
        "Wio-Work: aaa111\nWio-Action: deliver\nWio-Stage: wiring",
    )
    history = _FakeHistory(commits=(revert, target))

    # When effective records are read
    records = read_effective_records(history, "scan")

    # Then only the revert commit's own record remains
    assert records == (
        EffectiveRecord("b" * 40, "aaa111", "deliver", "wiring", None, None),
    )


def test_revert_matches_prefix_sha() -> None:
    """A revert line referencing a unique SHA prefix drops the target commit."""
    # Given a commit and a later revert naming only a 7-character SHA prefix
    target = Commit(
        "1234567" + "a" * 33,
        "feat\n\nWio-Work: aaa111\nWio-Action: deliver\nWio-Stage: architecture",
    )
    revert = Commit("b" * 40, 'Revert "feat"\n\nThis reverts commit 1234567.')
    history = _FakeHistory(commits=(revert, target))

    # When effective records are read
    records = read_effective_records(history, "scan")

    # Then the reverted commit's records are dropped
    assert records == ()


def test_revert_of_revert_restores_original_records() -> None:
    """Reverting a revert restores the original commit's records."""
    # Given a commit, a revert of it, and a revert of the revert
    original = Commit(
        "a" * 40,
        "feat\n\nWio-Work: aaa111\nWio-Action: deliver\nWio-Stage: architecture",
    )
    revert1 = Commit("b" * 40, f'Revert "feat"\n\nThis reverts commit {"a" * 40}.')
    revert2 = Commit("c" * 40, f'Reapply "feat"\n\nThis reverts commit {"b" * 40}.')
    history = _FakeHistory(commits=(revert2, revert1, original))

    # When effective records are read
    records = read_effective_records(history, "scan")

    # Then the original commit's record is restored
    assert records == (
        EffectiveRecord("a" * 40, "aaa111", "deliver", "architecture", None, None),
    )


def test_revert_referencing_absent_sha_is_ignored() -> None:
    """A revert naming a SHA not in walked history is ignored without error."""
    # Given a commit and a revert referencing an unknown SHA
    c1 = Commit(
        "a" * 40,
        "feat\n\nWio-Work: aaa111\nWio-Action: deliver\nWio-Stage: architecture",
    )
    revert_unknown = Commit(
        "b" * 40, f'Revert "old"\n\nThis reverts commit {"f" * 40}.'
    )
    history = _FakeHistory(commits=(revert_unknown, c1))

    # When effective records are read
    records = read_effective_records(history, "scan")

    # Then the known commit's record is preserved without error
    assert records == (
        EffectiveRecord("a" * 40, "aaa111", "deliver", "architecture", None, None),
    )
