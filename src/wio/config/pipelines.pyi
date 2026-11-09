# SPDX-License-Identifier: Apache-2.0
"""The checks of the names that pipelines use for one another.

Every function is a `Check` of `wio.config.checks`: it reads the `Config` and
returns diagnostics, and never raises for a problem of the config. A check
judges the best-effort `Config` as it stands and only names, so an item that the
shape dropped is gone and the indexes after it shift, and a list that held no
string reads as empty. The shape's error comes first and its fix makes the key
paths of these checks true. A name that does not resolve
is an error whose message lists what exists, so an agent that edits the config
corrects it in one turn. Every `where` is a key path built with `join_path`
and `item_path`, so a name with a dot is quoted, and a message words its names
and lists with `quoted` and `and_list` of `wio.config.messages`. The checks are
appended to `wio.config.CHECKS`.
"""

from collections.abc import Iterable, Mapping, Sequence

from wio.config.checks import CheckInputs
from wio.models.config import Config
from wio.models.diagnostics import Diagnostic

def check_stage_references(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check the stages of every stage preset and the defaults of the actions.

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
        says it is not a declared action and lists the declared ones. A stage
        that is not declared and repeats gets the one error of the undeclared
        stage. An empty list is not an error.
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
        on demand, saying so. The cycles come from `find_cycles` on a graph of
        every declared action keyed by its `after` entries, where an entry that
        is not declared ends the search and an edge to an on-demand action is
        kept, so that action is also reported for it. One error for each
        cycle, which is a group of actions that reach one another, so cycles that
        share an action are one error, at `actions.<first>.after` where
        `<first>` is the least name `find_cycles` gives, that lists every action
        of the cycle in sorted order.
        An error at `actions.<name>.invalidated_by[<i>]` for an action that is
        not declared, naming the action after any prefix `@descendants:` or
        `@dependencies:` rather than the whole entry, and listing the declared
        actions; a prefix with no name
        after it is such an error. A note at the same place for any other entry
        that starts with `@`, a bare `@descendants` among them, saying that
        v0.2 reserves it. A valid entry gets no diagnostic.
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
        One tuple for each strongly connected component that has a cycle, so a
        self loop is one and two cycles that share an action are one. Its names
        are sorted, and the tuples are sorted by their first name, so every
        action that lies on a cycle is on exactly one tuple, and `a` and `b`
        that come after each other are `("a", "b")`.
    """
    ...
