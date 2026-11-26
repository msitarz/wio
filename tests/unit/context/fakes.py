# SPDX-License-Identifier: Apache-2.0
"""Port fakes for composing a bundle without a repository on disk.

Each fake supplies the configured result directly to the composition.
"""

from dataclasses import dataclass, field

from tests.fakes import value_or_raise
lazy from wio.errors import DiagnosticsError
lazy from wio.models.config import Config
lazy from wio.models.resolved import ResolvedContract
lazy from wio.models.rules import Selection
lazy from wio.models.skill import FoundSkill


@dataclass
class ContractStub:
    """Supply a resolved contract and its rendered view.

    Attributes:
        contract: The resolved contract to return.
    """

    contract: ResolvedContract

    def resolved(self, work_id: str) -> ResolvedContract:
        """Give the configured contract for the specified Work.

        Args:
            work_id: The id expected for the Work.

        Returns:
            The configured resolved contract.
        """
        assert work_id == self.contract.work.id
        return self.contract

    def view(self, contract: ResolvedContract) -> str:
        """Give the configured contract's rendered view.

        Args:
            contract: The already resolved contract.

        Returns:
            The configured view.
        """
        assert contract is self.contract
        return self.contract.own


@dataclass
class SelectionFake:
    """Give a selection or discovery failure and record the requests.

    Attributes:
        result: The configured selection or discovery failure.
        calls: The resolved contract and stage of each request.
    """

    result: Selection | DiagnosticsError
    calls: list[tuple[ResolvedContract, str]] = field(default_factory=list)

    def select(self, contract: ResolvedContract, stage: str) -> Selection:
        """Give the prepared selection for a stage of a resolved Work.

        Args:
            contract: The resolved contract.
            stage: The stage being composed.

        Returns:
            The configured selection.

        Raises:
            DiagnosticsError: The configured rule discovery failure.
        """
        self.calls.append((contract, stage))
        return value_or_raise(self.result)


@dataclass
class SkillsFake:
    """Give the prepared skill and record the names requested.

    Attributes:
        result: The prepared lookup result.
        calls: The configured names passed to the lookup.
    """

    result: FoundSkill | None
    calls: list[str] = field(default_factory=list)

    def find_skill(self, name: str) -> FoundSkill | None:
        """Find the prepared skill for a requested name.

        Args:
            name: The configured skill name.

        Returns:
            The prepared result, including None for a missing skill.
        """
        self.calls.append(name)
        return self.result


@dataclass(frozen=True)
class SettingsStub:
    """Supply fixed settings for one composition.

    Attributes:
        config: The config returned by every load.
    """

    config: Config

    def load(self) -> Config:
        """Give the prepared settings.

        Returns:
            The prepared config.
        """
        return self.config


class TopicsStub:
    """Supply fixed topics for the rule families used by the scenarios.

    The topics make each family recognizable in the rendered rules section.
    """

    def topic(self, ruleset: str, family: str) -> str:
        """Give the topic of one prepared family.

        Args:
            ruleset: The rule's ruleset.
            family: The rule's family.

        Returns:
            The topic associated with the pair.
        """
        return {("process", "FIX"): "Process", ("python", "API"): "Python API"}[
            ruleset, family
        ]
