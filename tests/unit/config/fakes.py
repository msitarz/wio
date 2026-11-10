# SPDX-License-Identifier: Apache-2.0
"""Fakes of the ports the loader reads through, for the tests of `wio.config`."""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from tests.unit.fakes import MemoryFileSystem
from wio.config import CHECKS, load_config
from wio.models.config import Config, Gates, Skills, Templates, Works
from wio.models.frozen import freeze

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from wio.config import Check, Loaded
    from wio.models.config import Action, Root, RulePreset, Ruleset, Stage
    from wio.models.diagnostics import Diagnostic

ROOT = Path("/repo")
CONFIG = ROOT / ".agents" / "wio" / "config.toml"


@dataclass
class FakeRepository:
    """A `Repository` whose root is fixed, or that is not inside a repository."""

    top: Path | None = ROOT
    message: str = "not inside a git repository: /elsewhere"

    def root(self) -> Path:
        """Find the root.

        Returns:
            The fixed root.

        Raises:
            RuntimeError: The fake is outside any repository.
        """
        if self.top is None:
            raise RuntimeError(self.message)
        return self.top

    def identity(self) -> Path:
        """Find the identity, which is the root's own `.git`.

        Returns:
            The path of the `.git` directory.
        """
        return self.root() / ".git"

    def show_index(self, path: Path) -> str | None:  # noqa: ARG002
        """Read a staged file; nothing is staged.

        Args:
            path: The file.

        Returns:
            None.
        """
        return None

    def is_dirty(self) -> bool:
        """Tell whether the tree is dirty; it never is.

        Returns:
            False.
        """
        return False


def load_text(text: str, checks: Sequence[Check] = ()) -> Loaded:
    """Run the loader on a config text kept in memory.

    Args:
        text: The content of `.agents/wio/config.toml`.
        checks: The checks to run after the shape.

    Returns:
        What the loader found.
    """
    return load_config(
        FakeRepository(), MemoryFileSystem({CONFIG: text}), checks=checks
    )


def run_order(ours: Sequence[Check]) -> list[Check]:
    """List some checks in the order the check run runs them.

    Args:
        ours: The checks of one Work.

    Returns:
        Those of `ours` that `wio.config.CHECKS` holds, in the order it holds
        them, so a test says that its Work's checks run in a stated order whatever
        the other Works append.
    """
    return [check for check in CHECKS if check in ours]


def make_config(
    *,
    stages: Mapping[str, Stage] | None = None,
    stage_presets: Mapping[str, tuple[str, ...]] | None = None,
    actions: Mapping[str, Action] | None = None,
    roots: Mapping[str, Root] | None = None,
    works: Works | None = None,
    gates: Gates | None = None,
    skills: Skills | None = None,
    templates: Templates | None = None,
    rule_presets: Mapping[str, RulePreset] | None = None,
    rulesets: Mapping[str, Ruleset] | None = None,
    always_include: Sequence[str] = (),
    always_exclude: Sequence[str] = (),
) -> Config:
    """Build a `Config` from the plain mappings a test writes.

    A test names only what it exercises, and everything else is valid, so one
    scenario trips one check and its result is that check's.

    Args:
        stages: The stages by name.
        stage_presets: The stages of each stage preset.
        actions: The actions by name.
        roots: The roots by name.
        works: The `works` table.
        gates: The `gates` table.
        skills: The `skills` table.
        templates: The `templates` table.
        rule_presets: The rule presets of the config by name.
        rulesets: The `[rulesets]` tables by name.
        always_include: The config's `rules_always_include`.
        always_exclude: The config's `rules_always_exclude`.

    Returns:
        The config, with the defaults for what is not given.
    """
    return Config(
        stages=freeze(stages or {}),
        stage_presets=freeze(stage_presets or {}),
        actions=freeze(actions or {}),
        roots=freeze(roots or {}),
        works=works or Works(),
        gates=gates or Gates(),
        skills=skills or Skills(),
        templates=templates or Templates(),
        rule_presets=freeze(rule_presets or {}),
        rulesets=freeze(rulesets or {}),
        rules_always_include=tuple(always_include),
        rules_always_exclude=tuple(always_exclude),
    )


def diagnostic_lines(diagnostics: Iterable[Diagnostic]) -> list[str]:
    """Write diagnostics as `severity: where: message`, in the order returned.

    Args:
        diagnostics: What a check returned.

    Returns:
        One line for each diagnostic.
    """
    return [f"{d.severity}: {d.where}: {d.message}" for d in diagnostics]
