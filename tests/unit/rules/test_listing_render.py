# SPDX-License-Identifier: Apache-2.0
"""Tests of the text and the JSON that `wio rules list` writes for a listing."""

import json
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from tests.unit.rules.support import make_rule
from wio.models.listing import Header, Listing, Row
from wio.models.rules import Decision
from wio.rules.listing import render_listing

if TYPE_CHECKING:
    from collections.abc import Mapping

    from wio.models.listing import Explanation

_HEADER = Header(
    "root api", None, ("roots", "always fields"), ("api",), None, (), not_selected=False
)


@dataclass(frozen=True)
class _Note:
    """An explanation that says one thing."""

    def lines(self) -> tuple[str, ...]:
        """Write the note for a person.

        Returns:
            One line.
        """
        return ("note: one",)

    def fields(self) -> Mapping[str, object]:
        """Write the note for a program.

        Returns:
            One field.
        """
        return {"note": "one"}


def _row(
    code: str,
    *,
    included: bool = True,
    roots: tuple[str, ...] = ("api",),
    explanation: Explanation | None = None,
    decided: bool = True,
) -> Row:
    """Build a row for a rule of `demo`.

    Args:
        code: The rule's code.
        included: Whether the decision includes it.
        roots: The roots of the decision.
        explanation: The row's explanation.
        decided: Whether the row has a decision at all.

    Returns:
        The row.
    """
    rule = make_rule("demo", code)
    decision = Decision(
        included=included,
        roots=roots if included else (),
        root_independent=False,
        effects=(),
        reason=None,
    )
    return Row(rule, decision if decided else None, (), explanation)


def _text(listing: Listing) -> list[str]:
    """Render a listing as text and split it into lines.

    Args:
        listing: The listing.

    Returns:
        The lines.
    """
    return render_listing(listing, as_json=False).splitlines()


def _blocks(listing: Listing) -> list[str]:
    """Render a listing as text and keep the lines after the header.

    Args:
        listing: The listing.

    Returns:
        The lines after the first blank line.
    """
    return _text(listing)[_text(listing).index("") + 1 :]


def test_the_text_is_the_header_a_blank_line_and_a_block_for_each_rule() -> None:
    """AC-7: header keys, blank line, padded first lines and detail lines."""
    # Given a listing of a rule with a summary and one without any
    bare = replace(make_rule("demo", "ARC002"), summary="")
    rows = (_row("ARC001"), replace(_row("ARC002"), rule=bare))
    listing = Listing(_HEADER, rows)

    # When it is rendered as text
    text = render_listing(listing, as_json=False)

    # Then the header lines come first, then a blank line, then the blocks with
    # the roots under the name, and no description line for the bare rule
    assert text.splitlines() == [
        "view: root api",
        "layers: roots, always fields",
        "roots: api",
        "",
        "demo.ARC001  arc001",
        "             Summary.",
        "             roots: api",
        "demo.ARC002  arc002",
        "             roots: api",
    ]
    assert text.endswith("\n")


def test_the_optional_header_lines_come_in_their_order() -> None:
    """AC-7: `stage:`, `references:` and `filter: not selected` when they apply."""
    # Given a header with a stage, references and the mark
    header = replace(
        _HEADER, stage="s", references=("demo.ARC", "web"), not_selected=True
    )

    # When it is rendered
    lines = _text(Listing(header, ()))

    # Then the lines follow `roots:` in that order
    assert lines[:7] == [
        "view: root api",
        "layers: roots, always fields",
        "roots: api",
        "stage: s",
        "references: demo.ARC, web",
        "filter: not selected",
        "",
    ]


def _out_listings() -> tuple[Listing, Listing, Listing]:
    """Build the three listings of a rule that is out.

    Returns:
        One with an explanation on the row, one with the header marked
        `not selected` and one with neither.
    """
    out = _row("ARC002", included=False)
    explained = Listing(_HEADER, (replace(out, explanation=_Note()),))
    marked = Listing(replace(_HEADER, not_selected=True), (out,))
    return explained, marked, Listing(_HEADER, (out,))


