# SPDX-License-Identifier: Apache-2.0
"""Scenario stubs of `wio contracts new`.

Each stub is a scenario of the Work's acceptance criteria. The implementation
stage replaces its body with the scenario.
"""

import pytest

# The implementation stage adds the sample repositories under
# `tests/fixtures/contracts`, named `new-*`, one for each project of the scenarios,
# each with its config and templates, and the DSL verb `read` that gives the
# text of a file of the sandbox. The real `Entropy` runs on both channels, so a
# scenario reads the new id from the report and puts it into the text it expects,
# and the scenarios that need fixed bytes (the exact id of AC-1) are unit tests.
# A scenario that runs `new` more than once starts each run from its own sandbox,
# by parametrizing the run, and asserts with `wio.fingerprint` that a mistake wrote
# nothing. AC-4 and AC-7 are unit tests too, because they name the template's
# block forms and a stand-in.

pytestmark = pytest.mark.skip(
    reason="architecture stub: the implementation stage fills it"
)


def test_a_work_is_created_from_the_entry_template_of_a_kind() -> None:
    """AC-1: scenario of the contract."""
    # Given a project with the kind `feature` and its entry template
    # When `wio contracts new feature --title "Read config" --root wio` runs
    # Then the file is the skeleton with the id, the roots and the heading, and
    # the report names the id and the path
    raise NotImplementedError


def test_any_template_can_be_used_and_kind_and_template_must_agree() -> None:
    """AC-2: scenario of the contract."""
    # Given a project with two kinds, a leaf template and a Work to be the parent
    # When `new` runs with a template and a parent, with a template alone, and
    # with a template of another kind
    # Then the first and second are written and the third is an error
    raise NotImplementedError


def test_a_bare_contract_holds_the_id_and_a_heading() -> None:
    """AC-3: scenario of the contract."""
    # Given a nesting project with no Work
    # When `new` runs with a slug, a title and a path
    # Then each is written as the bare contract and reported
    raise NotImplementedError


def test_a_mistake_creates_nothing() -> None:
    """AC-5: scenario of the contract."""
    # Given projects with no kinds, a missing entry template, a rejected one,
    # and the config of AC-1
    # When `new` runs with each mistake
    # Then each exits 2 with its message and no file is written, and a bare
    # contract still works
    raise NotImplementedError


def test_json_is_one_object_with_the_same_facts() -> None:
    """AC-6: scenario of the contract."""
    # Given a project with a parent Work and a leaf template
    # When `new --json` runs for a template under a parent, a bare contract and a path
    # Then each prints one object with the fields in order
    raise NotImplementedError
