# SPDX-License-Identifier: Apache-2.0
"""The checks of the names that pipelines use for one another.

Every function is a `Check` of `wio.config.checks`: it reads the `Config` and
returns diagnostics, and never raises for a problem of the config. A check
judges the best-effort `Config` as it stands and only names, so an item that the
shape dropped is gone and the indexes after it shift, and a list that held no
string reads as empty. The shape's error comes first and its fix makes the key
paths of these checks true. A name that does not resolve is an error whose
message lists what exists, or says there is none, so an agent that edits the
config corrects it in one turn. Every `where` is a key path built with `join_path`
and `item_path`, so a name with a dot is quoted, and a message words its names
and lists with `quoted` and `and_list` of `wio.config.messages`. The checks are
appended to `wio.config.CHECKS`.
"""

from typing import TYPE_CHECKING

from wio.config.messages import and_list, declared, item_path, join_path, quoted
from wio.models.diagnostics import Diagnostic

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from wio.config.checks import CheckInputs
    from wio.models.config import Config

# The prefixes of an `invalidated_by` entry that name an action of a related Work.
_PREFIXES = ("@descendants:", "@dependencies:")

_NEEDS = "a result list needs at least one result and no duplicate;"


def check_stage_references(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check the stages of every stage preset and the defaults of the actions.

    Args:
        config: The settings, whose stage presets and default actions are read.
        inputs: Unused; the stage references are read from the `Config` alone.

    Returns:
        An error for a stage or a default action that does not resolve, or a
        stage that repeats in one pipeline, at its key path. An empty list is
        not an error.
    """
    del inputs
    stages = sorted(config.stages)
    for name, pipeline in config.stage_presets.items():
        yield from _pipeline(join_path("stage_presets", name), pipeline, stages)
    yield from _default_actions(config, stages)


def check_stage_roots(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check that every root a stage selects is a root or `@work`.

    Args:
        config: The settings, whose stages are read.
        inputs: Unused; roots are named in the `Config`, never read from disk.

    Returns:
        An error at `stages.<name>.roots[<i>]` for a root that is neither
        declared nor `@work`, naming it and listing the declared roots and
        `@work`. A stage without `roots` is not judged.
    """
    del inputs
    known = [*sorted(config.roots), "@work"]
    for name, stage in config.stages.items():
        where = join_path(join_path("stages", name), "roots")
        for index, root in enumerate(stage.roots or ()):
            if root not in known:
                message = f"unknown root `{root}`. {_known('roots', known)}"
                yield _error(item_path(where, index), message)


def check_actions(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check that `after` and `invalidated_by` name declared actions.

    Args:
        config: The settings, whose actions are read.
        inputs: Unused; an action is judged against the other actions alone.

    Returns:
        An error for an `after` entry that is not a declared action or is on
        demand, one for each cycle of `after`, and one for an `invalidated_by`
        entry that names no declared action, also behind `@descendants:` and
        `@dependencies:`. A note for any other `@` entry of `invalidated_by`.
    """
    del inputs
    declared = sorted(config.actions)
    for name, action in config.actions.items():
        where = join_path("actions", name)
        yield from _after(join_path(where, "after"), action.after, config)
        yield from _invalidated_by(
            join_path(where, "invalidated_by"), action.invalidated_by, declared
        )
    yield from _cycles(config)


def check_gate_results(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check that `gates.results` is a vocabulary a gate can decide with.

    Args:
        config: The settings, whose `gates` table is read.
        inputs: Unused; the vocabulary is judged from the list itself.

    Returns:
        An error at `gates.results` when the list is empty or repeats a result.
    """
    del inputs
    results = config.gates.results
    repeated = sorted({item for item in results if results.count(item) > 1})
    if not results:
        yield _error("gates.results", f"{_NEEDS} this list is empty.")
    elif repeated:
        verb = "repeat" if len(repeated) > 1 else "repeats"
        yield _error("gates.results", f"{_NEEDS} {quoted(repeated)} {verb}.")


def find_cycles(after: Mapping[str, Sequence[str]]) -> tuple[tuple[str, ...], ...]:
    """Find the cycles of a graph by a depth-first search.

    Args:
        after: Each action's name mapped to the names it comes after. A name
            that is not a key has no edges, and an edge to it ends the search.

    Returns:
        One sorted tuple of names for each strongly connected component that has
        a cycle, a self loop included, and the tuples sorted by first name.
    """
    reach = {name: _reachable(after, name) for name in after}
    groups = {
        tuple(sorted(other for other in reach[name] if name in reach.get(other, ())))
        for name in after
        if name in reach[name]
    }
    return tuple(sorted(groups))


def _error(where: str, message: str) -> Diagnostic:
    """Build an error.

    Args:
        where: The key path.
        message: What is wrong and how to fix it.

    Returns:
        The diagnostic.
    """
    return Diagnostic("error", where, message)


def _known(kind: str, names: Sequence[str]) -> str:
    """List what exists, or say that nothing does.

    Args:
        kind: What the names are, in the plural, such as `stages`.
        names: The names that exist, in the order to list them.

    Returns:
        A sentence that lists the names, or says that none is declared.
    """
    return declared(f"Declared {kind}", f"No {kind} are declared.", names)


def _pipeline(
    where: str, names: Sequence[str], stages: Sequence[str]
) -> Iterable[Diagnostic]:
    """Check the stages of one pipeline.

    Args:
        where: The key path of the list.
        names: The stages the list names, in order.
        stages: The declared stages, sorted.

    Returns:
        An error for each stage that is not declared, and for each later
        mention of a declared stage.
    """
    seen: set[str] = set()
    for index, name in enumerate(names):
        at = item_path(where, index)
        if name not in stages:
            yield _error(at, f"unknown stage `{name}`. {_known('stages', stages)}")
        elif name in seen:
            yield _error(at, f"stage `{name}` repeats; a pipeline lists a stage once.")
        seen.add(name)


def _default_actions(config: Config, stages: Sequence[str]) -> Iterable[Diagnostic]:
    """Check `works.defaults.actions`.

    Args:
        config: The settings, whose default actions are read.
        stages: The declared stages, sorted.

    Returns:
        An error for an action that is not declared, for a string that is not a
        stage preset, and for the stages of a list.
    """
    presets = sorted(config.stage_presets)
    actions = sorted(config.actions)
    for name, value in config.works.defaults.actions.items():
        where = join_path("works.defaults.actions", name)
        if name not in actions:
            yield _error(
                where,
                f"`{name}` is not a declared action. {_known('actions', actions)}",
            )
        if not isinstance(value, str):
            yield from _pipeline(where, value, stages)
        elif value not in presets:
            yield _error(
                where,
                f"`{value}` is not a stage preset; a string is a stage preset id. "
                f"{_known('stage presets', presets)}",
            )


def _after(where: str, entries: Sequence[str], config: Config) -> Iterable[Diagnostic]:
    """Check the `after` entries of one action.

    Args:
        where: The key path of the list.
        entries: The actions it comes after.
        config: The settings, whose actions are read.

    Returns:
        An error for an entry that is not a declared action, an `@` entry
        among them, and for one that is on demand.
    """
    actions = sorted(config.actions)
    for index, entry in enumerate(entries):
        at = item_path(where, index)
        if entry not in config.actions:
            yield _error(at, f"unknown action `{entry}`. {_known('actions', actions)}")
        elif config.actions[entry].on_demand:
            yield _error(at, f"`{entry}` is on demand, so nothing comes after it.")


def _invalidated_by(
    where: str, entries: Sequence[str], declared: Sequence[str]
) -> Iterable[Diagnostic]:
    """Check the `invalidated_by` entries of one action.

    Args:
        where: The key path of the list.
        entries: The actions, or the `@` forms of them, that invalidate it.
        declared: The declared actions, sorted.

    Returns:
        An error for an entry that names no declared action, and a note for an
        `@` form that v0.2 reserves.
    """
    for index, entry in enumerate(entries):
        found = _invalidating(item_path(where, index), entry, declared)
        if found is not None:
            yield found


def _invalidating(at: str, entry: str, declared: Sequence[str]) -> Diagnostic | None:
    """Judge one `invalidated_by` entry.

    Args:
        at: The key path of the entry.
        entry: The action, or the `@` form of one.
        declared: The declared actions, sorted.

    Returns:
        A note for an `@` form that v0.2 reserves, an error for an entry that
        names no declared action, and `None` for a valid entry.
    """
    prefix = next((p for p in _PREFIXES if entry.startswith(p)), "")
    if entry.startswith("@") and not prefix:
        return Diagnostic("note", at, f"`{entry}` is reserved for v0.2 and ignored.")
    name = entry.removeprefix(prefix)
    if name in declared:
        return None
    return _error(
        at, f"unknown action `{name or entry}`. {_known('actions', declared)}"
    )


def _cycles(config: Config) -> Iterable[Diagnostic]:
    """Report each cycle of `after` once.

    Args:
        config: The settings, whose actions are read.

    Returns:
        An error at the `after` of the least action of each cycle.
    """
    graph = {name: action.after for name, action in config.actions.items()}
    for cycle in find_cycles(graph):
        where = join_path(join_path("actions", cycle[0]), "after")
        names = and_list([f"`{name}`" for name in cycle])
        phrase = "come after one another" if len(cycle) > 1 else "comes after itself"
        yield _error(where, f"{names} {phrase}; `after` has no cycle.")


def _reachable(graph: Mapping[str, Sequence[str]], start: str) -> set[str]:
    """Find the names that a name reaches by one edge or more.

    Args:
        graph: Each name mapped to the names it has an edge to.
        start: The name to start from.

    Returns:
        The names reached, `start` among them only when it lies on a cycle.
    """
    seen: set[str] = set()
    stack = list(graph[start])
    while stack:
        name = stack.pop()
        if name not in seen:
            seen.add(name)
            stack.extend(graph.get(name, ()))
    return seen
