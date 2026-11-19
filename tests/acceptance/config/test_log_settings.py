# SPDX-License-Identifier: Apache-2.0
"""Acceptance scenarios for the event-log settings of a config."""

import pytest


def test_built_in_harnesses_need_no_configuration() -> None:
    """AC-1: The config exposes the built-in harnesses with default sources."""
    # Given a config that omits the log settings.
    # When the default settings are shown and the config is checked.
    # Then both harnesses have their default variables and the config passes.
    pytest.skip("Pending log settings wiring")


def test_configured_harnesses_add_or_replace_entries() -> None:
    """AC-2: A configured harness replaces a built-in harness as a whole."""
    # Given a config that adds a harness and replaces another.
    # When the settings are listed and shown.
    # Then the new harness appears and the replaced parent list is empty.
    pytest.skip("Pending log settings wiring")


def test_harness_preference_names_are_checked() -> None:
    """AC-3: The preference accepts known names and refuses invalid choices."""
    # Given configs with valid, unknown, repeated and reserved harness names.
    # When each config is checked.
    # Then the valid preference passes and each invalid config gives one error.
    pytest.skip("Pending log settings wiring")


def test_additional_environment_variables_replace_the_default() -> None:
    """AC-4: A project can select extra variables or select none."""
    # Given configs that set a list and an empty list of variables.
    # When each list is shown and its config is checked.
    # Then the file's list replaces the default and both configs pass.
    pytest.skip("Pending log settings wiring")


def test_invalid_log_settings_are_reported_and_refused() -> None:
    """AC-5: The config check reports bad settings and other commands refuse them."""
    # Given configs with individual errors in their log settings.
    # When each config is checked and used by a command.
    # Then the check names the offending key and the command refuses the config.
    pytest.skip("Pending log settings wiring")
