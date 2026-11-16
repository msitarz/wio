# SPDX-License-Identifier: Apache-2.0
"""What `wio contracts show` finds out about a Work before it prints it."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

lazy from wio.contracts.discovery import WorkDiscovery
lazy from wio.contracts.hierarchy import Hierarchy

if TYPE_CHECKING:
    from argparse import Namespace
    from pathlib import Path

    from wio.contracts import Services
    from wio.contracts.ports import TemplateCatalog
    from wio.io.ports import FileSystem, Stdio
    from wio.models.config import Config
    from wio.models.config import Works as WorksSettings
    from wio.models.works import Work

type ShownSource = Literal["template", "contract", "defaults"]
"""Where an action comes from: the template, the Work's own `[actions]` or the
config's `[works.defaults.actions]`."""


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
        preset: The stage preset the action names, or `None` for a list of
            stages, for a removed action.
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
        ContractsError: The tree is incomplete, or the argument names no Work.
            Its message is the errors, one `error: <where>: <message>` to a
            line, or the one message of the lookup, and for an incomplete tree
            and a shared id the line "`wio contracts check` shows every
            problem.". The command line writes it to standard error and exits 2.
        ConfigurationError: The config has an error.
    """
    raise NotImplementedError


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
        ContractsError: No Work has the id, naming it and the closest id when
            there is one; two Works share it, with the error of discovery and the
            line that points to `wio contracts check`; or the path is not a Work,
            with the reason that `explain_not_a_work` gives.
    """
    raise NotImplementedError


def shown_actions(
    work: Work,
    config: Config,
    catalog: TemplateCatalog,
    root: Path,
    files: FileSystem,
) -> tuple[ShownAction, ...]:
    """Resolve the actions of a Work and say where each comes from.

    The actions are those that `resolve_actions` gives. The ones the config
    declares come first, in its order, then the names it does not declare in the
    order that the Work's own `[actions]`, the template's and the defaults list
    them. An action emptied by the Work is `removed`, and an action that is empty
    and that nothing else gives is left out. A template that the catalog does not
    have, or rejects, or whose file cannot be read gives no actions.

    Args:
        work: The Work.
        config: The config, for the actions, the stage presets and the defaults.
        catalog: Finds the Work's template.
        root: The repository root that the template's path is relative to.
        files: The port that reads the template's file.

    Returns:
        The actions in the order above.
    """
    raise NotImplementedError


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
    """
    raise NotImplementedError
