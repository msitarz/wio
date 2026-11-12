# SPDX-License-Identifier: Apache-2.0
"""Scenario stubs of the body checks of `wio contracts check`.

Each stub is one scenario of the Work's acceptance criteria. The implementation
stage replaces its body with the scenario and its fixture.
"""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

# The implementation stage adds the sample repositories under
# `tests/fixtures/contracts`, named `check-body-*`, each with the templates that
# its Works follow. AC-8 writes an item into a contract with `wio.put`. AC-7
# counts the reads of a file system, which no process shows, so it is a unit test.

pytestmark = pytest.mark.skip(
    reason="architecture stub: the implementation stage fills it"
)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_required_section_that_is_missing_is_an_error(wio: Wio) -> None:
    """AC-1: scenario of the contract."""
    # Given a template that requires `Purpose` and `Goals` and has `Notes`, and
    # a contract with `##  purpose` only
    # When `wio contracts check` runs
    # Then one error at the contract's file for `Goals`, and none for `Purpose`
    # or `Notes`
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_body_is_reported_in_the_same_run_as_the_metadata(wio: Wio) -> None:
    """AC-1: scenario of the contract."""
    # Given the same project and another Work with the unknown key `depend_on`
    # When `wio contracts check` runs, and with `--json`
    # Then both report the missing section and the key in one order, the second
    # as one array that parses, and each exits 1
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_items_and_their_ids_are_judged_as_the_items_leaf_judges_them(wio: Wio) -> None:
    """AC-2: scenario of the contract."""
    # Given a template with `items>=1` on Goals and a `pattern` on the criteria,
    # and a contract that breaks both
    # When `wio contracts check` runs
    # Then the three errors of the contract at their lines
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_misspelled_section_is_a_warning_with_a_suggestion(wio: Wio) -> None:
    """AC-3: scenario of the contract."""
    # Given a template with `Constraints` and a contract with `Constraint`,
    # `Zzz` and a deeper heading
    # When `wio contracts check` runs
    # Then two warnings at their lines, the first with the suggestion, and exit 0
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_contract_without_a_template_gets_no_section_warning(wio: Wio) -> None:
    """AC-3: scenario of the contract."""
    # Given a contract that names no template and has sections of its own
    # When `wio contracts check` runs
    # Then there is no warning about a section
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_directive_list_in_a_contract_that_follows_a_template_is_ignored(
    wio: Wio,
) -> None:
    """AC-4: scenario of the contract."""
    # Given a template that requires `Goals` and a contract that lacks it and
    # has three lists
    # When `wio contracts check` runs
    # Then one warning for each list, the error for `Goals` and nothing else
    # about the sections
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_contract_without_a_template_is_checked_by_its_own_headings(wio: Wio) -> None:
    """AC-5: scenario of the contract."""
    # Given a contract with no template whose headings carry directives, some of
    # them wrong
    # When `wio contracts check` runs
    # Then the errors of the contract at their lines and columns, and none for `Purpose`
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_contract_with_no_directives_has_no_body_diagnostic(wio: Wio) -> None:
    """AC-5: scenario of the contract."""
    # Given a contract with no template and no directive list
    # When `wio contracts check` runs
    # Then the contracts pass
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_repeated_section_and_a_missing_title_are_warnings(wio: Wio) -> None:
    """AC-6: scenario of the contract."""
    # Given a contract with `Goals` twice and one with no heading, under templates
    # When `wio contracts check` runs
    # Then the repeat and the missing title are warnings and the items of the
    # first are too few
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_fresh_work_passes_or_fails_by_what_its_template_requires(wio: Wio) -> None:
    """AC-8: scenario of the contract."""
    # Given a Work from a template that requires headings only and one from a
    # template that requires an item
    # When `wio contracts check` runs, then an item is written and it runs again
    # Then the first passes, the second fails and then passes
    raise NotImplementedError
