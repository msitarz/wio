# SPDX-License-Identifier: Apache-2.0
"""What `wio contracts show` finds out about a Work before it prints it."""

from dataclasses import dataclass
from os.path import normpath
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal

from wio.contracts.actions import resolve_actions, template_actions
from wio.contracts.discovery import discover_works, explain_not_a_work, find_work
from wio.contracts.errors import ContractsError
from wio.contracts.hierarchy import build_hierarchy
from wio.contracts.refusal import refuse, refuse_tree
from wio.contracts.resolve import render_resolved, resolve_work
from wio.contracts.show_render import render_show
from wio.models.diagnostics import Diagnostic
lazy from wio.formats import closest_key

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Mapping, Sequence

    from wio.contracts import Services
    from wio.contracts.actions import ActionSource, Pipeline, ResolvedAction
    from wio.contracts.discovery import WorkDiscovery
    from wio.contracts.hierarchy import Hierarchy
    from wio.contracts.ports import TemplateCatalog
    from wio.io.ports import FileSystem, Stdio
    from wio.models.config import Config
    from wio.models.config import Works as WorksSettings
    from wio.models.works import Work

type ShownSource = Literal["template", "contract", "defaults"]
"""Where an action comes from: the template, the Work's own `[actions]` or the
config's `[works.defaults.actions]`."""
_SOURCES: Final[Mapping[ActionSource, ShownSource]] = {
    "work": "contract",
    "template": "template",
    "defaults": "defaults",
}
"""The source of a resolved action as a contract names it."""


@dataclass(frozen=True)
class Related:
    """A Work named by another, as `<id>  <title>` shows it.

    Attributes:
        id: The id as written.
        title: The title, or `None` for a Work with none or an id no Work has.
        found: Whether a Work has the id.
    """

    id: str
    title: str | None
    found: bool


@dataclass(frozen=True)
class ShownAction:
    """One action of a Work as `show` prints it.

    Attributes:
        name: The action's name.
        source: Where the action comes from. A removed action has `contract`.
        on_demand: Whether the config marks the action on demand.
        preset: The stage preset the action names, or `None` for an action given
            as a list of stages and for a removed action.
        stages: The stages of the preset when the config declares it, or the
            listed stages; empty for a removed action and for a preset the
            config does not declare.
        removed: Whether the Work's own `[actions]` empty an inherited action.
    """

    name: str
    source: ShownSource
    on_demand: bool
    preset: str | None
    stages: tuple[str, ...]
    removed: bool


@dataclass(frozen=True)
class ShownWork:
    """Everything `show` prints of a Work, found and not yet laid out.

    Attributes:
        work: The Work.
        parent: Its parent, or `None` for a top Work and under `flat`.
        resolved_roots: Its roots with `@descendants` resolved.
        depends_on: What it lists in `depends_on`, in the order listed.
        dependents: The Works that list it, sorted by path.
        actions: Its resolved actions in the order that `shown_actions` gives.
        view: Its resolved view as `render_resolved` writes it.
    """

    work: Work
    parent: Related | None
    resolved_roots: tuple[str, ...]
    depends_on: tuple[Related, ...]
    dependents: tuple[Related, ...]
    actions: tuple[ShownAction, ...]
    view: str


