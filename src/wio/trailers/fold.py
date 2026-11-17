# SPDX-License-Identifier: Apache-2.0
"""The fold form of `wio trailers`: fold the records of a range.

A squash merge keeps only a pull request's body, so the records of its commits are
copied there, folded to what a reader needs: `wio trailers fold block <range>`
prints the folded records, and `wio trailers fold body <range>` reads a pull
request body on standard input and prints it with them at its end. `wio.cli`
dispatches on the first argument and wires the ports, and this module holds what
the form does, so it is run in a test with fakes of the ports. The records are
read with the reader of the config and written with the shared renderer, and the
form checks none of them, which the check commands do. The form composes the
reading of the history, the fold and the layout, and the leaves that settle the
reverts, merge the records and cut a body are stubbed.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.formats import render
from wio.trailers.errors import TrailersError

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace
    from collections.abc import Sequence

    from wio.io.ports import History, Stdio
    from wio.models.commits import Commit
    from wio.models.config import Reader
    from wio.trailers import Services


@dataclass(frozen=True)
class FoldedRecord:
    """One record of the fold, for one Work or for a list of Works that share it.

    It is immutable.

    Attributes:
        works: The ids of the Works, in the order of the history, one for a record
            of one Work.
        action: The action of the record.
        stage: The stage of the record.
        items: The item ids, in the order of their first appearance.
        result: The latest result of the stage, or `None` for a stage with none.
        judge: The latest judge, or `None` for a record that has none.
    """

    works: tuple[str, ...]
    action: str
    stage: str
    items: tuple[str, ...]
    result: str | None
    judge: str | None


@dataclass(frozen=True)
class Folded:
    """What the fold of a range holds.

    It is immutable.

    Attributes:
        reverts: The commits that were reverted by a commit of the range and are
            outside it, each as the revert wrote it, in the order of the history,
            so that a revert of work that is not in the range stays visible.
        records: The folded records, in the order of the history.
    """

    reverts: tuple[str, ...]
    records: tuple[FoldedRecord, ...]


def fold_commits(commits: Sequence[Commit], reader: Reader) -> Folded:
    """Fold the records of a range of commits.

    The reverts are settled first. The id on a line `This reverts commit <id>.` names
    a commit of the range when it is a prefix of the commit's id, so an abbreviated
    id counts, and a revert is a commit that has such a line. A revert is taken back
    by a later revert that names it, and a commit that an untaken revert names is
    taken back too, and the commits taken back and the reverts are dropped, whatever
    records their messages hold, before anything is folded, so that the neighbors of
    a dropped commit become consecutive. A revert of a commit outside the range is
    kept in `reverts` as the id was written, unless a later revert in the range takes
    that revert back.

    Then the records of each remaining commit are read with `reader`, a list of
    Works is expanded to one record for each Work in the order written, and a
    `Wio-Work: none` record is dropped. The fold takes two steps, in this order.
    Consecutive records of the same Work, action and stage, with no other record
    between them, become one at the later position, with the items united in order
    of appearance and the result and the judge of the later record, or the earlier
    one's when the later has none. Then consecutive records that differ only in the
    Work, which have the same action, stage, items, result and judge, become one
    record for a list of Works. Records that are not consecutive stay apart,
    because a record between two others can make the earlier one stale.

    The fold is a function of the commits, so folding the same range again gives
    the same value. It judges no record: a record that the check would refuse has
    no defined fold.

    Args:
        commits: The commits of the range, oldest first, as the `History` port
            gives them.
        reader: The reader of the config, which finds the records of a message.

    Returns:
        The folded records and the reverts of work outside the range.
    """
    kept, reverts = _apply_reverts(commits)
    expanded = [record for commit in kept for record in _expand(commit, reader)]
    return Folded(reverts, tuple(_merge(expanded)))


def render_block(folded: Folded) -> str:
    """Lay out the paragraphs that a pull request body ends with.

    Args:
        folded: The fold of a range.

    Returns:
        The paragraph `This reverts commit <id>.` for each revert of work outside
        the range, then each folded record as the shared renderer lays it out,
        each paragraph separated from the next by one blank line and the text
        ending with one newline; an empty string when there is nothing to show.
    """
    return "\n".join(_paragraphs(folded))


def fold_body(body: str, folded: Folded) -> str | None:
    """Put the folded paragraphs at the end of a pull request body.

    The paragraphs that the body already ends with, which are record paragraphs and
    revert paragraphs at the end of it and no others, are taken off and replaced, so
    a record paragraph inside the prose stays where it is, and the older records
    that the body ends with are not kept beside the current ones. They are found by
    their shape and never by the reader of the config: a record paragraph is one
    whose every line is a `Key: value` trailer with a `Wio-` key, and a revert
    paragraph is exactly `This reverts commit <id>.`, because a folded body holds
    several paragraphs, which the `git` reader does not read.

    Args:
        body: The pull request body as the person wrote it, with the records of an
            earlier fold at its end or none.
        folded: The fold of the range.

    Returns:
        The prose, without the line ends after it and otherwise unchanged, a blank
        line and the folded paragraphs, or `None` when the body already ends with
        exactly those paragraphs, so that a second run prints nothing, which is also
        the case for a body that ends with none when the fold has none.
    """
    prose, tail = _split_body(body)
    block = render_block(folded)
    if tail == block:
        return None
    return "\n\n".join(part for part in (prose, block) if part)


def configure_fold(parser: ArgumentParser) -> None:
    """Add the forms of `fold` to its parser.

    It does no I/O. The form is chosen by the required subcommand `block` or `body`,
    stored as `fold_form`, and each takes the revision range, a git revision
    range such as `main..HEAD`, stored as `range`, which is provisional as the parent's
    third assumption says, and argparse refuses a form that is not one of the two.

    Args:
        parser: The parser that `wio.cli` created for `fold`.
    """
    forms = parser.add_subparsers(dest="fold_form", required=True, metavar="<form>")
    for name in ("block", "body"):
        form = forms.add_parser(name, help=_HELP[name], description=_HELP[name])
        form.add_argument("range", help="A git revision range, such as main..HEAD.")


_HELP = {
    "block": "Print the folded records of a range of commits.",
    "body": "Print a pull request body from standard input with the folded records.",
}
"""What `--help` says of each form."""


def run_fold(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Fold a range and print the block or the body.

    The commits of the range come oldest first from the `History` port. A range
    that git does not resolve, which the port refuses with a `ValueError`, raises a
    `TrailersError` before anything is written, so a failed fold prints nothing. A
    working directory outside a repository is the port's `RuntimeError`, which is not
    caught. `block` writes `render_block` and `body` reads
    the body from standard input and writes `fold_body`, which is nothing when the
    body already ends with the folded paragraphs.

    Args:
        services: The ports the form reads the config and the history through.
        args: The arguments that `configure_fold` parsed.
        stdio: Where the body is read and the output is written.

    Returns:
        0 when the fold is written, or when `body` has nothing to add.

    Raises:
        TrailersError: If the range does not resolve.
        ConfigurationError: If the config cannot be read.
    """
    config = services.settings.load()
    commits = _commits(services.history, args.range)
    folded = fold_commits(commits, config.trailers.reader)
    if args.fold_form == "block":
        stdio.stdout.write(render_block(folded))
        return 0
    text = fold_body(stdio.stdin.read(), folded)
    if text is not None:
        stdio.stdout.write(text)
    return 0


