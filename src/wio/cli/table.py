# SPDX-License-Identifier: Apache-2.0
"""The table of commands: one entry per subcommand of a component.

Provisional: the names `table` and `COMMANDS` may change; `Component`, `Entry`
and `component_entry` are required as written.
"""

import importlib
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal

lazy from wio.config import ConfigCommand, ConfigSettings, RepositorySkills
lazy from wio.context import Compiler, Composition, ContextCommand
lazy from wio.context import Services as ContextServices
lazy from wio.context.inputs import KnownInputs
lazy from wio.context.known_work import KnownWork
lazy from wio.context.no_roots import NoRootsWarning
lazy from wio.context.pipeline import PipelineWarning
lazy from wio.contracts import (
    ContractsCommand,
    ContractViews,
    Services,
    WorkLookup,
    cached_discover,
)
lazy from wio.env import adapters as env
lazy from wio.io import adapters as io
lazy from wio.io import views
lazy from wio.log.command import LogCommand
lazy from wio.log.review import ReviewCommand
lazy from wio.log.sink import LogSink
lazy from wio.rules import RulesCommand, RuleSelector, RuleTopics
lazy from wio.rules import Services as RulesServices
lazy from wio.templates import TemplatesCatalog, TemplatesCommand
lazy from wio.trailers import Services as TrailersServices
lazy from wio.trailers import TrailersCommand
lazy from wio.trailers.errors import TrailersError
lazy from wio.trailers.reviewed import reviewed_commit
lazy from wio.trailers.write import TrailersReviewChecker

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from wio.cli.ports import Command, CommandSpec
    from wio.env.ports import Directories, Environment
    from wio.io.ports import FileSystem, History, Repository
    from wio.models.events import Event
    from wio.ports import EventSink, Settings

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
    """Wire `wio config` to the local disk and the git repository."""
    repository = io.GitRepository(env.ProcessEnvironment())
    return ConfigCommand(repository, io.LocalFileSystem())


def _templates() -> Command:
    """Wire `wio templates` to the local disk, the git repository and the config."""
    repository = io.GitRepository(env.ProcessEnvironment())
    files = io.LocalFileSystem()
    return TemplatesCommand(ConfigSettings(repository, files), repository, files)


def _contracts() -> Command:
    """Wire `wio contracts` to the project's ports and the system's randomness."""
    return ContractsCommand(_contracts_services())


def _contracts_services() -> Services:
    """Connect contract readers and writers to the current project."""
    environment = env.ProcessEnvironment()
    repository = io.GitRepository(environment)
    files = io.LocalFileSystem()
    settings = ConfigSettings(repository, files)
    catalog = TemplatesCatalog(settings, repository, files)
    return Services(
        settings, repository, files, catalog, env.SystemEntropy(), environment
    )


def _rules() -> Command:
    """Wire `wio rules` to the project's ports."""
    environment = env.ProcessEnvironment()
    repository = io.GitRepository(environment)
    files = io.LocalFileSystem()
    settings = ConfigSettings(repository, files)
    catalog = TemplatesCatalog(settings, repository, files)
    works = WorkLookup(settings, repository, catalog, files, [files])
    return RulesCommand(RulesServices(settings, repository, files, environment, works))


@dataclass(frozen=True)
class _ContextEventSink:
    """Defer `LogSink` construction until `wio context` delivers a bundle."""

    environment: Environment
    directories: Directories
    repository: Repository
    files: FileSystem
    settings: Settings

    def write(self, event: Event) -> None:
        """Forward the event to `LogSink` using the current project's log config.

        Any failure while loading settings or constructing the sink is reported
        as a warning and never raised, matching the `EventSink` port contract.

        Args:
            event: The `context` event to record.
        """
        try:
            sink = LogSink(
                self.environment,
                env.SystemClock(),
                self.directories,
                self.repository,
                self.files,
                io.SystemStdio(),
                self.settings.load().log,
            )
        except Exception as error:  # noqa: BLE001 - EventSink never raises
            with suppress(Exception):
                io.SystemStdio().stderr.write(
                    f"warning: the event log could not be written: {error}\n"
                )
            return
        sink.write(event)


