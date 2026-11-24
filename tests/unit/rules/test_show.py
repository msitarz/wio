# SPDX-License-Identifier: Apache-2.0
"""Tests of finding and writing the one rule that `wio rules show` prints."""

import json
from dataclasses import replace
from typing import TYPE_CHECKING

import pytest

from tests.unit.rules.support import make_rule, make_ruleset
from wio.errors import WioError
from wio.rules.discovery import Discovery
from wio.rules.showing import render_rule, show_rule

if TYPE_CHECKING:
    from wio.models.rule import Rule

_PRESETS = {"recommended": (["ARC"], [])}
_DEMO = make_ruleset("demo", ["ARC"], ["ARC001", "ARC002"], _PRESETS)
_DISCOVERY = Discovery((_DEMO, make_ruleset("other", ["PAY"], ["PAY001"])), ())
_FILE = ".agents/wio/rules/demo/ARC001-arc001.md"
_STRICT = pytest.mark.xfail(
    raises=NotImplementedError, strict=True, reason="show is a stub"
)


def _rule(
    description: str | None = None, body: str = "", summary: str = "Summary."
) -> Rule:
    """Build `demo.ARC001` with the text that a test needs.

    Args:
        description: Its one-line description.
        body: Its body.
        summary: Its summary.

    Returns:
        The rule.
    """
    return replace(
        make_rule("demo", "ARC001"), description=description, body=body, summary=summary
    )


@_STRICT
def test_it_finds_the_rule_by_its_ruleset_and_code() -> None:
    """AC-1: `demo.ARC002` is the rule of that ruleset and code."""
    # Given a discovery of two rulesets
    # When the qualified code of a rule is shown
    found = show_rule("demo.ARC002", _DISCOVERY)

    # Then it is that rule, and not one of another ruleset
    assert found == _DEMO.get("ARC002")


@_STRICT
@pytest.mark.parametrize(
    ("reference", "message"),
    [
        ("demo.ARC", "`demo.ARC` is a family and `show` takes a rule's code"),
        ("demo.recommended", "`demo.recommended` is a rule preset"),
        ("demo.all", "`demo.all` is a rule preset"),
        ("ARC001", "`ARC001` has no ruleset"),
        ("Docs", "`Docs` is not a reference"),
        ("nope.ARC001", "`nope`"),
        ("demo.ARC999", "`ARC001` and `ARC002`"),
        ("demo.arc001", "form of a rule preset name"),
        ("d.ARC001", "`d`"),
        ("a.b.c", "more than one dot"),
    ],
    ids=[
        "family",
        "preset",
        "all",
        "bare",
        "malformed",
        "ruleset",
        "rule",
        "lower",
        "alias",
        "dots",
    ],
)
def test_it_refuses_what_is_not_one_rules_code(reference: str, message: str) -> None:
    """AC-5: each reference is refused with the cause."""
    # Given a discovery whose `demo` holds `ARC001` and `ARC002`
    # When the reference is shown
    with pytest.raises(WioError) as caught:
        show_rule(reference, _DISCOVERY)

    # Then it says what is wrong
    assert message in str(caught.value)


@_STRICT
def test_the_ruleset_that_is_missing_is_listed_with_the_rulesets_that_exist() -> None:
    """AC-5: the unknown ruleset names those that were read."""
    # Given a discovery of `demo` and `other`
    # When a rule of an unknown ruleset is shown
    with pytest.raises(WioError) as caught:
        show_rule("nope.ARC001", _DISCOVERY)

    # Then the message lists both rulesets
    assert "`demo`, `other`" in str(caught.value)


@_STRICT
def test_the_text_is_the_header_a_blank_line_and_the_body() -> None:
    """AC-1: the block, the description, the file and the body."""
    # Given a rule with a description and a body of two paragraphs
    rule = _rule("One instruction.", "First.\n\nSecond.")

    # When it is rendered as text
    text = render_rule(rule, as_json=False)

    # Then the header is indented to the name and the body follows a blank line
    assert text == (
        "demo.ARC001  arc001\n"
        "             One instruction.\n"
        f"             file: {_FILE}\n"
        "\n"
        "First.\n\nSecond.\n"
    )


@_STRICT
def test_a_rule_without_a_description_or_a_body_prints_only_its_header() -> None:
    """AC-2: no description line, no blank line, one line feed."""
    # Given a rule with neither a description nor a body
    rule = _rule(summary="")

    # When it is rendered as text
    text = render_rule(rule, as_json=False)

    # Then only the name and the file line are printed
    assert text == f"demo.ARC001  arc001\n             file: {_FILE}\n"


@_STRICT
def test_the_body_keeps_its_spaces_and_its_line_endings() -> None:
    """AC-3: nothing is trimmed or translated, and one line feed ends it."""
    # Given a body that starts with two spaces and has CRLF line endings
    rule = _rule(body="  indented\r\nnext")

    # When it is rendered as text
    text = render_rule(rule, as_json=False)

    # Then the body is untouched and followed by one line feed
    assert text.endswith("\n\n  indented\r\nnext\n")


@_STRICT
def test_the_json_is_one_line_with_the_fields_in_order() -> None:
    """AC-7: code, name, description, summary, body and path."""
    # Given a rule with a description and a body
    rule = _rule("One instruction.", "First.\n\nSecond.", "First.")

    # When it is rendered as JSON
    text = render_rule(rule, as_json=True)

    # Then it is one line of one object with the fields in order
    assert text.count("\n") == 1
    found = json.loads(text)
    assert list(found) == ["code", "name", "description", "summary", "body", "path"]
    assert found == {
        "code": "demo.ARC001",
        "name": "arc001",
        "description": "One instruction.",
        "summary": "First.",
        "body": "First.\n\nSecond.",
        "path": _FILE,
    }


@_STRICT
def test_the_json_description_is_null_when_there_is_none() -> None:
    """AC-7: `null` and an empty body for the bare rule."""
    # Given a rule with no description and no body
    rule = _rule(summary="")

    # When it is rendered as JSON
    found = json.loads(render_rule(rule, as_json=True))

    # Then the description is null and the body is empty
    assert (found["description"], found["body"]) == (None, "")
