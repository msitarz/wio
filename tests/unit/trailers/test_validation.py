# SPDX-License-Identifier: Apache-2.0
"""Tests of the validator of the fields of a record.

The examples use a Work `k3m9xq` with the items `AC-1` and `AC-3`, a leaf whose
`deliver` is the `typed-boundary` stage preset, which lists the stages
`architecture`, which is not a gate, and `architecture-review`, which is a gate.
The config also has the stage `integration`, which that preset does not list, and
its results are `pass`, `fail` and `unknown`. R is the record `Wio-Work: k3m9xq`,
`Wio-Action: deliver` and `Wio-Stage: architecture`. The tests fail with
`NotImplementedError` until the implementation stage, which removes the marker.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

from wio.models.config import Action, Config, Stage
from wio.models.frozen import freeze
from wio.trailers.validation import Field, validate_names, validate_record

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.models.diagnostics import Diagnostic

PENDING = pytest.mark.xfail(
    raises=NotImplementedError, strict=True, reason="implementation stage"
)
CONFIG = Config(
    actions=freeze({"deliver": Action("Deliver."), "define": Action("Define.")}),
    stages=freeze(
        {
            "architecture": Stage(goal="a"),
            "architecture-review": Stage(goal="r", gate=True),
            "integration": Stage(goal="i"),
        }
    ),
)
PIPELINE = ["architecture", "architecture-review"]


@dataclass(frozen=True)
class FakeContracts:
    """The `Contracts` port over three Works, `k3m9xq`, `a7b2c4` and `b8c9d0`."""

    def items(self, work_id: str) -> frozenset[str] | None:
        """Find the items of a Work.

        Args:
            work_id: The Work's id.

        Returns:
            Its items, or `None` for a Work that the fake does not have.
        """
        return {
            "k3m9xq": frozenset({"AC-1", "AC-3"}),
            "a7b2c4": frozenset({"AC-1"}),
            "b8c9d0": frozenset(),
        }.get(work_id)

    def pipeline(self, work_id: str, action: str) -> Sequence[str] | None:
        """Find the stages of a Work's action.

        Args:
            work_id: The Work's id.
            action: The action.

        Returns:
            The stages of `deliver` for a Work of the fake, `architecture` alone
            for the other two, and `None` for any other action or Work.
        """
        if action != "deliver" or self.items(work_id) is None:
            return None
        return PIPELINE if work_id == "k3m9xq" else ["architecture"]


def _fields(
    *,
    work: str = "k3m9xq",
    action: str = "deliver",
    stage: str = "architecture",
    items: str | None = None,
    result: str | None = None,
    lines: bool = True,
) -> list[Field]:
    """Build the fields of R with the given changes.

    Args:
        work: The `Wio-Work` value.
        action: The `Wio-Action` value.
        stage: The `Wio-Stage` value.
        items: The `Wio-Items` value, or `None` for none.
        result: The `Wio-Result` value, or `None` for none.
        lines: Whether the fields carry the lines 3 and on.

    Returns:
        The fields in the order of a record.
    """
    pairs = [("Wio-Work", work), ("Wio-Action", action), ("Wio-Stage", stage)]
    pairs += [("Wio-Items", items)] if items is not None else []
    pairs += [("Wio-Result", result)] if result is not None else []
    return [Field(k, v, 3 + i if lines else None) for i, (k, v) in enumerate(pairs)]


def _run(fields: list[Field]) -> list[Diagnostic]:
    """Validate fields against the fake Works and the config.

    Args:
        fields: The record's fields.

    Returns:
        The diagnostics.
    """
    return validate_record(fields, FakeContracts(), CONFIG)


def _summary(found: list[Diagnostic]) -> list[tuple[str, str]]:
    """Reduce diagnostics to their severity and place.

    Args:
        found: The diagnostics.

    Returns:
        A pair for each, in order.
    """
    return [(d.severity, d.where) for d in found]


@PENDING
@pytest.mark.parametrize(
    "fields",
    [
        _fields(),
        _fields(items="AC-3, AC-1"),
        _fields(stage="architecture-review", result="pass"),
        [Field("Wio-Work", "none", 3)],
    ],
    ids=["R", "items", "gate-and-result", "none"],
)
def test_a_valid_record_has_no_diagnostics(fields: list[Field]) -> None:
    """AC-1: R, R with items, R with a gate and a result, and `Wio-Work: none`."""
    # Given a valid record
    # When `validate_record` runs on it
    found = _run(fields)

    # Then it returns no diagnostic
    assert found == []


@PENDING
def test_a_work_that_exists_nowhere_is_one_error() -> None:
    """AC-2: R with `Wio-Work: zz9zz9`, for which the port returns `None`."""
    # Given R with `Wio-Work: zz9zz9`
    # When `validate_record` runs
    found = _run(_fields(work="zz9zz9"))

    # Then it returns one `error` naming `zz9zz9` and no other diagnostic
    assert [d.severity for d in found] == ["error"]
    assert "zz9zz9" in found[0].message


@PENDING
def test_the_other_fields_are_still_checked_for_a_missing_work() -> None:
    """AC-2: a stage the config lacks is still an error beside the Work's."""
    # Given R with `Wio-Work: zz9zz9` and `Wio-Stage: nosuch`
    # When `validate_record` runs
    found = _run(_fields(work="zz9zz9", stage="nosuch"))

    # Then it returns the one `error` for `zz9zz9` and the one for `nosuch`, and
    # no `warning`
    assert [d.severity for d in found] == ["error", "error"]
    assert "zz9zz9" in found[0].message
    assert "nosuch" in found[1].message


