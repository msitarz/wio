# SPDX-License-Identifier: Apache-2.0
"""The finder of the commit a gate reviewed.

A gate's own commits carry only the gate's record and sit on top of the artifact
the gate judged, so the commit that a review saw is the first commit, from `HEAD`
down, that holds something else. `reviewed_commit` finds it from the history alone,
so a later reader of a record knows which artifact the review judged. It never
looks at the `context` event and has no override; the gate form of `wio trailers`
composes it. The finder walks the history and asks the leaf that judges a commit,
which reads the records of its message.
"""

from typing import TYPE_CHECKING

from wio.formats import read

if TYPE_CHECKING:
    from wio.io.ports import History
    from wio.models.config import Reader
    from wio.models.records import Record


def reviewed_commit(
    action: str, stage: str, history: History, reader: Reader
) -> str | None:
    """Find the commit that a gate reviewed, under the gate's own commits.

    The commits of `History.first_parents("HEAD")` are walked newest first, each
    message is read with `reader`, and the first commit that is not a pure gate
    commit is the reviewed one. A pure gate commit has at least one record, and
    every record of it has the action `action` and the stage `stage`, for any Work
    or list of Works. A commit with no record, a commit whose only record is
    `Wio-Work: none`, a commit with a record of another action or stage beside the
    gate's, and a commit whose gate record the reader cannot see are not pure gate
    commits, so each is the reviewed commit. The walk follows the first parents, as
    the `History` port gives them, and reads nothing else.

    Args:
        action: The action of the gate, such as `define`.
        stage: The stage of the gate, such as `review-contract`.
        history: The port that gives the first-parent ancestors of `HEAD`, newest
            first.
        reader: The reader of the config, which decides what a record is.

    Returns:
        The full id of the reviewed commit, or `None` when every commit is a pure
        gate commit or the history is empty.

    Raises:
        RuntimeError: If the working directory is not in a repository, as the
            `History` port raises it.
        ValueError: If the `History` port rejects the revision, as it raises it.
    """
    gate = (action, stage)
    for commit in history.first_parents("HEAD"):
        if not _is_gate_commit(commit.message, gate, reader):
            return commit.id
    return None


def _is_gate_commit(message: str, gate: tuple[str, str], reader: Reader) -> bool:
    """Tell whether a commit message carries only the gate's own records.

    Args:
        message: The full message of the commit.
        gate: The action and the stage of the gate.
        reader: The reader of the config, which decides what a record is.

    Returns:
        `True` when the message has at least one record and every record has the
        gate's action and stage, whichever Works it is for, and `False` for a
        message with no record, with a record of `Wio-Work: none`, or with a record
        of another action or stage, and for a gate record that the reader cannot
        see.
    """
    records = read(message, reader).records
    return bool(records) and all(_belongs_to(record, gate) for record in records)


def _belongs_to(record: Record, gate: tuple[str, str]) -> bool:
    """Tell whether a record is the record of a gate.

    Args:
        record: A record of the message.
        gate: The action and the stage of the gate.

    Returns:
        `True` when the record names the gate's action and stage, for any Work or
        list of Works, and `False` for one that lacks either key, such as a record
        of `Wio-Work: none`.
    """
    seen = {trailer.key: trailer.value for trailer in record.trailers}
    return (seen.get("Wio-Action"), seen.get("Wio-Stage")) == gate
