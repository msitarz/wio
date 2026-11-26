# SPDX-License-Identifier: Apache-2.0
"""Warn when a requested stage lies outside a Work's action pipeline."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.context.ports import Pipelines


class _PipelineNotImplementedError(NotImplementedError):
    """The pipeline warning boundary is not implemented yet."""


@dataclass(frozen=True)
class PipelineWarning:
    """Check a stage against the Work's effective, expanded pipeline.

    Attributes:
        works: Supplies a Work's effective pipeline for an action.
    """

    works: Pipelines

    def __call__(self, work_id: str, action: str, stage: str) -> Sequence[str]:
        """Warn when an action has no pipeline or the stage is outside it.

        The caller checks that the action and stage are declared first. The
        Work lookup supplies its effective pipeline, with presets expanded.

        Args:
            work_id: The Work being run.
            action: The declared action.
            stage: The declared stage.

        Returns:
            One warning naming the Work and action when no pipeline exists,
            one naming the Work, action and stage when outside it, or none when
            the pipeline contains the stage. A missing action uses the warning
            wording of `wio trailers`.

        Raises:
            ConfigurationError: The settings cannot be loaded.
        """
        del work_id, action, stage
        raise _PipelineNotImplementedError
