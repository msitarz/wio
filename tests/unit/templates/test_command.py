# SPDX-License-Identifier: Apache-2.0
"""Tests of `TemplatesCommand` in `wio.templates`, run against fakes."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_bare_templates_writes_its_help_and_loads_no_config() -> None:
    """AC-4: the help is written and the settings are never loaded."""
    # Given a command whose settings port records its calls
    # When it runs with no subcommand
    # Then the help is written, the exit code is 0 and the settings were not loaded


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
