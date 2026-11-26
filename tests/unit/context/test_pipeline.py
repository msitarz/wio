# SPDX-License-Identifier: Apache-2.0
"""Warnings for a stage outside a Work's effective pipeline."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from wio.context.pipeline import PipelineWarning

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass
class _Pipelines:
    """Give the prepared pipeline and record its requests."""

    stages: Sequence[str] | None
    calls: list[tuple[str, str]] = field(default_factory=list)

    def pipeline(self, work_id: str, action: str) -> Sequence[str] | None:
        """Give the prepared effective pipeline.

        Args:
            work_id: The requested Work.
            action: The requested action.

        Returns:
            The prepared stages, or None when there is no pipeline.
        """
        self.calls.append((work_id, action))
        return self.stages


def test_outside_stage_warns() -> None:
    """AC-1: an outside stage names the Work, action and stage."""
    # Given an effective pipeline without the requested stage
    works = _Pipelines(["architecture", "wiring"])

    # When the requested stage is checked
    warnings = PipelineWarning(works)("a1b2c3", "deliver", "define")

    # Then one warning names the request and lookup uses the Work and action
    assert len(warnings) == 1
    assert all(name in warnings[0] for name in ("a1b2c3", "deliver", "define"))
    assert works.calls == [("a1b2c3", "deliver")]


def test_missing_pipeline_uses_the_trailers_warning() -> None:
    """AC-1: no effective action gives the existing trailers warning."""
    # Given a Work without a pipeline for the action
    works = _Pipelines(None)

    # When a stage of the action is checked
    warnings = PipelineWarning(works)("a1b2c3", "deliver", "architecture")

    # Then the warning matches the one used by trailers
    assert warnings == ("The Work `a1b2c3` has no action `deliver`.",)


def test_inside_stage_has_no_warning() -> None:
    """AC-2: a stage anywhere in the effective pipeline needs no warning."""
    # Given a pipeline whose second stage is requested
    works = _Pipelines(["architecture", "wiring"])

    # When that stage is checked
    warnings = PipelineWarning(works)("a1b2c3", "deliver", "wiring")

    # Then no warning is returned
    assert not warnings


def test_the_requested_action_decides_the_pipeline() -> None:
    """AC-1: the pipeline and the warning are those of the requested action."""
    # Given an effective pipeline without the requested stage
    works = _Pipelines(["define"])

    # When a stage of an action other than deliver is checked
    warnings = PipelineWarning(works)("a1b2c3", "define", "wiring")

    # Then that action's pipeline is looked up and named
    assert works.calls == [("a1b2c3", "define")]
    assert warnings == (
        "The stage `wiring` is not in the `define` pipeline of `a1b2c3`.",
    )
