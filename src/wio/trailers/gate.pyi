# SPDX-License-Identifier: Apache-2.0
"""The spec of the gate form of `wio trailers`: record a gate's result.

`wio trailers <work> <action> <stage> --result RESULT [--judge JUDGE] [--cite
KEY=RESULT]...` extends the write form of `wio.trailers.write`. After the fields of
the record hold, the form checks what the review cites, finds the commit it judged,
writes one `review` event and then prints the record, so a review leaves a trace of
what it cited, of the commit it saw and of who judged. A gate that needs a human
changes nothing here: the judge is recorded as given, `agent` by default, so a
reviewer session and the driver each record a result and an event. The form
refuses without writing the event or printing the record, and a failing sink is the
sink's warning and never the command's failure.

`configure_write` also gains the meaning of `--cite`, which the print leaf accepts and
ignores, and `run_write` calls `run_review` once every field holds and has no error,
only when `--result` or `--cite` is given. `wio.trailers.Services` gains the fields
`rules`, the `StageRules` port, and `events`, the `EventSink` port. The print leaf's
scenario that a cited item is ignored is replaced by the scenarios of this form.

The stub is the spec until the wiring stage of the Work that records a gate's result
writes the module `wio.trailers.gate` and deletes this stub, so the spec and the code
never coexist.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from wio.io.ports import Stdio
from wio.models.config import Config
from wio.models.events import ReviewEvent
from wio.models.records import Finding
from wio.trailers import Services

@dataclass(frozen=True)
class Cite:
    """One item or rule that a review cited, with its result.

    It is immutable.

    Attributes:
        key: An item id of the Work, or the qualified code of a rule that the stage
            selects.
        result: The result, which is in the config's `gates.results`.
    """

    key: str
    result: str

def check_cites(
    raw: Sequence[str],
    has_result: bool,
    config: Config,
    known: tuple[frozenset[str], Mapping[str, str]],
) -> tuple[list[Cite], list[Finding]]:
    """Check the `--cite` arguments of a review.

    A key is an item id when the Work has that item, and otherwise it must be a
    qualified `ruleset.CODE` that the stage selects, which is stricter than the
    config choosing it. Every refusal is a `malformed` finding whose `key` is the
    name that the message prints after `error: `: `--cite` for a cite with no `=`,
    for an empty key or result and for `--cite` without `--result`, and the cite's
    own key otherwise. The refusals are a cite with no `=`, an empty key or result, a
    key repeated, a result outside `gates.results`, an item the Work lacks, a code
    that is not qualified or that the stage does not select, and `--cite` without
    `--result`; a cite that is not refused is checked as the others are, and one
    finding is given for each cite at most, in the order given.

    Args:
        raw: The values of `--cite`, each `KEY=RESULT`, in the order given.
        has_result: Whether `--result` was given.
        config: The config, for `gates.results`.
        known: The item ids of the Work and the rules that the stage selects for it,
            each qualified code with the hash of its file.

    Returns:
        The cites in the order given and no finding when every cite holds, and no
        cites and the findings otherwise.
    """
    ...

def review_event(
    record: Mapping[str, str],
    commit: str,
    cites: Sequence[Cite],
    rules: Mapping[str, str],
) -> ReviewEvent:
    """Build the `review` event of a recorded result.

    Args:
        record: The fields of the record, of which `Wio-Work`, `Wio-Action`,
            `Wio-Stage`, `Wio-Result` and `Wio-Judge` are read.
        commit: The full sha of the commit that the review judged.
        cites: The cites that `check_cites` accepted.
        rules: The rules that the stage selects, each with its hash, which a cited
            rule takes as its own; an item has no hash.

    Returns:
        The event, with each cited key and its result in the order given, and the
        hash of each cited rule.
    """
    ...

def run_review(
    services: Services,
    fields: Sequence[tuple[str, str]],
    cites: Sequence[str],
    stdio: Stdio,
) -> int:
    """Check what a review cites, find what it judged and write its event.

    It runs after the fields of the record have been checked and refused nothing.
    The cites are checked first, with the items of the Work from the `Contracts`
    port and the rules from the `StageRules` port, then the reviewed commit is found
    by `reviewed_commit` from the action and the stage with the reader of the
    config; the first of the two that finds something writes its findings as
    `error: <name>: <message>` to standard error and stops. A history with no
    reviewed commit writes `error: Wio-Work: no reviewed commit was found`. Nothing
    is written to standard output. The event is written once, to the `EventSink`
    port, only after every check passed and after a warning, and never on a
    refusal; a sink that fails reports its own warning on standard error, which
    changes nothing here.

    Args:
        services: The ports the form reads the Works, the rules and the history
            through, and writes the event to.
        fields: The key and the value of each field of the record, in the order of
            the keys of a record.
        cites: The values of `--cite` as given.
        stdio: Where the findings are written.

    Returns:
        0 when the event was written, and 1 when a cite or the reviewed commit was
        refused.

    Raises:
        RuntimeError: If the working directory is not in a repository, as the
            `History` port raises it.
    """
    ...
