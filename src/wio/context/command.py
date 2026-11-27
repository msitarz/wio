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
        """Deliver the bundle, report its warnings, and record the stage entry.

        Compilation warnings come first, followed by any size warning, before
        delivery, so a delivery error does not hide them. Standard output holds
        the bundle or the requested file path and a newline. Each warning is one
        line on standard error that begins `warning: `. After delivery succeeds,
        one `context` event is written through `services.events`.

        Args:
            args: The parsed `work`, `action`, `stage` and optional `output`.
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
        from wio.context.gate_start import read_gate_start
        from wio.context.size_warning import size_warning

        config = self._services.settings.load()
        warning = size_warning(compiled.bundle.size, config.bundle.size_threshold)
        if warning is not None:
            stdio.stderr.write(f"warning: {warning}\n")
        stage_config = config.stages.get(args.stage)
        gate = read_gate_start(
            args.action,
            args.stage,
            is_gate=bool(stage_config and stage_config.gate),
            reviewed=self._services.reviewed,
            repository=self._services.repository,
        )
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
        stdio.stderr.writelines(f"warning: {text}\n" for text in gate.warnings)
        from wio.context.entry import record_entry

        record_entry(
            args.work,
            args.action,
            args.stage,
            compiled.bundle,
            self._services.events,
            start=gate.start,
            dirty=gate.dirty,
        )
        return 0
