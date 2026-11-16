# SPDX-License-Identifier: Apache-2.0
"""Helpers that the unit tests of the discovery of Works share."""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast
from unittest.mock import Mock

from tests.fakes import FakeEnvironment
from tests.unit.fakes import ROOT, FakeEntropy, FakeRepository
from wio.contracts import Services
from wio.models.config import Config
from wio.models.frozen import freeze
from wio.models.works import Work

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from tests.unit.fakes import MemoryFileSystem
    from wio.contracts.ports import TemplateCatalog
    from wio.models.diagnostics import Diagnostic
    from wio.ports import Settings


BASE = ".agents/wio/works"
"""The default Works directory, relative to the repository root."""


def work_under_works(
    path: str,
    work_id: str,
    title: str | None = None,
    template: str | None = None,
    roots: tuple[str, ...] = (),
    depends_on: tuple[str, ...] = (),
    actions: Mapping[str, str | tuple[str, ...]] | None = None,
) -> Work:
    """Build a Work at `<Works directory>/<path>`.

    Args:
        path: The file, relative to the Works directory.
        work_id: The id.
        title: The title, or `None`.
        template: The template, or `None`.
        roots: The roots as written.
        depends_on: The dependencies as written.
        actions: The `[actions]` overrides.

    Returns:
        The Work.
    """
    return Work(
        id=work_id,
        title=title,
        path=Path(BASE) / path,
        template=template,
        roots=roots,
        depends_on=depends_on,
        actions=freeze(actions or {}),
    )


def where(diagnostics: Iterable[Diagnostic]) -> list[str]:
    """List the places of some diagnostics.

    Args:
        diagnostics: The diagnostics.

    Returns:
        Their places, in their order.
    """
    return [d.where for d in diagnostics]


def paths(items: Iterable[Path]) -> list[str]:
    """List some paths written with `/`.

    Args:
        items: The paths.

    Returns:
        Their strings, in their order.
    """
    return [p.as_posix() for p in items]


def work_with_id(work_id: str) -> Work:
    """Build a Work that has an id and sits at `<id>/README.md`.

    Args:
        work_id: The id.

    Returns:
        The Work, with nothing else set.
    """
    return Work(
        id=work_id,
        title=None,
        path=Path(work_id) / "README.md",
        template=None,
        roots=(),
        depends_on=(),
        actions=freeze({}),
    )


@dataclass(frozen=True)
class _Settings:
    """A `Settings` that gives one config."""

    config: Config

    def load(self) -> Config:
        """Give the config.

        Returns:
            The config.
        """
        return self.config


def services(
    files: MemoryFileSystem,
    config: Config | None = None,
    catalog: TemplateCatalog | None = None,
    directory: Path = ROOT,
) -> Services:
    """Build the services of `wio contracts` around an in-memory file system.

    Args:
        files: The files.
        config: What the settings give, the default config when none is given.
        catalog: The catalog, a mock when none is given.
        directory: The working directory.

    Returns:
        The services, with fakes for the repository, the entropy and the
        environment.
    """
    return Services(
        cast("Settings", _Settings(config or Config())),
        FakeRepository(),
        files,
        catalog or cast("TemplateCatalog", Mock()),
        FakeEntropy(),
        FakeEnvironment(directory),
    )
