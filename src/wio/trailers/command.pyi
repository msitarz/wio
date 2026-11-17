# SPDX-License-Identifier: Apache-2.0
"""The spec of the `wio trailers` command: the group of its three forms.

`wio trailers` runs the write form, `check` and `fold` from its arguments, so a
person or an agent reaches them as one command that tells them apart and reports a
usage mistake the same way for every form. The first argument chooses the form: the
word `check` or `fold` selects that subcommand, and any other value is the Work of
the write form, so a Work cannot be named `check` or `fold`. An option before the
first argument is a usage error. The group takes the arguments after `trailers` as
they are and parses them with the parser of the chosen form, `configure_write`,
`configure_check` or `configure_fold`, whose own mistakes, and a call with no
argument at all, raise a `TrailersError` that `wio.cli` turns into the exit code 2.
It has no `--json` option on purpose: the write form prints a plain record to append
to a commit message and a check sends its findings to standard error.

`wio.trailers.describe()` returns a `TrailersSpec`, and the package binds
`TrailersCommand` with a `lazy import`, so that describing the command loads no
module of the package but its `__init__`. `wio.cli` adds the entry
`component_entry("trailers", _trailers)` to its table, which wires the ports into
`wio.trailers.Services`: the git adapter of the `History` port, the
`WorkLookup` of `wio.contracts` for the `Contracts` port over the working tree and
over the index, the file system for a message to check, and the null adapters of
`wio.cli.null` for the rules of a stage and the event sink. `wio.trailers` never
imports an adapter.

The stub is the spec until the wiring stage of the Work that builds the command
writes the module `wio.trailers.command` and deletes this stub, so the spec and the
code never coexist.
"""

from argparse import ArgumentParser, Namespace

from wio.io.ports import Stdio
from wio.trailers import Services

class TrailersSpec:
    """What the usage needs to know about `wio trailers`, and nothing more."""

    name: str
    """The subcommand's name, `trailers`."""

    help: str
    """The line that `wio --help` shows for it."""

    def configure(self, parser: ArgumentParser) -> None:
        """Add the arguments of `wio trailers` to its subparser.

        It does no I/O and loads no module of the package. The subparser takes
        every argument after `trailers` as `forms` and leaves them to the group, so
        an option before the first argument, which no form takes there, is refused
        by argparse with the exit code 2. Its description lists the write form,
        `check` and `fold`, one line each, so `wio trailers --help` shows the three
        forms and exits 0.

        Args:
            parser: The subparser that `wio.cli` created for `trailers`.
        """
        ...

class TrailersCommand:
    """Runs `wio trailers`: the form that its first argument chooses."""

    def __init__(self, services: Services) -> None:
        """Keep the ports that the forms read the project through.

        Args:
            services: The ports of the forms, wired by `wio.cli`.
        """
        ...

    def run(self, args: Namespace, stdio: Stdio) -> int:
        """Run the form that the arguments choose.

        `check` runs the check form and `fold` the fold form, each with the parser
        of its own `configure_*`, and any other first argument runs the write form
        with the arguments from that Work on. The exit code is the form's, 0 for
        what it printed or passed and 1 for a record or a message that does not
        hold. A call with no argument, an unknown option, a form with a missing or
        unknown argument and an option before the first argument are usage
        mistakes, written as `error: <message>` to standard error, with nothing on
        standard output.

        Args:
            args: What the parser read, of which `forms` holds the arguments after
                `trailers`.
            stdio: Where the forms read and write.

        Returns:
            The exit code of the form: 0, or 1 for a failed check.

        Raises:
            TrailersError: For a usage mistake of any form, which exits 2.
            ConfigurationError: If a form loads a config that has an error.
        """
        ...
