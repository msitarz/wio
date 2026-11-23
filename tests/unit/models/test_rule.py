# SPDX-License-Identifier: Apache-2.0
"""Tests of the type of a rule."""

from pathlib import PurePosixPath

import pytest

from wio.models.rule import Rule


def _rule(code: str = "ARC001") -> Rule:
    """Build a rule with the given code and fixed other fields.

    Args:
        code: The code of the rule.

    Returns:
        The rule.
    """
    return Rule(
        ruleset="demo",
        code=code,
        name="keep-it-small",
        description=None,
        summary="Keep it small.",
        body="Keep it small.",
        body_line=7,
        path=PurePosixPath(".agents/wio/rules/demo/ARC001-keep-it-small.md"),
    )


def test_a_rule_tells_its_family_its_number_and_its_qualified_code() -> None:
    """AC-1: the parts of a code and the code with its ruleset."""
    # Given a rule of the ruleset `demo` with the code `ARC001`
    rule = _rule()

    # When its family, number and qualified code are asked
    found = (rule.family, rule.number, rule.qualified)

    # Then they are `ARC`, 1 and `demo.ARC001`
    assert found == ("ARC", 1, "demo.ARC001")


def test_a_rule_is_a_value_that_can_key_a_mapping() -> None:
    """AC-8: equal rules share a hash, a different one does not, none is mutable."""
    # Given two equal rules and one with another code
    first, second, other = _rule(), _rule(), _rule("ARC002")

    # When they are used as keys of one mapping and a field is assigned
    keys = {first: 1, second: 2, other: 3}
    with pytest.raises(AttributeError):
        first.name = "other"  # type: ignore[misc]

    # Then the equal rules share one key, the other is a different key, and the
    # assignment raised
    assert first == second
    assert hash(first) == hash(second)
    assert len(keys) == 2
    assert keys[first] == 2