@PENDING
@pytest.mark.parametrize(
    "fields",
    [_fields(action="nosuch"), _fields(stage="nosuch")],
    ids=["action", "stage"],
)
def test_an_action_or_a_stage_the_config_lacks_is_an_error(
    fields: list[Field],
) -> None:
    """AC-3: one error naming `nosuch` for each, and no warning."""
    # Given R with `Wio-Action: nosuch`, or R with `Wio-Stage: nosuch`
    # When `validate_record` runs
    found = _run(fields)

    # Then it returns one `error` naming `nosuch`, and no `warning`
    assert [d.severity for d in found] == ["error"]
    assert "nosuch" in found[0].message


@PENDING
def test_an_item_the_work_does_not_have_is_an_error() -> None:
    """AC-4: the item and the Work are named, for one Work and for a list."""
    # Given R with `Wio-Items: AC-99`, and R with `Wio-Work: k3m9xq, a7b2c4` and
    # `Wio-Items: AC-3`, where `a7b2c4` has the item `AC-1` and not `AC-3`
    first = _run(_fields(items="AC-99"))
    second = _run(_fields(work="k3m9xq, a7b2c4", items="AC-3"))

    # When `validate_record` ran on each
    # Then it returns one `error` for each, naming the item and the Work
    assert [d.severity for d in first] == ["error"]
    assert "AC-99" in first[0].message
    assert "k3m9xq" in first[0].message
    assert [d.severity for d in second] == ["error"]
    assert "AC-3" in second[0].message
    assert "a7b2c4" in second[0].message


@PENDING
def test_a_result_is_present_exactly_on_a_gate() -> None:
    """AC-5: a gate without a result, and a result on a stage that is no gate."""
    # Given R with the stage `architecture-review` and no `Wio-Result`, and R with
    # `Wio-Result: pass`
    # When `validate_record` runs on each
    missing = _run(_fields(stage="architecture-review"))
    stray = _run(_fields(result="pass"))

    # Then it returns one `error` for each, `result required` for the first and
    # `not a gate` for the second
    assert [d.severity for d in missing] == ["error"]
    assert "result required" in missing[0].message
    assert [d.severity for d in stray] == ["error"]
    assert "not a gate" in stray[0].message


@PENDING
def test_a_result_on_a_stage_the_config_lacks_is_not_checked() -> None:
    """AC-5: only the stage is refused."""
    # Given R with `Wio-Stage: nosuch` and `Wio-Result: pass`
    # When `validate_record` runs
    found = _run(_fields(stage="nosuch", result="pass"))

    # Then it returns the one `error` for `nosuch` and none for the result
    assert [d.severity for d in found] == ["error"]
    assert "nosuch" in found[0].message


