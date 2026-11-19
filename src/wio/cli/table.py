# SPDX-License-Identifier: Apache-2.0
"""The table of commands: one entry per subcommand of a component.

Provisional: the names `table` and `COMMANDS` may change; `Component`, `Entry`
and `component_entry` are required as written.
"""

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal

lazy from wio.cli.null import NoRules
lazy from wio.config import ConfigCommand, ConfigSettings
lazy from wio.contracts import ContractsCommand, Services, WorkLookup
lazy from wio.env import adapters as env
lazy from wio.io import adapters as io
lazy from wio.io import views
lazy from wio.log.command import LogCommand
lazy from wio.log.review import ReviewCommand
lazy from wio.log.sink import LogSink
lazy from wio.templates import TemplatesCatalog, TemplatesCommand
lazy from wio.trailers import Services as TrailersServices
lazy from wio.trailers import TrailersCommand
lazy from wio.trailers.errors import TrailersError
lazy from wio.trailers.write import TrailersReviewChecker

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from wio.cli.ports import Command, CommandSpec
    from wio.io.ports import Repository
    from wio.ports import EventSink

type Component = Literal[
    "config", "contracts", "templates", "rules", "trailers", "log", "context"
]
"""The components of wio, so the type checker rejects any other package name."""


@dataclass(frozen=True)
class Entry:
    """One subcommand: how to describe it and how to wire it, kept apart."""

    package: Component
    """The component whose package provides the command."""

    describe: Callable[[], CommandSpec]
    """Describe the command without wiring it or loading its implementation.

    It does no I/O and raises nothing in a working installation, because it
    runs for every entry on every run.
    """

    wire: Callable[[], Command]
    """Build the command with the adapters its component needs.

    It runs once, and only when the subcommand was chosen.
    """


def component_entry(package: Component, wire: Callable[[], Command]) -> Entry:
    """Make the entry of a component's command.

    The entry's `describe` imports `wio.<package>` and returns its `describe()`,
    a function every component's package provides. It does no I/O and raises
    nothing in a working installation.

    Args:
        package: The component, a name the type checker restricts.
        wire: Builds the command when its subcommand is chosen.

    Returns:
        The entry for the table.
    """

    def describe() -> CommandSpec:
        """Import the component's package and describe its command.

        Returns:
            The command spec the package's `describe()` returns.
        """
        spec: CommandSpec = importlib.import_module(f"wio.{package}").describe()
        return spec

    return Entry(package=package, describe=describe, wire=wire)


def _config() -> Command:
    """Wire `wio config` to the local disk and the git repository.

    Returns:
        The command, reading the config file through the adapters.
    """
    repository = io.GitRepository(env.ProcessEnvironment())
    return ConfigCommand(repository, io.LocalFileSystem())


def _templates() -> Command:
    """Wire `wio templates` to the local disk, the git repository and the config.

    Returns:
        The command, finding the templates through the adapters.
    """
    repository = io.GitRepository(env.ProcessEnvironment())
    files = io.LocalFileSystem()
    return TemplatesCommand(ConfigSettings(repository, files), repository, files)


def _contracts() -> Command:
    """Wire `wio contracts` to the project's ports and the system's randomness.

    Returns:
        The command, whose subcommands read the project through the adapters, find
        the templates through the catalog of `wio.templates` and draw ids from the
        system's randomness.
    """
    environment = env.ProcessEnvironment()
    repository = io.GitRepository(environment)
    files = io.LocalFileSystem()
    settings = ConfigSettings(repository, files)
    catalog = TemplatesCatalog(settings, repository, files)
    entropy = env.SystemEntropy()
    services = Services(settings, repository, files, catalog, entropy, environment)
    return ContractsCommand(services)


def trailers_command(events: EventSink | None = None) -> Command:
    """Wire `wio trailers` to git, the contracts component and a sink.

    Args:
        events: An override for the clone log that receives recorded reviews.

    Returns:
        The command, whose forms read the config, the history and the Works through
        the adapters, look a Work up in the working tree and then in `HEAD` and, for
        a commit message, in the index and then in `HEAD`, and wire a port that
        selects no rule until its component exists.

    Raises:
        TrailersError: If the working directory is not inside a git repository.
        ConfigurationError: If the config cannot be loaded, because the Works
            directory that the index view lists comes from it.
    """
    return TrailersCommand(_trailers_services(events))


def _trailers_services(events: EventSink | None = None) -> TrailersServices:
    """Build the shared review and record services over the local adapters.

    Args:
        events: An optional replacement for the real event sink.

    Returns:
        The ports for record and review operations, with config validated.
    """
    environment = env.ProcessEnvironment()
    repository = io.GitRepository(environment)
    history = io.GitHistory(environment)
    files = io.LocalFileSystem()
    settings = ConfigSettings(repository, files)
    catalog = TemplatesCatalog(settings, repository, files)
    root = _root(repository)
    head = views.HeadFiles(history, root)
    config = settings.load()
    works = Path(config.works.dir)
    index = views.IndexFiles(repository, history, files, root, works)
    tree = WorkLookup(settings, repository, catalog, files, [files, head])
    staged = WorkLookup(settings, repository, catalog, files, [index, head])
    if events is None:
        events = LogSink(
            environment,
            env.SystemClock(),
            env.ProcessDirectories(environment),
            repository,
            files,
            io.SystemStdio(),
            config.log,
        )
    return TrailersServices(settings, tree, history, staged, files, NoRules(), events)


def _log() -> Command:
    """Wire the log command to the local repository and filesystem.

    Returns:
        The command, which locates the log only when showing events.
    """
    environment = env.ProcessEnvironment()
    return LogCommand(
        io.GitRepository(environment),
        env.ProcessDirectories(environment),
        io.LocalFileSystem(),
        _review,
    )


def _review() -> ReviewCommand:
    """Supply the log review form with the checker and sink used by trailers.

    Returns:
        The form over the same configuration and Git history as trailers.
    """
    services = _trailers_services()
    return ReviewCommand(TrailersReviewChecker(services), services.events)


def _root(repository: Repository) -> Path:
    """Find the root of the repository, or say that there is none.

    Args:
        repository: The port that finds the root.

    Returns:
        The root of the repository that the working directory is in.

    Raises:
        TrailersError: If the working directory is not inside a repository.
    """
    try:
        return repository.root()
    except RuntimeError as error:
        raise TrailersError(str(error)) from error


COMMANDS: Final[Sequence[Entry]] = (
    component_entry("config", _config),
    component_entry("contracts", _contracts),
    component_entry("log", _log),
    component_entry("templates", _templates),
    component_entry("trailers", trailers_command),
)
"""Every subcommand of wio, one entry for each component that has a command."""
