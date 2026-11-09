# SPDX-License-Identifier: Apache-2.0
"""Tests that the loader refuses a config with the errors that the checks report."""

from pathlib import Path

import pytest

from tests.unit.config.fakes import CONFIG, FakeRepository, MemoryFileSystem
from wio.config import ConfigSettings, load_config
from wio.errors import ConfigurationError

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "config"


def _files(fixture: str) -> MemoryFileSystem:
    """Hold the config of a fixture, and nothing else, in memory.

    Args:
        fixture: The name of the fixture under `tests/fixtures/config`.

    Returns:
        A file system that has the config file.
    """
    text = (FIXTURES / fixture / ".agents" / "wio" / "config.toml").read_text(
        encoding="utf-8"
    )
    return MemoryFileSystem({CONFIG: text})


def test_load_raises_with_every_error_that_the_check_run_reports() -> None:
    """AC-2: `Settings.load` carries the five errors that `check` prints."""
    # Given a config with one error from each group of checks
    files = _files("checks-several")
    reported = [
        d
        for d in load_config(FakeRepository(), files).diagnostics
        if d.severity == "error"
    ]

    # When the settings are loaded
    with pytest.raises(ConfigurationError) as caught:
        ConfigSettings(FakeRepository(), files).load()

    # Then the error holds the five, the same ones, and renders them as lines
    assert len(reported) == 5
    assert caught.value.diagnostics == tuple(reported)
    assert str(caught.value).splitlines()[0].startswith("error: roots.out.paths[0]")


def test_load_does_not_refuse_for_a_warning_or_a_note() -> None:
    """AC-2: only an error blocks the other commands."""
    # Given a config with a warning and a note and no error
    files = _files("checks-quiet")

    # When the settings are loaded
    config = ConfigSettings(FakeRepository(), files).load()

    # Then the config is returned
    assert config.rules_always_include == ("p",)
