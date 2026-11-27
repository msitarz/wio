# SPDX-License-Identifier: Apache-2.0
"""Unit tests for `wio.describe` models and registry."""

import importlib.metadata

import pytest

from wio.describe import describe_command, describe_engine, registered_commands
from wio.errors import WioError
from wio.formats.directives import DIRECTIVES


def test_describe_engine_returns_version_codes_concepts_and_commands() -> None:
    """`describe_engine` derives version, exit codes, concepts and sorted commands."""
    # Given the installed work-it-out package
    expected_version = importlib.metadata.version("work-it-out")

    # When describe_engine is called
    engine = describe_engine()

    # Then version, exit codes, concepts and sorted commands are populated
    assert engine.version == expected_version
    assert [e.code for e in engine.exit_codes] == [0, 1, 2, 70]
    assert all(e.meaning for e in engine.exit_codes)
    assert engine.concepts
    names = [c.name for c in engine.commands]
    assert names == sorted(names)
    assert tuple(names) == registered_commands()


def test_describe_engine_is_deterministic() -> None:
    """Repeated calls to `describe_engine` return equal objects."""
    # Given no external state

    # When describe_engine is called twice
    first = describe_engine()
    second = describe_engine()

    # Then both results are identical
    assert first == second


def test_describe_engine_accepts_explicit_command_subset() -> None:
    """`describe_engine` sorts and filters when given explicit command names."""
    # Given an unsorted subset of valid command names
    subset = ("rules", "config")

    # When describe_engine is called with that subset
    engine = describe_engine(commands=subset)

    # Then only those commands appear in sorted order
    assert [c.name for c in engine.commands] == ["config", "rules"]


def test_describe_engine_rejects_unknown_command_in_subset() -> None:
    """`describe_engine` raises `WioError` when `commands` contains an unknown name."""
    # Given a subset with an unknown command name
    subset = ("config", "nosuch")

    # When describe_engine is called
    with pytest.raises(WioError, match="nosuch") as exc_info:
        describe_engine(commands=subset)

    # Then the error names valid commands
    assert "config" in str(exc_info.value)


def test_describe_command_config_includes_live_schema_keys() -> None:
    """`describe_command('config')` includes code-derived config schema keys."""
    # Given the config subcommand name

    # When describe_command is called for config
    desc = describe_command("config")

    # Then it returns forms, invariants and config schema reference entries
    assert desc.name == "config"
    assert desc.forms
    assert desc.invariants
    assert len(desc.references) == 1
    keys = {entry.key for entry in desc.references[0].entries}
    assert "works.dir" in keys
    assert "templates.dir" in keys
    assert "stages" in keys


def test_describe_command_templates_includes_live_directives() -> None:
    """`describe_command('templates')` includes the live directive table."""
    # Given the live directive names from wio.formats.directives
    expected_directives = {spec.name for spec in DIRECTIVES}

    # When describe_command is called for templates
    desc = describe_command("templates")

    # Then the reference table includes every directive
    assert desc.name == "templates"
    assert len(desc.references) == 1
    keys = {entry.key for entry in desc.references[0].entries}
    assert expected_directives <= keys


def test_describe_command_raises_wio_error_for_unknown_name() -> None:
    """`describe_command` raises `WioError` naming valid commands when unknown."""
    # Given an unknown command name
    unknown = "nonexistent"

    # When describe_command is called
    with pytest.raises(WioError) as exc_info:
        describe_command(unknown)

    # Then the error names the unknown command and every valid command
    message = str(exc_info.value)
    assert unknown in message
    for name in registered_commands():
        assert name in message
