# SPDX-License-Identifier: Apache-2.0
"""Tests of the shape: every problem of a config file, reported at once."""

import dataclasses
from typing import TYPE_CHECKING

from tests.unit.config.fakes import load_text
from wio.models.config import Config, Stage
from wio.models.diagnostics import Diagnostic

if TYPE_CHECKING:
    from wio.config import CheckInputs


def _errors(text: str) -> dict[str, str]:
    """Load a config text and map the place of each error to its message.

    Args:
        text: The content of the config file.

    Returns:
        The message of every error, by `where`.
    """
    loaded = load_text(text)
    assert loaded.config is None
    return {d.where: d.message for d in loaded.diagnostics if d.severity == "error"}


def test_an_unknown_key_suggests_the_closest_and_lists_the_valid_keys() -> None:
    """AC-4: the error names the key, the closest match and the valid keys."""
    # Given a stage with a key `sessions`
    text = '[stages.define]\ngoal = "g"\nsessions = "any"\n'

    # When the config is loaded
    errors = _errors(text)

    # Then one error is at the key, says it is unknown, suggests session and lists
    assert list(errors) == ["stages.define.sessions"]
    message = errors["stages.define.sessions"]
    assert "unknown key" in message
    assert "Did you mean `session`?" in message
    for item in dataclasses.fields(Stage):
        assert f"`{item.name}`" in message


def test_a_key_that_belongs_elsewhere_names_the_tables_that_have_it() -> None:
    """AC-4: the hint says which tables have a key of that name."""
    # Given rules_exclude on a root, rule_presets on an action and a stage's
    # rules_always_include
    text = """
[roots.r]
paths = ["p"]
rules_exclude = ["a"]
[actions.a]
description = "d"
rule_presets = ["x"]
[stages.s]
goal = "g"
rules_always_include = ["a"]
"""

    # When the config is loaded
    errors = _errors(text)

    # Then each error names the tables whose schema has the key
    assert "a stage and a rule preset" in errors["roots.r.rules_exclude"]
    assert "a root" in errors["actions.a.rule_presets"]
    assert "the top level of the config" in errors["stages.s.rules_always_include"]


def test_a_wrong_value_and_a_wrong_type_come_back_together() -> None:
    """AC-4: both name the received value and the setting's description."""
    # Given a hierarchy that is not allowed and a reader that is not a string
    text = '[works]\nhierarchy = "nest"\n[trailers]\nreader = 3\n'

    # When the config is loaded
    errors = _errors(text)

    # Then two errors name what was received, what is valid and the description
    assert set(errors) == {"works.hierarchy", "trailers.reader"}
    value = errors["works.hierarchy"]
    assert 'received "nest"' in value
    assert '"flat" and "nesting"' in value
    assert "How the hierarchy is derived" in value
    kind = errors["trailers.reader"]
    assert "received 3" in kind
    assert "expected a string" in kind
    assert "Who parses trailers" in kind


def test_a_missing_required_key_names_the_key_and_its_description() -> None:
    """AC-4: a root without paths and an action without a description."""
    # Given a root without paths and an action without a description
    text = "[roots.wio]\n[actions.deliver]\n"

    # When the config is loaded
    errors = _errors(text)

    # Then each table has an error naming the key and the setting's description
    assert "`paths`" in errors["roots.wio"]
    assert "The paths of the root; required." in errors["roots.wio"]
    assert "`description`" in errors["actions.deliver"]
    assert "What the action does; required." in errors["actions.deliver"]


def test_a_broken_entry_does_not_cascade_into_a_check() -> None:
    """AC-4: the root stays, empty, so a check that looks it up finds it."""
    # Given a root without paths, a stage that selects it and a stand-in check
    text = '[roots.wio]\n[stages.s]\ngoal = "g"\nroots = ["wio"]\n'

    def unknown_roots(config: Config, _inputs: CheckInputs) -> list[Diagnostic]:
        return [
            Diagnostic("error", f"stages.{name}.roots", f"unknown root {root}")
            for name, stage in config.stages.items()
            for root in stage.roots or ()
            if root not in config.roots
        ]

    # When the config is loaded
    loaded = load_text(text, checks=(unknown_roots,))

    # Then only the missing paths is reported and the stand-in reports none
    assert [d.where for d in loaded.diagnostics] == ["roots.wio"]


def test_a_wrong_default_action_says_what_a_value_is() -> None:
    """AC-4: a value is a stage preset id or a list of stage names."""
    # Given a default action set to an integer
    text = "[works.defaults.actions]\ndefine = 3\n"

    # When the config is loaded
    errors = _errors(text)

    # Then the error names the received value and the two forms
    message = errors["works.defaults.actions.define"]
    assert "received 3" in message
    assert "a stage preset id or a list of stage names" in message


def test_the_other_vocabularies_list_their_allowed_values() -> None:
    """AC-4: a session and a judge outside their vocabulary."""
    # Given a session and a judge that are not allowed
    text = '[stages.s]\ngoal = "g"\nsession = "later"\njudge = "robot"\n'

    # When the config is loaded
    errors = _errors(text)

    # Then one error lists any and fresh and one lists human
    assert '"any" and "fresh"' in errors["stages.s.session"]
    assert '"human"' in errors["stages.s.judge"]
    assert len(errors) == 2


