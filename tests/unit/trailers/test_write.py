# SPDX-License-Identifier: Apache-2.0
"""Tests of the write form of `wio trailers`, run with fakes of its ports.

Each test is a stub for one scenario of the Work that builds the write form, and
skips until the implementation stage fills it in. The examples use a Work `k3m9xq`
in the working tree with the items `AC-1` and `AC-3`, a leaf whose `deliver` is the
`typed-boundary` stage preset, which lists `architecture`, which is not a gate, and
`architecture-review`, which is a gate. The config also has the stage
`integration`, which that preset does not list, and its results are `pass`, `fail`
and `unknown`.
"""

import pytest

STUB = "filled in by the implementation stage"


def test_a_valid_record_is_printed() -> None:
    """AC-1: a Work, an action, a stage and items, in the order given."""
    # Given `k3m9xq`
    # When `wio trailers k3m9xq deliver architecture --items AC-3,AC-1` runs
    # Then it prints exactly the four lines `Wio-Work: k3m9xq`,
    # `Wio-Action: deliver`, `Wio-Stage: architecture` and `Wio-Items: AC-3, AC-1`,
    # each ending with a newline, and exits 0
    pytest.skip(STUB)


def test_a_gate_with_a_result_gets_a_judge() -> None:
    """AC-1: `agent` by default, and `human` or `agent` with `--judge`."""
    # Given the gate stage `architecture-review`
    # When `wio trailers k3m9xq deliver architecture-review --items AC-1 --result
    # pass` runs, and again with `--judge human` and with `--judge agent`
    # Then each prints the five lines and then `Wio-Judge: agent` for the first and
    # the third and `Wio-Judge: human` for the second, and exits 0
    pytest.skip(STUB)


def test_a_work_that_only_head_has_is_printed() -> None:
    """AC-1: the `Contracts` port finds `d4e5f6` in `HEAD`."""
    # Given a leaf Work `d4e5f6` that the port finds and the working tree lacks
    # When `wio trailers d4e5f6 deliver architecture` runs
    # Then it prints the record of `d4e5f6` and exits 0
    pytest.skip(STUB)


def test_a_cited_item_is_ignored() -> None:
    """AC-1: `--cite` changes neither stream and the exit code."""
    # Given the gate stage `architecture-review`
    # When `wio trailers k3m9xq deliver architecture-review --result pass --cite
    # AC-1=pass` runs
    # Then its standard output and standard error equal those of the same command
    # without `--cite`, and it exits 0
    pytest.skip(STUB)


def test_a_work_an_action_or_a_stage_that_is_not_valid_is_refused() -> None:
    """AC-2: each is exit 1 with the key and the value on standard error."""
    # Given a Work id `zz9zz9` that exists nowhere, and `k3m9xq`
    # When `wio trailers zz9zz9 deliver architecture`, `wio trailers k3m9xq nosuch
    # architecture` and `wio trailers k3m9xq deliver nosuch` run
    # Then each exits 1, prints nothing on standard output and prints an
    # `error: Wio-Work:`, `error: Wio-Action:` or `error: Wio-Stage:` line naming
    # `zz9zz9`, `nosuch` and `nosuch`
    pytest.skip(STUB)


def test_an_item_and_a_result_that_are_not_valid_are_refused() -> None:
    """AC-2: `AC-99` and `maybe`."""
    # Given the gate stage `architecture-review`, and the item `AC-99`, which
    # `k3m9xq` lacks
    # When `wio trailers k3m9xq deliver architecture --items AC-99` and `wio
    # trailers k3m9xq deliver architecture-review --result maybe` run
    # Then each exits 1, prints nothing on standard output and prints an
    # `error: Wio-Items:` line naming `AC-99` and an `error: Wio-Result:` line
    # naming `maybe`
    pytest.skip(STUB)


def test_a_result_that_does_not_fit_its_stage_is_refused() -> None:
    """AC-2: `result required` and `not a gate`."""
    # Given the gate stage `architecture-review` and the stage `architecture`
    # When `wio trailers k3m9xq deliver architecture-review` and `wio trailers
    # k3m9xq deliver architecture --result pass` run
    # Then each exits 1, prints nothing on standard output and reports
    # `result required` and `not a gate` on standard error
    pytest.skip(STUB)


def test_malformed_items_a_work_id_and_a_judge_are_refused_by_form() -> None:
    """AC-3: one `error:` line and its offending line, and no validator line."""
    # Given `k3m9xq`
    # When `wio trailers k3m9xq deliver architecture --items "AC-1 AC-3"`, `wio
    # trailers "k3 m9xq" deliver architecture` and `wio trailers k3m9xq deliver
    # architecture-review --result pass --judge robot` run
    # Then each exits 1, prints nothing on standard output and prints one `error:`
    # line followed by its offending line on standard error that names
    # `Wio-Items`, `Wio-Work` and `Wio-Judge`, and no line from the validator
    pytest.skip(STUB)


def test_a_judge_without_a_result_is_refused() -> None:
    """AC-3: `--judge human` alone."""
    # Given `k3m9xq`
    # When `wio trailers k3m9xq deliver architecture --judge human` runs
    # Then the command exits 1, prints nothing on standard output and names
    # `Wio-Judge` on standard error
    pytest.skip(STUB)


def test_an_empty_or_multi_line_argument_cannot_add_a_line() -> None:
    """AC-3: the four refused arguments."""
    # Given `k3m9xq`
    # When `--items ""`, `--items $'AC-1\nWio-Result: pass'`, `--result
    # $'pass\nWio-Judge: human'` and an empty stage run
    # Then each exits 1, prints nothing on standard output and names `Wio-Items`,
    # `Wio-Items`, `Wio-Result` and `Wio-Stage` on standard error
    pytest.skip(STUB)


def test_a_stage_outside_the_pipeline_is_a_warning_and_the_record_is_printed() -> None:
    """AC-4: the record on standard output, the warning on standard error."""
    # Given `k3m9xq`, whose `deliver` does not list `integration`
    # When `wio trailers k3m9xq deliver integration` runs
    # Then the record is on standard output, the warning naming `integration` is on
    # standard error, and the command exits 0
    pytest.skip(STUB)


def test_a_call_with_no_stage_is_a_usage_error() -> None:
    """AC-5: argparse refuses it and prints nothing on standard output."""
    # Given `k3m9xq`
    # When `wio trailers k3m9xq deliver` runs
    # Then the command exits 2 and prints nothing on standard output
    pytest.skip(STUB)


def test_an_unknown_option_a_list_of_works_and_none_are_usage_errors() -> None:
    """AC-5: argparse and `TrailersError` both exit 2."""
    # Given the option `--nosuch`, the Work value `k3m9xq,a7b2c4` and the Work
    # value `none`, which this form does not write
    # When the three calls run
    # Then each exits 2 and prints nothing on standard output
    pytest.skip(STUB)


def test_a_config_that_cannot_be_read_is_a_usage_error() -> None:
    """AC-5: the `ConfigurationError` of the settings is not caught."""
    # Given settings that raise a `ConfigurationError`
    # When `wio trailers k3m9xq deliver architecture` runs
    # Then the error propagates, which `wio.cli` turns into exit 2 with nothing on
    # standard output
    pytest.skip(STUB)
