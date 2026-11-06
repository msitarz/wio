# SPDX-License-Identifier: Apache-2.0
"""Tests of `Config` and of the `frozendict` helper of `wio.models`."""

import dataclasses
import inspect

import pytest

from wio.models import config as module
from wio.models.config import Config

STUB = pytest.mark.skip(reason="a stub until the implementation stage")


def test_a_config_with_no_arguments_holds_the_defaults() -> None:
    """A `Config()` is the settings of an empty config file (AC-1)."""
    # Given `Config()`.
    config = Config()

    # When its fields are read.
    tables = [
        config.actions,
        config.roots,
        config.stages,
        config.stage_presets,
        config.rule_presets,
        config.rulesets,
        config.works.defaults.actions,
        config.templates.kinds,
    ]

    # Then the defaults of AC-1 hold and every open table is empty.
    assert config.results == ("pass", "fail", "unknown")
    assert config.works.hierarchy == "flat"
    assert config.works.dir == ".agents/wio/works"
    assert config.templates.dir == ".agents/wio/templates"
    assert config.trailers.reader == "scan"
    assert config.bundle.separator == "\n\n"
    assert config.bundle.size_threshold is None
    assert config.skills.paths == ()
    assert config.rules_always_include == config.rules_always_exclude == ()
    assert all(len(table) == 0 for table in tables)


@STUB
def test_a_config_is_immutable_and_hashable() -> None:
    """A config cannot change and equal configs hash equal (AC-1)."""
    # Given a `Config` with one stage, and an equal one

    # When a field is assigned, or a stage is added to `stages`

    # Then each raises, and the hash equals that of an equal config


def test_every_setting_has_a_description() -> None:
    """Each field of each type reachable from `Config` is described (AC-2)."""
    # Given every dataclass of the module
    classes = [
        c
        for _, c in inspect.getmembers(module, inspect.isclass)
        if dataclasses.is_dataclass(c) and c.__module__ == module.__name__
    ]

    # When their fields are listed
    undescribed = [
        f"{c.__name__}.{f.name}"
        for c in classes
        for f in dataclasses.fields(c)
        if not f.metadata.get("description")
    ]

    # Then each has a non-empty description in its metadata
    assert len(classes) == 12
    assert undescribed == []


@STUB
def test_one_helper_holds_the_only_pyrefly_suppression() -> None:
    """`freeze` builds a `frozendict` and holds the only suppression (AC-6)."""
    # Given the source tree and a mapping.

    # When the mapping is frozen and the pyrefly suppressions of `src` are
    # searched.

    # Then the result is a hashable `frozendict`, and one occurrence names `bad-
    # argument-count` and the known issue, in the helper.
