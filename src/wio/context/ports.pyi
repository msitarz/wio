# SPDX-License-Identifier: Apache-2.0
"""The ports that `wio.context` consumes besides the shared ones in `wio.ports`.

Provisional: the architecture review may rename them. The component that
satisfies each is wired in by `wio.cli`; `wio.context` never imports it.
"""

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
            KeyError: If no Work has that id.
        """
        ...

class RuleSelection(Protocol):
    """The rules that apply to a Work at a stage."""

    def select(self, contract: ResolvedContract, stage: str) -> Selection:
        """Select the rules for a stage of a Work.

        A Work with no roots, for a stage that selects the Work's roots, gets a
        selection in which no rule is included.

        Args:
            contract: The Work's resolved contract, which gives its roots.
            stage: The name of a stage in the config.

        Returns:
            Every rule considered, in a fixed order so the same inputs give the
            same bytes, each with its decision: the roots of an included rule,
            or why a rule was left out.

        Raises:
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
        `.claude/skills`, never in the user's home, and
        finds a skill exactly when `wio config check` accepts it. It reads the
        settings first, so a config that they refuse gets no lookup.

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
