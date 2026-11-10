# SPDX-License-Identifier: Apache-2.0
"""Tests of `TemplatesCommand` in `wio.templates`, run against fakes."""

from argparse import Namespace
from typing import TYPE_CHECKING

import pytest

from tests.unit.fakes import FakeRepository, FakeStdio, MemoryFileSystem
from wio.templates import TemplatesCommand

if TYPE_CHECKING:
    from wio.models.config import Config


class _NoSettings:
    """A `Settings` that fails the test when it is asked for the config."""

    def load(self) -> Config:
        """Fail: the command must not load the config.

        Raises:
            AssertionError: Always.
        """
        message = "the settings were loaded"
        raise AssertionError(message)


def test_bare_templates_writes_its_help_and_loads_no_config() -> None:
    """AC-4: the help is written and the settings are never loaded."""
    # Given a command whose settings fail when they are loaded
    command = TemplatesCommand(_NoSettings(), FakeRepository(), MemoryFileSystem())
    streams = FakeStdio()
    args = Namespace(templates_view=None, templates_help=lambda: "usage: wio templates")

    # When it runs with no subcommand
    code = command.run(args, streams)

    # Then the help is written, the exit code is 0 and nothing else was done
    streams.stdout.seek(0)
    assert (code, streams.stdout.read()) == (0, "usage: wio templates")


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_kind_that_the_config_does_not_declare_is_refused() -> None:
    """AC-5: `--kind` names a declared kind, or the message lists the declared ones."""
    # Given a config that declares two kinds
    # When `list` runs with an undeclared kind
    # Then it raises an error that names the kind and the declared kinds


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_template_error_refuses_the_list_and_lists_nothing() -> None:
    """AC-6: the errors are the message, `check` is named and nothing is written."""
    # Given templates, one of which has an error
    # When `list` runs
    # Then it raises an error that holds the diagnostics and names the check,
    # and standard output is empty
