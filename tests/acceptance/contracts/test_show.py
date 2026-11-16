# SPDX-License-Identifier: Apache-2.0
"""Scenario stubs of `wio contracts show`.

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
def test_a_work_is_shown_with_its_facts_its_actions_and_its_resolved_contract(
    wio: Wio,
) -> None:
    """AC-1: scenario of the contract."""
    # Given a nesting project with a parent, a sibling and a child with an
    # override
    # When `wio contracts show k3m9xq` runs
    # Then it prints the text of AC-1 and exits 0
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_defaults_an_on_demand_action_and_an_undeclared_name_are_shown(
    wio: Wio,
) -> None:
    """AC-1: scenario of the contract."""
    # Given a config with defaults and a Work with no template and an undeclared
    # action
    # When `wio contracts show k3m9xq` runs
    # Then the actions block is the text of AC-1
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_roots_resolve_and_dependents_are_listed(wio: Wio) -> None:
    """AC-2: scenario of the contract."""
    # Given the Works of AC-1 with a parent that lists `@descendants` and two
    # dependents
    # When `show` runs on the sibling and on the parent
    # Then the sibling lists both dependents and the parent shows its roots
    # resolved
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_under_flat_there_is_no_parent_and_nothing_is_inherited(wio: Wio) -> None:
    """AC-2: scenario of the contract."""
    # Given `hierarchy = "flat"` and the Works of AC-1
    # When `wio contracts show k3m9xq` runs
    # Then there is no `Parent` line and the view is the Work's own contract
    raise NotImplementedError


@pytest.mark.channels(Channel.CLI)
def test_a_path_from_a_subdirectory_shows_the_same_work(wio: Wio) -> None:
    """AC-3: scenario of the contract."""
    # Given the Works of AC-1 and the working directory `.agents/wio/works/p`
    # When `wio contracts show c/README.md` runs
    # Then it prints the same as `wio contracts show k3m9xq`
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_an_id_that_no_work_has_is_told_with_the_closest_one(wio: Wio) -> None:
    """AC-3: scenario of the contract."""
    # Given the Works of AC-1
    # When `show k3m9xr` and `show zzzzzz` run
    # Then the first names the closest id, the second does not, and each exits 2
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_file_that_is_not_a_work_gives_its_reason_and_exits_2(wio: Wio) -> None:
    """AC-3: scenario of the contract."""
    # Given an unmarked file, a path that does not exist and a file outside the
    # Works directory
    # When `show` runs on each
    # Then each prints an error with a different reason and exits 2
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_shared_id_refuses_its_own_lookup_and_is_listed_twice_elsewhere(
    wio: Wio,
) -> None:
    """AC-3: scenario of the contract."""
    # Given two Works that share an id and a Work that lists it
    # When `show` runs on the id and on the Work that lists it
    # Then the first is refused with the error of discovery and the hint, and
    # the second lists both
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_an_incomplete_tree_refuses_the_command_and_other_errors_do_not(
    wio: Wio,
) -> None:
    """AC-4: scenario of the contract."""
    # Given a tree with an unreadable Work file, one with two marked files in a
    # directory and one with an undeclared root and a cycle
    # When `show` runs on a good Work of each
    # Then the first two write nothing to standard output and exit 2, and the
    # third prints the Work and exits 0
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_json_is_one_object_with_the_same_facts_and_the_view(wio: Wio) -> None:
    """AC-5: scenario of the contract."""
    # Given the Works of AC-1
    # When `wio contracts show k3m9xq --json` runs
    # Then it prints one object with the fields of AC-5 in order
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_showing_writes_nothing_and_prints_the_same_bytes_twice(wio: Wio) -> None:
    """AC-6: scenario of the contract."""
    # Given the Works of AC-1 and a hash of each contract
    # When `show` and `show --json` each run twice
    # Then the outputs of each are identical and no contract changed
    raise NotImplementedError


@pytest.mark.channels(Channel.CLI)
def test_a_run_without_json_imports_neither_json_nor_tomlkit(wio: Wio) -> None:
    """AC-6: scenario of the contract."""
    # Given a new Python process and the Works of AC-1
    # When `main(["contracts", "show", "k3m9xq"], stdio)` runs in it
    # Then neither `json` nor `tomlkit` is in `sys.modules`
    raise NotImplementedError
