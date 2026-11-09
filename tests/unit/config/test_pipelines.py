# SPDX-License-Identifier: Apache-2.0
"""Tests of the checks of actions, stages and stage presets."""

import pytest


def test_a_missing_stage_and_a_repeated_stage_in_a_stage_preset_are_errors() -> None:
    """AC-1: the error names the stage and lists the declared ones."""
    # Given a stage preset with an undeclared stage and one that repeats a stage
    # When the stage presets are checked
    # Then an error at `stage_presets.p[1]` lists the stages and one at
    # `stage_presets.q[1]` says the stage repeats
    pytest.skip("stub: the implementation stage writes this test")


def test_default_actions_name_a_stage_preset_or_stages_of_a_declared_action() -> None:
    """AC-1: each of the five faults of `works.defaults.actions` has its error."""
    # Given default actions with an unknown stage preset, a string that is a
    # stage, an unknown and a repeated stage in a list, an undeclared action, and
    # a valid list
    # When the stage presets are checked
    # Then each fault is an error at its own key path, and the valid list passes
    pytest.skip("stub: the implementation stage writes this test")


def test_a_shape_error_is_not_reported_again() -> None:
    """AC-1: the checks skip what the shape already reported."""
    # Given a best-effort config whose stage preset holds no stage names
    # When the stage presets are checked
    # Then no diagnostic is returned
    pytest.skip("stub: the implementation stage writes this test")


def test_an_unknown_root_of_a_stage_is_an_error_and_work_is_not() -> None:
    """AC-2: the error lists the declared roots and `@work`."""
    # Given a stage with the roots `contract` and `src`, and `@work`, where `src`
    # is not a root
    # When the stage roots are checked
    # Then an error at `stages.define.roots[1]` names `src` and lists the roots
    pytest.skip("stub: the implementation stage writes this test")


def test_an_after_cycle_an_on_demand_action_and_an_unknown_action_are_errors() -> None:
    """AC-3: one error for the cycle, and one for each bad entry."""
    # Given actions that form a cycle, come after an on-demand action, come
    # after an unknown action and are invalidated by unknown actions
    # When the actions are checked
    # Then there is one error for the cycle and one at each bad entry
    pytest.skip("stub: the implementation stage writes this test")


def test_an_invalidated_by_entry_reserved_for_v02_is_a_note() -> None:
    """AC-3: an `@` form other than the two known prefixes is a note."""
    # Given an `invalidated_by` entry `@children:a`
    # When the actions are checked
    # Then a note says it is reserved, and no error is returned
    pytest.skip("stub: the implementation stage writes this test")


@pytest.mark.parametrize("results", [(), ("pass", "pass")], ids=["empty", "duplicate"])
def test_an_empty_or_duplicated_gate_vocabulary_is_an_error(
    results: tuple[str, ...],
) -> None:
    """AC-4: `gates.results` needs a result and no duplicate."""
    # Given `gates.results` set to `results`
    # When the gate results are checked
    # Then an error at `gates.results` says what a result list needs
    del results
    pytest.skip("stub: the implementation stage writes this test")


@pytest.mark.parametrize(
    "graph", ["no edges", "one cycle", "two cycles", "self loop", "unknown name"]
)
def test_find_cycles_gives_each_cycle_once_from_its_least_name(graph: str) -> None:
    """AC-3: a cycle is reported once, however many actions reach it."""
    # Given the graph of `after` edges called `graph`
    # When its cycles are found
    # Then each cycle is a tuple that starts at its least name, in sorted order
    del graph
    pytest.skip("stub: the implementation stage writes this test")
