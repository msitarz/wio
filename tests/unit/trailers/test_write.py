# SPDX-License-Identifier: Apache-2.0
"""Tests of the write form of `wio trailers`, run with fakes of its ports.

The examples use a Work `k3m9xq` with the items `AC-1` and `AC-3`, a leaf whose
`deliver` is the `typed-boundary` stage preset, which lists `architecture`, which
is not a gate, and `architecture-review`, which is a gate. The config also has the
stage `integration`, which that preset does not list, and its results are `pass`,
`fail` and `unknown`. The Work `d4e5f6` stands for one that only `HEAD` has, which
the `Contracts` port finds wherever it is.
"""

import io
from argparse import ArgumentParser
from dataclasses import dataclass

import pytest

from tests.unit.fakes import FakeStdio
from tests.unit.trailers.test_validation import CONFIG, FakeContracts
from wio.errors import ConfigurationError
from wio.trailers import Services
from wio.trailers.errors import TrailersError
from wio.trailers.write import configure_write, run_write
lazy from wio.models.config import Config


@dataclass(frozen=True)
class FakeSettings:
    """The `Settings` port, loading a fixed config or failing."""

    failure: Exception | None = None

    def load(self) -> Config:
        """Load the config.

        Returns:
            The config of the examples.

        Raises:
            Exception: The failure the fake was given.
        """
        if self.failure is not None:
            raise self.failure
        return CONFIG


def _run(argv: list[str], settings: FakeSettings | None = None) -> tuple[int, str, str]:
    """Run the write form on the arguments.

    Args:
        argv: The arguments after `wio trailers`.
        settings: The settings, which load the config of the examples by default.

    Returns:
        The exit code, standard output and standard error.
    """
    parser = ArgumentParser(prog="wio trailers")
    configure_write(parser)
    args = parser.parse_args(argv)
    out, err = io.StringIO(), io.StringIO()
    services = Services(settings or FakeSettings(), FakeContracts())
    code = run_write(services, args, FakeStdio(stdout=out, stderr=err))
    return code, out.getvalue(), err.getvalue()


R = ["k3m9xq", "deliver", "architecture"]
GATE = ["k3m9xq", "deliver", "architecture-review"]


def test_a_valid_record_is_printed() -> None:
    """AC-1: a Work, an action, a stage and items, in the order given."""
    # Given `k3m9xq`
    # When `wio trailers k3m9xq deliver architecture --items AC-3,AC-1` runs
    code, out, err = _run([*R, "--items", "AC-3,AC-1"])

    # Then it prints exactly the four lines, each ending with a newline, and
    # exits 0
    assert out == (
        "Wio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: architecture\n"
        "Wio-Items: AC-3, AC-1\n"
    )
    assert (code, err) == (0, "")


@pytest.mark.parametrize(
    ("extra", "judge"),
    [([], "agent"), (["--judge", "human"], "human"), (["--judge", "agent"], "agent")],
    ids=["default", "human", "agent"],
)
def test_a_gate_with_a_result_gets_a_judge(extra: list[str], judge: str) -> None:
    """AC-1: `agent` by default, and `human` or `agent` with `--judge`."""
    # Given the gate stage `architecture-review`
    # When the command runs with `--items AC-1 --result pass`, and with a judge
    code, out, _ = _run([*GATE, "--items", "AC-1", "--result", "pass", *extra])

    # Then it prints the five lines and then the judge, and exits 0
    assert out == (
        "Wio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: architecture-review\n"
        f"Wio-Items: AC-1\nWio-Result: pass\nWio-Judge: {judge}\n"
    )
    assert code == 0


def test_a_work_that_only_head_has_is_printed() -> None:
    """AC-1: the `Contracts` port finds `d4e5f6` wherever it is."""
    # Given a leaf Work `d4e5f6` that the port finds
    # When `wio trailers d4e5f6 deliver architecture` runs
    code, out, _ = _run(["d4e5f6", "deliver", "architecture"])

    # Then it prints the record of `d4e5f6` and exits 0
    assert out.startswith("Wio-Work: d4e5f6\n")
    assert code == 0


