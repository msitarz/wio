# SPDX-License-Identifier: Apache-2.0
"""Record a checked review through the log command.

The command sends the event to the shared sink and can describe it as JSON.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from wio.formats import encode_json
from wio.formats.event_lines import review_payload
from wio.models.reviews import Refusal

if TYPE_CHECKING:
    from argparse import Namespace

    from wio.io.ports import Stdio
    from wio.log.ports import ReviewChecker
    from wio.ports import EventSink


class Arguments:
    """Parsed values specific to the review form.

    Attributes:
        work: The Work under review.
        action: The action whose gate is reviewed.
        stage: The gate that was reviewed.
        result: The overall result.
        judge: The human or agent who judged the review.
        cite: Citations in argument order.
        json: Whether to print the accepted event as JSON.
    """

    work: str
    action: str
    stage: str
    result: str
    judge: str
    cite: list[str]
    json: bool


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
        values = cast("Arguments", args)
        outcome = self.checker.check(
            values.work,
            values.action,
            values.stage,
            values.result,
            values.judge,
            values.cite,
        )
        if isinstance(outcome, Refusal):
            stdio.stderr.writelines(line + "\n" for line in outcome.lines)
            return 1
        stdio.stderr.writelines(line + "\n" for line in outcome.warnings)
        self.events.write(outcome.event)
        if values.json:
            stdio.stdout.write(
                encode_json({"event": review_payload(outcome.event)}) + "\n"
            )
        return 0