def run_show(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Run `wio contracts show`.

    It reads through `services` and writes only to `stdio.stdout`. The tree is
    judged first: an error of finding the Works that leaves it incomplete refuses
    the command for an id and for a path alike, while an error of the metadata or
    the graph does not. Then the argument is looked up by `find_target`.

    Args:
        services: What the command reads the project through.
        args: What the parser read: `work`, the id or the path, and `json`,
            whether to write the object.
        stdio: Where the output goes.

    Returns:
        0 after the Work is written.

    Raises:
        ContractsError: The tree is incomplete, or the argument names no Work,
            as `find_target` says. The command line writes it to standard error
            and exits 2.
        ConfigurationError: The config has an error.
        OSError: The Work's own file cannot be read, as `resolve_work` raises it.
        UnicodeDecodeError: The Work's own file is not UTF-8.
    """
    config = services.settings.load()
    root = services.repository.root()
    discovery = discover_works(root, config.works, services.files)
    refuse_tree(discovery, shared=False)
    directory = services.environment.working_directory()
    work = find_target(
        discovery, args.work, root, directory, config.works, services.files
    )
    found = build_hierarchy(discovery.works, config.works.hierarchy)
    shown = gather_work(work, found, config, services)
    stdio.stdout.write(render_show(shown, as_json=args.json))
    return 0


def find_target(
    discovery: WorkDiscovery,
    argument: str,
    root: Path,
    directory: Path,
    settings: WorksSettings,
    files: FileSystem,
) -> Work:
    """Find the Work that an argument names.

    An argument that contains `/` or ends in `.md` is a path, resolved against
    `directory`, and any other is an id, so an id of that form can be shown only
    by its path.

    Args:
        discovery: What discovery found, with its tree judged complete.
        argument: The id or the path as the person wrote it.
        root: The repository root.
        directory: The working directory, which a relative path is resolved
            against.
        settings: The `[works]` table of the config.
        files: The port that reads files.

    Returns:
        The Work.

    Raises:
        ContractsError: No Work has the id, two Works share it, or the path is
            not a Work, each with the message of its own lookup.
    """
    if _is_path(argument):
        return _by_path(discovery, argument, root, directory, settings, files)
    return _by_id(discovery, argument)


def shown_actions(
    work: Work,
    config: Config,
    catalog: TemplateCatalog,
    root: Path,
    files: FileSystem,
) -> tuple[ShownAction, ...]:
    """Resolve the actions of a Work and say where each comes from.

    The actions are those that `resolve_actions` gives. The ones the config
    declares come first, in its order, then the names it does not declare, the
    Work's own in the order written and then the inherited ones. An action
    emptied by the Work is `removed`, and an action that is empty
    and that nothing else gives is left out. A template that the catalog does not
    have, or rejects, or whose file cannot be read gives no actions, and the
    Work's own are still given.

    Args:
        work: The Work.
        config: The config, for the actions, the stage presets and the defaults.
        catalog: Finds the Work's template.
        root: The repository root that the template's path is relative to.
        files: The port that reads the template's file.

    Returns:
        The actions in the order above, none for a Work that resolves to no
        action.

    Raises:
        ConfigurationError: The config cannot be loaded, which `catalog` raises.
    """
    if work.template is None:
        resolved = resolve_actions(
            work.actions, config.works.defaults.actions, "defaults"
        )
    else:
        inherited = _template_pipelines(work.template, catalog, root, files)
        resolved = resolve_actions(work.actions, inherited, "template")
    return _in_config_order(resolved, config, tuple(work.actions))


def gather_work(
    work: Work, found: Hierarchy, config: Config, services: Services
) -> ShownWork:
    """Gather what `show` prints of a Work.

    Args:
        work: The Work.
        found: The hierarchy of the Works, for the parent, the resolved roots, the
            dependencies and the dependents.
        config: The config.
        services: What the actions and the view are read through.

    Returns:
        The Work with its related Works, its actions and its view.

    Raises:
        OSError: The Work's own file cannot be read, as `resolve_work` raises it.
        UnicodeDecodeError: The Work's own file is not UTF-8.
        ConfigurationError: The config cannot be loaded, which `catalog` raises.
    """
    root = services.repository.root()
    ancestors = found.ancestors[work.path]
    parent = found.parent[work.path]
    return ShownWork(
        work=work,
        parent=None if parent is None else Related(parent.id, parent.title, found=True),
        resolved_roots=found.roots[work.path],
        depends_on=_related_ids(found.dependencies[work.path], found.works),
        dependents=tuple(
            Related(other.id, other.title, found=True)
            for other in found.dependents[work.path]
        ),
        actions=shown_actions(work, config, services.catalog, root, services.files),
        view=render_resolved(
            resolve_work(work, ancestors, services.catalog, root, services.files)
        ),
    )


def _is_path(argument: str) -> bool:
    """Tell a path from an id by its form.

    Args:
        argument: What the person wrote.

    Returns:
        Whether it contains `/` or ends in `.md`.
    """
    return "/" in argument or argument.endswith(".md")


def _by_path(
    discovery: WorkDiscovery,
    argument: str,
    root: Path,
    directory: Path,
    settings: WorksSettings,
    files: FileSystem,
) -> Work:
    """Find the Work that a path names.

    Args:
        discovery: What discovery found.
        argument: The path as written, relative to `directory` or absolute.
        root: The repository root.
        directory: The working directory.
        settings: The `[works]` table of the config.
        files: The port that reads files.

    Returns:
        The Work whose file the path is.

    Raises:
        ContractsError: The path is not a Work, with the reason that
            `explain_not_a_work` gives.
    """
    target = Path(
        normpath(
            Path(argument) if Path(argument).is_absolute() else directory / argument
        )
    )
    reason = explain_not_a_work(root, target, settings, files)
    if reason is not None:
        raise ContractsError(reason)
    return {root / work.path: work for work in discovery.works}[target]


def _by_id(discovery: WorkDiscovery, argument: str) -> Work:
    """Find the Work that has an id.

    Args:
        discovery: What discovery found.
        argument: The id.

    Returns:
        The Work.

    Raises:
        ContractsError: No Work has the id, with the closest id when
            `closest_key` finds one, or two Works share it, with the error of
            discovery and the hint, as `refuse` raises it.
    """
    found = find_work(discovery, argument)
    if found is None:
        close = closest_key(argument, [work.id for work in discovery.works])
        hint = f" Did you mean `{close}`?" if close else ""
        message = f"No Work has the id `{argument}`.{hint}"
        raise ContractsError(message)
    if isinstance(found, Diagnostic):
        refuse([found])
    return found


def _related_ids(ids: Sequence[str], works: Sequence[Work]) -> tuple[Related, ...]:
    """Name the Works that some ids stand for.

    Args:
        ids: The ids in the order listed.
        works: Every Work.

    Returns:
        One entry for each Work that has an id, so a shared id gives one for
        each of them, and an entry that is not found for an id no Work has.
    """
    owners: dict[str, list[Work]] = {}
    for work in works:
        owners.setdefault(work.id, []).append(work)
    related: list[Related] = []
    for work_id in ids:
        related.extend(_named(work_id, owners.get(work_id, [])))
    return tuple(related)


def _named(work_id: str, owners: Sequence[Work]) -> list[Related]:
    """Name the Works that have an id.

    Args:
        work_id: The id as listed.
        owners: The Works that have it.

    Returns:
        An entry for each Work that has the id, or one that is not found.
    """
    if not owners:
        return [Related(work_id, None, found=False)]
    return [Related(work.id, work.title, found=True) for work in owners]


def _template_pipelines(
    name: str, catalog: TemplateCatalog, root: Path, files: FileSystem
) -> Mapping[str, Pipeline]:
    """Read the actions that a template gives.

    Args:
        name: The template's name.
        catalog: Finds the template and says whether it is rejected.
        root: The repository root that the template's path is relative to.
        files: The port that reads the template's file.

    Returns:
        The template's `[actions]`, empty when the catalog does not have the
        template, rejects it or its file cannot be used.
    """
    template = catalog.find(name)
    if template is None or catalog.is_rejected(name):
        return {}
    return template_actions(template, root, files) or {}


def _in_config_order(
    resolved: Sequence[ResolvedAction], config: Config, own: Sequence[str]
) -> tuple[ShownAction, ...]:
    """Turn resolved actions into the actions `show` prints, in order.

    Args:
        resolved: The actions that `resolve_actions` gave, in its order.
        config: The config, for the order, the on-demand flag and the presets.
        own: The names in the Work's own `[actions]`, in the order written.

    Returns:
        The actions in the order that `shown_actions` gives.
    """
    by_name = {action.name: action for action in resolved}
    names = _names_in_order(list(by_name), list(config.actions), own)
    return tuple(_shown(by_name[name], config) for name in names)


def _names_in_order(
    present: Sequence[str], declared: Sequence[str], own: Sequence[str]
) -> list[str]:
    """Order the names of the actions that a Work has.

    Args:
        present: The names, in the order of the resolved actions.
        declared: The names the config declares, in its order.
        own: The names in the Work's own `[actions]`, in the order written.

    Returns:
        The names in the order that `shown_actions` gives.
    """
    first = [name for name in declared if name in present]
    others = [name for name in present if name not in first]
    named = [name for name in own if name in others]
    return [*first, *named, *(name for name in others if name not in named)]


def _shown(action: ResolvedAction, config: Config) -> ShownAction:
    """Describe one resolved action as `show` prints it.

    Args:
        action: The resolved action.
        config: The config, for the on-demand flag and the stages of a preset.

    Returns:
        The action as `ShownAction` describes it.
    """
    declared = config.actions.get(action.name)
    on_demand = declared is not None and declared.on_demand
    source = _SOURCES[action.source]
    pipeline = action.pipeline
    if action.removed:
        return ShownAction(action.name, source, on_demand, None, (), removed=True)
    if isinstance(pipeline, str):
        stages = tuple(config.stage_presets.get(pipeline, ()))
        return ShownAction(
            action.name, source, on_demand, pipeline, stages, removed=False
        )
    return ShownAction(
        action.name, source, on_demand, None, tuple(pipeline), removed=False
    )
