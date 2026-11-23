# SPDX-License-Identifier: Apache-2.0
"""The report of `wio rules check`: every fault of the rules in one list."""

from typing import TYPE_CHECKING, Final

from wio.formats import render_check
from wio.models.diagnostics import has_error, sort_diagnostics
from wio.rules.discovery import discover
from wio.rules.errors import check_errors
from wio.rules.warns import check_warnings

if TYPE_CHECKING:
    from argparse import Namespace
    from pathlib import Path

    from wio.io.ports import FileSystem, Stdio
    from wio.models.config import Config
    from wio.models.diagnostics import Diagnostic
    from wio.rules import Services

PASSES: Final = "The rules pass."
"""What `wio rules check` says when it has nothing to report."""


def check_rules(
    root: Path, config: Config, files: FileSystem
) -> tuple[Diagnostic, ...]:
    """Judge the whole repository's rules and return every fault once.

    The discovery runs once. `check_errors` and `check_warnings` each return the
    faults of the discovery that have their severity, so a fault of a rule file
    or of a manifest comes through exactly one of them and is never judged a
    second time. The result is in the order of `sort_diagnostics`, whatever the
    order in which the two lists were built. It reads files only through
    `files` and writes none, and it judges every ruleset, whether or not any
    root or stage selects it.

    Args:
        root: The root of the repository.
        config: The settings, which are valid.
        files: Lists and reads the rule files.

    Returns:
        The errors and the warnings together, each at the place the author has to
        edit.
    """
    discovery = discover(root, files)
    return sort_diagnostics(
        (*check_errors(config, discovery), *check_warnings(config, discovery))
    )


def run_check(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Run `wio rules check`: report every fault and set the exit code.

    The report is written with `render_check`, as lines or, with `--json`, as one
    array, and says `The rules pass.` for a repository with nothing to report.

    Args:
        services: What the command reads the project through.
        args: The parsed arguments, with `json` for the array.
        stdio: Where the report goes.

    Returns:
        1 when the report holds an error, and 0 for a warning alone or nothing.

    Raises:
        ConfigurationError: The config has an error, which the command line
            reports and exits 2 for.
    """
    config = services.settings.load()
    found = check_rules(services.repository.root(), config, services.files)
    stdio.stdout.write(render_check(found, as_json=args.json, passes=PASSES))
    return int(has_error(found))
