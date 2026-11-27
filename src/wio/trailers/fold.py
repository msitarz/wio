# SPDX-License-Identifier: Apache-2.0
"""The fold form of `wio trailers`: fold the records of a range.

A squash merge keeps only a pull request's body, so the records of its commits are
copied there, folded to what a reader needs: `wio trailers fold block <range>`
prints the folded records, and `wio trailers fold body <range>` reads a pull
request body on standard input and prints it with them at its end. `wio.cli`
dispatches on the first argument and wires the ports, and this module holds what
the form does, so it is run in a test with fakes of the ports. The records are
read with the reader of the config and written with the shared renderer, and the
form checks none of them, which the check commands do. The form reads the
history, settles the reverts, folds the records, lays them out and cuts a body.
"""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.formats import read, render
from wio.trailers.errors import TrailersError

_REVERT = re.compile(r"^This reverts commit ([0-9a-fA-F]+)[.,]", re.MULTILINE)
"""A line that `git revert` writes, with the id of the commit it takes back, which
ends with a comma when the revert is of a merge, as `git revert -m` writes it."""
_TRAILER = re.compile(r"[A-Za-z][A-Za-z0-9-]*:.*")
"""A line of a record paragraph: a `Key: value` trailer."""
_REVERT_PARAGRAPH = re.compile(r"This reverts commit [0-9a-fA-F]+\.")
"""A paragraph that only says that a commit was reverted."""

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
    """Fold the records of a range of commits."""
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
        The prose, without the whitespace after it and otherwise unchanged, a blank
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
    """Read the commits of a range from the history."""
    try:
        return history.history(revision_range)
    except ValueError as error:
        message = str(error)
        raise TrailersError(message) from error


def _position(pair: tuple[int, str]) -> int:
    """Give the position that orders a revert of work outside the range."""
    return pair[0]


@dataclass
class _Settled:
    """What the reverts of a range have settled so far."""

    dropped: set[int]
    neutral: set[int]
    outside: list[tuple[int, str]]

    def settle(
        self, commits: Sequence[Commit], reverts: dict[int, tuple[str, ...]], index: int
    ) -> None:
        """Settle one revert, unless a later revert took it back.

        Args:
            commits: The commits of the range, oldest first.
            reverts: The ids that each revert names, by position.
            index: The position of the revert.
        """
        if index in self.neutral:
            return
        for written in reverts[index]:
            target = _resolve(commits, index, written)
            self.file(index, written, target, revert=target in reverts)

    def shown(self) -> tuple[str, ...]:
        """Give the reverts of work outside the range, in the order of the history.

        Returns:
            The ids as they were written.
        """
        return tuple(written for _, written in sorted(self.outside, key=_position))

    def file(
        self, index: int, written: str, target: int | None, *, revert: bool
    ) -> None:
        """Record what one revert line took back.

        Args:
            index: The position of the revert.
            written: The id on the line, as written.
            target: The position of the commit of the range it names, or `None`.
            revert: Whether that commit is itself a revert.
        """
        if target is None:
            self.outside.append((index, written))
        elif revert:
            self.neutral.add(target)
        else:
            self.dropped.add(target)


def _apply_reverts(commits: Sequence[Commit]) -> tuple[list[Commit], tuple[str, ...]]:
    """Settle the reverts of a range."""
    reverts = _reverts_of(commits)
    state = _Settled(set(reverts), set(), [])
    for index in sorted(reverts, reverse=True):
        state.settle(commits, reverts, index)
    kept = [c for i, c in enumerate(commits) if i not in state.dropped]
    return kept, state.shown()


def _reverts_of(commits: Sequence[Commit]) -> dict[int, tuple[str, ...]]:
    """Find the reverts among the commits of a range."""
    found = {i: _written(commit) for i, commit in enumerate(commits)}
    return {i: ids for i, ids in found.items() if ids}


def _written(commit: Commit) -> tuple[str, ...]:
    """Find the ids that a commit says it reverts."""
    return tuple(_REVERT.findall(commit.message))


def _resolve(commits: Sequence[Commit], index: int, written: str) -> int | None:
    """Find the commit of the range that a revert names."""
    found = [i for i in range(index) if commits[i].id.startswith(written.lower())]
    return found[0] if len(found) == 1 else None


