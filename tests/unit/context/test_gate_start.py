# SPDX-License-Identifier: Apache-2.0
"""Tests of reading the starting commit and dirty flag for a gate stage."""

from dataclasses import dataclass, field
from typing import override

import pytest

from tests.fakes import value_or_raise
from tests.unit.fakes import FakeRepository
from wio.context.gate_start import GateStart, read_gate_start


@dataclass
class _ReviewedStub:
    """Supply a fixed reviewed commit or failure and record calls."""

    result: str | Exception | None
    calls: list[tuple[str, str]] = field(default_factory=list)

    def find(self, action: str, stage: str) -> str | None:
        """Record the call and return the configured commit id or raise.

        Args:
            action: The action of the gate.
            stage: The stage of the gate.

        Returns:
            The configured commit id or `None`.
        """
        self.calls.append((action, stage))
        return value_or_raise(self.result)


@dataclass
class _DirtyRepository(FakeRepository):
    """A fake repository with a configurable `is_dirty` result or failure."""

    dirty_result: bool | Exception = False
    dirty_calls: int = 0

    @override
    def is_dirty(self) -> bool:
        """Record the call and return the configured dirty state or raise.

        Returns:
            The configured dirty flag.
        """
        self.dirty_calls += 1
        return value_or_raise(self.dirty_result)


@pytest.mark.xfail(strict=True, raises=NotImplementedError)
def test_non_gate_stage_reads_nothing() -> None:
    """A stage without `gate = true` skips both history and repository reads."""
    # Given a non-gate stage and ports that record calls
    reviewed = _ReviewedStub("a" * 40)
    repository = _DirtyRepository(dirty_result=True)

    # When gate start is read for a non-gate stage
    result = read_gate_start(
        "deliver",
        "implementation",
        is_gate=False,
        reviewed=reviewed,
        repository=repository,
    )

    # Then neither port was called and all fields are empty
    assert result == GateStart()
    assert (reviewed.calls, repository.dirty_calls) == ([], 0)


@pytest.mark.xfail(strict=True, raises=NotImplementedError)
def test_gate_stage_reads_start_commit_and_dirty_flag() -> None:
    """AC-1, AC-2: a gate reads both the reviewed commit and the dirty flag."""
    # Given a gate stage with a start commit and a dirty working tree
    reviewed = _ReviewedStub("b" * 40)
    repository = _DirtyRepository(dirty_result=True)

    # When gate start is read
    result = read_gate_start(
        "deliver",
        "review",
        is_gate=True,
        reviewed=reviewed,
        repository=repository,
    )

    # Then both values are returned with no warnings
    assert result == GateStart(start="b" * 40, dirty=True, warnings=())
    assert reviewed.calls == [("deliver", "review")]
    assert repository.dirty_calls == 1


@pytest.mark.xfail(strict=True, raises=NotImplementedError)
def test_gate_with_no_start_commit_omits_start_without_warning() -> None:
    """AC-3: an empty or pure-gate history returns `start=None` with no warning."""
    # Given a gate whose reviewed commit finder returns None
    reviewed = _ReviewedStub(None)
    repository = _DirtyRepository(dirty_result=False)

    # When gate start is read
    result = read_gate_start(
        "deliver",
        "review",
        is_gate=True,
        reviewed=reviewed,
        repository=repository,
    )

    # Then start is None, dirty is False, and no warning is produced
    assert result == GateStart(start=None, dirty=False, warnings=())


@pytest.mark.xfail(strict=True, raises=NotImplementedError)
@pytest.mark.parametrize("error", [ValueError("bad rev"), RuntimeError("no repo")])
def test_history_failure_drops_only_start_and_warns(error: Exception) -> None:
    """AC-6: a history read failure drops `start`, keeps `dirty`, and warns."""
    # Given a failing reviewed-commit port and a working repository port
    reviewed = _ReviewedStub(error)
    repository = _DirtyRepository(dirty_result=True)

    # When gate start is read
    result = read_gate_start(
        "deliver",
        "review",
        is_gate=True,
        reviewed=reviewed,
        repository=repository,
    )

    # Then start is None, dirty is preserved, and one warning names `start`
    assert (result.start, result.dirty) == (None, True)
    assert len(result.warnings) == 1
    assert "start" in result.warnings[0]


@pytest.mark.xfail(strict=True, raises=NotImplementedError)
@pytest.mark.parametrize("error", [RuntimeError("no repo"), ValueError("git failed")])
def test_repository_failure_drops_only_dirty_and_warns(error: Exception) -> None:
    """AC-6: a repository read failure drops `dirty`, keeps `start`, and warns."""
    # Given a working reviewed-commit port and a failing repository port
    reviewed = _ReviewedStub("c" * 40)
    repository = _DirtyRepository(dirty_result=error)

    # When gate start is read
    result = read_gate_start(
        "deliver",
        "review",
        is_gate=True,
        reviewed=reviewed,
        repository=repository,
    )

    # Then start is preserved, dirty is None, and one warning names `dirty`
    assert (result.start, result.dirty) == ("c" * 40, None)
    assert len(result.warnings) == 1
    assert "dirty" in result.warnings[0]


@pytest.mark.xfail(strict=True, raises=NotImplementedError)
def test_unexpected_error_propagates_as_bug() -> None:
    """A-6: errors other than ValueError/RuntimeError are not caught."""
    # Given a reviewed-commit port that raises an unexpected TypeError
    reviewed = _ReviewedStub(TypeError("unexpected"))
    repository = _DirtyRepository(dirty_result=False)

    # When gate start is read, Then TypeError propagates
    with pytest.raises(TypeError, match="unexpected"):
        read_gate_start(
            "deliver",
            "review",
            is_gate=True,
            reviewed=reviewed,
            repository=repository,
        )
