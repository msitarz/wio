# SPDX-License-Identifier: Apache-2.0
"""Real project adapters and a fixed composer for context checks."""

import io
from argparse import Namespace
from typing import TYPE_CHECKING

from tests.acceptance.drivers.in_process import MemoryStdio
from tests.support import enter, git
from wio.cli.table import _contracts_services
from wio.context import CompiledBundle, Compiler, ContextCommand
from wio.context import Services as ContextServices
from wio.contracts import WorkLookup

if TYPE_CHECKING:
    from collections.abc import Sequence

    import pytest

    from tests.sandbox import Sandbox
    from wio.context import Check


class _Composer:
    """Supply the same bundle regardless of the request."""

    def compose(self, work_id: str, action: str, stage: str) -> CompiledBundle:
        """Give the fixed bundle.

        Args:
            work_id: The Work's id.
            action: The requested action.
            stage: The requested stage.

        Returns:
            The fixed bundle.
        """
        del work_id, action, stage
        return CompiledBundle("fixed bundle\n", "123456789abc", 0, {})


def project(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> tuple[ContextServices, WorkLookup]:
    """Enter a git repository and wire real project services.

    Args:
        sandbox: The project repository.
        monkeypatch: Enters the project.

    Returns:
        The context services and working-tree Work lookup.
    """
    git(sandbox, "init", "-q", check=True)
    enter(sandbox, monkeypatch)
    contracts = _contracts_services()
    works = WorkLookup(
        contracts.settings,
        contracts.repository,
        contracts.catalog,
        contracts.files,
        [contracts.files],
    )
    services = ContextServices(
        contracts.repository, contracts.files, contracts.environment
    )
    return services, works


def command(services: ContextServices, checks: Sequence[Check]) -> ContextCommand:
    """Connect the supplied checks to the fixed composer.

    Args:
        services: The real context services.
        checks: The real checks in their run order.

    Returns:
        A command that prints the fixed bundle after the checks.
    """
    return ContextCommand(services, Compiler(_Composer(), tuple(checks)).compile)


def run(command: ContextCommand, work: str, stage: str) -> tuple[int, str, str]:
    """Run a context command and capture its output.

    Args:
        command: The command to run.
        work: The Work's id.
        stage: The stage of `deliver`.

    Returns:
        The exit code, standard output and standard error.
    """
    out, err = io.StringIO(), io.StringIO()
    code = command.run(
        Namespace(work=work, action="deliver", stage=stage),
        MemoryStdio(io.StringIO(), out, err),
    )
    return code, out.getvalue(), err.getvalue()
