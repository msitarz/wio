# SPDX-License-Identifier: Apache-2.0
"""Tests of what `wio.cli` gives `wio context`.

The run uses a real repository with a skill, a Work and a selected rule.
"""

from typing import TYPE_CHECKING

import pytest

from tests.support import enter, git
from wio.cli import main
from wio.cli.table import _context
from wio.io.adapters import SystemStdio

if TYPE_CHECKING:
    from tests.sandbox import Sandbox

_PROJECT = {
    ".agents/wio/config.toml": """\
rules_always_include = ["demo.ARC001"]
[works.defaults.actions]
deliver = ["architecture"]
[actions.deliver]
description = "Deliver"
[roots.api]
paths = []
[rulesets.demo]
root_independent = true
[stages.architecture]
skill = "example"
""",
    ".agents/wio/works/demo/README.md": """\
<!-- wio
id = "k3m9xq"
roots = ["api"]
-->

# Demo
""",
    ".agents/skills/example/SKILL.md": "Read the contract.\n",
    ".agents/wio/rules/demo/ruleset.toml": '[families]\nARC = "Architecture"\n',
    ".agents/wio/rules/demo/ARC001-use-ports.md": """\
<!-- wio
code = "ARC001"
name = "use-ports"
-->

Keep ports typed.
""",
}


def test_context_reads_the_project_through_the_adapters() -> None:
    """The entry wires the shell over the adapters of `wio.io` and `wio.env`."""
    # Given no setup

    # When `wio.cli` wires `wio context`; `tests.integration` may not import
    # `wio.context`, so the services are reached by their public name
    services = getattr(_context(), "services")  # noqa: B009
    found = [
        type(services.repository).__name__,
        type(services.files).__name__,
        type(services.environment).__name__,
        type(services.events).__name__,
    ]

    # Then they are the real adapters
    assert found == [
        "GitRepository",
        "LocalFileSystem",
        "ProcessEnvironment",
        "_ContextEventSink",
    ]


@pytest.mark.slow
def test_a_run_composes_the_project_work_skill_and_rule(
    sandbox: Sandbox,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Compose a bundle through the command's real project adapters.

    Args:
        sandbox: The isolated repository for the command.
        monkeypatch: Installs the repository as the working directory.
        capsys: Captures the command's output.
    """
    # Given a repository with a Work, a skill stage and one rule
    for name, contents in _PROJECT.items():
        path = sandbox.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
    git(sandbox, "init", "-q", check=True)
    enter(sandbox, monkeypatch)

    # When the command is run for the Work and stage
    code = main(["context", "k3m9xq", "deliver", "architecture"], SystemStdio())
    out, err = capsys.readouterr()

    # Then the bundle includes the Work, the skill location and the rule
    assert (code, err) == (0, "")
    assert "work: k3m9xq (Demo)" in out
    assert "rules: 1" in out
    assert "`.agents/skills/example/SKILL.md`" in out
    assert "--- contract ---\n\n# Demo" in out
    assert "demo: Architecture (ARC)" in out
    assert "demo.ARC001 use-ports\nKeep ports typed." in out
