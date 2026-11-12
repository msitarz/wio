# SPDX-License-Identifier: Apache-2.0
"""Test stubs of the listing of Works.

Each stub is a scenario of the Work's acceptance criteria. The implementation
stage replaces its body with the scenario.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="architecture stub: the implementation stage fills it"
)


def test_a_parent_comes_before_its_children_and_each_child_is_indented() -> None:
    """Check a scenario of AC-1."""
    # Given nesting Works: a parent and three children, one with overrides, one
    # with dependencies, one with no heading
    # When the Works are rendered as text
    # Then the text is the one AC-1 gives
    raise NotImplementedError


def test_under_flat_every_work_is_at_the_same_indent() -> None:
    """Check a scenario of AC-2."""
    # Given flat Works with ids of different widths
    # When the Works are rendered as text
    # Then the ids are padded to the widest and the order is the order of the paths
    raise NotImplementedError


def test_json_is_one_array_in_the_order_of_the_paths() -> None:
    """Check a scenario of AC-3."""
    # Given the Works of AC-1
    # When they are rendered as JSON
    # Then one line parses to the objects of AC-3, with the fields in their order
    raise NotImplementedError


def test_a_tree_with_no_work_renders_nothing() -> None:
    """Check a scenario of AC-4."""
    # Given no Work
    # When it is rendered in each form
    # Then the text is empty and the JSON is `[]`
    raise NotImplementedError


def test_only_the_overrides_of_a_work_show() -> None:
    """Check a scenario of AC-1."""
    # Given a Work whose `[actions]` hold a preset, a list and an empty list
    # When it is rendered
    # Then each is written as `name = value` in the order written
    raise NotImplementedError
