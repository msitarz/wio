# SPDX-License-Identifier: Apache-2.0
"""Tests of finding what a key path names in a config."""

from typing import TYPE_CHECKING

import pytest

from tests.unit.config.fakes import load_text
from wio.config.keypath import Target, resolve
from wio.errors import ConfigurationError

if TYPE_CHECKING:
    from wio.models.config import Config

CONFIG = """
[stages.define]
goal = "g"
rules_include = ["a.b"]

[stages."x.y"]
skill = "s"
"""


def _config() -> Config:
    """Build the config the tests ask about.

    Returns:
        A config with the stages `define` and `x.y`.
    """
    config = load_text(CONFIG).config
    assert config is not None
    return config


@pytest.mark.parametrize(
    ("key", "path", "single"),
    [
        ("works.hierarchy", "works.hierarchy", True),
        ("stages.define.rules_include", "stages.define.rules_include", True),
        ("stages", "stages", False),
        ("stages.define", "stages.define", False),
        ("", "", False),
        ("roots", "roots", False),
        ('stages."x.y".skill', 'stages."x.y".skill', True),
        ('stages."x\\\\y"', None, False),
    ],
)
def test_a_key_path_names_a_setting_or_a_table(
    key: str,
    path: str | None,
    single: bool,  # noqa: FBT001
) -> None:
    """A leaf is a single setting and anything with keys is a table."""
    # Given a config with two stages

    # When a key path is resolved
    if path is None:
        with pytest.raises(ConfigurationError, match="no setting"):
            resolve(_config(), key)
        return
    target = resolve(_config(), key)

    # Then it names a single setting or a table, in canonical form
    assert target == Target(path, single=single)


def test_a_table_covers_the_settings_below_it_and_not_a_sibling() -> None:
    """The prefix match respects the dot."""
    # Given the target `stages.define`
    target = Target("stages.define", single=False)

    # When it is asked about a setting below it and a similarly named one
    below = target.covers("stages.define.goal")
    sibling = target.covers("stages.define2.goal")

    # Then only the first is covered
    assert (below, sibling) == (True, False)


def test_a_single_setting_covers_only_itself() -> None:
    """A single target does not take the keys that start with its path."""
    # Given the target of one setting
    target = Target("stages.define.goal", single=True)

    # When it is asked about itself and about a longer path
    own = target.covers("stages.define.goal")
    longer = target.covers("stages.define.goal.x")

    # Then it covers only itself
    assert (own, longer) == (True, False)


def test_the_whole_config_covers_every_setting() -> None:
    """The empty target is the root."""
    # Given the target of the whole config
    target = Target("", single=False)

    # When it is asked about any setting
    covered = target.covers("works.hierarchy")

    # Then it covers it
    assert covered


def test_an_unknown_top_level_key_names_the_closest_and_the_valid_keys() -> None:
    """`stage` is a typo of `stages`."""
    # Given a config

    # When a misspelled top-level key is resolved
    with pytest.raises(ConfigurationError) as caught:
        resolve(_config(), "stage.define")

    # Then the message names the closest match and the valid top-level keys
    message = str(caught.value)
    assert "Did you mean `stages`?" in message
    assert "the top level of the config" in message
    assert "`works`" in message


def test_an_unknown_entry_names_the_closest_path_and_the_entries() -> None:
    """`definer` is a typo of the stage `define`."""
    # Given a config with the stage `define`

    # When a misspelled stage is resolved
    with pytest.raises(ConfigurationError) as caught:
        resolve(_config(), "stages.definer")

    # Then the message names `stages.define` and the stages
    message = str(caught.value)
    assert "Did you mean `stages.define`?" in message
    assert "`define`" in message
    assert "`x.y`" in message


def test_an_unknown_key_in_an_empty_table_says_it_has_no_entries() -> None:
    """There is nothing to suggest under `roots` when no root is declared."""
    # Given a config without roots

    # When an entry of roots is resolved
    with pytest.raises(ConfigurationError) as caught:
        resolve(_config(), "roots.repo")

    # Then the message says the table has no entries
    assert "`roots` has no entries" in str(caught.value)


def test_an_optional_setting_that_is_not_set_is_refused() -> None:
    """`judge` has no value."""
    # Given a stage without a judge

    # When the judge is resolved
    with pytest.raises(ConfigurationError) as caught:
        resolve(_config(), "stages.define.judge")

    # Then the message says it is not set
    assert "optional setting" in str(caught.value)
    assert "not set" in str(caught.value)


def test_an_item_of_a_list_is_refused_and_the_list_is_named() -> None:
    """A list is shown whole."""
    # Given a stage with a `rules_include` list

    # When an item of it is resolved
    with pytest.raises(ConfigurationError) as caught:
        resolve(_config(), "stages.define.rules_include[0]")

    # Then the message says a list is shown whole, as the list's own key path
    assert "a list is shown whole" in str(caught.value)
    assert "`stages.define.rules_include`" in str(caught.value)


def test_an_index_after_a_key_that_holds_no_list_is_refused() -> None:
    """`hierarchy` is a string."""
    # Given a config

    # When an index follows a string setting
    with pytest.raises(ConfigurationError) as caught:
        resolve(_config(), "works.hierarchy[0]")

    # Then the message says it is not a list
    assert "is not a list" in str(caught.value)


def test_a_key_below_a_setting_is_refused() -> None:
    """A setting has no keys."""
    # Given a config

    # When a key is asked below a setting
    with pytest.raises(ConfigurationError) as caught:
        resolve(_config(), "works.hierarchy.x")

    # Then the message says the setting has no key
    assert "`works.hierarchy` is a setting" in str(caught.value)


@pytest.mark.parametrize("key", ["stages.", ".stages", "stages..define", "a b", "x]"])
def test_a_malformed_key_path_explains_the_syntax(key: str) -> None:
    """The message points at the place and shows a good key path."""
    # Given a text that is not a key path

    # When it is resolved
    with pytest.raises(ConfigurationError) as caught:
        resolve(_config(), key)

    # Then the message says it is not a key path and gives an example
    assert "is not a key path" in str(caught.value)
    assert "stages.define.goal" in str(caught.value)
