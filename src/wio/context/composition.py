# SPDX-License-Identifier: Apache-2.0
"""Compose the text and recorded identities of a stage's context bundle.

The caller supplies the repository services and checks the request before
composition.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wio.context.ports import Contracts, RuleSelection, SkillLookup, Topics
    from wio.io.ports import FileSystem, Repository
    from wio.models.bundle import CompiledBundle
    from wio.ports import Settings


@dataclass(frozen=True)
class Composition:
    """Build a complete bundle from one resolved contract and one selection.

    Attributes:
        contracts: Resolves and renders the Work's contract.
        selection: Selects the rules of the Work and stage.
        topics: Gives the topics of selected rule families.
        skills: Finds a configured skill and hashes its files.
        settings: Gives the config for the requested stage and rules section.
        repository: Finds the root of the repository.
        files: Reads the bytes of printed rules under that root.
    """

    contracts: Contracts
    selection: RuleSelection
    topics: Topics
    skills: SkillLookup
    settings: Settings
    repository: Repository
    files: FileSystem

    def compose(self, work_id: str, action: str, stage: str) -> CompiledBundle:
        """Build the bundle and the identities needed to record it.

        The text, rule count and ordered hashes use the same rule selection.
        A stage with a skill looks it up once for the guidance and header.

        Args:
            work_id: The id of the Work.
            action: The action named in the request.
            stage: The stage named in the request.

        Returns:
            The assembled text, its id, the body's UTF-8 byte count and the
            hashes of the printed rule files, in print order.

        Raises:
            DiagnosticsError: Rule discovery reports a fault.
            WioError: A printed rule file cannot be read or the configured
                skill cannot be found.
        """
        raise NotImplementedError
