# SPDX-License-Identifier: Apache-2.0
"""Tests of the checks of actions, stages and stage presets."""

from typing import TYPE_CHECKING

import pytest

from tests.unit.config.fakes import CONFIG, ROOT, FakeRepository, MemoryFileSystem
from wio.config import CHECKS, CheckInputs, load_config, pipelines
from wio.models.config import (
    Action,
    Config,
    Defaults,
    Gates,
    Root,
    Stage,
    Works,
)
from wio.models.frozen import freeze

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from wio.models.diagnostics import Diagnostic

_INPUTS = CheckInputs(ROOT, MemoryFileSystem())


def _config(
    *,
    stages: Mapping[str, Stage] | None = None,
    stage_presets: Mapping[str, tuple[str, ...]] | None = None,
    actions: Mapping[str, Action] | None = None,
    roots: Mapping[str, Root] | None = None,
    works: Works | None = None,
    gates: Gates | None = None,
) -> Config:
    """Build a `Config` from the plain mappings a test writes.

    Args:
        stages: The stages by name.
        stage_presets: The stages of each stage preset.
        actions: The actions by name.
        roots: The roots by name.
        works: The `works` table.
        gates: The `gates` table.

    Returns:
        The config, with defaults for what is not given.
    """
    return Config(
        stages=freeze(stages or {}),
        stage_presets=freeze(stage_presets or {}),
        actions=freeze(actions or {}),
        roots=freeze(roots or {}),
        works=works or Works(),
        gates=gates or Gates(),
    )


def _action(
    after: tuple[str, ...] = (), invalidated_by: tuple[str, ...] = ()
) -> Action:
    """Build an action with a description and the lists it is given.

    Args:
        after: The actions it comes after.
        invalidated_by: The actions that invalidate it.

    Returns:
        The action.
    """
    return Action("an action", after=after, invalidated_by=invalidated_by)


def _stage() -> Stage:
    """Build a stage with a goal.

    Returns:
        The stage.
    """
    return Stage(goal="a goal")


def _found(diagnostics: Iterable[Diagnostic]) -> dict[str, str]:
    """Index the severity and message of diagnostics by their place.

    Args:
        diagnostics: What a check returned.

    Returns:
        Each `where` mapped to its severity and message, joined by a colon.
    """
    return {d.where: f"{d.severity}: {d.message}" for d in diagnostics}


def test_the_check_run_includes_the_pipeline_checks_in_order() -> None:
    """AC-1 to AC-4: the loader runs them after the shape, so `check` prints them."""
    # Given the checks that the loader runs by default

    # When they are listed
    names = [check.__name__ for check in CHECKS]

    # Then the pipeline checks are among them, in the order of the contract
    assert names == [
        pipelines.check_stage_references.__name__,
        pipelines.check_stage_roots.__name__,
        pipelines.check_actions.__name__,
        pipelines.check_gate_results.__name__,
    ]


def test_a_missing_stage_and_a_repeated_stage_in_a_stage_preset_are_errors() -> None:
    """AC-1: the error names the stage and lists the declared ones."""
    # Given a stage preset with an undeclared stage and one that repeats a stage
    config = _config(
        stages={"define": _stage()},
        stage_presets={"p": ("define", "review"), "q": ("define", "define")},
    )

    # When the stage references are checked
    found = _found(pipelines.check_stage_references(config, _INPUTS))

    # Then an error at `stage_presets.p[1]` lists the stages and one at
    # `stage_presets.q[1]` says the stage repeats
    assert found == {
        "stage_presets.p[1]": "error: unknown stage `review`. Declared stages: "
        "`define`.",
        "stage_presets.q[1]": "error: stage `define` repeats; a pipeline lists a "
        "stage once.",
    }


def test_default_actions_name_a_stage_preset_or_stages_of_a_declared_action() -> None:
    """AC-1: each of the five faults of `works.defaults.actions` has its error."""
    # Given default actions with an unknown stage preset, a string that is a
    # stage, an unknown and a repeated stage in a list, an undeclared action, and
    # a valid list
    defaults: dict[str, str | tuple[str, ...]] = {
        "deliver": "missing",
        "review": "define",
        "build": ("define", "ghost"),
        "twice": ("define", "define"),
        "define": ("define",),
        "ship": ("define",),
    }
    declared = ("define", "deliver", "review", "build", "twice")
    config = _config(
        stages={"define": _stage()},
        stage_presets={"solo": ("define",)},
        works=Works(defaults=Defaults(actions=freeze(defaults))),
        actions={name: _action() for name in declared},
    )

    # When the stage references are checked
    found = _found(pipelines.check_stage_references(config, _INPUTS))

    # Then each fault is an error at its own key path, and the valid list passes
    assert set(found) == {
        "works.defaults.actions.deliver",
        "works.defaults.actions.review",
        "works.defaults.actions.build[1]",
        "works.defaults.actions.twice[1]",
        "works.defaults.actions.ship",
    }
    assert "Declared stage presets: `solo`." in found["works.defaults.actions.deliver"]
    assert "a string is a stage preset id" in found["works.defaults.actions.review"]
    assert "`ship` is not a declared action" in found["works.defaults.actions.ship"]
    assert "`define` repeats" in found["works.defaults.actions.twice[1]"]


