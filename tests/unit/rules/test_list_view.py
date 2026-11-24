# SPDX-License-Identifier: Apache-2.0
"""Tests of the view that `wio rules list` builds from a selector."""

from pathlib import PurePosixPath
from typing import TYPE_CHECKING

import pytest

from tests.unit.rules.support import Roots, make_ruleset
from wio.models.config import Config, Root, Ruleset, Stage
from wio.models.frozen import freeze
from wio.rules.listing import ListRequest, list_view

if TYPE_CHECKING:
    from collections.abc import Mapping

    from wio.models.listing import Listing
    from wio.models.rule import LoadedRuleset

_WORKS = Roots({"W": ("api",), "N": ()})


def _rulesets(*, reverse: bool = False) -> Mapping[str, LoadedRuleset]:
    """Build the rulesets of the repository of AC-2.

    Args:
        reverse: Whether to build them in the opposite order.

    Returns:
        `demo` with `ARC001`, `ARC002` and `PAY001` and a rule preset `arc`,
        `web` with `WEB001` and a rule preset `core`, and `process` with
        `FIX001`.
    """
    sets = [
        make_ruleset(
            "demo",
            ["ARC", "PAY"],
            ["ARC001", "ARC002", "PAY001"],
            {"arc": (["ARC"], [])},
        ),
        make_ruleset("web", ["WEB"], ["WEB001"], {"core": (["WEB001"], [])}),
        make_ruleset("process", ["FIX"], ["FIX001"]),
    ]
    return {s.name: s for s in (reversed(sets) if reverse else sets)}


def _config(*, reverse: bool = False) -> Config:
    """Build the config of the repository of AC-2 to AC-4.

    Args:
        reverse: Whether to write its tables in the opposite order.

    Returns:
        The roots `api` and `ui`, the stages `s`, `t` and `x`, and the always
        include of `process.FIX001`.
    """
    roots = [
        ("api", Root(("src/api",), ("demo.arc",))),
        ("ui", Root(("src/ui",), ("web.core",))),
    ]
    stages = [
        ("s", Stage(goal="g", rules_include=("demo.PAY001", "web.WEB001"))),
        ("t", Stage(goal="g", roots=("ui",))),
        ("x", Stage(goal="g", rules_exclude=("demo.ARC002",))),
    ]
    return Config(
        roots=freeze(dict(reversed(roots) if reverse else roots)),
        stages=freeze(dict(reversed(stages) if reverse else stages)),
        rulesets=freeze({"process": Ruleset(root_independent=True)}),
        rules_always_include=("process.FIX001",),
    )


def _request(
    *,
    root: str | None = None,
    path: str | None = None,
    work: str | None = None,
    stage: str | None = None,
) -> ListRequest:
    """Build a request for a view.

    Args:
        root: The `--root` argument.
        path: The `--path` argument, relative to the repository.
        work: The `--work` argument.
        stage: The `--stage` argument.

    Returns:
        The request, with no references and no flags.
    """
    where = PurePosixPath(path) if path else None
    return ListRequest(
        root, where, work, stage, (), not_selected=False, explain=False, as_json=False
    )


def _view(request: ListRequest, *, reverse: bool = False) -> Listing:
    """Build the listing of a request over the repository.

    Args:
        request: The view.
        reverse: Whether to declare the repository in the opposite order.

    Returns:
        The listing.
    """
    return list_view(
        request, _config(reverse=reverse), _rulesets(reverse=reverse), _WORKS
    )


def _included(listing: Listing) -> list[str]:
    """List the qualified codes of the included rules.

    Args:
        listing: The listing.

    Returns:
        The codes in the order of the rows.
    """
    return [
        row.rule.qualified
        for row in listing.rows
        if row.decision is not None and row.decision.included
    ]


@pytest.mark.parametrize(
    ("request_", "view"),
    [
        (_request(root="api"), "root api"),
        (_request(path="src/api/app.py"), "file src/api/app.py"),
        (_request(work="W"), "Work W"),
    ],
    ids=["root", "path", "work"],
)
def test_a_root_a_path_or_a_work_gives_the_rules_that_apply(
    request_: ListRequest, view: str
) -> None:
    """AC-2: the roots' layer and the always fields give the same rules."""
    # Given the repository, and a request for a root, a path or a Work
    # When the view is built
    listing = _view(request_)

    # Then it holds the rules of `api` and the always include, under the header
    assert _included(listing) == ["demo.ARC001", "demo.ARC002", "process.FIX001"]
    assert listing.header.view == view
    assert listing.header.layers == ("roots", "always fields")
    assert listing.header.roots == ("api",)


