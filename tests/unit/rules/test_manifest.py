# SPDX-License-Identifier: Apache-2.0
"""Tests of the reader of a ruleset's manifest, which runs on text alone."""

from pathlib import PurePosixPath

import pytest

from tests.unit.rules.support import kinds
from wio.models.config import RulePreset
from wio.rules import ManifestReading, read_manifest

_PATH = PurePosixPath(".agents/wio/rules/demo/ruleset.toml")
_FILE = str(_PATH)


def _read(text: str) -> ManifestReading:
    """Read a text as the manifest of the ruleset `demo`.

    Args:
        text: The text of the file.

    Returns:
        What the reader gave.
    """
    return read_manifest(_PATH, text)


def test_a_full_manifest_is_read_in_the_order_written() -> None:
    """AC-1: the description, the families and the rule presets."""
    # Given a manifest with a description, two families and one rule preset
    text = (
        'description = "How to build adapters."\n\n'
        '[families]\nARC = "Architecture"\nPAY = "Payments"\n\n'
        "[rule_presets.recommended]\n"
        'rules_include = ["ARC", "PAY001"]\nrules_exclude = ["ARC009"]\n'
    )

    # When it is read
    reading = _read(text)

    # Then the manifest holds them in the order written, and nothing is reported
    manifest = reading.manifest
    assert manifest is not None
    assert manifest.description == "How to build adapters."
    assert list(manifest.families.items()) == [
        ("ARC", "Architecture"),
        ("PAY", "Payments"),
    ]
    assert dict(manifest.rule_presets) == {
        "recommended": RulePreset(("ARC", "PAY001"), ("ARC009",))
    }
    assert reading.diagnostics == ()


def test_an_empty_manifest_declares_nothing() -> None:
    """AC-1: a ruleset can be started before its first rule."""
    # Given an empty `ruleset.toml`

    # When it is read
    reading = _read("")

    # Then the manifest has no description, family or rule preset, and nothing is
    # reported
    assert reading.manifest is not None
    assert reading.manifest.description is None
    assert not reading.manifest.families
    assert not reading.manifest.rule_presets
    assert reading.diagnostics == ()


def test_a_manifest_that_does_not_parse_is_one_error_with_its_line() -> None:
    """AC-2: the place is the path followed by `:` and the line of the fault."""
    # Given a manifest whose fault is on line 2
    text = 'description = "ok"\nfamilies = ]\n'

    # When it is read
    reading = _read(text)

    # Then it is one error at the path and line 2, and there is no manifest
    assert reading.manifest is None
    assert kinds(reading.diagnostics) == [("error", f"{_FILE}:2")]


@pytest.mark.parametrize(
    ("text", "key"),
    [
        ("description = 3\n", "description"),
        ("families = []\n", "families"),
        ("[families]\nARC = 3\n", "families.ARC"),
        ('[families]\nArc = "Architecture"\n', "families.Arc"),
        ("[rule_presets.Backend]\n", "rule_presets.Backend"),
        ('rule_presets.x = "all"\n', "rule_presets.x"),
        ('[rule_presets.x]\nrules_include = "ARC"\n', "rule_presets.x.rules_include"),
        (
            "[rule_presets.x]\nrules_include = [3]\n",
            "rule_presets.x.rules_include[0]",
        ),
    ],
)
def test_a_fault_of_the_shape_is_one_error_at_its_key_path(text: str, key: str) -> None:
    """AC-2: the place is the path followed by `#` and the key path."""
    # Given a manifest with one fault of its shape

    # When it is read
    reading = _read(text)

    # Then it is one error at the path, `#` and the key path, and no manifest
    assert reading.manifest is None
    assert kinds(reading.diagnostics) == [("error", f"{_FILE}#{key}")]


@pytest.mark.parametrize(
    ("text", "key", "close"),
    [
        ('description = "ok"\nfamily = {}\n', "family", "families"),
        (
            '[rule_presets.x]\nrules_includes = ["ARC"]\n',
            "rule_presets.x.rules_includes",
            "rules_include",
        ),
    ],
)
def test_a_doubtful_key_is_a_warning_that_names_the_closest_key(
    text: str, key: str, close: str
) -> None:
    """AC-2: the manifest is still returned."""
    # Given a manifest with a valid part and a mistyped key

    # When it is read
    reading = _read(text)

    # Then one warning names the key and the closest known key, and the manifest
    # is returned
    assert kinds(reading.diagnostics) == [("warning", f"{_FILE}#{key}")]
    message = reading.diagnostics[0].message
    assert f"`{key.rsplit('.', 1)[-1]}`" in message
    assert f"Did you mean `{close}`?" in message
    assert reading.manifest is not None
