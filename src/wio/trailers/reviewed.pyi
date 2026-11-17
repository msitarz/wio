# SPDX-License-Identifier: Apache-2.0
"""The spec of the finder of the commit a gate reviewed.

A gate's own commits are empty and sit on top of the artifact the gate judged, so
the commit that a review saw is the first commit, from `HEAD` down, that holds
something else. `reviewed_commit` finds it from the history alone, so a later
reader of a record knows which artifact the review judged. It never looks at the
`context` event and has no override; the gate form of `wio trailers` composes it.

The stub is the spec until the wiring stage of the Work that builds the finder
writes the module `wio.trailers.reviewed` and deletes this stub, so the spec and
the code never coexist.
"""

from wio.io.ports import History
from wio.models.config import Reader

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
    """
    ...