def test_an_out_row_is_shown_in_the_text_only_when_asked_for() -> None:
    """AC-5: with an explanation or the mark, and with no `roots:` line."""
    # Given a rule that is out, in a listing with an explanation on it, in one
    # with the header marked and in one with neither
    explained, marked, plain = _out_listings()

    # When each is rendered as text
    shown = [_blocks(explained)[0], _blocks(marked)[0]]

    # Then the first two show the rule with no `roots:` line and the third hides it
    assert [line[:12] for line in shown] == ["demo.ARC002 "] * 2
    assert "roots:" not in "".join(_blocks(explained) + _blocks(marked))
    assert _blocks(plain) == []


def test_an_out_row_is_in_the_json_with_its_decision() -> None:
    """AC-5: `included` false and `roots` an empty array, hidden when not asked."""
    # Given the three listings of a rule that is out
    explained, marked, plain = _out_listings()

    # When each is rendered as JSON
    rules = [
        json.loads(render_listing(x, as_json=True))["rules"]
        for x in (explained, marked, plain)
    ]

    # Then the first two have the rule with its decision and the third none
    assert [(r["included"], r["roots"]) for r in rules[0]] == [(False, [])]
    assert [len(found) for found in rules] == [1, 1, 0]


def test_an_explanation_is_printed_without_being_known() -> None:
    """AC-9: its lines under the block and its fields after the rule's."""
    # Given a row with an explanation that says `note: one`
    listing = Listing(_HEADER, (_row("ARC001", explanation=_Note()),))

    # When the listing is rendered as text and as JSON
    lines = _text(listing)
    rule = json.loads(render_listing(listing, as_json=True))["rules"][0]

    # Then the line is the last of the block and the field follows the rule's
    assert lines[-1].strip() == "note: one"
    assert list(rule)[-1] == "note"
    assert rule["note"] == "one"


def test_the_json_is_one_line_with_the_header_keys_and_the_rules() -> None:
    """AC-8: keys in order, each rule with its fields, `null` for no description."""
    # Given a listing of one rule with no description, for a Work and a stage
    header = replace(_HEADER, view="Work W", work="W", stage="s")
    listing = Listing(header, (_row("ARC001"),))

    # When it is rendered as JSON
    text = render_listing(listing, as_json=True)
    found = json.loads(text)

    # Then it is one line, the keys are in order and the rule has its fields
    assert text.count("\n") == 1
    assert list(found) == [
        "view",
        "work",
        "layers",
        "roots",
        "stage",
        "references",
        "not_selected",
        "rules",
    ]
    assert (found["work"], found["roots"], found["stage"]) == ("W", ["api"], "s")
    assert list(found["rules"][0]) == [
        "code",
        "name",
        "description",
        "summary",
        "roots",
        "root_independent",
        "included",
    ]
    assert found["rules"][0]["code"] == "demo.ARC001"
    assert found["rules"][0]["description"] is None


def test_an_empty_listing_is_the_header_and_an_empty_array() -> None:
    """AC-12: the header and a blank line as text, `"rules": []` as JSON."""
    # Given a listing with no row
    listing = Listing(_HEADER, ())

    # When it is rendered as text and as JSON
    lines = _text(listing)
    found = json.loads(render_listing(listing, as_json=True))

    # Then the text ends at the blank line and the JSON has no rule
    assert lines[-1] == ""
    assert found["rules"] == []


def test_a_row_with_no_decision_is_included_with_nulls() -> None:
    """AC-12: `roots` and `root_independent` are `null` and `included` is true."""
    # Given a listing whose rows were never decided
    listing = Listing(
        Header("every rule", None, (), None, None, (), not_selected=False),
        (_row("ARC001", decided=False),),
    )

    # When it is rendered as text and as JSON
    lines = _text(listing)
    rule = json.loads(render_listing(listing, as_json=True))["rules"][0]

    # Then the text has `layers: none` and `roots: not applied` and no `roots:`
    # under the block, and the JSON has the nulls
    assert lines[:3] == ["view: every rule", "layers: none", "roots: not applied"]
    assert not any(line.strip().startswith("roots:") for line in lines[4:])
    assert (rule["roots"], rule["root_independent"], rule["included"]) == (
        None,
        None,
        True,
    )
