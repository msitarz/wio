# SPDX-License-Identifier: Apache-2.0
"""Tests of planning the next rule of a family."""

from dataclasses import replace
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

import pytest

from tests.unit.rules.support import make_ruleset
from wio.errors import WioError
from wio.rules.discovery import Discovery
from wio.rules.planning import plan_rule
from wio.rules.reading import read_rule

if TYPE_CHECKING:
    from wio.models.rule import LoadedRuleset

_DEMO = PurePosixPath(".agents/wio/rules/demo")


def _discovery(*rulesets: LoadedRuleset) -> Discovery:
    """Build what a walk found.

    Args:
        *rulesets: The rulesets that were read.

    Returns:
        A discovery with no diagnostic.
    """
    return Discovery(rulesets, ())


def _demo(*codes: str) -> LoadedRuleset:
    """Build `demo`, which declares `ARC` and `PAY`.

    Args:
        *codes: The codes of its rules.

    Returns:
        The ruleset.
    """
    return make_ruleset("demo", ["ARC", "PAY"], list(codes))


def test_the_code_is_the_number_after_the_highest_and_a_gap_is_left_alone() -> None:
    """AC-1: `ARC004` after `ARC003`, and `PAY001` for an empty family."""
    # Given `demo` with `ARC001` and `ARC003`
    found = _discovery(_demo("ARC001", "ARC003"))

    # When the next rule of `ARC` and of `PAY` are planned
    arc = plan_rule("demo", "ARC", "keep-it-small", None, found)
    pay = plan_rule("demo", "PAY", "pay-first", None, found)

    # Then the codes are `ARC004` and `PAY001`, in files named after them
    assert (arc.rule.code, arc.path.name) == ("ARC004", "ARC004-keep-it-small.md")
    assert (pay.rule.code, pay.path.name) == ("PAY001", "PAY001-pay-first.md")


@pytest.mark.parametrize(
    ("highest", "expected"),
    [("ARC999", "ARC1000"), ("ARC0007", "ARC0008"), ("ARC12", "ARC013")],
)
def test_the_number_is_as_wide_as_the_family_s(highest: str, expected: str) -> None:
    """AC-2: three digits at least, and the width of the highest code."""
    # Given a family whose highest code is `highest`
    found = _discovery(_demo(highest))

    # When the next rule is planned
    new = plan_rule("demo", "ARC", "x", None, found)

    # Then the number has the expected width
    assert new.rule.code == expected


def test_the_file_goes_next_to_the_last_rule_of_the_family() -> None:
    """AC-3: the directory of the highest code, or of the ruleset."""
    # Given `demo` whose `ARC` rules are in a subdirectory and whose `PAY` has none
    base = _demo("ARC001", "ARC002")
    moved = tuple(
        replace(rule, path=_DEMO / "arc" / rule.path.name) for rule in base.rules
    )
    found = _discovery(replace(base, rules=moved))

    # When the next rule of each family is planned
    arc = plan_rule("demo", "ARC", "keep-it-small", None, found)
    pay = plan_rule("demo", "PAY", "pay-first", None, found)

    # Then the first is in the subdirectory and the second in the ruleset's
    assert arc.path.parent == _DEMO / "arc"
    assert pay.path.parent == _DEMO


def test_the_file_is_a_valid_comment_block_with_an_empty_body() -> None:
    """AC-4: the block starts the file, and reading it gives the planned rule."""
    # Given `demo` and a description with a quote, a backslash and `-->`
    found = _discovery(_demo("ARC001"))
    text = 'Use "quotes", a \\ and --> carefully.'

    # When the next rule is planned with it
    new = plan_rule("demo", "ARC", "keep-it-small", text, found)

    # Then the file starts with the block, has an empty body, and reads back as
    # the planned rule with exactly that description
    assert new.text.startswith("<!-- wio\n")
    assert new.text.count("-->") == 1
    reading = read_rule("demo", new.path, new.text)
    assert reading.rule == new.rule
    assert (new.rule.description, new.rule.body) == (text, "")


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (("nope", "ARC", "x", None), "demo"),
        (("demo", "ZZZ", "x", None), "ARC"),
        (("demo", "ARC", "Bad_Name", None), "lower-case words"),
        (("demo", "ARC", "x", ""), "one line"),
        (("demo", "ARC", "x", "a\nb"), "one line"),
        (("demo", "ARC", "arc001", None), "ARC001"),
    ],
    ids=["ruleset", "family", "name", "blank", "lines", "taken"],
)
def test_a_request_that_cannot_be_met_is_refused(
    args: tuple[str, str, str, str | None], message: str
) -> None:
    """AC-6: a `WioError` that says what is wrong and what would do."""
    # Given `demo`, whose rule `ARC001` is named `arc001` as `make_ruleset` names it
    found = _discovery(_demo("ARC001"))
    ruleset, family, name, description = args

    # When the request is planned
    # Then it is refused with the cause named
    with pytest.raises(WioError) as raised:
        plan_rule(ruleset, family, name, description, found)
    assert message in str(raised.value)


def test_the_same_request_gives_the_same_file() -> None:
    """AC-11: the same path and bytes, whatever the order of the rulesets."""
    # Given two discoveries of the same rules, in two orders
    web = make_ruleset("web", ["WEB"], ["WEB001"])
    one = _discovery(_demo("ARC001"), web)
    two = _discovery(web, _demo("ARC001"))

    # When the same request is planned on each
    first = plan_rule("demo", "ARC", "x", "d", one)
    second = plan_rule("demo", "ARC", "x", "d", two)

    # Then the plans are equal
    assert first == second
