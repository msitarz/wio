# SPDX-License-Identifier: Apache-2.0
"""Tests of the table of commands and of the import-light check."""

import pytest

pytestmark = pytest.mark.skip(reason="architecture stub: the command-table leaf")


def test_describing_an_entry_does_not_wire_it() -> None:
    """The `describe` of a `component_entry` returns the spec and wires nothing."""
    # Given a stand-in module installed as wio.config whose describe() returns a
    # spec, and an entry from component_entry("config", wire)

    # When the entry's describe() is called

    # Then it returns that spec and wire was not called


def test_the_component_names_match_the_packages() -> None:
    """`Component` names exactly the packages that are components."""
    # Given the packages directly under src/wio and the packages that are not
    # components, listed in this test (assumption A-2)

    # When the first without the second is compared to the names in Component

    # Then the two are equal (the names come from
    # typing.get_args(Component.__value__), because Component is a `type` alias)


def test_every_entry_of_the_real_table_names_a_component() -> None:
    """Each entry of the real table has a package that `Component` names."""
    # Given the real table of commands

    # When each entry's package is read

    # Then each is a name in Component


def test_import_light_violations_names_an_eager_import() -> None:
    """The check names the implementation that an eager package loads."""
    # Given two fixture packages, created in the implementation stage, one whose
    # __init__ imports an implementation module eagerly and one that imports it
    # lazily, each with a describe

    # When import_light_violations runs for each

    # Then it returns the implementation module for the first and an empty list
    # for the second


def test_every_entry_of_the_real_table_is_import_light() -> None:
    """Describing a real command loads none of its implementation."""
    # Given the real table of commands

    # When import_light_violations runs for "wio." + entry.package of each

    # Then each returns an empty list
