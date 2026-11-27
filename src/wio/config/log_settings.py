# SPDX-License-Identifier: Apache-2.0
"""Checks for the harness and environment settings of the event log."""

import re
from collections import Counter
from typing import TYPE_CHECKING

from wio.formats.wording import join_path, quoted
from wio.models.diagnostics import Diagnostic

if TYPE_CHECKING:
    from collections.abc import Iterator

    from wio.config.checks import CheckInputs
    from wio.models.config import Config, Harness

_VARIABLE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_HARNESS = re.compile(r"[A-Za-z0-9_-]+")


def check_log_settings(config: Config, _inputs: CheckInputs) -> Iterator[Diagnostic]:
    """Judge harness names, preference order and environment variable names.

    Args:
        config: The best-effort config assembled by the shape reader.
        _inputs: The shared check inputs. This check reads only the config.

    Yields:
        Errors at the setting that contains a bad name or a repeat.
    """
    log = config.log
    preference = "log.prefer_harness"
    yield from _repeats(preference, log.prefer_harness)
    unknown = sorted(set(log.prefer_harness) - log.harnesses.keys())
    if unknown:
        yield Diagnostic(
            "error", preference, f"unknown harness names {quoted(unknown)}."
        )
    yield from _variables("log.record_env_vars", log.record_env_vars)
    for name, harness in log.harnesses.items():
        yield from _check_harness(name, harness)


def _check_harness(name: str, harness: Harness) -> Iterator[Diagnostic]:
    """Judge a harness name and its variable lists."""
    path = join_path("log.harnesses", name)
    if name == "none":
        yield Diagnostic("error", path, "`none` is reserved by `WIO_PREFER_HARNESS`.")
    elif not _HARNESS.fullmatch(name):
        yield Diagnostic("error", path, "a harness name must be a TOML bare key.")
    yield from _variables(f"{path}.session", harness.session)
    yield from _variables(f"{path}.parent", harness.parent)


def _variables(path: str, names: tuple[str, ...]) -> Iterator[Diagnostic]:
    """Judge the names in one variable list."""
    invalid = sorted({name for name in names if not _VARIABLE.fullmatch(name)})
    if invalid:
        yield Diagnostic("error", path, f"invalid environment names {quoted(invalid)}.")
    yield from _repeats(path, names)


def _repeats(path: str, names: tuple[str, ...]) -> Iterator[Diagnostic]:
    """Find repeated names in one list."""
    repeated = sorted(name for name, count in Counter(names).items() if count > 1)
    if repeated:
        yield Diagnostic("error", path, f"repeated names {quoted(repeated)}.")
