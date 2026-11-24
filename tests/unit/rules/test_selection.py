# SPDX-License-Identifier: Apache-2.0
"""System tests of the selection: the discovery, the layers, the roots, the
selector and `selected_anywhere` working together over one repository."""

from pathlib import Path
from typing import TYPE_CHECKING

from tests.unit.fakes import ROOT, FakeRepository, MemoryFileSystem
from tests.unit.rules.support import Roots, Settings
from wio.formats import rule_hash
from wio.models.config import Config, Root, Ruleset, Stage
from wio.models.frozen import freeze
from wio.models.resolved import ResolvedContract
from wio.models.works import Work
from wio.rules import RuleSelector, discover, ruleset_map, select, selected_anywhere

if TYPE_CHECKING:
    from wio.models.rules import Selection

_DIR = ROOT / ".agents" / "wio" / "rules"
_ARC1 = _DIR / "demo" / "ARC001-arc001.md"


def _ruleset(name: str, manifest: str, codes: list[str]) -> dict[Path, str]:
    """Write the files of a ruleset.

    Args:
        name: The ruleset's name.
        manifest: The text of its `ruleset.toml`.
        codes: The codes of its rules, each in a file of its own.

    Returns:
        The files by path.
    """
    files = {_DIR / name / "ruleset.toml": manifest}
    for code in codes:
        slug = code.lower()
        text = f'<!-- wio\ncode = "{code}"\nname = "{slug}"\n-->\n\nRule {code}.\n'
        files[_DIR / name / f"{code}-{slug}.md"] = text
    return files


def _files() -> dict[Path, str]:
    """Write the rule files of the repository of AC-1 and AC-2.

    Returns:
        `demo` with `ARC001`, `ARC002`, `PAY001` and `PAY002`, `web` with
        `WEB001` and `process` with `FIX001`.
    """
    demo = '[families]\nARC = "A"\nPAY = "P"\n'
    demo += '[rule_presets.recommended]\nrules_include = ["ARC"]\n'
    web = '[families]\nWEB = "W"\n[rule_presets.core]\nrules_include = ["WEB001"]\n'
    return {
        **_ruleset("demo", demo, ["ARC001", "ARC002", "PAY001", "PAY002"]),
        **_ruleset("web", web, ["WEB001"]),
        **_ruleset("process", '[families]\nFIX = "F"\n', ["FIX001"]),
    }


def _config() -> Config:
    """Build the config of the repository of AC-1 and AC-2.

    Returns:
        The roots `api` and `contract`, the stages of both criteria, `FIX001`
        always included, `PAY001` always excluded and `process` independent of
        roots.
    """
    stages = {
        "main": Stage(
            goal="g",
            rules_include=("demo.PAY001", "web.WEB001"),
            rules_exclude=("demo.ARC002",),
        ),
        "alone": Stage(goal="g", roots=("contract",)),
        "both": Stage(goal="g", roots=("contract", "@work")),
        "none": Stage(goal="g", roots=()),
    }
    return Config(
        roots=freeze(
            {
                "api": Root(("src",), ("demo.recommended",)),
                "contract": Root(("docs",), ("web.core",)),
            }
        ),
        stages=freeze(stages),
        rulesets=freeze({"process": Ruleset(root_independent=True)}),
        rules_always_include=("process.FIX001",),
        rules_always_exclude=("demo.PAY001",),
    )


def _selector(disk: MemoryFileSystem) -> RuleSelector:
    """Build the selector over the repository.

    Args:
        disk: The files.

    Returns:
        A selector whose Work `in-api` has the root `api` and whose Work `bare`
        has none.
    """
    return RuleSelector(
        Settings(_config()),
        FakeRepository(),
        disk,
        Roots({"in-api": ("api",), "bare": ()}),
    )


def _by_code(selection: Selection) -> dict[str, tuple[bool, str | None]]:
    """Summarize a selection by the qualified code of each rule.

    Args:
        selection: The selection.

    Returns:
        For each rule whether it is included and the kind of its reason.
    """
    return {
        f"{rule.ruleset}.{rule.code}": (
            decision.included,
            decision.reason.kind if decision.reason else None,
        )
        for rule, decision in selection.items()
    }


def _included(selection: Selection) -> set[str]:
    """Collect the qualified codes of the rules a selection includes.

    Args:
        selection: The selection.

    Returns:
        The codes.
    """
    return {code for code, (included, _) in _by_code(selection).items() if included}


