# SPDX-License-Identifier: Apache-2.0
"""Outcomes of judging a review before it reaches an event sink.

The two commands consuming a judgement can preserve the same diagnostics.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wio.models.events import ReviewEvent


@dataclass(frozen=True)
class Accepted:
    """An event whose checks all passed.

    Attributes:
        event: The review to write to the event sink.
        warnings: Diagnostic lines in emission order, without terminators.
    """

    event: ReviewEvent
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class Refusal:
    """The diagnostics of a review that cannot be recorded.

    Attributes:
        lines: Diagnostics and offending lines in emission order, without
            terminators.
    """

    lines: tuple[str, ...]
