# SPDX-License-Identifier: Apache-2.0
"""Tests of the type of a rule."""

from pathlib import PurePosixPath

import pytest

from wio.models.config import RulePreset
from wio.models.frozen import freeze
from wio.models.rule import LoadedRuleset, Manifest, Rule


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


def _ruleset(*codes: str) -> LoadedRuleset:
    """Build a ruleset `demo` that holds rules with the given codes.

    Args:
        *codes: The codes of the rules, in the order to hold them.

    Returns:
        The ruleset.
    """
    manifest = Manifest(
        description="Demo.",
        families=freeze({"ARC": "Architecture"}),
        rule_presets=freeze({"all": RulePreset(("ARC",), ())}),
    )
    return LoadedRuleset(
        name="demo",
        path=PurePosixPath(".agents/wio/rules/demo"),
        manifest=manifest,
        rules=tuple(_rule(code) for code in codes),
    )


def test_a_ruleset_finds_its_rules_by_family_and_by_code() -> None:
    """AC-3: `rules_of` keeps the order, `get` matches the code exactly."""
    # Given a ruleset with two `ARC` rules and one `PAY` rule
    ruleset = _ruleset("ARC001", "ARC2", "PAY1")

    # When the rules of a family and of a code are asked
    arc = ruleset.rules_of("ARC")
    found = ruleset.get("ARC2")

    # Then the family gives its rules in order, an unknown family and a code that
    # only looks alike give none
    assert [r.code for r in arc] == ["ARC001", "ARC2"]
    assert ruleset.rules_of("ZZZ") == ()
    assert found is not None
    assert found.code == "ARC2"
    assert ruleset.get("ARC02") is None


def test_a_ruleset_is_a_value_that_hashes() -> None:
    """AC-3: equal rulesets share a hash, and a different rule makes them differ."""
    # Given two equal rulesets and one with another rule
    first, second, other = _ruleset("ARC1"), _ruleset("ARC1"), _ruleset("ARC2")

    # When they are used as keys of one mapping
    keys = {first: 1, second: 2, other: 3}

    # Then the equal ones share a key and the other does not
    assert len(keys) == 2
    assert hash(first) == hash(second)
