# SPDX-License-Identifier: Apache-2.0
"""Tests that the check run holds the checks of every Work in its own order."""

from typing import TYPE_CHECKING

import pytest

from tests.unit.config.fakes import run_order
from wio.config import paths, pipelines, selection

if TYPE_CHECKING:
    from wio.config.checks import Check

_WORKS: dict[str, list[Check]] = {
    "pipelines": [
        pipelines.check_stage_references,
        pipelines.check_stage_roots,
        pipelines.check_actions,
        pipelines.check_gate_results,
    ],
    "paths": [
        paths.check_root_paths,
        paths.check_skills,
        paths.check_templates,
        paths.check_works_dir,
    ],
    "selection": [
        selection.check_rule_references,
        selection.check_rule_preset_cycles,
        selection.check_rulesets,
        selection.check_always_include_note,
    ],
}


@pytest.mark.parametrize("work", _WORKS)
def test_the_check_run_includes_the_checks_of_a_work_in_its_order(work: str) -> None:
    """The loader runs the checks of a Work after the shape, so `check` prints them."""
    # Given the checks of a Work, in the order its contract gives
    ours = _WORKS[work]

    # When the check run's order of them is read
    found = run_order(ours)

    # Then all of them run, in that order, whatever the other Works append
    assert found == ours
