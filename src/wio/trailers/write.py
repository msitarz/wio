# SPDX-License-Identifier: Apache-2.0
"""The write form of `wio trailers`: print a checked record.

`wio trailers <work> <action> <stage>` prints the record for a Work, an action and
a stage, with optional item ids, a result and a judge, when every field holds, and
nothing when one does not. `wio.cli` dispatches on the first argument and wires
the ports, and this module holds what the form does, so the form is run in a test
with fakes of the ports. The form composes `render`, `check_shape` and
`validate_record`, and for a result or a cite the review of
`wio.trailers.gate`, which records what the gate judged.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.formats import check_shape, render
from wio.models.records import Finding
from wio.models.reviews import Accepted, Refusal
from wio.trailers.errors import TrailersError
from wio.trailers.gate import check_review_event
from wio.trailers.validation import Field, validate_record

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace
    from collections.abc import Sequence

    from wio.io.ports import Stdio
    from wio.models.config import Config
    from wio.ports import EventSink
    from wio.trailers import Services


_POSITIONALS = {
    "work": "Id of the Work the record is for.",
    "action": "The action the stage belongs to.",
    "stage": "The stage the commit works on.",
}
"""The positional arguments and what `--help` says of each."""
_OPTIONS = {
    "items": "Item ids, separated by a comma.",
    "result": "The result of a gate.",
    "judge": "Who judged a gate: human or agent.",
}
"""The options that take one value and what `--help` says of each."""
_CITE = "An item id or a rule code and its result, as KEY=RESULT."


@dataclass(frozen=True)
class TrailersReviewChecker:
    """The review checker backed by the ports that trailers uses.

    Attributes:
        services: The settings, contracts, rules and repository history.
    """

    services: Services

    def check(
        self,
        work: str,
        action: str,
        stage: str,
        result: str,
        judge: str,
        cites: Sequence[str],
    ) -> Accepted | Refusal:
        """Check a review without writing an event or record.

        Args:
            work: The Work under review.
            action: The action that contains the gate.
            stage: The gate that was reviewed.
            result: The overall judgement.
            judge: Who judged the review.
            cites: Citations in their original order.

        Returns:
            The accepted review or the diagnostics that refused it.
        """
        _one_work(work)
        fields = [
            ("Wio-Work", work),
            ("Wio-Action", action),
            ("Wio-Stage", stage),
            ("Wio-Result", result),
            ("Wio-Judge", judge),
        ]
        decision = _check_review(
            self.services, fields, cites, self.services.settings.load()
        )
        return decision if isinstance(decision, Refusal) else decision[1]


def configure_write(parser: ArgumentParser) -> None:
    """Add the arguments of the write form to its parser.

    It does no I/O. The positional arguments are the Work, the action and the stage,
    which argparse refuses to lack, and the options are `--items`, a comma-separated
    list of item ids, `--result`, `--judge` and `--cite`, which may be repeated and
    names an item or a rule and its result for the gate form. An unknown option is
    argparse's usage error.

    Args:
        parser: The parser that `wio.cli` created for the form.
    """
    for name, text in _POSITIONALS.items():
        parser.add_argument(name, help=text)
    for name, text in _OPTIONS.items():
        parser.add_argument(f"--{name}", help=text)
    parser.add_argument("--cite", action="append", default=[], help=_CITE)


def run_write(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Print a checked record and record its event when it describes a review.

    Args:
        services: The ports for checking and recording the request.
        args: The arguments that configure_write parsed.
        stdio: Receives the record and the diagnostics.

    Returns:
        Zero for a printed record or one for a refusal with empty stdout.

    Raises:
        TrailersError: The Work argument is a comma-separated list.
        ConfigurationError: The effective configuration cannot be read.
    """
    _one_work(args.work)
    config = services.settings.load()
    fields = _fields(args)
    if args.result is not None or args.cite:
        checked = _check_review(services, fields, args.cite, config)
    else:
        checked = _check_fields(services, fields, config)
    return _write_checked(checked, services.events, stdio)


def _write_checked(
    checked: tuple[str, Accepted | tuple[str, ...]] | Refusal,
    events: EventSink,
    stdio: Stdio,
) -> int:
    """Emit the diagnostics, accepted event and record in that order.

    Args:
        checked: The checked record and its outcome, or the refusal.
        events: Receives the event of an accepted review.
        stdio: Receives diagnostics and the printed record.

    Returns:
        Zero for a printed record, or one when the checks refused it.
    """
    if isinstance(checked, Refusal):
        stdio.stderr.writelines(line + "\n" for line in checked.lines)
        return 1
    record, outcome = checked
    warnings = outcome.warnings if isinstance(outcome, Accepted) else outcome
    stdio.stderr.writelines(line + "\n" for line in warnings)
    if isinstance(outcome, Accepted):
        events.write(outcome.event)
    stdio.stdout.write(record)
    return 0


