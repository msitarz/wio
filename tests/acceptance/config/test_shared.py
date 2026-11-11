# SPDX-License-Identifier: Apache-2.0
"""Acceptance tests of `wio config` where it shares helpers with other commands."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_mistyped_setting_and_a_mistyped_key_name_the_closest() -> None:
    """AC-4: the messages and exit codes of `show` and `check` are as before."""
    # Given a config with a `[stages]` table, and another whose stage `define` has a
    # `goal` and the key `sessionn`
    # When `wio config show stagez` and `wio config check` run on them
    # Then the first names `stagez` and `stages` and exits 2, and the second reports
    # `sessionn` and `session` and exits 1


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_warning_does_not_fail_the_check_and_an_error_does() -> None:
    """AC-6: `wio config check` exits 0 for a warning alone and 1 for an error."""
    # Given a config with a warning and no error and one with an error
    # When `wio config check` runs on both
    # Then it exits 0 and then 1, with the output it had