@dataclass(frozen=True)
class _ContextReviewedCommit:
    """Close `wio.trailers.reviewed.reviewed_commit` over history and settings."""

    history: History
    settings: Settings

    def find(self, action: str, stage: str) -> str | None:
        """Find the first commit from `HEAD` down that is not a pure gate commit.

        Args:
            action: The action of the gate.
            stage: The stage of the gate.

        Returns:
            The full commit id, or `None` when none exists.
        """
        return reviewed_commit(
            action, stage, self.history, self.settings.load().trailers.reader
        )


def _context() -> Command:
    """Wire `wio context` to the project's ports."""
    contracts = _contracts_services()
    settings, repository, files = (
        contracts.settings,
        contracts.repository,
        contracts.files,
    )
    discover = cached_discover()
    works = WorkLookup(
        settings, repository, contracts.catalog, files, [files], discover=discover
    )
    views = ContractViews(contracts, discover=discover)
    composer = Composition(
        views,
        RuleSelector(settings, repository, files, works),
        RuleTopics(repository, files),
        RepositorySkills(repository, files, settings),
        settings,
        repository,
        files,
    )
    directories = env.ProcessDirectories(contracts.environment)
    events = _ContextEventSink(
        contracts.environment, directories, repository, files, settings
    )
    reviewed = _ContextReviewedCommit(io.GitHistory(contracts.environment), settings)
    services = ContextServices(
        repository,
        files,
        contracts.environment,
        directories,
        settings,
        events,
        reviewed,
    )
    return ContextCommand(
        services,
        Compiler(
            composer,
            (
                KnownWork(views),
                KnownInputs(settings, works),
                PipelineWarning(works),
                NoRootsWarning(settings, works),
            ),
        ).compile,
    )


def trailers_command(events: EventSink | None = None) -> Command:
    """Wire `wio trailers` to git, the contracts component and a sink.

    Args:
        events: An override for the clone log that receives recorded reviews.

    Returns:
        The command, whose forms read the config, the history and the Works through
        the adapters, look a Work up in the working tree and then in `HEAD` and, for
        a commit message, in the index and then in `HEAD`, and select the rules of a
        stage with a `RuleSelector` over the working tree.

    Raises:
        TrailersError: If the working directory is not inside a git repository.
        ConfigurationError: If the config cannot be loaded, because the Works
            directory that the index view lists comes from it.
    """
    return TrailersCommand(_trailers_services(events))


def _trailers_services(events: EventSink | None = None) -> TrailersServices:
    """Build the shared review and record services over the local adapters."""
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
    selector = RuleSelector(settings, repository, files, tree)
    return TrailersServices(settings, tree, history, staged, files, selector, events)


def _log() -> Command:
    """Wire the log command to the local repository and filesystem."""
    environment = env.ProcessEnvironment()
    return LogCommand(
        io.GitRepository(environment),
        env.ProcessDirectories(environment),
        io.LocalFileSystem(),
        _review,
    )


def _review() -> ReviewCommand:
    """Supply the log review form with the checker and sink used by trailers."""
    services = _trailers_services()
    return ReviewCommand(TrailersReviewChecker(services), services.events)


def _root(repository: Repository) -> Path:
    """Find the root of the repository, or say that there is none."""
    try:
        return repository.root()
    except RuntimeError as error:
        raise TrailersError(str(error)) from error


COMMANDS: Final[Sequence[Entry]] = (
    component_entry("config", _config),
    component_entry("context", _context),
    component_entry("contracts", _contracts),
    component_entry("log", _log),
    component_entry("rules", _rules),
    component_entry("templates", _templates),
    component_entry("trailers", trailers_command),
)
"""Every subcommand of wio, one entry for each component that has a command."""
