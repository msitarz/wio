# SPDX-License-Identifier: Apache-2.0
"""Tests of the topics that the manifests declare."""

from typing import TYPE_CHECKING

import pytest

from tests.unit.fakes import ROOT, FakeRepository, MemoryFileSystem
from wio.rules.topics import RuleTopics

if TYPE_CHECKING:
    from wio.context.ports import Topics

_RULES = ROOT / ".agents" / "wio" / "rules"


def _topics() -> Topics:
    """Build the provider over two rulesets that share the family `ERR`.

    Returns:
        The provider, typed as the port that it satisfies.
    """
    files = {
        _RULES / "mattpocock" / "ruleset.toml": (
            '[families]\nERR = "Error handling"\nARC = "Architecture"\n'
        ),
        _RULES / "python" / "ruleset.toml": (
            '[families]\nAPI = "Python API"\nERR = "Process"\n'
        ),
    }
    return RuleTopics(FakeRepository(), MemoryFileSystem(files))


@pytest.mark.parametrize(
    ("ruleset", "family", "expected"),
    [
        ("mattpocock", "ERR", "Error handling"),
        ("mattpocock", "ARC", "Architecture"),
        ("python", "API", "Python API"),
        ("python", "ERR", "Process"),
    ],
)
def test_the_port_answers_from_the_manifests(
    ruleset: str, family: str, expected: str
) -> None:
    """AC-4: each ruleset's own manifest gives the topic."""
    # Given two rulesets whose manifests declare their families
    topics = _topics()

    # When the topic is asked for
    found = topics.topic(ruleset, family)

    # Then it is the one that the ruleset's manifest declares
    assert found == expected


@pytest.mark.parametrize(
    ("ruleset", "family"), [("ghost", "ERR"), ("mattpocock", "API")]
)
def test_an_unknown_ruleset_or_family_is_a_key_error(ruleset: str, family: str) -> None:
    """AC-4: the port does not make a topic up."""
    # Given two rulesets
    topics = _topics()

    # When a ruleset or a family that no manifest declares is asked for
    # Then it is refused
    with pytest.raises(KeyError):
        topics.topic(ruleset, family)
