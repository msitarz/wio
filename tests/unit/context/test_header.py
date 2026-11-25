# SPDX-License-Identifier: Apache-2.0
"""Tests of the header of a bundle."""

import pytest

from wio.context.header import header
from wio.models.config import Stage

_PENDING = pytest.mark.xfail(strict=True)
_SKILL = ("wio-define", ".agents/skills/wio-define", "1a47c19b09044a02")


def _header(
    stage: Stage,
    *,
    title: str | None = "Demo",
    rules: int = 3,
    skill: tuple[str, str, str] | None = None,
) -> str:
    """Build the header of `k3m9xq` at `deliver` and `architecture`.

    Args:
        stage: The stage's settings.
        title: The Work's title.
        rules: The number of rules.
        skill: The skill, if the stage has one.

    Returns:
        The header.
    """
    return header(
        "k3m9xq", title, "deliver", "architecture", stage, rules, 1234, 56, skill
    )


@_PENDING
def test_a_fresh_gate_that_a_person_judges() -> None:
    """AC-1, AC-2, AC-3: every line of a header, in order."""
    # Given a stage that is a gate with a person as judge and a fresh session
    stage = Stage(goal="Judge.", gate=True, judge="human", session="fresh")

    # When the header is built
    text = _header(stage)

    # Then it names the Work, action and stage first and states the rest
    assert text.split("\n") == [
        "work: k3m9xq (Demo)",
        "action: deliver",
        "stage: architecture",
        "gate: yes, judged by a person",
        "session: fresh",
        "rules: 3",
        "size: 1234 bytes, 56 lines (body)",
        "command: wio context k3m9xq deliver architecture",
    ]


@_PENDING
@pytest.mark.parametrize(
    ("stage", "gate", "session"),
    [
        (
            Stage(goal="Do.", continuable=False),
            "gate: no",
            "session: any, do not continue it",
        ),
        (Stage(goal="Do.", judge="human"), "gate: no", "session: any"),
        (Stage(goal="Do.", gate=True), "gate: yes", "session: any"),
        (
            Stage(goal="Do.", session="fresh", continuable=False),
            "gate: no",
            "session: fresh, do not continue it",
        ),
    ],
    ids=["not-continuable", "judge-without-gate", "agent-gate", "fresh-and-single"],
)
def test_the_gate_and_session_lines(stage: Stage, gate: str, session: str) -> None:
    """AC-1: only a gate says who judges, and the session advice is given."""
    # Given the stage

    # When the header is built
    lines = _header(stage).split("\n")

    # Then the gate and session lines say what the stage is
    assert lines[3:5] == [gate, session]


@_PENDING
def test_a_work_with_no_title_is_named_by_its_id_alone() -> None:
    """AC-1: no empty parentheses."""
    # Given a Work with no title

    # When the header is built
    lines = _header(Stage(goal="Do."), title=None).split("\n")

    # Then the first line holds the id alone
    assert lines[0] == "work: k3m9xq"


@_PENDING
def test_a_bundle_with_no_rule_says_so() -> None:
    """AC-2: zero rules is stated."""
    # Given no rule

    # When the header is built
    text = _header(Stage(goal="Do."), rules=0)

    # Then it states zero
    assert "rules: 0" in text.split("\n")


@_PENDING
def test_a_stage_with_a_skill_names_where_it_was_found() -> None:
    """AC-4: the skill, its directory and its hash, and no such line for a goal."""
    # Given a stage with a skill and one with a goal

    # When the header is built for each
    with_skill = _header(Stage(skill="wio-define"), skill=_SKILL).split("\n")
    with_goal = _header(Stage(goal="Do.")).split("\n")

    # Then only the first has the skill line, after the command
    assert with_skill[-1] == (
        "skill: wio-define (.agents/skills/wio-define, files 1a47c19b09044a02)"
    )
    assert with_skill[:-1] == with_goal


@_PENDING
@pytest.mark.parametrize("skill", [None, _SKILL], ids=["goal", "skill"])
@pytest.mark.parametrize("title", ["Demo", None], ids=["titled", "untitled"])
def test_the_header_is_one_block(
    skill: tuple[str, str, str] | None, title: str | None
) -> None:
    """AC-5: no blank line and no newline at the end."""
    # Given every kind of header
    stage = Stage(goal="Do.", gate=True, judge="human", continuable=False)

    # When it is built
    text = _header(stage, title=title, skill=skill)

    # Then it has no empty line and does not end with a newline
    assert "" not in text.split("\n")
