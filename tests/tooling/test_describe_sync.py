# SPDX-License-Identifier: Apache-2.0
"""Anti-drift tests keeping `wio.describe` in sync with `wio.cli.table`."""

import typing

from wio.cli.table import COMMANDS, Component
from wio.describe import describe_command, registered_commands


def test_every_registered_cli_command_has_a_descriptor() -> None:
    """Every command in `wio.cli.table.COMMANDS` has a descriptor in `wio.describe`."""
    # Given the commands wired into the CLI table
    cli_commands = {entry.package for entry in COMMANDS}

    # When the descriptor registry is queried
    described = set(registered_commands())

    # Then the CLI table and descriptor registry match one-to-one
    assert cli_commands == described


def test_descriptor_registry_matches_cli_components() -> None:
    """Every descriptor in `wio.describe` names a `wio.cli.table.Component`."""
    # Given the component names declared in wio.cli.table
    components = set(typing.get_args(Component.__value__))

    # When the descriptor registry is queried
    described = set(registered_commands())

    # Then every described command is a valid component (in-progress components
    # without a wired CLI command yet are allowed)
    assert described <= components


def test_every_registered_descriptor_builds_cleanly() -> None:
    """Calling `describe_command` succeeds for every registered command."""
    # Given every command name in the registry
    names = registered_commands()

    # When each command is described
    descriptions = [describe_command(name) for name in names]

    # Then each description carries its own name, a summary and at least one form
    assert all(
        d.name == n and d.summary and d.forms
        for d, n in zip(descriptions, names, strict=True)
    )
