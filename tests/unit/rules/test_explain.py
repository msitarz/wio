# SPDX-License-Identifier: Apache-2.0
"""Tests of the explanation that `--explain` adds to a listing."""

import json
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

import pytest

from tests.unit.rules.support import Roots, make_ruleset
from wio.models.config import Config, Root, Ruleset, Stage
from wio.models.frozen import freeze
from wio.models.rules import Reason
from wio.rules import narrow, selected_anywhere
from wio.rules.explaining import explain
from wio.rules.listing import ListRequest, list_view, render_listing

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from wio.models.listing import Listing
    from wio.models.rule import LoadedRuleset

_RECOMMENDED = "root api ← demo.recommended ← demo.ARC"


@dataclass(frozen=True)
class _Repo:
    """A repository of the examples, which each criterion adjusts a little."""

    api: tuple[str, ...] = ("demo.recommended",)
    include: tuple[str, ...] = ("demo.PAY001",)
    exclude: tuple[str, ...] = ()
    veto: tuple[str, ...] = ()
    cut: tuple[str, ...] = ()
    recommended: tuple[str, ...] = ()
    reverse: bool = False
    always: tuple[str, ...] = ()

    def rulesets(self) -> Mapping[str, LoadedRuleset]:
        """Build the rulesets.

        Returns:
            `demo` with four rules and the rule presets `recommended` and `extra`,
            `process` with `FIX001`, and `web` with `WEB001`.
        """
        presets = {
            "recommended": (["ARC"], list(self.recommended)),
            "extra": (["PAY"], ["PAY002"]),
        }
        arc = ["ARC001", "ARC002", "PAY001", "PAY002"]
        sets = [
            make_ruleset("demo", ["ARC", "PAY"], arc, presets),
            make_ruleset("process", ["FIX"], ["FIX001"]),
            make_ruleset("web", ["WEB"], ["WEB001"]),
        ]
        return {s.name: s for s in (reversed(sets) if self.reverse else sets)}

    def config(self) -> Config:
        """Build the config.

        Returns:
            The root `api`, the stage `s`, `process.all` always included and
            `process` independent of roots.
        """
        stage = Stage(goal="g", rules_include=self.include, rules_exclude=self.exclude)
        tables = [("api", Root(("src",), self.api)), ("s", stage)]
        order = tables[::-1] if self.reverse else tables
        return Config(
            roots=freeze({k: v for k, v in order if isinstance(v, Root)}),
            stages=freeze({k: v for k, v in order if isinstance(v, Stage)}),
            rulesets=freeze({"process": Ruleset(root_independent=True)}),
            rules_always_include=("process.all", *self.always),
            rules_always_exclude=self.veto,
        )


def _listing(
    repo: _Repo,
    *,
    refs: tuple[str, ...] = (),
    not_selected: bool = False,
    view: str = "work",
) -> Listing:
    """Build, narrow and explain the listing of a view.

    Args:
        repo: The repository.
        refs: The references to narrow by.
        not_selected: Whether to narrow by `--not-selected`.
        view: `work` for the Work at the stage `s`, `root` for the root `api`, or
            `all` for every rule with no layers.

    Returns:
        The explained listing.
    """
    config, rulesets = repo.config(), repo.rulesets()
    work = "W" if view == "work" else None
    root = "api" if view == "root" else None
    stage = "s" if view == "work" else None
    request = ListRequest(
        root,
        None,
        work,
        stage,
        refs,
        not_selected=not_selected,
        explain=True,
        as_json=False,
    )
    found = list_view(request, config, rulesets, Roots({"W": ("api",)}))
    anywhere = selected_anywhere(config, rulesets)
    if refs or not_selected:
        found = narrow(
            found,
            refs,
            not_selected=not_selected,
            config=config,
            rulesets=rulesets,
            anywhere=anywhere,
        )
    return explain(found, anywhere)


def _lines(listing: Listing, code: str) -> tuple[str, ...]:
    """Find the explanation lines of a rule.

    Args:
        listing: The explained listing.
        code: The rule's qualified code.

    Returns:
        Its `lines()`.
    """
    (row,) = (r for r in listing.rows if r.rule.qualified == code)
    assert row.explanation is not None
    return row.explanation.lines()


def _agree(listing: Listing, code: str, rule: Mapping[str, Sequence[object]]) -> bool:
    """Tell whether the text and the JSON of a rule state the same chains.

    Args:
        listing: The explained listing.
        code: The rule's qualified code.
        rule: Its JSON object.

    Returns:
        Whether it has as many `from:` and `by:` lines as `origins` and
        `removed_by` have chains.
    """
    lines = _lines(listing, code)
    origins, removed = rule["origins"], rule["removed_by"]
    origin_lines = [line for line in lines if line.startswith("from:")]
    removal_lines = [line for line in lines if line.startswith("by:")]
    return (len(origin_lines), len(removal_lines)) == (len(origins), len(removed))


