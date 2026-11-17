# SPDX-License-Identifier: Apache-2.0
"""Tests of the validator of the fields of a record.

Each test is a stub for one scenario of the Work that builds the validator, and
skips until the implementation stage fills it in. The examples use a Work
`k3m9xq` with the items `AC-1` and `AC-3`, a leaf whose `deliver` is the
`typed-boundary` stage preset, which lists the stages `architecture`, which is not
a gate, and `architecture-review`, which is a gate. The config also has the stage
`integration`, which that preset does not list, and its results are `pass`,
`fail` and `unknown`. R is the record `Wio-Work: k3m9xq`, `Wio-Action: deliver`
and `Wio-Stage: architecture`.
"""

import pytest

STUB = "filled in by the implementation stage"


def test_a_valid_record_has_no_diagnostics() -> None:
    """AC-1: R, R with items, R with a gate and a result, and `Wio-Work: none`."""
    # Given R, R with `Wio-Items: AC-3, AC-1`, R with the gate stage
    # `architecture-review` and `Wio-Result: pass`, and `Wio-Work: none`
    # When `validate_record` runs on each
    # Then it returns no diagnostic for any
    pytest.skip(STUB)


def test_a_work_that_exists_nowhere_is_one_error() -> None:
    """AC-2: R with `Wio-Work: zz9zz9`, for which the port returns `None`."""
    # Given R with `Wio-Work: zz9zz9`
    # When `validate_record` runs
    # Then it returns one `error` naming `zz9zz9` and no other diagnostic
    pytest.skip(STUB)


def test_the_other_fields_are_still_checked_for_a_missing_work() -> None:
    """AC-2: a stage the config lacks is still an error beside the Work's."""
    # Given R with `Wio-Work: zz9zz9` and `Wio-Stage: nosuch`
    # When `validate_record` runs
    # Then it returns the one `error` for `zz9zz9` and the one for `nosuch`, and
    # no `warning`
    pytest.skip(STUB)


def test_an_action_or_a_stage_the_config_lacks_is_an_error() -> None:
    """AC-3: one error naming `nosuch` for each, and no warning."""
    # Given R with `Wio-Action: nosuch`, and R with `Wio-Stage: nosuch`
    # When `validate_record` runs on each
    # Then it returns one `error` for each naming `nosuch`, and no `warning`
    pytest.skip(STUB)


def test_an_item_the_work_does_not_have_is_an_error() -> None:
    """AC-4: the item and the Work are named, for one Work and for a list."""
    # Given R with `Wio-Items: AC-99`, and R with `Wio-Work: k3m9xq, a7b2c4` and
    # `Wio-Items: AC-3`, where `a7b2c4` has the item `AC-1` and not `AC-3`
    # When `validate_record` runs on each
    # Then it returns one `error` for each, the first naming `AC-99` and `k3m9xq`
    # and the second naming `AC-3` and `a7b2c4`
    pytest.skip(STUB)


def test_a_result_is_present_exactly_on_a_gate() -> None:
    """AC-5: a gate without a result, and a result on a stage that is no gate."""
    # Given R with the stage `architecture-review` and no `Wio-Result`, and R with
    # `Wio-Result: pass`
    # When `validate_record` runs on each
    # Then it returns one `error` for each, `result required` for the first and
    # `not a gate` for the second
    pytest.skip(STUB)


def test_a_result_on_a_stage_the_config_lacks_is_not_checked() -> None:
    """AC-5: only the stage is refused."""
    # Given R with `Wio-Stage: nosuch` and `Wio-Result: pass`
    # When `validate_record` runs
    # Then it returns the one `error` for `nosuch` and none for the result
    pytest.skip(STUB)


def test_a_result_the_config_does_not_list_is_an_error() -> None:
    """AC-6: `maybe` on a gate stage."""
    # Given R with the stage `architecture-review` and `Wio-Result: maybe`
    # When `validate_record` runs
    # Then it returns one `error` naming `maybe`
    pytest.skip(STUB)


