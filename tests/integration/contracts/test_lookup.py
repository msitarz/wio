# SPDX-License-Identifier: Apache-2.0
"""Tests of `WorkLookup` on a real repository with real git behind it.

Each test is a stub for one criterion of the Work that builds the lookup, and
skips until the implementation stage fills it in. The examples use a Work
`k3m9xq`, a leaf under a parent that has a constraint `C-1`, with the items
`AC-1` and `AC-3` in its own sections, whose `deliver` is the `typed-boundary`
stage preset. "The working-tree adapter" is the lookup over the working tree and
`HEAD`, and "the index adapter" is the lookup over the index and `HEAD`.
"""

import pytest

STUB = "filled in by the implementation stage"


@pytest.mark.slow
def test_the_items_of_a_work_are_its_own() -> None:
    """AC-1: the working-tree adapter returns the Work's items and not the parent's."""
    # Given `k3m9xq` in the working tree
    # When `items("k3m9xq")` runs on the working-tree adapter
    # Then it returns `AC-1` and `AC-3` and not `C-1`
    pytest.skip(STUB)


@pytest.mark.slow
def test_the_pipeline_of_an_action_is_found_in_order() -> None:
    """AC-2: an action the Work has, and one it lacks."""
    # Given `k3m9xq` in the working tree
    # When `pipeline("k3m9xq", "deliver")` and `pipeline("k3m9xq", "nosuch")` run
    # Then the first returns the eight stages of `typed-boundary` in order and
    # the second returns `None`
    pytest.skip(STUB)


@pytest.mark.slow
def test_a_work_whose_contract_overrides_an_action_uses_its_own() -> None:
    """AC-2: the Work's `[actions]` replace the template's."""
    # Given a Work `m5n6p7` whose `[actions]` sets
    # `deliver = ["implementation", "implementation-review"]`
    # When `pipeline("m5n6p7", "deliver")` runs
    # Then it returns `implementation` and `implementation-review`
    pytest.skip(STUB)


@pytest.mark.slow
def test_a_work_that_only_head_has_is_found_by_both_adapters() -> None:
    """AC-3: a Work that the commit being made deletes is still found."""
    # Given a Work `d4e5f6` in `HEAD` and in neither the working tree nor the
    # index, with the item `AC-1` and `deliver` set to `["implementation"]`
    # When `items("d4e5f6")` and `pipeline("d4e5f6", "deliver")` run on each
    # adapter
    # Then each returns `AC-1` and `implementation`
    pytest.skip(STUB)


@pytest.mark.slow
def test_the_items_of_the_working_tree_and_the_index_may_differ() -> None:
    """AC-3: each adapter reads its own tree before `HEAD`."""
    # Given `k3m9xq` with the item `AC-3` in the working tree and without it in
    # the index
    # When `items("k3m9xq")` runs on each adapter
    # Then the working-tree adapter returns `AC-1` and `AC-3` and the index
    # adapter returns `AC-1`
    pytest.skip(STUB)


@pytest.mark.slow
def test_the_pipelines_of_the_working_tree_and_the_index_may_differ() -> None:
    """AC-3: each adapter reads its own `[actions]` before `HEAD`."""
    # Given `m5n6p7` whose `deliver` is `["implementation"]` in the working tree
    # and `["implementation", "implementation-review"]` in the index
    # When `pipeline("m5n6p7", "deliver")` runs on each adapter
    # Then the working-tree adapter returns `implementation` and the index
    # adapter returns `implementation` and `implementation-review`
    pytest.skip(STUB)


@pytest.mark.slow
def test_a_work_with_no_items_has_an_empty_set_and_not_none() -> None:
    """AC-4: a Work with no item in its own sections."""
    # Given a Work `p8q9r1` that has no item in its own sections
    # When `items("p8q9r1")` runs
    # Then it returns an empty `frozenset`, not `None`
    pytest.skip(STUB)


@pytest.mark.slow
def test_an_action_that_the_work_removed_is_none() -> None:
    """AC-4: an empty list in `[actions]` removes the action."""
    # Given `k3m9xq` with `[actions]` setting `amend = []`
    # When `pipeline("k3m9xq", "amend")` runs
    # Then it returns `None`
    pytest.skip(STUB)


@pytest.mark.slow
def test_an_unknown_id_is_absent() -> None:
    """AC-4: an id that is in no place gives `None` for both members."""
    # Given an id `zz9zz9` that is in no place
    # When `items("zz9zz9")` and `pipeline("zz9zz9", "deliver")` run
    # Then both return `None`
    pytest.skip(STUB)
