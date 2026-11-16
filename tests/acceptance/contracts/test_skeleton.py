# SPDX-License-Identifier: Apache-2.0
"""Scenario stubs of `wio contracts skeleton`.

Each stub is one scenario of the Work's acceptance criteria. The implementation
stage replaces its body with the scenario and its fixture.
"""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

pytestmark = pytest.mark.skip(
    reason="architecture stub: the implementation stage fills it"
)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_moved_leaf_keeps_its_identity_and_names_what_it_dropped(
    wio: Wio,
) -> None:
    # Given the Work `k3m9xq` with roots, an `[actions]` table and an `[x]` table, and
    # the template `feature.parent`
    # When `wio contracts skeleton feature.parent --work k3m9xq` runs
    # Then standard output is the skeleton of AC-1, standard error is the note, nothing
    # is written and it exits 0
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_keep_replaces_a_key_and_the_note_names_only_what_is_still_dropped(
    wio: Wio,
) -> None:
    # Given the Work and the template of AC-1
    # When the command runs with `--keep roots --keep x`
    # Then standard output has `roots` and `[x]` of the Work, and the note names only
    # `actions`
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_keeping_everything_leaves_no_note(wio: Wio) -> None:
    # Given the Work and the template of AC-1
    # When the command runs with `--keep roots --keep actions --keep x`
    # Then standard output has all three and standard error is empty
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_kept_table_replaces_the_template_s_own_and_is_added_when_it_has_none(
    wio: Wio,
) -> None:
    # Given the Work of AC-1 and the template `t.tabled` with its own `[x]`
    # When `wio contracts skeleton t.tabled --work k3m9xq --keep actions` runs
    # Then the template's `[x]` and `roots = []` stand, `[actions]` is added, and the
    # note names `roots` and `x`
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_bare_work_and_a_front_matter_work_differ_from_templates_show_only_by_the_id(
    wio: Wio,
) -> None:
    # Given the Works `k3m9xq` and `p5n2hv`, bare and in `+++` form, and the template
    # `feature.parent`
    # When the command runs for each and `wio templates show feature.parent` runs
    # Then each skeleton is the output of `templates show` with the `id` first, and
    # standard error is empty
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_front_matter_template_and_a_crlf_template_keep_their_form(wio: Wio) -> None:
    # Given the Work of AC-1 and the templates `t.front` and `t.crlf`
    # When the command runs for each, the second with `--keep x`
    # Then the first is in `+++` form with `wio = 1`, `id` and `template` in order, and
    # the second has CRLF endings throughout
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_each_mistake_prints_nothing_and_says_what_to_do(wio: Wio) -> None:
    # Given the Work of AC-1, two Works that share an id and a rejected template
    # When the command runs with each mistake of AC-4 in turn
    # Then each exits 2 with its own message and nothing on standard output
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_tree_that_is_not_complete_refuses_the_command(wio: Wio) -> None:
    # Given the Work of AC-1 and an unreadable Work file
    # When `wio contracts skeleton feature.parent --work k3m9xq` runs
    # Then it exits 2 with the error of finding the Works and the pointer to
    # `wio contracts check`, and nothing on standard output
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_wrong_type_of_depends_on_is_carried_as_the_file_has_it(wio: Wio) -> None:
    # Given a Work whose `depends_on` is the string `"a7b2c4"`
    # When the command runs
    # Then it prints `depends_on = "a7b2c4"` and exits 0
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_several_mistakes_report_only_the_first_of_the_order(wio: Wio) -> None:
    # Given the tree of the mistakes and a rejected template `bad`
    # When `skeleton bad` and `skeleton bad --work k3m9xr --keep nosuch` run
    # Then the first reports only that `--work` is required and the second only the
    # error of finding the Works
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_nothing_is_written_and_two_runs_print_the_same_bytes(wio: Wio) -> None:
    # Given the Work and the template of AC-1 and a hash of each contract
    # When the command runs twice, with and without `--keep roots`
    # Then the outputs of each are identical and no contract changed
    raise NotImplementedError
