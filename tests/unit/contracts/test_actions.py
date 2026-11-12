# SPDX-License-Identifier: Apache-2.0
"""Test stubs of the resolution of a Work's actions.

Each stub is a scenario of the Work's acceptance criteria. The implementation
stage replaces its body with the scenario.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="architecture stub: the implementation stage fills it"
)


def test_a_layering_replaces_an_inherited_action_and_keeps_its_source() -> None:
    """AC-5: scenario of the contract."""
    # Given a template's actions and a Work's own
    # When they are resolved
    # Then the Work's actions replace, the rest is inherited, an empty list
    # removes and keeps the source
    raise NotImplementedError


def test_the_defaults_apply_only_to_a_work_without_a_template() -> None:
    """AC-5: scenario of the contract."""
    # Given the config defaults and a Work with no template
    # When its actions are resolved over the defaults
    # Then they are layered, and an empty inherited list gives no entry
    raise NotImplementedError


def test_the_actions_of_a_template_are_read_from_its_file() -> None:
    """AC-5: scenario of the contract."""
    # Given a template file with `[actions]`, one with none and one that cannot be read
    # When the actions are read
    # Then the first gives them in order, the second none and the third `None`
    raise NotImplementedError
