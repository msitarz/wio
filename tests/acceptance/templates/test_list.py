# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio templates`, which finds and lists the templates."""

from json import loads
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

FEATURE_GROUP = (
    "feature\n"
    "  feature.draft [entry] shape: draft\n"
    "    The working space of a new Work.\n"
    "  feature.leaf          shape: leaf\n"
    "    A capability\n"
    "    delivered as one outcome.\n"
)
FULL_LIST = f"bugfix\n  bugfix.fix\n\n{FEATURE_GROUP}\nold\n  old.note\n"


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


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_list_groups_the_templates_by_kind(wio: Wio) -> None:
    """AC-5: kinds in order, the entry marked, columns aligned, descriptions kept."""
    # Given templates of two declared kinds and one undeclared kind, and a third
    # declared kind that has none
    wio.fixture("templates/project")

    # When the templates are listed
    output = wio.run(["templates", "list"])

    # Then the lines are those of the contract, with the entry mark only in the
    # group where the config names an entry of its own kind
    assert output.stdout == FULL_LIST.replace("bugfix.fix\n", "bugfix.fix [entry]\n", 1)
    assert (output.stderr, output.exit_code) == ("", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_list_can_be_limited_to_one_declared_kind(wio: Wio) -> None:
    """AC-5: `--kind` limits the list, and an undeclared kind is refused."""
    # Given the same project
    wio.fixture("templates/project")

    # When `--kind feature`, `--kind spec` and `--kind nosuch` run
    one = wio.run(["templates", "list", "--kind", "feature"])
    empty = wio.run(["templates", "list", "--kind", "spec"])
    unknown = wio.run(["templates", "list", "--kind", "nosuch"])

    # Then the first prints one group, the second nothing, the third names the
    # kind and the declared kinds and exits 2
    assert (one.stdout, one.exit_code) == (FEATURE_GROUP, 0)
    assert (empty.stdout, empty.exit_code) == ("", 0)
    assert unknown.exit_code == 2
    assert "`nosuch`" in unknown.stderr
    assert "`bugfix`, `feature`, `spec`" in unknown.stderr
    assert unknown.stdout == ""


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_list_prints_one_json_array(wio: Wio) -> None:
    """AC-5: `--json` prints the objects of the contract, sorted."""
    # Given the same project
    wio.fixture("templates/project")

    # When `--json` runs, alone and with `--kind feature`
    everything = wio.run(["templates", "list", "--json"])
    feature = wio.run(["templates", "list", "--kind", "feature", "--json"])

    # Then the first is one array sorted by kind and name, with `null` for what a
    # template lacks, and the second holds the objects of that kind
    found = loads(everything.stdout)
    assert [(item["kind"], item["name"]) for item in found] == [
        ("bugfix", "bugfix.fix"),
        ("feature", "feature.draft"),
        ("feature", "feature.leaf"),
        ("old", "old.note"),
    ]
    assert (found[0]["shape"], found[0]["entry"]) == (None, True)
    assert found[0]["path"] == ".agents/wio/templates/bugfix.fix.md"
    assert found[2]["description"] == "A capability\ndelivered as one outcome.\n"
    assert [item["name"] for item in loads(feature.stdout)] == [
        "feature.draft",
        "feature.leaf",
    ]
    assert everything.exit_code == feature.exit_code == 0


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_list_prints_nothing_for_a_project_without_templates(wio: Wio) -> None:
    """AC-5: no templates give nothing, or `[]` as JSON, and exit 0."""
    # Given a project with no templates directory
    wio.fixture("templates/none")

    # When the templates are listed, in text and as JSON
    text = wio.run(["templates", "list"])
    machine = wio.run(["templates", "list", "--json"])

    # Then nothing is printed, and `[]` is printed, each exiting 0
    assert (text.stdout, text.exit_code) == ("", 0)
    assert (machine.stdout, machine.exit_code) == ("[]\n", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_list_refuses_a_project_with_a_template_error(wio: Wio) -> None:
    """AC-6: the errors are printed, nothing is listed and the exit code is 2."""
    # Given a project with a valid template and one whose block does not close
    wio.fixture("templates/broken")

    # When `list`, `list --json` and `list --kind feature` run
    outputs = [
        wio.run(["templates", "list"]),
        wio.run(["templates", "list", "--json"]),
        wio.run(["templates", "list", "--kind", "feature"]),
    ]

    # Then each names the broken file and `wio templates check`, lists nothing
    # and exits 2
    for output in outputs:
        assert ".agents/wio/templates/broken.md:1" in output.stderr
        assert "wio templates check" in output.stderr
        assert (output.stdout, output.exit_code) == ("", 2)
