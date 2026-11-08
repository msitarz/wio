# SPDX-License-Identifier: Apache-2.0
"""What the usage knows about `wio config`, which `wio.config.describe()` returns.

The stub is the spec of the command's registration. The wiring stage writes the
class in the package's `__init__`, and deletes this stub, because describing the
command must load no other module of `wio.config`. The class satisfies the
`CommandSpec` of `wio.cli` structurally, and `wio.config` never imports that
port.
"""

from argparse import ArgumentParser

class ConfigSpec:
    """The name, the help and the arguments of `wio config`.

    Making it and calling `configure` does no I/O and raises nothing, because
    they happen for every command on every run.
    """

    @property
    def name(self) -> str:
        """The subcommand's name: `config`."""
        ...

    @property
    def help(self) -> str:
        """One line for `wio --help`; it is also the description of `config`."""
        ...

    def configure(self, parser: ArgumentParser) -> None:
        """Add the views of `wio config` to its subparser.

        It gives `parser` two defaults, `config_view` as `None` and
        `config_help` as the parser's own `format_help`, and a subparser for
        each view whose default `config_view` is its name: `list` takes
        `--json`, and `show` takes an optional positional `key` (all the
        settings when omitted) and `--json`.

        Args:
            parser: The subparser that `wio.cli` created for `config`.
        """
        ...

def describe() -> ConfigSpec:
    """Describe `wio config` without loading the rest of the package.

    Returns:
        The spec of `config`. Importing `wio.config`, calling this and calling
        `configure` load no other module of `wio.config`; `ConfigCommand` is
        exported with a `lazy` import, and the CLI table wires it with the local
        file system and the git repository.
    """
    ...
