# SPDX-License-Identifier: Apache-2.0
"""Test stubs of the hierarchy and the dependency graph of the Works.

Each stub is one scenario of the Work's acceptance criteria. The
implementation stage replaces its body with the scenario.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="architecture stub: the implementation stage fills it"
)


def test_the_parent_is_the_nearest_directory_above_that_holds_a_work() -> None:
    """Check scenario of AC-1."""
    # Given `p`, `p/c1`, `p/c1/d`, `p/g/x` (`p/g` holds no Work) and `q`
    # When the hierarchy is built
    # Then children, ancestors, descendants and parents of each Work are as AC-1 states
    raise NotImplementedError


def test_a_directory_whose_work_was_left_out_is_passed_over() -> None:
    """Check scenario of AC-1."""
    # Given `p` and `p/m/k`, with `p/m/README.md` left out
    # When the hierarchy is built
    # Then the parent of `k` are as AC-1 states
    raise NotImplementedError


def test_under_flat_nobody_is_related_and_descendants_resolves_to_nothing() -> None:
    """Check scenario of AC-2."""
    # Given the Works of the first scenario of AC-1, with `p` listing
    # `@descendants` and `wio` and `d` listing `p`
    # When the hierarchy is built
    # Then the relations, the roots of `p` and the dependencies of `d` are as
    # AC-2 states
    raise NotImplementedError


def test_roots_resolve_through_the_children_into_one_sorted_set() -> None:
    """Check scenario of AC-3."""
    # Given `top`, `mid`, `deep`, `leaf`, `bad` and `solo` with their roots
    # When the hierarchy is built
    # Then the resolved roots of each are as AC-3 states
    raise NotImplementedError


def test_a_middle_parent_passes_up_what_its_own_roots_resolve_to() -> None:
    """Check scenario of AC-3."""
    # Given the previous tree with `mid` listing `@descendants`
    # When the hierarchy is built
    # Then the resolved roots of `mid` and `top` are as AC-3 states
    raise NotImplementedError


def test_dependents_are_the_works_that_list_the_id_and_a_parent_is_not_one() -> None:
    """Check scenario of AC-4."""
    # Given `a`, `d`, `c` and `p/b` under `p`
    # When the hierarchy is built
    # Then the dependents of `b` and the dependencies of `a` are as AC-4 states
    raise NotImplementedError


def test_an_unknown_id_is_one_error_for_each_work_and_id_and_a_shared_id_exists() -> (
    None
):
    """Check scenario of AC-4."""
    # Given `u1`, `u2`, `u3`, `r`, `s1` and `s2`
    # When the hierarchy is built
    # Then the diagnostics and the dependents of `s1` and `s2` are as AC-4 states
    raise NotImplementedError


def test_a_cycle_of_a_parent_that_lists_its_child_calls_the_edge_listed() -> None:
    """Check scenario of AC-5."""
    # Given a parent and a child that list each other
    # When the hierarchy is built
    # Then the one diagnostic are as AC-5 states
    raise NotImplementedError


def test_a_cycle_through_a_parent_names_the_implicit_edge() -> None:
    """Check scenario of AC-5."""
    # Given a parent and a child that lists the parent
    # When the hierarchy is built
    # Then the one diagnostic are as AC-5 states
    raise NotImplementedError


def test_overlapping_cycles_are_one_error_and_a_self_dependency_is_a_cycle_of_one() -> (
    None
):
    """Check scenario of AC-5."""
    # Given `a7b2c4`, `c9d4e6`, `b8c3d5` and `s5t3wx` under `flat`
    # When the hierarchy is built
    # Then the two diagnostics are as AC-5 states
    raise NotImplementedError


def test_two_separate_cycles_are_two_errors_in_order() -> None:
    """Check scenario of AC-5."""
    # Given `f4g5h6`, `e1f2g3`, `w4x5y6` and `t1v2w3` under `flat`
    # When the hierarchy is built
    # Then the two diagnostics are as AC-5 states
    raise NotImplementedError
