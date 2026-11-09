# SPDX-License-Identifier: Apache-2.0
"""Tests of the checks of actions, stages and stage presets."""

import pytest


def test_a_missing_stage_and_a_repeated_stage_in_a_stage_preset_are_errors() -> None:
    """AC-1: the error names the stage and lists the declared ones."""
    # Given a stage preset with an undeclared stage and one that repeats a stage
    # When the stage presets are checked
    # Then an error at `stage_presets.p[1]` lists the stages and one at
    # `stage_presets.q[1]` says the stage repeats
    pytest.skip("not implemented")


def test_default_actions_name_a_stage_preset_or_stages_of_a_declared_action() -> None:
    """AC-1: each of the five faults of `works.defaults.actions` has its error."""
    # Given default actions with an unknown stage preset, a string that is a
    # stage, an unknown and a repeated stage in a list, an undeclared action, and
    # a valid list
    # When the stage presets are checked
    # Then each fault is an error at its own key path, and the valid list passes
    pytest.skip("not implemented")


def test_an_item_the_shape_dropped_shifts_the_indexes_after_it() -> None:
    """AC-1: a check judges the best-effort `Config` as it stands."""
    # Given a best-effort config whose stage preset lost a non-string item
    # When the stage references are checked
    # Then the errors name the indexes of the items that were kept
    pytest.skip("not implemented")


def test_a_stage_without_roots_and_an_empty_list_are_not_errors() -> None:
    """AC-1, AC-2: a stage may leave `roots` unset, and a list may be empty."""
    # Given a stage without `roots`, a stage with `roots = []`, and an empty stage
    # preset and an empty default action list
    # When the stage references are checked
    # Then no diagnostic is returned
    pytest.skip("not implemented")


def test_an_unknown_root_of_a_stage_is_an_error_and_work_is_not() -> None:
    """AC-2: the error lists the declared roots and `@work`."""
    # Given a stage with the roots `contract` and `src`, and `@work`, where `src`
    # is not a root
    # When the stage roots are checked
    # Then an error at `stages.define.roots[1]` names `src` and lists the roots
    pytest.skip("not implemented")


def test_an_after_cycle_an_on_demand_action_and_an_unknown_action_are_errors() -> None:
    """AC-3: one error for the cycle, and one for each bad entry."""
    # Given actions that form a cycle, come after an on-demand action, come
    # after an unknown action and are invalidated by unknown actions
    # When the actions are checked
    # Then there is one error for the cycle and one at each bad entry, and the
    # valid entries, a declared action and `@dependencies:` of one, get none
    pytest.skip("not implemented")


def test_an_after_entry_that_starts_with_at_is_an_error() -> None:
    """AC-3: `after` has no `@` form, so the entry is not a declared action."""
    # Given an action that comes after `@descendants:deliver`
    # When the actions are checked
    # Then an error at `actions.<name>.after[0]` names it and lists the actions
    pytest.skip("not implemented")


def test_a_self_loop_and_a_cycle_through_an_on_demand_action_are_reported() -> None:
    """AC-3: both are found, and the on-demand edge is also its own error."""
    # Given an action that comes after itself, and a cycle through an on-demand
    # action
    # When the actions are checked
    # Then each cycle is one error, and the on-demand entry is one more
    pytest.skip("not implemented")


def test_nothing_that_exists_is_said_instead_of_listed() -> None:
    """AC-1, AC-2, AC-3: a message does not list an empty set."""
    # Given a config that declares no stages, no roots and no actions, and names
    # one of each
    # When the checks run
    # Then each message says there is none declared
    pytest.skip("not implemented")


def test_an_invalidated_by_entry_reserved_for_v02_is_a_note() -> None:
    """AC-3: an `@` form other than the two known prefixes is a note."""
    # Given `invalidated_by` entries `@children:a` and a bare `@descendants`,
    # and an `@descendants:` with no name
    # When the actions are checked
    # Then a note says each of the first two is reserved, and the last is an error
    pytest.skip("not implemented")


@pytest.mark.parametrize("results", [(), ("pass", "pass")], ids=["empty", "duplicate"])
def test_an_empty_or_duplicated_gate_vocabulary_is_an_error(
    results: tuple[str, ...],
) -> None:
    """AC-4: `gates.results` needs a result and no duplicate."""
    # Given `gates.results` set to `results`
    # When the gate results are checked
    # Then an error at `gates.results` says what a result list needs
    del results
    pytest.skip("not implemented")


@pytest.mark.parametrize(
    "graph",
    ["no edges", "one cycle", "two cycles", "shared name", "self loop", "unknown name"],
)
def test_find_cycles_gives_each_cycle_once_from_its_least_name(graph: str) -> None:
    """AC-3: a cycle is reported once, however many actions reach it."""
    # Given the graph of `after` edges called `graph`
    # When its cycles are found
    # Then each strongly connected cycle is one tuple of sorted names, and the
    # tuples are sorted
    del graph
    pytest.skip("not implemented")
