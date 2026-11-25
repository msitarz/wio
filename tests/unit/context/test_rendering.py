# SPDX-License-Identifier: Apache-2.0
"""Tests of how a rule is written and how the items of the section are joined."""

from pathlib import PurePosixPath

import pytest

from wio.context.rendering import join_items, render_rule
from wio.models.config import Bundle
from wio.models.rule import Rule

_ITEMS = (
    "Rules for root api (services/api):",
    "mattpocock: Error handling (ERR)",
    "mattpocock.ERR003 errors-carry-context\nWrap.",
    "  mattpocock.ERR004 no-silent-catch\nA hard break.  ",
    "mattpocock: Error handling (ERR)",
)


def _rule(
    body: str,
    ruleset: str = "mattpocock",
    code: str = "ERR003",
    name: str = "errors-carry-context",
) -> Rule:
    """Build a rule whose other texts differ from its body and name.

    Args:
        body: The body.
        ruleset: The ruleset's canonical name.
        code: The code.
        name: The name.

    Returns:
        The rule.
    """
    return Rule(
        ruleset=ruleset,
        code=code,
        name=name,
        description="A description that is not shown.",
        summary="A summary that is not shown.",
        body=body,
        body_line=7,
        path=PurePosixPath("rules/ERR003-errors-carry-context.md"),
    )


@pytest.mark.parametrize(
    "body",
    [
        "Wrap an error.\n\nWhy: so it is found.",
        "    indented first line\n\n\n  kept  \nlast  ",
        "    every line\n    is indented",
        "a\ttab\t",
        "one\r\ntwo",
    ],
    ids=["paragraphs", "whitespace", "indented", "tabs", "line-ends"],
)
def test_a_rule_is_its_qualified_line_and_its_body(body: str) -> None:
    """AC-1: the line, one newline and the body unchanged, and nothing else."""
    # Given a rule with the body
    rule = _rule(body)

    # When it is rendered
    text = render_rule(rule)

    # Then it is the qualified line, a newline and the body as it is
    assert text == "mattpocock.ERR003 errors-carry-context\n" + body


def test_a_rule_with_no_body_is_its_line_alone() -> None:
    """AC-1: no newline follows the line, and the ruleset is the rule's own."""
    # Given a rule of another ruleset with an empty body
    rule = _rule("", ruleset="python", code="API001", name="typed-results")

    # When it is rendered
    text = render_rule(rule)

    # Then it is the line alone
    assert text == "python.API001 typed-results"


@pytest.mark.parametrize(
    "separator",
    [Bundle().separator, "\n---\n", " | ", "\\n{0}", ""],
    ids=["default", "configured", "no-newline", "as-written", "empty"],
)
def test_every_item_is_joined_by_the_separator_as_written(separator: str) -> None:
    """AC-2: between every two items, and at neither end."""
    # Given a group line, a family line, two rules and a repeated line, and a
    # separator
    first, second, third, fourth, fifth = _ITEMS

    # When they are joined
    text = join_items(_ITEMS, separator)

    # Then the separator stands between each two and nowhere else
    head = first + separator + second + separator + third
    assert text == head + separator + fourth + separator + fifth


@pytest.mark.parametrize(("items", "expected"), [((), ""), (("only",), "only")])
def test_no_item_or_one_has_no_separator(items: tuple[str, ...], expected: str) -> None:
    """AC-2: the separator is never added to an end."""
    # Given no item or one

    # When it is joined with a separator
    text = join_items(items, "\n---\n")

    # Then no separator is there
    assert text == expected


def test_the_default_separator_is_a_blank_line() -> None:
    """AC-2: a config that sets none gives a blank line."""
    # Given a config that sets no separator

    # When the default is read
    separator = Bundle().separator

    # Then it is two newlines
    assert separator == "\n\n"
