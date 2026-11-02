# SPDX-License-Identifier: Apache-2.0
"""The types for the events that sessions leave in the event log.

The stubs are the spec until the Work that implements `wio log` replaces them
with a `.py` of the same annotations. They declare no fields: the event
format is that Work's to settle.
"""

class ContextEvent:
    """A session entered a stage and received a context bundle.

    It records ids, hashes and codes, and never prompts, code or free text.
    """

class ReviewEvent:
    """A gate finished and judged an artifact.

    It records the Work, the action, the stage, the reviewed commit, the judge
    and the results, and never prompts, code or free text.
    """

type Event = ContextEvent | ReviewEvent
"""Either kind of event that the event log accepts."""
