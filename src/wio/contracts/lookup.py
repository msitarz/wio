# SPDX-License-Identifier: Apache-2.0
"""The lookup of a Work by its id, for the commands that check a record.

The `wio.trailers` commands find the item ids and the pipeline of the Work that a
record names through the `Contracts` port of its `ports.pyi`. `WorkLookup`
satisfies that port structurally and never imports it, and `wio.cli` wires it in.
It reuses the discovery, the hierarchy, the actions and the items of this
component, which run on any `FileSystem`, so a Work is found the way the other
commands find one.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from wio.contracts.body import BodyChecker
from wio.contracts.discovery import WorkDiscovery, discover_works, find_work
from wio.contracts.hierarchy import build_hierarchy
from wio.contracts.showing import shown_actions
from wio.formats import read_metadata_block
from wio.formats.errors import MetadataBlockError
from wio.models.works import Work

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from wio.contracts.ports import TemplateCatalog
    from wio.io.ports import FileSystem, Repository
    from wio.models.config import Config
    from wio.models.config import Works as WorksSettings
    from wio.ports import Settings


@dataclass(frozen=True)
class _Found:
    """A Work and the view that has it.

    Attributes:
        work: The Work.
        files: The view of the working tree, the index or `HEAD` that the Work
            was found in, which its own file is read through.
    """

    work: Work
    files: FileSystem


@dataclass(frozen=True)
class _Reading:
    """What a Work's template is read through.

    Attributes:
        catalog: Finds the Work's template.
        templates: The file system of the working tree, which the template is
            read from.
        root: The repository root, which the template's path is relative to.
    """

    catalog: TemplateCatalog
    templates: FileSystem
    root: Path


@dataclass(frozen=True)
class WorkLookup:
    """Finds the items and the pipelines of a Work by its id.

    It is built once for the working tree and once for the index, each with the
    view of `HEAD` after it, so a Work that the commit being made deletes is
    still found. The views are tried in order and the first that has the id
    answers, so a Work that differs between two views answers as the first does.
    The config and the templates are always those of the working tree. It reads
    and writes nothing else. A view reads its listing of files once, so a change
    made after the first call is seen by a new lookup and not by the same one.

    A Work is found when exactly one Work of a view has the id. An id that two
    Works of a view share makes the answer absent, and the next view is not
    asked, because discovery cannot say which Work is meant and a record must not
    be checked against an older copy; the contracts component reports the shared
    id. A file that cannot be read or decoded, a malformed contract and a missing
    template are the contracts component's to report, and the lookup finds what
    it can.

    Attributes:
        settings: Loads the config, for the Works directory, the hierarchy, the
            default actions and the stage presets.
        repository: Finds the repository root.
        catalog: Finds a Work's template.
        templates: The file system of the working tree, which the template's
            actions and sections are read from.
        views: The file systems that a Work is looked up in, in order: the
            working tree or the index, then `HEAD`.
    """

    settings: Settings
    repository: Repository
    catalog: TemplateCatalog
    templates: FileSystem
    views: Sequence[FileSystem]
    discover: Callable[[Path, WorksSettings, FileSystem], WorkDiscovery] = (
        discover_works
    )
    _discoveries: dict[int, WorkDiscovery] = field(
        default_factory=dict, init=False, repr=False, compare=False
    )

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
        found = self._find(work_id)
        if found is None:
            return None
        return _own_items(found, self._reading())

    def pipeline(self, work_id: str, action: str) -> Sequence[str] | None:
        """Find the stages of a Work's action.

        The action is resolved as `wio contracts show` resolves it, the Work's
        own `[actions]` over its template's, or over the config defaults for a
        Work with no template, and a stage preset is expanded from the config's
        stage presets.

        Args:
            work_id: The Work's id.
            action: The name of an action, one of the config or one that the Work
                names itself.

        Returns:
            The names of the stages in the order of the pipeline, or `None` when
            no view has such a Work, the Work has no such action or removed it,
            or the action names a stage preset that the config does not declare.

        Raises:
            ConfigurationError: If the config cannot be loaded.
        """
        found = self._find(work_id)
        if found is None:
            return None
        return _stages(found.work, action, self.settings.load(), self._reading())

    def roots_of(self, work_id: str) -> tuple[str, ...] | None:
        """Find the roots of a Work, with `@descendants` expanded.

        The roots come from the `Hierarchy` of the view that has the Work, the
        one that `wio contracts show` reads, so a name is each once and sorted.
        It writes nothing.

        Args:
            work_id: The Work's id.

        Returns:
            The roots, empty for a Work that has none or a leaf that lists
            `@descendants`, or `None` when no view has such a Work.

        Raises:
            ConfigurationError: If the config cannot be loaded.
        """
        found = self._find(work_id)
        if found is None:
            return None
        config = self.settings.load()
        discovery = self._discover(found.files)
        hierarchy = build_hierarchy(discovery.works, config.works.hierarchy)
        return hierarchy.roots.get(found.work.path, ())

    def _discover(self, view: FileSystem) -> WorkDiscovery:
        """Discover Works in a view, caching the result for this lookup.

        Args:
            view: The file system view to walk.

        Returns:
            The Work discovery for `view`.
        """
        key = id(view)
        cached = self._discoveries.get(key)
        if cached is not None:
            return cached
        discovery = self.discover(
            self.repository.root(), self.settings.load().works, view
        )
        self._discoveries[key] = discovery
        return discovery

    def _reading(self) -> _Reading:
        """Gather what a Work's template is read through.

        Returns:
            The catalog, the working tree and the repository root.
        """
        return _Reading(self.catalog, self.templates, self.repository.root())

    def _find(self, work_id: str) -> _Found | None:
        """Look a Work up in each view in turn.

        Args:
            work_id: The Work's id.

        Returns:
            The Work and the view that has it, or `None` when the first view
            that knows the id has two Works with it, or when no view has it.

        Raises:
            ConfigurationError: If the config cannot be loaded.
        """
        for view in self.views:
            match find_work(self._discover(view), work_id):
                case Work() as work:
                    return _Found(work, view)
                case None:
                    continue
                case _:
                    return None
        return None


def _own_items(found: _Found, reading: _Reading) -> frozenset[str]:
    """Find the ids that a Work's own sections carry.

    Args:
        found: The Work and the view its file is read through.
        reading: What the Work's template is read through.

    Returns:
        The ids that the template's `pattern` directives give the sections of the
        Work's own contract, empty for a Work with no template, a template that
        cannot be used, or a file that cannot be read again.
    """
    work = found.work
    try:
        block = read_metadata_block(found.files.read_text(reading.root / work.path))
    except UnicodeDecodeError, OSError, MetadataBlockError:
        return frozenset()
    template = None if work.template is None else reading.catalog.find(work.template)
    if block is None:
        return frozenset()
    return BodyChecker(reading.root, reading.templates).items(block, template)


def _stages(
    work: Work, action: str, config: Config, reading: _Reading
) -> Sequence[str] | None:
    """Expand the pipeline of one action of a Work.

    Args:
        work: The Work.
        action: The name of the action.
        config: The config, for the default actions and the stage presets.
        reading: What the Work's template and its actions are read through.

    Returns:
        The stages in order, or `None` when the Work has no such action, removed
        it, or names a stage preset that the config does not declare.
    """
    actions = shown_actions(
        work, config, reading.catalog, reading.root, reading.templates
    )
    named = next((a for a in actions if a.name == action), None)
    if named is None or named.removed or not named.stages:
        return None
    return list(named.stages)
