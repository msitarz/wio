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
    # Then the first prints the errors and exits 1, the second a warning and exits 0
    del wio
    pytest.skip("not implemented")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_skill_is_found_in_the_repository_or_the_stage_fails(wio: Wio) -> None:
    """AC-2: a skill is found in the searched directories, never in the home."""
    # Given a config with skills found in the repository, a stage whose skill is
    # in no directory that is searched, and a skill path outside the repository
    # When `wio config check` runs
    # Then it prints an error at the stage and one at the path, and exits 1
    del wio
    pytest.skip("not implemented")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_templates_table_has_its_shape(wio: Wio) -> None:
    """AC-3: a bad directory or template name is an error at its key path."""
    # Given a config with `[templates] dir = "../t"` and an empty template name,
    # and a config without a `[templates]` table
    # When `wio config check` runs on each
    # Then the first prints an error at each key path and exits 1, the second
    # prints nothing about templates
    del wio
    pytest.skip("not implemented")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_works_dir_outside_the_repository_fails(wio: Wio) -> None:
    """AC-4: the Works directory is a normalized path inside the repository."""
    # Given a config with `[works] dir = "/abs"`
    # When `wio config check` runs
    # Then it prints an error at `works.dir` and exits 1
    del wio
    pytest.skip("not implemented")
