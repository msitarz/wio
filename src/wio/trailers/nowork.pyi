# SPDX-License-Identifier: Apache-2.0
"""The `none` form of `wio trailers`: print the record of a commit with no Work.

`wio trailers none` prints `Wio-Work: none`, the record of a commit that belongs
to no Work, and nothing else: that record allows no other key, so the form takes
no action, stage or option. `wio.cli` wires the ports and the config is read then,
as for every form, so this form loads nothing.
"""

from argparse import ArgumentParser, Namespace

from wio.io.ports import Stdio
from wio.trailers import Services

def configure_nowork(parser: ArgumentParser) -> None:
    """Add the arguments of the `none` form to its parser, which are none.

    It does no I/O. A parser with no argument makes argparse refuse an action, a
    stage, an option or any other argument that follows `none` as an unrecognized
    argument, which the command turns into a usage mistake with the exit code 2.

    Args:
        parser: The parser that the command created for the form.
    """
    ...

def run_nowork(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Print the record of a commit that belongs to no Work.

    The record is rendered by the shared renderer of `wio.formats` from the one
    field `Wio-Work`, and written to standard output with its newline. Nothing is
    read, judged or written elsewhere, so the form cannot refuse.

    Args:
        services: The ports of the command, none of which this form uses.
        args: What the form's parser read, which holds nothing.
        stdio: Where the record is written.

    Returns:
        0, always.
    """
    ...