def test_a_work_at_a_stage_gets_one_decision_for_every_rule() -> None:
    """AC-1: included with roots and layers, or out with the reason."""
    # Given the repository, a Work in `api` and a stage that excludes, includes
    # and cuts rules
    selector = _selector(MemoryFileSystem(_files()))

    # When the selection for the Work at the stage is asked for
    chosen = selector.selection("in-api", "main")

    # Then each rule has one decision: included with its root and layer, or out
    # for the reason of the layer or the roots that removed it
    arc1 = next(d for r, d in chosen.items() if r.code == "ARC001")
    assert (arc1.roots, arc1.effects[0].layer) == (("api",), "root")
    assert _by_code(chosen) == {
        "demo.ARC001": (True, None),
        "demo.ARC002": (False, "excluded"),
        "demo.PAY001": (False, "vetoed"),
        "demo.PAY002": (False, "not-selected"),
        "web.WEB001": (False, "cut-by-roots"),
        "process.FIX001": (True, None),
    }
    assert len(chosen) == 6


def test_the_stage_decides_which_roots_count() -> None:
    """AC-2: its own roots, `@work`, or none."""
    # Given the repository, stages that select `contract`, `contract` and
    # `@work`, and no root, and a Work in `api` and one with no roots
    selector = _selector(MemoryFileSystem(_files()))

    # When the selection is asked for each stage and Work
    found = {
        (stage, work): selector.selection(work, stage)
        for stage in ("alone", "both", "none")
        for work in ("in-api", "bare")
    }

    # Then `alone` and `none` ignore the Work, `both` adds its roots, and a Work
    # with no roots gets every rule out as `not-selected` where it is needed
    web = {"web.WEB001"}
    for work in ("in-api", "bare"):
        assert _included(found["alone", work]) == web | {"process.FIX001"}
        assert _included(found["none", work]) == {"process.FIX001"}
    assert _included(found["both", "in-api"]) == web | {
        "demo.ARC001",
        "demo.ARC002",
        "process.FIX001",
    }
    assert {r for _, r in _by_code(found["both", "bare"]).values()} == {"not-selected"}


def test_context_and_trailers_get_the_selection_and_the_hashes() -> None:
    """AC-3: the selection, and the code and hash of each included rule."""
    # Given the repository with its Work and stage
    disk = MemoryFileSystem(_files())
    selector = _selector(disk)
    work = Work("in-api", None, Path("w.md"), None, (), (), freeze({}))

    # When `select` and `selected` run, then `ARC001` is edited and `selected`
    # runs again
    chosen = selector.select(ResolvedContract(work, "", ()), "main")
    first = selector.selected("in-api", "deliver", "main")
    same = selector.selection("in-api", "main")
    disk.files[_ARC1] += "More.\n"
    second = selector.selected("in-api", "deliver", "main")

    # Then the selection is that of AC-1, only the included rules have a hash,
    # and the edit changes the hash of `ARC001` alone
    assert chosen == same
    assert set(first) == {"demo.ARC001", "process.FIX001"}
    assert first["demo.ARC001"] == rule_hash(_files()[_ARC1].encode()), (
        "the hash is that of the file"
    )
    assert second["demo.ARC001"] != first["demo.ARC001"]
    assert second["process.FIX001"] == first["process.FIX001"]


def test_a_rule_that_is_selected_nowhere_is_never_included() -> None:
    """AC-4: `select` includes only keys of `SelectedAnywhere.selected`."""
    # Given the repository, where no entry includes `demo.PAY002`
    config = _config()
    rulesets = ruleset_map(discover(ROOT, MemoryFileSystem(_files())))

    # When `selected_anywhere` runs and `select` runs for each root and stage, and
    # for no roots and no stage
    anywhere = selected_anywhere(config, rulesets)
    views = [
        select(roots, stage, config, rulesets)
        for roots in [(), *((name,) for name in config.roots)]
        for stage in (None, *config.stages)
    ]

    # Then every included rule is selected anywhere, the excluded and vetoed
    # rules are selected, and `PAY002` is not and is out in every view
    keys = {f"{rule.ruleset}.{rule.code}" for rule in anywhere.selected}
    assert set().union(*(_included(view) for view in views)) <= keys
    assert {"demo.ARC002", "demo.PAY001"} <= keys
    assert "demo.PAY002" not in keys
    assert all("demo.PAY002" not in _included(view) for view in views)
