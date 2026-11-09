# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio config check` on the names that pipelines use."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_stage_presets_and_default_actions_name_known_stages(wio: Wio) -> None:
    """AC-1: an unknown or repeated stage is an error that lists what exists."""
    # Given a config with a missing stage and a repeated stage in stage presets
    # and the faults of the default actions
    # When `wio config check` runs
    lines_run = wio.check_config("pipelines-stages")
    lines, code = lines_run.lines, lines_run.exit_code

    # Then it prints an error at each key path and exits 1
    where = [line.split(": ")[1] for line in lines]
    assert where == [
        "stage_presets.p[1]",
        "stage_presets.q[1]",
        "works.defaults.actions.build[1]",
        "works.defaults.actions.deliver",
        "works.defaults.actions.review",
        "works.defaults.actions.ship",
        "works.defaults.actions.twice[1]",
    ]
    assert all(line.startswith("error: ") for line in lines)
    assert code == 1


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_stage_with_an_unknown_root_fails(wio: Wio) -> None:
    """AC-2: the error lists the declared roots and `@work`."""
    # Given a config whose stage selects a root that is not declared
    # When `wio config check` runs
    lines_run = wio.check_config("pipelines-root")
    lines, code = lines_run.lines, lines_run.exit_code

    # Then it prints an error at `stages.<name>.roots[<i>]` and exits 1
    message = "unknown root `src`. Declared roots: `contract`, `@work`."
    assert lines == [f"error: stages.define.roots[1]: {message}"]
    assert code == 1


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_after_and_invalidated_by_name_declared_actions(wio: Wio) -> None:
    """AC-3: a cycle and undeclared actions are errors, a reserved entry a note."""
    # Given a config with an `after` cycle, an on-demand `after` and undeclared
    # actions, and a config whose only finding is an `@children:` entry
    # When `wio config check` runs on each
    errors_run = wio.check_config("pipelines-actions")
    errors, error_code = errors_run.lines, errors_run.exit_code
    notes_run = wio.check_config("pipelines-reserved")
    notes, note_code = notes_run.lines, notes_run.exit_code

    # Then the first prints the errors and exits 1, and the second prints the
    # note and exits 0
    assert [line.split(": ")[1] for line in errors] == [
        "actions.a.after",
        "actions.c.after[0]",
        "actions.e.invalidated_by[0]",
        "actions.e.invalidated_by[1]",
        "actions.h.after[0]",
        "actions.i.after[0]",
    ]
    assert error_code == 1
    assert len(notes) == 1
    assert notes[0].startswith("note: actions.a.invalidated_by[0]: ")
    assert note_code == 0


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize(
    "fixture", ["pipelines-results-empty", "pipelines-results-duplicate"]
)
def test_an_empty_or_duplicated_gate_vocabulary_fails(wio: Wio, fixture: str) -> None:
    """AC-4: an empty or duplicated `gates.results` is an error there."""
    # Given a config whose `gates.results` is empty or repeats a result
    # When `wio config check` runs
    lines_run = wio.check_config(fixture)
    lines, code = lines_run.lines, lines_run.exit_code

    # Then it prints an error at `gates.results` and exits 1
    assert len(lines) == 1
    assert lines[0].startswith("error: gates.results: a result list needs")
    assert code == 1