def _commits(history: History, revision_range: str) -> Sequence[Commit]:
    """Read the commits of a range from the history.

    Args:
        history: The port that lists the commits of a range.
        revision_range: The range as written.

    Returns:
        The commits oldest first.

    Raises:
        TrailersError: If the port refuses the range, with the port's message.
    """
    try:
        return history.history(revision_range)
    except ValueError as error:
        message = str(error)
        raise TrailersError(message) from error


def _apply_reverts(commits: Sequence[Commit]) -> tuple[list[Commit], tuple[str, ...]]:
    """Settle the reverts of a range.

    Args:
        commits: The commits of the range, oldest first.

    Returns:
        The commits that are neither taken back nor reverts, in order, and the ids of
        the reverts of commits outside the range as they were written.
    """
    raise NotImplementedError


def _expand(commit: Commit, reader: Reader) -> list[FoldedRecord]:
    """Read the records of a commit, one for each Work.

    Args:
        commit: A commit that is kept.
        reader: The reader of the config.

    Returns:
        A record for each Work that each record of the message names, in the order
        written, none for a `Wio-Work: none` record.
    """
    raise NotImplementedError


def _merge(records: list[FoldedRecord]) -> list[FoldedRecord]:
    """Merge the consecutive records of the fold, in its two steps.

    Args:
        records: The records in the order of the history, one for each Work.

    Returns:
        The records after the first step, which merges each run of one Work, action
        and stage at its last position, and the second, which merges each run of
        records that have one action, stage, items, result and judge and differ
        only in the Work into one record for a list of Works.
    """
    raise NotImplementedError


def _paragraphs(folded: Folded) -> list[str]:
    """Lay out each paragraph of the block.

    Args:
        folded: The fold of a range.

    Returns:
        The revert paragraphs and then the records as `render` lays them out, each
        ending with one newline.
    """
    reverts = [f"This reverts commit {commit}.\n" for commit in folded.reverts]
    return [*reverts, *(_laid_out(record) for record in folded.records)]


def _laid_out(record: FoldedRecord) -> str:
    """Lay out one folded record with the shared renderer.

    Args:
        record: A folded record.

    Returns:
        The paragraph, with the Works and the items joined by a comma and one space
        and no line for a result or a judge that the record lacks.
    """
    fields = {
        "Wio-Work": ", ".join(record.works),
        "Wio-Action": record.action,
        "Wio-Stage": record.stage,
        "Wio-Items": ", ".join(record.items),
        "Wio-Result": record.result,
        "Wio-Judge": record.judge,
    }
    return render({key: value for key, value in fields.items() if value})


def _split_body(body: str) -> tuple[str, str]:
    """Cut a body into its prose and the paragraphs it ends with.

    Args:
        body: A pull request body.

    Returns:
        The prose without the line ends after it, and the trailing record and
        revert paragraphs laid out as `render_block` lays out a block.
    """
    raise NotImplementedError
