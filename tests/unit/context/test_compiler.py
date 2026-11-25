# SPDX-License-Identifier: Apache-2.0
"""Tests of the compiler: the order of the checks and the composition."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pytest

from wio.context import Compiled, CompiledBundle, Compiler
from wio.errors import WioError

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.context import Check

_PENDING = pytest.mark.xfail(strict=True)
_INPUTS = ("k3m9xq", "deliver", "architecture")
_BUNDLE = CompiledBundle("text\n", "4f3a9c01b2d7", 5, {})


@dataclass
class _Composer:
    """A `Composer` that records what it was asked for."""

    calls: list[tuple[str, str, str]] = field(default_factory=list)

    def compose(self, work_id: str, action: str, stage: str) -> CompiledBundle:
        """Record the call and return the fixed bundle.

        Args:
            work_id: The Work's id.
            action: The action.
            stage: The stage.

        Returns:
            The bundle.
        """
        self.calls.append((work_id, action, stage))
        return _BUNDLE


def _check(
    name: str, ran: list[tuple[str, str, str, str]], error: Exception | None = None
) -> Check:
    """Make a check that records its call.

    Args:
        name: The name that its call and its warning carry.
        ran: Takes the name and the inputs of each call.
        error: What it raises instead of warning.

    Returns:
        The check.
    """

    def check(work_id: str, action: str, stage: str) -> Sequence[str]:
        ran.append((name, work_id, action, stage))
        if error is not None:
            raise error
        return [f"warning of {name}"]

    return check


@_PENDING
def test_a_failing_check_stops_the_run() -> None:
    """AC-4: nothing runs after the first check that raises."""
    # Given a composer that records its calls and two checks, the first failing
    composer = _Composer()
    ran: list[tuple[str, str, str, str]] = []
    error = WioError("no")
    checks = (_check("first", ran, error), _check("second", ran))

    # When the compiler runs
    with pytest.raises(WioError) as raised:
        Compiler(composer, checks).compile(*_INPUTS)

    # Then the error reaches the caller, and nothing else was called
    assert raised.value is error
    assert ran == [("first", *_INPUTS)]
    assert composer.calls == []


@_PENDING
def test_passing_checks_compose_once_with_their_warnings_in_order() -> None:
    """AC-4: one composition, and the warnings in the order the checks ran."""
    # Given a composer that records its calls and two checks that each warn
    composer = _Composer()
    ran: list[tuple[str, str, str, str]] = []
    checks = (_check("first", ran), _check("second", ran))

    # When the compiler runs
    compiled = Compiler(composer, checks).compile(*_INPUTS)

    # Then it composed once, after both checks, and holds the bundle and warnings
    assert composer.calls == [_INPUTS]
    assert ran == [("first", *_INPUTS), ("second", *_INPUTS)]
    assert compiled == Compiled(_BUNDLE, ("warning of first", "warning of second"))
