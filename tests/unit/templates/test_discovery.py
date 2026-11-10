# SPDX-License-Identifier: Apache-2.0
"""Tests of the discovery of templates in `wio.templates`."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_walk_finds_the_marked_files_and_names_them_by_their_file() -> None:
    """AC-1: only marked `.md` files outside hidden directories are templates."""
    # Given a templates directory with two templates, a file with no block, a
    # hidden directory, an upper-case extension and a symbolic link
    # When the templates are found
    # Then they are `feature.leaf` and `feature.parent`, with no error


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_template_has_its_kind_shape_description_path_and_entry_mark() -> None:
    """AC-2: each field of a template is what its block and the config say."""
    # Given the kind `feature` with its entry and two templates, one with a shape
    # and a description and one with neither
    # When the templates are found
    # Then the entry is marked, the fields are present or `None`, and each has
    # its path


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_problem_in_reading_a_template_is_an_error_diagnostic() -> None:
    """AC-3: each problem is an error that names its place."""
    # Given a file that is not UTF-8, a block that does not close, a block with
    # no kind, a shape that is not a string, two files with one name, and a
    # directory that is missing, a file or a symbolic link
    # When the templates are found
    # Then each gives an error that names the file, the files or the directory,
    # the other templates are still returned after a file problem, and none
    # after a directory problem


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_missing_default_directory_holds_no_templates() -> None:
    """AC-3: the default directory may be absent, and no diagnostic is given."""
    # Given a repository with no templates directory and no `[templates] dir`
    # When the templates are found
    # Then there are none and no diagnostic
