# SPDX-License-Identifier: Apache-2.0
"""The loader: finds the config file, reads it and returns what it found."""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from wio.config.checks import CHECKS, CheckInputs, run_checks
from wio.config.shape import read_shape
from wio.errors import ConfigurationError
from wio.models.diagnostics import Diagnostic, sort_diagnostics
lazy from wio.formats import TomlSyntaxError, decode_toml

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.config.checks import Check
    from wio.config.shape import Source
    from wio.io.ports import FileSystem, Repository
    from wio.models.config import Config

CONFIG_PATH = Path(".agents/wio/config.toml")
"""The config file, relative to the root of the repository."""


@dataclass(frozen=True)
class Loaded:
    """Everything one run of the loader found.

    Attributes:
        config: The `Config`, or `None` whenever any diagnostic is an error, so
            no other component ever receives a `Config` with an error in it.
        diagnostics: Every finding of the check run, the shape and the checks
            together, in the order of `sort_diagnostics`.
        sources: Whether each key path of the effective settings that has a
            value comes from the `file` or is the `default`; leaf settings only,
            and an optional setting that is `None` has no entry. Empty when the
            file is not valid TOML.
    """

    config: Config | None
    diagnostics: tuple[Diagnostic, ...]
    sources: frozendict[str, Source]


def load_config(
    repository: Repository,
    files: FileSystem,
    checks: Sequence[Check] = CHECKS,
) -> Loaded:
    """Find the config at the root of the repository, read it and check it.

    The file is `<root>/.agents/wio/config.toml`, where the root is the one
    `repository` finds for the working directory. The shape of the file is read
    into a best-effort `Config`, and then every check runs on it, also when the
    shape has errors, so one run reports every problem.

    Args:
        repository: Finds the root of the repository that holds the working
            directory.
        files: Reads the file.
        checks: The checks to run after the shape, in order.

    Returns:
        The `Config` when no diagnostic is an error, the diagnostics and the
        source of each setting. A file that is not valid TOML gives one error at
        `<file>:<line>:<column>` and no `Config`.

    Raises:
        ConfigurationError: There is no repository, or no readable file; the
            message names the path or the working directory that was looked at.
    """
    root = _root(repository)
    text = _read(files, root / CONFIG_PATH)
    try:
        data = decode_toml(text)
    except TomlSyntaxError as error:
        return Loaded(None, (_syntax(error),), frozendict())
    shape = read_shape(data)
    checked = run_checks(shape.config, CheckInputs(root, files), checks)
    found = sort_diagnostics((*shape.diagnostics, *checked))
    blocked = any(item.severity == "error" for item in found)
    return Loaded(None if blocked else shape.config, found, shape.sources)


def config_or_raise(loaded: Loaded) -> Config:
    """Hand over the `Config` of a load, or refuse with every error at once.

    Args:
        loaded: What `load_config` returned.

    Returns:
        The `Config`; warnings and notes never block.

    Raises:
        ConfigurationError: A diagnostic is an error. It carries every error and
            its message renders them.
    """
    raise NotImplementedError


def _root(repository: Repository) -> Path:
    """Find the root of the repository that holds the working directory.

    Args:
        repository: The port that finds it.

    Returns:
        The absolute root.

    Raises:
        ConfigurationError: There is no repository or it cannot be found; the
            message is the adapter's own, which says what is wrong and what to
            do, and the loader adds nothing to it.
    """
    try:
        return repository.root()
    except RuntimeError as error:
        raise ConfigurationError(str(error)) from error


def _read(files: FileSystem, path: Path) -> str:
    """Read the config file.

    Args:
        files: The port that reads it.
        path: The absolute path of the file.

    Returns:
        The text of the file.

    Raises:
        ConfigurationError: The file is missing or cannot be read. The message
            names the path once, says in words what is wrong and what to do, and
            carries no Python-style error text.
    """
    try:
        return files.read_text(path)
    except FileNotFoundError as error:
        message = f"no config file at {path}; create it there, an empty file is valid"
        raise ConfigurationError(message) from error
    except (OSError, UnicodeDecodeError) as error:
        raise ConfigurationError(_unreadable(path, error)) from error


def _unreadable(path: Path, error: OSError | UnicodeDecodeError) -> str:
    """Say why the config file cannot be read, and what to do.

    Args:
        path: The absolute path of the file.
        error: What reading it raised.

    Returns:
        A sentence that names the path once, says what is wrong in words and
        says what to do next.
    """
    match error:
        case PermissionError():
            return (
                f"the config file {path} cannot be read because of its "
                "permissions; make it readable"
            )
        case IsADirectoryError():
            return f"the config file {path} is a directory; replace it with a file"
        case NotADirectoryError():
            return (
                f"the config file {path} cannot be reached because part of its "
                "path is a file, not a directory; move the file"
            )
        case UnicodeDecodeError():
            return f"the config file {path} is not valid UTF-8; save it as UTF-8"
        case _:
            reason = error.strerror or type(error).__name__
            return (
                f"the config file {path} cannot be read: {reason}; "
                "check that it can be opened"
            )


def _syntax(error: TomlSyntaxError) -> Diagnostic:
    """Turn a syntax error into the one diagnostic of an invalid file.

    Args:
        error: What the decoder raised.

    Returns:
        An error at `<file>:<line>:<column>`, the file relative to the root.
    """
    where = f"{CONFIG_PATH.as_posix()}:{error.line}:{error.column}"
    return Diagnostic("error", where, error.message)