@PENDING
def test_a_stage_the_config_lacks_gets_no_check_of_the_result_at_all() -> None:
    """AC-5, AC-6: not even `maybe` is judged against `gates.results`."""
    # Given R with `Wio-Stage: nosuch` and `Wio-Result: maybe`
    # When `validate_record` runs
    found = _run(_fields(stage="nosuch", result="maybe"))

    # Then it returns the one `error` for `nosuch`
    assert [d.severity for d in found] == ["error"]
    assert "nosuch" in found[0].message


@PENDING
def test_the_checks_of_a_result_are_independent_on_a_stage_the_config_has() -> None:
    """AC-5, AC-6: a result `maybe` on a stage that is not a gate is two errors."""
    # Given R with `Wio-Result: maybe`, whose stage `architecture` is not a gate
    # When `validate_record` runs
    found = _run(_fields(result="maybe"))

    # Then it returns `not a gate` and the error naming `maybe`
    assert [d.severity for d in found] == ["error", "error"]
    assert any("not a gate" in d.message for d in found)
    assert any("maybe" in d.message for d in found)


@PENDING
def test_a_pipeline_is_not_warned_about_for_a_name_the_config_lacks() -> None:
    """AC-2, AC-3: `nosuch` is an error and never also a warning."""
    # Given R with `Wio-Action: nosuch`, and R with `Wio-Stage: nosuch` of a Work
    # whose pipelines the port knows
    # When `validate_record` runs on each
    action = _run(_fields(action="nosuch"))
    stage = _run(_fields(stage="nosuch"))

    # Then each is one `error` and no `warning`
    assert [d.severity for d in action] == ["error"]
    assert [d.severity for d in stage] == ["error"]


@PENDING
def test_the_place_of_an_item_error_is_the_line_of_the_items() -> None:
    """AC-4, AC-8: the error for `AC-99` is at the line of `Wio-Items`."""
    # Given R with `Wio-Items: AC-99` on line 6
    # When `validate_record` runs
    found = _run(_fields(items="AC-99"))

    # Then the `error` has `where` `6`
    assert _summary(found) == [("error", "6")]


@PENDING
def test_a_result_the_config_does_not_list_is_an_error() -> None:
    """AC-6: `maybe` on a gate stage."""
    # Given R with the stage `architecture-review` and `Wio-Result: maybe`
    # When `validate_record` runs
    found = _run(_fields(stage="architecture-review", result="maybe"))

    # Then it returns one `error` naming `maybe`
    assert [d.severity for d in found] == ["error"]
    assert "maybe" in found[0].message


@PENDING
def test_a_stage_outside_the_pipeline_is_a_warning() -> None:
    """AC-7: the stage `integration`, which the preset does not list."""
    # Given R with `Wio-Stage: integration`
    # When `validate_record` runs
    found = _run(_fields(stage="integration"))

    # Then it returns one `warning` naming `integration` and no `error`
    assert [d.severity for d in found] == ["warning"]
    assert "integration" in found[0].message


@PENDING
def test_an_action_the_work_does_not_have_is_a_warning() -> None:
    """AC-7: `define` is in the config and `k3m9xq` lacks it."""
    # Given a record of `k3m9xq` with `Wio-Action: define`
    # When `validate_record` runs
    found = _run(_fields(action="define"))

    # Then it returns one `warning` naming `define` and no `error`
    assert [d.severity for d in found] == ["warning"]
    assert "define" in found[0].message


@PENDING
def test_the_place_of_a_present_field_is_its_line_or_its_key() -> None:
    """AC-8: lines 3 to 5, and no lines."""
    # Given R with `Wio-Stage: nosuch` whose fields carry the lines 3 to 5, and
    # the same record whose fields carry no lines
    # When `validate_record` runs on each
    with_lines = _run(_fields(stage="nosuch"))
    without = _run(_fields(stage="nosuch", lines=False))

    # Then the `error` has `where` `5` for the first and `Wio-Stage` for the second
    assert _summary(with_lines) == [("error", "5")]
    assert _summary(without) == [("error", "Wio-Stage")]


