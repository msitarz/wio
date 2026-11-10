# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio templates show`, which prints a template as a skeleton."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio


LEAF_SKELETON = (
    '<!-- wio\ntemplate = "feature.leaf"\nroots = []\n-->\n\n'
    "# Title\n\nWrite it.\n\n## A\n"
)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_show_prints_the_skeleton_of_the_named_template(wio: Wio) -> None:
    """AC-1: standard output is the skeleton, standard error is empty, exit 0."""
    # Given a project with the templates `feature.leaf` and `feature.parent`
    wio.fixture("templates/shown")

    # When `wio templates show feature.leaf` runs, and again
    first = wio.run(["templates", "show", "feature.leaf"])
    second = wio.run(["templates", "show", "feature.leaf"])

    # Then standard output is the skeleton of that file under that name, standard
    # error is empty, the exit code is 0 and the two outputs are equal
    assert first.stdout == LEAF_SKELETON
    assert (first.stderr, first.exit_code) == ("", 0)
    assert second == first


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_show_refuses_a_name_that_no_template_has(wio: Wio) -> None:
    """AC-2: each wrong name is an error that lists the names that exist."""
    # Given the same project, with the kind `feature`
    wio.fixture("templates/shown")

    # When `show nosuch`, `show Feature.Leaf` and `show feature` run
    outputs = {
        name: wio.run(["templates", "show", name])
        for name in ("nosuch", "Feature.Leaf", "feature")
    }

    # Then each names what was given, lists `feature.leaf` and `feature.parent`,
    # prints nothing to standard output and exits 2
    for name, output in outputs.items():
        assert f"`{name}`" in output.stderr
        assert "`feature.leaf`, `feature.parent`" in output.stderr
        assert (output.stdout, output.exit_code) == ("", 2)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_show_refuses_a_project_with_a_broken_neighbour(wio: Wio) -> None:
    """AC-3: a template error found by discovery refuses even a valid template."""
    # Given a project with the valid `feature.draft` and a template whose block
    # does not close
    wio.fixture("templates/broken")

    # When `wio templates show feature.draft` runs
    output = wio.run(["templates", "show", "feature.draft"])

    # Then it names the broken file and `wio templates check`, prints nothing to
    # standard output and exits 2
    assert ".agents/wio/templates/broken.md:1" in output.stderr
    assert "wio templates check" in output.stderr
    assert (output.stdout, output.exit_code) == ("", 2)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_show_names_the_line_and_column_of_a_bad_directive_list(wio: Wio) -> None:
    """AC-3: the error of the skeleton function names the file, line and column."""
    # Given a project whose `feature.leaf` has `## A <!-- wio: mandatory -->` on
    # line 12
    wio.fixture("templates/bad-list")

    # When `wio templates show feature.leaf` runs
    output = wio.run(["templates", "show", "feature.leaf"])

    # Then it names the file, line 12 and column 16, prints nothing to standard
    # output and exits 2
    assert ".agents/wio/templates/feature.leaf.md:12:16" in output.stderr
    assert "wio templates check" in output.stderr
    assert (output.stdout, output.exit_code) == ("", 2)


@pytest.mark.channels(Channel.CLI)
def test_show_with_a_wrong_command_line_is_a_usage_mistake(wio: Wio) -> None:
    """AC-4: no name, two names and `--json` exit 2, and the help names `show`."""
    # Given a repository
    wio.fixture("config/rich")

    # When `show`, `show a b` and `show feature.leaf --json` run, and then
    # `wio templates`
    wrong = [
        wio.run(["templates", "show"]),
        wio.run(["templates", "show", "a", "b"]),
        wio.run(["templates", "show", "feature.leaf", "--json"]),
    ]
    help_output = wio.run(["templates"])

    # Then each of the first three exits 2 with a usage message, and the help
    # names `show`
    for output in wrong:
        assert (output.exit_code, output.stdout) == (2, "")
        assert "usage:" in output.stderr
    assert "show" in help_output.stdout
