# SPDX-License-Identifier: Apache-2.0
"""Test what guidance a session receives from the configured stage.

The cases use the shared settings port and the caller's skill lookup result.
"""

from unittest.mock import Mock

import pytest

from wio.context.guidance import stage_guidance
from wio.models.config import Config, Stage
from wio.models.frozen import freeze
from wio.models.skill import FoundSkill


@pytest.mark.parametrize("goal", ["  Read the contract.\nWrite the tests.\n", ""])
def test_guidance_preserves_the_goal(goal: str) -> None:
    """Give the session the goal exactly as written in the config.

    Args:
        goal: The empty or multiline stage goal.
    """
    # Given a stage configured with a goal
    settings = Mock()
    settings.load.return_value = Config(stages=freeze({"design": Stage(goal=goal)}))

    # When the stage guidance is built
    guidance = stage_guidance(settings, "design", None)

    # Then the guidance preserves all the goal's text
    assert guidance == goal


@pytest.mark.parametrize(
    ("name", "directory", "shown_name", "shown_directory"),
    [
        (
            "wio-define",
            ".agents/wio/skills/wio-define",
            "wio-define",
            ".agents/wio/skills/wio-define",
        ),
        ("review", "team/procedures/review", "review", "team/procedures/review"),
        pytest.param(
            "review\r\nnow",
            "team\nskills/review\r\nnow",
            r"review\r\nnow",
            r"team\nskills/review\r\nnow",
            id="line-breaks",
            marks=pytest.mark.xfail(strict=True, raises=AssertionError),
        ),
        pytest.param(
            r"review\r\nnow",
            r"team\nskills/review\r\nnow",
            r"review\\r\\nnow",
            r"team\\nskills/review\\r\\nnow",
            id="literal-backslashes",
            marks=pytest.mark.xfail(strict=True, raises=AssertionError),
        ),
    ],
)
def test_guidance_points_to_the_found_skill(
    name: str, directory: str, shown_name: str, shown_directory: str
) -> None:
    """Direct the session to the named skill using the caller's lookup.

    The complete line is fixed and contains only the name and file location
    supplied for the skill.

    Args:
        name: The stage's configured skill.
        directory: The directory found by the caller.
        shown_name: The skill name as it should appear in the guidance.
        shown_directory: The directory as it should appear in the guidance.
    """
    # Given a stage with a skill found in a configured directory
    settings = Mock()
    settings.load.return_value = Config(stages=freeze({"define": Stage(skill=name)}))
    skill = FoundSkill(directory, "a" * 64)

    # When the stage guidance is built
    guidance = stage_guidance(settings, "define", skill)

    # Then the guidance is exactly one instruction pointing to SKILL.md
    assert guidance == (
        f"This stage's procedure is the skill `{shown_name}`. Read "
        f"`{shown_directory}/SKILL.md` and follow it; "
        "its other files are in the same directory."
    )
