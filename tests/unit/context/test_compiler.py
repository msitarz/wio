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
type _Calls = list[tuple[str, str, str, str]]


@dataclass
class _Composer:
    """A `Composer` that records its calls under the name `composer`.

    Attributes:
        calls: The calls, which a test can share with its checks to see the
            order of all of them.
    """

    calls: _Calls = field(default_factory=list)

    def compose(self, work_id: str, action: str, stage: str) -> CompiledBundle:
        """Record the call and return the fixed bundle.

        Args:
            work_id: The Work's id.
            action: The action.
            stage: The stage.

        Returns:
            The bundle.
        """
        self.calls.append(("composer", work_id, action, stage))
        return _BUNDLE


def _check(name: str, calls: _Calls, error: Exception | None = None) -> Check:
    """Make a check that records its call.

    Args:
        name: The name that its call and its warning carry.
        calls: Takes the name and the inputs of each call.
        error: What it raises instead of warning.

    Returns:
        The check.
    """

    def check(work_id: str, action: str, stage: str) -> Sequence[str]:
        """Record the call, and raise or warn.

        Args:
            work_id: The Work's id.
            action: The action.
            stage: The stage.

        Returns:
            One warning that names the check.

        Raises:
            Exception: The error that the check was made with.
        """
        calls.append((name, work_id, action, stage))
        if error is not None:
            raise error
        return [f"warning of {name}"]

    return check


@_PENDING
def test_a_failing_check_stops_the_run() -> None:
    """AC-4: nothing runs after the first check that raises."""
    # Given a composer and two checks that record their calls, the first failing
    composer = _Composer()
    error = WioError("no")
    checks = (
        _check("zulu", composer.calls, error),
        _check("alpha", composer.calls),
    )

    # When the compiler runs
    with pytest.raises(WioError) as raised:
        Compiler(composer, checks).compile(*_INPUTS)

    # Then the error reaches the caller, and nothing else was called
    assert raised.value is error
    assert composer.calls == [("zulu", *_INPUTS)]


@_PENDING
def test_passing_checks_compose_once_with_their_warnings_in_order() -> None:
    """AC-4: one composition after the checks, whose warnings keep their order."""
    # Given a composer and two checks that each warn, named so that the order
    # they run in is not the sorted one
    composer = _Composer()
    checks = (_check("zulu", composer.calls), _check("alpha", composer.calls))

    # When the compiler runs
    compiled = Compiler(composer, checks).compile(*_INPUTS)

    # Then it composed once, after both checks, and holds the bundle and warnings
    assert composer.calls == [
        ("zulu", *_INPUTS),
        ("alpha", *_INPUTS),
        ("composer", *_INPUTS),
    ]
    assert compiled == Compiled(_BUNDLE, ("warning of zulu", "warning of alpha"))
