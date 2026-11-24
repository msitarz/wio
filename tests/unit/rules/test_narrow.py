# SPDX-License-Identifier: Apache-2.0
"""Tests of narrowing a listing by references and by `--not-selected`."""

from dataclasses import replace
from typing import TYPE_CHECKING

import pytest

from tests.unit.rules.support import Roots, make_ruleset
from wio.errors import WioError
from wio.models.config import Config, Root, Ruleset, Stage
from wio.models.frozen import freeze
from wio.rules import selected_anywhere
from wio.rules.listing import ListRequest, list_view, render_listing
from wio.rules.narrowing import narrow

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from wio.models.listing import Listing
    from wio.models.rule import LoadedRuleset

pytestmark = pytest.mark.xfail(
    raises=NotImplementedError, strict=True, reason="narrow is a stub"
)


def _rulesets(
    *, broken: bool = False, reverse: bool = False
) -> Mapping[str, LoadedRuleset]:
    """Build the rulesets of the repository.

    Args:
        broken: Whether `demo` also has the rule presets `loop` and `bad`.
        reverse: Whether to build them in the opposite order.

    Returns:
        `demo` with `ARC001`, `ARC002`, `PAY001` and `PAY002` and the rule presets
        `recommended` and `spare`, `web` with `WEB001`, and `process` with
        `FIX001` and `FIX002`.
    """
    presets: dict[str, tuple[list[str], list[str]]] = {
        "recommended": (["ARC"], ["ARC002"]),
        "spare": (["PAY"], []),
    }
    if broken:
        presets |= {"loop": (["loop"], []), "bad": (["ZZZ"], [])}
    sets = [
        make_ruleset(
            "demo", ["ARC", "PAY"], ["ARC001", "ARC002", "PAY001", "PAY002"], presets
        ),
        make_ruleset("web", ["WEB"], ["WEB001"]),
        make_ruleset("process", ["FIX"], ["FIX001", "FIX002"]),
    ]
    return {s.name: s for s in (reversed(sets) if reverse else sets)}


def _config(*, reverse: bool = False) -> Config:
    """Build the config: a root `api`, a stage `s` and an always include.

    Args:
        reverse: Whether to write its tables in the opposite order.

    Returns:
        The root `api` whose only rule preset is `demo.recommended`, the stage `s`
        that includes `demo.PAY001`, and `process.FIX001` always included, with
        `process` independent of roots.
    """
    included = ("demo.PAY001",)
    return Config(
        roots=_table({"api": Root(("src",), ("demo.recommended",))}, reverse),
        stages=_table({"s": Stage(goal="g", rules_include=included)}, reverse),
        rulesets=_table({"process": Ruleset(root_independent=True)}, reverse),
        rules_always_include=("process.FIX001",),
    )


def _table[T](table: dict[str, T], reverse: bool) -> frozendict[str, T]:  # noqa: FBT001
    """Freeze a table of the config, in the opposite order when asked.

    Args:
        table: The entries by name.
        reverse: Whether to insert them in the opposite order.

    Returns:
        The frozen table.
    """
    return freeze(dict(reversed(table.items()) if reverse else table.items()))


def _view(
    *, root: str | None = None, stage: str | None = None, reverse: bool = False
) -> Listing:
    """Build the listing of a view over the repository.

    Args:
        root: The root of the view, if any.
        stage: The stage of the view, if any.
        reverse: Whether to declare the repository in the opposite order.

    Returns:
        The listing, with no layers when neither is given.
    """
    request = ListRequest(
        root, None, None, stage, (), not_selected=False, explain=False, as_json=False
    )
    return list_view(
        request, _config(reverse=reverse), _rulesets(reverse=reverse), Roots({})
    )


def _narrow(
    listing: Listing,
    references: Sequence[str] = (),
    *,
    not_selected: bool = False,
    broken: bool = False,
    reverse: bool = False,
) -> Listing:
    """Narrow a listing over the repository.

    Args:
        listing: The listing.
        references: The references.
        not_selected: Whether to keep only the rules that no entry delivers.
        broken: Whether `demo` has the rule presets `loop` and `bad`.
        reverse: Whether to declare the repository in the opposite order.

    Returns:
        The narrowed listing.
    """
    config = _config(reverse=reverse)
    rulesets = _rulesets(broken=broken, reverse=reverse)
    anywhere = selected_anywhere(config, rulesets)
    return narrow(
        listing,
        references,
        not_selected=not_selected,
        config=config,
        rulesets=rulesets,
        anywhere=anywhere,
    )


def _codes(listing: Listing) -> list[str]:
    """List the codes of the rows of a listing.

    Args:
        listing: The listing.

    Returns:
        The codes in the order of the rows.
    """
    return [row.rule.code for row in listing.rows]


@pytest.mark.parametrize(
    ("reference", "codes"),
    [
        ("demo.recommended", ["ARC001"]),
        ("demo.ARC", ["ARC001", "ARC002"]),
        ("demo.PAY001", ["PAY001"]),
        ("demo.all", ["ARC001", "ARC002", "PAY001", "PAY002"]),
    ],
)
def test_a_reference_narrows_to_the_rules_it_delivers(
    reference: str, codes: list[str]
) -> None:
    """AC-1: the rows are what the reference expands to, and the header names it."""
    # Given the listing of every rule with no layers
    listing = _view()

    # When it is narrowed by one reference
    found = _narrow(listing, [reference])

    # Then the rows are the rules the reference delivers, in order
    assert _codes(found) == codes
    assert found.header.references == (reference,)


