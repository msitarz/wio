# SPDX-License-Identifier: Apache-2.0
"""Tests of the new Work command's wiring around its stubbed leaves."""

from argparse import ArgumentParser
from pathlib import Path
from typing import TYPE_CHECKING, cast
from unittest.mock import Mock

import pytest

from tests.unit.fakes import (
    ROOT,
    FakeEntropy,
    FakeRepository,
    FakeStdio,
    MemoryFileSystem,
)
from wio.contracts import ContractsCommand, ContractsError, Services, describe
from wio.contracts.creation import NewArguments, NewWork
from wio.models.config import Config

if TYPE_CHECKING:
    from io import StringIO

    from wio.contracts.ports import TemplateCatalog
    from wio.ports import Settings


def _services(files: MemoryFileSystem) -> Services:
    """Build the command's services around an in-memory file system.

    Args:
        files: The in-memory file system.

    Returns:
        Services backed by the file system and fakes.
    """
    settings = Mock()
    settings.load.return_value = Config()
    return Services(
        cast("Settings", settings),
        FakeRepository(),
        files,
        cast("TemplateCatalog", Mock()),
        FakeEntropy(),
    )


def test_new_routes_options_through_the_plan_and_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The command passes its parsed options to the plan, then writes and reports."""
    # Given the command with a stubbed plan and report and in-memory ports
    parser = ArgumentParser()
    describe().configure(parser)
    args = parser.parse_args(
        [
            "new",
            "feature",
            "--template",
            "feature.leaf",
            "--parent",
            "p5n2hv",
            "--slug",
            "child",
            "--title",
            "Child",
            "--path",
            "works/c.md",
            "--root",
            "api",
            "--root",
            "web",
            "--json",
        ]
    )
    files = MemoryFileSystem()
    services = _services(files)
    work = NewWork(
        "k3m9xq", "Child", Path("works/c.md"), "feature.leaf", "p5n2hv", "text"
    )
    plan = Mock(return_value=work)
    report = Mock(return_value="report\n")
    monkeypatch.setattr("wio.contracts.creation.plan_work", plan)
    monkeypatch.setattr("wio.contracts.creation.render_report", report)
    stdio = FakeStdio()

    # When the command runs
    result = ContractsCommand(services).run(args, stdio)

    # Then it passes every option, writes the planned file and reports it
    arguments = cast("NewArguments", plan.call_args.args[0])
    assert (arguments.kind, arguments.template, arguments.roots) == (
        "feature",
        "feature.leaf",
        ("api", "web"),
    )
    assert (
        arguments.name.slug,
        arguments.name.title,
        arguments.name.path,
        arguments.name.parent,
    ) == ("child", "Child", "works/c.md", "p5n2hv")
    assert files.files[ROOT / work.path] == "text"
    report.assert_called_once_with(work, as_json=True)
    assert (result, cast("StringIO", stdio.stdout).getvalue()) == (0, "report\n")


def test_new_does_not_report_when_guard_refuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A guard refusal leaves the existing file and standard output alone."""
    # Given a plan whose destination is already occupied
    parser = ArgumentParser()
    describe().configure(parser)
    args = parser.parse_args(["new", "--slug", "child"])
    path = Path("works/c.md")
    files = MemoryFileSystem({ROOT / path: "existing"})
    services = _services(files)
    work = NewWork("k3m9xq", None, path, None, None, "new")
    monkeypatch.setattr("wio.contracts.creation.plan_work", Mock(return_value=work))
    report = Mock(return_value="report\n")
    monkeypatch.setattr("wio.contracts.creation.render_report", report)
    stdio = FakeStdio()

    # When the command reaches the guard
    with pytest.raises(ContractsError):
        ContractsCommand(services).run(args, stdio)

    # Then the existing file is unchanged and nothing is reported
    assert files.files[ROOT / path] == "existing"
    assert cast("StringIO", stdio.stdout).getvalue() == ""
    report.assert_not_called()
