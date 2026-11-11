# SPDX-License-Identifier: Apache-2.0
"""Acceptance tests of `wio templates` where it shares helpers with other commands."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_mistyped_key_in_a_template_names_the_closest() -> None:
    """AC-5: `descriptions` gets a suggestion and `zzz` does not."""
    # Given a config with the kind `feature` and two templates, one with the key
    # `descriptions` and one with the key `zzz`
    # When `wio templates check` runs
    # Then it reports both unknown keys, the first with `Did you mean `description`?`,
    # each at its file, and exits 1


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_templates_commands_print_what_they_printed() -> None:
    """AC-9: the repository's templates and a templates directory that is a link."""
    # Given this repository's templates, and a repository whose templates directory is a
    # symbolic link
    # When `list`, `check` and `check --json` run on each
    # Then the first prints what it printed and `The templates pass.`, and the second
    # reports the link with exit 1 for `check` and 2 for `list`
