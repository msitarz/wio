# SPDX-License-Identifier: Apache-2.0
"""The ports that `wio.context` consumes besides the shared ones in `wio.ports`.

Provisional: the architecture review may rename them. The component that
satisfies each is wired in by `wio.cli`; `wio.context` never imports it.
"""

from collections.abc import Sequence
from typing import Protocol

from wio.models.bundle import CompiledBundle
from wio.models.resolved import ResolvedContract
from wio.models.rules import Selection
from wio.models.skill import FoundSkill

class Contracts(Protocol):
    """The Work contracts that a bundle shows."""

    def resolved(self, work_id: str) -> ResolvedContract:
        """Read a Work's contract with its ancestors' inherited sections.

        Args:
            work_id: The Work's id.

        Returns:
            The resolved contract.

        Raises:
            ContractsError: The tree is incomplete, or the id is unknown or
                shared.
            ConfigurationError: The config cannot be loaded.
            OSError: The Work's own file cannot be read.
            UnicodeDecodeError: The Work's own file is not UTF-8.
        """
        ...

    def view(self, contract: ResolvedContract) -> str:
        """Write the view of an already resolved contract.

        Args:
            contract: The contract returned by `resolved`.

        Returns:
            The resolved view as `wio contracts show` prints it, empty when
            the Work has no body and no inherited sections.
        """
        ...

class RuleSelection(Protocol):
    """The rules that apply to a Work at a stage."""

    def select(self, contract: ResolvedContract, stage: str) -> Selection:
        """Select the rules for a stage of a Work.

        A Work with no roots, for a stage that selects the Work's roots, gets a
        selection in which no rule is included.

        Args:
            contract: The resolved contract, which gives the Work's id.
            stage: The name of a stage in the config.

        Returns:
            Every rule considered, in a fixed order so the same inputs give the
            same bytes, each with its decision: the roots of an included rule,
            or why a rule was left out.

        Raises:
            DiagnosticsError: Rule discovery reports a fault.
            KeyError: If the stage or the Work is not known.
        """
        ...

class Composer(Protocol):
    """What composes the bundle of a Work at a stage of an action."""

    def compose(self, work_id: str, action: str, stage: str) -> CompiledBundle:
        """Compose the bundle.

        Args:
            work_id: The Work's id.
            action: The name of the action.
            stage: The name of the stage.

        Returns:
            The finished bundle.

        Raises:
            WioError: For what the user must fix before there is a bundle.
        """
        ...

class Topics(Protocol):
    """The topics that the rulesets declare for their families."""

    def topic(self, ruleset: str, family: str) -> str:
        """Give the topic of a family of a ruleset.

        Args:
            ruleset: The ruleset's canonical name.
            family: The upper-case letters of the family.

        Returns:
            The topic that the ruleset's manifest declares for the family.

        Raises:
            KeyError: If no ruleset has that name, or its manifest declares no
                such family, which no rule of a selection leads to.
        """
        ...

class SkillLookup(Protocol):
    """The skills of the repository that a stage can name."""

    def find_skill(self, name: str) -> FoundSkill | None:
        """Find a skill and hash its files.

        It looks in `[skills] paths`, in their order and with the paths that
        have a fault left out, and then in `.agents/skills` and
        `.claude/skills`, never in the user's home. In a config that loads, it
        finds the skill of every stage that names one. It reads the settings
        first, so a config that they refuse gets their error and no answer.

        Args:
            name: The skill's name, as a stage writes it.

        Returns:
            The directory `<dir>/<name>` of the first `<dir>` searched in which
            it holds a `SKILL.md`, with the hash of the files of
            `<dir>/<name>`, or `None` when there is none or the name is empty,
            `.`, `..` or holds `/`.

        Raises:
            ConfigurationError: If the settings cannot be loaded.
            OSError: If a file of the skill cannot be listed or read.
        """
        ...

class WorkRoots(Protocol):
    """The roots of a Work, with descendants expanded."""

    def roots_of(self, work_id: str) -> tuple[str, ...] | None:
        """Find the Work's roots in the working tree.

        Args:
            work_id: The id of the Work.

        Returns:
            The sorted, distinct roots, or None if the Work is unknown.

        Raises:
            ConfigurationError: The settings cannot be loaded.
        """
        ...

class Pipelines(Protocol):
    """The effective pipelines of a Work."""

    def pipeline(self, work_id: str, action: str) -> Sequence[str] | None:
        """Find the expanded stages of a Work's action.

        The Work's actions override its template, or the config defaults for a
        Work without a template. A stage preset is expanded from the config.

        Args:
            work_id: The Work's id.
            action: The requested action.

        Returns:
            The stages in order, or None if the Work or action is absent, the
            action was removed, or its preset is undeclared.

        Raises:
            ConfigurationError: The settings cannot be loaded.
        """
        ...
