# SPDX-License-Identifier: Apache-2.0
"""Tests of the checks of paths, skills and templates."""

import pytest


@pytest.mark.parametrize(
    "path",
    ["src", ".", "a/b", "src/", "a/./b", "a/../b", "../x", "/abs", ""],
    ids=[
        "normalized",
        "whole repository",
        "nested",
        "trailing slash",
        "dot segment",
        "dot-dot segment inside",
        "leaves the repository",
        "absolute",
        "empty",
    ],
)
def test_a_path_is_judged_as_text_and_gets_its_normalized_form(path: str) -> None:
    """AC-1: the first fault that applies, and the form that names the same place."""
    # Given a path as the config writes it
    # When it is judged
    # Then a normalized path has no fault, and any other has the first fault of
    # the order, with the normalized form where one exists
    del path
    pytest.skip("not implemented")


def test_root_paths_that_are_not_normalized_or_leave_the_repository_are_errors() -> (
    None
):
    """AC-1: each error names the rule and the normalized form where one exists."""
    # Given a root `a` with paths `src/`, `../x`, `/abs` and `a/./b`
    # When the root paths are checked
    # Then each is an error at its path that names the rule and the normalized form
    pytest.skip("not implemented")


def test_a_repeated_root_path_is_judged_on_its_normalized_text() -> None:
    """AC-1: the error names the first occurrence, and two roots may share a path."""
    # Given a root `b` with `src` twice and `src/` a third time, and a root `c`
    # with `src`
    # When the root paths are checked
    # Then each later path is an error that names the index of the first, and the
    # root `c` has none
    pytest.skip("not implemented")


def test_a_missing_root_path_is_a_warning_and_a_faulty_one_is_not_asked_about() -> None:
    """AC-1: only a valid path is looked for below the repository root."""
    # Given a root path `docs/new` that does not exist, one that exists, and an
    # absolute path
    # When the root paths are checked
    # Then the first is a warning, the second has no diagnostic, and the third
    # only its error
    pytest.skip("not implemented")


def test_a_skill_is_found_in_the_searched_directories_in_order() -> None:
    """AC-2: `skills.paths`, then `.agents/skills`, then `.claude/skills`."""
    # Given skills `a` in `.claude/skills` and `b` in a configured path, and a
    # stage with a goal
    # When the skills are checked
    # Then `a` and `b` pass and the stage with a goal is not judged
    pytest.skip("not implemented")


def test_a_skill_that_is_not_found_lists_where_wio_looked() -> None:
    """AC-2: the directories in order, and that the user's home is not searched."""
    # Given a stage naming `c`, which exists only in the user's home
    # When the skills are checked
    # Then an error at `stages.<name>.skill` lists the directories and says the
    # user's home is not searched
    pytest.skip("not implemented")


def test_a_skill_path_outside_the_repository_is_an_error_and_not_searched() -> None:
    """AC-2: a skill path follows the rule of a root path."""
    # Given `[skills] paths = ["../skills"]`
    # When the skills are checked
    # Then an error at `skills.paths[0]` says the path must stay inside the
    # repository, and the directories listed for a missing skill leave it out
    pytest.skip("not implemented")


def test_the_templates_table_needs_a_valid_dir_and_non_empty_template_names() -> None:
    """AC-3: each error names the key path and what a valid value is."""
    # Given `[templates] dir = "../t"` and a kind whose template name is empty
    # When the templates are checked
    # Then each is an error that names the key path and what a valid value is
    pytest.skip("not implemented")


def test_no_templates_table_gets_no_diagnostic() -> None:
    """AC-3: the defaults are valid."""
    # Given a config without a `[templates]` table
    # When the templates are checked
    # Then no diagnostic is returned
    pytest.skip("not implemented")


def test_a_works_dir_outside_the_repository_is_an_error() -> None:
    """AC-4: the directory is a normalized path inside the repository."""
    # Given `[works] dir = "/abs"`
    # When the Works directory is checked
    # Then an error at `works.dir` says the path must be inside the repository
    pytest.skip("not implemented")
