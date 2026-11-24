# SPDX-License-Identifier: Apache-2.0
"""System tests of `wio.rules` through the selector that `wio.context` will use."""

import json
from argparse import Namespace
from typing import TYPE_CHECKING

from tests.fakes import FakeEnvironment
from tests.unit.fakes import ROOT, FakeRepository, FakeStdio, MemoryFileSystem
from tests.unit.rules.support import Roots, Settings, contract, said
from wio.models.config import Config, Root, Stage
from wio.models.frozen import freeze
from wio.rules import RuleSelector, Services
from wio.rules.creating import run_new
from wio.rules.listing import run_list

if TYPE_CHECKING:
    from wio.models.rules import Decision, Selection

_RULES = ROOT / ".agents" / "wio" / "rules"
_MANIFEST = '[families]\nARC = "A"\n'


def _rule(code: str, name: str) -> str:
    """Write a rule file in the comment form.

    Args:
        code: The rule's code.
        name: The rule's name.

    Returns:
        The text of the file.
    """
    return f'<!-- wio\ncode = "{code}"\nname = "{name}"\n-->\n\nBody.\n'


def _front(code: str, name: str) -> str:
    """Write a rule file in the `+++` front matter form.

    Args:
        code: The rule's code.
        name: The rule's name.

    Returns:
        The text of the file.
    """
    return f'+++\nwio = 1\ncode = "{code}"\nname = "{name}"\n+++\n\nBody.\n'


def _config() -> Config:
    """Build a config with a root `api` that reaches `demo`, and two stages.

    Returns:
        The root `api` with `demo.all`, the stage `s` that includes `web.WEB001` and
        excludes `demo.ARC002`, and the stage `t` with no entries.
    """
    return Config(
        roots=freeze({"api": Root(("src",), ("demo.all",))}),
        stages=freeze(
            {
                "s": Stage(
                    goal="g",
                    rules_include=("web.WEB001",),
                    rules_exclude=("demo.ARC002",),
                ),
                "t": Stage(goal="g"),
            }
        ),
    )


def _disk(files: dict[str, str]) -> MemoryFileSystem:
    """Build the files of a repository.

    Args:
        files: The text of each file by its path below the rules directory.

    Returns:
        The file system.
    """
    return MemoryFileSystem({_RULES / name: text for name, text in files.items()})


def _services(disk: MemoryFileSystem) -> Services:
    """Wire `wio rules` over a disk, for a Work `w1` whose root is `api`.

    Args:
        disk: The files.

    Returns:
        The services.
    """
    return Services(
        Settings(_config()),
        FakeRepository(),
        disk,
        FakeEnvironment(ROOT),
        Roots({"w1": ("api",)}),
    )


def _selector(disk: MemoryFileSystem) -> RuleSelector:
    """Build the selector over a disk, as `wio.cli` builds it.

    Args:
        disk: The files.

    Returns:
        A selector for a Work `w1` whose root is `api`.
    """
    return RuleSelector(
        Settings(_config()), FakeRepository(), disk, Roots({"w1": ("api",)})
    )


def _included(selection: Selection) -> dict[str, tuple[str, ...]]:
    """Collect the included rules of a selection with their roots.

    Args:
        selection: The selection.

    Returns:
        The roots of each included rule by qualified code.
    """
    return {r.qualified: d.roots for r, d in selection.items() if d.included}


def _reasons(selection: Selection) -> dict[str, str]:
    """Collect why each rule that is out of a selection is out.

    Args:
        selection: The selection.

    Returns:
        The kind of the reason of each rule that is out, by qualified code.
    """
    return {r.qualified: _kind(d) for r, d in selection.items() if not d.included}


def _kind(decision: Decision) -> str:
    """Name the reason that a decision is out.

    Args:
        decision: The decision of a rule that is out.

    Returns:
        The kind of its reason.
    """
    assert decision.reason is not None
    return decision.reason.kind


def test_a_new_rule_is_selected_through_the_port_without_an_edit() -> None:
    """AC-1: after `new`, the selection for the Work at the stage includes it."""
    # Given a ruleset whose root reaches it and a Work whose root is `api`
    disk = _disk(
        {"demo/ruleset.toml": _MANIFEST, "demo/ARC001-a.md": _rule("ARC001", "a")}
    )
    streams = FakeStdio()

    # When a rule is created, and the selection is asked for through `RuleSelection`
    done = run_new(
        _services(disk),
        Namespace(
            ruleset="demo", family="ARC", name="keep", description=None, json=False
        ),
        streams,
    )
    selection = _selector(disk).select(contract("w1"), "t")

    # Then the new rule is included with the root `api`
    assert done == 0
    assert _included(selection)["demo.ARC002"] == ("api",)


def test_the_selection_of_the_port_is_the_one_that_list_explains() -> None:
    """AC-2: the same included rules, roots and reasons as `list --explain`."""
    # Given an included rule, one excluded by the stage and one cut by the roots
    disk = _disk(
        {
            "demo/ruleset.toml": _MANIFEST,
            "demo/ARC001-keep.md": _rule("ARC001", "keep"),
            "demo/ARC002-name.md": _rule("ARC002", "name"),
            "web/ruleset.toml": '[families]\nWEB = "W"\n',
            "web/WEB001-page.md": _rule("WEB001", "page"),
        }
    )
    streams = FakeStdio()

    # When the selection is asked for through `RuleSelection` and `list --explain`
    # runs for the same Work and stage
    selection = _selector(disk).select(contract("w1"), "s")
    args = Namespace(
        root=None,
        path=None,
        work="w1",
        stage="s",
        references=(),
        not_selected=False,
        explain=True,
        json=True,
    )
    assert run_list(_services(disk), args, streams) == 0
    rows = json.loads(said(streams))["rules"]

    # Then the included rules and their roots, and the reasons for the others, are
    # identical
    listed = {r["code"]: tuple(r["roots"]) for r in rows if r["included"]}
    assert listed == _included(selection) == {"demo.ARC001": ("api",)}
    reasons = {r["code"]: r["reason"] for r in rows if not r["included"]}
    assert set(reasons) == set(_reasons(selection))
    assert _reasons(selection) == {
        "demo.ARC002": "excluded",
        "web.WEB001": "cut-by-roots",
    }
    assert all(reasons.values())


def test_a_rule_in_either_form_is_selected_alike() -> None:
    """AC-7: both forms are included with the root `api`, and the hash is cited."""
    # Given `ARC001` in the comment form and `ARC002` in the `+++` form, both
    # reached by the root `api`
    disk = _disk(
        {
            "demo/ruleset.toml": _MANIFEST,
            "demo/ARC001-comment.md": _rule("ARC001", "comment"),
            "demo/ARC002-front.md": _front("ARC002", "front"),
        }
    )
    selector = _selector(disk)

    # When the selection is asked for through `RuleSelection`, and the rules that
    # the stage selects are asked for through `StageRules`
    selection = selector.select(contract("w1"), "t")
    cited = selector.selected("w1", "deliver", "t")

    # Then both are included alike and both are cited with a hash
    assert _included(selection) == {"demo.ARC001": ("api",), "demo.ARC002": ("api",)}
    assert set(cited) == {"demo.ARC001", "demo.ARC002"}