def test_a_cited_item_is_ignored() -> None:
    """AC-1: `--cite` changes neither stream and the exit code."""
    # Given the gate stage `architecture-review`
    # When the command runs with and without `--cite AC-1=pass`
    with_cite = _run([*GATE, "--result", "pass", "--cite", "AC-1=pass"])
    without = _run([*GATE, "--result", "pass"])

    # Then the exit code and both streams are the same, and the code is 0
    assert with_cite == without
    assert with_cite[0] == 0


@pytest.mark.parametrize(
    ("argv", "key", "value"),
    [
        (["zz9zz9", "deliver", "architecture"], "Wio-Work", "zz9zz9"),
        (["k3m9xq", "nosuch", "architecture"], "Wio-Action", "nosuch"),
        (["k3m9xq", "deliver", "nosuch"], "Wio-Stage", "nosuch"),
    ],
    ids=["work", "action", "stage"],
)
def test_a_work_an_action_or_a_stage_that_is_not_valid_is_refused(
    argv: list[str], key: str, value: str
) -> None:
    """AC-2: each is exit 1 with the key and the value on standard error."""
    # Given a Work id `zz9zz9` that exists nowhere, and `k3m9xq`
    # When the command runs on each
    code, out, err = _run(argv)

    # Then it exits 1, prints nothing on standard output and names the key and the
    # value on standard error
    assert (code, out) == (1, "")
    assert f"error: {key}:" in err
    assert value in err


@pytest.mark.parametrize(
    ("argv", "key", "value"),
    [
        ([*R, "--items", "AC-99"], "Wio-Items", "AC-99"),
        ([*GATE, "--result", "maybe"], "Wio-Result", "maybe"),
    ],
    ids=["item", "result"],
)
def test_an_item_and_a_result_that_are_not_valid_are_refused(
    argv: list[str], key: str, value: str
) -> None:
    """AC-2: `AC-99` and `maybe`."""
    # Given the gate stage `architecture-review`, and the item `AC-99`
    # When the command runs on each
    code, out, err = _run(argv)

    # Then it exits 1, prints nothing on standard output and names the key
    assert (code, out) == (1, "")
    assert f"error: {key}:" in err
    assert value in err


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (GATE, "result required"),
        ([*R, "--result", "pass"], "not a gate"),
    ],
    ids=["missing", "stray"],
)
def test_a_result_that_does_not_fit_its_stage_is_refused(
    argv: list[str], message: str
) -> None:
    """AC-2: `result required` and `not a gate`."""
    # Given the gate stage `architecture-review` and the stage `architecture`
    # When the command runs on each
    code, out, err = _run(argv)

    # Then it exits 1, prints nothing on standard output and reports the message
    assert (code, out) == (1, "")
    assert message in err


@pytest.mark.parametrize(
    ("argv", "key"),
    [
        ([*R, "--items", "AC-1 AC-3"], "Wio-Items"),
        (["k3 m9xq", "deliver", "architecture"], "Wio-Work"),
        ([*GATE, "--result", "pass", "--judge", "robot"], "Wio-Judge"),
    ],
    ids=["items", "work", "judge"],
)
def test_malformed_items_a_work_id_and_a_judge_are_refused_by_form(
    argv: list[str], key: str
) -> None:
    """AC-3: one `error:` line and its offending line, and no validator line."""
    # Given `k3m9xq`
    # When the command runs on each
    code, out, err = _run(argv)

    # Then it exits 1, prints nothing on standard output and prints one `error:`
    # line and the offending line naming the key
    lines = err.splitlines()
    assert (code, out) == (1, "")
    assert len(lines) == 2
    assert lines[0].startswith(f"error: {key}:")
    assert lines[1].startswith(f"{key}:")


def test_a_judge_without_a_result_is_refused() -> None:
    """AC-3: `--judge human` alone, before the record is rendered."""
    # Given `k3m9xq`
    # When `wio trailers k3m9xq deliver architecture --judge human` runs
    code, out, err = _run([*R, "--judge", "human"])

    # Then the command exits 1, prints nothing on standard output and names
    # `Wio-Judge` on standard error, in one finding of the form and not of the
    # shape check
    assert (code, out) == (1, "")
    assert err.splitlines()[0].startswith("error: Wio-Judge:")
    assert len(err.splitlines()) == 2


