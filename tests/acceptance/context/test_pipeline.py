# SPDX-License-Identifier: Apache-2.0
"""Warnings about stages outside a Work's effective pipeline."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio


class _PipelineWarningMissingError(Exception):
    """A valid bundle was printed without the required pipeline warning."""


def _warning(stderr: str) -> None:
    """Require a warning after a successfully printed bundle.

    Args:
        stderr: The command's standard error.

    Raises:
        _PipelineWarningMissingError: The new warning has not been wired yet.
    """
    if not stderr:
        raise _PipelineWarningMissingError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.xfail(strict=True, raises=_PipelineWarningMissingError)
@pytest.mark.parametrize(
    ("work", "stage", "kind"),
    [
        ("a1b2c3", "define", "outside"),
        ("c3d4e5", "architecture", "missing"),
        ("d4e5f6", "architecture", "outside"),
        ("e5f6g7", "architecture", "missing"),
        ("h8i9j0", "architecture", "missing"),
        ("f6g7h8", "wiring", "outside"),
        ("g7h8i9", "architecture", "outside"),
    ],
)
def test_outside_or_missing_effective_pipeline_warns(
    wio: Wio, work: str, stage: str, kind: str
) -> None:
    """AC-1, AC-3–AC-5: effective pipeline choice produces the warning."""
    # Given Works with list, missing preset, override, removal and inherited actions
    wio.fixture("context/pipeline")

    if work == "h8i9j0":
        path = ".agents/wio/config.toml"
        config = wio.read(path).replace(b'deliver = ["implementation"]\n', b"", 1)
        wio.put(path, config)

    # When the requested stage is outside or has no pipeline
    result = wio.run(["context", work, "deliver", stage])

    # Then the bundle prints and one warning names the relevant request
    assert result.exit_code == 0
    assert result.stdout.startswith("bundle: ")
    _warning(result.stderr)
    assert len(result.stderr.splitlines()) == 1
    assert f"`{work}`" in result.stderr
    assert "`deliver`" in result.stderr
    if kind == "missing":
        assert f"The Work `{work}` has no action `deliver`." in result.stderr
    else:
        assert f"`{stage}`" in result.stderr


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize(
    ("work", "stage"),
    [
        ("a1b2c3", "architecture"),
        ("b2c3d4", "architecture"),
        ("f6g7h8", "architecture"),
        ("g7h8i9", "implementation"),
    ],
)
def test_stage_in_effective_pipeline_does_not_warn(
    wio: Wio, work: str, stage: str
) -> None:
    """AC-2, AC-4 and AC-5: list, preset, template and default include the stage."""
    # Given Works with list, preset, template and default pipelines
    wio.fixture("context/pipeline")

    # When the stage in the effective pipeline runs
    result = wio.run(["context", work, "deliver", stage])

    # Then the bundle prints without a warning
    assert (result.exit_code, result.stderr) == (0, "")
    assert result.stdout.startswith("bundle: ")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.xfail(strict=True, raises=_PipelineWarningMissingError)
def test_pipeline_warning_precedes_empty_roots_warning(wio: Wio) -> None:
    """The parent's two warnings appear once each, in order."""
    # Given a Work with no roots and a stage outside its action's pipeline
    wio.fixture("context/pipeline")
    path = ".agents/wio/works/list/README.md"
    wio.put(path, wio.read(path).replace(b'roots = ["api"]', b"roots = []"))

    # When the stage runs through the command's real wiring
    result = wio.run(["context", "a1b2c3", "deliver", "define"])

    # Then the bundle prints and the pipeline warning precedes the roots warning
    assert result.exit_code == 0
    assert result.stdout.startswith("bundle: ")
    lines = result.stderr.splitlines()
    if lines == ["warning: The Work `a1b2c3` has no roots."]:
        raise _PipelineWarningMissingError
    assert len(lines) == 2
    assert "`define`" in lines[0]
    assert "pipeline" in lines[0]
    assert "no roots" in lines[1]
