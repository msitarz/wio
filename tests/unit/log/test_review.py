# SPDX-License-Identifier: Apache-2.0
"""Exercise how the log review command handles checker verdicts.

Typed fakes isolate the output and sink behavior from validation and Git.
"""

import json
from argparse import Namespace
from dataclasses import dataclass
from io import StringIO
from typing import TYPE_CHECKING

import pytest

from tests.unit.fakes import FakeStdio, RecordingSink
from wio.log.review import ReviewCommand
from wio.models.events import ReviewEvent
from wio.models.reviews import Accepted, Refusal

if TYPE_CHECKING:
    from collections.abc import Sequence

_EVENT = ReviewEvent(
    "k3m9xq", "deliver", "docs-review", "a" * 40, "agent", "pass", {}, {}
)
_WARNING = "warning: Wio-Stage: the stage is outside the pipeline"
_REFUSAL = ("error: Wio-Work: invalid Work", "Wio-Work: invalid")


@dataclass(frozen=True)
class FixedChecker:
    """Supply one checker verdict to the command.

    Attributes:
        verdict: The review outcome prepared by the scenario.
    """

    verdict: Accepted | Refusal

    def check(
        self,
        work: str,
        action: str,
        stage: str,
        result: str,
        judge: str,
        cites: Sequence[str],
    ) -> Accepted | Refusal:
        """Return the prepared outcome for any request.

        Args:
            work: Requested Work.
            action: Requested action.
            stage: Requested gate.
            result: Requested judgement.
            judge: Requested reviewer.
            cites: Requested citations.

        Returns:
            The verdict prepared by the scenario.
        """
        del work, action, stage, result, judge, cites
        return self.verdict


@pytest.mark.parametrize(
    ("verdict", "exit_code", "diagnostics", "events"),
    [
        (Accepted(_EVENT, (_WARNING,)), 0, (_WARNING,), [_EVENT]),
        (Refusal(_REFUSAL), 1, _REFUSAL, []),
    ],
    ids=["accepted-with-warning", "refused-with-offending-line"],
)
def test_json_output_is_separate_from_checker_diagnostics(
    verdict: Accepted | Refusal,
    exit_code: int,
    diagnostics: tuple[str, ...],
    events: list[ReviewEvent],
) -> None:
    """Keep JSON on stdout and send only accepted reviews to the sink.

    Args:
        verdict: The configured checker outcome.
        exit_code: The expected command result.
        diagnostics: The expected lines on standard error.
        events: The events expected at the sink.
    """
    # Given the prepared verdict and a request for JSON output.
    sink = RecordingSink()
    command = ReviewCommand(FixedChecker(verdict), sink)
    stdout, stderr = StringIO(), StringIO()
    args = Namespace(
        work="k3m9xq",
        action="deliver",
        stage="docs-review",
        result="pass",
        judge="agent",
        cite=[],
        json=True,
    )

    # When the review runs.
    status = command.run(args, FakeStdio(stdout=stdout, stderr=stderr))

    # Then the verdict determines the result and separates both streams.
    assert status == exit_code
    assert stderr.getvalue() == "".join(f"{line}\n" for line in diagnostics)
    assert sink.events == events
    if events:
        assert json.loads(stdout.getvalue())["event"]["commit"] == _EVENT.commit
    else:
        assert stdout.getvalue() == ""
