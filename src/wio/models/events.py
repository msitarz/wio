# SPDX-License-Identifier: Apache-2.0
"""The types for the events that sessions leave in the event log.

The event types carry the fields of a context bundle or a review. The
envelope carries the session and time information shared by both events.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(frozen=True)
class ContextEvent:
    """A session entered a stage and received a context bundle.

    It records ids, hashes and codes, and never prompts, code or free text.

    Attributes:
        work: The id of the Work entering the stage.
        action: The action that contains the stage.
        stage: The stage the session entered.
        bundle: The opaque id of the context bundle.
        size: The length of the bundle in bytes.
        rules: The hash of each rule file, keyed by qualified rule code in
            bundle order.
        start: The starting commit of a gate session, or `None` for other stages.
        dirty: Whether the repository was dirty for a gate session, or `None`
            for other stages.
    """

    work: str
    action: str
    stage: str
    bundle: str
    size: int
    rules: Mapping[str, str]
    start: str | None
    dirty: bool | None


@dataclass(frozen=True)
class Envelope:
    """The context that accompanies one recorded event.

    Attributes:
        time: Finite, nonnegative seconds since the Unix epoch in UTC.
        directory: The working directory of the session.
        harness: The chosen harness name, if available.
        session: The chosen harness's session id, if available.
        parent: The parent session id, if available.
        matches: The names of matching harnesses in config order.
        ids: The recorded environment variable names and their values.
    """

    time: float
    directory: str
    harness: str | None
    session: str | None
    parent: str | None
    matches: tuple[str, ...]
    ids: Mapping[str, str]


@dataclass(frozen=True)
class ReviewEvent:
    """A gate finished and judged an artifact.

    It records the Work, the action, the stage, the reviewed commit, the judge
    and the results, and never prompts, code or free text. It is immutable.

    Attributes:
        work: The id of the Work.
        action: The action of the gate.
        stage: The stage that is the gate.
        commit: The full sha of the commit that the review judged.
        judge: Who judged, `agent` or `human`.
        result: The overall result, in the config's vocabulary.
        cited: The result of each item id or rule code that the review cited,
            in the order the citations were given; what is not cited was not
            judged.
        hashes: The hash of the file of each cited rule, by its qualified code, as
            the `context` event records it; an item has none.
    """

    work: str
    action: str
    stage: str
    commit: str
    judge: str
    result: str
    cited: Mapping[str, str]
    hashes: Mapping[str, str]


type Event = ContextEvent | ReviewEvent
"""Either kind of event that the event log accepts."""
