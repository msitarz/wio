# SPDX-License-Identifier: Apache-2.0
"""Check citations and find the commit that a review judged.

The command checks the record fields first. The gate check then validates
citations and resolves the reviewed commit before either command records
the resulting event.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.models.events import ReviewEvent
from wio.models.records import Finding
from wio.models.reviews import Accepted, Refusal
from wio.trailers.reviewed import reviewed_commit

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from wio.models.config import Config
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
    config: Config,
    known: tuple[frozenset[str], Mapping[str, str]],
    *,
    has_result: bool,
) -> tuple[list[Cite], list[Finding]]:
    """Check the `--cite` arguments of a review."""
    seen: set[str] = set()
    refusals = [
        _refusal(text, (known, seen), config, has_result=has_result) for text in raw
    ]
    findings = [
        Finding("malformed", refusal[0], text, number, refusal[1])
        for number, (text, refusal) in enumerate(zip(raw, refusals, strict=True), 1)
        if refusal is not None
    ]
    if findings:
        return [], findings
    return [Cite(*text.split("=", 1)) for text in raw], []


def _refusal(
    text: str,
    context: tuple[tuple[frozenset[str], Mapping[str, str]], set[str]],
    config: Config,
    *,
    has_result: bool,
) -> tuple[str, str] | None:
    """Say why one `--cite` value is refused, if it is, and remember its key."""
    key, _, result = text.partition("=")
    if not has_result:
        return ("--cite", "`--cite` needs a `--result`.")
    if not (key and result):
        return ("--cite", f"`{text}` is not `KEY=RESULT` with a key and a result.")
    if result not in config.gates.results:
        return (key, f"`{result}` is not a result of the config.")
    if key in context[1]:
        return (key, f"`{key}` is cited more than once.")
    context[1].add(key)
    return _unknown_key(key, context[0])


def _unknown_key(
    key: str, known: tuple[frozenset[str], Mapping[str, str]]
) -> tuple[str, str] | None:
    """Say why a cited key is neither an item of the Work nor a selected rule."""
    items, rules = known
    if key in items or key in rules:
        return None
    if "." in key:
        return (key, f"The stage does not select the rule `{key}`.")
    return (key, f"`{key}` is neither an item of the Work nor a qualified rule code.")


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
    return ReviewEvent(
        record["Wio-Work"],
        record["Wio-Action"],
        record["Wio-Stage"],
        commit,
        record["Wio-Judge"],
        record["Wio-Result"],
        {cite.key: cite.result for cite in cites},
        {cite.key: rules[cite.key] for cite in cites if cite.key in rules},
    )


def check_review_event(
    services: Services, fields: Sequence[tuple[str, str]], cites: Sequence[str]
) -> Accepted | Refusal:
    """Judge citations and find a reviewed commit after checking the fields.

    Args:
        services: Supplies config, Work items, selected rules and history.
        fields: The checked fields of the record in printing order.
        cites: The requested citations in argument order.

    Returns:
        An event if every check passed, or the first group's refusal lines.

    Raises:
        RuntimeError: The history port cannot find the repository.
        ValueError: The history port rejects the revision it was asked to read.
    """
    record = dict(fields)
    work, action, stage = record["Wio-Work"], record["Wio-Action"], record["Wio-Stage"]
    config = services.settings.load()
    selected = services.rules.selected(work, action, stage)
    items = services.contracts.items(work) or frozenset()
    cited, findings = check_cites(
        cites, config, (items, selected), has_result="Wio-Result" in record
    )
    if findings:
        return Refusal(tuple(f"error: {f.key}: {f.message}" for f in findings))
    commit = reviewed_commit(action, stage, services.history, config.trailers.reader)
    if commit is None:
        return Refusal(("error: Wio-Work: no reviewed commit was found",))
    return Accepted(review_event(record, commit, cited, selected))
