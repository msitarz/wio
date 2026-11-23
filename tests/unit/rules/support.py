# SPDX-License-Identifier: Apache-2.0
"""Helpers that the tests of the rule readers share."""

from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from wio.models.config import RulePreset
from wio.models.frozen import freeze
from wio.models.rule import LoadedRuleset, Manifest, Rule

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

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
