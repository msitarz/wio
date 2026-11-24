# SPDX-License-Identifier: Apache-2.0
"""Tests of the rules that `wio.cli` gives `wio trailers`."""

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from tests.support import enter, git
from wio.cli import null
from wio.cli.table import _trailers_services

if TYPE_CHECKING:
    import pytest

    from tests.sandbox import Sandbox

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "trailers" / "command"


def test_trailers_selects_its_rules_with_the_selector(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-9: `NoRules` is gone and the `StageRules` of `wio trailers` is a selector."""
    # Given a repository, entered as the working directory
    shutil.copytree(FIXTURE, sandbox.root, dirs_exist_ok=True)
    git(sandbox, "init", "-q", check=True)
    enter(sandbox, monkeypatch)

    # When `wio.cli` builds the services of `wio trailers`
    services = _trailers_services()

    # Then `wio.cli.null` has no `NoRules`, and the rules are a `RuleSelector`
    # that finds the roots of a Work where the contracts are found; `tests.integration`
    # may not import `wio.rules`, so the class is named and not imported
    assert not hasattr(null, "NoRules")
    assert type(services.rules).__name__ == "RuleSelector"
    assert getattr(services.rules, "work_roots", None) is services.contracts
