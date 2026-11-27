# SPDX-License-Identifier: Apache-2.0
"""Compose the text and recorded identities of a stage's context bundle.

The caller supplies the repository services and checks the request before
composition.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.context import assembly, guidance, heading, identity, section
from wio.errors import WioError
from wio.formats import rule_hash
from wio.models.bundle import CompiledBundle

if TYPE_CHECKING:
    from wio.context.ports import Contracts, RuleSelection, SkillLookup, Topics
    from wio.io.ports import FileSystem, Repository
    from wio.models.config import Config
    from wio.models.rules import Selection
    from wio.models.skill import FoundSkill
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
                skill cannot be found or read.
        """
        resolved = self.contracts.resolved(work_id)
        view = self.contracts.view(resolved)
        selection = self.selection.select(resolved, stage)
        config = self.settings.load()
        stage_settings = config.stages[stage]
        settings = _BundleSettings(config)
        name = stage_settings.skill
        skill = self._find_skill(name)
        stage_text = guidance.stage_guidance(settings, stage, skill)
        rules = section.rules_section(selection, settings, self.topics)
        heading_skill = (
            (name, skill.directory, skill.files_hash)
            if name is not None and skill is not None
            else None
        )
        body_size = 0

        def header_for(size: int, lines: int) -> str:
            """Keep the body's size and build the header from the request.

            Args:
                size: The number of UTF-8 bytes in the body.
                lines: The number of newlines in the body.

            Returns:
                The header for the body assembly measured.
            """
            nonlocal body_size
            body_size = size
            return heading.header(
                resolved.work.id,
                resolved.work.title,
                action,
                stage,
                stage_settings,
                len(rules.codes),
                size,
                lines,
                heading_skill,
            )

        text = assembly.assemble(stage_text, view, rules.text, header_for)
        _, _, payload = text.partition("\n\n")
        return CompiledBundle(
            text,
            identity.bundle_id(payload),
            body_size,
            self._rule_hashes(selection, rules.codes),
        )

    def _find_skill(self, name: str | None) -> FoundSkill | None:
        """Find the configured skill or refuse with its name."""
        if name is None:
            return None
        try:
            skill = self.skills.find_skill(name)
        except OSError as error:
            message = f"The skill `{name}` cannot be read: {error}"
            raise WioError(message) from error
        if skill is None:
            message = f"The skill `{name}` was not found."
            raise WioError(message)
        return skill

    def _rule_hashes(
        self, selection: Selection, codes: tuple[str, ...]
    ) -> dict[str, str]:
        """Hash the stored bytes of each printed rule in print order."""
        if not codes:
            return {}
        paths = {
            rule.qualified: rule.path
            for rule, decision in selection.items()
            if decision.included
        }
        root = self.repository.root()
        hashes: dict[str, str] = {}
        for code in codes:
            path = paths[code]
            try:
                data = self.files.read_bytes(root / path)
            except OSError as error:
                message = f"The rule file {path} cannot be read: {error}"
                raise WioError(message) from error
            hashes[code] = rule_hash(data)
        return hashes


@dataclass(frozen=True)
class _BundleSettings:
    """Share the config read by composition with its part builders."""

    config: Config

    def load(self) -> Config:
        """Supply the settings already read for this bundle.

        Returns:
            The configuration shared by the header and the part builders.
        """
        return self.config
