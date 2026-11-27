# SPDX-License-Identifier: Apache-2.0
"""The validator of the fields of a record.

The write command and the commit-time check judge a record against the config and
the Works with the one `validate_record`, so a record cannot pass one and fail
the other. It judges nothing about the record's own form, which the shape check of
`wio.formats` has judged, and finds no Work, which the `Contracts` port does.
"""

from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING

from wio.models.diagnostics import Diagnostic, Severity

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.models.config import Config, Stage
    from wio.trailers.ports import Contracts

_ORDER = ("Wio-Work", "Wio-Action", "Wio-Stage", "Wio-Items", "Wio-Result")
"""The keys that a diagnostic is about, in the order the diagnostics come in."""


@dataclass(frozen=True)
class Field:
    """One field of a record: its key, its value and where it was written.

    It is immutable. The reader of messages gives a line to every field, and the
    write command builds a record from its arguments, which have none.

    Attributes:
        key: The key as written, such as `Wio-Stage`.
        value: The value as written, such as `architecture`.
        line: The 1-based line of the field in the message, or `None` for a
            field that was not read from one.
    """

    key: str
    value: str
    line: int | None


@dataclass(frozen=True)
class _Record:
    """The fields of one record, looked up by key."""

    fields: tuple[Field, ...]

    def get(self, key: str) -> Field | None:
        """Find a field by its key.

        Args:
            key: The key, such as `Wio-Stage`.

        Returns:
            The field, or `None` when the record has none.
        """
        return next((f for f in self.fields if f.key == key), None)

    def where(self, key: str) -> str:
        """Say where a diagnostic about a field is placed.

        Args:
            key: The key of the field the diagnostic is about.

        Returns:
            The field's line as a string, or the record's first line for an
            absent field, or the key itself when the fields have no lines. The
            record has at least `Wio-Work`, which the shape check guarantees.
        """
        field = self.get(key) or self.fields[0]
        return key if field.line is None else str(field.line)


@dataclass(frozen=True)
class _Finding:
    """A diagnostic and the field it is about, which orders it."""

    key: str
    diagnostic: Diagnostic


def validate_record(
    fields: Sequence[Field], contracts: Contracts, config: Config
) -> list[Diagnostic]:
    """Validate one shape-checked record against the config and Works.

    Checks `Wio-Work`, `Wio-Action`, `Wio-Stage`, `Wio-Items`, and `Wio-Result`
    (ignoring `Wio-Work: none`). Unknown actions/stages/Works/items and
    missing or disallowed gate results are errors; a stage outside a Work's
    pipeline or an action absent from the Work is a warning.

    Returns:
        Diagnostics ordered by field (`Wio-Work` through `Wio-Result`), empty
        when the record is valid.
    """
    record = _Record(tuple(fields))
    found = [
        *_work_checks(record, contracts, config),
        *_config_checks(record, config, names_only=False),
    ]
    return [f.diagnostic for f in sorted(found, key=lambda f: _ORDER.index(f.key))]


def validate_names(fields: Sequence[Field], config: Config) -> list[Diagnostic]:
    """Judge only the names of a record against the config.

    It is the name checks of `validate_record` on their own, for the later check
    that tolerates what the config no longer has and turns what it returns into
    warnings. It reads no Work.

    Args:
        fields: The fields of the record.
        config: The config, for the action names, the stage names and
            `gates.results`.

    Returns:
        The errors for an action or a stage that the config lacks and for a result
        outside `gates.results`, in the order of the fields, and none for a Work or
        an item. A record that holds gives none.
    """
    found = _config_checks(_Record(tuple(fields)), config, names_only=True)
    return [f.diagnostic for f in found]


def _work_checks(
    record: _Record, contracts: Contracts, config: Config
) -> list[_Finding]:
    """Judge the Works of a record and what depends on them."""
    works = _value(record, "Wio-Work")
    if works is None or works == "none":
        return []
    found: list[_Finding] = []
    for work in works.split(", "):
        have = contracts.items(work)
        if have is None:
            found.append(_error(record, "Wio-Work", f"No Work has the id `{work}`."))
        else:
            found += _item_findings(record, work, have)
            found += _pipeline_findings(record, (work, contracts), config)
    return found


def _item_findings(record: _Record, work: str, have: frozenset[str]) -> list[_Finding]:
    """Judge the items of a record against one Work."""
    items = _value(record, "Wio-Items")
    return [
        _error(record, "Wio-Items", f"`{item}` is not an item of the Work `{work}`.")
        for item in (items.split(", ") if items else [])
        if item not in have
    ]


def _pipeline_findings(
    record: _Record, found_in: tuple[str, Contracts], config: Config
) -> list[_Finding]:
    """Warn when a Work's pipeline does not hold the action or the stage."""
    work, contracts = found_in
    action, stage = _value(record, "Wio-Action"), _value(record, "Wio-Stage")
    if action is None or action not in config.actions:
        return []
    stages = contracts.pipeline(work, action)
    if stages is None:
        return [
            _warning(
                record, "Wio-Action", f"The Work `{work}` has no action `{action}`."
            )
        ]
    if stage in config.stages and stage not in stages:
        message = f"The stage `{stage}` is not in the `{action}` pipeline of `{work}`."
        return [_warning(record, "Wio-Stage", message)]
    return []


def _config_checks(
    record: _Record, config: Config, *, names_only: bool
) -> list[_Finding]:
    """Judge a record against what the config declares."""
    action, stage = _value(record, "Wio-Action"), _value(record, "Wio-Stage")
    found = []
    if action is not None and action not in config.actions:
        found.append(_error(record, "Wio-Action", f"`{action}` is not an action."))
    if stage is not None and stage not in config.stages:
        found.append(_error(record, "Wio-Stage", f"`{stage}` is not a stage."))
    result = _value(record, "Wio-Result")
    known = config.stages.get(stage) if stage is not None else None
    if names_only:
        return found + _listed(record, config, result)
    if known is None:
        return found
    return [*found, *_listed(record, config, result), *_gated(record, known, result)]


def _listed(record: _Record, config: Config, result: str | None) -> list[_Finding]:
    """Judge a result against the results that a gate can decide."""
    if result is None or result in config.gates.results:
        return []
    return [_error(record, "Wio-Result", f"`{result}` is not a result of a gate.")]


def _gated(record: _Record, stage: Stage, result: str | None) -> list[_Finding]:
    """Judge whether a result is present exactly on a gate."""
    if stage.gate and result is None:
        return [_error(record, "Wio-Result", "result required")]
    if result is not None and not stage.gate:
        return [_error(record, "Wio-Result", "not a gate")]
    return []


def _value(record: _Record, key: str) -> str | None:
    """Read the value of a field."""
    field = record.get(key)
    return None if field is None else field.value


def _finding(severity: Severity, record: _Record, key: str, message: str) -> _Finding:
    """Make a diagnostic about a field."""
    return _Finding(key, Diagnostic(severity, record.where(key), message))


_error = partial(_finding, "error")
"""Make an error about a field from the record, its key and a message."""
_warning = partial(_finding, "warning")
"""Make a warning about a field from the record, its key and a message."""
