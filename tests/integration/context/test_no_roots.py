# SPDX-License-Identifier: Apache-2.0
"""The warning with real Work lookup and a fixed bundle composer."""

import io
from argparse import Namespace
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.drivers.in_process import MemoryStdio
from tests.support import enter, git
from wio.cli.table import _contracts_services
from wio.context import CompiledBundle, Compiler, ContextCommand
from wio.context import Services as ContextServices
from wio.context.inputs import KnownInputs
from wio.context.no_roots import NoRootsWarning
from wio.contracts import WorkLookup

if TYPE_CHECKING:
    from tests.sandbox import Sandbox

_CONFIG = """\
[actions.deliver]
description = "Deliver"
[roots.api]
paths = []
[roots.contract]
paths = []
[stages.review]
goal = "Review"
"""


class _Composer:
    """Give a fixed bundle, independent of Work metadata."""

    def compose(self, work_id: str, action: str, stage: str) -> CompiledBundle:
        """Give the fixed bundle for the requested stage.

        Args:
            work_id: The Work's id.
            action: The action.
            stage: The stage.

        Returns:
            The fixed bundle.
        """
        assert (work_id, action, stage) == ("k3m9xq", "deliver", "review")
        return CompiledBundle("fixed bundle\n", "123456789abc", 0, {})


@pytest.mark.slow
@pytest.mark.xfail(strict=True, raises=NotImplementedError)
@pytest.mark.parametrize("roots", ["roots = []\n", "", 'roots = ["@descendants"]\n'])
@pytest.mark.parametrize("selection", ["", 'roots = ["contract", "@work"]\n'])
def test_empty_expanded_work_roots_warn_with_fixed_composer(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch, roots: str, selection: str
) -> None:
    """AC-1: real metadata and hierarchy produce a warning with the bundle."""
    # Given a real repository with one Work and a stage selecting its roots
    config = sandbox.root / ".agents/wio/config.toml"
    config.parent.mkdir(parents=True)
    config.write_text(_CONFIG + selection)
    work = sandbox.root / ".agents/wio/works/demo/README.md"
    work.parent.mkdir(parents=True)
    work.write_text(f'<!-- wio\nid = "k3m9xq"\n{roots}-->\n\n# Demo\n')
    git(sandbox, "init", "-q", check=True)
    enter(sandbox, monkeypatch)
    project = _contracts_services()
    works = WorkLookup(
        project.settings,
        project.repository,
        project.catalog,
        project.files,
        [project.files],
    )
    assert works.roots_of("k3m9xq") == ()
    checks = (
        KnownInputs(project.settings, works),
        NoRootsWarning(project.settings, works),
    )
    services = ContextServices(project.repository, project.files, project.environment)
    command = ContextCommand(services, Compiler(_Composer(), checks).compile)
    out, err = io.StringIO(), io.StringIO()

    # When the command runs through the real checks and fixed composer
    code = command.run(
        Namespace(work="k3m9xq", action="deliver", stage="review"),
        MemoryStdio(io.StringIO(), out, err),
    )

    # Then it prints the bundle and one warning naming the Work and its roots
    assert (code, out.getvalue()) == (0, "fixed bundle\n")
    assert len(err.getvalue().splitlines()) == 1
    assert err.getvalue().startswith("warning: ")
    assert "k3m9xq" in err.getvalue()
    assert "no roots" in err.getvalue()
