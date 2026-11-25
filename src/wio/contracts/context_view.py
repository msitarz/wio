# SPDX-License-Identifier: Apache-2.0
"""Provide resolved Work contracts and their views for context bundles.

Bundle composition uses the same lookup and rendering rules as the contracts
command, with the resolved contract available separately for rule selection.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.contracts.discovery import discover_works
from wio.contracts.hierarchy import build_hierarchy
from wio.contracts.refusal import refuse_tree
from wio.contracts.resolve import render_resolved, resolve_work
from wio.contracts.showing import find_by_id

if TYPE_CHECKING:
    from wio.contracts import Services
    from wio.models.resolved import ResolvedContract


@dataclass(frozen=True)
class ContractViews:
    """Read the same resolved contract that `wio contracts show` presents.

    Attributes:
        services: The services used to find the Work and read its contract.
    """

    services: Services

    def resolved(self, work_id: str) -> ResolvedContract:
        """Resolve a Work against its ancestors in the current tree.

        Args:
            work_id: The Work's id.

        Returns:
            The Work's own contract and the sections passed on by its ancestors.

        Raises:
            ContractsError: The tree is incomplete, or the id is unknown or
                shared. The refusal uses the wording of `wio contracts show`.
            ConfigurationError: The config cannot be loaded.
            OSError: The Work's own file cannot be read.
            UnicodeDecodeError: The Work's own file is not UTF-8.
        """
        settings = self.services.settings.load().works
        root = self.services.repository.root()
        files = self.services.files
        discovery = discover_works(root, settings, files)
        refuse_tree(discovery, shared=False)
        work = find_by_id(discovery, work_id)
        hierarchy = build_hierarchy(discovery.works, settings.hierarchy)
        return resolve_work(
            work, hierarchy.ancestors[work.path], self.services.catalog, root, files
        )

    def view(self, contract: ResolvedContract) -> str:
        """Write the resolved view without looking up the Work again.

        Args:
            contract: The resolved contract returned by `resolved`.

        Returns:
            The text after the blank line following the separator in
            `wio contracts show`, or the empty string when there is no view.
        """
        return render_resolved(contract)
