# SPDX-License-Identifier: Apache-2.0
"""Tests of the catalog of templates that `wio.contracts` asks for."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_template_is_found_by_name_and_a_missing_name_gives_none() -> None:
    """AC-3: `feature.leaf` in a subdirectory is found with its path."""
    # Given a config with the kind `feature` and a valid template `feature.leaf` of
    # that kind in a subdirectory of the templates directory
    # When `find("feature.leaf")` and `find("nosuch")` run
    # Then the first gives that template with its `path` relative to the root and the
    # second gives none


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_template_with_an_error_is_rejected_and_a_missing_one_is_not() -> None:
    """AC-4: errors reject, warnings and missing names do not."""
    # Given templates `good`, `warned`, `badkey`, `unclosed`, `baddirective` and two
    # files named `twin`
    # When `is_rejected` runs for each and for `nosuch`, and `find` runs for `unclosed`
    # Then it is false for `good`, `warned` and `nosuch`, and true for the rest, and
    # `find("unclosed")` gives none


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_refused_templates_directory_rejects_no_name() -> None:
    """AC-4: a symbolic link as the directory."""
    # Given a templates directory that is a symbolic link
    # When `is_rejected` runs for any name
    # Then it is false


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_templates_are_discovered_once_and_checked_once() -> None:
    """AC-5: the reads are those of one discovery and one check, in either order."""
    # Given a catalog over a file system that counts the reads of each template, and
    # the counts of a reference `discover` and a whole `check_templates`
    # When `find` runs twice and `is_rejected` three times, and on a fresh catalog
    # `is_rejected` runs twice and `find` twice
    # Then the counts follow the reference runs after each call, and the config file is
    # not counted
