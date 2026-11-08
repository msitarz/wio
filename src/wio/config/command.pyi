# SPDX-License-Identifier: Apache-2.0
"""The `wio config` command: list and show the effective settings.

The stub is the spec until the implementation stage replaces it with a `.py` of
the same annotations. It follows the rules of the command line: its output goes
to the streams it is given, a config with an error is refused before anything is
printed, and the `json` module is imported only for `--json`.
"""

from argparse import Namespace

from wio.io.ports import FileSystem, Repository, Stdio

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
            args: The parsed arguments: `config_view` is `list`, `show` or
                `None`, `config_help` returns the help text, `json` says whether
                to write one JSON object, and `key` is the key path of `show`.
            stdio: The streams to write to.

        Returns:
            0. Bare `wio config` writes its help and reads no config file.

        Raises:
            ConfigurationError: The config has an error, or the key path names
                nothing that can be shown; the command line exits 2.
        """
        ...
