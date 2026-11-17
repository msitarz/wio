# SPDX-License-Identifier: Apache-2.0
"""The spec of the fold form of `wio trailers`: fold the records of a range.

A squash merge keeps only a pull request's body, so the records of its commits are
copied there, folded to what a reader needs: `wio trailers fold block <range>`
prints the folded records, and `wio trailers fold body <range>` reads a pull
request body on standard input and prints it with them at its end. `wio.cli`
dispatches on the first argument and wires the ports, and this module holds what
the form does, so it is run in a test with fakes of the ports. The records are
read with the reader of the config and written with the shared renderer, and the
form checks none of them, which the check commands do.

The stub is the spec until the wiring stage of the Work that builds the fold writes
the module `wio.trailers.fold` and deletes this stub, so the spec and the code
never coexist.
"""

from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from dataclasses import dataclass

from wio.io.ports import Stdio
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

    The records of each commit are read with `reader`, a list of Works is expanded
    to one record for each Work in the order written, and a `Wio-Work: none` record
    is dropped. A commit that a revert in the range takes back leaves no record,
    and a revert carries no record of its own: the revert line is `This reverts
    commit <id>.`, a revert of a revert restores the commit, and a revert of a
    commit outside the range is kept in `reverts`. The fold takes two steps, in
    this order. Consecutive records of the same Work, action and stage, with no
    other record between them, become one at the later position, with the items
    united in order of appearance and the latest result and judge. Then consecutive
    records that differ only in the Work become one record for a list of Works.
    Records that are not consecutive stay apart, because a record between two
    others can make the earlier one stale.

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
    ...

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
    ...

def fold_body(body: str, folded: Folded, reader: Reader) -> str | None:
    """Put the folded paragraphs at the end of a pull request body.

    The paragraphs that the body already ends with, which are record paragraphs and
    revert paragraphs at the end of it and no others, are taken off and replaced, so
    a record paragraph inside the prose stays where it is, and the older records
    that the body ends with are not kept beside the current ones.

    Args:
        body: The pull request body as the person wrote it, with the records of an
            earlier fold at its end or none.
        folded: The fold of the range.
        reader: The reader of the config, which finds the record paragraphs of the
            body.

    Returns:
        The prose unchanged, a blank line and the folded paragraphs, or `None` when
        the body already ends with exactly those paragraphs, so that a second run
        prints nothing.
    """
    ...

def configure_fold(parser: ArgumentParser) -> None:
    """Add the forms of `fold` to its parser.

    It does no I/O. `block` and `body` each take the revision range, a git revision
    range such as `main..HEAD`, which is provisional as the parent's third
    assumption says, and argparse refuses a form that is not one of the two.

    Args:
        parser: The parser that `wio.cli` created for `fold`.
    """
    ...

def run_fold(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Fold a range and print the block or the body.

    The commits of the range come oldest first from the `History` port. A range
    that git does not resolve raises a `TrailersError` before anything is written,
    so a failed fold prints nothing. `block` writes `render_block` and `body` reads
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
    ...
