# SPDX-License-Identifier: Apache-2.0
"""The `wio config` command: list and show the effective settings.

It follows the rules of the command line: its output goes to the streams it is
given, a config with an error is refused before anything is printed, and the
`json` module is imported only for `--json`.
"""

from typing import TYPE_CHECKING, Literal, cast
lazy import json

from wio.config.keypath import resolve
from wio.config.listing import as_object, full_line, settings_of, short_line
from wio.config.loader import config_or_raise, load_config

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Callable

    from wio.config.listing import Setting
    from wio.io.ports import FileSystem, Repository, Stdio


class Arguments:
    """The attributes of the parsed arguments that `ConfigCommand.run` reads.

    `wio.config.describe()` makes the parser set them; the command reads them
    from the `Namespace` it is given, so this class only documents and types
    them.
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
        self._repository = repository
        self._files = files

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
        arguments = cast("Arguments", args)
        if arguments.config_view is None:
            stdio.stdout.write(arguments.config_help())
            return 0
        loaded = load_config(self._repository, self._files)
        config = config_or_raise(loaded)
        every = settings_of(config, loaded.sources)
        if arguments.config_view == "list":
            stdio.stdout.write(_list(every, as_json=arguments.json))
        else:
            target = resolve(config, arguments.key)
            chosen = tuple(item for item in every if target.covers(item.path))
            text = _show(chosen, single=target.single, as_json=arguments.json)
            stdio.stdout.write(text)
        return 0


def _list(settings: tuple[Setting, ...], *, as_json: bool) -> str:
    """Write every setting, shortened to a line each, or in full as JSON.

    Args:
        settings: The settings, sorted by key path.
        as_json: Whether to write the JSON object.

    Returns:
        The text to print.
    """
    if as_json:
        return _as_json(settings)
    return "".join(f"{short_line(item)}\n" for item in settings)


def _show(settings: tuple[Setting, ...], *, single: bool, as_json: bool) -> str:
    """Write settings in full, with the description of a single setting.

    Args:
        settings: The settings to show, sorted by key path.
        single: Whether they are one setting asked for by its key path.
        as_json: Whether to write the JSON object.

    Returns:
        The text to print; empty for a table without settings.
    """
    if as_json:
        return _as_json(settings)
    text = "".join(f"{full_line(item)}\n" for item in settings)
    if single:
        text += f"{settings[0].description}\n"
    return text


def _as_json(settings: tuple[Setting, ...]) -> str:
    """Write settings as one JSON object keyed by key path.

    Args:
        settings: The settings, sorted by key path.

    Returns:
        The object that `as_object` describes, serialized.
    """
    return json.dumps(as_object(settings), indent=2, ensure_ascii=False) + "\n"