@pytest.mark.parametrize(
    ("argv", "key"),
    [
        ([*R, "--items", ""], "Wio-Items"),
        ([*R, "--items", "AC-1\nWio-Result: pass"], "Wio-Items"),
        ([*GATE, "--result", "pass\nWio-Judge: human"], "Wio-Result"),
        (["k3m9xq", "deliver", ""], "Wio-Stage"),
        ([*GATE, "--result", "pass", "--judge", ""], "Wio-Judge"),
    ],
    ids=["empty-items", "items-line", "result-line", "empty-stage", "empty-judge"],
)
def test_an_empty_or_multi_line_argument_cannot_add_a_line(
    argv: list[str], key: str
) -> None:
    """AC-3: each refused argument names its field and prints no record."""
    # Given `k3m9xq`
    # When the command runs on each
    code, out, err = _run(argv)

    # Then it exits 1, prints nothing on standard output and names the key, in one
    # `error:` line and one offending line, whatever the argument held
    assert (code, out) == (1, "")
    assert f"error: {key}:" in err
    assert len(err.splitlines()) == 2


def test_a_stage_outside_the_pipeline_is_a_warning_and_the_record_is_printed() -> None:
    """AC-4: the record on standard output, the warning on standard error."""
    # Given `k3m9xq`, whose `deliver` does not list `integration`
    # When `wio trailers k3m9xq deliver integration` runs
    code, out, err = _run(["k3m9xq", "deliver", "integration"])

    # Then the record is on standard output, the warning naming `integration` is on
    # standard error, and the command exits 0
    assert out.startswith("Wio-Work: k3m9xq\n")
    assert "warning" in err
    assert "integration" in err
    assert code == 0


def test_a_call_with_no_stage_is_a_usage_error() -> None:
    """AC-5: argparse refuses it and prints nothing on standard output."""
    # Given `k3m9xq`
    # When `wio trailers k3m9xq deliver` runs
    # Then argparse exits 2
    with pytest.raises(SystemExit) as caught:
        _run(["k3m9xq", "deliver"])
    assert caught.value.code == 2


@pytest.mark.parametrize("work", ["k3m9xq,a7b2c4", "none"])
def test_a_list_of_works_and_none_are_usage_errors(work: str) -> None:
    """AC-5: the form refuses them with a `TrailersError`, which exits 2."""
    # Given the Work value `k3m9xq,a7b2c4` and the Work value `none`
    # When the command runs on each
    # Then it raises a `TrailersError` and writes nothing
    with pytest.raises(TrailersError):
        _run([work, "deliver", "architecture"])


def test_an_unknown_option_is_a_usage_error() -> None:
    """AC-5: argparse refuses `--nosuch`."""
    # Given the option `--nosuch`
    # When `wio trailers k3m9xq deliver architecture --nosuch` runs
    # Then argparse exits 2
    with pytest.raises(SystemExit) as caught:
        _run([*R, "--nosuch"])
    assert caught.value.code == 2


@pytest.mark.parametrize("work", ["k3m9xq,a7b2c4", "none"])
def test_a_list_of_works_is_refused_before_the_config_is_loaded(work: str) -> None:
    """AC-5: the `TrailersError` comes first, so a bad config does not hide it."""
    # Given settings that raise a `ConfigurationError`
    settings = FakeSettings(ConfigurationError("The config is not valid TOML."))

    # When the command runs on a list of Works and on `none`
    # Then it raises a `TrailersError` and not the `ConfigurationError`
    with pytest.raises(TrailersError):
        _run([work, "deliver", "architecture"], settings)


def test_a_config_that_cannot_be_read_is_a_usage_error() -> None:
    """AC-5: the `ConfigurationError` of the settings is not caught."""
    # Given settings that raise a `ConfigurationError`
    settings = FakeSettings(ConfigurationError("The config is not valid TOML."))

    # When `wio trailers k3m9xq deliver architecture` runs
    # Then the error propagates, which `wio.cli` turns into exit 2
    with pytest.raises(ConfigurationError):
        _run(R, settings)
