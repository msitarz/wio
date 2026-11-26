# SPDX-License-Identifier: Apache-2.0
"""Warnings about stages outside a Work's effective pipeline."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio


def _outside(work: str, stage: str) -> str:
    """Word the warning for a stage outside the `deliver` pipeline.

    Args:
        work: The Work's id.
        stage: The requested stage.

    Returns:
        The whole line of the warning.
    """
    text = f"The stage `{stage}` is not in the `deliver` pipeline of `{work}`."
    return f"warning: {text}\n"


def _missing(work: str) -> str:
    """Word the warning for a Work with no `deliver` pipeline.

    Args:
        work: The Work's id.

    Returns:
        The whole line of the warning.
    """
    return f"warning: The Work `{work}` has no action `deliver`.\n"


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize(
    ("work", "stage", "warning"),
    [
        ("a1b2c3", "define", _outside("a1b2c3", "define")),
        ("c3d4e5", "architecture", _missing("c3d4e5")),
        ("f6g7h8", "wiring", _outside("f6g7h8", "wiring")),
        ("g7h8i9", "architecture", _outside("g7h8i9", "architecture")),
    ],
)
def test_outside_or_missing_effective_pipeline_warns(
    wio: Wio, work: str, stage: str, warning: str
) -> None:
    """AC-1, AC-4 and AC-5: list, preset, template and default pipelines warn."""
    # Given Works with list, missing preset, template and default pipelines
    wio.fixture("context/pipeline")

    # When the requested stage is outside or has no pipeline
    result = wio.run(["context", work, "deliver", stage])

    # Then the bundle prints with the one warning
    assert (result.exit_code, result.stderr) == (0, warning)
    assert result.stdout.startswith("bundle: ")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize(
    ("work", "warning"),
    [
        ("d4e5f6", _outside("d4e5f6", "architecture")),
        ("e5f6g7", _missing("e5f6g7")),
        ("h8i9j0", _missing("h8i9j0")),
    ],
)
def test_the_works_own_pipeline_decides(wio: Wio, work: str, warning: str) -> None:
    """AC-3: an override, a removal and an absence are judged as the Work's own."""
    # Given a config whose defaults give no `deliver`, and a Work that overrides
    # the template's, removes it, or has none
    wio.fixture("context/pipeline")
    path = ".agents/wio/config.toml"
    config = wio.read(path)
    wio.put(path, config.replace(b'deliver = ["implementation"]\n', b"", 1))

    # When a stage that the template's pipeline holds is requested
    result = wio.run(["context", work, "deliver", "architecture"])

    # Then the bundle prints with the one warning
    assert (result.exit_code, result.stderr) == (0, warning)
    assert result.stdout.startswith("bundle: ")


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