def test_a_row_records_the_routes_of_the_references() -> None:
    """AC-1: the route of `ARC001` runs through the rule preset to the family."""
    # Given the listing of every rule with no layers
    listing = _view()

    # When it is narrowed by `demo.recommended`
    (row,) = _narrow(listing, ["demo.recommended"]).rows

    # Then the row holds the route of the rule preset and its family
    assert row.via == (("demo.recommended", "demo.ARC"),)


def test_several_references_keep_the_rules_that_any_delivers() -> None:
    """AC-2: a union, each rule once, in the order of the repository."""
    # Given the listing of every rule with no layers
    listing = _view()

    # When it is narrowed by `demo.PAY` and `demo.ARC001` together
    found = _narrow(listing, ["demo.PAY", "demo.ARC001"])

    # Then the rows are the three rules in order, and the header names both
    assert _codes(found) == ["ARC001", "PAY001", "PAY002"]
    assert found.header.references == ("demo.PAY", "demo.ARC001")


def test_a_reference_narrows_a_listing_that_applied_layers() -> None:
    """AC-3: the row of an included rule, or only out rows, and no error."""
    # Given the listing of the root `api`, which holds every rule with its decision
    listing = _view(root="api")

    # When it is narrowed by `demo.ARC001` and by `demo.PAY`
    included = _narrow(listing, ["demo.ARC001"])
    out = _narrow(listing, ["demo.PAY"])

    # Then the first holds the included row with its roots and the second only
    # out rows, so nothing is shown
    (row,) = included.rows
    assert row.decision is not None
    assert (row.decision.included, row.decision.roots) == (True, ("api",))
    assert _codes(out) == ["PAY001", "PAY002"]
    assert all(r.decision and not r.decision.included for r in out.rows)
    assert render_listing(out, as_json=False).endswith("\n\n")


def test_not_selected_keeps_the_rules_that_no_entry_delivers() -> None:
    """AC-4: the unselected rules are held, and the header is marked."""
    # Given the listing of every rule with no layers, in a repository whose
    # root-independent `process` also has `FIX002`, which nothing delivers
    listing = _view()

    # When it is narrowed with `--not-selected` and no references
    found = _narrow(listing, not_selected=True)

    # Then the rules no entry delivers are held and the header is marked
    assert [row.rule.qualified for row in found.rows] == [
        "demo.ARC002",
        "demo.PAY002",
        "process.FIX002",
        "web.WEB001",
    ]
    assert found.header.not_selected


def test_the_candidates_follow_the_roots_of_the_view() -> None:
    """AC-5: roots applied cut `web`, and no roots keep every rule."""
    # Given the listing of the root `api` and the listing of the stage `s`
    rooted = _view(root="api")
    staged = _view(stage="s")

    # When each is narrowed with `--not-selected`
    with_roots = _narrow(rooted, not_selected=True)
    without = _narrow(staged, not_selected=True)

    # Then the first lacks `WEB001` and the second has it
    assert _codes(with_roots) == ["ARC002", "PAY002", "FIX002"]
    assert _codes(without) == ["ARC002", "PAY002", "FIX002", "WEB001"]


@pytest.mark.parametrize(
    ("reference", "codes"),
    [("demo.spare", ["PAY002"]), ("demo.recommended", []), ("demo.PAY", ["PAY002"])],
)
def test_a_reference_with_not_selected_says_whether_it_is_in_use(
    reference: str, codes: list[str]
) -> None:
    """AC-6: of the rules a reference delivers, those that no entry delivers."""
    # Given the listing of every rule with no layers
    listing = _view()

    # When it is narrowed with `--not-selected` and the reference
    found = _narrow(listing, [reference], not_selected=True)

    # Then the rows are the rules of the reference that nothing delivers
    assert _codes(found) == codes


@pytest.mark.parametrize(
    ("reference", "why"),
    [
        ("demo.ZZZ", "names nothing"),
        ("demo.ARC999", "names nothing"),
        ("demo.none", "names nothing"),
        ("Docs", "is not a reference"),
        ("recommended", "names no rule preset"),
        ("demo.loop", "cycle"),
        ("demo.bad", "ZZZ"),
    ],
)
def test_a_reference_that_cannot_be_used_is_refused(reference: str, why: str) -> None:
    """AC-7: a `WioError` that names the reference and says why."""
    # Given the listing, a rule preset that includes itself and one with a bad entry
    listing = _view()

    # When it is narrowed by the reference
    # Then a `WioError` names the reference and the reason
    with pytest.raises(WioError) as raised:
        _narrow(listing, [reference], broken=True)
    assert reference in str(raised.value)
    assert why in str(raised.value)


def test_the_result_does_not_depend_on_the_order_of_the_inputs() -> None:
    """AC-8: equal results, except the order the header names the references."""
    # Given the repository declared in two orders and the references in two orders
    refs = ["demo.PAY", "demo.spare"]

    # When it is narrowed with `--not-selected` on each
    forward = _narrow(_view(), refs, not_selected=True)
    backward = _narrow(_view(reverse=True), refs[::-1], not_selected=True, reverse=True)

    # Then the results are equal but for the references of the header
    assert forward.header.references == tuple(refs)
    assert backward.header.references == tuple(refs[::-1])
    bare = replace(forward.header, references=())
    assert replace(backward, header=replace(backward.header, references=())) == replace(
        forward, header=bare
    )