def test_a_date_or_a_time_is_never_a_setting() -> None:
    """AC-4: no setting holds a date or a time (A-2)."""
    # Given a key set to a date and another set to a time
    text = "[works]\ndir = 1979-05-27\n[trailers]\nreader = 07:32:00\n"

    # When the config is loaded
    errors = _errors(text)

    # Then each has an error that says so
    assert set(errors) == {"works.dir", "trailers.reader"}
    for message in errors.values():
        assert "no setting holds a date or a time" in message


def test_goal_and_skill_are_exactly_one() -> None:
    """AC-4: a stage with both or neither says what each is."""
    # Given a stage with both and a stage with neither
    text = '[stages.both]\ngoal = "g"\nskill = "s"\n[stages.neither]\ngate = true\n'

    # When the config is loaded
    errors = _errors(text)

    # Then each error says what goal and skill are, and that one is needed
    assert set(errors) == {"stages.both", "stages.neither"}
    for message in errors.values():
        assert "exactly one of `goal`" in message
        assert "`skill`" in message
    assert "sets both" in errors["stages.both"]
    assert "sets neither" in errors["stages.neither"]


def test_an_entry_of_the_wrong_type_is_dropped_and_the_rest_is_kept() -> None:
    """AC-4: a stage that is not a table and a list item that is not a string."""
    # Given a stage set to an integer and a rules list with an integer in it
    text = (
        "[stages]\ndefine = 3\n"
        '[stages.keep]\ngoal = "g"\nrules_include = ["a", 4, "b"]\n'
    )
    captured: list[Config] = []

    def capture(config: Config, _inputs: CheckInputs) -> list[Diagnostic]:
        captured.append(config)
        return []

    # When the config is loaded
    loaded = load_text(text, checks=(capture,))

    # Then both are errors, the bad entry is gone and the good items stay
    assert {d.where for d in loaded.diagnostics} == {
        "stages.define",
        "stages.keep.rules_include[1]",
    }
    assert list(captured[0].stages) == ["keep"]
    assert captured[0].stages["keep"].rules_include == ("a", "b")


def test_a_key_with_a_dot_is_quoted_in_its_path() -> None:
    """AC-4: a key path quotes a key that contains a dot, as TOML does."""
    # Given a stage whose name contains a dot and a bad value in it
    text = '[stages."a.b"]\ngoal = "g"\nsession = "later"\n'

    # When the config is loaded
    errors = _errors(text)

    # Then the key path quotes the name
    assert list(errors) == ['stages."a.b".session']


def test_a_list_of_strings_given_something_else_says_what_it_takes() -> None:
    """AC-4: a root whose paths are a string is told it takes a list of strings."""
    # Given a root whose paths are one string
    text = '[roots.r]\npaths = "p"\n'

    # When the config is loaded
    errors = _errors(text)

    # Then the one error names what was received, what is expected and the setting
    assert list(errors) == ["roots.r.paths"]
    message = errors["roots.r.paths"]
    assert 'received "p"' in message
    assert "expected a list of strings" in message
    assert "The paths of the root; required." in message


def test_a_boolean_an_integer_and_a_table_are_named_by_their_kind() -> None:
    """AC-4: each wrong type says which kind of value the key takes."""
    # Given a flag set to a word, a threshold set to a word, and two tables set to a
    # number
    text = """
works = 3
[templates]
kinds = 3
[bundle]
size_threshold = "big"
[stages.s]
goal = "g"
continuable = "yes"
"""

    # When the config is loaded
    errors = _errors(text)

    # Then each error names what was received and the kind the key takes
    assert 'received "yes", expected a boolean' in errors["stages.s.continuable"]
    assert 'received "big", expected an integer' in errors["bundle.size_threshold"]
    assert "received 3, expected a table." in errors["templates.kinds"]
    assert "received 3, expected a table (" in errors["works"]


def test_a_stage_preset_and_a_list_of_stages_are_both_accepted() -> None:
    """AC-4: an action's pipeline is a preset id or a list of stage names."""
    # Given one action set to a preset id and another to a list of stage names
    text = '[works.defaults.actions]\ndefine = "define-feature"\ndeliver = ["a", "b"]\n'

    # When the config is loaded
    loaded = load_text(text)

    # Then there is no error, and each is kept as written
    assert loaded.diagnostics == ()
    assert loaded.config is not None
    assert dict(loaded.config.works.defaults.actions) == {
        "define": "define-feature",
        "deliver": ("a", "b"),
    }


def test_a_pipeline_that_is_neither_is_told_what_it_takes() -> None:
    """AC-4: a number, and a list with a number in it, are reported separately."""
    # Given one action set to a number and another to a list holding a number
    text = '[works.defaults.actions]\nx = 3\ny = ["a", 1]\n'

    # When the config is loaded
    errors = _errors(text)

    # Then the number is told the two forms, and the item is told it is not a string
    assert (
        "stage preset id or a list of stage names" in errors["works.defaults.actions.x"]
    )
    assert "received 1, expected a string" in errors["works.defaults.actions.y[1]"]
    assert set(errors) == {"works.defaults.actions.x", "works.defaults.actions.y[1]"}


def test_an_entry_of_an_open_table_has_the_file_as_its_source() -> None:
    """AC-3: a name the file adds to an open table is a setting of the file."""
    # Given a stage preset and an action pipeline, both entries of open tables
    text = '[stage_presets]\nx = ["a"]\n[works.defaults.actions]\ndefine = "p"\n'

    # When the config is loaded
    sources = load_text(text).sources

    # Then each entry is `file`
    assert sources["stage_presets.x"] == "file"
    assert sources["works.defaults.actions.define"] == "file"
