# SPDX-License-Identifier: Apache-2.0
"""Run the selected log command over the adapters supplied by the CLI.

Bare help can run in any working directory.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from wio.log.render import render
from wio.log.show import read_report

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Callable

    from wio.env.ports import Directories
    from wio.io.ports import FileSystem, Repository, Stdio


class Arguments:
    """The parser values shared by the log forms.

    Attributes:
        log_form: The form name, or None for bare help.
        log_help: Returns help for the bare log command.
        work: The optional Work filter for show.
        json: Whether show uses its JSON form.
    """

    log_form: str | None
    log_help: Callable[[], str]
    work: str | None
    json: bool


@dataclass(frozen=True)
class LogCommand:
    """The log command wired to the ports shared by its forms.

    Attributes:
        repository: Supplies the identity of the clone.
        directories: Supplies the Wio home.
        filesystem: Reads the clone's log files.
    """

    repository: Repository
    directories: Directories
    filesystem: FileSystem

    def run(self, args: Namespace, stdio: Stdio) -> int:
        """Run the chosen form of the command.

        Args:
            args: The parsed help or show arguments.
            stdio: Receives the report and any text-form note.

        Returns:
            Zero for help or a readable log, including an empty log.

        Raises:
            WioError: The log cannot be located or read.
        """
        arguments = cast("Arguments", args)
        if arguments.log_form is None:
            stdio.stdout.write(arguments.log_help())
            return 0
        report = read_report(
            self.repository, self.directories, self.filesystem, arguments.work
        )
        stdio.stdout.write(render(report, as_json=arguments.json))
        if report.skipped and not arguments.json:
            noun = "line" if report.skipped == 1 else "lines"
            stdio.stderr.write(
                f"note: skipped {report.skipped} {noun} of the event log\n"
            )
        return 0
