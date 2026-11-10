# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio templates check`, which reports every template problem."""

import json
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

DIR = ".agents/wio/templates"


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_says_that_a_project_passes(wio: Wio) -> None:
    """AC-1: the text says so, the JSON is `[]`, and both exit 0."""
    # Given a project whose templates have no problem
    wio.fixture("templates/check-pass")

    # When `wio templates check` and `wio templates check --json` run
    text = wio.run(["templates", "check"])
    as_json = wio.run(["templates", "check", "--json"])

    # Then the first says that the templates pass and the second prints `[]`,
    # each exiting 0
    assert (text.stdout, text.stderr, text.exit_code) == (
        "The templates pass.\n",
        "",
        0,
    )
    assert (as_json.stdout, as_json.exit_code) == ("[]\n", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_passes_a_project_with_no_templates(wio: Wio) -> None:
    """AC-1: no templates directory and no kind is no problem."""
    # Given a project with no templates
    wio.fixture("templates/none")

    # When `wio templates check` runs
    output = wio.run(["templates", "check"])

    # Then it says that the templates pass and exits 0
    assert (output.stdout, output.exit_code) == ("The templates pass.\n", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_prints_two_problems_at_once(wio: Wio) -> None:
    """AC-1: both problems are printed in order, as text and as JSON, exit 1."""
    # Given a project with an unknown key in one template and a wrong directive
    # in another
    wio.fixture("templates/check-two")

    # When `wio templates check` and `wio templates check --json` run
    text = wio.run(["templates", "check"])
    as_json = wio.run(["templates", "check", "--json"])

    # Then the first prints both as `<severity>: <where>: <message>` lines and
    # the second one array of two objects, in that order, each exiting 1
    lines = text.lines
    assert len(lines) == 2
    assert lines[0].startswith(f"error: {DIR}/feature.draft.md: ")
    assert lines[1].startswith(f"error: {DIR}/other.md:7:16: ")
    data = json.loads(as_json.stdout)
    assert [(item["severity"], item["where"]) for item in data] == [
        ("error", f"{DIR}/feature.draft.md"),
        ("error", f"{DIR}/other.md:7:16"),
    ]
    assert (text.exit_code, as_json.exit_code) == (1, 1)


@pytest.mark.channels(Channel.CLI)
def test_check_refuses_a_config_with_an_error(wio: Wio) -> None:
    """AC-1: the config's error is printed and the exit code is 2."""
    # Given a project whose config has an error
    wio.fixture("config/invalid")

    # When `wio templates check` runs
    output = wio.run(["templates", "check"])

    # Then it prints that error and exits 2
    assert output.exit_code == 2
    assert output.stdout == ""
    assert "error" in output.stderr


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_reports_what_discovery_finds(wio: Wio) -> None:
    """AC-2: an unclosed block and a duplicate name."""
    # Given a project with a comment block that does not close and two files
    # named `a.md`
    wio.fixture("templates/check-discovery")

    # When `wio templates check` runs
    output = wio.run(["templates", "check"])

    # Then it prints an error for the block and one for the duplicate, naming the
    # files, and exits 1
    assert f"error: {DIR}/broken.md:1: " in output.stdout
    assert f"error: {DIR}/a.md, {DIR}/sub/a.md: " in output.stdout
    assert (len(output.lines), output.exit_code) == (2, 1)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_reports_a_missing_directory_alone(wio: Wio) -> None:
    """AC-2: one error that names the directory, and none for the entry."""
    # Given a project whose templates directory `t` is missing
    wio.fixture("templates/check-missing-dir")

    # When `wio templates check` runs
    output = wio.run(["templates", "check"])

    # Then it prints one error that names the directory and none for the entry
    # template, and exits 1
    assert output.lines == ["error: t: The templates directory does not exist"]
    assert output.exit_code == 1


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_reports_unknown_keys(wio: Wio) -> None:
    """AC-3: four errors that name the file and the key, none for `[contract]`."""
    # Given templates with `name`, `descriptions`, `contract = 1`, `actions = 1`
    # and a `[contract]` that holds `ticket = ""`
    wio.fixture("templates/check-keys")

    # When `wio templates check` runs
    output = wio.run(["templates", "check"])

    # Then the first four each give an error that names the file and the key, the
    # first saying that a template is named by its file, and the last gives none
    assert [line.split(": ")[1] for line in output.lines] == [
        f"{DIR}/{name}.md" for name in "abcd"
    ]
    assert "named by its file" in output.lines[0]
    assert "`descriptions`" in output.lines[1]
    assert "`contract`" in output.lines[2]
    assert "`actions`" in output.lines[3]
    assert output.exit_code == 1


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_names_the_line_and_column_of_a_directive_error(wio: Wio) -> None:
    """AC-4: the places are `<file>:12:16`, `<file>:14:6` and `<file>:16:7`."""
    # Given a template with a refused list on line 12, an unclosed one on line 14
    # and a list on a level-3 heading on line 16
    wio.fixture("templates/check-directives")

    # When `wio templates check` runs
    output = wio.run(["templates", "check"])

    # Then it prints an error for each at those places
    places = [line.split(": ")[1] for line in output.lines]
    assert places == [
        f"{DIR}/feature.draft.md:{where}" for where in ("12:16", "14:6", "16:7")
    ]
    assert "level-2 headings only" in output.lines[2]
    assert output.exit_code == 1


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_reports_names_the_config_does_not_declare(wio: Wio) -> None:
    """AC-5: undeclared names and wrong value types are errors, empty is not."""
    # Given a config declaring the action `define`, the stage preset
    # `define-feature` and the stage `implementation`, and templates whose
    # `[actions]` hold `define = "nosuch"`, `nosuch = "define-feature"`,
    # `define = ["nosuch"]`, `define = 1`, `define = [1]`, `define = []` and
    # `define = ["implementation"]`
    wio.fixture("templates/check-actions")

    # When `wio templates check` runs
    output = wio.run(["templates", "check"])

    # Then the first three name the file and the undeclared name, the next two
    # name the file and the key `define`, and the last two give none
    places = [line.split(": ")[1] for line in output.lines]
    assert places == [f"{DIR}/t{index}.md" for index in range(5)]
    assert all("`nosuch`" in line for line in output.lines[:3])
    assert all("`define` must be" in line for line in output.lines[3:])
    assert output.exit_code == 1


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_reports_a_kind_that_disagrees_with_the_config(wio: Wio) -> None:
    """AC-6: an undeclared kind, a missing entry and an entry of another kind."""
    # Given the kinds `feature = "feature.draft"` and `bugfix = "missing"`, a
    # template `feature.draft` of kind `bugfix`, and a template `other` of kind
    # `nokind`
    wio.fixture("templates/check-kinds")

    # When `wio templates check` runs
    output = wio.run(["templates", "check"])

    # Then it prints the three errors at their places and exits 1
    places = [line.split(": ")[1] for line in output.lines]
    assert places == [
        f"{DIR}/feature.draft.md",
        f"{DIR}/other.md",
        "templates.kinds.bugfix",
    ]
    assert "`nokind`" in output.lines[1]
    assert "`missing`" in output.lines[2]
    assert "entry template of `feature`" in output.lines[0]
    assert "kind `bugfix` differs" in output.lines[0]
    assert output.exit_code == 1


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_warns_of_a_repeated_heading_and_still_passes(wio: Wio) -> None:
    """AC-7: a warning at the second heading, and the exit code is 0."""
    # Given a template with `## Goals <!-- wio: required -->` and `## goals`
    wio.fixture("templates/check-repeat")

    # When `wio templates check` runs
    output = wio.run(["templates", "check"])

    # Then it prints a warning at the second heading that names the first line,
    # and exits 0
    assert output.lines == [
        f"warning: {DIR}/feature.draft.md:9: The heading repeats the one on line 7"
    ]
    assert (output.stderr, output.exit_code) == ("", 0)
