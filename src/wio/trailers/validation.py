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
    """The fields of one record, looked up by key.

    Attributes:
        fields: The fields in the order written.
    """

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
    """A diagnostic and the field it is about, which orders it.

    Findings of one key keep the order in which a check emitted them, which the
    sort by key relies on.

    Attributes:
        key: The key of the field the diagnostic is about, one of `_ORDER`.
        diagnostic: The diagnostic.
    """

    key: str
    diagnostic: Diagnostic


def validate_record(
    fields: Sequence[Field], contracts: Contracts, config: Config
) -> list[Diagnostic]:
    """Judge the fields of one record against the config and the Works.

    The record has passed the shape check, so its keys are the six that a record
    has, each at most once, and the form of each value holds. Every field except
    `Wio-Judge` is checked: the Work against the `Contracts` port, the action and
    the stage against the config's actions and stages, the items against the items
    of each Work named, and the result against the config's `gates.results` and
    against whether the stage is a gate. A `Wio-Work: none` record names no Work,
    and the shape check has refused any other key on it, so it has nothing to
    check.

    A Work that no view has gets its own error and no check of its items or its
    pipeline, an action or a stage that the config lacks gets an error and no
    pipeline warning, and a stage that the config lacks gets no result check.
    Every other field is still checked. A stage that a Work's pipeline for the
    action does not list, and an action that the Work does not have, are warnings
    and never errors. A gate without a result is the error `result required`, and
    a result on a stage that is not a gate is the error `not a gate`.

    Each message names the value it is about, such as `nosuch`, and an item error
    names the item and the Work. A list of Works gives one diagnostic for each
    Work that lacks an item, for each item, Work by Work in the order written and
    each Work's items in the order written. A diagnostic is placed at the field it
    is about: a missing Work at `Wio-Work`, an action the Work lacks at
    `Wio-Action`, a stage outside the pipeline at `Wio-Stage`, an item at
    `Wio-Items` and a result at `Wio-Result`. An action that the Work lacks is one
    warning, and the stage is not warned about as well, because there is no
    pipeline to list it. For a stage that the config has, the checks of the result
    are independent: a result outside `gates.results` is an error whether or not
    the stage is a gate. A stage that the config lacks gets no check of the result
    at all.

    Args:
        fields: The record's fields in the order written.
        contracts: Finds the items and the pipelines of the Works.
        config: The config, for the action names, the stage names, the gate stages
            and `gates.results`.

    Returns:
        The diagnostics in the order of the fields, `Wio-Work`, `Wio-Action`,
        `Wio-Stage`, `Wio-Items` and `Wio-Result`, an absent field at the place it
        would have, and none for a record that holds. The `where` of one is the
        line of its field as a string, or the key of the field for a record whose
        fields have no lines; for an absent field it is the record's first line,
        or the key of the field concerned.
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
    """Judge the Works of a record and what depends on them.

    A `Wio-Work: none` record gives nothing. The config is read only to tell a name
    that the config lacks, which `_config_checks` refuses, from one that a Work
    lacks, so an action or a stage that the config lacks is never warned about.

    Args:
        record: The record.
        contracts: Finds the items and the pipelines of the Works.
        config: The config, for the action names and the stage names.

    Returns:
        The error for each Work that no view has, the error for each item that a
        Work lacks, Work by Work and each Work's items in the order written, the
        warning for each Work that lacks the action, and the warning for each Work
        whose pipeline does not list the stage, none for a Work that is absent.
    """
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
    """Judge the items of a record against one Work.

    Args:
        record: The record.
        work: The id of a Work that exists.
        have: The item ids of that Work.

    Returns:
        An error for each item that the Work lacks, in the order written, naming
        the item and the Work.
    """
    items = _value(record, "Wio-Items")
    return [
        _error(record, "Wio-Items", f"`{item}` is not an item of the Work `{work}`.")
        for item in (items.split(", ") if items else [])
        if item not in have
    ]


def _pipeline_findings(
    record: _Record, found_in: tuple[str, Contracts], config: Config
) -> list[_Finding]:
    """Warn when a Work's pipeline does not hold the action or the stage.

    Args:
        record: The record.
        found_in: The id of a Work that exists, and the port that finds its
            pipeline.
        config: The config, for the action names and the stage names.

    Returns:
        One warning when the Work lacks the action, or one when the pipeline of the
        action does not list the stage, and none for an action or a stage that the
        config lacks, which is an error elsewhere.
    """
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
    """Judge a record against what the config declares.

    Args:
        record: The record.
        config: The config, for the action names, the stage names, the gate
            stages and `gates.results`.
        names_only: Judge only the names, which are the action, the stage and the
            result against `gates.results`, and not whether a result is present
            exactly on a gate.

    Returns:
        The errors for an action or a stage that the config lacks and for a
        result outside `gates.results`, in the order of the fields, then, unless
        `names_only`, the error `result required` for a gate without a result and
        `not a gate` for a result on a stage that is not a gate. Unless
        `names_only`, a stage that the config lacks gets no check of the result at
        all, and with `names_only` a result is judged against `gates.results`
        whatever the stage is.
    """
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
    """Judge a result against the results that a gate can decide.

    Args:
        record: The record.
        config: The config, for `gates.results`.
        result: The `Wio-Result` value, or `None` for none.

    Returns:
        An error naming a result that `gates.results` does not list, none for no
        result or a listed one.
    """
    if result is None or result in config.gates.results:
        return []
    return [_error(record, "Wio-Result", f"`{result}` is not a result of a gate.")]


def _gated(record: _Record, stage: Stage, result: str | None) -> list[_Finding]:
    """Judge whether a result is present exactly on a gate.

    Args:
        record: The record.
        stage: The stage of the record, which the config has.
        result: The `Wio-Result` value, or `None` for none.

    Returns:
        The error `result required` for a gate without a result and `not a gate`
        for a result on a stage that is not a gate.
    """
    if stage.gate and result is None:
        return [_error(record, "Wio-Result", "result required")]
    if result is not None and not stage.gate:
        return [_error(record, "Wio-Result", "not a gate")]
    return []


def _value(record: _Record, key: str) -> str | None:
    """Read the value of a field.

    Args:
        record: The record.
        key: The key.

    Returns:
        The value, or `None` when the record has no such field.
    """
    field = record.get(key)
    return None if field is None else field.value


def _finding(severity: Severity, record: _Record, key: str, message: str) -> _Finding:
    """Make a diagnostic about a field.

    Args:
        severity: `error` for what is wrong and `warning` for what is doubtful.
        record: The record, which places the diagnostic.
        key: The key of the field the diagnostic is about.
        message: What is wrong or doubtful.

    Returns:
        The finding.
    """
    return _Finding(key, Diagnostic(severity, record.where(key), message))


_error = partial(_finding, "error")
"""Make an error about a field from the record, its key and a message."""
_warning = partial(_finding, "warning")
"""Make a warning about a field from the record, its key and a message."""
