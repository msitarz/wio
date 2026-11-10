# SPDX-License-Identifier: Apache-2.0
"""Tests of the rendering of `wio templates list` in `wio.templates`."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_human_form_groups_by_kind_and_aligns_the_columns() -> None:
    """AC-5: kinds in order, the entry marked, names padded, descriptions kept."""
    # Given templates of three kinds, with and without a shape and a description
    # When they are rendered for a person
    # Then the lines are exactly those of the contract, without trailing spaces


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_description_is_printed_as_written_with_its_outer_empty_lines_dropped() -> (
    None
):
    """AC-5: each line of a description is kept, and the empty lines around it go."""
    # Given a template whose description has two lines and empty lines around them
    # When it is rendered for a person
    # Then each line is indented under the name and the empty lines are dropped


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_json_form_is_one_sorted_array_and_loads_json_only_for_it() -> None:
    """AC-5: objects with the fields of the contract, and no `json` import otherwise."""
    # Given templates of two kinds, one without a shape and a description
    # When they are rendered as JSON, and for a person
    # Then the array is sorted by kind and name with `null` for the missing
    # fields, `[]` for none, and the human form does not import `json`
