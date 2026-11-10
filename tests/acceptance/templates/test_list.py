# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio templates`, which finds and lists the templates."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_bare_templates_shows_the_help_of_the_component(wio: Wio) -> None:
    """AC-4: `wio templates` names `list` and exits 0."""
    # Given a repository
    wio.fixture("config/rich")

    # When `wio templates` runs
    output = wio.run(["templates"])

    # Then the output names `list` and the exit code is 0
    assert "list" in output.stdout
    assert output.exit_code == 0


@pytest.mark.skip(reason="Pending the implementation stage.")
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_list_groups_the_templates_by_kind(wio: Wio) -> None:
    """AC-5: kinds in order, the entry marked, columns aligned, descriptions kept."""
    # Given templates of three declared kinds and one undeclared kind
    # When the templates are listed
    # Then the lines are exactly those of the contract


@pytest.mark.skip(reason="Pending the implementation stage.")
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_list_can_be_limited_to_one_declared_kind(wio: Wio) -> None:
    """AC-5: `--kind` limits the list, and an undeclared kind is refused."""
    # Given the same project
    # When `--kind feature`, `--kind spec` and `--kind nosuch` run
    # Then the first prints one group, the second nothing, the third exits 2


@pytest.mark.skip(reason="Pending the implementation stage.")
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_list_prints_one_json_array(wio: Wio) -> None:
    """AC-5: `--json` prints the objects of the contract, sorted."""
    # Given the same project
    # When `--json` runs, alone and with `--kind feature`
    # Then one array of objects with the fields of the contract is printed


@pytest.mark.skip(reason="Pending the implementation stage.")
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_list_prints_nothing_for_a_project_without_templates(wio: Wio) -> None:
    """AC-5: no templates give nothing, or `[]` as JSON, and exit 0."""
    # Given a project with no templates
    # When the templates are listed, in text and as JSON
    # Then nothing is printed and `[]` is printed


@pytest.mark.skip(reason="Pending the implementation stage.")
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_list_refuses_a_project_with_a_template_error(wio: Wio) -> None:
    """AC-6: the errors are printed, nothing is listed and the exit code is 2."""
    # Given a project with a valid template and one whose block does not close
    # When `list`, `list --json` and `list --kind feature` run
    # Then each names the broken file and `wio templates check`, and exits 2


@pytest.mark.skip(reason="Pending the implementation stage.")
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_templates_of_this_repository_are_named_by_their_files(wio: Wio) -> None:
    """AC-7: the three `feature` templates are listed and have no `name` key."""
    # Given this repository
    # When the templates are listed
    # Then `feature.draft` is the entry, with the other two under `feature`
