# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio config check` on the names that pipelines use."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_stage_presets_and_default_actions_name_known_stages(wio: Wio) -> None:
    """AC-1: an unknown or repeated stage is an error that lists what exists."""
    # Given a config with a missing stage and a repeated stage in stage presets
    # and the faults of the default actions
    # When `wio config check` runs
    # Then it prints an error at each key path and exits 1
    del wio
    pytest.skip("not implemented")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_stage_with_an_unknown_root_fails(wio: Wio) -> None:
    """AC-2: the error lists the declared roots and `@work`."""
    # Given a config whose stage selects a root that is not declared
    # When `wio config check` runs
    # Then it prints an error at `stages.<name>.roots[<i>]` and exits 1
    del wio
    pytest.skip("not implemented")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_after_and_invalidated_by_name_declared_actions(wio: Wio) -> None:
    """AC-3: a cycle and undeclared actions are errors, a reserved entry a note."""
    # Given a config with an `after` cycle, an on-demand `after` and undeclared
    # actions, and a config whose only finding is an `@children:` entry
    # When `wio config check` runs on each
    # Then the first prints the errors and exits 1, and the second prints the
    # note and exits 0
    del wio
    pytest.skip("not implemented")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize("results", ["[]", '["pass", "pass"]'])
def test_an_empty_or_duplicated_gate_vocabulary_fails(wio: Wio, results: str) -> None:
    """AC-4: an empty or duplicated `gates.results` is an error there."""
    # Given a config with `gates.results` set to `results`
    # When `wio config check` runs
    # Then it prints an error at `gates.results` and exits 1
    del wio, results
    pytest.skip("not implemented")
