# SPDX-License-Identifier: Apache-2.0
"""Helpers that the tests of the rule readers share."""

import io
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from wio.models.config import Config, RulePreset
from wio.models.frozen import freeze
from wio.models.resolved import ResolvedContract
from wio.models.rule import LoadedRuleset, Manifest, Rule
from wio.models.works import Work

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from tests.unit.fakes import FakeStdio
    from wio.models.diagnostics import Diagnostic


def kinds(diagnostics: Iterable[Diagnostic]) -> list[tuple[str, str]]:
    """List the severity and the place of each diagnostic.

    Args:
        diagnostics: What a reader or the discovery reported.

    Returns:
        A pair for each diagnostic, in the order given.
    """
    return [(d.severity, d.where) for d in diagnostics]


def make_rule(ruleset: str, code: str) -> Rule:
    """Build a rule of a ruleset.

    Args:
        ruleset: The ruleset's name.
        code: The rule's code, which is also the stem of its name.

    Returns:
        The rule.
    """
    name = code.lower()
    return Rule(
        ruleset=ruleset,
        code=code,
        name=name,
        description=None,
        summary="Summary.",
        body="Summary.",
        body_line=5,
        path=PurePosixPath(f".agents/wio/rules/{ruleset}/{code}-{name}.md"),
    )


def make_ruleset(
    name: str,
    families: Sequence[str],
    codes: Sequence[str],
    presets: Mapping[str, tuple[Sequence[str], Sequence[str]]] | None = None,
) -> LoadedRuleset:
    """Build a ruleset with rules in the order of family, number and code.

    Args:
        name: The ruleset's name.
        families: The families its manifest declares.
        codes: The codes of its rules.
        presets: Its rule presets by name, with their includes and excludes.

    Returns:
        The ruleset.
    """
    rules = sorted(
        (make_rule(name, code) for code in codes),
        key=lambda r: (r.family, r.number, r.code),
    )
    manifest = Manifest(
        families=freeze(dict.fromkeys(families, "Topic")),
        rule_presets=freeze(
            {n: RulePreset(tuple(i), tuple(e)) for n, (i, e) in (presets or {}).items()}
        ),
    )
    path = PurePosixPath(f".agents/wio/rules/{name}")
    return LoadedRuleset(name, path, manifest, tuple(rules))


@dataclass
class Settings:
    """Settings that give one config."""

    config: Config

    def load(self) -> Config:
        """Give the config.

        Returns:
            The config.
        """
        return self.config


@dataclass
class Roots:
    """The roots of the Works, by id."""

    roots: Mapping[str, tuple[str, ...]]

    def roots_of(self, work_id: str) -> tuple[str, ...] | None:
        """Find the roots of a Work.

        Args:
            work_id: The Work's id.

        Returns:
            Its roots, or `None` for an id that no Work has.
        """
        return self.roots.get(work_id)


def said(streams: FakeStdio) -> str:
    """Read what a run wrote to standard output.

    Args:
        streams: The streams of the run.

    Returns:
        The text.
    """
    assert isinstance(streams.stdout, io.StringIO)
    return streams.stdout.getvalue()


def contract(work_id: str) -> ResolvedContract:
    """Build the resolved contract that a bundle is made from.

    Args:
        work_id: The Work's id.

    Returns:
        A contract with no text.
    """
    work = Work(work_id, None, Path("w.md"), None, (), (), freeze({}))
    return ResolvedContract(work, "", ())
