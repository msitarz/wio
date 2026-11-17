# SPDX-License-Identifier: Apache-2.0
"""The spec of `WorkLookup`, the adapter of the `Contracts` port of `wio.trailers`.

The `wio.trailers` commands find the item ids and the pipeline of the Work that
a record names through the `Contracts` port of its `ports.pyi`. `WorkLookup`
satisfies that port structurally and never imports it, and `wio.cli` wires it in.
It reuses the discovery, the hierarchy, the actions and the items of this
component, which run on any `FileSystem`, so a Work is found the way the other
commands find one.

The stub is the spec until the wiring stage of the Work that builds the lookup
writes the class into `wio.contracts.lookup` and deletes this stub, so the spec
and the code never coexist.
"""

from collections.abc import Sequence

from wio.contracts.ports import TemplateCatalog
from wio.io.ports import FileSystem, Repository
from wio.ports import Settings

class WorkLookup:
    """Finds the items and the pipelines of a Work by its id.

    It is built once for the working tree and once for the index, each with the
    view of `HEAD` after it, so a Work that the commit being made deletes is
    still found. The views are tried in order and the first that has the Work
    answers, so a Work that differs between two views answers as the first does.
    The config and the templates are always those of the working tree. It reads
    and writes nothing else, and every call reads afresh, so a change between two
    calls is seen.

    A Work is found when exactly one Work of a view has the id: an id that two
    Works share is not found in that view, because discovery cannot say which is
    meant, and the contracts component reports it. A file that cannot be read or
    decoded, a malformed contract and a missing template are the contracts
    component's to report, and the lookup finds what it can.
    """

    def __init__(
        self,
        settings: Settings,
        repository: Repository,
        catalog: TemplateCatalog,
        templates: FileSystem,
        views: Sequence[FileSystem],
    ) -> None:
        """Keep what the lookup reads through.

        Args:
            settings: Loads the config, for the Works directory, the hierarchy,
                the default actions and the stage presets.
            repository: Finds the repository root.
            catalog: Finds a Work's template.
            templates: The file system of the working tree, which the template's
                actions and sections are read from.
            views: The file systems that a Work is looked up in, in order: the
                working tree or the index, then `HEAD`.
        """
        ...

    def items(self, work_id: str) -> frozenset[str] | None:
        """Find the item ids of a Work.

        The ids are those that the `pattern` directives of the Work's template
        give the sections of the Work's own contract, found with
        `wio.formats.find_items`, whatever the sections mean; an inherited
        section's ids are not included. A Work without a template, or whose
        template cannot be read, has no ids.

        Args:
            work_id: The Work's id.

        Returns:
            The Work's item ids, such as `AC-1`, empty for a Work that has none,
            or `None` when no view has such a Work.

        Raises:
            ConfigurationError: If the config cannot be loaded.
        """
        ...

    def pipeline(self, work_id: str, action: str) -> Sequence[str] | None:
        """Find the stages of a Work's action.

        The action is resolved as `wio contracts show` resolves it, the Work's
        own `[actions]` over its template's, or over the config defaults for a
        Work with no template, and a stage preset is expanded from the config's
        stage presets.

        Args:
            work_id: The Work's id.
            action: The name of an action in the config.

        Returns:
            The names of the stages in the order of the pipeline, or `None` when
            no view has such a Work, the Work has no such action or removed it,
            or the action names a stage preset that the config does not declare.

        Raises:
            ConfigurationError: If the config cannot be loaded.
        """
        ...