def _check_fields(
    services: Services, fields: list[tuple[str, str]], config: Config
) -> tuple[str, tuple[str, ...]] | Refusal:
    """Validate the arguments, record syntax and effective fields in order.

    Args:
        services: Supplies Work metadata for validating the fields.
        fields: The requested fields in their printing order.
        config: The effective config for record shape and validation.

    Returns:
        The rendered record and warnings, or the ordered refusal lines.
    """
    refused = _refused_arguments(fields)
    record = "" if refused else render(dict(fields))
    findings = refused or check_shape(record, config.trailers.reader)
    if findings:
        return Refusal(_finding_lines(findings))
    checked = [Field(key, value, None) for key, value in fields]
    diagnostics = validate_record(checked, services.contracts, config)
    lines = tuple(f"{d.severity}: {d.where}: {d.message}" for d in diagnostics)
    return (
        Refusal(lines)
        if any(d.severity == "error" for d in diagnostics)
        else (record, lines)
    )


def _check_review(
    services: Services,
    fields: list[tuple[str, str]],
    cites: Sequence[str],
    config: Config,
) -> tuple[str, Accepted] | Refusal:
    """Check both review forms before either caller writes an event.

    Args:
        services: The readers of the Work, rules and commit history.
        fields: The record fields in their printing order.
        cites: The review citations.
        config: The effective config for the field checks.

    Returns:
        The rendered record and accepted review, or the combined refusal.
        Field warnings precede citation and history diagnostics.
    """
    checked = _check_fields(services, fields, config)
    if isinstance(checked, Refusal):
        return checked
    record, warnings = checked
    decision = check_review_event(services, fields, cites)
    if isinstance(decision, Refusal):
        return Refusal(warnings + decision.lines)
    return record, Accepted(decision.event, warnings + decision.warnings)


def _fields(args: Namespace) -> list[tuple[str, str]]:
    """Build the fields of the record from the arguments.

    Args:
        args: The arguments that `configure_write` parsed.

    Returns:
        The key and the value of each field that the arguments give, in the order of
        the keys of a record, with the items joined by a comma and one space and the
        judge `agent` when a result is given and no judge is.
    """
    fields = [
        ("Wio-Work", args.work),
        ("Wio-Action", args.action),
        ("Wio-Stage", args.stage),
    ]
    if args.items is not None:
        fields.append(("Wio-Items", ", ".join(args.items.split(","))))
    if args.result is not None:
        fields.append(("Wio-Result", args.result))
    if args.judge is not None or args.result is not None:
        judge = args.judge if args.judge is not None else "agent"
        fields.append(("Wio-Judge", judge))
    return fields


def _one_work(work: str) -> None:
    """Refuse a Work that this form does not write.

    Args:
        work: The Work argument as given.

    Raises:
        TrailersError: If it holds a comma, which makes it a list of Works. `none`
            never reaches this form, because the command gives it a form of its own.
    """
    if "," in work:
        message = (
            f"`{work}` is a list of Works, which `wio trailers` does not write for "
            "a record; name one Work."
        )
        raise TrailersError(message)


def _refused_arguments(fields: list[tuple[str, str]]) -> list[Finding]:
    """Refuse the arguments that cannot be rendered into one line of a record.

    Args:
        fields: The key and the value of each field.

    Returns:
        A `malformed` finding for each value that is empty or holds a line end, and
        one for a `Wio-Judge` without a `Wio-Result`, each at its own field, in the
        order of the fields, and one at most for a field, the empty or line-end
        one first. The `line` of a finding is the field as it would be
        written, with each line end of the value shown as an escaped newline, so that
        it is one line and an argument cannot add one to the output either.
    """
    keys = {key for key, _ in fields}
    reasons = [(key, value, _reason(key, value, keys)) for key, value in fields]
    return [
        Finding("malformed", key, _shown(key, value), number, reason)
        for number, (key, value, reason) in enumerate(reasons, start=1)
        if reason is not None
    ]


def _reason(key: str, value: str, keys: set[str]) -> str | None:
    """Say why an argument cannot be rendered, if it cannot.

    Args:
        key: The key of the field.
        value: The value of the field.
        keys: The keys of every field of the record.

    Returns:
        The message for a value that is empty or holds a line end, or for a
        `Wio-Judge` without a `Wio-Result`, the former first, and `None` for a
        value that can be rendered.
    """
    if not value or "\n" in value or "\r" in value:
        return f"`{key}` must be one line and not empty."
    if key == "Wio-Judge" and "Wio-Result" not in keys:
        return "`Wio-Judge` needs a `Wio-Result`."
    return None


def _shown(key: str, value: str) -> str:
    """Show a field on one line, with each line end of the value escaped.

    Args:
        key: The key of the field.
        value: The value of the field.

    Returns:
        `Key: value` with a carriage return or a line feed written as an escape.
    """
    return f"{key}: {value}".replace("\r", "\\r").replace("\n", "\\n")


def _finding_lines(findings: list[Finding]) -> tuple[str, ...]:
    """Give syntax diagnostics with each offending line just after its error.

    Args:
        findings: The findings of the argument or record shape check.

    Returns:
        The lines to write to standard error, in order, without terminators.
    """
    return tuple(
        line
        for finding in findings
        for line in (f"error: {finding.key}: {finding.message}", finding.line)
    )
