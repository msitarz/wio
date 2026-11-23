# SPDX-License-Identifier: Apache-2.0
"""The selector that gives `wio context` and `wio trailers` their rules."""

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from wio.errors import WioError
from wio.formats import rule_hash
from wio.models.rules import Reason
from wio.rules.applicability import select
from wio.rules.discovery import discover, refuse_on_errors
from wio.rules.inputs import ruleset_map
from wio.rules.roots import stage_roots

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from wio.io.ports import FileSystem, Repository
    from wio.models.resolved import ResolvedContract
    from wio.models.rule import Rule
    from wio.models.rules import Selection
    from wio.ports import Settings
    from wio.rules.ports import WorkRoots


@dataclass(frozen=True)
class RuleSelector:
    """What a Work at a stage selects, for the two consumers that need it.

    It satisfies the `RuleSelection` port of `wio.context` with `select` and the
    `StageRules` port of `wio.trailers` with `selected`, so `wio.cli` wires one
    instance to both. The config, the rule files and the roots of the Work are
    read from the working tree each time, so a call sees the files as they are on
    disk.

    Attributes:
        settings: Loads the config.
        repository: Finds the repository root.
        files: Reads the rule files and the manifests, and the bytes of the files
            that `selected` hashes.
        work_roots: Gives the roots of a Work's contract.
    """

    settings: Settings
    repository: Repository
    files: FileSystem
    work_roots: WorkRoots

    def selection(self, work_id: str, stage: str) -> Selection:
        """Select the rules of a Work at a stage.

        It discovers the rulesets and refuses when the discovery holds an error,
        so no consumer works from a partial answer. It then takes the roots that
        the stage selects for the Work and returns the selection of `select`. A
        Work with no roots, for a stage that selects the Work's roots, gets every
        rule out with the reason `not-selected`, and raises nothing, so a gate
        record of such a Work needs no rule. It reads only the files that the
        discovery reads.

        Args:
            work_id: The Work's id.
            stage: The name of a stage in the config.

        Returns:
            One decision for every rule, in the order of C-2 of `wio rules`.

        Raises:
            DiagnosticsError: The discovery reported an error; it carries the
                diagnostics.
            KeyError: The stage, the Work or a root of either is not known.
        """
        config = self.settings.load()
        discovery = discover(self.repository.root(), self.files)
        refuse_on_errors(discovery)
        rulesets = ruleset_map(discovery)
        try:
            roots = stage_roots(config, stage, work_id, self.work_roots)
        except ValueError:
            return _all_out(select((), None, config, rulesets))
        return select(roots, stage, config, rulesets)

    def select(self, contract: ResolvedContract, stage: str) -> Selection:
        """Give `selection` for the Work of a resolved contract.

        This is the method of the `RuleSelection` port, so a Work without roots
        raises no `ValueError`, and what `selection` raises is raised here.

        Args:
            contract: The Work's resolved contract.
            stage: The name of a stage in the config.

        Returns:
            What `selection` returns for the Work's id.
        """
        return self.selection(contract.work.id, stage)

    def selected(self, work_id: str, action: str, stage: str) -> Mapping[str, str]:
        """Give the rules that a stage selects for a Work, with their hashes.

        This is the method of the `StageRules` port. The action does not change
        the rules a stage selects, so it is not read. It reads the bytes of the
        files of the rules that the selection includes and of no other, through
        the `FileSystem` port.

        Args:
            work_id: The Work's id.
            action: The action, which is ignored.
            stage: The name of a stage in the config.

        Returns:
            The qualified code of each included rule, such as `demo.ARC001`,
            with `rule_hash` of the bytes of its file; empty when none is
            included.

        Raises:
            DiagnosticsError: The discovery reported an error.
            WioError: The stage or the Work is not known, or a rule file that
                the discovery read cannot be read as bytes, naming the cause, so
                that `wio trailers` exits 2 and not 70.
        """
        del action
        try:
            chosen = self.selection(work_id, stage)
        except KeyError as error:
            raise WioError(_unknown(error.args[0], stage)) from error
        root = self.repository.root()
        return {
            f"{rule.ruleset}.{rule.code}": rule_hash(self._bytes_of(root, rule))
            for rule, decision in chosen.items()
            if decision.included
        }

    def _bytes_of(self, root: Path, rule: Rule) -> bytes:
        """Read the bytes of a rule's file.

        Args:
            root: The root of the repository.
            rule: The rule, whose path is relative to the root.

        Returns:
            The bytes as stored.

        Raises:
            WioError: The file cannot be read, naming its path.
        """
        try:
            return self.files.read_bytes(root / rule.path)
        except OSError as error:
            message = f"The rule file {rule.path} cannot be read: {error}"
            raise WioError(message) from error


def _all_out(selection: Selection) -> Selection:
    """Turn every decision of a selection into one that leaves the rule out.

    Args:
        selection: The selection whose rules and order are kept.

    Returns:
        The same rules, each out as `not-selected` with no roots and no effect.
    """
    out = Reason("not-selected", None)
    return {
        rule: replace(decision, included=False, roots=(), effects=(), reason=out)
        for rule, decision in selection.items()
    }


def _unknown(name: object, stage: str) -> str:
    """Say which name was not known.

    Args:
        name: The name that the `KeyError` carries.
        stage: The stage that was asked for.

    Returns:
        A sentence that names the stage, or the Work or root, that is unknown.
    """
    if name == stage:
        return f"The config has no stage `{name}`."
    return f"No Work or root `{name}` is known."
