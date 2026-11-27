# SPDX-License-Identifier: Apache-2.0
"""The `wio describe` command handler."""

from typing import TYPE_CHECKING

from wio.describe.registry import describe_command, describe_engine
from wio.describe.render import (
    render_command_json,
    render_command_text,
    render_engine_json,
    render_engine_text,
)

if TYPE_CHECKING:
    from argparse import Namespace

    from wio.io.ports import Stdio


class DescribeCommand:
    """Run `wio describe [<command>] [--json]` offline without I/O."""

    def run(self, args: Namespace, stdio: Stdio) -> int:
        """Render the engine overview or one subcommand to `stdio.stdout`.

        Args:
            args: Parsed arguments carrying `describe_command` and `json`.
            stdio: Standard streams to write output to.

        Returns:
            Exit code `0` on success.

        Raises:
            WioError: If `args.describe_command` names an unknown command.
        """
        command: str | None = args.describe_command
        as_json: bool = args.json
        if command is None:
            engine = describe_engine()
            output = (
                render_engine_json(engine) if as_json else render_engine_text(engine)
            )
        else:
            desc = describe_command(command)
            output = render_command_json(desc) if as_json else render_command_text(desc)
        stdio.stdout.write(output)
        return 0
