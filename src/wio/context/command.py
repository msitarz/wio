# SPDX-License-Identifier: Apache-2.0
"""The `wio context` command: what a run writes."""

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Callable

    from wio.context import Compiled, Services
    from wio.io.ports import Stdio


class ContextCommand:
    """The object that `wio.cli` runs for `wio context`."""

    def __init__(
        self, services: Services, compiler: Callable[[str, str, str], Compiled]
    ) -> None:
        """Remember what a run reads and writes through.

        Args:
            services: The ports of the shell.
            compiler: Takes the Work's id, the action and the stage, and returns
                the bundle and the warnings.
        """
        self._services = services
        self._compiler = compiler

    @property
    def services(self) -> Services:
        """What the command reads the project and writes its results through."""
        return self._services

    def run(self, args: Namespace, stdio: Stdio) -> int:
        """Print the bundle and report the warnings of its compilation.

        Standard output holds the bundle's text and nothing else. Each warning is
        one line on standard error that begins `warning: `.

        Args:
            args: The parsed arguments `work`, `action` and `stage`.
            stdio: The streams to write to.

        Returns:
            0, also when there are warnings.

        Raises:
            WioError: For what the user must fix, with nothing written to
                standard output. The command catches no error, so any other one
                reaches the command line as a bug.
        """
        compiled = self._compiler(args.work, args.action, args.stage)
        stdio.stderr.writelines(f"warning: {text}\n" for text in compiled.warnings)
        output = getattr(args, "output", False)
        if output is False:
            stdio.stdout.write(compiled.bundle.text)
        else:
            from wio.context.delivery import write_bundle

            path, warnings = write_bundle(
                compiled.bundle,
                cast("str | None", output),
                self._services.repository,
                self._services.files,
                self._services.directories,
            )
            stdio.stderr.writelines(f"warning: {text}\n" for text in warnings)
            stdio.stdout.write(f"{path}\n")
        return 0
