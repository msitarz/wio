# SPDX-License-Identifier: Apache-2.0
"""Tests of `load_config`: finding the file, defaults, sources and syntax errors."""

import dataclasses
from collections.abc import Mapping
from typing import TYPE_CHECKING

import pytest

from tests.unit.config.fakes import (
    CONFIG,
    ROOT,
    FakeRepository,
    MemoryFileSystem,
    load_text,
)
from wio.config import load_config
from wio.errors import ConfigurationError
from wio.models.config import Config

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

SHAPE = pytest.mark.skip(reason="needs the shape, stubbed until implementation")


@SHAPE
def test_the_file_is_read_at_the_root_of_the_repository() -> None:
    """AC-1: the file is `<root>/.agents/wio/config.toml`."""
    # Given a repository whose config sets the hierarchy to nesting
    text = '[works]\nhierarchy = "nesting"\n'
    files = MemoryFileSystem({CONFIG: text})

    # When load_config runs
    loaded = load_config(FakeRepository(), files)

    # Then the hierarchy is nesting
    assert loaded.config is not None
    assert loaded.config.works.hierarchy == "nesting"


def test_a_missing_repository_names_the_working_directory() -> None:
    """AC-1: outside any repository the error names where the process is."""
    # Given a directory outside any repository
    repository = FakeRepository(top=None, message="not inside a repository: /work")

    # When load_config runs
    with pytest.raises(ConfigurationError) as caught:
        load_config(repository, MemoryFileSystem())

    # Then the error names the working directory and not wio init
    assert "/work" in str(caught.value)
    assert "wio init" not in str(caught.value)


def test_a_missing_file_names_the_path_looked_at() -> None:
    """AC-1: a repository without a config names the path it looked at."""
    # Given a repository without a config file
    files = MemoryFileSystem()

    # When load_config runs
    with pytest.raises(ConfigurationError) as caught:
        load_config(FakeRepository(), files)

    # Then the error names the path and not wio init
    assert str(CONFIG) in str(caught.value)
    assert "wio init" not in str(caught.value)


def test_a_file_that_cannot_be_read_is_a_configuration_error() -> None:
    """AC-1: a file that is not UTF-8 text is refused with its path."""

    # Given a config file whose text cannot be decoded
    reason = "invalid start byte"
    failure = UnicodeDecodeError("utf-8", b"\xff", 0, 1, reason)
    files = MemoryFileSystem({CONFIG: ""}, failure=failure)

    # When load_config runs
    with pytest.raises(ConfigurationError) as caught:
        load_config(FakeRepository(), files)

    # Then the error names the path
    assert str(CONFIG) in str(caught.value)


@SHAPE
def test_an_empty_file_and_a_partial_one_keep_the_defaults() -> None:
    """AC-2: a key the file does not set has the default of its field."""
    # Given an empty file, and one that sets a reader and one stage
    partial = '[trailers]\nreader = "git"\n[stages.define]\ngoal = "g"\n'

    # When load_config runs on each
    empty_loaded = load_text("")
    partial_loaded = load_text(partial)

    # Then the first is Config() and the second has the reader and the stage
    assert empty_loaded.config == Config()
    assert empty_loaded.diagnostics == ()
    config = partial_loaded.config
    assert config is not None
    assert config.trailers.reader == "git"
    assert list(config.stages) == ["define"]
    assert config.stages["define"].session == "any"
    assert config.stages["define"].continuable is True
    assert (
        dataclasses.replace(config, trailers=Config().trailers, stages=Config().stages)
        == Config()
    )


def _paths(value: DataclassInstance, prefix: str = "") -> set[str]:
    """Walk the fields of a value as the schema defines them.

    Args:
        value: A `Config` or one of its tables.
        prefix: The key path of the value, with its trailing dot.

    Returns:
        The key path of every leaf setting that is not `None`.
    """
    found: set[str] = set()
    for item in dataclasses.fields(value):
        found |= _leaves(getattr(value, item.name), f"{prefix}{item.name}")
    return found


def _leaves(child: object, path: str) -> set[str]:
    """List the key paths below one field.

    Args:
        child: The value of the field.
        path: The key path of the field.

    Returns:
        Nothing for `None`, the entries of an open table, the leaves of a table,
        or the field's own path for any other value.
    """
    if child is None:
        return set()
    if isinstance(child, Mapping):
        return {f"{path}.{key}" for key in child}
    if dataclasses.is_dataclass(child) and not isinstance(child, type):
        return _paths(child, f"{path}.")
    return {path}


@SHAPE
def test_the_source_of_each_setting_is_the_file_or_the_default() -> None:
    """AC-3: a key set to its default is still `file`; the rest is `default`."""
    # Given a file that sets the default hierarchy and one stage with a goal
    text = '[works]\nhierarchy = "flat"\n[stages.define]\ngoal = "g"\n'

    # When load_config runs
    sources = load_text(text).sources

    # Then the sources say file and default, and cover every setting but the None
    assert sources["works.hierarchy"] == "file"
    assert sources["works.dir"] == "default"
    assert sources["stages.define.goal"] == "file"
    assert sources["stages.define.session"] == "default"
    stage = {f"stages.define.{n}" for n in ("goal", "session", "continuable", "gate")}
    stage |= {"stages.define.rules_include", "stages.define.rules_exclude"}
    assert set(sources) == _paths(Config()) | stage
    assert "bundle.size_threshold" not in sources
    assert "stages.define.judge" not in sources
    assert "stages.define.roots" not in sources


@SHAPE
def test_the_sources_follow_the_fields_of_config() -> None:
    """AC-3: the key paths of an empty file are the fields found by walking."""
    # Given the dataclasses of Config

    # When the sources of an empty file are compared with the walked fields
    sources = load_text("").sources

    # Then they are the same set
    assert set(sources) == _paths(Config())


def test_a_syntax_error_is_one_diagnostic_with_a_position() -> None:
    """AC-5: the place is the file relative to the root, a line and a column."""
    # Given a config whose second line is `b = = 2`
    text = "a = 1\nb = = 2\n"

    # When load_config runs
    loaded = load_text(text)

    # Then one error is at the file, line 2, column 5, and there is no Config
    assert loaded.config is None
    assert [(d.severity, d.where) for d in loaded.diagnostics] == [
        ("error", ".agents/wio/config.toml:2:5")
    ]
    assert str(ROOT) not in loaded.diagnostics[0].where
