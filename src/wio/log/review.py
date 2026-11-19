# SPDX-License-Identifier: Apache-2.0
"""Record a checked review through the log command.

The command sends the event to the shared sink and can describe it as JSON.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace

    from wio.io.ports import Stdio
    from wio.log.ports import ReviewChecker
    from wio.ports import EventSink


@dataclass(frozen=True)
class ReviewCommand:
    """Check and record a review using the ports supplied by the CLI.

    Attributes:
        checker: Checks the request and finds its reviewed commit.
        events: Receives an accepted review.
    """

    checker: ReviewChecker
    events: EventSink

    def run(self, args: Namespace, stdio: Stdio) -> int:
        """Record the review parsed by the log command.

        Args:
            args: The Work, action, gate, judgement, cites and output option.
            stdio: Receives diagnostics and optional JSON.

        Returns:
            Zero for an accepted event or one for a refusal, with no output
            on stdout for a refusal or a successful text-mode command.
        """
        raise NotImplementedError
