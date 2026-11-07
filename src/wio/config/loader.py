# SPDX-License-Identifier: Apache-2.0
"""The loader: finds the config file, reads it and returns what it found."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.config.checks import CHECKS

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.config.checks import Check
    from wio.config.shape import Source
    from wio.io.ports import FileSystem, Repository
    from wio.models.config import Config
    from wio.models.diagnostics import Diagnostic


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
    raise NotImplementedError
