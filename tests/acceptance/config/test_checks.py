# SPDX-License-Identifier: Apache-2.0
"""Scenarios of the checks of the config taken together, as a person sees them."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

# The five problems of `checks-several`, one from each group of checks, in the
# order that the renderer sorts them.
SEVERAL = [
    "roots.out.paths[0]",
    "stage_presets.p[1]",
    "stages.build.skill",
    "stages.define.rules_include[0]",
    "works.nonsense",
]


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_one_run_reports_every_problem_once_and_sorted(wio: Wio) -> None:
    """AC-1: a problem in one group never hides another."""
    # Given a config with an unknown key, a stage preset that names a missing
    # stage, a rule reference to a missing ruleset, a root path outside the
    # repository and a stage whose skill exists nowhere, and nothing else wrong
    # When `wio config check` runs
    output = wio.check_config("checks-several")

    # Then each of the five is reported once, the output is sorted, and the exit
    # code is 1
    assert [line.split(": ")[1] for line in output.lines] == SEVERAL
    assert all(line.startswith("error: ") for line in output.lines)
    assert output.exit_code == 1


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_every_error_also_stops_the_other_commands(wio: Wio) -> None:
    """AC-2: `wio config list` refuses with the errors that `check` reports."""
    # Given the config with one error from each group
    checked = wio.check_config("checks-several")

    # When `wio config list` runs on it
    listed = wio.run(["config", "list"])

    # Then the command exits 2, standard output is empty, and standard error holds
    # each of the five errors, written as `check` writes them
    assert listed.exit_code == 2
    assert listed.stdout == ""
    assert listed.stderr.splitlines() == checked.lines


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_warnings_and_notes_show_only_in_the_check(wio: Wio) -> None:
    """AC-2: a warning and a note never change an exit code or reach `list`."""
    # Given a config with a root path that does not exist yet, which is a warning,
    # and a rule preset `p` with `rules_always_include = ["p"]`, which is a note
    checked = wio.check_config("checks-quiet")

    # When `wio config list` runs on it too
    listed = wio.run(["config", "list"])

    # Then `list` prints the settings and nothing of the warning or the note, and
    # `check` prints both and exits 0
    assert listed.exit_code == 0
    assert listed.stderr == ""
    assert "does not exist yet" not in listed.stdout
    assert "every session receives" not in listed.stdout
    assert [line.split(": ")[0] for line in checked.lines] == ["warning", "note"]
    assert checked.exit_code == 0
