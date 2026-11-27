# SPDX-License-Identifier: Apache-2.0
"""Warnings when a stage selects an empty set of Work roots."""

import io
from argparse import Namespace
from dataclasses import dataclass

import pytest

from tests.fakes import FakeEnvironment, ReviewedCommitFake
from tests.unit import fakes as unit_fakes
from tests.unit.cli.fakes import FakeStdio
from tests.unit.context.fakes import EventSinkFake, SettingsStub
from wio import context
from wio.context.no_roots import NoRootsWarning
from wio.models.config import Config, Stage
from wio.models.frozen import freeze


@dataclass
class _Roots:
    """Give prepared expanded Work roots and count requests."""

    roots: tuple[str, ...] | None
    calls: int = 0

    def roots_of(self, work_id: str) -> tuple[str, ...] | None:
        """Give the prepared roots for the Work.

        Args:
            work_id: The Work requested.

        Returns:
            The prepared roots, or None when the Work is unknown.
        """
        assert work_id == "k3m9xq"
        self.calls += 1
        return self.roots


class _Composer:
    """Give a fixed bundle after the checks run."""

    def compose(self, work_id: str, action: str, stage: str) -> context.CompiledBundle:
        """Compose the fixed bundle for the requested stage.

        Args:
            work_id: The Work's id.
            action: The action.
            stage: The stage.

        Returns:
            The fixed bundle.
        """
        assert (work_id, action, stage) == ("k3m9xq", "deliver", "review")
        return context.CompiledBundle("fixed bundle\n", "123456789abc", 0, {})


def _check(
    selection: tuple[str, ...] | None, roots: tuple[str, ...] | None
) -> tuple[NoRootsWarning, _Roots]:
    """Prepare a warning check with the given selection and Work roots.

    Args:
        selection: The stage's roots, or None when unset.
        roots: The expanded Work roots, or None for an unknown Work.

    Returns:
        The check and its roots fake.
    """
    config = Config(stages=freeze({"review": Stage(goal="Review", roots=selection)}))
    works = _Roots(roots)
    return NoRootsWarning(SettingsStub(config), works), works


@pytest.mark.parametrize("selection", [None, ("contract", "@work")])
def test_selected_empty_roots_warn_and_still_print_bundle(
    selection: tuple[str, ...] | None,
) -> None:
    """AC-1: a warning accompanies the fixed bundle, without a refusal."""
    # Given a stage selecting the empty roots of a Work and a fixed composer
    check, _ = _check(selection, ())
    out, err = io.StringIO(), io.StringIO()
    streams = FakeStdio(stdout=out, stderr=err)
    services = context.Services(
        unit_fakes.FakeRepository(),
        unit_fakes.MemoryFileSystem(),
        FakeEnvironment(unit_fakes.ROOT),
        unit_fakes.FakeDirectories(unit_fakes.ROOT),
        SettingsStub(Config()),
        EventSinkFake(),
        ReviewedCommitFake(),
    )
    compiler = context.Compiler(_Composer(), (check,))
    command = context.ContextCommand(services, compiler.compile)

    # When the command runs
    code = command.run(
        Namespace(work="k3m9xq", action="deliver", stage="review"),
        streams,
    )

    # Then the bundle prints and exactly one warning names the Work and its roots
    assert (code, out.getvalue()) == (0, "fixed bundle\n")
    lines = err.getvalue().splitlines()
    assert len(lines) == 1
    assert lines[0].startswith("warning: ")
    assert all(part in lines[0] for part in ("k3m9xq", "no roots"))


@pytest.mark.parametrize(
    ("selection", "roots"), [(None, ("api",)), (("contract",), ()), ((), ())]
)
def test_no_warning_when_roots_exist_or_are_not_selected(
    selection: tuple[str, ...] | None, roots: tuple[str, ...]
) -> None:
    """AC-2: present or unselected Work roots need no warning."""
    # Given Work roots and a stage's selection
    check, works = _check(selection, roots)

    # When the inputs are checked
    warnings = check("k3m9xq", "deliver", "review")

    # Then no warning is returned and unselected roots are not looked up
    assert not warnings
    assert works.calls == (1 if selection is None else 0)


def test_unknown_work_is_left_to_its_own_check() -> None:
    """An unknown Work is not treated as a known Work with no roots."""
    # Given an unknown Work at a stage that selects Work roots
    check, _ = _check(None, None)

    # When the inputs are checked
    warnings = check("k3m9xq", "deliver", "review")

    # Then there is no warning about its roots
    assert not warnings