def test_an_undeclared_stage_that_repeats_gets_one_error_for_each_mention() -> None:
    """AC-1: the undeclared stage takes precedence over the repetition."""
    # Given a stage preset that lists an undeclared stage twice
    config = _config(stage_presets={"p": ("ghost", "ghost")})

    # When the stage references are checked
    found = _found(pipelines.check_stage_references(config, _INPUTS))

    # Then each mention has one error, which says the stage is unknown
    assert set(found) == {"stage_presets.p[0]", "stage_presets.p[1]"}
    assert all("unknown stage `ghost`" in message for message in found.values())


def test_an_item_the_shape_dropped_shifts_the_indexes_after_it() -> None:
    """AC-1: a check judges the best-effort `Config` as it stands."""
    # Given a file whose stage preset holds a non-string item before a bad stage
    text = '[stage_presets]\np = ["define", 3, "ghost"]\n[stages.define]\ngoal = "g"\n'
    files = MemoryFileSystem({CONFIG: text})

    # When the config is loaded and checked
    loaded = load_config(FakeRepository(), files)

    # Then the stage that was kept is named by its index among the kept items
    unknown = [d.where for d in loaded.diagnostics if "unknown stage" in d.message]
    assert unknown == ["stage_presets.p[1]"]


def test_a_stage_without_roots_and_an_empty_list_are_not_errors() -> None:
    """AC-1, AC-2: a stage may leave `roots` unset, and a list may be empty."""
    # Given a stage without `roots`, a stage with `roots = []`, and an empty stage
    # preset and an empty default action list
    config = _config(
        stages={"a": _stage(), "b": Stage(goal="g", roots=())},
        stage_presets={"empty": ()},
        works=Works(defaults=Defaults(actions=freeze({"define": ()}))),
        actions={"define": _action()},
    )

    # When the stage references and roots are checked
    found = [
        *pipelines.check_stage_references(config, _INPUTS),
        *pipelines.check_stage_roots(config, _INPUTS),
    ]

    # Then no diagnostic is returned
    assert found == []


def test_an_unknown_root_of_a_stage_is_an_error_and_work_is_not() -> None:
    """AC-2: the error lists the declared roots and `@work`."""
    # Given a stage with the roots `contract` and `src`, and `@work`, where `src`
    # is not a root
    config = _config(
        roots={"contract": Root(paths=("a",))},
        stages={"define": Stage(goal="g", roots=("contract", "src", "@work"))},
    )

    # When the stage roots are checked
    found = _found(pipelines.check_stage_roots(config, _INPUTS))

    # Then an error at `stages.define.roots[1]` names `src` and lists the roots
    assert found == {
        "stages.define.roots[1]": "error: unknown root `src`. Declared roots: "
        "`contract`, `@work`."
    }


def test_an_after_cycle_an_on_demand_action_and_an_unknown_action_are_errors() -> None:
    """AC-3: one error for the cycle, and one for each bad entry."""
    # Given actions that form a cycle, come after an on-demand action, come
    # after an unknown action and are invalidated by unknown actions
    invalidated = ("f", "@descendants:g", "a", "@dependencies:b")
    config = _config(
        actions={
            "a": _action(after=("b",)),
            "b": _action(after=("a",)),
            "c": _action(after=("d",)),
            "d": Action("on demand", on_demand=True),
            "h": _action(after=("zzz",)),
            "e": _action(invalidated_by=invalidated),
        }
    )

    # When the actions are checked
    found = _found(pipelines.check_actions(config, _INPUTS))

    # Then there is one error for the cycle and one at each bad entry, and the
    # valid entries, a declared action and `@dependencies:` of one, get none
    assert set(found) == {
        "actions.a.after",
        "actions.c.after[0]",
        "actions.h.after[0]",
        "actions.e.invalidated_by[0]",
        "actions.e.invalidated_by[1]",
    }
    assert "`a` and `b` come after one another" in found["actions.a.after"]
    assert "`d` is on demand" in found["actions.c.after[0]"]
    assert "unknown action `zzz`" in found["actions.h.after[0]"]
    assert "unknown action `g`" in found["actions.e.invalidated_by[1]"]


def test_an_after_entry_that_starts_with_at_is_an_error() -> None:
    """AC-3: `after` has no `@` form, so the entry is not a declared action."""
    # Given an action that comes after `@descendants:deliver`
    config = _config(actions={"i": _action(after=("@descendants:deliver",))})

    # When the actions are checked
    found = _found(pipelines.check_actions(config, _INPUTS))

    # Then an error at `actions.i.after[0]` names it and lists the actions
    assert found == {
        "actions.i.after[0]": "error: unknown action `@descendants:deliver`. "
        "Declared actions: `i`."
    }


