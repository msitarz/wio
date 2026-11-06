# SPDX-License-Identifier: Apache-2.0
"""Tests of `Config` and of the `frozendict` helper of `wio.models`."""

import dataclasses
import inspect
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest

from wio.models import config as module
from wio.models.config import Config, Stage
from wio.models.frozen import freeze

if TYPE_CHECKING:
    from collections.abc import MutableMapping

SRC = Path(__file__).resolve().parents[3] / "src"


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


def test_a_config_is_immutable_and_hashable() -> None:
    """A config cannot change and equal configs hash equal (AC-1)."""
    # Given a Config with one stage, an equal one, and a field name
    config = Config(stages=freeze({"build": Stage(goal="Build it.")}))
    equal = Config(stages=freeze({"build": Stage(goal="Build it.")}))
    name = "results"
    table = cast("MutableMapping[str, Stage]", config.stages)

    # When a field is assigned, or a stage is added to `stages`
    with pytest.raises(FrozenInstanceError):
        setattr(config, name, ())
    with pytest.raises(TypeError):
        table["other"] = Stage()

    # Then each raises, and the hash equals that of an equal config
    assert hash(config) == hash(equal)
    assert config == equal


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


def test_one_helper_holds_the_only_pyrefly_suppression() -> None:
    """`freeze` builds a `frozendict` and holds the only suppression (AC-6)."""
    # Given the source tree and a mapping
    mapping = {"a": (1, 2)}
    marker = "pyrefly: " + "ignore"
    hits = [
        (path, line)
        for path in SRC.rglob("*.py")
        for line in path.read_text(encoding="utf-8").splitlines()
        if marker in line
    ]

    # When the mapping is frozen and the pyrefly suppressions of `src` are
    # searched
    frozen = freeze(mapping)

    # Then the result is a hashable frozendict, and one occurrence names
    # bad-argument-count, in the helper that names the known issue
    assert frozen == mapping
    assert isinstance(hash(frozen), int)
    assert len(hits) == 1
    path, line = hits[0]
    assert path.name == "frozen.py"
    assert "bad-argument-count" in line
    assert "known-issues.md" in path.read_text(encoding="utf-8")
