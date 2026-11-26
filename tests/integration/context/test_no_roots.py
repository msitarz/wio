# SPDX-License-Identifier: Apache-2.0
"""The warning with real Work lookup and a fixed bundle composer."""

from typing import TYPE_CHECKING

import pytest

from tests.integration.context.support import command, project, run
from wio.context.inputs import KnownInputs
from wio.context.no_roots import NoRootsWarning

if TYPE_CHECKING:
    from tests.sandbox import Sandbox
    from wio.context import ContextCommand

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


def _command(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch, roots: str, selection: str
) -> ContextCommand:
    """Build a command with real project checks and a fixed composer.

    Args:
        sandbox: The project repository.
        monkeypatch: Enters the project.
        roots: The Work's roots metadata.
        selection: The stage's roots setting.

    Returns:
        The command wired over the isolated project.
    """
    config = sandbox.root / ".agents/wio/config.toml"
    config.parent.mkdir(parents=True)
    config.write_text(_CONFIG + selection)
    work = sandbox.root / ".agents/wio/works/demo/README.md"
    work.parent.mkdir(parents=True)
    work.write_text(f'<!-- wio\nid = "k3m9xq"\n{roots}-->\n\n# Demo\n')
    services, works = project(sandbox, monkeypatch)
    settings = works.settings
    return command(
        services, (KnownInputs(settings, works), NoRootsWarning(settings, works))
    )


@pytest.mark.slow
@pytest.mark.parametrize("roots", ["roots = []\n", "", 'roots = ["@descendants"]\n'])
@pytest.mark.parametrize("selection", ["", 'roots = ["contract", "@work"]\n'])
def test_empty_expanded_work_roots_warn_with_fixed_composer(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch, roots: str, selection: str
) -> None:
    """AC-1: real metadata and hierarchy produce a warning with the bundle."""
    # Given a real Work with no roots at a stage selecting its roots
    context = _command(sandbox, monkeypatch, roots, selection)

    # When the real checks and fixed composer run
    code, out, err = run(context, "k3m9xq", "review")

    # Then the fixed bundle and one warning naming the Work are printed
    assert (code, out) == (0, "fixed bundle\n")
    assert len(err.splitlines()) == 1
    assert err.startswith("warning: ")
    assert "k3m9xq" in err
    assert "no roots" in err


@pytest.mark.slow
@pytest.mark.parametrize(
    ("roots", "selection"),
    [
        ('roots = ["api"]\n', ""),
        ("roots = []\n", 'roots = ["contract"]\n'),
        ("roots = []\n", "roots = []\n"),
    ],
)
def test_present_or_unselected_real_roots_do_not_warn(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch, roots: str, selection: str
) -> None:
    """AC-2: real present or unselected roots pass with the fixed bundle."""
    # Given a Work and a stage with the specified roots
    context = _command(sandbox, monkeypatch, roots, selection)

    # When the real checks and fixed composer run
    code, out, err = run(context, "k3m9xq", "review")

    # Then the fixed bundle is printed with no warning
    assert (code, out, err) == (0, "fixed bundle\n", "")