def test_an_included_rule_shows_where_it_came_from() -> None:
    """AC-1: one `from:` line for each route of each origin."""
    # Given the repository, a Work in `api` and the stage `s`
    repo = _Repo()

    # When the listing of the Work at the stage is built and explained
    listing = _listing(repo)

    # Then each included rule names the layer and the route that selected it
    assert f"from: demo.ARC001 ← {_RECOMMENDED}" in _lines(listing, "demo.ARC001")
    assert "from: demo.PAY001 ← stage s ← demo.PAY001" in _lines(listing, "demo.PAY001")
    assert "from: process.FIX001 ← rules_always_include ← process.all" in _lines(
        listing, "process.FIX001"
    )


def test_a_rule_with_several_origins_shows_them_in_order() -> None:
    """AC-2: the root first and the stage second."""
    # Given a stage that also includes `demo.ARC001`
    repo = _Repo(include=("demo.PAY001", "demo.ARC001"))

    # When the listing of the Work at the stage is built and explained
    lines = _lines(_listing(repo), "demo.ARC001")

    # Then there are two `from:` lines, the root's and then the stage's
    assert [line for line in lines if line.startswith("from:")] == [
        f"from: demo.ARC001 ← {_RECOMMENDED}",
        "from: demo.ARC001 ← stage s ← demo.ARC001",
    ]


def test_a_rule_that_is_out_shows_the_reason_and_what_removed_it() -> None:
    """AC-3: an `out:` line for each reason and a `by:` line for each removal."""
    # Given a stage that excludes `ARC002` and includes `WEB001`, a veto of
    # `PAY001`, and `api` that also names the rule preset `extra`
    repo = _Repo(
        api=("demo.recommended", "demo.extra"),
        include=("demo.PAY001", "web.WEB001"),
        exclude=("demo.ARC002",),
        veto=("demo.PAY001",),
    )

    # When the listing of the Work at the stage is built and explained
    listing = _listing(repo)

    # Then each out rule has its reason and the chain of what removed it
    arc2 = _lines(listing, "demo.ARC002")
    assert "out: excluded by the stage" in arc2
    assert "by: demo.ARC002 ← stage s ← demo.ARC002" in arc2
    pay1 = _lines(listing, "demo.PAY001")
    assert "from: demo.PAY001 ← root api ← demo.extra ← demo.PAY" in pay1
    assert "from: demo.PAY001 ← stage s ← demo.PAY001" in pay1
    assert "out: vetoed by rules_always_exclude" in pay1
    assert "by: demo.PAY001 ← rules_always_exclude ← demo.PAY001" in pay1
    pay2 = _lines(listing, "demo.PAY002")
    assert "out: excluded by the root's rule preset" in pay2
    assert "by: demo.PAY002 ← root api ← demo.extra ← demo.PAY002" in pay2
    web = _lines(listing, "web.WEB001")
    assert "out: cut by the roots" in web
    assert "from: web.WEB001 ← stage s ← web.WEB001" in web


def test_a_listing_of_references_shows_the_routes_of_the_references() -> None:
    """AC-4: each route, sorted, with no layer."""
    # Given the repository and the listing of every rule
    repo = _Repo()

    # When it is narrowed by `demo.recommended` and `demo.ARC` and explained
    listing = _listing(repo, refs=("demo.recommended", "demo.ARC"), view="all")

    # Then `ARC001` has the two routes in order
    assert _lines(listing, "demo.ARC001") == (
        "from: demo.ARC001 ← demo.ARC",
        "from: demo.ARC001 ← demo.recommended ← demo.ARC",
    )


def test_an_unselected_rule_shows_what_removed_it() -> None:
    """AC-5: `out: not selected`, and the exclude of a rule preset where it applies."""
    # Given a rule preset `recommended` that excludes `ARC002`
    repo = _Repo(recommended=("ARC002",))

    # When the listing of every rule is narrowed by `demo.ARC`, `demo.PAY` and
    # `--not-selected`, and the listing of the root `api` by `--not-selected`
    refs = _listing(repo, refs=("demo.ARC", "demo.PAY"), not_selected=True, view="all")
    root = _listing(repo, not_selected=True, view="root")

    # Then the first shows the routes of the references, `not selected` and what
    # removed `ARC002`, and the second the reason of the layers
    assert _lines(refs, "demo.ARC002") == (
        "from: demo.ARC002 ← demo.ARC",
        "out: not selected",
        "by: demo.ARC002 ← root api ← demo.recommended ← demo.ARC002",
    )
    assert _lines(refs, "demo.PAY002") == (
        "from: demo.PAY002 ← demo.PAY",
        "out: not selected",
    )
    assert _lines(root, "demo.ARC002") == (
        "out: excluded by the root's rule preset",
        "by: demo.ARC002 ← root api ← demo.recommended ← demo.ARC002",
    )
    assert _lines(root, "demo.PAY002") == ("out: not selected",)


