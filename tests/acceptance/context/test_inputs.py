# SPDX-License-Identifier: Apache-2.0
"""Refusals of unknown context inputs at the command boundary."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_unknown_action_is_refused(wio: Wio) -> None:
    """AC-1: the refusal names the action and the declared actions."""
    # Given a Work and two declared actions
    wio.fixture("context/inputs")
    wio.put(
        ".agents/wio/works/demo/README.md",
        b'<!-- wio\nid = "k3m9xq"\nroots = ["api"]\n-->\n\n# Demo\n',
    )

    # When the action is misspelled
    result = wio.run(["context", "k3m9xq", "delivr", "implementation"])

    # Then no bundle is printed and the error lists the actions
    assert (result.exit_code, result.stdout) == (2, "")
    assert all(name in result.stderr for name in ("delivr", "define", "deliver"))


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_unknown_stage_is_refused(wio: Wio) -> None:
    """AC-2: the refusal names the stage and the declared stages."""
    # Given a Work and declared stages
    wio.fixture("context/inputs")
    wio.put(
        ".agents/wio/works/demo/README.md",
        b'<!-- wio\nid = "k3m9xq"\nroots = ["api"]\n-->\n\n# Demo\n',
    )

    # When a stage is unknown
    result = wio.run(["context", "k3m9xq", "deliver", "no-such-stage"])

    # Then no bundle is printed and the error lists the stages
    assert (result.exit_code, result.stdout) == (2, "")
    assert all(
        name in result.stderr
        for name in ("`no-such-stage`", "`implementation`", "`explicit`", "`own`")
    )


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_unknown_selected_work_root_is_refused(wio: Wio) -> None:
    """AC-3: implicit and explicit Work roots are checked."""
    # Given a Work with an undeclared root
    wio.fixture("context/inputs")

    # When stages selecting Work roots run
    results = [
        wio.run(["context", "k3m9xq", "deliver", stage])
        for stage in ("implementation", "explicit")
    ]

    # Then each refuses the root and names the Work without printing a bundle
    for result in results:
        assert (result.exit_code, result.stdout) == (2, "")
        assert "ghost" in result.stderr
        assert "k3m9xq" in result.stderr


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_unselected_work_root_does_not_block_bundle(wio: Wio) -> None:
    """AC-4: a stage selecting its own roots gets a bundle."""
    # Given a Work with an unknown root and a stage selecting its own roots
    wio.fixture("context/inputs")

    # When that stage runs
    result = wio.run(["context", "k3m9xq", "deliver", "own"])

    # Then a bundle is printed successfully
    assert (result.exit_code, result.stderr) == (0, "")
    assert result.stdout.startswith("bundle: ")
