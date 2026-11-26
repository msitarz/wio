# SPDX-License-Identifier: Apache-2.0
"""Expect the temporary Work check stub in every context scenario."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.drivers.stub_known_work import (
    KnownWorkStubReachedError,
    identify_known_work_stub,
)
from tests.acceptance.dsl.wio import Wio

if TYPE_CHECKING:
    from collections.abc import Sequence

    from tests.acceptance.dsl.wio import Output


@pytest.fixture(autouse=True)
def _identify_stub(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Expect each scenario to fail by reaching the stub, and no other way.

    Args:
        request: Marks the scenario as a strict expected failure.
        monkeypatch: Wraps the facade's verb for one test.
    """
    request.applymarker(
        pytest.mark.xfail(
            strict=True,
            raises=KnownWorkStubReachedError,
            reason="Work check is stubbed",
        )
    )
    run = Wio.run

    def identified(
        wio: Wio, args: Sequence[str], directory: str | None = None, stdin: str = ""
    ) -> Output:
        """Run `wio` and identify the stub.

        Args:
            wio: The scenario's facade.
            args: The arguments after the program name.
            directory: A directory below the root to run in.
            stdin: What standard input holds.

        Returns:
            The output of the run.
        """
        output = run(wio, args, directory, stdin)
        identify_known_work_stub(output.exit_code, output.stdout, output.stderr)
        return output

    monkeypatch.setattr(Wio, "run", identified)
