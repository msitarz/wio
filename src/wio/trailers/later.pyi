# SPDX-License-Identifier: Apache-2.0
"""The spec of the later check of `wio trailers`: a body or a range afterwards.

`wio trailers check [PATH]` checks a pull request body, and `wio trailers check
--ref-range RANGE` checks the commits of a range, long after their records were
written. A record that was valid then must not fail now, so this mode judges a
record's form and warns about the rest: it never asks whether a Work or an item
still exists, because Works are deleted later and the readers ignore unknown ids,
and it never requires a record, because a body or a commit of no Work has none. It
shares the check form with the commit-time mode of `wio.trailers.check`, which is
changed when this mode is wired: `configure_check` also adds the option
`--ref-range` and no longer requires `--require`, and `run_check` runs the
commit-time mode for `--require` and this mode otherwise, with a call that gives
`--require` and `--ref-range`, or a path and `--ref-range`, a usage error.

The stub is the spec until the wiring stage of the Work that builds the later check
writes the module `wio.trailers.later` and deletes this stub, so the spec and the
code never coexist.
"""

from argparse import Namespace
from collections.abc import Sequence

from wio.io.ports import Stdio
from wio.models.commits import Commit
from wio.models.config import Config
from wio.models.diagnostics import Diagnostic
from wio.trailers import Services

def check_afterwards(message: str, config: Config) -> list[Diagnostic]:
    """Judge a body or a message that was written some time ago.

    The records are read with the reader of the config. `check_shape` judges each
    record's own form: a `malformed` finding is an error, and an `invisible` or an
    `unknown-key` finding is a warning, so a line that the reader cannot see or a key
    that the engine does not define is reported and never fails the check. A finding
    belongs to the record whose lines hold its `number`. Every record that has no
    `malformed` finding is then judged by `validate_names` against the config, with
    the fields carrying their lines, and each error it returns is turned into a
    warning, because the config may have changed since the record was written. A Work
    or an item is not looked up, and a record is not required.

    Args:
        message: The pull request body or the commit message.
        config: The config, for the reader, the names and the results.

    Returns:
        The diagnostics, each with the 1-based line number in the message as its
        `where`, sorted by that number as a number, then errors before warnings, then
        by message; none for a message with no record.
    """
    ...

def check_range(commits: Sequence[Commit], config: Config) -> list[Diagnostic]:
    """Judge the messages of the commits of a range.

    Each commit is judged as `check_afterwards` judges a message, with the reader of
    the config, and the `where` of a diagnostic is the full id of the commit, a
    colon and the line in its message.

    Args:
        commits: The commits of the range, oldest first, as the `History` port gives
            them.
        config: The config.

    Returns:
        The diagnostics of each commit, in the order of the commits and sorted within
        a commit as `check_afterwards` sorts them.
    """
    ...

def run_later(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Check a body or a range and report each diagnostic.

    With `--ref-range` the commits of the range come from the `History` port,
    oldest first, and otherwise the body is read from the file `path`, or from
    standard input when it is `-` or absent. Each diagnostic is written to standard
    error as `<severity>: <where>: <message>`, one to a line, in the order above, and
    nothing is written to standard output.

    Args:
        services: The ports the form reads the config, the body and the history
            through.
        args: The arguments that `configure_check` parsed, of which `ref_range` and
            `path` are read here.
        stdio: Where the body is read when it is not in a file and where the
            diagnostics are written.

    Returns:
        1 when a diagnostic is an error, and otherwise 0, so a warning never changes
        the exit code.

    Raises:
        TrailersError: If both a path and a range are given, if the file cannot be
            read or decoded, or if the `History` port refuses the range with a
            `ValueError` or cannot reach a repository with a `RuntimeError`, which
            is a usage error that exits 2.
        ConfigurationError: If the config cannot be read.
    """
    ...
