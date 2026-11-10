# SPDX-License-Identifier: Apache-2.0
"""Tests of showing a template as a skeleton in `wio.templates`."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_skeleton_of_the_named_template_is_what_the_skeleton_function_gives() -> (
    None
):
    """AC-1: the text is the skeleton of that file under the template's name."""
    # Given a project with the templates `feature.leaf` and `feature.parent`
    # When the skeleton of `feature.leaf` is shown, and again
    # Then it is what the skeleton function gives for that file's text under that
    # name, and the two results are equal


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_name_that_no_template_has_lists_the_names_that_exist() -> None:
    """AC-2: an unknown name, another case and a kind are refused with the names."""
    # Given the same project, with the kind `feature`
    # When `nosuch`, `Feature.Leaf` and `feature` are shown
    # Then each raises an error that names what was given and lists
    # `feature.leaf` and `feature.parent`


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_project_without_templates_says_that_none_exists() -> None:
    """AC-2: with no template, the refusal says so instead of listing nothing."""
    # Given a project with no templates
    # When a name is shown
    # Then the error names it and says that no template exists


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_bad_directive_list_names_the_file_the_line_and_the_column() -> None:
    """AC-3: the file is added to the error of the skeleton function."""
    # Given a template whose line 12 is `## A <!-- wio: mandatory -->`
    # When it is shown
    # Then the error holds one diagnostic whose place is the file, line 12 and
    # column 16, and says that `wio templates check` shows every problem


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_template_that_the_skeleton_function_refuses_names_its_file() -> None:
    """AC-3: a block that does not close in the shown template names the file."""
    # Given a template whose block does not close, read after discovery
    # When it is shown
    # Then the error holds one diagnostic whose place is the file and line 1