def test_a_stage_alone_applies_its_layer_and_cuts_nothing() -> None:
    """AC-3: the roots are not applied and each rule lists the roots reaching it."""
    # Given the repository and the stage `s`
    # When the view of `--stage s` is built
    listing = _view(_request(stage="s"))

    # Then the roots are not applied and the rules carry the roots that reach them
    found = {
        row.rule.qualified: (row.decision.roots, row.decision.root_independent)
        for row in listing.rows
        if row.decision and row.decision.included
    }
    assert found == {
        "demo.PAY001": (("api",), False),
        "process.FIX001": ((), True),
        "web.WEB001": (("ui",), False),
    }
    assert listing.header.layers == ("stage", "always fields")
    assert listing.header.roots is None


def test_a_root_with_a_stage_applies_both() -> None:
    """AC-3: the stage's include joins the root's rules and its line is shown."""
    # Given the repository and the stage `s`
    # When the view of `--root api --stage s` is built
    listing = _view(_request(root="api", stage="s"))

    # Then `PAY001` joins the rules of `api` and `WEB001` is cut
    assert _included(listing) == [
        "demo.ARC001",
        "demo.ARC002",
        "demo.PAY001",
        "process.FIX001",
    ]
    assert listing.header.stage == "s"


def test_the_stage_decides_which_roots_of_a_work_count() -> None:
    """AC-4: with no stage, or one with no roots, the Work's; else the stage's."""
    # Given the repository, a Work `W` in `api` and the stages `s` and `t`
    # When the views of `--work W`, `--work W --stage s` and `--work W --stage t`
    # are built
    plain = _view(_request(work="W"))
    own = _view(_request(work="W", stage="s"))
    chosen = _view(_request(work="W", stage="t"))

    # Then the first two have the roots `api`, and the third has `ui` only
    assert plain.header.roots == own.header.roots == ("api",)
    assert _included(chosen) == ["process.FIX001", "web.WEB001"]
    assert chosen.header.roots == ("ui",)


def test_a_path_with_a_stage_applies_the_roots_that_contain_it() -> None:
    """AC-14: `--path` with `--stage` is `--root` with `--stage`."""
    # Given the repository and the stage `s`
    # When the view of a file of `api` with `s` is built
    listing = _view(_request(path="src/api/app.py", stage="s"))

    # Then the rules are those of `--root api --stage s`
    assert _included(listing) == _included(_view(_request(root="api", stage="s")))
    assert listing.header.layers == ("roots", "stage", "always fields")


def test_a_view_without_a_selector_has_no_decision() -> None:
    """AC-12: every rule is a row with no decision, and no layer is applied."""
    # Given the repository
    # When the view with no selector is built
    listing = _view(_request())

    # Then every rule is a row without a decision, in the order of the rulesets
    assert [row.rule.qualified for row in listing.rows] == [
        "demo.ARC001",
        "demo.ARC002",
        "demo.PAY001",
        "process.FIX001",
        "web.WEB001",
    ]
    assert all(row.decision is None for row in listing.rows)
    assert (listing.header.layers, listing.header.roots) == ((), None)


def test_a_path_in_no_root_applies_no_root() -> None:
    """AC-12: only the root-independent rules remain, with `roots` empty."""
    # Given the repository and a file that no root contains
    # When the view of that file is built
    listing = _view(_request(path="docs/readme.md"))

    # Then the roots applied are none and only `process.FIX001` is included
    assert listing.header.roots == ()
    assert _included(listing) == ["process.FIX001"]


@pytest.mark.parametrize(
    ("request_", "error"),
    [
        (_request(stage="nope"), KeyError),
        (_request(root="nope"), KeyError),
        (_request(work="nope"), KeyError),
        (_request(work="N"), ValueError),
    ],
    ids=["stage", "root", "work", "no roots"],
)
def test_a_selector_that_cannot_be_used_is_not_caught(
    request_: ListRequest, error: type[Exception]
) -> None:
    """AC-6: the errors of the roots and the layers reach the command."""
    # Given the repository
    # When the view is built
    # Then the error of the selector is raised
    with pytest.raises(error):
        _view(request_)


@pytest.mark.parametrize(
    "request_",
    [
        _request(),
        _request(root="api"),
        _request(path="src/ui/a.py"),
        _request(work="W", stage="s"),
        _request(stage="x"),
    ],
)
def test_the_listing_does_not_depend_on_the_order_of_the_inputs(
    request_: ListRequest,
) -> None:
    """AC-11: two declarations of the same repository give equal listings."""
    # Given the repository declared in two orders, with a fake `WorkRoots`
    # When the view is built on each
    forward = _view(request_)
    backward = _view(request_, reverse=True)

    # Then the listings are equal
    assert forward == backward
