# SPDX-License-Identifier: Apache-2.0
"""Tests of the rules section: grouping, ordering, topics and rendering as one."""

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

import pytest

from tests.unit.context.support import applies, left_out
from tests.unit.fakes import ROOT, FakeRepository, MemoryFileSystem
from wio.context.section import RulesSection, rules_section
from wio.models.config import Bundle, Config, Root
from wio.models.frozen import freeze
from wio.models.rule import Rule
from wio.rules.topics import RuleTopics

if TYPE_CHECKING:
    from wio.models.rules import ReasonKind, Selection

_RULES = ROOT / ".agents" / "wio" / "rules"
_FAMILIES = {
    "mattpocock": 'ARC = "Architecture"',
    "process": 'FIX = "Process"',
    "python": 'API = "Python API"',
}
_GOLDEN = """\
Rules for every root:

process: Process (FIX)

process.FIX001 fix-the-cause
Fix the underlying problem.

Rules for root api (services/api):

mattpocock: Architecture (ARC)

mattpocock.ARC001 keep-it-small
Keep each module small.

mattpocock.ARC002 depend-inward
Depend on abstractions.

Rules for roots api, web (services/api, apps/web):

python: Python API (API)

python.API001 adapters-return-typed-results
Adapters return typed results."""


@dataclass
class _Settings:
    """Settings that give the roots `web` and `api` and a separator.

    Attributes:
        separator: The configured separator.
    """

    separator: str = Bundle().separator

    def load(self) -> Config:
        """Give the config, which declares `web` before `api`.

        Returns:
            The config.
        """
        roots = {
            "web": Root(paths=("apps/web",)),
            "api": Root(paths=("services/api",)),
        }
        return Config(roots=freeze(roots), bundle=Bundle(separator=self.separator))


def _topics() -> RuleTopics:
    """Build the topics port over the manifests of the three rulesets.

    Returns:
        The provider.
    """
    files = {
        _RULES / name / "ruleset.toml": f"[families]\n{families}\n"
        for name, families in _FAMILIES.items()
    }
    return RuleTopics(FakeRepository(), MemoryFileSystem(files))


def _rule(qualified: str, name: str, body: str) -> Rule:
    """Build a rule from its qualified code.

    Args:
        qualified: The ruleset and the code.
        name: The rule's name.
        body: The rule's body.

    Returns:
        The rule.
    """
    ruleset, code = qualified.split(".")
    return Rule(ruleset, code, name, None, body, body, 1, PurePosixPath("r.md"))


def _selection() -> Selection:
    """Select rules of three reaches, not in the order the section prints them.

    Returns:
        The selection.
    """
    return {
        _rule(
            "process.FIX001", "fix-the-cause", "Fix the underlying problem."
        ): applies(),
        _rule("mattpocock.ARC002", "depend-inward", "Depend on abstractions."): applies(
            "api"
        ),
        _rule("mattpocock.ARC001", "keep-it-small", "Keep each module small."): applies(
            "api"
        ),
        _rule(
            "python.API001",
            "adapters-return-typed-results",
            "Adapters return typed results.",
        ): applies("api", "web"),
    }


@pytest.mark.parametrize(
    "separator", [Bundle().separator, "\n---\n"], ids=["default", "configured"]
)
def test_a_selection_becomes_one_section(separator: str) -> None:
    """AC-1: the groups, family lines and rules in one text, with their codes."""
    # Given rules of different reach, the manifests with their topics and a
    # config with a separator
    selection = _selection()
    settings = _Settings(separator)

    # When the section is built
    found = rules_section(selection, settings, _topics())

    # Then the text is the golden one, joined by the separator, and the codes
    # are in the order of the text
    assert found == RulesSection(
        _GOLDEN.replace("\n\n", separator),
        (
            "process.FIX001",
            "mattpocock.ARC001",
            "mattpocock.ARC002",
            "python.API001",
        ),
    )


def test_no_included_rule_gives_an_empty_section() -> None:
    """AC-1: every way out leaves neither text nor codes."""
    # Given one rule of each way out
    kinds: tuple[ReasonKind, ...] = (
        "excluded",
        "vetoed",
        "cut-by-roots",
        "not-selected",
    )
    selection: Selection = {
        _rule(f"python.API00{number}", "a-rule", "Body."): left_out(kind)
        for number, kind in enumerate(kinds, start=1)
    }

    # When the section is built
    found = rules_section(selection, _Settings(), _topics())

    # Then it is empty
    assert found == RulesSection("", ())
