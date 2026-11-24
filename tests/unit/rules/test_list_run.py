# SPDX-License-Identifier: Apache-2.0
"""Tests of how `wio rules list` runs its pipeline."""

from argparse import Namespace
from typing import TYPE_CHECKING, Any

from tests.fakes import FakeEnvironment
from tests.unit.fakes import ROOT, FakeRepository, FakeStdio, MemoryFileSystem
from tests.unit.rules.support import Roots, Settings
from wio.models.config import Config, Root
from wio.models.frozen import freeze
from wio.rules import Services, listing

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def _files() -> dict[Path, str]:
    """Write the rule files of a ruleset `demo` with a rule preset.

    Returns:
        The files by path.
    """
    base = ROOT / ".agents" / "wio" / "rules" / "demo"
    rule = '<!-- wio\ncode = "ARC001"\nname = "keep"\n-->\n\nKeep.\n'
    manifest = '[families]\nARC = "A"\n[rule_presets.all2]\nrules_include = ["ARC"]\n'
    return {base / "ruleset.toml": manifest, base / "ARC001-keep.md": rule}


def _args(**given: Any) -> Namespace:  # noqa: ANN401
    """Build the parsed arguments of `wio rules list`.

    Args:
        **given: The arguments that differ from no selector and no flag.

    Returns:
        The namespace.
    """
    found: dict[str, Any] = {
        "root": None,
        "path": None,
        "work": None,
        "stage": None,
        "references": [],
        "not_selected": False,
        "explain": False,
        "json": False,
    }
    return Namespace(**{**found, **given})


def test_the_rules_selected_anywhere_are_computed_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """C-2: one call gives its result to both `narrow` and `explain`."""
    # Given a repository, and a count of the calls of `selected_anywhere`
    config = Config(roots=freeze({"api": Root(("src",), ("demo.all2",))}))
    services = Services(
        Settings(config),
        FakeRepository(),
        MemoryFileSystem(_files()),
        FakeEnvironment(ROOT),
        Roots({}),
    )
    calls: list[int] = []
    real = listing.selected_anywhere

    def counted(*args: Any) -> Any:  # noqa: ANN401
        calls.append(1)
        return real(*args)

    monkeypatch.setattr(listing, "selected_anywhere", counted)

    # When the command narrows and explains one listing
    code = listing.run_list(
        services,
        _args(references=["demo.all"], not_selected=True, explain=True),
        FakeStdio(),
    )

    # Then the rules were selected anywhere once
    assert code == 0
    assert calls == [1]