def test_a_self_loop_and_a_cycle_through_an_on_demand_action_are_reported() -> None:
    """AC-3: both are found, and the on-demand edge is also its own error."""
    # Given an action that comes after itself, and a cycle through an on-demand
    # action
    config = _config(
        actions={
            "s": _action(after=("s",)),
            "x": _action(after=("y",)),
            "y": Action("on demand", after=("x",), on_demand=True),
        }
    )

    # When the actions are checked
    found = _found(pipelines.check_actions(config, _INPUTS))

    # Then each cycle is one error, and the on-demand entry is one more
    assert set(found) == {"actions.s.after", "actions.x.after", "actions.x.after[0]"}
    assert "`x` and `y` come after one another" in found["actions.x.after"]
    assert "`y` is on demand" in found["actions.x.after[0]"]


def test_nothing_that_exists_is_said_instead_of_listed() -> None:
    """AC-1, AC-2, AC-3: a message does not list an empty set."""
    # Given configs that declare nothing and name a stage, a stage preset, an
    # action and a root
    presets = _config(stage_presets={"p": ("ghost",)})
    defaults = _config(works=Works(defaults=Defaults(actions=freeze({"x": "missing"}))))
    stage = _config(stages={"s": Stage(goal="g", roots=("src",))})

    # When the checks run
    found = [
        *pipelines.check_stage_references(presets, _INPUTS),
        *pipelines.check_stage_references(defaults, _INPUTS),
        *pipelines.check_stage_roots(stage, _INPUTS),
    ]

    # Then each message says what is declared, or that none is
    messages = [d.message for d in found]
    assert any("No stages are declared." in m for m in messages)
    assert any("No stage presets are declared." in m for m in messages)
    assert any("No actions are declared." in m for m in messages)
    assert any("Declared roots: `@work`." in m for m in messages)


def test_an_invalidated_by_entry_reserved_for_v02_is_a_note() -> None:
    """AC-3: an `@` form other than the two known prefixes is a note."""
    # Given `invalidated_by` entries `@children:a` and a bare `@descendants`,
    # and an `@descendants:` with no name
    entries = ("@children:a", "@descendants", "@descendants:")
    config = _config(actions={"a": _action(invalidated_by=entries)})

    # When the actions are checked
    found = _found(pipelines.check_actions(config, _INPUTS))

    # Then a note says each of the first two is reserved, and the last is an error
    assert found["actions.a.invalidated_by[0]"].startswith("note: ")
    assert found["actions.a.invalidated_by[1]"].startswith("note: ")
    assert found["actions.a.invalidated_by[2]"].startswith("error: ")
    assert "`@descendants:`" in found["actions.a.invalidated_by[2]"]


@pytest.mark.parametrize(
    ("results", "reason"),
    [((), "is empty"), (("pass", "pass"), "`pass` repeats")],
    ids=["empty", "duplicate"],
)
def test_an_empty_or_duplicated_gate_vocabulary_is_an_error(
    results: tuple[str, ...], reason: str
) -> None:
    """AC-4: `gates.results` needs a result and no duplicate."""
    # Given `gates.results` set to `results`
    config = _config(gates=Gates(results=results))

    # When the gate results are checked
    found = _found(pipelines.check_gate_results(config, _INPUTS))

    # Then an error at `gates.results` says what a result list needs
    assert set(found) == {"gates.results"}
    assert "needs at least one result and no duplicate" in found["gates.results"]
    assert reason in found["gates.results"]


def test_a_usable_gate_vocabulary_passes() -> None:
    """AC-4: the default vocabulary is not an error."""
    # Given the default settings

    # When the gate results are checked
    found = list(pipelines.check_gate_results(_config(), _INPUTS))

    # Then no diagnostic is returned
    assert found == []


@pytest.mark.parametrize(
    ("graph", "cycles"),
    [
        ({"a": (), "b": ("a",)}, ()),
        ({"a": ("b",), "b": ("a",)}, (("a", "b"),)),
        (
            {"a": ("b",), "b": ("a",), "c": ("d",), "d": ("c",)},
            (("a", "b"), ("c", "d")),
        ),
        ({"a": ("b", "c"), "b": ("a",), "c": ("a",)}, (("a", "b", "c"),)),
        ({"a": ("a",)}, (("a",),)),
        ({"a": ("zzz",), "b": ("a",)}, ()),
        ({"a": ("b",), "b": ("a",), "c": ("a",)}, (("a", "b"),)),
    ],
    ids=[
        "no edges",
        "one cycle",
        "two cycles",
        "shared name",
        "self loop",
        "unknown name",
        "path into a cycle",
    ],
)
def test_find_cycles_gives_each_cycle_once_from_its_least_name(
    graph: dict[str, tuple[str, ...]], cycles: tuple[tuple[str, ...], ...]
) -> None:
    """AC-3: a cycle is reported once, however many actions reach it."""
    # Given the graph of `after` edges

    # When its cycles are found
    found = pipelines.find_cycles(graph)

    # Then each strongly connected cycle is one tuple of sorted names, and the
    # tuples are sorted
    assert found == cycles
