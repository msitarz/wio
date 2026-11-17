# SPDX-License-Identifier: Apache-2.0
"""The types for the events that sessions leave in the event log.

The stubs are the spec until the wiring stage of the Work that records a gate's
result replaces them with a `.py` of the same annotations, so the spec and the code
never coexist. `ReviewEvent` declares the fields that `wio trailers --result`
writes; `ContextEvent` declares none, and the Work that implements `wio log`
extends both.
"""

from collections.abc import Mapping
from dataclasses import dataclass

@dataclass(frozen=True)
class ContextEvent:
    """A session entered a stage and received a context bundle.

    It records ids, hashes and codes, and never prompts, code or free text.
    """

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
