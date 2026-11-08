# SPDX-License-Identifier: Apache-2.0
"""The `wio config` command: list and show the effective settings.

The stub is the spec until the implementation stage replaces it with a `.py` of
the same annotations. It follows the rules of the command line: its output goes
to the streams it is given, a config with an error is refused before anything is
printed, and the `json` module is imported only for `--json`.
"""

from argparse import Namespace
from collections.abc import Callable
from typing import Literal

from wio.io.ports import FileSystem, Repository, Stdio

class Arguments(Namespace):
    """The attributes of the parsed arguments that `ConfigCommand.run` reads.

    `wio.config.describe()` makes the parser set them; the command reads them
    from the `Namespace` it is given.
    """

    config_view: Literal["list", "show"] | None
    """The subcommand chosen, `None` for bare `wio config`."""

    config_help: Callable[[], str]
    """Returns the usage of `wio config`; set by the parser of `config`, so bare
    `wio config` prints it without loading the config file."""

    json: bool
    """Whether to write one JSON object; present for `list` and `show`."""

    key: str
    """The key path of `show`, empty for the whole config; present for `show`."""

class ConfigCommand:
    """Runs `wio config`: bare for its help, `list` and `show` for the settings."""

    def __init__(self, repository: Repository, files: FileSystem) -> None:
        """Keep the ports the loader reads through.

        Args:
            repository: Finds the root of the repository.
            files: Reads the config file.
        """
        ...

    def run(self, args: Namespace, stdio: Stdio) -> int:
        """Run the chosen view.

        Args:
            args: The parsed arguments, with the attributes of `Arguments`.
            stdio: The streams to write to.

        Returns:
            0. Bare `wio config` writes its help and reads no config file. `list`
            and `show` write to `stdio.stdout` only, one line per setting. A
            single setting shown by `show` is followed by a line that holds its
            description.

        Raises:
            ConfigurationError: The config has an error: it carries every error
                and renders them as its message, as `ConfigSettings.load` does,
                and nothing is written to `stdio.stdout`. Or the key path, which
                `show` judges after the config is loaded, names nothing that can
                be shown. The command line exits 2.
        """
        ...
