# SPDX-License-Identifier: Apache-2.0
"""Tests of the order of the rules of a group and of the family lines."""

from dataclasses import dataclass, field
from pathlib import PurePosixPath

import pytest

from wio.context.ordering import order_rules
from wio.models.rule import Rule

_PENDING = pytest.mark.xfail(strict=True, raises=NotImplementedError)


@dataclass
class _Topics:
    """A `Topics` over a dictionary.

    Attributes:
        topics: The topic by ruleset and family.
    """

    topics: dict[tuple[str, str], str] = field(
        default_factory=lambda: {
            ("mattpocock", "ARC"): "Architecture",
            ("mattpocock", "ERR"): "Error handling",
            ("python", "API"): "Python API",
            ("python", "ERR"): "Process",
        }
    )

    def topic(self, ruleset: str, family: str) -> str:
        """Give a topic.

        Args:
            ruleset: The ruleset.
            family: The family.

        Returns:
            The topic.

        Raises:
            KeyError: If the dictionary has none.
        """
        return self.topics[ruleset, family]


def _rule(qualified: str) -> Rule:
    """Build a rule from its qualified code.

    Args:
        qualified: The ruleset and the code, such as `python.API001`.

    Returns:
        The rule.
    """
    ruleset, code = qualified.split(".")
    return Rule(ruleset, code, "a-rule", None, "", "", 1, PurePosixPath("r.md"))


def _shown(items: tuple[str | Rule, ...]) -> list[str]:
    """Name each item: a line as it is, a rule by its qualified code.

    Args:
        items: The ordered items.

    Returns:
        The names.
    """
    return [item if isinstance(item, str) else item.qualified for item in items]


@_PENDING
def test_the_order_depends_only_on_names() -> None:
    """AC-1: by ruleset, family, number and text, whatever the order given."""
    # Given two rulesets and codes that a text sort misorders, unsorted
    given = [
        "python.API002",
        "mattpocock.ERR010",
        "mattpocock.ERR002",
        "python.API001",
        "mattpocock.ARC1000",
        "mattpocock.ARC01",
        "mattpocock.ARC999",
        "mattpocock.ARC001",
    ]

    # When the group is ordered
    found = order_rules([_rule(name) for name in given], _Topics())

    # Then the rules are in the order of their names
    assert [item.qualified for item in found if isinstance(item, Rule)] == [
        "mattpocock.ARC001",
        "mattpocock.ARC01",
        "mattpocock.ARC999",
        "mattpocock.ARC1000",
        "mattpocock.ERR002",
        "mattpocock.ERR010",
        "python.API001",
        "python.API002",
    ]


@_PENDING
def test_a_family_has_one_topic_line_before_its_first_rule() -> None:
    """AC-2: once for each family, ahead of it."""
    # Given two families of one ruleset, mixed
    names = ["mattpocock.ERR002", "mattpocock.ARC001", "mattpocock.ERR010"]

    # When the group is ordered
    found = order_rules([_rule(name) for name in names], _Topics())

    # Then each family has its line once, before its rules
    assert _shown(found) == [
        "mattpocock: Architecture (ARC)",
        "mattpocock.ARC001",
        "mattpocock: Error handling (ERR)",
        "mattpocock.ERR002",
        "mattpocock.ERR010",
    ]


@_PENDING
def test_a_family_of_the_same_letters_has_a_line_for_each_ruleset() -> None:
    """AC-2: a family belongs to its ruleset, also when two share the letters."""
    # Given two rulesets with a family `ERR` that stand next to each other
    names = ["python.ERR001", "mattpocock.ERR001"]

    # When the group is ordered
    found = order_rules([_rule(name) for name in names], _Topics())

    # Then each ruleset has its own line with its own topic
    assert _shown(found) == [
        "mattpocock: Error handling (ERR)",
        "mattpocock.ERR001",
        "python: Process (ERR)",
        "python.ERR001",
    ]


@_PENDING
@pytest.mark.parametrize("reverse", [False, True], ids=["one-order", "the-other"])
def test_the_route_by_which_rules_arrive_moves_nothing(*, reverse: bool) -> None:
    """AC-3: the same rules give the same result in any order of arrival."""
    # Given the same rules arriving in one order or the other, as two rule
    # presets would give them
    names = ["mattpocock.ERR002", "mattpocock.ARC001", "python.API001"]
    arriving = list(reversed(names)) if reverse else names

    # When the group is ordered
    found = order_rules((_rule(name) for name in arriving), _Topics())

    # Then the order and the family lines are the same
    assert _shown(found) == [
        "mattpocock: Architecture (ARC)",
        "mattpocock.ARC001",
        "mattpocock: Error handling (ERR)",
        "mattpocock.ERR002",
        "python: Python API (API)",
        "python.API001",
    ]


@_PENDING
def test_no_rule_gives_no_line() -> None:
    """AC-2: nothing to introduce."""
    # Given no rule

    # When the group is ordered
    found = order_rules([], _Topics())

    # Then there is nothing
    assert found == ()
