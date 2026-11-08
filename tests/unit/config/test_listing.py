# SPDX-License-Identifier: Apache-2.0
"""Tests of the list of settings and of the lines that show them."""

from typing import TYPE_CHECKING

import pytest

from tests.unit.config.fakes import load_text
from wio.config.listing import (
    WIDTH,
    Setting,
    full_line,
    quote,
    settings_of,
    short_line,
    toml_value,
)

if TYPE_CHECKING:
    from wio.config.listing import Value

CONFIG = f"""
[stages.define]
goal = \"\"\"Turn an intent
into "a Work"
and stop\"\"\"
rules_include = ["py.ARC001", "py.ARC002"]

[stages."a.b"]
skill = "writing"

[actions.define]
description = "{"d" * 90}"
"""


def _settings() -> dict[str, Setting]:
    """List the settings of a config with a stage, a quoted stage and an action.

    Returns:
        The settings by key path.
    """
    loaded = load_text(CONFIG)
    assert loaded.config is not None
    found = settings_of(loaded.config, dict(loaded.sources))
    return {item.path: item for item in found}


def test_settings_are_sorted_by_key_path_and_carry_their_source() -> None:
    """Each set value and each default is listed once, in key-path order."""
    # Given a config that sets some stage keys and leaves the rest to defaults

    # When its settings are listed
    found = _settings()

    # Then they are sorted and each one knows whether the file or a default set it
    assert list(found) == sorted(found)
    assert found["stages.define.goal"].source == "file"
    assert found["stages.define.session"].source == "default"
    assert found["works.hierarchy"].description == (
        "How the hierarchy is derived; `flat` by default."
    )


def test_a_key_that_needs_quotes_is_quoted_in_its_path() -> None:
    """A stage named with a dot is listed under a TOML-quoted key."""
    # Given a config with a stage named `a.b`

    # When its settings are listed
    found = _settings()

    # Then the key path quotes the name as TOML does
    assert found['stages."a.b".skill'].value == "writing"


def test_an_optional_setting_that_is_not_set_is_not_listed() -> None:
    """A setting with no value has no line."""
    # Given a stage without a judge and a bundle without a size threshold

    # When its settings are listed
    found = _settings()

    # Then neither is in the list
    assert "stages.define.judge" not in found
    assert "bundle.size_threshold" not in found


def test_a_multi_line_string_shows_its_first_line_and_an_ellipsis() -> None:
    """The short line keeps the first line of the goal and marks the cut."""
    # Given a goal of three lines
    setting = _settings()["stages.define.goal"]

    # When its short line is written
    line = short_line(setting)

    # Then the first line is shown, then an ellipsis and the closing quote
    assert line == 'stages.define.goal = "Turn an intent…"  # file'


def test_a_long_string_is_cut_so_that_the_line_is_80_columns() -> None:
    """The label stays whole and the value gives way."""
    # Given a description of ninety characters
    setting = _settings()["actions.define.description"]

    # When its short line is written
    line = short_line(setting)

    # Then the line is at most 80 columns and ends with the cut mark and label
    assert len(line) <= WIDTH
    assert line.endswith('…"  # file')


def test_a_list_loses_items_from_its_end_to_fit() -> None:
    """An array that does not fit keeps its leading items and an ellipsis."""
    # Given a list setting with a long key path
    path = "x" * 50
    setting = Setting(path, ("alpha", "beta", "gamma"), "file", "")

    # When its short line is written
    line = short_line(setting)

    # Then it is at most 80 columns and shows the leading items then the mark
    assert line == f'{path} = ["alpha", …]  # file'
    assert len(line) <= WIDTH


def test_a_value_that_does_not_fit_at_all_is_an_ellipsis() -> None:
    """When the key path and the label leave no room, the value is `…`."""
    # Given a setting whose key path and label reach 80 columns
    path = "k" * 70
    setting = Setting(path, "value", "default", "")

    # When its short line is written
    line = short_line(setting)

    # Then the value is an ellipsis and the key path and label are whole
    assert line == f"{path} = …  # default"


def test_an_array_that_cannot_show_one_item_is_an_ellipsis() -> None:
    """With room for no item the array gives way to `…`."""
    # Given a list and a key path that leave room for two columns
    path = "k" * 67
    setting = Setting(path, ("alpha",), "file", "")

    # When its short line is written
    line = short_line(setting)

    # Then the value is an ellipsis
    assert line == f"{path} = …  # file"


def test_the_full_line_shows_the_whole_value() -> None:
    """Nothing is shortened, and a newline is written as an escape."""
    # Given the three-line goal
    setting = _settings()["stages.define.goal"]

    # When its full line is written
    line = full_line(setting)

    # Then every line of the goal is in it on one line
    assert line == (
        'stages.define.goal = "Turn an intent\\ninto \\"a Work\\"\\nand stop"  # file'
    )


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (True, "true"),
        (False, "false"),
        (3, "3"),
        ("a", '"a"'),
        ((), "[]"),
        (("a", "b"), '["a", "b"]'),
    ],
)
def test_values_are_written_in_toml_syntax(value: Value, text: str) -> None:
    """Strings are quoted and lists are arrays."""
    # Given a string, a boolean, an integer or a list of strings

    # When it is written as a setting's value
    written = toml_value(value)

    # Then it appears as the config file would hold it
    assert written == text


def test_a_control_character_is_escaped_in_a_quoted_string() -> None:
    """A string holds no raw control character once quoted."""
    # Given a string with a tab, a backslash and a bell
    text = "a\tb\\c\x07"

    # When it is quoted
    quoted = quote(text)

    # Then each is escaped as TOML escapes it
    assert quoted == '"a\\tb\\\\c\\u0007"'