def test_a_stage_outside_the_pipeline_is_a_warning() -> None:
    """AC-7: the stage `integration`, which the preset does not list."""
    # Given R with `Wio-Stage: integration`
    # When `validate_record` runs
    # Then it returns one `warning` naming `integration` and no `error`
    pytest.skip(STUB)


def test_an_action_the_work_does_not_have_is_a_warning() -> None:
    """AC-7: `define` is in the config and `k3m9xq` lacks it."""
    # Given a record of `k3m9xq` with `Wio-Action: define`
    # When `validate_record` runs
    # Then it returns one `warning` naming `define` and no `error`
    pytest.skip(STUB)


def test_the_place_of_a_present_field_is_its_line_or_its_key() -> None:
    """AC-8: lines 3 to 5, and no lines."""
    # Given R with `Wio-Stage: nosuch` whose fields carry the lines 3 to 5, and
    # the same record whose fields carry no lines
    # When `validate_record` runs on each
    # Then the `error` has `where` `5` for the first and `Wio-Stage` for the second
    pytest.skip(STUB)


def test_the_place_of_an_absent_field_is_the_first_line_or_its_key() -> None:
    """AC-8: a gate without a result."""
    # Given R with the stage `architecture-review` and no `Wio-Result`, with the
    # lines 3 to 5 and without lines
    # When `validate_record` runs on each
    # Then the `error` has `where` `3`, the record's first line, for the first and
    # `Wio-Result` for the second
    pytest.skip(STUB)


def test_each_diagnostic_points_at_its_own_field() -> None:
    """AC-8: the warning and the error have their own lines."""
    # Given R with `Wio-Stage: integration` on line 5 and `Wio-Items: AC-99` on
    # line 6
    # When `validate_record` runs
    # Then the `error` for `AC-99` has `where` `6` and the `warning` for
    # `integration` has `where` `5`
    pytest.skip(STUB)


def test_the_diagnostics_come_in_the_order_of_the_fields() -> None:
    """AC-9: the action, then the stage, then the item."""
    # Given R with `Wio-Action: nosuch`, `Wio-Stage: nosuch` and
    # `Wio-Items: AC-99`, in that order of fields
    # When `validate_record` runs
    # Then it returns the `error` for the action, then the stage, then `AC-99`
    pytest.skip(STUB)


def test_a_list_of_works_gives_one_diagnostic_per_work_in_order() -> None:
    """AC-9: `b8c9d0` before `a7b2c4`."""
    # Given R with `Wio-Work: b8c9d0, a7b2c4` and `Wio-Items: AC-3`, where both
    # lack `AC-3` and their `deliver` lists `architecture`
    # When `validate_record` runs
    # Then it returns the `error` for `b8c9d0` and then the one for `a7b2c4`
    pytest.skip(STUB)


def test_a_warning_comes_before_an_error_of_a_later_field() -> None:
    """AC-9: the stage warning, then the item error."""
    # Given R with `Wio-Stage: integration` and `Wio-Items: AC-99`
    # When `validate_record` runs
    # Then it returns the `warning` for the stage, then the `error` for `AC-99`
    pytest.skip(STUB)


def test_an_absent_field_comes_at_its_place() -> None:
    """AC-9: the item error, then `result required`."""
    # Given R with the stage `architecture-review`, `Wio-Items: AC-99` and no
    # `Wio-Result`
    # When `validate_record` runs
    # Then it returns the `error` for `AC-99` and then `result required`
    pytest.skip(STUB)


def test_the_name_checks_stand_alone() -> None:
    """AC-10: `validate_names` judges only the names."""
    # Given R with `Wio-Work: zz9zz9`, `Wio-Action: nosuch`, `Wio-Stage: nosuch`
    # and `Wio-Items: AC-99`, and R with the stage `architecture-review` and
    # `Wio-Result: maybe`
    # When `validate_names` runs on each
    # Then it returns the two `error`s for the action and the stage, and none for
    # `zz9zz9` or `AC-99`, and for the second the one `error` naming `maybe`
    pytest.skip(STUB)
