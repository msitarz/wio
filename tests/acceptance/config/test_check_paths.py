# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio config check` on paths, skills and templates."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_root_paths_are_normalized_inside_the_repository_and_unique(wio: Wio) -> None:
    """AC-1: faults are errors, and a missing path is a warning that exits 0."""
    # Given a config whose roots have faulty and repeated paths, and a config
    # whose only finding is a root path that does not exist yet
    # When `wio config check` runs on each
    errors_run = wio.check_config("paths-roots")
    errors, error_code = errors_run.lines, errors_run.exit_code
    warnings_run = wio.check_config("paths-missing")
    warnings, warning_code = warnings_run.lines, warnings_run.exit_code

    # Then the first prints the errors and exits 1, the second a warning and exits 0
    assert [line.split(": ")[1] for line in errors] == [
        "roots.a.paths[0]",
        "roots.a.paths[1]",
        "roots.a.paths[2]",
        "roots.a.paths[3]",
        "roots.b.paths[1]",
    ]
    assert all(line.startswith("error: ") for line in errors)
    assert error_code == 1
    assert warnings == ["warning: roots.docs.paths[0]: `docs/new` does not exist yet."]
    assert warning_code == 0


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_skill_is_found_in_the_repository_or_the_stage_fails(wio: Wio) -> None:
    """AC-2: a skill is found in the searched directories, never in the home."""
    # Given a config with skills found in the repository, a stage whose skill is
    # in no directory that is searched, and a skill path outside the repository
    # When `wio config check` runs
    lines_run = wio.check_config("paths-skills")
    lines, code = lines_run.lines, lines_run.exit_code

    # Then it prints an error at the stage and one at the path, and exits 1
    assert [line.split(": ")[1] for line in lines] == [
        "skills.paths[1]",
        "stages.c.skill",
    ]
    assert "the user's home is not searched" in lines[1]
    assert code == 1


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_templates_table_has_its_shape(wio: Wio) -> None:
    """AC-3: a bad directory or template name is an error at its key path."""
    # Given a config with `[templates] dir = "../t"` and an empty template name,
    # and a config without a `[templates]` table
    # When `wio config check` runs on each
    errors_run = wio.check_config("paths-templates")
    errors, error_code = errors_run.lines, errors_run.exit_code
    clean_run = wio.check_config("rich")
    clean, clean_code = clean_run.lines, clean_run.exit_code

    # Then the first prints an error at each key path and exits 1, the second
    # prints nothing about templates
    assert [line.split(": ")[1] for line in errors] == [
        "templates.dir",
        "templates.kinds.feature",
    ]
    assert error_code == 1
    assert clean == ["Config check passed!"]
    assert clean_code == 0


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_works_dir_outside_the_repository_fails(wio: Wio) -> None:
    """AC-4: the Works directory is a normalized path inside the repository."""
    # Given a config with `[works] dir = "/abs"`
    # When `wio config check` runs
    lines_run = wio.check_config("paths-works-dir")
    lines, code = lines_run.lines, lines_run.exit_code

    # Then it prints an error at `works.dir` and exits 1
    assert lines == [
        "error: works.dir: `/abs` is absolute. The path must be inside the repository."
    ]
    assert code == 1
