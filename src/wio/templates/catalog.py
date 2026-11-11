# SPDX-License-Identifier: Apache-2.0
"""The catalog of the templates of a project, for the commands that read them."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wio.io.ports import FileSystem, Repository
    from wio.models.config import Config
    from wio.models.diagnostics import Diagnostic
    from wio.models.template import Template
    from wio.ports import Settings
    from wio.templates.discovery import Discovery


class TemplatesCatalog:
    """Finds a template by name and says whether `wio templates check` rejects it.

    It satisfies the `TemplateCatalog` port of `wio.contracts`, which it never
    imports, and `wio.cli` hands it to the group.
    """

    def __init__(
        self, settings: Settings, repository: Repository, files: FileSystem
    ) -> None:
        """Keep the ports the catalog reads through.

        Args:
            settings: Loads the config on the first call of either method, and
                once.
            repository: Finds the repository root.
            files: Lists the templates directory and reads the templates.
        """
        self._ports = (settings, repository, files)
        self._config: Config | None = None
        self._discovery: Discovery | None = None
        self._findings: tuple[Diagnostic, ...] | None = None

    def find(self, name: str) -> Template | None:
        """Find a template by name.

        The templates directory is walked once, on the first call, and what it
        found is kept; the check is not run.

        Args:
            name: The template's name, which is its file's name without `.md`.

        Returns:
            The template, or `None` when no template that could be built has that
            name. A config with an error raises `ConfigurationError`, as the port
            says.
        """
        raise NotImplementedError

    def is_rejected(self, name: str) -> bool:
        """Tell whether `wio templates check` reports an error for a template.

        `check_templates` runs once, on the first call, and what it found is kept;
        `find` is not run.

        Args:
            name: The template's name, which is its file's name without `.md`.

        Returns:
            Whether an error is reported for a file whose name without `.md` is
            the name, the `, `-joined places of a repeated name included, also for
            a template that discovery could not build. A warning never rejects, a
            name that no file has is not rejected, and no name is when the
            templates directory itself is refused. A config with an error raises
            `ConfigurationError`, as the port says.
        """
        raise NotImplementedError
