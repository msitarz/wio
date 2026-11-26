# SPDX-License-Identifier: Apache-2.0
"""Refuse a run whose Work cannot be told from the tree."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.context.ports import Contracts


class _KnownWorkNotImplementedError(NotImplementedError):
    """The Work check boundary is not implemented yet."""


@dataclass(frozen=True)
class KnownWork:
    """Judge the config, the tree and the Work before any name of the request.

    It runs ahead of the other checks, so that no later refusal or warning
    answers for a Work that cannot be found.

    Attributes:
        contracts: Resolves a Work as the composition does.
    """

    contracts: Contracts

    def __call__(self, work_id: str, action: str, stage: str) -> Sequence[str]:
        """Refuse a Work that cannot be resolved.

        Faults that leave the tree complete do not refuse the Work.

        Args:
            work_id: The Work being run.
            action: The requested action, which is not judged.
            stage: The requested stage, which is not judged.

        Returns:
            No warnings when the Work resolves.

        Raises:
            ConfigurationError: The config cannot be loaded.
            DiagnosticsError: The tree is incomplete, or the id is unknown or
                shared.
            OSError: The Work's own file cannot be read.
            UnicodeDecodeError: The Work's own file is not UTF-8.
        """
        del work_id, action, stage
        raise _KnownWorkNotImplementedError
