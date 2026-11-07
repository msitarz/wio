# SPDX-License-Identifier: Apache-2.0
"""Tests of `ConfigSettings` and of the checks that join the check run."""

from typing import TYPE_CHECKING

import pytest

import wio.config
from tests.unit.config.fakes import CONFIG, FakeRepository, MemoryFileSystem, load_text
from wio.config import ConfigSettings, load_config
from wio.errors import ConfigurationError
from wio.models.config import Config
from wio.models.diagnostics import Diagnostic

if TYPE_CHECKING:
    from wio.config import CheckInputs
    from wio.ports import Settings


BAD = '[works]\nhierarchy = "nest"\n[trailers]\nreader = 3\n'


def _wired(text: str, checks: tuple[wio.config.Check, ...] = ()) -> Settings:
    """Wire `ConfigSettings` where the `Settings` port is expected.

    Args:
        text: The content of the config file.
        checks: The checks to run after the shape.

    Returns:
        The adapter, which type checking accepts as `Settings`.
    """
    return ConfigSettings(FakeRepository(), MemoryFileSystem({CONFIG: text}), checks)


def _error_at_x(_config: Config, _inputs: CheckInputs) -> list[Diagnostic]:
    """Report an error at `x` whatever the config is.

    Args:
        _config: Ignored.
        _inputs: Ignored.

    Returns:
        One error at `x`.
    """
    return [Diagnostic("error", "x", "a check found a problem")]


def _warning_and_note(_config: Config, _inputs: CheckInputs) -> list[Diagnostic]:
    """Report a warning and a note, which never block.

    Args:
        _config: Ignored.
        _inputs: Ignored.

    Returns:
        A warning and a note.
    """
    return [Diagnostic("warning", "w", "careful"), Diagnostic("note", "n", "fyi")]


def test_load_returns_the_config_or_raises_with_every_error() -> None:
    """AC-6: valid, two shape errors, and a valid one with a warning and a note."""
    # Given a valid config, one with two shape errors, and a valid one whose
    # checks return a warning and a note
    valid = _wired("")
    invalid = _wired(BAD)
    soft = _wired("", checks=(_warning_and_note,))

    # When load runs on each
    config = valid.load()
    with pytest.raises(ConfigurationError) as caught:
        invalid.load()
    soft_config = soft.load()

    # Then the first returns the Config, the second carries both errors in its
    # diagnostics and its message, and the third returns the Config
    assert config == Config()
    assert {d.where for d in caught.value.diagnostics} == {
        "works.hierarchy",
        "trailers.reader",
    }
    assert "works.hierarchy" in str(caught.value)
    assert "trailers.reader" in str(caught.value)
    assert soft_config == Config()


def test_an_added_check_joins_the_shape_in_one_run() -> None:
    """AC-7: a check returns its error beside the shape's, also with an error."""
    # Given a check that errors at x, a valid file and one with an unknown key
    valid = '[stages.s]\ngoal = "g"\n'
    unknown = '[stages.s]\ngoal = "g"\nsessions = "any"\n'

    # When load_config and Settings.load run on each
    first = load_text(valid, checks=(_error_at_x,))
    second = load_text(unknown, checks=(_error_at_x,))
    with pytest.raises(ConfigurationError):
        _wired(valid, checks=(_error_at_x,)).load()

    # Then the first holds that error, has no Config and load raises, and the
    # second holds the unknown key's error and that one together
    assert [d.where for d in first.diagnostics] == ["x"]
    assert first.config is None
    assert [d.where for d in second.diagnostics] == ["stages.s.sessions", "x"]


def test_the_loader_runs_the_checks_in_order_with_the_root_and_files() -> None:
    """AC-7: a check gets the root of the repository and the file port."""
    # Given two checks that record what they were given
    seen: list[tuple[str, object]] = []

    def first(_config: Config, inputs: CheckInputs) -> list[Diagnostic]:
        seen.append(("first", inputs.root))
        return []

    def second(_config: Config, inputs: CheckInputs) -> list[Diagnostic]:
        seen.append(("second", inputs.files))
        return []

    files = MemoryFileSystem({CONFIG: ""})

    # When load_config runs
    load_config(FakeRepository(), files, checks=(first, second))

    # Then they ran in order with the root and the file port
    assert seen == [("first", CONFIG.parents[2]), ("second", files)]


def test_the_default_checks_are_the_ordered_tuple_of_wio_config() -> None:
    """AC-7: CHECKS is one tuple that the loader and Settings default to."""
    # Given the checks of wio.config

    # When they are read
    checks = wio.config.CHECKS

    # Then they are one tuple
    assert isinstance(checks, tuple)
