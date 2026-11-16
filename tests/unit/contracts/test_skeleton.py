# SPDX-License-Identifier: Apache-2.0
"""Tests of how `skeleton` prepares the skeleton of an existing Work.

Each case is a scenario of the Work's acceptance criteria. The implementation
stage replaces a stub with the scenario and its fixture.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="architecture stub: the implementation stage fills it"
)


@pytest.mark.parametrize(
    "scenario",
    [
        "writes the skeleton and the note to their streams (AC-1)",
        "writes no note when nothing was dropped (AC-2)",
        "refuses a missing --work with the pointer to templates show (AC-4)",
        "reports the first mistake of the order (AC-4)",
        "refuses an incomplete tree with the pointer to check (AC-4)",
        "changes no file and prints the same bytes twice (AC-5)",
    ],
)
def test_run_skeleton(scenario: str) -> None:
    """run_skeleton: each case is one scenario of the contract."""
    # Given the inputs of the scenario
    # When `run_skeleton` runs
    # Then it gives what the contract says
    raise NotImplementedError


@pytest.mark.parametrize(
    "scenario",
    [
        "names the id and the closest one (AC-4)",
        "refuses a shared id with the error of discovery (AC-4)",
    ],
)
def test_find_work_by_id(scenario: str) -> None:
    """find_work_by_id: each case is one scenario of the contract."""
    # Given the inputs of the scenario
    # When `find_work_by_id` runs
    # Then it gives what the contract says
    raise NotImplementedError


@pytest.mark.parametrize(
    "scenario",
    [
        "points to list for a missing template (AC-4)",
        "points to check for a rejected template (AC-4)",
    ],
)
def test_usable_template(scenario: str) -> None:
    """usable_template: each case is one scenario of the contract."""
    # Given the inputs of the scenario
    # When `usable_template` runs
    # Then it gives what the contract says
    raise NotImplementedError


@pytest.mark.parametrize(
    "scenario",
    [
        "refuses each key that cannot be kept (AC-4)",
        "refuses those before a key the Work lacks (AC-4)",
        "lists the keys that can be kept in the order of the Work (AC-4)",
    ],
)
def test_check_keep(scenario: str) -> None:
    """check_keep: each case is one scenario of the contract."""
    # Given the inputs of the scenario
    # When `check_keep` runs
    # Then it gives what the contract says
    raise NotImplementedError


@pytest.mark.parametrize(
    "scenario",
    [
        "puts the id first and carries depends_on exactly (AC-1)",
        "leaves the template's depends_on for a Work with none (AC-3)",
        "gives an empty depends_on for an empty one (AC-1)",
        "carries a wrong type of depends_on as the file has it (AC-4)",
        "replaces a template key and adds a missing one when kept (AC-2)",
        "carries a kept table as a value (AC-2)",
        "lists the dropped keys in the order of the Work (AC-1)",
        "keeps the form, the endings and the body of the template (AC-3)",
    ],
)
def test_plan_skeleton(scenario: str) -> None:
    """plan_skeleton: each case is one scenario of the contract."""
    # Given the inputs of the scenario
    # When `plan_skeleton` runs
    # Then it gives what the contract says
    raise NotImplementedError


@pytest.mark.parametrize(
    "scenario",
    [
        "names the keys in order without values (AC-1)",
        "is empty when nothing was dropped (AC-2)",
        "writes the path with slashes (AC-1)",
    ],
)
def test_skeleton_note(scenario: str) -> None:
    """Skeleton.note: each case is one scenario of the contract."""
    # Given the inputs of the scenario
    # When `Skeleton.note` runs
    # Then it gives what the contract says
    raise NotImplementedError
