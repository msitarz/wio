# SPDX-License-Identifier: Apache-2.0
"""The port through which the log command checks a review.

Its adapter owns the validation and repository history lookup.
"""

from collections.abc import Sequence
from typing import Protocol

from wio.models.reviews import Accepted, Refusal

class ReviewChecker(Protocol):
    """Judge a review before the caller writes or reports its event.

    Checking supplies diagnostics and the event without writing to the sink.
    """

    def check(
        self,
        work: str,
        action: str,
        stage: str,
        result: str,
        judge: str,
        cites: Sequence[str],
    ) -> Accepted | Refusal:
        """Check the fields, citations and reviewed commit.

        Args:
            work: The id of the single Work under review.
            action: The action whose gate is being reviewed.
            stage: The gate to record.
            result: The overall judgement.
            judge: The reviewer who gave the judgement.
            cites: The KEY=RESULT citations in the request's order.

        Returns:
            The accepted event and warnings, or all lines of the refusal in
            their emission order.
        """
        ...
