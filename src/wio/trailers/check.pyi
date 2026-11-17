# SPDX-License-Identifier: Apache-2.0
"""The spec of the check form of `wio trailers`, in its commit-time mode.

`wio trailers check --require [PATH]` judges a commit message against the config
and the Works it was written for, so that a wrong record is refused before it
enters the history. `wio.cli` dispatches on the first argument and wires the
ports, and this module holds what the form does, so it is run in a test with
fakes. The later check of a body or a range shares the form and adds its own mode,
which makes the option `--require` optional. The records are read and their form is
judged by `wio.formats`, and their fields by the validator of this package.

The stub is the spec until the wiring stage of the Work that builds the commit-time
check writes the module `wio.trailers.check` and deletes this stub, so the spec and
the code never coexist.
"""

from argparse import ArgumentParser, Namespace

from wio.io.ports import Stdio
from wio.models.config import Config
from wio.models.diagnostics import Diagnostic
from wio.trailers import Services
from wio.trailers.ports import Contracts

def has_exempt_subject(message: str) -> bool:
    """Tell whether git wrote the subject of a message, which needs no record.

    The subject is the first line that is not a `#` comment, because a commit-msg
    hook sees the comments that git removes afterwards. It is exempt when it starts
    with `Merge`, `Revert`, `Reapply`, `fixup!` or `squash!` followed by a space, so
    `amend! x`, `fixup!x` and `Merged x` are not. The exemption is only from the
    requirement of a record: a record that such a message has is still judged.

    Args:
        message: The commit message as the hook is given it.

    Returns:
        Whether the subject is one that git writes. A message with no subject, such
        as an empty one, has none.
    """
    ...

def check_commit_message(
    message: str, contracts: Contracts, config: Config
) -> list[Diagnostic]:
    """Judge a commit message as it is committed.

    The records are read with the reader of the config and judged in three steps.
    `check_shape` judges each record's own form: a `malformed` or `invisible` finding
    is an error, and an `unknown-key` finding is a warning, deliberately, because a
    key that the engine no longer defines is no reason to refuse a commit. A record
    with no finding is then judged by `validate_record` against the config and the
    Works, with the fields carrying their lines in the message, so a name that the
    config lacks, a Work or an item that does not exist and a result that does not fit
    its stage are errors, and a stage outside the Work's pipeline is a warning. A
    record that has a finding is not validated, because its fields cannot be trusted.
    Last, a message with no record whose subject is not one that git writes has the
    error `no record was found` at line 1.

    Args:
        message: The commit message.
        contracts: Finds the Works in the index and then in `HEAD`, so that a Work
            that the commit being made deletes is still found.
        config: The config, for the reader, the names and the results.

    Returns:
        The diagnostics, each with the 1-based line number in the message as its
        `where`, or `1` for the record that was not found, sorted by that number as
        a number, then errors before warnings, then by message.
    """
    ...

def configure_check(parser: ArgumentParser) -> None:
    """Add the arguments of the check form to its parser.

    It does no I/O. `path` is optional: the file that holds the message, or standard
    input when it is `-` or absent. `--require` selects the commit-time mode, which
    requires a record, and is required until the later check adds its own mode.

    Args:
        parser: The parser that `wio.cli` created for `check`.
    """
    ...

def run_check(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Check the commit message of the arguments.

    The message is read from the file or from standard input, and each diagnostic of
    `check_commit_message` is written to standard error as
    `<severity>: <where>: <message>`, one to a line, in its order. Nothing is
    written to standard output.

    Args:
        services: The ports the form reads the config, the message and the Works
            through.
        args: The arguments that `configure_check` parsed.
        stdio: Where the message is read when it is not in a file and where the
            diagnostics are written.

    Returns:
        1 when a diagnostic is an error, and otherwise 0, so a warning never changes
        the exit code.

    Raises:
        TrailersError: If the file cannot be read or decoded.
        ConfigurationError: If the config cannot be read.
    """
    ...
