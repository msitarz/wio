# SPDX-License-Identifier: Apache-2.0
"""Test stubs of the check of the body of a contract.

Each stub is a scenario of the Work's acceptance criteria. The implementation
stage replaces its body with the scenario.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="architecture stub: the implementation stage fills it"
)


def test_a_required_section_that_is_missing_is_an_error() -> None:
    """AC-1: scenario of the contract."""
    # Given a template that requires `Purpose` and `Goals` and has `Notes`, and
    # a contract with `##  purpose` only
    # When the body is checked
    # Then one error at the file for `Goals`, none for `Purpose`, which matches
    # in another case, and none for `Notes`
    raise NotImplementedError


def test_items_and_their_ids_are_judged_as_the_items_leaf_judges_them() -> None:
    """AC-2: scenario of the contract."""
    # Given a template with `items>=1` and a `pattern`, and a contract whose
    # Goals holds an authoring comment and whose criteria repeat an id and lack
    # one
    # When the body is checked
    # Then an error at `## Goals`, one at the first repeated id naming the other
    # line, and one at the item with no id
    raise NotImplementedError


def test_a_misspelled_section_is_a_warning_with_the_closest_section() -> None:
    """AC-3: scenario of the contract."""
    # Given a template with `Constraints` and a contract with `Constraint`,
    # `Zzz` and a deeper heading
    # When the body is checked
    # Then two warnings, the first with the suggestion, and none for the deeper heading
    raise NotImplementedError


def test_a_contract_without_a_template_gets_no_warning_about_a_section() -> None:
    """AC-3: scenario of the contract."""
    # Given a contract with no template and sections of its own
    # When the body is checked
    # Then there is no warning about a section
    raise NotImplementedError


def test_a_directive_list_in_a_contract_that_follows_a_template_is_ignored() -> None:
    """AC-4: scenario of the contract."""
    # Given a template that requires `Goals` and a contract that lacks it and
    # has lists on two `##` headings and a deeper one
    # When the body is checked
    # Then one warning at each of the three lines, no parser error, no stray
    # section, and the error for the missing `Goals`
    raise NotImplementedError


def test_a_contract_without_a_template_is_checked_by_its_own_headings() -> None:
    """AC-5: scenario of the contract."""
    # Given a contract with no template whose headings have `required`,
    # `items>=2` over one item, `mandatory` and a list on a deeper heading
    # When the body is checked
    # Then the error for the items, the parser's error at its line and column
    # and the error for the deeper heading, and none for `Purpose`
    raise NotImplementedError


def test_a_contract_with_no_directive_list_has_no_diagnostic_about_its_body() -> None:
    """AC-5: scenario of the contract."""
    # Given a contract with no template and no directive list
    # When the body is checked
    # Then there is nothing
    raise NotImplementedError


def test_a_repeated_section_and_a_missing_title_are_warnings() -> None:
    """AC-6: scenario of the contract."""
    # Given a contract with `Goals` twice under a template that wants two items,
    # and a contract with no heading
    # When the bodies are checked
    # Then the repeat is a warning at the second, the first's items are too few,
    # and the second contract has no title
    raise NotImplementedError


def test_a_template_that_cannot_be_used_gets_no_body_check_and_is_read_once() -> None:
    """AC-7: scenario of the contract."""
    # Given Works that name a missing and a rejected template, and three that
    # follow one good template, and a file system that counts reads
    # When the bodies are checked on their own
    # Then the first two have nothing, and the good template's file was read once
    raise NotImplementedError


def test_a_template_that_cannot_be_read_is_skipped() -> None:
    """A-3: scenario of the contract."""
    # Given a template whose file cannot be read, one that is not text, one whose
    # block does not close and one with no block, and a file system that counts
    # reads, which `test_checking.py` already has and moves to `helpers.py`
    # When a contract that follows each is checked
    # Then there is no diagnostic
    raise NotImplementedError


def test_a_fresh_work_passes_when_the_template_requires_only_headings() -> None:
    """AC-8: scenario of the contract."""
    # Given a template that requires `Purpose` and a contract made from it
    # When the body is checked
    # Then it passes, and a template that requires an item fails until it has one
    raise NotImplementedError


def test_the_first_of_two_template_headings_is_the_section() -> None:
    """Constraint: scenario of the contract."""
    # Given a template that has `Goals` twice with different directives
    # When a contract is checked against it
    # Then the first heading's directives apply
    raise NotImplementedError


def test_a_work_whose_template_is_of_a_wrong_type_gets_no_body_check() -> None:
    """Constraint: nothing is reported twice."""
    # Given a Work whose `template` is a number, which discovery reported
    # When the Works are checked
    # Then the error of discovery is all it gets, and its body is not checked by
    # its own headings
    raise NotImplementedError


def test_a_directive_list_on_a_repeated_heading_is_warned_of_twice() -> None:
    """Constraint: every list is judged and a repeat is a warning."""
    # Given a contract that follows a template and repeats a `##` heading with a
    # list on the repeat
    # When the body is checked
    # Then there are the warning that the list is ignored and the warning that
    # the heading is repeated
    raise NotImplementedError


def test_a_template_section_that_inherits_and_is_required_is_required() -> None:
    """Constraint: inheritance does not lift a requirement."""
    # Given a template section with `inherit` and `required` that a contract lacks
    # When the body is checked
    # Then the section is reported as required
    raise NotImplementedError
