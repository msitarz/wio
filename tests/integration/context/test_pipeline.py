# SPDX-License-Identifier: Apache-2.0
"""Effective pipeline warnings with real Work lookup and a fixed composer."""

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.integration.context.support import command, project, run
from wio.context.inputs import KnownInputs
from wio.context.no_roots import NoRootsWarning
from wio.context.pipeline import PipelineWarning, _PipelineNotImplementedError

if TYPE_CHECKING:
    from tests.sandbox import Sandbox

_FIXTURE = Path(__file__).resolve().parents[2] / "fixtures/context/pipeline"


@pytest.mark.slow
@pytest.mark.xfail(strict=True, raises=_PipelineNotImplementedError)
@pytest.mark.parametrize(
    ("work", "stage", "expected_pipeline", "warning"),
    [
        ("a1b2c3", "define", ["architecture", "wiring"], "outside"),
        ("c3d4e5", "architecture", None, "missing"),
        ("a1b2c3", "architecture", ["architecture", "wiring"], "none"),
        ("b2c3d4", "architecture", ["architecture"], "none"),
        ("d4e5f6", "architecture", ["implementation"], "outside"),
        ("e5f6g7", "architecture", None, "missing"),
        ("h8i9j0", "architecture", None, "missing"),
        ("f6g7h8", "architecture", ["architecture"], "none"),
        ("f6g7h8", "wiring", ["architecture"], "outside"),
        ("g7h8i9", "implementation", ["implementation"], "none"),
        ("g7h8i9", "architecture", ["implementation"], "outside"),
    ],
)
def test_effective_pipelines_with_fixed_composer(
    sandbox: Sandbox,
    monkeypatch: pytest.MonkeyPatch,
    work: str,
    stage: str,
    expected_pipeline: list[str] | None,
    warning: str,
) -> None:
    """AC-1–AC-5: actual Work actions, templates and defaults determine warnings."""
    # Given a real project and a fixed composer, with no default for absent action
    shutil.copytree(_FIXTURE, sandbox.root, dirs_exist_ok=True)
    config = sandbox.root / ".agents/wio/config.toml"
    if work == "h8i9j0":
        config.write_text(
            config.read_text().replace('deliver = ["implementation"]\n', "", 1)
        )
    services, works = project(sandbox, monkeypatch)
    assert works.pipeline(work, "deliver") == expected_pipeline
    context = command(
        services, (KnownInputs(works.settings, works), PipelineWarning(works))
    )

    # When the real checks and fixed composer run
    code, out, err = run(context, work, stage)

    # Then the fixed bundle and the expected warning are printed
    assert (code, out) == (0, "fixed bundle\n")
    if warning == "none":
        assert err == ""
    elif warning == "missing":
        assert err == f"warning: The Work `{work}` has no action `deliver`.\n"
    else:
        assert len(err.splitlines()) == 1
        assert all(part in err for part in (f"`{work}`", "`deliver`", f"`{stage}`"))


@pytest.mark.slow
@pytest.mark.xfail(strict=True, raises=_PipelineNotImplementedError)
def test_pipeline_warning_precedes_no_roots_warning(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The parent requires the pipeline warning before the no-roots warning."""
    # Given a Work with no roots and a stage outside its pipeline
    shutil.copytree(_FIXTURE, sandbox.root, dirs_exist_ok=True)
    work = sandbox.root / ".agents/wio/works/list/README.md"
    work.write_text(work.read_text().replace('roots = ["api"]', "roots = []"))
    services, works = project(sandbox, monkeypatch)
    checks = (
        KnownInputs(works.settings, works),
        PipelineWarning(works),
        NoRootsWarning(works.settings, works),
    )
    context = command(services, checks)

    # When the real checks and fixed composer run
    code, out, err = run(context, "a1b2c3", "define")

    # Then both warnings are printed once in the required order
    assert (code, out) == (0, "fixed bundle\n")
    warnings = err.splitlines()
    assert len(warnings) == 2
    assert "`define`" in warnings[0]
    assert "pipeline" in warnings[0]
    assert "no roots" in warnings[1]
