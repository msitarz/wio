# SPDX-License-Identifier: Apache-2.0
"""The write form of `wio trailers`: print a checked record.

`wio trailers <work> <action> <stage>` prints the record for a Work, an action and
a stage, with optional item ids, a result and a judge, when every field holds, and
nothing when one does not. `wio.cli` dispatches on the first argument and wires
the ports, and this module holds what the form does, so the form is run in a test
with fakes of the ports. The form composes `render`, `check_shape` and
`validate_record`, and the leaves that refuse an argument and write what it found
are stubbed.
"""

from typing import TYPE_CHECKING

from wio.formats import check_shape, render
from wio.models.records import Finding
from wio.trailers.errors import TrailersError
from wio.trailers.validation import Field, validate_record

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace

    from wio.io.ports import Stdio
    from wio.models.diagnostics import Diagnostic
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
_CITE = "An item and its result, accepted and ignored here."


def configure_write(parser: ArgumentParser) -> None:
    """Add the arguments of the write form to its parser.

    It does no I/O. The positional arguments are the Work, the action and the stage,
    which argparse refuses to lack, and the options are `--items`, a comma-separated
    list of item ids, `--result`, `--judge` and `--cite`, which may be repeated, is
    accepted and is ignored here because the gate leaf handles it. An unknown option
    is argparse's usage error.

    Args:
        parser: The parser that `wio.cli` created for the form.
    """
    for name, text in _POSITIONALS.items():
        parser.add_argument(name, help=text)
    for name, text in _OPTIONS.items():
        parser.add_argument(f"--{name}", help=text)
    parser.add_argument("--cite", action="append", default=[], help=_CITE)


def run_write(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Print the record of the arguments, or say why it is refused.

    The Work is checked first: a value that holds a comma, which is a list of Works,
    or that is exactly `none` is a usage error, before the config is loaded or
    anything is judged, and any other value, such as one with a space, is judged by
    form like the other fields. The record is then built from the arguments, with
    the `--items` ids joined by a comma and one space in the order given and the
    judge `agent` when a result is given and no judge is, and it is judged in this
    order. An argument that is empty or holds a line end is refused as the finding
    of its field, so no argument can add a line to the record, and a `--judge`
    without a result is refused the same way, as the finding of `Wio-Judge`, before
    the record is rendered. The record is rendered and `check_shape` judges it
    with the reader of the config, and only when that finds nothing does
    `validate_record` judge its fields against the config and the Works, which the
    `Contracts` port finds in the working tree and then in `HEAD`.

    Each finding of the shape check is written to standard error as
    `error: <key>: <message>` followed by its offending line, and each diagnostic of
    the validator as `<severity>: <where>: <message>`, in the order they come, with
    the key of the field as `<where>`. Nothing is written to standard output when
    anything is an error. A warning does not stop the record, which is written to
    standard output with its lines in the order of the keys.

    Args:
        services: The ports the form reads the config and the Works through.
        args: The arguments that `configure_write` parsed.
        stdio: Where the record and the findings are written.

    Returns:
        0 for a record that is printed, with or without a warning, and 1 for a field
        that is refused.

    Raises:
        TrailersError: If the Work is a list of ids or `none`, which this form does
            not write.
        ConfigurationError: If the config cannot be read.
    """
    _one_work(args.work)
    config = services.settings.load()
    fields = _fields(args)
    refused = _refused_arguments(fields)
    record = "" if refused else render(dict(fields))
    findings = refused or check_shape(record, config.trailers.reader)
    if findings:
        _write_findings(findings, stdio)
        return 1
    checked = [Field(key, value, None) for key, value in fields]
    return _finish(validate_record(checked, services.contracts, config), record, stdio)


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
        TrailersError: If it holds a comma, which makes it a list of Works, or is
            exactly `none`.
    """
    if "," in work or work == "none":
        message = (
            f"`{work}` is a list of Works or none, which `wio trailers` does not write "
            "for a record; name one Work."
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


def _write_findings(findings: list[Finding], stdio: Stdio) -> None:
    """Write the findings of the shape check to standard error.

    Args:
        findings: What `check_shape` or the refusal of an argument found.
        stdio: Where they are written.
    """
    for finding in findings:
        stdio.stderr.write(f"error: {finding.key}: {finding.message}\n{finding.line}\n")


def _finish(diagnostics: list[Diagnostic], record: str, stdio: Stdio) -> int:
    """Write what the validator found, and the record when nothing is an error.

    Args:
        diagnostics: What `validate_record` returned, in the order of the fields.
        record: The rendered record.
        stdio: Where the diagnostics and the record are written.

    Returns:
        1 when a diagnostic is an error, and then nothing is written to standard
        output, and 0 otherwise, after the record is written to standard output.
    """
    for d in diagnostics:
        stdio.stderr.write(f"{d.severity}: {d.where}: {d.message}\n")
    if any(d.severity == "error" for d in diagnostics):
        return 1
    stdio.stdout.write(record)
    return 0