@PENDING
def test_the_place_of_an_absent_field_is_the_first_line_or_its_key() -> None:
    """AC-8: a gate without a result."""
    # Given R with the stage `architecture-review` and no `Wio-Result`, with the
    # lines 3 to 5 and without lines
    # When `validate_record` runs on each
    with_lines = _run(_fields(stage="architecture-review"))
    without = _run(_fields(stage="architecture-review", lines=False))

    # Then the `error` has `where` `3`, the record's first line, for the first and
    # `Wio-Result` for the second
    assert _summary(with_lines) == [("error", "3")]
    assert _summary(without) == [("error", "Wio-Result")]


@PENDING
def test_each_diagnostic_points_at_its_own_field() -> None:
    """AC-8: the warning and the error have their own lines."""
    # Given R with `Wio-Stage: integration` on line 5 and `Wio-Items: AC-99` on
    # line 6
    # When `validate_record` runs
    found = _run(_fields(stage="integration", items="AC-99"))

    # Then the `error` for `AC-99` has `where` `6` and the `warning` for
    # `integration` has `where` `5`
    assert _summary(found) == [("warning", "5"), ("error", "6")]


@PENDING
def test_the_diagnostics_come_in_the_order_of_the_fields() -> None:
    """AC-9: the action, then the stage, then the item."""
    # Given R with `Wio-Action: nosuch`, `Wio-Stage: nosuch` and
    # `Wio-Items: AC-99`, in that order of fields
    # When `validate_record` runs
    found = _run(_fields(action="nosuch", stage="nosuch", items="AC-99"))

    # Then it returns the `error` for the action, then the stage, then `AC-99`
    assert _summary(found) == [("error", "4"), ("error", "5"), ("error", "6")]
    assert "AC-99" in found[2].message


@PENDING
def test_a_list_of_works_gives_one_diagnostic_per_work_in_order() -> None:
    """AC-9: `b8c9d0` before `a7b2c4`."""
    # Given R with `Wio-Work: b8c9d0, a7b2c4` and `Wio-Items: AC-3`, where both
    # lack `AC-3` and their `deliver` lists `architecture`
    # When `validate_record` runs
    found = _run(_fields(work="b8c9d0, a7b2c4", items="AC-3"))

    # Then it returns the `error` for `b8c9d0` and then the one for `a7b2c4`
    assert [d.severity for d in found] == ["error", "error"]
    assert "b8c9d0" in found[0].message
    assert "a7b2c4" in found[1].message


@PENDING
def test_a_warning_comes_before_an_error_of_a_later_field() -> None:
    """AC-9: the stage warning, then the item error."""
    # Given R with `Wio-Stage: integration` and `Wio-Items: AC-99`
    # When `validate_record` runs
    found = _run(_fields(stage="integration", items="AC-99"))

    # Then it returns the `warning` for the stage, then the `error` for `AC-99`
    assert [d.severity for d in found] == ["warning", "error"]


@PENDING
def test_an_absent_field_comes_at_its_place() -> None:
    """AC-9: the item error, then `result required`."""
    # Given R with the stage `architecture-review`, `Wio-Items: AC-99` and no
    # `Wio-Result`
    # When `validate_record` runs
    found = _run(_fields(stage="architecture-review", items="AC-99"))

    # Then it returns the `error` for `AC-99` and then `result required`
    assert "AC-99" in found[0].message
    assert "result required" in found[1].message


@PENDING
def test_the_name_checks_stand_alone() -> None:
    """AC-10: `validate_names` judges only the names."""
    # Given R with `Wio-Work: zz9zz9`, `Wio-Action: nosuch`, `Wio-Stage: nosuch`
    # and `Wio-Items: AC-99`, and R with the stage `architecture-review` and
    # `Wio-Result: maybe`
    # When `validate_names` runs on each
    first = validate_names(
        _fields(work="zz9zz9", action="nosuch", stage="nosuch", items="AC-99"), CONFIG
    )
    second = validate_names(
        _fields(stage="architecture-review", result="maybe"), CONFIG
    )

    # Then it returns the two `error`s for the action and the stage, and none for
    # `zz9zz9` or `AC-99`, and for the second the one `error` naming `maybe`
    assert [d.severity for d in first] == ["error", "error"]
    assert all("nosuch" in d.message for d in first)
    assert [d.severity for d in second] == ["error"]
    assert "maybe" in second[0].message
