# SPDX-License-Identifier: Apache-2.0
"""The checks of the names that pipelines use for one another.

Every function is a `Check` of `wio.config.checks`: it reads the `Config` and
returns diagnostics, and never raises for a problem of the config. The `Config`
is best effort, so a check skips what the shape already reported, such as a
list that holds no strings, and judges only names. A name that does not resolve
is an error whose message lists what exists, so an agent that edits the config
corrects it in one turn. The stub is the spec until the implementation stage
replaces it with a `.py` of the same annotations, and the wiring stage appends
the checks to `wio.config.CHECKS`.
"""

from collections.abc import Iterable, Mapping, Sequence

from wio.config.checks import CheckInputs
from wio.models.config import Config
from wio.models.diagnostics import Diagnostic

def check_stage_presets(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check the stages of every stage preset and of every default action.

    Args:
        config: The settings to check.
        inputs: Unused; the check reads no file.

    Returns:
        An error at `stage_presets.<name>[<i>]` for a stage that is not
        declared, naming it and listing the declared stages, and for a stage
        that repeats an earlier one in the same list. For `works.defaults.actions`:
        an error at the key for a string that is not a stage preset, which says
        a string is a stage preset id and lists the stage presets; an error at
        `<key>[<i>]` for a stage that is not declared or that repeats; and an
        error at the key for an action that `[actions]` does not declare, which
        lists the declared actions. An empty list is not an error.
    """
    ...

def check_stage_roots(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check that every root a stage selects is a root or `@work`.

    Args:
        config: The settings to check.
        inputs: Unused; the check reads no file.

    Returns:
        An error at `stages.<name>.roots[<i>]` for an entry that is neither a
        declared root nor `@work`, naming it and listing the declared roots and
        `@work`. A stage without `roots` is not judged.
    """
    ...

def check_actions(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check that `after` and `invalidated_by` name declared actions.

    Args:
        config: The settings to check.
        inputs: Unused; the check reads no file.

    Returns:
        An error at `actions.<name>.after[<i>]` for an action that is not
        declared, naming it and listing the declared actions, and for one that is
        on demand, saying so. One error for each `after` cycle, at
        `actions.<first>.after` where `<first>` is the least action name on the
        cycle, that names every action on it. An error at
        `actions.<name>.invalidated_by[<i>]` for an action that is not declared,
        also behind the prefixes `@descendants:` and `@dependencies:`, listing
        the declared actions. A note at the same place for any other entry that
        starts with `@`, saying that v0.2 reserves it.
    """
    ...

def check_gate_results(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check that `gates.results` is a vocabulary a gate can decide with.

    Args:
        config: The settings to check.
        inputs: Unused; the check reads no file.

    Returns:
        An error at `gates.results` when the list is empty or holds a result
        twice, saying that a result list needs at least one result and no
        duplicate.
    """
    ...

def find_cycles(after: Mapping[str, Sequence[str]]) -> tuple[tuple[str, ...], ...]:
    """Find the cycles of a graph by a depth-first search.

    Args:
        after: Each action's name mapped to the names it comes after. A name
            that is not a key has no edges, and an edge to it ends the search.

    Returns:
        One tuple of names for each cycle, each in the order of its edges and
        starting at its least name, and the tuples sorted. Every action that
        lies on a cycle is on exactly one tuple, so two actions that `after`
        each other are one cycle.
    """
    ...
