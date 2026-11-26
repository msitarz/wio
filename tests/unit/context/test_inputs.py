# SPDX-License-Identifier: Apache-2.0
"""The check of declared action, stage and selected Work roots."""

from dataclasses import dataclass

import pytest

from tests.unit.context.fakes import SettingsStub
from wio.context.inputs import KnownInputs
from wio.errors import WioError
from wio.models.config import Action, Config, Root, Stage
from wio.models.frozen import freeze

pytestmark = pytest.mark.xfail(strict=True, raises=NotImplementedError)


@dataclass
class _Roots:
    """Give fixed expanded roots and record lookups."""

    calls: int = 0
    roots: tuple[str, ...] = ("api", "ghost")

    def roots_of(self, work_id: str) -> tuple[str, ...] | None:
        """Give the prepared Work roots.

        Args:
            work_id: The requested Work.

        Returns:
            Its roots.
        """
        assert work_id == "k3m9xq"
        self.calls += 1
        return self.roots


def _check(roots: tuple[str, ...] | None = None) -> tuple[KnownInputs, _Roots]:
    """Build a check with two actions, two stages and two roots.

    Args:
        roots: The implementation stage's selection.

    Returns:
        The check and its Work roots fake.
    """
    config = Config(
        actions=freeze({"define": Action("Define"), "deliver": Action("Deliver")}),
        stages=freeze(
            {
                "implementation": Stage(goal="Build", roots=roots),
                "wiring": Stage(goal="Join"),
            }
        ),
        roots=freeze({"api": Root(()), "contract": Root(())}),
    )
    works = _Roots()
    return KnownInputs(SettingsStub(config), works), works


def test_unknown_action_names_declared_actions() -> None:
    """AC-1: an unknown action is refused with the declared names."""
    # Given a check with two declared actions
    check, _ = _check()

    # When an unknown action is checked
    with pytest.raises(WioError) as error:
        check("k3m9xq", "delivr", "implementation")

    # Then it names the unknown and declared actions
    assert all(name in str(error.value) for name in ("delivr", "define", "deliver"))


def test_unknown_stage_names_declared_stages() -> None:
    """AC-2: an unknown stage is refused with the declared names."""
    # Given a check with two declared stages
    check, _ = _check()

    # When an unknown stage is checked
    with pytest.raises(WioError) as error:
        check("k3m9xq", "deliver", "no-such-stage")

    # Then it names the unknown and declared stages
    assert all(
        name in str(error.value)
        for name in ("no-such-stage", "implementation", "wiring")
    )


@pytest.mark.parametrize("roots", [None, ("contract", "@work")])
def test_unknown_selected_work_root_is_refused(roots: tuple[str, ...] | None) -> None:
    """AC-3: implicit and explicit Work roots are checked."""
    # Given a Work with an unknown root selected by the stage
    check, _ = _check(roots)

    # When its inputs are checked
    with pytest.raises(WioError) as error:
        check("k3m9xq", "deliver", "implementation")

    # Then the refusal names the root and Work
    assert "ghost" in str(error.value)
    assert "k3m9xq" in str(error.value)


def test_unselected_work_roots_do_not_block_the_run() -> None:
    """AC-4: a stage's own roots leave the Work roots alone."""
    # Given a stage that selects only its own roots
    check, works = _check(("contract",))

    # When its inputs are checked
    warnings = check("k3m9xq", "deliver", "implementation")

    # Then it passes without looking up the Work roots
    assert not warnings
    assert works.calls == 0


@pytest.mark.parametrize("roots", [("api",), ()])
def test_selected_known_or_empty_work_roots_pass(roots: tuple[str, ...]) -> None:
    """Known and empty Work roots are not unknown roots."""
    # Given a Work with only known roots or none
    check, works = _check()
    works.roots = roots

    # When the stage selects its roots
    warnings = check("k3m9xq", "deliver", "implementation")

    # Then the check passes
    assert not warnings


def test_unknown_names_are_refused_in_order() -> None:
    """The action precedes the stage, which precedes the Work roots."""
    # Given an unknown action, stage and Work root
    check, _ = _check()

    # When each earlier fault is corrected
    messages = []
    for action, stage in (
        ("bad-action", "bad-stage"),
        ("deliver", "bad-stage"),
        ("deliver", "implementation"),
    ):
        with pytest.raises(WioError) as error:
            check("k3m9xq", action, stage)
        messages.append(str(error.value))

    # Then the refusals follow the required order
    assert "bad-action" in messages[0]
    assert "bad-stage" in messages[1]
    assert "ghost" in messages[2]
