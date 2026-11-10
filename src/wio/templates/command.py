# SPDX-License-Identifier: Apache-2.0
"""The `wio templates` command: show the templates of the project."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Callable
    from typing import Literal

    from wio.io.ports import FileSystem, Repository, Stdio
    from wio.ports import Settings


class Arguments:
    """The attributes of the parsed arguments that `TemplatesCommand.run` reads.

    The parser set up by `wio.templates.describe()` sets them; the command reads
    them from the `Namespace` it is given, so this class only documents and types
    them.
    """

    templates_view: Literal["list"] | None
    """The subcommand chosen, `None` for bare `wio templates`."""

    templates_help: Callable[[], str]
    """Returns the usage of `wio templates`; set by the parser, so bare
    `wio templates` prints it without loading the config."""

    kind: str | None
    """The kind that `list` is limited to; present for `list`."""

    json: bool
    """Whether `list` writes JSON; present for `list`."""


class TemplatesCommand:
    """Runs `wio templates`: its help, and `list` for the templates."""

    def __init__(
        self, settings: Settings, repository: Repository, files: FileSystem
    ) -> None:
        """Keep the ports the command reads through.

        Args:
            settings: Loads the config, whose `[templates]` table says where the
                templates are and which one is each kind's entry.
            repository: Finds the repository root.
            files: Lists the templates directory and reads the templates.
        """
        self._files = files
        self._settings = settings
        self._repository = repository

    def run(self, args: Namespace, stdio: Stdio) -> int:
        """Run `wio templates` as the arguments ask.

        Args:
            args: What the parser read, as `Arguments` describes it.
            stdio: Where the output and the errors go.

        Returns:
            The exit code, 0. Bare `wio templates` writes its help and loads no
            config. `list` writes the templates to `stdio.stdout`, limited to
            `--kind` when it is given, as one JSON array with `--json`, and
            nothing for a declared kind with no templates.

        Raises:
            ConfigurationError: The config has an error.
            TemplatesError: A template or the templates directory has an error,
                which `list` refuses to list around: it carries the errors and
                says that `wio templates check` shows every problem. Or `--kind`
                names a kind that the config does not declare, and the message
                names it and the declared kinds. The command line exits 2.
        """
        raise NotImplementedError
