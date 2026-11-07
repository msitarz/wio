# SPDX-License-Identifier: Apache-2.0
"""The checks of the check run, kept in one ordered tuple."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence
    from pathlib import Path

    from wio.io.ports import FileSystem
    from wio.models.config import Config
    from wio.models.diagnostics import Diagnostic


@dataclass(frozen=True)
class CheckInputs:
    """What a check may read besides the `Config`.

    Provisional: a check that needs more adds a member, and `Loaded`,
    `load_config`, `Check` and `CHECKS` stay as they are.

    Attributes:
        root: The absolute root of the repository, the base of every path the
            config names.
        files: The port a check reads the files it needs through.
    """

    root: Path
    files: FileSystem


type Check = Callable[[Config, CheckInputs], Iterable[Diagnostic]]
"""One concern of the check run, a function from the `Config` and its inputs.

A check never raises for a problem of the config: it returns the diagnostics. It
may be given a best-effort `Config` that has errors of its own shape, so it must
not report again what the shape already reported.
"""

CHECKS: tuple[Check, ...] = ()
"""The checks that the loader runs after the shape, in order.

A leaf that adds a check appends it here, which changes neither `load_config`'s
callers nor `Settings.load`.
"""


def run_checks(
    config: Config, inputs: CheckInputs, checks: Sequence[Check]
) -> tuple[Diagnostic, ...]:
    """Run every check, in order, on one `Config`.

    Args:
        config: The best-effort `Config` of the shape, which may have errors.
        inputs: What the checks may read.
        checks: The checks to run, in order.

    Returns:
        Every diagnostic that the checks returned, in the order they came.
    """
    raise NotImplementedError
