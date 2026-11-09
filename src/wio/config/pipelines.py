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

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from wio.config.checks import CheckInputs
    from wio.models.config import Config
    from wio.models.diagnostics import Diagnostic


# The leaves are stubs of one shape until the implementation stage, so the
# duplicate detector skips them, and the markers go with the stubs.
# jscpd:ignore-start  # noqa: ERA001
def check_stage_references(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check the stages of every stage preset and the defaults of the actions.

    Args:
        config: The settings to check.
        inputs: Unused; the check reads no file.

    Returns:
        An error for a stage or a default action that does not resolve, or a
        stage that repeats in one pipeline, at its key path. An empty list is
        not an error.
    """
    del config, inputs
    return ()


def check_stage_roots(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check that every root a stage selects is a root or `@work`.

    Args:
        config: The settings to check.
        inputs: Unused; the check reads no file.

    Returns:
        An error at `stages.<name>.roots[<i>]` for a root that is neither
        declared nor `@work`. A stage without `roots` is not judged.
    """
    del config, inputs
    return ()


def check_actions(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check that `after` and `invalidated_by` name declared actions.

    Args:
        config: The settings to check.
        inputs: Unused; the check reads no file.

    Returns:
        An error for an `after` entry that is not a declared action or is on
        demand, one for each cycle of `after`, and one for an `invalidated_by`
        entry that names no declared action, also behind `@descendants:` and
        `@dependencies:`. A note for any other `@` entry of `invalidated_by`.
    """
    del config, inputs
    return ()


def check_gate_results(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check that `gates.results` is a vocabulary a gate can decide with.

    Args:
        config: The settings to check.
        inputs: Unused; the check reads no file.

    Returns:
        An error at `gates.results` when the list is empty or repeats a result.
    """
    del config, inputs
    return ()


def find_cycles(after: Mapping[str, Sequence[str]]) -> tuple[tuple[str, ...], ...]:
    """Find the cycles of a graph by a depth-first search.

    Args:
        after: Each action's name mapped to the names it comes after. A name
            that is not a key has no edges, and an edge to it ends the search.

    Returns:
        One sorted tuple of names for each strongly connected component that has
        a cycle, a self loop included, and the tuples sorted by first name.
    """
    del after
    return ()


# jscpd:ignore-end  # noqa: ERA001