def test_the_json_carries_the_same_explanation() -> None:
    """AC-6: `origins`, `reason` and `removed_by`, as arrays and a kind and layer."""
    # Given the repository of AC-3
    repo = _Repo(
        api=("demo.recommended", "demo.extra"),
        include=("demo.PAY001", "web.WEB001"),
        exclude=("demo.ARC002",),
        veto=("demo.PAY001",),
    )

    # When the listing is rendered as JSON, and its rows' lines are read
    listing = _listing(repo)
    rules = json.loads(render_listing(listing, as_json=True))["rules"]
    found = {rule["code"]: rule for rule in rules}

    # Then each rule has the three fields in the form of the contract, which
    # state what the text states
    assert found["demo.ARC001"]["origins"] == [
        ["root api", "demo.recommended", "demo.ARC"]
    ]
    assert found["demo.ARC001"]["reason"] is None
    assert found["demo.ARC002"]["reason"] == {"kind": "excluded", "layer": "stage"}
    assert found["demo.ARC002"]["removed_by"] == [["stage s", "demo.ARC002"]]
    assert found["demo.PAY001"]["reason"] == {"kind": "vetoed", "layer": None}
    assert found["demo.PAY002"]["reason"] == {"kind": "excluded", "layer": "root"}
    assert all(_agree(listing, code, rule) for code, rule in found.items())


def test_without_an_explanation_nothing_is_added() -> None:
    """AC-7: no `from:`, `out:` or `by:` line and no explanation field."""
    # Given the listing of the Work at the stage, built and not explained
    repo = _Repo()
    request = ListRequest(
        None, None, "W", "s", (), not_selected=False, explain=False, as_json=False
    )
    listing = list_view(request, repo.config(), repo.rulesets(), Roots({"W": ("api",)}))

    # When it is rendered as text and as JSON
    text = render_listing(listing, as_json=False)
    rules = json.loads(render_listing(listing, as_json=True))["rules"]

    # Then there is no line and no field
    assert not any(tag in text for tag in ("from:", "out:", "by:"))
    fields = ("origins", "reason", "removed_by")
    assert all(name not in rule for rule in rules for name in fields)


def test_the_explanation_does_not_depend_on_the_order_of_the_inputs() -> None:
    """AC-8: equal explanations for two orders of the tables and entries."""
    # Given the repository in two orders
    api = ("demo.recommended", "demo.extra")
    forward = _Repo(api=api, include=("demo.PAY001", "demo.ARC001"))
    backward = _Repo(
        api=api[::-1], include=("demo.ARC001", "demo.PAY001"), reverse=True
    )

    # When the listing of the Work at the stage is explained on each
    one, two = _listing(forward), _listing(backward)

    # Then the explanations are equal
    assert [r.explanation for r in one.rows] == [r.explanation for r in two.rows]


def test_there_is_nothing_to_explain_without_layers_or_references() -> None:
    """AC-9: no line for every rule with no layers."""
    # Given the repository and the listing of every rule
    repo = _Repo()

    # When it is explained
    listing = _listing(repo, view="all")

    # Then no `lines()` has a `from:`, `out:` or `by:` line
    assert all(row.explanation and not row.explanation.lines() for row in listing.rows)


def test_layers_explain_a_row_even_when_references_narrowed_it() -> None:
    """AC-9: the layers' chain, and not the route of the reference."""
    # Given the listing of the root `api`, narrowed by `demo.ARC`
    repo = _Repo()

    # When it is explained
    lines = _lines(_listing(repo, refs=("demo.ARC",), view="root"), "demo.ARC001")

    # Then the chain is that of the layers
    assert f"from: demo.ARC001 ← {_RECOMMENDED}" in lines
    assert "from: demo.ARC001 ← demo.ARC" not in lines


def test_a_reason_that_is_not_known_is_refused_and_not_explained_as_cut() -> None:
    """A reason of a layer that nothing gives is an error and not `cut by the roots`."""
    # Given the listing of the Work at the stage, in which a rule that the stage
    # excludes has a reason with no layer
    repo = _Repo(exclude=("demo.ARC002",))
    config, rulesets = repo.config(), repo.rulesets()
    request = ListRequest(
        None, None, "W", "s", (), not_selected=False, explain=True, as_json=False
    )
    found = list_view(request, config, rulesets, Roots({"W": ("api",)}))
    odd = Reason("excluded", None)
    rows = tuple(
        replace(row, decision=replace(row.decision, reason=odd))
        if row.rule.code == "ARC002" and row.decision is not None
        else row
        for row in found.rows
    )

    # When the listing is explained and written
    explained = explain(replace(found, rows=rows), selected_anywhere(config, rulesets))
    with pytest.raises(ValueError, match="is not one that a decision gives"):
        render_listing(explained, as_json=False)

    # Then writing it was refused


def test_a_rule_that_a_later_layer_added_back_shows_the_removal_too() -> None:
    """An included row has a `by:` line for what removed it before it came back."""
    # Given a rule that the root includes, the stage excludes and the always
    # includes add back
    repo = _Repo(exclude=("demo.ARC001",), always=("demo.ARC001",))

    # When the listing of the Work at the stage is explained
    lines = _lines(_listing(repo), "demo.ARC001")

    # Then the rule is included, and its lines show the origin and the removal
    assert not any(line.startswith("out:") for line in lines)
    assert "by: demo.ARC001 ← stage s ← demo.ARC001" in lines
    assert any(
        line.startswith("from: demo.ARC001 ← rules_always_include") for line in lines
    )
