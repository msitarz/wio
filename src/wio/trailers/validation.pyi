# SPDX-License-Identifier: Apache-2.0
"""The spec of the validator of the fields of a record.

The write command and the commit-time check judge a record against the config and
the Works with the one `validate_record`, so a record cannot pass one and fail
the other. It judges nothing about the record's own form, which the shape check of
`wio.formats` has judged, and finds no Work, which the `Contracts` port does.

The stub is the spec until the wiring stage of the Work that builds the validator
writes the module `wio.trailers.validation` and deletes this stub, so the spec and
the code never coexist.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from wio.models.config import Config
from wio.models.diagnostics import Diagnostic
from wio.trailers.ports import Contracts

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
    action or stage and has nothing to check.

    A Work that no view has gets its own error and no check of its items or its
    pipeline, an action or a stage that the config lacks gets an error and no
    pipeline warning, and a stage that the config lacks gets no result check.
    Every other field is still checked. A stage that a Work's pipeline for the
    action does not list, and an action that the Work does not have, are warnings
    and never errors. A gate without a result is the error `result required`, and
    a result on a stage that is not a gate is the error `not a gate`.

    Each message names the value it is about, such as `nosuch`, and an item error
    names the item and the Work. A list of Works gives one diagnostic for each
    Work and one for each item, in the order written.

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

    Raises:
        ConfigurationError: If the `Contracts` port cannot load the config.
    """
    ...

def validate_names(fields: Sequence[Field], config: Config) -> list[Diagnostic]:
    """Judge only the names of a record against the config.

    It is the name checks of `validate_record` on their own, for the later check
    that tolerates what the config no longer has and turns what it returns into
    warnings. It reads no Work.

    Args:
        fields: The record's fields in the order written.
        config: The config, for the action names, the stage names and
            `gates.results`.

    Returns:
        The errors for an action or a stage that the config lacks and for a result
        outside `gates.results`, in the order of the fields, and none for a Work or
        an item. A record that holds gives none.
    """
    ...