def _expand(commit: Commit, reader: Reader) -> list[FoldedRecord]:
    """Read the records of a commit, one for each Work."""
    return [
        folded
        for record in read(commit.message, reader).records
        for folded in _for_each_work(
            {t.key: t.value for t in reversed(record.trailers)}
        )
    ]


def _for_each_work(values: dict[str, str]) -> list[FoldedRecord]:
    """Make a folded record for each Work that a record names."""
    work = values.get("Wio-Work", "none")
    items = values.get("Wio-Items")
    return [
        FoldedRecord(
            (one,),
            values.get("Wio-Action", ""),
            values.get("Wio-Stage", ""),
            tuple(items.split(", ")) if items else (),
            values.get("Wio-Result"),
            values.get("Wio-Judge"),
        )
        for one in ([] if work == "none" else work.split(", "))
    ]


def _merge(records: list[FoldedRecord]) -> list[FoldedRecord]:
    """Merge the consecutive records of the fold, in its two steps."""
    return _by_work(_by_stage(records))


def _by_stage(records: list[FoldedRecord]) -> list[FoldedRecord]:
    """Merge each run of records of one Work, action and stage."""
    merged: list[FoldedRecord] = []
    for record in records:
        if merged and _same_stage(merged[-1], record):
            merged[-1] = _united(merged[-1], record)
        else:
            merged.append(record)
    return merged


def _same_stage(left: FoldedRecord, right: FoldedRecord) -> bool:
    """Tell whether two records are of one Work, action and stage."""
    return (left.works, left.action, left.stage) == (
        right.works,
        right.action,
        right.stage,
    )


def _united(earlier: FoldedRecord, later: FoldedRecord) -> FoldedRecord:
    """Make one record of two of one Work, action and stage."""
    items = earlier.items + tuple(i for i in later.items if i not in earlier.items)
    return FoldedRecord(
        later.works,
        later.action,
        later.stage,
        items,
        later.result or earlier.result,
        later.judge or earlier.judge,
    )


def _by_work(records: list[FoldedRecord]) -> list[FoldedRecord]:
    """Merge each run of records that differ only in the Work."""
    merged: list[FoldedRecord] = []
    for record in records:
        last = merged[-1] if merged else None
        if last and record.works[0] not in last.works and _same_but_work(last, record):
            merged[-1] = FoldedRecord(
                (*last.works, *record.works),
                record.action,
                record.stage,
                record.items,
                record.result,
                record.judge,
            )
        else:
            merged.append(record)
    return merged


def _same_but_work(left: FoldedRecord, right: FoldedRecord) -> bool:
    """Tell whether two records differ in nothing but the Work."""
    return (left.action, left.stage, left.items, left.result, left.judge) == (
        right.action,
        right.stage,
        right.items,
        right.result,
        right.judge,
    )


def _paragraphs(folded: Folded) -> list[str]:
    """Lay out each paragraph of the block."""
    reverts = [f"This reverts commit {commit}.\n" for commit in folded.reverts]
    return [*reverts, *(_laid_out(record) for record in folded.records)]


def _laid_out(record: FoldedRecord) -> str:
    """Lay out one folded record with the shared renderer."""
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
    """Cut a body into its prose and the paragraphs it ends with."""
    lines = body.splitlines(keepends=True)
    paragraphs: list[str] = []
    end = len(lines)
    while (span := _last_paragraph(lines, end)) is not None:
        first, last = span
        text = [line.rstrip() for line in lines[first:last]]
        if not _is_trailing(text):
            break
        paragraphs.insert(0, "\n".join(text) + "\n")
        end = first
    return "".join(lines[:end]).rstrip(), "\n".join(paragraphs)


def _last_paragraph(lines: list[str], end: int) -> tuple[int, int] | None:
    """Find the last paragraph among the first lines of a body."""
    last = end
    while last > 0 and not lines[last - 1].strip():
        last -= 1
    first = last
    while first > 0 and lines[first - 1].strip():
        first -= 1
    return (first, last) if last > first else None


def _is_trailing(paragraph: list[str]) -> bool:
    """Tell whether a paragraph is one that a fold puts at the end of a body."""
    if len(paragraph) == 1 and _REVERT_PARAGRAPH.fullmatch(paragraph[0]):
        return True
    return all(_TRAILER.fullmatch(line) for line in paragraph) and any(
        line.startswith("Wio-") for line in paragraph
    )
