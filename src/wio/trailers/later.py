# SPDX-License-Identifier: Apache-2.0
"""The later check of `wio trailers`: a body or a range afterwards.

`wio trailers check [PATH]` checks a pull request body, and `wio trailers check
--ref-range RANGE` checks the commits of a range, long after their records were
written. A record that was valid then must not fail now, so this mode judges a
record's form and warns about the rest: it never asks whether a Work or an item
still exists, because Works are deleted later and the readers ignore unknown ids,
and it never requires a record, because a body or a commit of no Work has none. It
shares the check form with the commit-time mode of `wio.trailers.check`, which
chooses this mode when `--require` is absent, and it imports nothing from it: what
the two share is in `wio.trailers.report`. The mode composes the reading, the
judgment and the report, and the leaves that judge and read a range are stubbed.
"""

from dataclasses import replace
from typing import TYPE_CHECKING

from wio.formats import check_shape, read
from wio.trailers.report import by_line, read_message, write_diagnostics

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Sequence

    from wio.io.ports import History, Stdio
    from wio.models.commits import Commit
    from wio.models.config import Config
    from wio.models.diagnostics import Diagnostic
    from wio.models.records import Finding, Reading
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
    or an item is not looked up, and a record is not required. Both kinds of warning
    are judged together and sorted as one list.

    Args:
        message: The pull request body or the commit message.
        config: The config, for the reader, the names and the results.

    Returns:
        The diagnostics, each with the 1-based line number in the message as its
        `where`, sorted by that number as a number, then errors before warnings, then
        by message; none for a message with no record.
    """
    reader = config.trailers.reader
    reading, findings = read(message, reader), check_shape(message, reader)
    found = [
        *_shape_diagnostics(findings),
        *_name_warnings(reading, findings, config),
    ]
    return sorted(found, key=by_line)


def check_range(commits: Sequence[Commit], config: Config) -> list[Diagnostic]:
    """Judge the messages of the commits of a range.

    Each commit is judged as `check_afterwards` judges a message, with the reader of
    the config. The diagnostics of a commit are sorted with the key of
    `check_afterwards`, and then the `where` of each becomes the full id of the
    commit, a colon and the line in its message.

    Args:
        commits: The commits of the range, oldest first, as the `History` port gives
            them.
        config: The config.

    Returns:
        The diagnostics of each commit, in the order of the commits and sorted within
        a commit as `check_afterwards` sorts them.
    """
    return [
        replace(diagnostic, where=f"{commit.id}:{diagnostic.where}")
        for commit in commits
        for diagnostic in check_afterwards(commit.message, config)
    ]


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
        The exit code of the check: 1 for a body or a range with an error, and 0 for
        one with only warnings or none.

    Raises:
        TrailersError: If both a path and a range are given, if the file cannot be
            read or decoded, or if the `History` port refuses the range with a
            `ValueError` or cannot reach a repository with a `RuntimeError`, which
            is a usage error that exits 2.
        ConfigurationError: If the config cannot be read.
    """
    _one_input(args.path, args.ref_range)
    config = services.settings.load()
    if args.ref_range:
        commits = _commits_of(services.history, args.ref_range)
        return write_diagnostics(check_range(commits, config), stdio)
    message = read_message(services, args.path, stdio)
    return write_diagnostics(check_afterwards(message, config), stdio)


def _one_input(path: str | None, revision_range: str | None) -> None:
    """Refuse a call that names two inputs.

    Args:
        path: The path argument, or `None`.
        revision_range: The value of `--ref-range`, or `None`.

    Raises:
        TrailersError: If both are given, because a file and a range are read
            differently.
    """
    raise NotImplementedError


def _commits_of(history: History, text: str) -> Sequence[Commit]:
    """Ask the history for the commits that a range names.

    Args:
        history: The port that gives the commits of a range with their messages.
        text: The revision range exactly as the person wrote it.

    Returns:
        Each commit of the range, the oldest one first.

    Raises:
        TrailersError: If the port refuses the range with a `ValueError` or cannot
            reach a repository with a `RuntimeError`, with the port's message.
    """
    raise NotImplementedError


def _shape_diagnostics(findings: list[Finding]) -> list[Diagnostic]:
    """Turn the findings of the shape check into diagnostics.

    Args:
        findings: What `check_shape` found.

    Returns:
        An error for a `malformed` finding and a warning for an `invisible` or an
        `unknown-key` finding, each at the line of the finding.
    """
    raise NotImplementedError


def _name_warnings(
    reading: Reading, findings: list[Finding], config: Config
) -> list[Diagnostic]:
    """Warn about the names of the records that are not malformed.

    Args:
        reading: The records of the message.
        findings: What `check_shape` found, which says which records are malformed.
        config: The config, for the action names, the stage names and the results.

    Returns:
        A warning for each error of `validate_names` on a record that has no
        `malformed` finding, with the line of the field as its place.
    """
    raise NotImplementedError
