# SPDX-License-Identifier: Apache-2.0
"""Tests of `Config` and of the `frozendict` helper of `wio.models`."""

import pytest

STUB = pytest.mark.skip(reason="a stub until the implementation stage")


@STUB
def test_a_config_with_no_arguments_holds_the_defaults() -> None:
    """A `Config()` is the settings of an empty config file (AC-1)."""
    # Given `Config()`.

    # When its fields are read.

    # Then the defaults of AC-1 hold and every open table is empty.


@STUB
def test_a_config_is_immutable_and_hashable() -> None:
    """A config cannot change and equal configs hash equal (AC-1)."""
    # Given a `Config` with one stage.

    # When a field is assigned, or a stage is added to `stages`.

    # Then each raises, and the hash equals that of an equal config.


@STUB
def test_every_setting_has_a_description() -> None:
    """Each field of each type reachable from `Config` is described (AC-2)."""
    # Given every dataclass reachable from `Config`.

    # When their fields are listed.

    # Then each has a non-empty `description` in its metadata.


@STUB
def test_one_helper_holds_the_only_pyrefly_suppression() -> None:
    """`freeze` builds a `frozendict` and holds the only suppression (AC-6)."""
    # Given the source tree and a mapping.

    # When the mapping is frozen and the pyrefly suppressions of `src` are
    # searched.

    # Then the result is a hashable `frozendict`, and one occurrence names `bad-
    # argument-count` and the known issue, in the helper.
