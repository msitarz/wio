# SPDX-License-Identifier: Apache-2.0
"""The topics of the families, as the manifests of the rulesets declare them."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wio.io.ports import FileSystem, Repository


@dataclass(frozen=True)
class RuleTopics:
    """Gives the topic of a family from the manifest of its ruleset.

    It satisfies the `Topics` port of `wio.context`. It reads the rulesets that
    the discovery of the rules loads, from the working tree, and writes nothing.
    A fault in the rules is not its to report: the selection of the same run
    refuses it.

    Attributes:
        repository: Finds the repository root.
        files: Lists and reads the rule files and the manifests.
    """

    repository: Repository
    files: FileSystem

    def topic(self, ruleset: str, family: str) -> str:
        """Give the topic of a family of a ruleset.

        Args:
            ruleset: The ruleset's canonical name.
            family: The upper-case letters of the family.

        Returns:
            The topic that the ruleset's manifest declares for the family.

        Raises:
            KeyError: If the discovery loads no ruleset of that name, or its
                manifest declares no such family.
        """
        del ruleset, family
        raise NotImplementedError
